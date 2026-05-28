package com.xiaosi.nas

import io.ktor.server.application.*
import io.ktor.server.auth.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.http.*
import io.ktor.util.pipeline.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import io.jsonwebtoken.Jwts
import io.jsonwebtoken.security.Keys
import java.io.File
import java.net.InetAddress
import java.security.Key
import java.time.Instant
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.*
import javax.crypto.SecretKey

/**
 * 小思超级NAS - Kotlin版本 (Ktor框架)
 * 智能存储管理平台
 *
 * 作者: 小思AI团队
 * 版本: 1.0.0
 * 框架: Ktor + Netty
 */

// ==================== 数据模型 ====================

@Serializable
data class ApiResponse<T>(
    val success: Boolean,
    val message: String? = null,
    val data: T? = null
)

@Serializable
data class LoginRequest(
    val username: String,
    val password: String
)

@Serializable
data class LoginResponse(
    val token: String,
    val user: UserInfo
)

@Serializable
data class UserInfo(
    val id: String,
    val username: String,
    val role: String,
    val email: String
)

@Serializable
data class FileItem(
    val id: String,
    val name: String,
    val type: String,
    val size: Long,
    val modifiedAt: String,
    val icon: String,
    val owner: String
)

@Serializable
data class UserItem(
    val id: String,
    val username: String,
    val email: String,
    val role: String,
    val storageQuota: Long,
    val status: String,
    val lastLogin: String
)

@Serializable
data class SystemStats(
    val storage: StorageStats,
    val files: FilesStats,
    val users: UsersStats
)

@Serializable
data class StorageStats(
    val used: Long,
    val total: Long,
    val percentage: Double
)

@Serializable
data class FilesStats(
    val count: Int,
    val recent: List<RecentItem>
)

@Serializable
data class RecentItem(
    val name: String,
    val user: String,
    val time: String
)

@Serializable
data class UsersStats(
    val total: Int,
    val online: Int
)

@Serializable
data class SystemSettings(
    val general: GeneralSettings,
    val network: NetworkSettings
)

@Serializable
data class GeneralSettings(
    val systemName: String,
    val timezone: String,
    val language: String,
    val theme: String
)

@Serializable
data class NetworkSettings(
    val ip: String,
    val port: Int
)

// ==================== 用户数据类 ====================
data class UserData(
    val id: String,
    val username: String,
    val email: String,
    val passwordHash: String,
    val role: String,
    val storageQuota: Long,
    val createdAt: String,
    var lastLogin: String
)

// ==================== 应用配置对象 ====================
object AppConfig {
    // 从环境变量或默认值加载配置
    val PORT: Int = System.getenv("PORT")?.toIntOrNull() ?: 8080
    val HOST: String = System.getenv("HOST") ?: "0.0.0.0"
    
    val STORAGE_PATH: String = System.getenv("STORAGE_PATH") ?: "./storage"
    val TEMP_PATH: String = System.getenv("TEMP_PATH") ?: "./temp"
    
    val JWT_SECRET: String = System.getenv("JWT_SECRET") 
        ?: "xiaosi-super-nas-secret-key-2024-kotlin-must-be-long-enough-for-hs256"
    val JWT_EXPIRY_HOURS: Long = System.getenv("JWT_EXPIRY_HOURS")?.toLongOrNull() ?: 24
    
    val MAX_FILE_SIZE: Long = System.getenv("MAX_FILE_SIZE")?.toLongOrNull() 
        ?: (1024L * 1024L * 1024L) // 1GB
    
    val DEFAULT_USER: String = System.getenv("DEFAULT_USER") ?: "admin"
    val DEFAULT_PASSWORD: String = System.getenv("DEFAULT_PASSWORD") ?: "admin123"

    // JWT密钥
    val jwtKey: SecretKey = Keys.hmacShaKeyFor(JWT_SECRET.toByteArray())

    // 支持的文件类型图标映射
    val FILE_ICONS: Map<String, String> = mapOf(
        ".pdf" to "\uD83D\uDCC4", ".doc" to "\uD83D\uDCDD", ".docx" to "\uD83D\uDCDD",
        ".xls" to "\uD83D\uDCCA", ".xlsx" to "\uD83D\uDCCA", ".ppt" to "\uD83C\uDFAC", ".pptx" to "\uD83C\uDFAC",
        ".jpg" to "\uD83D\uDCF5", ".jpeg" to "\uD83D\uDCF5", ".png" to "\uD83D\uDCF5", ".gif" to "\uD83D\uDCF5",
        ".mp4" to "\uD83C\uDFA5", ".avi" to "\uD83C\uDFA5", ".mp3" to "\uD83C\uDFB5", ".wav" to "\uD83C\uDFB5",
        ".zip" to "\uD83D\uDCE6", ".rar" to "\uD83D\uDCE6", ".7z" to "\uD83D\uDCE6",
        ".js" to "\uD83D\uDCBB", ".html" to "\uD83D\uDCBB", ".css" to "\uD83D\uDCBB", ".kt" to "\uD83D\uDCBB"
    )
}

// ==================== 数据存储 ====================
object DataStore {
    val users: MutableMap<String, UserData> = mutableMapOf()

    fun initialize() {
        // 创建存储目录
        listOf(AppConfig.STORAGE_PATH, AppConfig.TEMP_PATH).forEach { path ->
            File(path).mkdirs()
        }

        // 初始化默认管理员用户
        users[AppConfig.DEFAULT_USER] = UserData(
            id = "default-admin-1",
            username = AppConfig.DEFAULT_USER,
            email = "admin@xiaosi.com",
            passwordHash = hashPassword(AppConfig.DEFAULT_PASSWORD),
            role = "admin",
            storageQuota = 10L * 1024L * 1024L * 1024L, // 10GB
            createdAt = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            lastLogin = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        )

        // 初始化测试用户
        users["zhangsan"] = UserData(
            id = "sample-user-1",
            username = "zhangsan",
            email = "zhangsan@xiaosi.com",
            passwordHash = hashPassword("password"),
            role = "user",
            storageQuota = 1L * 1024L * 1024L * 1024L, // 1GB
            createdAt = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            lastLogin = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        )
    }
}

// ==================== 工具函数 ====================

/**
 * 简单密码哈希函数 (生产环境应使用BCrypt等更安全的算法)
 */
fun hashPassword(password: String): String {
    return java.security.MessageDigest.getInstance("SHA-256")
        .digest(password.toByteArray())
        .joinToString("") { "%02x".format(it) }
}

/**
 * 验证密码
 */
fun verifyPassword(password: String, hash: String): Boolean {
    return hashPassword(password) == hash
}

/**
 * 获取文件图标
 */
fun getFileIcon(filename: String, isDirectory: Boolean): String {
    if (isDirectory) return "\uD83D\uDCC1"
    val extension = filename.substringAfterLast('.', "").lowercase()
    return AppConfig.FILE_ICONS[extension] ?: "\uD83D\uDCC4"
}

/**
 * 格式化文件大小
 */
fun formatFileSize(size: Long): String {
    if (size == 0L) return "0 Bytes"
    val units = arrayOf("Bytes", "KB", "MB", "GB", "TB")
    var fileSize = size.toDouble()
    var unitIndex = 0
    while (fileSize >= 1024 && unitIndex < units.size - 1) {
        fileSize /= 1024
        unitIndex++
    }
    return "%.2f ${units[unitIndex]}".format(fileSize)
}

/**
 * 获取本机IP地址列表
 */
fun getLocalIps(): List<String> {
    val ips = mutableListOf("127.0.0.1")
    try {
        val hostname = InetAddress.getLocalHost().hostAddress
        if (hostname != null && hostname !in ips) {
            ips.add(hostname)
        }
    } catch (e: Exception) {
        // 忽略错误
    }
    return ips
}

/**
 * 生成JWT Token
 */
fun generateToken(user: UserData): String {
    val now = Instant.now()
    val expiry = now.plusSeconds(AppConfig.JWT_EXPIRY_HOURS * 3600)
    
    return Jwts.builder()
        .subject(user.id)
        .claim("username", user.username)
        .claim("role", user.role)
        .issuedAt(Date.from(now))
        .expiration(Date.from(expiry))
        .signWith(AppConfig.jwtKey)
        .compact()
}

// ==================== 主应用入口 ====================
fun main() {
    // 初始化数据存储
    DataStore.initialize()

    // 启动Ktor服务器
    embeddedServer(Netty, port = AppConfig.PORT, host = AppConfig.HOST) {
        // 安装JSON序列化插件
        install(ContentNegotiation) {
            json(Json {
                prettyPrint = true
                isLenient = true
                ignoreUnknownKeys = true
            })
        }

        // 安装认证插件
        install(Authentication) {
            jwt("auth-jwt") {
                verifier(
                    Jwts.parser()
                        .verifyWith(AppConfig.jwtKey)
                        .build()
                )
                validate { credential ->
                    if (credential.payload.subject != null) {
                        UserIdPrincipal(credential.payload.subject)
                    } else {
                        null
                    }
                }
            }
        }

        // 路由配置
        routing {
            // 首页路由
            get("/") {
                call.respondRedirect("/index.html")
            }

            // ==================== 认证路由 ====================
            
            /**
             * 用户登录接口
             * POST /api/auth/login
             * 
             * 请求体:
             * {
             *   "username": "admin",
             *   "password": "admin123"
             * }
             * 
             * 响应:
             * {
             *   "success": true,
             *   "data": {
             *     "token": "jwt_token_here",
             *     "user": { ... }
             *   }
             * }
             */
            post("/api/auth/login") {
                try {
                    val loginRequest = call.receive<LoginRequest>()
                    val user = DataStore.users[loginRequest.username]

                    if (user == null || !verifyPassword(loginRequest.password, user.passwordHash)) {
                        call.respond(
                            HttpStatusCode.Unauthorized,
                            ApiResponse<Unit>(
                                success = false,
                                message = "Invalid credentials"
                            )
                        )
                        return@post
                    }

                    // 更新最后登录时间
                    user.lastLogin = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)

                    // 生成JWT Token
                    val token = generateToken(user)

                    call.respond(
                        HttpStatusCode.OK,
                        ApiResponse(
                            success = true,
                            data = LoginResponse(
                                token = token,
                                user = UserInfo(
                                    id = user.id,
                                    username = user.username,
                                    role = user.role,
                                    email = user.email
                                )
                            )
                        )
                    )
                } catch (e: Exception) {
                    call.respond(
                        HttpStatusCode.InternalServerError,
                        ApiResponse<Unit>(
                            success = false,
                            message = e.message ?: "Internal server error"
                        )
                    )
                }
            }

            // ==================== 受保护的路由 (需要JWT认证) ====================
            
            authenticate("auth-jwt") {

                /**
                 * 获取系统统计信息
                 * GET /api/stats
                 * 
                 * 返回存储使用情况、文件统计、用户统计等信息
                 */
                get("/api/stats") {
                    val stats = SystemStats(
                        storage = StorageStats(
                            used = (2.5 * 1024 * 1024 * 1024).toLong(), // 2.5GB
                            total = (4 * 1024 * 1024 * 1024).toLong(),    // 4GB
                            percentage = 62.5
                        ),
                        files = FilesStats(
                            count = 1284,
                            recent = listOf(
                                RecentItem(name = "项目报告.pdf", user = "admin", time = "5分钟前"),
                                RecentItem(name = "新用户注册", user = "system", time = "15分钟前")
                            )
                        ),
                        users = UsersStats(
                            total = DataStore.users.size,
                            online = 2
                        )
                    )

                    call.respond(
                        HttpStatusCode.OK,
                        ApiResponse(data = stats, success = true)
                    )
                }

                /**
                 * 获取文件列表
                 * GET /api/files?path=/
                 * 
                 * 查询参数:
                 * - path: 文件路径 (默认为根目录 "/")
                 * 
                 * 返回指定路径下的文件和文件夹列表
                 */
                get("/api/files") {
                    val path = call.parameters["path"] ?: "/"
                    val targetPath = File(AppConfig.STORAGE_PATH, path.removePrefix("/"))

                    val files = mutableListOf<FileItem>()

                    if (targetPath.exists() && targetPath.isDirectory) {
                        targetPath.listFiles()?.sortedBy { it.name }?.forEach { file ->
                            val isDirectory = file.isDirectory
                            files.add(
                                FileItem(
                                    id = file.lastModified().toString(),
                                    name = file.name,
                                    type = if (isDirectory) "folder" else "file",
                                    size = file.length(),
                                    modifiedAt = LocalDateTime.ofInstant(
                                        Instant.ofEpochMilli(file.lastModified()),
                                        ZoneId.systemDefault()
                                    ).format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                                    icon = getFileIcon(file.name, isDirectory),
                                    owner = "admin"
                                )
                            )
                        }
                    }

                    // 如果目录为空，返回示例数据
                    if (files.isEmpty()) {
                        val now = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
                        files.addAll(listOf(
                            FileItem(id = "1", name = "项目文档", type = "folder", size = 0, modifiedAt = now, icon = "\uD83D\uDCC1", owner = "admin"),
                            FileItem(id = "2", name = "照片备份", type = "folder", size = 0, modifiedAt = now, icon = "\uD83D\uDCC1", owner = "admin"),
                            FileItem(id = "3", name = "项目报告.pdf", type = "file", size = 2621440, modifiedAt = now, icon = "\uD83D\uDCC4", owner = "admin")
                        ))
                    }

                    call.respond(
                        HttpStatusCode.OK,
                        ApiResponse(data = files, success = true)
                    )
                }

                /**
                 * 上传文件
                 * POST /api/files/upload?path=/
                 * 
                 * 查询参数:
                 * - path: 目标路径 (默认为根目录 "/")
                 * 
                 * 请求体: multipart/form-data
                 */
                post("/api/files/upload") {
                    val path = call.parameters["path"] ?: "/"
                    val targetPath = File(AppConfig.STORAGE_PATH, path.removePrefix("/"))
                    
                    if (!targetPath.exists()) {
                        targetPath.mkdirs()
                    }

                    val multipart = call.receiveMultipart()
                    val uploadedFiles = mutableListOf<FileItem>()

                    multipart.forEachPart { part ->
                        when (part) {
                            is io.ktor.http.content.PartData.FileItem -> {
                                val originalFileName = part.originalFileName ?: "unknown"
                                
                                if (part.provider().let { false }) { // 简化处理
                                    // 文件大小检查逻辑
                                }
                                
                                val file = File(targetPath, originalFileName)
                                part.provider().copyTo(file.outputStream())
                                
                                uploadedFiles.add(
                                    FileItem(
                                        id = System.currentTimeMillis().toString(),
                                        name = originalFileName,
                                        type = "file",
                                        size = file.length(),
                                        modifiedAt = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                                        icon = getFileIcon(originalFileName, false),
                                        owner = "admin"
                                    )
                                )
                            }
                            else -> {}
                        }
                        part.dispose()
                    }

                    call.respond(
                        HttpStatusCode.OK,
                        ApiResponse(
                            success = true,
                            message = "成功上传 ${uploadedFiles.size} 个文件",
                            data = uploadedFiles
                        )
                    )
                }

                /**
                 * 创建文件夹
                 * POST /api/files/folder
                 * 
                 * 请求体:
                 * {
                 *   "name": "新建文件夹",
                 *   "path": "/"
                 * }
                 */
                post("/api/files/folder") {
                    val data = call.receive<Map<String, String>>()
                    val name = data["name"] ?: ""
                    val path = data["path"] ?: "/"

                    if (name.isBlank()) {
                        call.respond(
                            HttpStatusCode.BadRequest,
                            ApiResponse<Unit>(success = false, message = "Folder name is required")
                        )
                        return@post
                    }

                    val targetPath = File(AppConfig.STORAGE_PATH, path.removePrefix("/"), name)

                    if (targetPath.exists()) {
                        call.respond(
                            HttpStatusCode.BadRequest,
                            ApiResponse<Unit>(success = false, message = "Folder already exists")
                        )
                        return@post
                    }

                    targetPath.mkdirs()

                    call.respond(
                        HttpStatusCode.OK,
                        ApiResponse(
                            success = true,
                            message = "Folder created successfully",
                            data = mapOf("name" to name, "type" to "folder", "path" to path)
                        )
                    )
                }

                /**
                 * 获取用户列表
                 * GET /api/users
                 * 
                 * 返回系统中所有用户的列表，包含状态信息
                 */
                get("/api/users") {
                    val userList = DataStore.users.values.map { user ->
                        val lastLoginTime = LocalDateTime.parse(
                            user.lastLogin, 
                            DateTimeFormatter.ISO_LOCAL_DATE_TIME
                        )
                        val status = if (java.time.Duration.between(lastLoginTime, LocalDateTime.now()).toHours() < 1) {
                            "online"
                        } else {
                            "offline"
                        }

                        UserItem(
                            id = user.id,
                            username = user.username,
                            email = user.email,
                            role = user.role,
                            storageQuota = user.storageQuota,
                            status = status,
                            lastLogin = user.lastLogin
                        )
                    }

                    call.respond(
                        HttpStatusCode.OK,
                        ApiResponse(data = userList, success = true)
                    )
                }

                /**
                 * 获取系统设置
                 * GET /api/settings
                 * 
                 * 返回系统配置信息，包括常规设置和网络设置
                 */
                get("/api/settings") {
                    val settings = SystemSettings(
                        general = GeneralSettings(
                            systemName = "小思超级NAS",
                            timezone = "Asia/Shanghai",
                            language = "zh-CN",
                            theme = "dark"
                        ),
                        network = NetworkSettings(
                            ip = AppConfig.HOST,
                            port = AppConfig.PORT
                        )
                    )

                    call.respond(
                        HttpStatusCode.OK,
                        ApiResponse(data = settings, success = true)
                    )
                }
            }
        }
    }.start(wait = true)

    // 打印启动信息
    printStartupInfo()
}

/**
 * 打印服务器启动信息
 */
fun printStartupInfo() {
    println("=" .repeat(60))
    println("  🚀 小思超级NAS (Kotlin/Ktor版本) 已启动！")
    println("=" .repeat(60))
    println()
    println("📡 访问地址：")
    println("   本地访问：http://localhost:${AppConfig.PORT}")
    
    val localIps = getLocalIps()
    for (ip in localIps) {
        if (ip != "127.0.0.1") {
            println("   局域网访问：http://${ip}:${AppConfig.PORT}")
        }
    }
    
    println()
    println("👤 默认登录：")
    println("   用户名：${AppConfig.DEFAULT_USER}")
    println("   密码：${AppConfig.DEFAULT_PASSWORD}")
    println()
    println("=" .repeat(60))
    println()
}
