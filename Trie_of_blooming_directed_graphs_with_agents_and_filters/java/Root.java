package rootanchor;

import java.util.HashMap;
import java.util.Map;

/**
 * Root anchor: Trie_of_blooming_directed_graphs_with_agents_and_filters
 * Single entry point for blooming-directed-graph + filter_agents + trigger_process_agent per key.
 */
public final class Root {

    public static final class TrieNodeValue {
        public Object graphRef;
        public Object filterAgentsRef;
        public Object triggerProcessAgentRef;
    }

    public static final class TrieOfBloomingDirectedGraphsWithAgentsAndFilters {
        private final Map<Character, TrieOfBloomingDirectedGraphsWithAgentsAndFilters> children = new HashMap<>();
        private boolean isEnd;
        private TrieNodeValue value;

        public void insert(String key, TrieNodeValue val) {
            if (key == null || key.isEmpty()) {
                isEnd = true;
                value = val;
                return;
            }
            char c = key.charAt(0);
            children.computeIfAbsent(c, k -> new TrieOfBloomingDirectedGraphsWithAgentsAndFilters())
                    .insert(key.substring(1), val);
        }

        public TrieNodeValue get(String key) {
            if (key == null || key.isEmpty())
                return isEnd ? value : null;
            TrieOfBloomingDirectedGraphsWithAgentsAndFilters child = children.get(key.charAt(0));
            return child != null ? child.get(key.substring(1)) : null;
        }

        public boolean startsWith(String prefix) {
            if (prefix == null || prefix.isEmpty()) return true;
            TrieOfBloomingDirectedGraphsWithAgentsAndFilters child = children.get(prefix.charAt(0));
            return child != null && child.startsWith(prefix.substring(1));
        }
    }

    /** Global root anchor (Trie_of_blooming_directed_graphs_with_agents_and_filters). */
    public static final TrieOfBloomingDirectedGraphsWithAgentsAndFilters Trie_of_blooming_directed_graphs_with_agents_and_filters =
            new TrieOfBloomingDirectedGraphsWithAgentsAndFilters();

    private Root() {}
}
