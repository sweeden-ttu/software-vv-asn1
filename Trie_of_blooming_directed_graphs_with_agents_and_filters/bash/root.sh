# Root anchor: Trie_of_blooming_directed_graphs_with_agents_and_filters
# Single entry point for blooming-directed-graph + filter_agents + trigger_process_agent per key.
# Source this file to get Trie_of_blooming_directed_graphs_with_agents_and_filters_* functions.

declare -g -A _trie_bdgaf_children
declare -g _trie_bdgaf_keys

_trie_bdgaf_keys=()

_trie_of_blooming_directed_graphs_with_agents_and_filters_insert() {
  local key="$1" graph_ref="$2" filter_ref="$3" trigger_ref="$4"
  _trie_bdgaf_keys+=("$key")
  _trie_bdgaf_children["${key}:graph"]="$graph_ref"
  _trie_bdgaf_children["${key}:filter"]="$filter_ref"
  _trie_bdgaf_children["${key}:trigger"]="$trigger_ref"
}

_trie_of_blooming_directed_graphs_with_agents_and_filters_get() {
  local key="$1"
  echo "${_trie_bdgaf_children[${key}:graph]:-}"
  echo "${_trie_bdgaf_children[${key}:filter]:-}"
  echo "${_trie_bdgaf_children[${key}:trigger]:-}"
}

_trie_of_blooming_directed_graphs_with_agents_and_filters_starts_with() {
  local prefix="$1" k
  for k in "${_trie_bdgaf_keys[@]}"; do
    [[ "$k" == "$prefix"* ]] && return 0
  done
  return 1
}

# Root anchor name (Trie_of_blooming_directed_graphs_with_agents_and_filters) – use the functions above.
export Trie_of_blooming_directed_graphs_with_agents_and_filters_root=1
