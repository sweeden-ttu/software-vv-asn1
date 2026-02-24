// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "DataStructuresIEEE752",
    platforms: [.macOS(.v13), .iOS(.v16)],
    products: [
        .library(name: "DataStructuresIEEE752", targets: ["DataStructuresIEEE752"]),
    ],
    targets: [
        .target(
            name: "DataStructuresIEEE752",
            path: "Sources/DataStructuresIEEE752"
        ),
        .testTarget(
            name: "DataStructuresIEEE752Tests",
            dependencies: ["DataStructuresIEEE752"],
            path: "Tests/DataStructuresIEEE752Tests"
        ),
    ]
)
