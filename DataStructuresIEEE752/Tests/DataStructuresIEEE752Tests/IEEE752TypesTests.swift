import XCTest
@testable import DataStructuresIEEE752

final class IEEE752TypesTests: XCTestCase {

    func testEpochMsIsUInt64() {
        let ms: EpochMs = 1_700_000_000_000
        XCTAssertEqual(ms, 1_700_000_000_000)
    }

    func testCountIsUInt64() {
        let c: Count = 100
        XCTAssertEqual(c, 100)
    }

    func testIndexIsInt64() {
        let i: Index = -1
        XCTAssertEqual(i, -1)
    }
}
