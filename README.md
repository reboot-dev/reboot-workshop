# Welcome!

This is a starter repository for creating an app with Reboot!

This repository includes a devcontainer you can use instead of
installing necessary dependencies. Or launch a GitHub codespace:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/reboot-dev/reboot-workshop)

[Check out the docs!](https://docs.reboot.dev)

Steps to get started

```
curl -fsSL https://claude.ai/install.sh | bash
```

```
claude
```

```
`/plugin marketplace add reboot-dev/reboot-skills`
```

```
`/plugin install reboot-chat-app@reboot-skills`
```

```
`/reload-plugins`
```

1. You can also do the above few steps from outside claude.  
   a. `claude plugin marketplace add reboot-dev/reboot-skills`  
   a. `claude plugin install reboot-chat-app@reboot-skills`

To vibe-code the todo list:

```
/reboot-chat-app build a todo list app with drag-and-drop to reorder
```

In a new terminal

```
uv run rbt dev run
```

In a new terminal

```
cd web
npm install
npm run dev
```

In a new terminal

```
npx @mcpjam/inspector@2.4.0 –config mcp_server.json –server ai_chat_todo
```

In Claude:

```
Create a todo list with a well known ID like default-todo
and add a few todos that would be appropriate for a hackathon

```

then

```
Show me my todo list UI
```

# Branch: todo-list

After you've completed the above steps, you should have something that resebles what is in branch: `todo-list`.

Next claude prompt:

```
Create a workflow method called `research` that can be called by clicking a
button next to every todo item and have that `research` workflow use a Reboot
pydatnic_ai Agent which will research the todo list item and store what it gets
back as markdown for that todo list item and then add another UI where we can
see the research markdown for that todo list item. You can use
https://github.com/reboot-dev/reboot-agent-wiki for an example of creating an
Agent (specifically that project has a "librarian" agent). After you click the
research button for an item then you can no longer click it but the text should
flash while the research workflow is running and once the workflow is done then
it should change to the text `Completed` (clicking this button shows a drop
down of the research, clicking it again collapses the research).
```

# Branch: agent-todo-list

After running the prompt above, you should have something like what is in branch
`agent-todo-list`.
