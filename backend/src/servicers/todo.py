from ai_chat_todo.v1.todo import TodoItem
from ai_chat_todo.v1.todo_rbt import TodoList, User
from reboot.aio.contexts import (
    ReaderContext,
    TransactionContext,
    WriterContext,
)
import uuid7


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
            TodoItem(id=item_id, text=request.text, completed=False)
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
