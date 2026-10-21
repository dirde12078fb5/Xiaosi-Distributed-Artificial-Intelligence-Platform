// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "NAS",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(name: "nas-server", targets: ["NAS"])
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-nio.git", from: "2.62.0"),
        .package(url: "https://github.com/apple/swift-nio-http2.git", from: "1.28.0")
    ],
    targets: [
        .executableTarget(
            name: "NAS",
            dependencies: [
                .product(name: "NIO", package: "swift-nio"),
                .product(name: "NIOHTTP1", package: "swift-nio"),
                .product(name: "NIOFoundationCompat", package: "swift-nio")
            ],
            path: "Sources"
        )
    ]
)