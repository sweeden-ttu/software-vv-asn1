// Root anchor: Trie_of_blooming_directed_graphs_with_agents_and_filters
// Single entry point for blooming-directed-graph + filter_agents + trigger_process_agent per key.

#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface TrieNodeValue : NSObject
@property (nonatomic, nullable) id graphRef;
@property (nonatomic, nullable) id filterAgentsRef;
@property (nonatomic, nullable) id triggerProcessAgentRef;
@end

@interface TrieOfBloomingDirectedGraphsWithAgentsAndFilters : NSObject
- (void)insertKey:(NSString *)key value:(TrieNodeValue *)value;
- (nullable TrieNodeValue *)get:(NSString *)key;
- (BOOL)startsWithPrefix:(NSString *)prefix;
@end

/// Global root anchor (Trie_of_blooming_directed_graphs_with_agents_and_filters).
FOUNDATION_EXPORT TrieOfBloomingDirectedGraphsWithAgentsAndFilters *Trie_of_blooming_directed_graphs_with_agents_and_filters(void);

NS_ASSUME_NONNULL_END
