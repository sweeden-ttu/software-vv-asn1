import XCTest
@testable import DataStructuresIEEE752

final class TrieTests: XCTestCase {

    func testTrieInsertGet() {
        let trie = Trie<String>()
        trie.insert(key: "key", value: "value")
        XCTAssertEqual(trie.get(key: "key"), "value")
        XCTAssertNil(trie.get(key: "k"))
        XCTAssertEqual(trie.size, 1)
    }

    func testTrieSize() {
        let trie = Trie<Int>()
        trie.insert(key: "a", value: 1)
        trie.insert(key: "ab", value: 2)
        XCTAssertEqual(trie.size, 2)
    }
}
