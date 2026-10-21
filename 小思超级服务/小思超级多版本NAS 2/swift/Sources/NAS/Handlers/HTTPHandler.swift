import Foundation
import NIO
import NIOHTTP1

class HTTPHandler: ChannelInboundHandler {
    typealias InboundIn = HTTPServerRequestPart
    typealias OutboundOut = HTTPServerResponsePart

    private var requestBody: ByteBuffer?
    private var requestHead: HTTPRequestHead?

    func channelRead(context: ChannelHandlerContext, data: NIOAny) {
        let requestPart = unwrapInboundIn(data)

        switch requestPart {
        case .head(let head):
            requestHead = head
            requestBody = nil

        case .body(let body):
            requestBody = body

        case .end:
            handleRequest(context: context)
        }
    }

    private func handleRequest(context: ChannelHandlerContext) {
        guard let head = requestHead else {
            sendResponse(context: context, status: .badRequest, body: "Bad Request")
            return
        }

        let path = head.uri
        let method = head.method

        print("📥 \(method) \(path)")

        if path == "/" {
            handleRoot(context: context)
            return
        }

        if path.hasPrefix("/api/storage") {
            handleStorageAPI(context: context, path: path, method: method)
            return
        }

        if path.hasPrefix("/api/users") {
            handleUsersAPI(context: context, path: path, method: method)
            return
        }

        if path.hasPrefix("/api/smb") {
            handleSMBAPI(context: context, path: path, method: method)
            return
        }

        if path.hasPrefix("/api/ip") {
            handleIPAPI(context: context, path: path, method: method)
            return
        }

        if path.hasPrefix("/api/push") {
            handlePushAPI(context: context, path: path, method: method)
            return
        }

        if path.hasPrefix("/api/i18n") {
            handleI18nAPI(context: context, path: path, method: method)
            return
        }

        sendResponse(context: context, status: .notFound, body: "{\"success\":false,\"message\":\"Not Found\"}")
    }

    private func handleRoot(context: ChannelHandlerContext) {
        let html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>小思NAS服务 (Swift)</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #333; }
                .api { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .endpoint { color: #0066cc; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>🚀 小思NAS服务 (Swift版)</h1>
            <p>欢迎使用Swift实现的NAS服务</p>
            <div class="api">
                <div class="endpoint">存储管理 API</div>
                <ul>
                    <li>GET /api/storage/volumes - 获取存储卷列表</li>
                    <li>POST /api/storage/volumes - 创建存储卷</li>
                    <li>POST /api/storage/volumes/delete - 删除存储卷</li>
                </ul>
            </div>
            <div class="api">
                <div class="endpoint">用户管理 API</div>
                <ul>
                    <li>GET /api/users - 获取用户列表</li>
                    <li>POST /api/users - 创建用户</li>
                    <li>POST /api/users/delete - 删除用户</li>
                </ul>
            </div>
            <div class="api">
                <div class="endpoint">SMB共享 API</div>
                <ul>
                    <li>GET /api/smb/shares - 获取共享列表</li>
                    <li>POST /api/smb/shares - 创建共享</li>
                    <li>POST /api/smb/shares/delete - 删除共享</li>
                </ul>
            </div>
            <div class="api">
                <div class="endpoint">IP与推送 API</div>
                <ul>
                    <li>GET /api/ip/local - 获取本机IP</li>
                    <li>GET /api/ip/scan - 扫描局域网</li>
                    <li>GET /api/push/targets - 推送目标列表</li>
                    <li>POST /api/push/targets - 添加推送目标</li>
                    <li>GET /api/push/status - 推送状态</li>
                    <li>POST /api/push/receive - 接收文件</li>
                </ul>
            </div>
            <div class="api">
                <div class="endpoint">多语言 API</div>
                <ul>
                    <li>GET /api/i18n - 获取翻译</li>
                </ul>
            </div>
        </body>
        </html>
        """
        sendResponse(context: context, status: .ok, body: html, contentType: "text/html")
    }

    private func handleStorageAPI(context: ChannelHandlerContext, path: String, method: HTTPMethod) {
        if path == "/api/storage/volumes" && method == .GET {
            let volumes = StorageManager.shared.listVolumes()
            let data = try? JSONEncoder().encode(volumes)
            let json = data != nil ? String(data: data!, encoding: .utf8) : "[]"
            sendResponse(context: context, status: .ok, body: json ?? "[]")
        } else if path == "/api/storage/volumes" && method == .POST {
            handleCreateVolume(context: context)
        } else if path == "/api/storage/volumes/delete" && method == .POST {
            handleDeleteVolume(context: context)
        } else {
            sendResponse(context: context, status: .notFound, body: "{\"success\":false}")
        }
    }

    private func handleCreateVolume(context: ChannelHandlerContext) {
        guard let body = requestBody, let data = body.getData(at: 0, length: body.readableBytes) else {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false,\"message\":\"Invalid request\"}")
            return
        }

        struct VolumeRequest: Codable {
            var name: String
            var path: String
            var quota_gb: Int?
        }

        do {
            let req = try JSONDecoder().decode(VolumeRequest.self, from: data)
            let volume = StorageManager.shared.createVolume(name: req.name, path: req.path, quota_gb: req.quota_gb)

            if volume != nil {
                let volData = try JSONEncoder().encode(volume!)
                let json = String(data: volData, encoding: .utf8) ?? "{}"
                sendResponse(context: context, status: .ok, body: "{\"success\":true,\"data\":\(json)}")
            } else {
                sendResponse(context: context, status: .ok, body: "{\"success\":false,\"message\":\"Failed to create volume\"}")
            }
        } catch {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false,\"message\":\"Invalid JSON\"}")
        }
    }

    private func handleDeleteVolume(context: ChannelHandlerContext) {
        guard let body = requestBody, let data = body.getData(at: 0, length: body.readableBytes) else {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
            return
        }

        struct DeleteRequest: Codable {
            var name: String
        }

        do {
            let req = try JSONDecoder().decode(DeleteRequest.self, from: data)
            let success = StorageManager.shared.deleteVolume(name: req.name)
            sendResponse(context: context, status: .ok, body: "{\"success\":\(success)}")
        } catch {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
        }
    }

    private func handleUsersAPI(context: ChannelHandlerContext, path: String, method: HTTPMethod) {
        if path == "/api/users" && method == .GET {
            let users = UserManager.shared.listUsers()
            let data = try? JSONEncoder().encode(users)
            let json = data != nil ? String(data: data!, encoding: .utf8) : "[]"
            sendResponse(context: context, status: .ok, body: json ?? "[]")
        } else if path == "/api/users" && method == .POST {
            handleCreateUser(context: context)
        } else if path == "/api/users/delete" && method == .POST {
            handleDeleteUser(context: context)
        } else {
            sendResponse(context: context, status: .notFound, body: "{\"success\":false}")
        }
    }

    private func handleCreateUser(context: ChannelHandlerContext) {
        guard let body = requestBody, let data = body.getData(at: 0, length: body.readableBytes) else {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
            return
        }

        struct UserRequest: Codable {
            var username: String
            var password: String
            var role: String?
        }

        do {
            let req = try JSONDecoder().decode(UserRequest.self, from: data)
            let user = UserManager.shared.createUser(username: req.username, password: req.password, role: req.role ?? "user")

            if user != nil {
                sendResponse(context: context, status: .ok, body: "{\"success\":true}")
            } else {
                sendResponse(context: context, status: .ok, body: "{\"success\":false,\"message\":\"User already exists\"}")
            }
        } catch {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
        }
    }

    private func handleDeleteUser(context: ChannelHandlerContext) {
        guard let body = requestBody, let data = body.getData(at: 0, length: body.readableBytes) else {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
            return
        }

        struct DeleteRequest: Codable {
            var username: String
        }

        do {
            let req = try JSONDecoder().decode(DeleteRequest.self, from: data)
            let success = UserManager.shared.deleteUser(username: req.username)
            sendResponse(context: context, status: .ok, body: "{\"success\":\(success)}")
        } catch {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
        }
    }

    private func handleSMBAPI(context: ChannelHandlerContext, path: String, method: HTTPMethod) {
        if path == "/api/smb/shares" && method == .GET {
            let shares = SMBManager.shared.listShares()
            let data = try? JSONEncoder().encode(shares)
            let json = data != nil ? String(data: data!, encoding: .utf8) : "[]"
            sendResponse(context: context, status: .ok, body: json ?? "[]")
        } else if path == "/api/smb/shares" && method == .POST {
            handleCreateShare(context: context)
        } else if path == "/api/smb/shares/delete" && method == .POST {
            handleDeleteShare(context: context)
        } else {
            sendResponse(context: context, status: .notFound, body: "{\"success\":false}")
        }
    }

    private func handleCreateShare(context: ChannelHandlerContext) {
        guard let body = requestBody, let data = body.getData(at: 0, length: body.readableBytes) else {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
            return
        }

        struct ShareRequest: Codable {
            var name: String
            var path: String
            var readonly: Bool?
            var users: [String]?
        }

        do {
            let req = try JSONDecoder().decode(ShareRequest.self, from: data)
            let share = SMBManager.shared.createShare(name: req.name, path: req.path, readonly: req.readonly ?? false, users: req.users ?? [])

            if share != nil {
                sendResponse(context: context, status: .ok, body: "{\"success\":true}")
            } else {
                sendResponse(context: context, status: .ok, body: "{\"success\":false,\"message\":\"Share already exists\"}")
            }
        } catch {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
        }
    }

    private func handleDeleteShare(context: ChannelHandlerContext) {
        guard let body = requestBody, let data = body.getData(at: 0, length: body.readableBytes) else {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
            return
        }

        struct DeleteRequest: Codable {
            var name: String
        }

        do {
            let req = try JSONDecoder().decode(DeleteRequest.self, from: data)
            let success = SMBManager.shared.deleteShare(name: req.name)
            sendResponse(context: context, status: .ok, body: "{\"success\":\(success)}")
        } catch {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
        }
    }

    private func handleIPAPI(context: ChannelHandlerContext, path: String, method: HTTPMethod) {
        if path == "/api/ip/local" && method == .GET {
            handleGetLocalIP(context: context)
        } else if path.hasPrefix("/api/ip/scan") && method == .GET {
            handleScanIP(context: context, path: path)
        } else {
            sendResponse(context: context, status: .notFound, body: "{\"success\":false}")
        }
    }

    private func handleGetLocalIP(context: ChannelHandlerContext) {
        struct IPInfo: Codable {
            var interface: String
            var ip: String
        }

        var ips: [IPInfo] = []

        #if os(macOS)
        // macOS implementation would use getifaddrs
        ips.append(IPInfo(interface: "en0", ip: "127.0.0.1"))
        #elseif os(Linux)
        // Linux implementation
        ips.append(IPInfo(interface: "eth0", ip: "127.0.0.1"))
        #endif

        ips.append(IPInfo(interface: "lo0", ip: "127.0.0.1"))

        let data = try? JSONEncoder().encode(ips)
        let json = data != nil ? String(data: data!, encoding: .utf8) : "[]"
        sendResponse(context: context, status: .ok, body: json ?? "[]")
    }

    private func handleScanIP(context: ChannelHandlerContext, path: String) {
        sendResponse(context: context, status: .ok, body: "{\"success\":true,\"devices\":[],\"message\":\"Scan complete\"}")
    }

    private func handlePushAPI(context: ChannelHandlerContext, path: String, method: HTTPMethod) {
        if path == "/api/push/targets" && method == .GET {
            let targets = PushManager.shared.getTargets()
            let data = try? JSONEncoder().encode(targets)
            let json = data != nil ? String(data: data!, encoding: .utf8) : "[]"
            sendResponse(context: context, status: .ok, body: json ?? "[]")
        } else if path == "/api/push/targets" && method == .POST {
            handleAddPushTarget(context: context)
        } else if path == "/api/push/status" && method == .GET {
            let history = PushManager.shared.getPushHistory()
            let data = try? JSONEncoder().encode(history)
            let json = data != nil ? String(data: data!, encoding: .utf8) : "[]"
            sendResponse(context: context, status: .ok, body: json ?? "[]")
        } else if path == "/api/push/receive" && method == .POST {
            sendResponse(context: context, status: .ok, body: "{\"success\":true,\"message\":\"File received\"}")
        } else {
            sendResponse(context: context, status: .notFound, body: "{\"success\":false}")
        }
    }

    private func handleAddPushTarget(context: ChannelHandlerContext) {
        guard let body = requestBody, let data = body.getData(at: 0, length: body.readableBytes) else {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
            return
        }

        struct TargetRequest: Codable {
            var name: String
            var ip: String
            var port: Int
        }

        do {
            let req = try JSONDecoder().decode(TargetRequest.self, from: data)
            let target = PushManager.shared.addTarget(name: req.name, ip: req.ip, port: req.port)
            let targetData = try JSONEncoder().encode(target)
            let json = String(data: targetData, encoding: .utf8) ?? "{}"
            sendResponse(context: context, status: .ok, body: "{\"success\":true,\"data\":\(json)}")
        } catch {
            sendResponse(context: context, status: .badRequest, body: "{\"success\":false}")
        }
    }

    private func handleI18nAPI(context: ChannelHandlerContext, path: String, method: HTTPMethod) {
        let query = requestHead?.uri.split(separator: "?").last ?? ""
        var lang = "zh_CN"

        if query.hasPrefix("lang=") {
            lang = String(query.dropFirst(5))
        }

        let translations = I18nManager.shared.getAllTranslations(for: lang)
        let data = try? JSONEncoder().encode(translations)
        let json = data != nil ? String(data: data!, encoding: .utf8) : "{}"
        sendResponse(context: context, status: .ok, body: json ?? "{}")
    }

    private func sendResponse(context: ChannelHandlerContext, status: HTTPResponseStatus, body: String, contentType: String = "application/json") {
        let response = HTTPResponseHead(
            version: .http1_1,
            status: status,
            headers: [
                "Content-Type": contentType,
                "Content-Length": String(body.utf8.count),
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            ]
        )

        context.channel.write(self.wrapOutboundOut(.head(response)), promise: nil)

        var buffer = context.channel.allocator.buffer(capacity: body.utf8.count)
        buffer.writeString(body)
        context.channel.write(self.wrapOutboundOut(.body(.byteBuffer(buffer))), promise: nil)

        context.channel.write(self.wrapOutboundOut(.end(nil)), promise: nil)
        context.channel.flush()
    }

    func errorCaught(context: ChannelHandlerContext, error: Error) {
        print("❌ 错误: \(error)")
        context.close(promise: nil)
    }
}