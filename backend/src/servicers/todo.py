import asyncio
import logging
from dataclasses import dataclass

import pydantic_ai
import uuid7
from pydantic_ai import RunContext
from reboot.agents.pydantic_ai import Agent
from reboot.aio.contexts import (
    ReaderContext,
    TransactionContext,
    WorkflowContext,
    WriterContext,
)
from reboot.aio.workflows import at_most_once

from ai_chat_todo.v1.todo import TodoItem
from ai_chat_todo.v1.todo_rbt import TodoList, User

logger = logging.getLogger(__name__)


# -- Researcher agent. --


@dataclass
class ResearcherDeps:
    item_text: str


researcher = Agent(
    # NOTE: Pydantic AI reads the Anthropic API key from the
    # `ANTHROPIC_API_KEY` environment variable.
    "anthropic:claude-sonnet-4-5",
    name="researcher",
    deps_type=ResearcherDeps,
    system_prompt=(
        "You are a research assistant. Given a single todo "
        "list item, produce a concise but thorough markdown "
        "research brief on the topic the item describes. "
        "Use markdown headings, bullet lists, code blocks, "
        "and links where useful. Aim for roughly 200–500 "
        "words. Output only the markdown body — no "
        "preamble, no closing remarks. Do not wrap the "
        "whole response in a code fence."
    ),
)


def _truncate(value: object, limit: int = 300) -> str:
    text = value if isinstance(value, str) else repr(value)
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [+{len(text) - limit} chars]"


def _log_node(prefix: str, node: object) -> None:
    if pydantic_ai.Agent.is_user_prompt_node(node):
        logger.info("%s prompt submitted", prefix)
    elif pydantic_ai.Agent.is_call_tools_node(node):
        for part in node.model_response.parts:
            kind = getattr(part, "part_kind", None)
            if kind == "text":
                logger.info(
                    "%s text: %s", prefix, _truncate(part.content)
                )
    elif pydantic_ai.Agent.is_end_node(node):
        logger.info("%s done", prefix)


# -- Servicers. --


class UserServicer(User.Servicer):

    async def create_todo_list(
        self,
        context: TransactionContext,
        request: User.CreateTodoListRequest,
    ) -> User.CreateTodoListResponse:
        todo_list, _ = await TodoList.create(context, title=request.title)
        return User.CreateTodoListResponse(todo_list_id=todo_list.state_id)


class TodoListServicer(TodoList.Servicer):

    async def create(
        self,
        context: WriterContext,
        request: TodoList.CreateRequest,
    ) -> None:
        self.state.title = request.title

    async def get(
        self,
        context: ReaderContext,
    ) -> TodoList.GetResponse:
        return TodoList.GetResponse(
            title=self.state.title,
            items=list(self.state.items),
        )

    async def add_item(
        self,
        context: WriterContext,
        request: TodoList.AddItemRequest,
    ) -> TodoList.AddItemResponse:
        item_id = str(uuid7.create())
        self.state.items.append(
            TodoItem(
                id=item_id,
                text=request.text,
                completed=False,
                research_status="idle",
                research_markdown="",
            )
        )
        return TodoList.AddItemResponse(item_id=item_id)

    async def remove_item(
        self,
        context: WriterContext,
        request: TodoList.RemoveItemRequest,
    ) -> None:
        self.state.items = [
            item for item in self.state.items if item.id != request.item_id
        ]

    async def toggle_item(
        self,
        context: WriterContext,
        request: TodoList.ToggleItemRequest,
    ) -> None:
        for item in self.state.items:
            if item.id == request.item_id:
                item.completed = not item.completed
                break

    async def update_item_text(
        self,
        context: WriterContext,
        request: TodoList.UpdateItemTextRequest,
    ) -> None:
        for item in self.state.items:
            if item.id == request.item_id:
                item.text = request.text
                break

    async def reorder_item(
        self,
        context: WriterContext,
        request: TodoList.ReorderItemRequest,
    ) -> None:
        items = self.state.items
        n = len(items)
        if not (0 <= request.from_index < n and 0 <= request.to_index < n):
            return
        if request.from_index == request.to_index:
            return
        item = items.pop(request.from_index)
        items.insert(request.to_index, item)
        self.state.items = items

    async def start_research(
        self,
        context: WriterContext,
        request: TodoList.StartResearchRequest,
    ) -> None:
        for item in self.state.items:
            if item.id != request.item_id:
                continue
            # Only kick off if currently idle.
            if item.research_status in ("running", "completed"):
                return
            item.research_status = "running"
            await self.ref().schedule().research(
                context, item_id=request.item_id
            )
            return

    @classmethod
    async def research(
        cls,
        context: WorkflowContext,
        request: TodoList.ResearchRequest,
    ) -> None:
        todo_list = TodoList.ref()
        item_id = request.item_id

        # Pull the item text from current state.
        state = await todo_list.read(context)
        item_text = ""
        for item in state.items:
            if item.id == item_id:
                item_text = item.text
                break
        if not item_text:
            return

        log_prefix = (
            f"researcher[list={todo_list.state_id} "
            f"item={item_id}]"
        )

        async def run_researcher() -> str:
            prompt = (
                f"Research the following todo item and "
                f"return a markdown brief:\n\n{item_text}"
            )
            async with researcher.iter(
                context,
                prompt,
                deps=ResearcherDeps(item_text=item_text),
            ) as run:
                async for node in run:
                    _log_node(log_prefix, node)
            assert run.result is not None
            return str(run.result.output)

        try:
            markdown = await at_most_once(
                f"Research {item_id}",
                context,
                run_researcher,
                type=str,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            import traceback
            traceback.print_exc()
            markdown = (
                "_Research failed. Check the backend log "
                "for details (e.g., missing "
                "`ANTHROPIC_API_KEY`)._"
            )

        async def save_result(state):
            for item in state.items:
                if item.id == item_id:
                    item.research_status = "completed"
                    item.research_markdown = markdown
                    break

        await todo_list.idempotently(
            f"save research result {item_id}",
        ).write(context, save_result)
