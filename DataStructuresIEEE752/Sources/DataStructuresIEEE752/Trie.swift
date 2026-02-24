/**
 * Trie (prefix trie). IEEE 752: size as UInt64.
 */
import Foundation

public final class Trie<T> {
    public let root = TrieNode<T>()

    public init() {}

    public func insert(key: String, value: T) {
        var node: TrieNode<T> = root
        for char in key {
            if node.children[char] == nil {
                node.children[char] = TrieNode<T>()
            }
            node = node.children[char]!
        }
        node.value = value
    }

    public func get(key: String) -> T? {
        var node: TrieNode<T>? = root
        for char in key {
            node = node?.children[char]
            if node == nil { return nil }
        }
        return node?.value
    }

    /// Number of keys (IEEE 752: 64-bit).
    public var size: UInt64 {
        root.keyCount
    }
}
