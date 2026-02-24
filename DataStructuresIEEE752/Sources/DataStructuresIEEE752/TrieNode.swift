/**
 * Trie node (LangChain). IEEE 752: counts 64-bit.
 */
import Foundation

public final class TrieNode<T> {
    public var value: T?
    public var children: [Character: TrieNode<T>] = [:]

    public init(value: T? = nil) {
        self.value = value
    }

    /// Total number of keys in subtrie (IEEE 752: UInt64).
    public var keyCount: UInt64 {
        var n: UInt64 = value != nil ? 1 : 0
        for child in children.values {
            n += child.keyCount
        }
        return n
    }
}
