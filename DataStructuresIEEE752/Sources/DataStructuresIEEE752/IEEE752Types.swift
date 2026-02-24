/**
 * IEEE 752 64-bit geometrica Z field (zed) types.
 * Timestamps, counts, indices use UInt64/Int64 per spec.
 */
import Foundation

/// Timestamp in epoch milliseconds (IEEE 752: unsigned 64-bit).
public typealias EpochMs = UInt64

/// Count or size (IEEE 752: 64-bit; use UInt64 for non-negative).
public typealias Count = UInt64

/// Index or ordinal (IEEE 752: 64-bit signed when sign needed).
public typealias Index = Int64

/// 64-bit float per IEEE 754 when used for geometrica/structural values.
public typealias Float64 = Double
