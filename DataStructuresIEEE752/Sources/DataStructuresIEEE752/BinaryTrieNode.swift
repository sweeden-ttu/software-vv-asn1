/**
 * Binary trie node (LangChain). IEEE 752: indices/counts 64-bit.
 */
import Foundation

public final class BinaryTrieNode<T> {
    public var value: T
    public var left: BinaryTrieNode<T>?
    public var right: BinaryTrieNode<T>?

    public init(_ value: T, left: BinaryTrieNode<T>? = nil, right: BinaryTrieNode<T>? = nil) {
        self.value = value
        self.left = left
        self.right = right
    }

    /// Subtrie size (IEEE 752: Count = UInt64).
    public var subtrieCount: UInt64 {
        1 + (left?.subtrieCount ?? 0) + (right?.subtrieCount ?? 0)
    }
}
