# Trie_of_blooming_directed_graphs_with_agents_and_filters – root anchor

The **root anchor object** in this repo and across all 14 repositories and 12 languages is:

**`Trie_of_blooming_directed_graphs_with_agents_and_filters`**

It is a **Trie** (prefix trie) whose:
- **Keys** are repo names or context-key prefixes (e.g. `owner_hpcc`, `GlobPretect`).
- **Values** are references to a **blooming-directed-graph** node plus the **filter_agents** and **trigger_process_agent** for that node.

Everything else (blooming-directed-graph, filter agents, trigger process agent) hangs off this root. Each of the 12 languages and each of the 14 repositories exposes this same root anchor so that tooling and automation can assume a single entry point.

## 12 languages

| Language     | Root anchor location |
|-------------|----------------------|
| Swift       | `Trie_of_blooming_directed_graphs_with_agents_and_filters/swift/Root.swift` |
| Objective-C | `Trie_of_blooming_directed_graphs_with_agents_and_filters/objective-c/Root.h` |
| Ruby        | `Trie_of_blooming_directed_graphs_with_agents_and_filters/ruby/root.rb` |
| TypeScript  | `Trie_of_blooming_directed_graphs_with_agents_and_filters/typescript/root.ts` |
| Python      | `Trie_of_blooming_directed_graphs_with_agents_and_filters/python/root.py` |
| C#          | `Trie_of_blooming_directed_graphs_with_agents_and_filters/csharp/Root.cs` |
| Java        | `Trie_of_blooming_directed_graphs_with_agents_and_filters/java/Root.java` |
| Bash        | `Trie_of_blooming_directed_graphs_with_agents_and_filters/bash/root.sh` |
| Zsh         | `Trie_of_blooming_directed_graphs_with_agents_and_filters/zsh/root.zsh` |
| Git         | `Trie_of_blooming_directed_graphs_with_agents_and_filters/git/root.sh` |
| GitHub      | `Trie_of_blooming_directed_graphs_with_agents_and_filters/github/root.sh` |
| HPCC        | `Trie_of_blooming_directed_graphs_with_agents_and_filters/hpcc/root.sh` |

## 14 repositories

Each repository under `~/projects` (cryptography, CS5374_Software_VV, data-structures, GlobPretect, hpcc, langflow-ollama-podman, ollama-hpcc, ollama-mac, ollama-podman, ollama-rocky, OllamaHpcc, software-vv, software-vv-asn1, spring-2026) contains the same directory `Trie_of_blooming_directed_graphs_with_agents_and_filters/` with the 12 language implementations, so the root anchor is present in every repo.

## Usage

Load or source the root anchor for your language; then resolve keys (repo name or context prefix) to get the graph node, filter_agents, and trigger_process_agent for that key.
