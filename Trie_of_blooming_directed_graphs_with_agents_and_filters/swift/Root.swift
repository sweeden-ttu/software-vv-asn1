// Root anchor: Trie_of_blooming_directed_graphs_with_agents_and_filters
// Single entry point for blooming-directed-graph + filter_agents + trigger_process_agent per key.

import Foundation

/// Trie node holding a blooming-directed-graph reference plus agents and filters.
public struct TrieNodeValue {
    public var graphRef: Any?
    public var filterAgentsRef: Any?
    public var triggerProcessAgentRef: Any?
    public init(graphRef: Any? = nil, filterAgentsRef: Any? = nil, triggerProcessAgentRef: Any? = nil) {
        self.graphRef = graphRef
        self.filterAgentsRef = filterAgentsRef
        self.triggerProcessAgentRef = triggerProcessAgentRef
    }
}

/// Root anchor: Trie of blooming-directed-graphs with agents and filters (key = repo/context prefix).
public final class TrieOfBloomingDirectedGraphsWithAgentsAndFilters {
    private var children: [Character: TrieOfBloomingDirectedGraphsWithAgentsAndFilters] = [:]
    private var isEnd: Bool = false
    private var value: TrieNodeValue?

    public init() {}

    public func insert(key: String, value: TrieNodeValue) {
        var node: TrieOfBloomingDirectedGraphsWithAgentsAndFilters = self
        for char in key {
            if node.children[char] == nil {
                node.children[char] = TrieOfBloomingDirectedGraphsWithAgentsAndFilters()
            }
            node = node.children[char]!
        }
        node.isEnd = true
        node.value = value
    }

    public func get(key: String) -> TrieNodeValue? {
        var node: TrieOfBloomingDirectedGraphsWithAgentsAndFilters? = self
        for char in key {
            guard let next = node?.children[char] else { return nil }
            node = next
        }
        return node?.isEnd == true ? node?.value : nil
    }

    public func starts(with prefix: String) -> Bool {
        var node: TrieOfBloomingDirectedGraphsWithAgentsAndFilters? = self
        for char in prefix {
            guard let next = node?.children[char] else { return false }
            node = next
        }
        return true
    }
}

/// Global root anchor object (Trie_of_blooming_directed_graphs_with_agents_and_filters).
public let Trie_of_blooming_directed_graphs_with_agents_and_filters = TrieOfBloomingDirectedGraphsWithAgentsAndFilters()
