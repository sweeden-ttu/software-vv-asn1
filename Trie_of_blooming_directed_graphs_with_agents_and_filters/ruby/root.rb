# Root anchor: Trie_of_blooming_directed_graphs_with_agents_and_filters
# Single entry point for blooming-directed-graph + filter_agents + trigger_process_agent per key.

TrieNodeValue = Struct.new(:graph_ref, :filter_agents_ref, :trigger_process_agent_ref, keyword_init: true)

class TrieOfBloomingDirectedGraphsWithAgentsAndFilters
  def initialize
    @children = {}
    @is_end = false
    @value = nil
  end

  def insert(key, value)
    if key.empty?
      @is_end = true
      @value = value
      return
    end
    c = key[0]
    @children[c] ||= TrieOfBloomingDirectedGraphsWithAgentsAndFilters.new
    @children[c].insert(key[1..], value)
  end

  def get(key)
    if key.empty?
      return @is_end ? @value : nil
    end
    c = key[0]
    child = @children[c]
    child&.get(key[1..])
  end

  def starts_with?(prefix)
    return true if prefix.empty?
    c = prefix[0]
    child = @children[c]
    child&.starts_with?(prefix[1..]) || false
  end
end

# Global root anchor object (Trie_of_blooming_directed_graphs_with_agents_and_filters).
Trie_of_blooming_directed_graphs_with_agents_and_filters = TrieOfBloomingDirectedGraphsWithAgentsAndFilters.new
