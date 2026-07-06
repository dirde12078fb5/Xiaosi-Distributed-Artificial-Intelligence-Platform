package com.xiaosi.nas.managers

import java.io.File
import java.util.UUID
import java.time.Instant
import scala.util.Try
import com.xiaosi.nas.models._
import com.xiaosi.nas.config.ConfigManager

/**
 * 推送管理器
 */
class PushManager(configManager: ConfigManager) {
  
  def listTargets(): List[PushTarget] = {
    configManager.getConfig.pushTargets
  }
  
  def addTarget(name: String, ip: String, port: Int): Try[PushTarget] = {
    Try {
      val id = UUID.randomUUID().toString
      val created = Instant.now.getEpochSecond
      
      val target = PushTarget(
        id = id,
        name = name,
        ip = ip,
        port = port,
        active = true,
        created = created
      )
      
      val currentConfig = configManager.getConfig
      val newConfig = currentConfig.copy(
        pushTargets = currentConfig.pushTargets :+ target
      )
      configManager.updateConfig(newConfig)
      
      target
    }
  }
  
  def deleteTarget(id: String): Try[Boolean] = {
    Try {
      val currentConfig = configManager.getConfig
      val targets = currentConfig.pushTargets.filter(_.id != id)
      val newConfig = currentConfig.copy(pushTargets = targets)
      configManager.updateConfig(newConfig)
      true
    }
  }
  
  def listHistory(): List[PushHistory] = {
    configManager.getConfig.pushHistory
  }
  
  def pushFolder(sourceFolder: String, targetId: String): Try[PushHistory] = {
    Try {
      val targetOpt = configManager.getConfig.pushTargets.find(_.id == targetId)
      if (targetOpt.isEmpty) {
        throw new Exception("目标设备不存在")
      }
      
      val target = targetOpt.get
      val folder = new File(sourceFolder)
      
      if (!folder.exists() || !folder.isDirectory) {
        throw new Exception("源文件夹不存在")
      }
      
      val fileCount = countFiles(folder)
      val totalSize = calculateFolderSize(folder)
      val created = Instant.now.getEpochSecond
      val id = UUID.randomUUID().toString
      
      val history = PushHistory(
        id = id,
        sourceFolder = sourceFolder,
        targetId = targetId,
        targetName = target.name,
        fileCount = fileCount,
        totalSize = totalSize,
        status = "success",
        timestamp = created
      )
      
      val currentConfig = configManager.getConfig
      val newConfig = currentConfig.copy(
        pushHistory = currentConfig.pushHistory :+ history
      )
      configManager.updateConfig(newConfig)
      
      history
    }
  }
  
  private def countFiles(folder: File): Int = {
    if (folder.isDirectory) {
      folder.listFiles().foldLeft(0) { (count, file) =>
        if (file.isFile) count + 1
        else count + countFiles(file)
      }
    } else 0
  }
  
  private def calculateFolderSize(folder: File): Long = {
    if (folder.isDirectory) {
      folder.listFiles().foldLeft(0L) { (size, file) =>
        if (file.isFile) size + file.length()
        else size + calculateFolderSize(file)
      }
    } else 0L
  }
}