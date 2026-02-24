#import "Root.h"

@implementation TrieNodeValue
@end

@interface TrieOfBloomingDirectedGraphsWithAgentsAndFilters ()
@property (nonatomic) NSMutableDictionary<NSString *, TrieOfBloomingDirectedGraphsWithAgentsAndFilters *> *children;
@property (nonatomic) BOOL isEnd;
@property (nonatomic, nullable) TrieNodeValue *value;
@end

@implementation TrieOfBloomingDirectedGraphsWithAgentsAndFilters

- (instancetype)init {
    if (self = [super init]) {
        _children = [NSMutableDictionary dictionary];
        _isEnd = NO;
        _value = nil;
    }
    return self;
}

- (void)insertKey:(NSString *)key value:(TrieNodeValue *)value {
    if (key.length == 0) {
        self.isEnd = YES;
        self.value = value;
        return;
    }
    NSString *first = [key substringToIndex:1];
    TrieOfBloomingDirectedGraphsWithAgentsAndFilters *child = self.children[first];
    if (!child) {
        child = [[TrieOfBloomingDirectedGraphsWithAgentsAndFilters alloc] init];
        self.children[first] = child;
    }
    [child insertKey:[key substringFromIndex:1] value:value];
}

- (TrieNodeValue *)get:(NSString *)key {
    if (key.length == 0)
        return self.isEnd ? self.value : nil;
    NSString *first = [key substringToIndex:1];
    TrieOfBloomingDirectedGraphsWithAgentsAndFilters *child = self.children[first];
    return [child get:[key substringFromIndex:1]];
}

- (BOOL)startsWithPrefix:(NSString *)prefix {
    if (prefix.length == 0) return YES;
    NSString *first = [prefix substringToIndex:1];
    TrieOfBloomingDirectedGraphsWithAgentsAndFilters *child = self.children[first];
    return child ? [child startsWithPrefix:[prefix substringFromIndex:1]] : NO;
}

@end

static TrieOfBloomingDirectedGraphsWithAgentsAndFilters *_rootAnchor;

TrieOfBloomingDirectedGraphsWithAgentsAndFilters *Trie_of_blooming_directed_graphs_with_agents_and_filters(void) {
    static dispatch_once_t once;
    dispatch_once(&once, ^{
        _rootAnchor = [[TrieOfBloomingDirectedGraphsWithAgentsAndFilters alloc] init];
    });
    return _rootAnchor;
}
