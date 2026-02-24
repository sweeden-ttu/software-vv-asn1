// Root anchor: Trie_of_blooming_directed_graphs_with_agents_and_filters
// Single entry point for blooming-directed-graph + filter_agents + trigger_process_agent per key.

using System.Collections.Generic;

namespace TrieRootAnchor
{
    public class TrieNodeValue
    {
        public object? GraphRef { get; set; }
        public object? FilterAgentsRef { get; set; }
        public object? TriggerProcessAgentRef { get; set; }
    }

    public class TrieOfBloomingDirectedGraphsWithAgentsAndFilters
    {
        private readonly Dictionary<char, TrieOfBloomingDirectedGraphsWithAgentsAndFilters> _children = new();
        private bool _isEnd;
        private TrieNodeValue? _value;

        public void Insert(string key, TrieNodeValue value)
        {
            if (string.IsNullOrEmpty(key))
            {
                _isEnd = true;
                _value = value;
                return;
            }
            var c = key[0];
            if (!_children.TryGetValue(c, out var child))
            {
                child = new TrieOfBloomingDirectedGraphsWithAgentsAndFilters();
                _children[c] = child;
            }
            child.Insert(key.Substring(1), value);
        }

        public TrieNodeValue? Get(string key)
        {
            if (string.IsNullOrEmpty(key))
                return _isEnd ? _value : null;
            if (!_children.TryGetValue(key[0], out var child))
                return null;
            return child.Get(key.Substring(1));
        }

        public bool StartsWith(string prefix)
        {
            if (string.IsNullOrEmpty(prefix)) return true;
            if (!_children.TryGetValue(prefix[0], out var child))
                return false;
            return child.StartsWith(prefix.Substring(1));
        }
    }

    /// <summary>Global root anchor (Trie_of_blooming_directed_graphs_with_agents_and_filters).</summary>
    public static class Root
    {
        public static readonly TrieOfBloomingDirectedGraphsWithAgentsAndFilters Trie_of_blooming_directed_graphs_with_agents_and_filters =
            new TrieOfBloomingDirectedGraphsWithAgentsAndFilters();
    }
}
