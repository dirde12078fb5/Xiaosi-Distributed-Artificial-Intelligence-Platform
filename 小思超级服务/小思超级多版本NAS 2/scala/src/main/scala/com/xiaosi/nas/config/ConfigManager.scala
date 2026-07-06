package com.xiaosi.nas.config

import java.io.{File, FileInputStream}
import java.nio.file.{Files, Paths}
import scala.util.{Try, Using}
import spray.json._
import com.xiaosi.nas.models._
import com.xiaosi.nas.models.ModelsJsonProtocol._

/**
 * 配置管理 - 从 ../config/config.json 加载配置
 */
class ConfigManager {
  private var config: NASConfig = NASConfig()
  
  def load(): Try[NASConfig] = {
    Try {
      val configPath = findConfigPath()
      if (Files.exists(Paths.get(configPath))) {
        val jsonContent = Files.readString(Paths.get(configPath))
        config = jsonContent.parseJson.convertTo[NASConfig]
        config
      } else {
        config = NASConfig()
        save()
        config
      }
    }
  }
  
  private def findConfigPath(): String = {
    val possibilities = List(
      "../config/config.json",  // 相对路径
      "../../config/config.json",  // Scala子目录的相对路径
      "./config.json",  // 当前目录
      "config/config.json"  // config子目录
    )
    
    possibilities.find(path => Files.exists(Paths.get(path))).getOrElse {
      // 默认使用第一个路径
      "../config/config.json"
    }
  }
  
  def save(): Try[Unit] = {
    Try {
      val configPath = findConfigPath()
      val parentDir = new File(configPath).getParentFile
      if (parentDir != null && !parentDir.exists()) {
        parentDir.mkdirs()
      }
      
      val jsonContent = config.toJson.prettyPrint
      Files.writeString(Paths.get(configPath), jsonContent)
    }
  }
  
  def getConfig: NASConfig = config
  
  def updateConfig(newConfig: NASConfig): Try[Unit] = {
    config = newConfig
    save()
  }
  
  // 数据目录管理
  def getDataDir: String = config.dataDir
  
  def ensureDataDir(): Unit = {
    val dir = new File(config.dataDir)
    if (!dir.exists()) {
      dir.mkdirs()
    }
  }
}