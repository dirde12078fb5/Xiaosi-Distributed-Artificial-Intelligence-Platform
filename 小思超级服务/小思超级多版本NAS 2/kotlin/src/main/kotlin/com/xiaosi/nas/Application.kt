package com.xiaosi.nas

import com.xiaosi.nas.config.ConfigLoader
import com.xiaosi.nas.routes.configureRoutes
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.plugins.cors.routing.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.http.*
import kotlinx.serialization.json.Json

fun main() {
    val config = ConfigLoader.load()

    embeddedServer(Netty, port = config.port, module = Application::module)
        .start(wait = true)
}

fun Application.module() {
    val config = ConfigLoader.load()

    install(ContentNegotiation) {
        json(Json {
            prettyPrint = true
            isLenient = true
            ignoreUnknownKeys = true
        })
    }

    install(CORS) {
        anyHost()
        allowHeader(HttpHeaders.ContentType)
        allowHeader(HttpHeaders.Authorization)
        allowMethod(HttpMethod.Get)
        allowMethod(HttpMethod.Post)
        allowMethod(HttpMethod.Put)
        allowMethod(HttpMethod.Delete)
        allowMethod(HttpMethod.Options)
    }

    install(StatusPages) {
        exception<Throwable> { call, cause ->
            call.respond(HttpStatusCode.InternalServerError, mapOf(
                "success" to false,
                "message" to "Internal server error: ${cause.message}"
            ))
        }
    }

    configureRoutes(config)

    println("╔════════════════════════════════════════════╗")
    println("║   小思NAS服务已启动                          ║")
    println("║   版本: ${config.version.padEnd(32)}║")
    println("║   端口: ${config.port.toString().padEnd(32)}║")
    println("║   存储路径: ${config.storagePath.padEnd(28)}║")
    println("╚════════════════════════════════════════════╝")
}