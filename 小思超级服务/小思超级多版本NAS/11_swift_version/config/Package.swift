// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "XiaosiNAS",
    platforms: [
        .macOS(.v13)
    ],
    dependencies: [
        // Vapor Web框架依赖
        .package(url: "https://github.com/vapor/vapor.git", from: "4.89.0"),
        // JWT认证库
        .package(url: "https://github.com/vapor/jwt.git", from: "4.6.0"),
        // JWT密钥库 (用于生成和验证JWT)
        .package(url: "https://github.com/vapor/jwt-kit.git", from: "4.13.0"),
    ],
    targets: [
        .executableTarget(
            name: "XiaosiNAS",
            dependencies: [
                .product(name: "Vapor", package: "vapor"),
                .product(name: "JWT", package: "jwt"),
                .product(name: "JWTKit", package: "jwt-kit"),
            ],
            path: "src",
            swiftSettings: [
                // 启用并发功能
                .enableUpcomingFeature("StrictConcurrency"),
                // 设置语言版本
                .swiftLanguageMode(.v5)
            ]
        ),
        .testTarget(
            name: "XiaosiNASTests",
            dependencies: [
                .target(name: "XiaosiNAS"),
                .product(name: "XCTVaporTesting", package: "vapor"),
            ],
            path: "tests"
        )
    ]
)

// 包配置信息
let products = [
    .executable(
        name: "XiaosiNAS",
        targets: ["XiaosiNAS"]
    )
]

// Swift编译器设置
let swiftSettings: [SwiftSetting] = [
    .unsafeFlags(["-cross-module-optimization"], .when(configuration: .release)),
]
