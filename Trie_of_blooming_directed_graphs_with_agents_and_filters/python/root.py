"""
Root anchor: Trie_of_blooming_directed_graphs_with_agents_and_filters
Single entry point for blooming-directed-graph + filter_agents + trigger_process_agent per key.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TrieNodeValue:
    graph_ref: Any = None
    filter_agents_ref: Any = None
    trigger_process_agent_ref: Any = None


class TrieOfBloomingDirectedGraphsWithAgentsAndFilters:
    def __init__(self) -> None:
        self._children: dict[str, TrieOfBloomingDirectedGraphsWithAgentsAndFilters] = {}
        self._is_end = False
        self._value: Optional[TrieNodeValue] = None

    def insert(self, key: str, value: TrieNodeValue) -> None:
        if not key:
            self._is_end = True
            self._value = value
            return
        c = key[0]
        if c not in self._children:
            self._children[c] = TrieOfBloomingDirectedGraphsWithAgentsAndFilters()
        self._children[c].insert(key[1:], value)

    def get(self, key: str) -> Optional[TrieNodeValue]:
        if not key:
            return self._value if self._is_end else None
        c = key[0]
        child = self._children.get(c)
        return child.get(key[1:]) if child else None

    def starts_with(self, prefix: str) -> bool:
        if not prefix:
            return True
        c = prefix[0]
        child = self._children.get(c)
        return bool(child and child.starts_with(prefix[1:]))


# Global root anchor object (Trie_of_blooming_directed_graphs_with_agents_and_filters).
Trie_of_blooming_directed_graphs_with_agents_and_filters = TrieOfBloomingDirectedGraphsWithAgentsAndFilters()
