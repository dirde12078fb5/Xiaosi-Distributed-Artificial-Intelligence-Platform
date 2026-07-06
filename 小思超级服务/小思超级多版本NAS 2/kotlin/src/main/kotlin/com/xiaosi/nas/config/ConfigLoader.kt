package com.xiaosi.nas.config

import com.google.gson.Gson
import com.xiaosi.nas.models.NasConfig
import java.io.File

object ConfigLoader {
    private val gson = Gson()

    fun load(configPath: String = "../config/config.json"): NasConfig {
        val file = File(configPath)
        return if (file.exists()) {
            try {
                gson.fromJson(file.readText(), NasConfig::class.java)
            } catch (e: Exception) {
                println("Failed to load config from $configPath, using defaults: ${e.message}")
                NasConfig()
            }
        } else {
            println("Config file not found at $configPath, creating default config")
            val defaultConfig = NasConfig()
            file.parentFile?.mkdirs()
            file.writeText(gson.toJson(defaultConfig))
            defaultConfig
        }
    }
}