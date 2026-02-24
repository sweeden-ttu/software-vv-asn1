import XCTest
@testable import DataStructuresIEEE752

final class GraphEdgeTests: XCTestCase {

    func testGraphEdgeIEEE752Timestamp() {
        let ms: UInt64 = 1_700_000_000_000
        let edge = GraphEdge(
            edgeId: "e1",
            fromNodeId: "n1",
            toNodeId: "n2",
            created_at_epoch_ms: ms
        )
        XCTAssertEqual(edge.created_at_epoch_ms, ms)
        XCTAssertEqual(edge.fromNodeId, "n1")
    }
}
