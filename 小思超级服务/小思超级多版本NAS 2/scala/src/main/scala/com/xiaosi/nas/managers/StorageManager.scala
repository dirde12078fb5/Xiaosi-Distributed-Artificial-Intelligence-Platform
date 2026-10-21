package com.xiaosi.nas.managers

import java.io.File
import java.nio.file.{Files, Paths}
import java.util.UUID
import java.time.Instant
import scala.util.Try
import com.xiaosi.nas.models._
import com.xiaosi.nas.config.ConfigManager

/**
 * 存储管理器
 */
class StorageManager(configManager: ConfigManager) {
  
  def listVolumes(): List[Volume] = {
    configManager.getConfig.volumes
  }
  
  def createVolume(name: String, path: String, quota: Long): Try[Volume] = {
    Try {
      val id = UUID.randomUUID().toString
      val created = Instant.now.getEpochSecond
      
      // 创建目录
      val dir = new File(path)
      if (!dir.exists()) {
        dir.mkdirs()
      }
      
      val volume = Volume(
        id = id,
        name = name,
        path = path,
        quota = quota,
        used = calculateUsedSpace(path),
        available = quota - calculateUsedSpace(path),
        created = created
      )
      
      val currentConfig = configManager.getConfig
      val newConfig = currentConfig.copy(
        volumes = currentConfig.volumes :+ volume
      )
      configManager.updateConfig(newConfig)
      
      volume
    }
  }
  
  def deleteVolume(id: String): Try[Boolean] = {
    Try {
      val currentConfig = configManager.getConfig
      val volumes = currentConfig.volumes.filter(_.id != id)
      val newConfig = currentConfig.copy(volumes = volumes)
      configManager.updateConfig(newConfig)
      true
    }
  }
  
  def getVolume(id: String): Option[Volume] = {
    configManager.getConfig.volumes.find(_.id == id)
  }
  
  def updateVolumeStats(): Unit = {
    val currentConfig = configManager.getConfig
    val updatedVolumes = currentConfig.volumes.map { vol =>
      val used = calculateUsedSpace(vol.path)
      vol.copy(used = used, available = vol.quota - used)
    }
    val newConfig = currentConfig.copy(volumes = updatedVolumes)
    configManager.updateConfig(newConfig)
  }
  
  private def calculateUsedSpace(path: String): Long = {
    Try {
      val dir = new File(path)
      if (dir.exists() && dir.isDirectory) {
        dir.listFiles().foldLeft(0L) { (total, file) =>
          if (file.isFile) {
            total + file.length() / (1024 * 1024 * 1024)  // Convert to GB
          } else {
            total + calculateUsedSpace(file.getAbsolutePath)
          }
        }
      } else {
        0L
      }
    }.getOrElse(0L)
  }
}