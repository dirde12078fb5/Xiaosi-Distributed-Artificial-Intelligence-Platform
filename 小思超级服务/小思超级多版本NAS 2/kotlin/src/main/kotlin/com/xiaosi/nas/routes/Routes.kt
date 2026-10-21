package com.xiaosi.nas.routes

import com.xiaosi.nas.models.NasConfig
import com.xiaosi.nas.services.FileService
import com.xiaosi.nas.services.TranslationService
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.http.content.*
import java.io.File

fun Application.configureRoutes(config: NasConfig) {
    val fileService = FileService(config.storagePath)
    val translationService = TranslationService()

    routing {
        route("/api") {
            // 健康检查
            get("/health") {
                call.respond(mapOf(
                    "success" to true,
                    "message" to "Service is running",
                    "version" to config.version
                ))
            }

            // 获取服务信息
            get("/info") {
                call.respond(mapOf(
                    "success" to true,
                    "data" to mapOf(
                        "name" to "小思NAS",
                        "version" to config.version,
                        "storagePath" to config.storagePath,
                        "maxFileSize" to config.maxFileSize,
                        "port" to config.port
                    )
                ))
            }

            // 获取存储统计
            get("/stats") {
                call.respond(mapOf(
                    "success" to true,
                    "data" to fileService.getStorageStats()
                ))
            }

            // 文件操作路由
            route("/files") {
                // 列出文件
                get {
                    val path = call.request.queryParameters["path"] ?: "/"
                    call.respond(mapOf(
                        "success" to true,
                        "data" to fileService.listFiles(path)
                    ))
                }

                // 获取文件信息
                get("/info") {
                    val path = call.request.queryParameters["path"]
                    if (path.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Path parameter is required"
                        ))
                        return@get
                    }

                    val fileInfo = fileService.getFileInfo(path)
                    if (fileInfo != null) {
                        call.respond(mapOf("success" to true, "data" to fileInfo))
                    } else {
                        call.respond(HttpStatusCode.NotFound, mapOf(
                            "success" to false,
                            "message" to "File not found"
                        ))
                    }
                }

                // 下载文件
                get("/download") {
                    val path = call.request.queryParameters["path"]
                    if (path.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Path parameter is required"
                        ))
                        return@get
                    }

                    val file = fileService.getFile(path)
                    if (file != null) {
                        call.response.header(
                            HttpHeaders.ContentDisposition,
                            ContentDisposition.Attachment
                                .withParameter(ContentDisposition.Parameters.FileName, file.name)
                                .toString()
                        )
                        call.respondFile(file)
                    } else {
                        call.respond(HttpStatusCode.NotFound, mapOf(
                            "success" to false,
                            "message" to "File not found"
                        ))
                    }
                }

                // 上传文件
                post("/upload") {
                    val uploadPath = call.request.queryParameters["path"] ?: "/"
                    val multipart = call.receiveMultipart()

                    multipart.forEachPart { part ->
                        if (part is PartData.FileItem) {
                            val fileName = part.originalFileName ?: "unknown"
                            val dir = File(config.storagePath, uploadPath.trimStart('/')).apply { mkdirs() }
                            val file = File(dir, fileName)

                            part.streamProvider().use { input ->
                                file.outputStream().use { output ->
                                    input.copyTo(output)
                                }
                            }
                        }
                        part.dispose()
                    }

                    call.respond(mapOf(
                        "success" to true,
                        "message" to "File uploaded successfully"
                    ))
                }

                // 创建目录
                post("/mkdir") {
                    val path = call.request.queryParameters["path"]
                    if (path.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Path parameter is required"
                        ))
                        return@post
                    }

                    val result = fileService.createDirectory(path)
                    call.respond(mapOf(
                        "success" to result,
                        "message" to if (result) "Directory created" else "Failed to create directory"
                    ))
                }

                // 删除文件/目录
                delete {
                    val path = call.request.queryParameters["path"]
                    if (path.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Path parameter is required"
                        ))
                        return@delete
                    }

                    val result = fileService.deleteFile(path)
                    call.respond(mapOf(
                        "success" to result,
                        "message" to if (result) "Deleted successfully" else "Failed to delete"
                    ))
                }

                // 移动文件
                put("/move") {
                    val source = call.request.queryParameters["source"]
                    val dest = call.request.queryParameters["dest"]

                    if (source.isNullOrBlank() || dest.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Source and destination parameters are required"
                        ))
                        return@put
                    }

                    val result = fileService.moveFile(source, dest)
                    call.respond(mapOf(
                        "success" to result,
                        "message" to if (result) "Moved successfully" else "Failed to move"
                    ))
                }

                // 复制文件
                put("/copy") {
                    val source = call.request.queryParameters["source"]
                    val dest = call.request.queryParameters["dest"]

                    if (source.isNullOrBlank() || dest.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Source and destination parameters are required"
                        ))
                        return@put
                    }

                    val result = fileService.copyFile(source, dest)
                    call.respond(mapOf(
                        "success" to result,
                        "message" to if (result) "Copied successfully" else "Failed to copy"
                    ))
                }

                // 重命名文件
                put("/rename") {
                    val path = call.request.queryParameters["path"]
                    val newName = call.request.queryParameters["newName"]

                    if (path.isNullOrBlank() || newName.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Path and newName parameters are required"
                        ))
                        return@put
                    }

                    val result = fileService.renameFile(path, newName)
                    call.respond(mapOf(
                        "success" to result,
                        "message" to if (result) "Renamed successfully" else "Failed to rename"
                    ))
                }

                // 搜索文件
                get("/search") {
                    val query = call.request.queryParameters["q"]
                    val path = call.request.queryParameters["path"] ?: "/"

                    if (query.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Query parameter 'q' is required"
                        ))
                        return@get
                    }

                    call.respond(mapOf(
                        "success" to true,
                        "data" to fileService.searchFiles(query, path)
                    ))
                }

                // 计算文件哈希
                get("/hash") {
                    val path = call.request.queryParameters["path"]
                    val algorithm = call.request.queryParameters["algorithm"] ?: "MD5"

                    if (path.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Path parameter is required"
                        ))
                        return@get
                    }

                    val hash = fileService.calculateHash(path, algorithm)
                    if (hash != null) {
                        call.respond(mapOf(
                            "success" to true,
                            "data" to mapOf("hash" to hash, "algorithm" to algorithm)
                        ))
                    } else {
                        call.respond(HttpStatusCode.NotFound, mapOf(
                            "success" to false,
                            "message" to "File not found"
                        ))
                    }
                }
            }

            // 多语言翻译路由
            route("/i18n") {
                // 获取支持的语言列表
                get("/languages") {
                    call.respond(mapOf(
                        "success" to true,
                        "data" to translationService.getSupportedLanguages()
                    ))
                }

                // 获取指定语言的翻译
                get("/translations") {
                    val lang = call.request.queryParameters["lang"] ?: "zh-CN"
                    call.respond(mapOf(
                        "success" to true,
                        "data" to translationService.getTranslations(lang)
                    ))
                }

                // 翻译指定文本
                get("/translate") {
                    val key = call.request.queryParameters["key"]
                    val lang = call.request.queryParameters["lang"] ?: "zh-CN"

                    if (key.isNullOrBlank()) {
                        call.respond(HttpStatusCode.BadRequest, mapOf(
                            "success" to false,
                            "message" to "Key parameter is required"
                        ))
                        return@get
                    }

                    val translation = translationService.translate(key, lang)
                    call.respond(mapOf(
                        "success" to true,
                        "data" to mapOf("key" to key, "translation" to translation, "lang" to lang)
                    ))
                }
            }
        }
    }
}