# Actions: fetch_merge, push_merge, pull_merge

These three actions are defined **across all 14 repositories**, **all 12 languages** (Swift, Objective-C, Ruby, TypeScript, Python, C#, Java, Bash, Zsh, Git, GitHub, HPCC), and **all 4 environments** (the four Ollama model contexts: **granite**, **deepseek**, **qwen**, **codellama**).

| Action        | Description |
|---------------|-------------|
| **fetch_merge** | Git fetch from remote, then merge (e.g. `git fetch origin` then `git merge origin/<branch>`). Payload: `remote` (default `origin`), `branch` (default `main`). |
| **push_merge** | Optionally merge a branch into current, then push (e.g. `git merge <branch>` then `git push`). Payload: `remote`, `branch`. |
| **pull_merge** | Git pull (fetch + merge in one step). Payload: `remote`, `branch` (optional). |

They are invoked by the blooming_directed_graph_trigger_process_agent with action type `fetch_merge`, `push_merge`, or `pull_merge`. In each of the 4 environments (granite, deepseek, qwen, codellama), the same action names and semantics apply.
