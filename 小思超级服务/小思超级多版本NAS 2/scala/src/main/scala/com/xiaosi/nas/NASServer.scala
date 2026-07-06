package com.xiaosi.nas

import akka.actor.typed.ActorSystem
import akka.actor.typed.scaladsl.Behaviors
import akka.http.scaladsl.Http
import akka.http.scaladsl.server.Route
import scala.concurrent.{ExecutionContextExecutor, Future}
import scala.util.{Success, Failure}
import com.xiaosi.nas.config.ConfigManager
import com.xiaosi.nas.managers._
import com.xiaosi.nas.routes.Routes
import org.slf4j.LoggerFactory

/**
 * 小思超级多版本NAS服务 - Scala实现
 * 基于Akka HTTP框架
 * 默认端口: 8093
 */
object NASServer {
  
  private val logger = LoggerFactory.getLogger(getClass)
  
  def main(args: Array[String]): Unit = {
    // 创建Actor系统
    implicit val system: ActorSystem[Nothing] = ActorSystem(Behaviors.empty, "nas-system")
    implicit val executionContext: ExecutionContextExecutor = system.executionContext
    
    // 初始化配置和管理器
    val configManager = new ConfigManager()
    configManager.load()
    configManager.ensureDataDir()
    
    val storageManager = new StorageManager(configManager)
    val userManager = new UserManager(configManager)
    val smbManager = new SMBManager(configManager)
    val pushManager = new PushManager(configManager)
    
    // 创建路由
    val routeHandler = new Routes(storageManager, userManager, smbManager, pushManager)
    val routes = routeHandler.routes
    
    // 获取端口配置
    val port = configManager.getConfig.port
    
    // 启动HTTP服务器
    val serverBinding: Future[Http.ServerBinding] = Http().newServerAt("0.0.0.0", port).bind(routes)
    
    serverBinding.onComplete {
      case Success(binding) =>
        val address = binding.localAddress
        logger.info(s"小思超级NAS服务启动成功 - Scala版本")
        logger.info(s"服务地址: http://${address.getHostString}:${address.getPort}")
        logger.info(s"API文档: http://${address.getHostString}:${address.getPort}/api/health")
        logger.info(s"默认端口: $port")
        logger.info("支持28种语言翻译")
        logger.info("基于Akka HTTP框架，遵循Scala最佳实践")
        
      case Failure(ex) =>
        logger.error(s"服务启动失败: ${ex.getMessage}")
        system.terminate()
    }
    
    // 等待终止信号
    scala.io.StdIn.readLine()
    
    // 关闭服务器
    serverBinding.flatMap(_.unbind()).onComplete { _ =>
      logger.info("服务已停止")
      system.terminate()
    }
  }
}