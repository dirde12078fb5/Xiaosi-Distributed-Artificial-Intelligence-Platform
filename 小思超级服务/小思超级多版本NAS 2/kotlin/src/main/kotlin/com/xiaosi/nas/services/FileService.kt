package com.xiaosi.nas.services

import com.xiaosi.nas.models.FileInfo
import java.io.File
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.security.MessageDigest

class FileService(private val storagePath: String) {

    private val storageDir = File(storagePath).apply { mkdirs() }

    fun listFiles(path: String = "/"): List<FileInfo> {
        val targetDir = File(storageDir, path.trimStart('/'))
        if (!targetDir.exists() || !targetDir.isDirectory) return emptyList()

        return targetDir.listFiles()?.map { file ->
            FileInfo(
                name = file.name,
                path = file.relativeTo(storageDir).path.replace('\\', '/'),
                size = if (file.isFile) file.length() else 0L,
                isDirectory = file.isDirectory,
                lastModified = file.lastModified(),
                extension = if (file.isFile) file.extension else ""
            )
        }?.sortedWith(compareBy<FileInfo> { !it.isDirectory }.thenBy { it.name }) ?: emptyList()
    }

    fun getFileInfo(path: String): FileInfo? {
        val file = File(storageDir, path.trimStart('/'))
        if (!file.exists()) return null

        return FileInfo(
            name = file.name,
            path = file.relativeTo(storageDir).path.replace('\\', '/'),
            size = if (file.isFile) file.length() else 0L,
            isDirectory = file.isDirectory,
            lastModified = file.lastModified(),
            extension = if (file.isFile) file.extension else ""
        )
    }

    fun createDirectory(path: String): Boolean {
        val dir = File(storageDir, path.trimStart('/'))
        return if (!dir.exists()) dir.mkdirs() else false
    }

    fun deleteFile(path: String): Boolean {
        val file = File(storageDir, path.trimStart('/'))
        return if (file.exists()) file.deleteRecursively() else false
    }

    fun moveFile(sourcePath: String, destPath: String): Boolean {
        val source = File(storageDir, sourcePath.trimStart('/'))
        val dest = File(storageDir, destPath.trimStart('/'))
        return if (source.exists()) {
            dest.parentFile?.mkdirs()
            Files.move(source.toPath(), dest.toPath(), StandardCopyOption.REPLACE_EXISTING)
            true
        } else false
    }

    fun copyFile(sourcePath: String, destPath: String): Boolean {
        val source = File(storageDir, sourcePath.trimStart('/'))
        val dest = File(storageDir, destPath.trimStart('/'))
        return if (source.exists()) {
            dest.parentFile?.mkdirs()
            source.copyRecursively(dest, overwrite = true)
        } else false
    }

    fun renameFile(path: String, newName: String): Boolean {
        val file = File(storageDir, path.trimStart('/'))
        if (!file.exists()) return false

        val newFile = File(file.parentFile, newName)
        return file.renameTo(newFile)
    }

    fun searchFiles(query: String, path: String = "/"): List<FileInfo> {
        val searchDir = File(storageDir, path.trimStart('/'))
        if (!searchDir.exists()) return emptyList()

        val results = mutableListOf<FileInfo>()
        searchDir.walkTopDown()
            .filter { it.name.contains(query, ignoreCase = true) }
            .forEach { file ->
                results.add(FileInfo(
                    name = file.name,
                    path = file.relativeTo(storageDir).path.replace('\\', '/'),
                    size = if (file.isFile) file.length() else 0L,
                    isDirectory = file.isDirectory,
                    lastModified = file.lastModified(),
                    extension = if (file.isFile) file.extension else ""
                ))
            }
        return results
    }

    fun calculateHash(path: String, algorithm: String = "MD5"): String? {
        val file = File(storageDir, path.trimStart('/'))
        if (!file.exists() || !file.isFile) return null

        val digest = MessageDigest.getInstance(algorithm)
        file.inputStream().use { input ->
            val buffer = ByteArray(8192)
            var bytesRead: Int
            while (input.read(buffer).also { bytesRead = it } != -1) {
                digest.update(buffer, 0, bytesRead)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }

    fun getFile(path: String): File? {
        val file = File(storageDir, path.trimStart('/'))
        return if (file.exists() && file.isFile) file else null
    }

    fun getStorageStats(): Map<String, Any> {
        val totalSpace = storageDir.totalSpace()
        val freeSpace = storageDir.freeSpace()
        val usedSpace = totalSpace - freeSpace

        var fileCount = 0L
        var dirCount = 0L
        storageDir.walkTopDown().forEach { file ->
            if (file.isFile) fileCount++ else if (file.isDirectory && file != storageDir) dirCount++
        }

        return mapOf(
            "totalSpace" to totalSpace,
            "freeSpace" to freeSpace,
            "usedSpace" to usedSpace,
            "fileCount" to fileCount,
            "directoryCount" to dirCount
        )
    }
}