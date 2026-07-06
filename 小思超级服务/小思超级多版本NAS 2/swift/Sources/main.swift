import Foundation
import NIO
import NIOHTTP1

let configManager = ConfigManager.shared
let i18n = I18nManager.shared
let storageManager = StorageManager.shared
let userManager = UserManager.shared
let smbManager = SMBManager.shared
let pushManager = PushManager.shared

let group = MultiThreadedEventLoopGroup(numberOfThreads: System.coreCount)
let bootstrap = ServerBootstrap(group: group)
    .serverChannelOption(ChannelOptions.backlog, value: 256)
    .serverChannelOption(ChannelOptions.socket(SocketOptionLevel(SOL_SOCKET), SO_REUSEADDR), value: 1)
    .childChannelInitializer { channel in
        channel.pipeline.configureHTTPServerPipeline().flatMap { _ in
            channel.pipeline.addHandler(HTTPHandler())
        }
    }
    .childChannelOption(ChannelOptions.socket(IPPROTO_TCP, TCP_NODELAY), value: 1)

defer {
    try! group.syncShutdownGracefully()
}

let host = configManager.config.server.host
let port = configManager.config.server.port

print("🚀 小思NAS服务 (Swift) 启动中...")
print("📡 监听地址: http://\(host):\(port)")
print("🌍 支持语言: \(i18n.supportedLanguages.count) 种")
print("📁 数据目录: \(configManager.dataDir)")

let channel = try bootstrap.bind(host: host, port: port).wait()

try channel.closeFuture.wait()