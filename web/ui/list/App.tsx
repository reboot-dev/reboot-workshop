import {
  useEffect,
  useRef,
  useState,
  type DragEvent,
  type FC,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { useTodoList } from "@api/ai_chat_todo/v1/todo_rbt_react";
import css from "./App.module.css";

export const ShowListApp: FC = () => {
  const todoList = useTodoList();
  const { response, isLoading } = todoList.useGet();

  const [newItemText, setNewItemText] = useState("");
  const [dragFromIndex, setDragFromIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState("");

  const editingInputRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    if (editingId && editingInputRef.current) {
      editingInputRef.current.focus();
      editingInputRef.current.select();
    }
  }, [editingId]);

  if (isLoading && response === undefined) {
    return (
      <div className={css.container}>
        <div className={css.loading}>loading...</div>
      </div>
    );
  }

  const items = response?.items ?? [];
  const title = response?.title ?? "";
  const completedCount = items.filter((item) => item.completed).length;

  const handleAddItem = async (e: FormEvent) => {
    e.preventDefault();
    const text = newItemText.trim();
    if (!text) return;
    setNewItemText("");
    await todoList.addItem({ text });
  };

  const handleToggle = async (itemId: string) => {
    await todoList.toggleItem({ itemId });
  };

  const handleRemove = async (itemId: string) => {
    await todoList.removeItem({ itemId });
  };

  const startEditing = (itemId: string, currentText: string) => {
    setEditingId(itemId);
    setEditingText(currentText);
  };

  const commitEdit = async () => {
    if (editingId === null) return;
    const text = editingText.trim();
    const id = editingId;
    setEditingId(null);
    setEditingText("");
    if (!text) return;
    await todoList.updateItemText({ itemId: id, text });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingText("");
  };

  const handleEditKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      void commitEdit();
    } else if (e.key === "Escape") {
      e.preventDefault();
      cancelEdit();
    }
  };

  const handleDragStart =
    (index: number) => (e: DragEvent<HTMLDivElement>) => {
      setDragFromIndex(index);
      e.dataTransfer.effectAllowed = "move";
      try {
        e.dataTransfer.setData("text/plain", String(index));
      } catch {
        // Some browsers throw if setData is called outside dragstart.
      }
    };

  const handleDragOver =
    (index: number) => (e: DragEvent<HTMLDivElement>) => {
      if (dragFromIndex === null) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      if (dragOverIndex !== index) {
        setDragOverIndex(index);
      }
    };

  const handleDragLeave = () => {
    setDragOverIndex(null);
  };

  const handleDrop =
    (toIndex: number) => async (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      const fromIndex = dragFromIndex;
      setDragFromIndex(null);
      setDragOverIndex(null);
      if (fromIndex === null || fromIndex === toIndex) return;
      await todoList.reorderItem({ fromIndex, toIndex });
    };

  const handleDragEnd = () => {
    setDragFromIndex(null);
    setDragOverIndex(null);
  };

  return (
    <div className={css.container}>
      <header className={css.header}>
        <div className={css.title}>{title || "todo"}</div>
        <div className={css.count}>
          {completedCount}/{items.length} done
        </div>
      </header>

      <div className={css.list}>
        {items.length === 0 && (
          <div className={css.empty}>no items yet — add one below</div>
        )}
        {items.map((item, index) => {
          const isDragging = dragFromIndex === index;
          const isDragOver =
            dragOverIndex === index && dragFromIndex !== index;
          const rowClass = [
            css.row,
            item.completed ? css.completed : "",
            isDragging ? css.dragging : "",
            isDragOver ? css.dragOver : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <div
              key={item.id}
              className={rowClass}
              draggable={editingId !== item.id}
              onDragStart={handleDragStart(index)}
              onDragOver={handleDragOver(index)}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop(index)}
              onDragEnd={handleDragEnd}
            >
              <span
                className={css.handle}
                title="Drag to reorder"
                aria-hidden
              >
                ⋮⋮
              </span>
              <input
                type="checkbox"
                className={css.checkbox}
                checked={item.completed}
                onChange={() => void handleToggle(item.id)}
              />
              {editingId === item.id ? (
                <input
                  ref={editingInputRef}
                  className={css.editInput}
                  value={editingText}
                  onChange={(e) => setEditingText(e.target.value)}
                  onBlur={() => void commitEdit()}
                  onKeyDown={handleEditKey}
                />
              ) : (
                <span
                  className={css.text}
                  onDoubleClick={() => startEditing(item.id, item.text)}
                  title="Double-click to edit"
                >
                  {item.text}
                </span>
              )}
              <button
                className={css.deleteButton}
                onClick={() => void handleRemove(item.id)}
                aria-label="Delete item"
              >
                ✕
              </button>
            </div>
          );
        })}
      </div>

      <form className={css.addForm} onSubmit={handleAddItem}>
        <input
          className={css.addInput}
          value={newItemText}
          onChange={(e) => setNewItemText(e.target.value)}
          placeholder="Add a todo..."
        />
        <button
          type="submit"
          className={css.addButton}
          disabled={!newItemText.trim()}
        >
          +
        </button>
      </form>
    </div>
  );
};
