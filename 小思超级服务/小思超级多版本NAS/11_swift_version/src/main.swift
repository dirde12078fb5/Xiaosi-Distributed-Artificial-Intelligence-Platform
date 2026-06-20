import Vapor
import JWT

// ==================== 数据模型 ====================

/// API统一响应结构体
struct ApiResponse<T: Content>: Content {
    let success: Bool
    var message: String? = nil
    var data: T? = nil
    
    init(success: Bool, message: String? = nil, data: T? = nil) {
        self.success = success
        self.message = message
        self.data = data
    }
}

/// 登录请求结构体
struct LoginRequest: Content {
    let username: String
    let password: String
}

/// 登录响应结构体
struct LoginResponse: Content {
    let token: String
    let user: UserInfo
}

/// 用户信息结构体
struct UserInfo: Content {
    let id: String
    let username: String
    let role: String
    let email: String
}

/// 文件项结构体
struct FileItem: Content {
    let id: String
    let name: String
    let type: String
    let size: Int64
    let modifiedAt: String
    let icon: String
    let owner: String
}

/// 用户列表项结构体
struct UserItem: Content {
    let id: String
    let username: String
    let email: String
    let role: String
    let storageQuota: Int64
    let status: String
    let lastLogin: String
}

/// 系统统计数据结构体
struct SystemStats: Content {
    let storage: StorageStats
    let files: FilesStats
    let users: UsersStats
}

/// 存储统计结构体
struct StorageStats: Content {
    let used: Int64
    let total: Int64
    let percentage: Double
}

/// 文件统计结构体
struct FilesStats: Content {
    let count: Int
    let recent: [RecentItem]
}

/// 最近活动项结构体
struct RecentItem: Content {
    let name: String
    let user: String
    let time: String
}

/// 用户统计结构体
struct UsersStats: Content {
    let total: Int
    let online: Int
}

/// 系统设置结构体
struct SystemSettings: Content {
    let general: GeneralSettings
    let network: NetworkSettings
}

/// 常规设置结构体
struct GeneralSettings: Content {
    let systemName: String
    let timezone: String
    let language: String
    let theme: String
}

/// 网络设置结构体
struct NetworkSettings: Content {
    let ip: String
    let port: Int
}

// ==================== JWT Payload ====================

/// JWT载荷结构体
struct XPayload: JWTPayload {
    enum CodingKeys: String, CodingKey {
        case subject = "sub"
        case username
        case role
        case expiration = "exp"
        case issuedAt = "iat"
    }
    
    let subject: SubjectClaim
    let username: String
    let role: String
    let expiration: ExpirationClaim
    let issuedAt: IssuedAtClaim
    
    func verify(using signer: some Signer) throws {
        try self.expiration.verifyNotExpired()
    }
}

// ==================== 用户数据模型 ====================

/// 用户数据模型 (内存存储)
class UserData {
    let id: String
    let username: String
    let email: String
    let passwordHash: String
    let role: String
    let storageQuota: Int64
    let createdAt: String
    var lastLogin: String
    
    init(id: String, username: String, email: String, passwordHash: String, 
         role: String, storageQuota: Int64, createdAt: String, lastLogin: String) {
        self.id = id
        self.username = username
        self.email = email
        self.passwordHash = passwordHash
        self.role = role
        self.storageQuota = storageQuota
        self.createdAt = createdAt
        self.lastLogin = lastLogin
    }
}

// ==================== 配置管理器 ====================

/// 应用配置管理器
class AppConfig {
    // 从环境变量加载配置，提供默认值
    static var port: Int {
        Environment.get("PORT").flatMap(Int.init) ?? 8080
    }
    
    static var host: String {
        Environment.get("HOST") ?? "0.0.0.0"
    }
    
    static var storagePath: String {
        Environment.get("STORAGE_PATH") ?? "./storage"
    }
    
    static var tempPath: String {
        Environment.get("TEMP_PATH") ?? "./temp"
    }
    
    static var jwtSecret: String {
        Environment.get("JWT_SECRET") ?? "xiaosi-super-nas-secret-key-2024-swift-vapor-must-be-long-enough-for-hs256"
    }
    
    static var jwtExpiryHours: Int {
        Environment.get("JWT_EXPIRY_HOURS").flatMap(Int.init) ?? 24
    }
    
    static var maxFileSize: Int64 {
        Environment.get("MAX_FILE_SIZE").flatMap(Int64.init) ?? (1024 * 1024 * 1024)
    }
    
    static var defaultUser: String {
        Environment.get("DEFAULT_USER") ?? "admin"
    }
    
    static var defaultPassword: String {
        Environment.get("DEFAULT_PASSWORD") ?? "admin123"
    }

    // 支持的文件类型图标映射
    static let fileIcons: [String: String] = [
        ".pdf": "📄", ".doc": "📝", ".docx": "📝",
        ".xls": "📊", ".xlsx": "📊", ".ppt": "📽️", ".pptx": "📽️",
        ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️", ".gif": "🖼️",
        ".mp4": "🎬", ".avi": "🎬", ".mp3": "🎵", ".wav": "🎵",
        ".zip": "📦", ".rar": "📦", ".7z": "📦",
        ".js": "💻", ".html": "💻", ".css": "💻", ".swift": "💻"
    ]
}

// ==================== 数据存储 ====================

/// 内存数据存储
class DataStore {
    static var users: [String: UserData] = [:]
    
    static func initialize() {
        // 创建存储目录
        let fileManager = FileManager.default
        try? fileManager.createDirectory(atPath: AppConfig.storagePath, 
                                          withIntermediateDirectories: true)
        try? fileManager.createDirectory(atPath: AppConfig.tempPath, 
                                          withIntermediateDirectories: true)

        // 初始化默认管理员用户
        users[AppConfig.defaultUser] = UserData(
            id: "default-admin-1",
            username: AppConfig.defaultUser,
            email: "admin@xiaosi.com",
            passwordHash: hashPassword(AppConfig.defaultPassword),
            role: "admin",
            storageQuota: 10 * 1024 * 1024 * 1024, // 10GB
            createdAt: ISO8601DateFormatter().string(from: Date()),
            lastLogin: ISO8601DateFormatter().string(from: Date())
        )

        // 初始化测试用户
        users["zhangsan"] = UserData(
            id: "sample-user-1",
            username: "zhangsan",
            email: "zhangsan@xiaosi.com",
            passwordHash: hashPassword("password"),
            role: "user",
            storageQuota: 1 * 1024 * 1024 * 1024, // 1GB
            createdAt: ISO8601DateFormatter().string(from: Date()),
            lastLogin: ISO8601DateFormatter().string(from: Date())
        )
    }
}

// ==================== 工具函数 ====================

/// 简单密码哈希函数 (生产环境应使用BCrypt等更安全的算法)
func hashPassword(_ password: String) -> String {
    guard let data = password.data(using: .utf8) else { return "" }
    let hashed = data.sha256()
    return hashed.compactMap { String(format: "%02x", $0) }.joined()
}

/// 验证密码
func verifyPassword(_ password: String, _ hash: String) -> Bool {
    return hashPassword(password) == hash
}

/// 获取文件图标
func getFileIcon(filename: String, isDirectory: Bool) -> String {
    if isDirectory { return "📁" }
    
    let ext = (filename as NSString).pathExtension.lowercased()
    return AppConfig.fileIcons[ext] ?? "📄"
}

/// 格式化文件大小
func formatFileSize(_ size: Int64) -> String {
    if size == 0 { return "0 Bytes" }
    
    let units = ["Bytes", "KB", "MB", "GB", "TB"]
    var fileSize = Double(size)
    var unitIndex = 0
    
    while fileSize >= 1024 && unitIndex < units.count - 1 {
        fileSize /= 1024
        unitIndex += 1
    }
    
    return String(format: "%.2f %@", fileSize, units[unitIndex])
}

/// 获取本机IP地址列表
func getLocalIps() -> [String] {
    var ips = ["127.0.0.1"]
    
    var ifaddr: UnsafeMutablePointer<ifaddrs>?
    guard getifaddrs(&ifaddr) == 0, let firstAddr = ifaddr else {
        return ips
    }
    defer { freeifaddrs(ifaddr) }
    
    var ptr = firstAddr
    while true {
        let interface = ptr.pointee
        let addrFamily = interface.ifa_addr.pointee.sa_family
        
        if addrFamily == UInt8(AF_INET) {
            let name = String(cString: interface.ifa_name)
            if name != "lo0" {
                var hostname = [CChar](repeating: 0, count: Int(NI_MAXHOST))
                getnameinfo(interface.ifa_addr, socklen_t(interface.ifa_addr.pointee.sa_len),
                           &hostname, socklen_t(hostname.count),
                           nil, 0, NI_NUMERICHOST)
                let ip = String(cString: hostname)
                if !ips.contains(ip) {
                    ips.append(ip)
                }
            }
        }
        
        guard let next = interface.ifa_next else { break }
        ptr = next
    }
    
    return ips
}

// ==================== 路由控制器 ====================

/// 认证路由控制器
class AuthController {
    
    /// 用户登录接口
    /// POST /api/auth/login
    /// 
    /// 请求体:
    /// {
    ///   "username": "admin",
    ///   "password": "admin123"
    /// }
    /// 
    /// 响应:
    /// {
    ///   "success": true,
    ///   "data": {
    ///     "token": "jwt_token_here",
    ///     "user": { ... }
    ///   }
    /// }
    func login(req: Request) async throws -> ApiResponse<LoginResponse> {
        do {
            let loginRequest = try req.content.decode(LoginRequest.self)
            
            guard let user = DataStore.users[loginRequest.username] else {
                throw Abort(.unauthorized, reason: "Invalid credentials")
            }
            
            guard verifyPassword(loginRequest.password, user.passwordHash) else {
                throw Abort(.unauthorized, reason: "Invalid credentials")
            }
            
            // 更新最后登录时间
            user.lastLogin = ISO8601DateFormatter().string(from: Date())

            // 生成JWT Token
            let payload = XPayload(
                subject: .init(value: user.id),
                username: user.username,
                role: user.role,
                expiration: .init(value: Date().addingTimeInterval(Double(AppConfig.jwtExpiryHours * 3600))),
                issuedAt: .init(value: Date())
            )
            
            let token = try req.jwt.sign(payload)
            
            return ApiResponse(
                success: true,
                data: LoginResponse(
                    token: token,
                    user: UserInfo(
                        id: user.id,
                        username: user.username,
                        role: user.role,
                        email: user.email
                    )
                )
            )
        } catch let error as AbortError {
            throw error
        } catch {
            throw Abort(.internalServerError, reason: error.localizedDescription)
        }
    }
}

/// 统计数据路由控制器
class StatsController {
    
    /// 获取系统统计信息
    /// GET /api/stats
    /// 返回存储使用情况、文件统计、用户统计等信息
    func getStats(req: Request) async throws -> ApiResponse<SystemStats> {
        let stats = SystemStats(
            storage: StorageStats(
                used: Int64(2.5 * 1024 * 1024 * 1024), // 2.5GB
                total: Int64(4 * 1024 * 1024 * 1024),   // 4GB
                percentage: 62.5
            ),
            files: FilesStats(
                count: 1284,
                recent: [
                    RecentItem(name: "项目报告.pdf", user: "admin", time: "5分钟前"),
                    RecentItem(name: "新用户注册", user: "system", time: "15分钟前")
                ]
            ),
            users: UsersStats(
                total: DataStore.users.count,
                online: 2
            )
        )
        
        return ApiResponse(data: stats, success: true)
    }
}

/// 文件管理路由控制器
class FilesController {
    
    /// 获取文件列表
    /// GET /api/files?path=/
    /// 查询参数:
    /// - path: 文件路径 (默认为根目录 "/")
    /// 返回指定路径下的文件和文件夹列表
    func getFiles(req: Request) async throws -> ApiResponse<[FileItem]> {
        let path = req.query[String.self, at: "path"] ?? "/"
        let targetPath = "\(AppConfig.storagePath)\(path)"
        
        var files: [FileItem] = []
        let fileManager = FileManager.default
        
        if fileManager.fileExists(atPath: targetPath) {
            var isDir: ObjCBool = false
            fileManager.fileExists(atPath: targetPath, isDirectory: &isDir)
            
            if isDir.boolValue {
                if let contents = try? fileManager.contentsOfDirectory(atPath: targetPath) {
                    for item in contents.sorted() {
                        let itemPath = "\(targetPath)/\(item)"
                        var attributes: [FileAttributeKey: Any]? = nil
                        
                        do {
                            attributes = try fileManager.attributesOfItem(atPath: itemPath)
                        } catch {
                            continue
                        }
                        
                        guard let attrs = attributes else { continue }
                        
                        let fileType = attrs[.type] as? FileAttributeType
                        let isDirectory = fileType == .directory
                        let size = (attrs[.size] as? Int64) ?? 0
                        let modDate = (attrs[.modificationDate] as? Date) ?? Date()
                        
                        files.append(FileItem(
                            id: "\(modDate.timeIntervalSince1970)",
                            name: item,
                            type: isDirectory ? "folder" : "file",
                            size: size,
                            modifiedAt: ISO8601DateFormatter().string(from: modDate),
                            icon: getFileIcon(filename: item, isDirectory: isDirectory),
                            owner: "admin"
                        ))
                    }
                }
            }
        }
        
        // 如果目录为空，返回示例数据
        if files.isEmpty {
            let now = ISO8601DateFormatter().string(from: Date())
            files = [
                FileItem(id: "1", name: "项目文档", type: "folder", size: 0, 
                        modifiedAt: now, icon: "📁", owner: "admin"),
                FileItem(id: "2", name: "照片备份", type: "folder", size: 0, 
                        modifiedAt: now, icon: "📁", owner: "admin"),
                FileItem(id: "3", name: "项目报告.pdf", type: "file", size: 2621440, 
                        modifiedAt: now, icon: "📄", owner: "admin")
            ]
        }
        
        return ApiResponse(data: files, success: true)
    }
    
    /// 上传文件
    /// POST /api/files/upload?path=/
    /// 查询参数:
    /// - path: 目标路径 (默认为根目录 "/")
    /// 请求体: multipart/form-data
    func uploadFiles(req: Request) async throws -> ApiResponse<[FileItem]> {
        let path = req.query[String.self, at: "path"] ?? "/"
        let targetPath = "\(AppConfig.storagePath)\(path)"
        
        // 创建目标目录
        let fileManager = FileManager.default
        try? fileManager.createDirectory(atPath: targetPath, withIntermediateDirectories: true)
        
        // 处理上传的文件
        var uploadedFiles: [FileItem] = []
        
        for try await file in req.body.files {
            let filename = file.filename ?? "unknown"
            let filePath = "\(targetPath)/\(filename)"
            
            try file.data.write(to: URL(fileURLWithPath: filePath))
            
            let attributes = try? fileManager.attributesOfItem(atPath: filePath)
            let size = (attributes?[.size] as? Int64) ?? 0
            
            uploadedFiles.append(FileItem(
                id: "\(Int(Date().timeIntervalSince1970))",
                name: filename,
                type: "file",
                size: size,
                modifiedAt: ISO8601DateFormatter().string(from: Date()),
                icon: getFileIcon(filename: filename, isDirectory: false),
                owner: "admin"
            ))
        }
        
        return ApiResponse(
            success: true,
            message: "成功上传 \(uploadedFiles.count) 个文件",
            data: uploadedFiles
        )
    }
    
    /// 创建文件夹
    /// POST /api/files/folder
    /// 请求体:
    /// {
    ///   "name": "新建文件夹",
    ///   "path": "/"
    /// }
    func createFolder(req: Request) async throws -> ApiResponse<[String: String]> {
        struct FolderRequest: Content {
            let name: String
            let path: String?
        }
        
        let folderRequest = try req.content.decode(FolderRequest.self)
        let name = folderRequest.name.trimmingCharacters(in: .whitespacesAndNewlines)
        let path = folderRequest.path ?? "/"
        
        guard !name.isEmpty else {
            throw Abort(.badRequest, reason: "Folder name is required")
        }
        
        let targetPath = "\(AppConfig.storagePath)\(path)/\(name)"
        let fileManager = FileManager.default
        
        guard !fileManager.fileExists(atPath: targetPath) else {
            throw Abort(.badRequest, reason: "Folder already exists")
        }
        
        try fileManager.createDirectory(atPath: targetPath, withIntermediateDirectories: true)
        
        return ApiResponse(
            success: true,
            message: "Folder created successfully",
            data: ["name": name, "type": "folder", "path": path]
        )
    }
}

/// 用户管理路由控制器
class UsersController {
    
    /// 获取用户列表
    /// GET /api/users
    /// 返回系统中所有用户的列表，包含状态信息
    func getUsers(req: Request) async throws -> ApiResponse<[UserItem]> {
        let userList = DataStore.users.values.map { user -> UserItem in
            let dateFormatter = ISO8601DateFormatter()
            guard let lastLoginDate = dateFormatter.date(from: user.lastLogin) else {
                return UserItem(
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    role: user.role,
                    storageQuota: user.storageQuota,
                    status: "offline",
                    lastLogin: user.lastLogin
                )
            }
            
            let timeInterval = Date().timeIntervalSince(lastLoginDate)
            let status = timeInterval < 3600 ? "online" : "offline"
            
            return UserItem(
                id: user.id,
                username: user.username,
                email: user.email,
                role: user.role,
                storageQuota: user.storageQuota,
                status: status,
                lastLogin: user.lastLogin
            )
        }
        
        return ApiResponse(data: userList, success: true)
    }
}

/// 系统设置路由控制器
class SettingsController {
    
    /// 获取系统设置
    /// GET /api/settings
    /// 返回系统配置信息，包括常规设置和网络设置
    func getSettings(req: Request) async throws -> ApiResponse<SystemSettings> {
        let settings = SystemSettings(
            general: GeneralSettings(
                systemName: "小思超级NAS",
                timezone: "Asia/Shanghai",
                language: "zh-CN",
                theme: "dark"
            ),
            network: NetworkSettings(
                ip: AppConfig.host,
                port: AppConfig.port
            )
        )
        
        return ApiResponse(data: settings, success: true)
    }
}

// ==================== 应用入口 ====================
/// 配置并启动Vapor应用
func configure(_ app: Application) throws {
    // 初始化数据存储
    DataStore.initialize()
    
    // 注册路由
    app.routes.grouped([
        // 这里可以添加中间件，如CORS、日志等
    ]).group("api") { api in
        
        // 公开路由 (无需认证)
        let authController = AuthController()
        authController.login.route(on: api.grouped("auth"))
        
        // 受保护的路由 (需要JWT认证)
        let protected = api.grouped(
            JWTAuthenticator<XPayload>()
        )
        
        // 统计数据路由
        let statsController = StatsController()
        statsController.getStats.route(on: protected.grouped("stats"))
        
        // 文件管理路由
        let filesController = FilesController()
        filesController.getFiles.route(on: protected.grouped("files"))
        filesController.uploadFiles.route(on: protected.grouped("files", "upload"))
        filesController.createFolder.route(on: protected.grouped("files", "folder"))
        
        // 用户管理路由
        let usersController = UsersController()
        usersController.getUsers.route(on: protected.grouped("users"))
        
        // 系统设置路由
        let settingsController = SettingsController()
        settingsController.getSettings.route(on: protected.grouped("settings"))
    }
    
    // 首页重定向
    app.get { req in
        req.redirect(to: "/index.html")
    }
}

// ==================== 主入口点 ====================
@main
enum Entry {
    static func main() async throws {
        var env = try Environment.detect()
        try LoggingSystem.bootstrap(from: &env)
        
        let app = Application(env)
        defer { app.shutdown() }
        
        try configure(app)
        
        // 打印启动信息
        printStartupInfo(port: AppConfig.port)
        
        try await app.execute()
    }
}

/// 打印服务器启动信息
func printStartupInfo(port: Int) {
    print(String(repeating: "=", count: 60))
    print("  🚀 小思超级NAS (Swift/Vapor版本) 已启动！")
    print(String(repeating: "=", count: 60))
    print()
    print("📡 访问地址：")
    print("   本地访问：http://localhost:\(port)")
    
    let localIps = getLocalIps()
    for ip in localIps {
        if ip != "127.0.0.1" {
            print("   局域网访问：http://\(ip):\(port)")
        }
    }
    
    print()
    print("👤 默认登录：")
    print("   用户名：\(AppConfig.defaultUser)")
    print("   密码：\(AppConfig.defaultPassword)")
    print()
    print(String(repeating: "=", count: 60))
    print()
}
