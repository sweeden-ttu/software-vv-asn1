import XCTest
@testable import DataStructuresIEEE752

final class TrieTests: XCTestCase {

    func testEmptyTrie() {
        let trie = Trie<String>(root: nil)
        XCTAssertTrue(trie.isEmpty)
        XCTAssertEqual(trie.size, 0)
    }

    func testTrieSize() {
        let root = TrieNode("a")
        root.addChild(TrieNode("b"))
        root.addChild(TrieNode("c"))
        let trie = Trie(root: root)
        XCTAssertFalse(trie.isEmpty)
        XCTAssertEqual(trie.size, 3)
    }
}
