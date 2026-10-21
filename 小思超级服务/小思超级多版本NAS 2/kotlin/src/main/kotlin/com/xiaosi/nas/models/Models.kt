package com.xiaosi.nas.models

import kotlinx.serialization.Serializable

@Serializable
data class NasConfig(
    val version: String = "1.0.0",
    val port: Int = 8090,
    val storagePath: String = "./storage",
    val maxFileSize: Long = 1024 * 1024 * 1024, // 1GB
    val allowedExtensions: List<String> = emptyList(),
    val enableAuth: Boolean = false,
    val users: List<User> = emptyList()
)

@Serializable
data class User(
    val username: String,
    val password: String,
    val permissions: List<String> = listOf("read", "write", "delete")
)

@Serializable
data class FileInfo(
    val name: String,
    val path: String,
    val size: Long,
    val isDirectory: Boolean,
    val lastModified: Long,
    val extension: String = ""
)

@Serializable
data class ApiResponse<T>(
    val success: Boolean,
    val message: String,
    val data: T? = null,
    val code: Int = if (success) 200 else 400
)

@Serializable
data class Language(
    val code: String,
    val name: String,
    val nativeName: String
)

@Serializable
data class Translation(
    val key: String,
    val translations: Map<String, String>
)