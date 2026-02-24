/**
 * Generic trie (LangChain). IEEE 752: size/count as UInt64.
 */
import Foundation

public struct Trie<T> {
    public let root: TrieNode<T>?

    public init(root: TrieNode<T>? = nil) {
        self.root = root
    }

    public var isEmpty: Bool { root == nil }

    /// Total node count (IEEE 752: 64-bit).
    public var size: UInt64 {
        root?.subtrieCount ?? 0
    }
}
