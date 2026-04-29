from reboot.api import (
    API,
    UI,
    Field,
    Methods,
    Model,
    Reader,
    Tool,
    Transaction,
    Type,
    Workflow,
    Writer,
)


# -- Helper Models. --


class TodoItem(Model):
    id: str = Field(tag=1, default="")
    text: str = Field(tag=2, default="")
    completed: bool = Field(tag=3, default=False)
    # "" or "idle" → idle, "running", "completed".
    # Drives the research button's three states in the
    # React UI. Empty string is treated as idle (proto3
    # zero-value default).
    research_status: str = Field(tag=4, default="")
    research_markdown: str = Field(tag=5, default="")


# -- User models. --


class CreateTodoListRequest(Model):
    title: str = Field(tag=1, default="")


class CreateTodoListResponse(Model):
    todo_list_id: str = Field(tag=1)


class UserState(Model):
    pass


# -- TodoList models. --


class TodoListState(Model):
    title: str = Field(tag=1, default="")
    items: list[TodoItem] = Field(tag=2, default_factory=list)


class CreateRequest(Model):
    title: str = Field(tag=1, default="")


class GetResponse(Model):
    title: str = Field(tag=1)
    items: list[TodoItem] = Field(tag=2, default_factory=list)


class AddItemRequest(Model):
    text: str = Field(tag=1)


class AddItemResponse(Model):
    item_id: str = Field(tag=1)


class ItemIdRequest(Model):
    item_id: str = Field(tag=1)


class UpdateItemTextRequest(Model):
    item_id: str = Field(tag=1)
    text: str = Field(tag=2)


class ReorderItemRequest(Model):
    from_index: int = Field(tag=1)
    to_index: int = Field(tag=2)


class ResearchRequest(Model):
    item_id: str = Field(tag=1)


api = API(
    User=Type(
        state=UserState,
        methods=Methods(
            create_todo_list=Transaction(
                request=CreateTodoListRequest,
                response=CreateTodoListResponse,
                description="Create a new todo list with the "
                "given title. Returns the ID of the new list. "
                "That ID is not human-readable; pass it to "
                "future tool calls where needed, but do not "
                "tell the human what it is.",
                mcp=Tool(),
            ),
        ),
    ),
    TodoList=Type(
        state=TodoListState,
        methods=Methods(
            show_list=UI(
                request=None,
                path="web/ui/list",
                title="Todo List",
                description="Interactive todo list UI with "
                "drag-and-drop reordering. Open this so the "
                "human can see and edit their list.",
            ),
            show_research=UI(
                request=ResearchRequest,
                path="web/ui/research",
                title="Research",
                description="Open the research markdown "
                "viewer for a specific todo item. The item "
                "must have already had its `start_research` "
                "called and its research workflow finished. "
                "Pass the item's `item_id`.",
            ),
            create=Writer(
                request=CreateRequest,
                response=None,
                factory=True,
                mcp=None,
            ),
            get=Reader(
                request=None,
                response=GetResponse,
                description="Get the todo list's title and "
                "all items in order, including each item's "
                "research_status and research_markdown.",
                mcp=Tool(),
            ),
            add_item=Writer(
                request=AddItemRequest,
                response=AddItemResponse,
                description="Append a new item to the end "
                "of the list. Returns the new item's ID.",
                mcp=Tool(),
            ),
            remove_item=Writer(
                request=ItemIdRequest,
                response=None,
                description="Remove the item with the given "
                "ID from the list.",
                mcp=Tool(),
            ),
            toggle_item=Writer(
                request=ItemIdRequest,
                response=None,
                description="Toggle the completed state of "
                "the item with the given ID.",
                mcp=Tool(),
            ),
            update_item_text=Writer(
                request=UpdateItemTextRequest,
                response=None,
                description="Replace the text of the item "
                "with the given ID.",
                mcp=Tool(),
            ),
            reorder_item=Writer(
                request=ReorderItemRequest,
                response=None,
                description="Move the item at from_index to "
                "to_index. Both indices are 0-based.",
                mcp=Tool(),
            ),
            start_research=Writer(
                request=ResearchRequest,
                response=None,
                description="Kick off the background "
                "research workflow on the item with the "
                "given ID. Marks the item's research_status "
                "as 'running' and schedules the `research` "
                "workflow which will populate "
                "research_markdown when it finishes. No-op "
                "if the item's research_status is not "
                "'idle'.",
                mcp=Tool(),
            ),
            research=Workflow(
                request=ResearchRequest,
                response=None,
                description="Background research workflow "
                "that uses an LLM agent to produce a "
                "markdown research brief for a single todo "
                "item, then stores it on the item. Triggered "
                "by `start_research`; not intended for "
                "direct invocation.",
                mcp=None,
            ),
        ),
    ),
)
