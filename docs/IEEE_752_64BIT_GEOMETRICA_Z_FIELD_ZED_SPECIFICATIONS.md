# IEEE 752 64-bit geometrica Z field (zed) specifications

This document defines the **IEEE 752 64-bit geometrica Z field (zed)** specifications for the data-structures repository. All implementations across all languages and all repositories that consume or extend data-structures MUST follow these rules for numeric representation.

## 1. Scope

- **Z field (zed)**: The integer domain ℤ. All geometric, structural, and index-like numeric values that are integers MUST use fixed-width 64-bit integer representation where the schema or API specifies a numeric type.
- **64-bit**: All such integer fields use **64-bit** width (signed or unsigned as specified per field).
- **Geometrica**: Applies to geometric/structural uses: timestamps (epoch ms), counts, indices, sizes, dimensions, and any numeric identifier or ordinal used in graph/node/edge or trie structures.

## 2. Integer (Z field) rules

| Context | Type | Width | Notes |
|--------|------|-------|-------|
| Timestamps (epoch ms) | unsigned 64-bit | 64 | e.g. `created_at_epoch_ms` (uint64) |
| Counts, sizes, indices | signed or unsigned 64-bit | 64 | Use uint64 for non-negative; int64 when sign needed |
| Identity ordinals / slots | as in schema | e.g. hex 0x00..0x63 (0x64) | Global identity space cap remains per schema |

- **No 32-bit for geometric/count/timestamp fields**: Do not use 32-bit integer types for timestamp, count, index, or size fields in the geometrica Z field; use 64-bit.
- **Serialization**: In wire formats (Protobuf, JSON, Avro), use the 64-bit type (e.g. `uint64`, `int64`, `long`) as defined in the schema. In languages without native 64-bit types, use the widest available (e.g. 64-bit on 64-bit runtimes) and document any range limits.

## 3. Floating-point (when used)

Where floating-point is required (e.g. priorities, weights, metrics):

- Use **IEEE 754-2019** (or equivalent) **binary64** (64-bit double precision).
- Do not use 32-bit float for geometrica or structural numeric fields when 64-bit is available.

## 4. Language mapping (all implementations)

Implementations MUST follow this mapping for fields governed by the IEEE 752 64-bit geometrica Z field (zed) spec:

| Language / Platform | 64-bit unsigned (Z field) | 64-bit signed | 64-bit float (IEEE 754) |
|--------------------|---------------------------|---------------|--------------------------|
| **Swift** | `UInt64` | `Int64` | `Double` |
| **Objective-C** | `uint64_t` / `unsigned long long` | `int64_t` / `long long` | `double` |
| **Ruby** | `Integer` (Bignum as needed) | `Integer` | `Float` (64-bit on MRI) |
| **TypeScript** | `bigint` or number (range-documented) | `bigint` or number | `number` (IEEE 754 double) |
| **Python** | `int` (arbitrary precision; store/serialize as 64-bit where schema says so) | `int` | `float` (64-bit) |
| **C#** | `ulong` | `long` | `double` |
| **Java** | `long` (unsigned semantics via `Long.parseUnsignedLong` where needed) | `long` | `double` |
| **Bash / Zsh** | Integer arithmetic (64-bit when available) | Same | N/A or external tool |
| **Git / GitHub / HPCC** | Scripts: use 64-bit when invoking other langs or APIs | Same | N/A |

For scripting (Bash, Zsh, Git, GitHub, HPCC): when passing or storing numeric values that fall under the Z field (e.g. epoch ms), use 64-bit-capable tools or delegate to a language that implements this spec.

## 5. Schema compliance

- **Protobuf**: Use `uint64` / `int64` for timestamp, count, index, size fields (e.g. `created_at_epoch_ms: uint64`). No `uint32`/`int32` for such geometrica fields.
- **JSON Schema**: Use `"type": "integer"` with `"minimum"`/`"maximum"` or format hint for 64-bit range where applicable.
- **Avro**: Use `long` for 64-bit integers; `double` for 64-bit float.

## 6. References

- Gated Loopback Flower: `created_at_epoch_ms` is `uint64` (already compliant).
- Node identity hex space: `0x00..0x63` (0x64 slots) is separate from the 64-bit Z field; both apply.
- IEEE 754: ISO/IEC/IEEE 60559 (binary64) for double-precision floating-point when used.

All implementations in this repository and in consuming repositories (blooming-directed-graph agents, Trie root anchor, trigger process agent, filter agents) MUST follow the IEEE 752 64-bit geometrica Z field (zed) specifications above for any numeric field that represents timestamps, counts, indices, or sizes.
