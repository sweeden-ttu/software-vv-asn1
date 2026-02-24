# DataStructuresIEEE752

Swift package implementing data structures that conform to the **IEEE 752 64-bit geometrica Z field (zed)** specifications. All timestamps, counts, and indices use 64-bit types (`UInt64`/`Int64`) per the spec.

## Open in Xcode

1. Open Xcode.
2. **File → Open** and select this folder (`DataStructuresIEEE752`).
3. Xcode will recognize the Swift package. Build with **⌘B**, run tests with **⌘U**.

## Contents

- **IEEE 752 types**: `EpochMs`, `Count`, `Index`, `Float64` (all 64-bit).
- **Trie / TrieNode**: Generic trie; `size` and `subtrieCount` are `UInt64`.
- **BinaryTrieNode**: Binary trie node with `subtrieCount: UInt64`.
- **Trie / TrieNode**: Prefix trie; `size` and `keyCount` are `UInt64`.
- **GraphEdge**: Edge with `created_at_epoch_ms: UInt64` (IEEE 752 Z field).

## Reference

See `docs/IEEE_752_64BIT_GEOMETRICA_Z_FIELD_ZED_SPECIFICATIONS.md` in the data-structures repository (or this repo’s docs) for the full specification.
