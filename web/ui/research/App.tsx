import { useMemo, type FC } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useTodoList } from "@api/ai_chat_todo/v1/todo_rbt_react";
import { useMcpToolData } from "@reboot-dev/reboot-react/internal";
import css from "./App.module.css";

const useItemIdFromRequest = (): string | null => {
  const toolData = useMcpToolData() as
    | Record<string, unknown>
    | null;
  return useMemo(() => {
    if (toolData) {
      const camel = toolData["itemId"];
      if (typeof camel === "string") return camel;
      const snake = toolData["item_id"];
      if (typeof snake === "string") return snake;
    }
    if (typeof window !== "undefined") {
      const urlItemId = new URLSearchParams(
        window.location.search,
      ).get("itemId");
      if (urlItemId) return urlItemId;
    }
    return null;
  }, [toolData]);
};

export const ShowResearchApp: FC = () => {
  const itemId = useItemIdFromRequest();
  const todoList = useTodoList();
  const { response, isLoading } = todoList.useGet();

  if (isLoading && response === undefined) {
    return (
      <div className={css.container}>
        <div className={css.loading}>loading...</div>
      </div>
    );
  }

  if (!itemId) {
    return (
      <div className={css.container}>
        <div className={css.empty}>
          No itemId provided to this view.
        </div>
      </div>
    );
  }

  const item = response?.items?.find((entry) => entry.id === itemId);

  if (!item) {
    return (
      <div className={css.container}>
        <div className={css.empty}>
          item not found in this list
        </div>
      </div>
    );
  }

  const status = item.researchStatus || "idle";
  const statusKey = status as "idle" | "running" | "completed";

  return (
    <div className={css.container}>
      <header className={css.header}>
        <div className={css.label}>Research</div>
        <div className={css.itemText}>{item.text}</div>
        <div
          className={`${css.statusBadge} ${css[`status_${statusKey}`] ?? ""}`}
        >
          {status}
        </div>
      </header>

      {status === "completed" && item.researchMarkdown ? (
        <article className={css.markdown}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {item.researchMarkdown}
          </ReactMarkdown>
        </article>
      ) : status === "running" ? (
        <div className={css.placeholder}>
          <span className={css.flashing}>researching…</span>
        </div>
      ) : (
        <div className={css.placeholder}>
          No research yet. Click the Research button on this
          item in the list, or call <code>start_research</code>{" "}
          on it.
        </div>
      )}
    </div>
  );
};
