# Blooming directed graph – repos as nodes, GitHub Actions interaction

Each repository under `~/projects` (except **data-structures**) is a **node** in a directed graph. Edges link each repo to **github_actions** (workflow runs). Ruby, Python, and TypeScript code in **src/** discover nodes and interact with the GitHub Actions API for each repo.

## Nodes

- **Projects dir:** `PROJECTS_DIR` (default `~/projects`).
- **Excluded:** `data-structures`.
- **Node:** name (dir name), path, owner/repo from `git remote get-url origin`.

## Edges

- Directed: each repo node → `github_actions` (when the repo has a GitHub remote).

## GitHub Actions API

All three implementations support:

- **List workflows** – `GET /repos/{owner}/{repo}/actions/workflows`
- **List workflow runs** – `GET /repos/{owner}/{repo}/actions/runs`
- **Trigger workflow_dispatch** – `POST /repos/{owner}/{repo}/actions/workflows/{id}/dispatches`

Set **GITHUB_TOKEN** (with `repo` and `actions` scope) for API calls.

## Running the code

### Ruby

```bash
cd /path/to/GlobPretect
export GITHUB_TOKEN=ghp_...
ruby src/ruby/blooming_graph.rb
```

Requires: Ruby stdlib (json, net/http, uri, shellwords).

### Python

```bash
cd /path/to/GlobPretect
export GITHUB_TOKEN=ghp_...
python3 src/python/blooming_graph.py
```

Requires: Python 3 (stdlib only: os, re, json, urllib.request, pathlib, subprocess).

### TypeScript / Node

```bash
cd /path/to/GlobPretect
export GITHUB_TOKEN=ghp_...
npx ts-node src/typescript/blooming-graph.ts
# or: node --loader ts-node/esm src/typescript/blooming-graph.ts
```

Requires: Node 18+ (fetch), ts-node. Or compile and run:

```bash
npx tsc --outDir dist src/typescript/blooming-graph.ts && node dist/blooming-graph.js
```

## File layout

- **src/ruby/blooming_graph.rb** – `BloomingDirectedGraph` class + CLI
- **src/python/blooming_graph.py** – `BloomingDirectedGraph` class + `main()`
- **src/typescript/blooming-graph.ts** – `BloomingDirectedGraph` class + `main()`

## Usage from code

- **Ruby:** `require_relative "blooming_graph"`; `g = BloomingDirectedGraph.new`; `g.each_repo_workflows { |name, owner, repo, list| ... }`
- **Python:** `from blooming_graph import BloomingDirectedGraph`; `g = BloomingDirectedGraph()`; `for name, owner, repo, list in g.each_repo_workflows(): ...`
- **TypeScript:** `import { BloomingDirectedGraph } from "./blooming-graph"`; `const g = new BloomingDirectedGraph()`; `for await (const [name, owner, repo, list] of g.eachRepoWorkflows()) { ... }`

## Context keys

The graph aligns with the 20 context keys (see **CONTEXT_KEYS.md**): keys with **github** imply action by the GitHub workflow agent; each repo’s workflows are the Actions entry point for that node.
