/**
 * Root anchor: Trie_of_blooming_directed_graphs_with_agents_and_filters
 * Single entry point for blooming-directed-graph + filter_agents + trigger_process_agent per key.
 */

export interface TrieNodeValue {
  graphRef?: unknown;
  filterAgentsRef?: unknown;
  triggerProcessAgentRef?: unknown;
}

class TrieOfBloomingDirectedGraphsWithAgentsAndFilters {
  private children: Map<string, TrieOfBloomingDirectedGraphsWithAgentsAndFilters> = new Map();
  private isEnd = false;
  private value: TrieNodeValue | null = null;

  insert(key: string, value: TrieNodeValue): void {
    if (key === '') {
      this.isEnd = true;
      this.value = value;
      return;
    }
    const c = key[0];
    if (!this.children.has(c)) {
      this.children.set(c, new TrieOfBloomingDirectedGraphsWithAgentsAndFilters());
    }
    this.children.get(c)!.insert(key.slice(1), value);
  }

  get(key: string): TrieNodeValue | null {
    if (key === '') {
      return this.isEnd ? this.value : null;
    }
    const c = key[0];
    const child = this.children.get(c);
    return child ? child.get(key.slice(1)) : null;
  }

  startsWith(prefix: string): boolean {
    if (prefix === '') return true;
    const c = prefix[0];
    const child = this.children.get(c);
    return child ? child.startsWith(prefix.slice(1)) : false;
  }
}

/** Global root anchor object (Trie_of_blooming_directed_graphs_with_agents_and_filters). */
export const Trie_of_blooming_directed_graphs_with_agents_and_filters =
  new TrieOfBloomingDirectedGraphsWithAgentsAndFilters();
