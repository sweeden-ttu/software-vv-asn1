/**
 * Graph edge with IEEE 752 timestamp (created_at_epoch_ms: UInt64).
 */
import Foundation

public struct GraphEdge {
    public let edgeId: String
    public let fromNodeId: String
    public let toNodeId: String
    /// IEEE 752 64-bit Z field (zed): epoch milliseconds.
    public let created_at_epoch_ms: UInt64

    public init(edgeId: String, fromNodeId: String, toNodeId: String, created_at_epoch_ms: UInt64) {
        self.edgeId = edgeId
        self.fromNodeId = fromNodeId
        self.toNodeId = toNodeId
        self.created_at_epoch_ms = created_at_epoch_ms
    }
}
