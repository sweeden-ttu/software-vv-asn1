/**
 * Trie node (LangChain). IEEE 752: counts/sizes use 64-bit.
 */
import Foundation

public final class TrieNode<T> {
    public let value: T
    public private(set) var children: [TrieNode<T>]

    public init(_ value: T, children: [TrieNode<T>] = []) {
        self.value = value
        self.children = children
    }

    public func addChild(_ node: TrieNode<T>) {
        children.append(node)
    }

    /// Number of nodes in subtrie (IEEE 752: Count = UInt64).
    public var subtrieCount: UInt64 {
        children.reduce(1) { $0 + $1.subtrieCount }
    }
}
