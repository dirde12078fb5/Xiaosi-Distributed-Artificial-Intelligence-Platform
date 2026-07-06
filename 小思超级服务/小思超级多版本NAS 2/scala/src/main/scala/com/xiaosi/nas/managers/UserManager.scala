package com.xiaosi.nas.managers

import java.security.MessageDigest
import java.util.UUID
import java.time.Instant
import scala.util.Try
import com.xiaosi.nas.models._
import com.xiaosi.nas.config.ConfigManager

/**
 * 用户管理器
 */
class UserManager(configManager: ConfigManager) {
  
  def listUsers(): List[User] = {
    configManager.getConfig.users
  }
  
  def createUser(username: String, password: String, isAdmin: Boolean, storageQuota: Long, homeDirectory: String): Try[User] = {
    Try {
      // 检查用户名是否已存在
      if (configManager.getConfig.users.exists(_.username == username)) {
        throw new Exception("用户名已存在")
      }
      
      val id = UUID.randomUUID().toString
      val passwordHash = hashPassword(password)
      val created = Instant.now.getEpochSecond
      
      val user = User(
        id = id,
        username = username,
        passwordHash = passwordHash,
        isAdmin = isAdmin,
        storageQuota = storageQuota,
        homeDirectory = homeDirectory,
        created = created
      )
      
      val currentConfig = configManager.getConfig
      val newConfig = currentConfig.copy(
        users = currentConfig.users :+ user
      )
      configManager.updateConfig(newConfig)
      
      user
    }
  }
  
  def deleteUser(id: String): Try[Boolean] = {
    Try {
      val currentConfig = configManager.getConfig
      val users = currentConfig.users.filter(_.id != id)
      val newConfig = currentConfig.copy(users = users)
      configManager.updateConfig(newConfig)
      true
    }
  }
  
  def getUser(id: String): Option[User] = {
    configManager.getConfig.users.find(_.id == id)
  }
  
  def authenticateUser(username: String, password: String): Option[User] = {
    val passwordHash = hashPassword(password)
    configManager.getConfig.users.find(u => u.username == username && u.passwordHash == passwordHash)
  }
  
  def updateUserQuota(id: String, newQuota: Long): Try[Boolean] = {
    Try {
      val currentConfig = configManager.getConfig
      val users = currentConfig.users.map { user =>
        if (user.id == id) user.copy(storageQuota = newQuota)
        else user
      }
      val newConfig = currentConfig.copy(users = users)
      configManager.updateConfig(newConfig)
      true
    }
  }
  
  private def hashPassword(password: String): String = {
    val md = MessageDigest.getInstance("SHA-256")
    val hashBytes = md.digest(password.getBytes("UTF-8"))
    hashBytes.map("%02x".format(_)).mkString
  }
}