package com.xiaosi.nas.routes

import akka.http.scaladsl.server.Directives._
import akka.http.scaladsl.model.{ContentTypes, HttpEntity}
import akka.http.scaladsl.server.Route
import spray.json._
import com.xiaosi.nas.models._
import com.xiaosi.nas.models.ModelsJsonProtocol._
import com.xiaosi.nas.i18n.Translations
import com.xiaosi.nas.managers._

/**
 * REST API路由定义
 */
class Routes(
  storageManager: StorageManager,
  userManager: UserManager,
  smbManager: SMBManager,
  pushManager: PushManager
) {
  
  // JSON格式化
  implicit val volumeListFormat: JsonFormat[List[Volume]] = listFormat(jsonFormat7(Volume))
  implicit val userListFormat: JsonFormat[List[User]] = listFormat(jsonFormat7(User))
  implicit val shareListFormat: JsonFormat[List[SMBShare]] = listFormat(jsonFormat8(SMBShare))
  implicit val targetListFormat: JsonFormat[List[PushTarget]] = listFormat(jsonFormat6(PushTarget))
  implicit val historyListFormat: JsonFormat[List[PushHistory]] = listFormat(jsonFormat8(PushHistory))
  implicit val deviceListFormat: JsonFormat[List[Device]] = listFormat(jsonFormat4(Device))
  
  val routes: Route = concat(
    // CORS支持
    respondWithHeaders(
      akka.http.scaladsl.model.headers.`Access-Control-Allow-Origin`(akka.http.scaladsl.model.headers.HttpOriginRange.*),
      akka.http.scaladsl.model.headers.`Access-Control-Allow-Methods`(akka.http.scaladsl.model.HttpMethods.GET, akka.http.scaladsl.model.HttpMethods.POST, akka.http.scaladsl.model.HttpMethods.PUT, akka.http.scaladsl.model.HttpMethods.DELETE, akka.http.scaladsl.model.HttpMethods.OPTIONS),
      akka.http.scaladsl.model.headers.`Access-Control-Allow-Headers`("Content-Type", "Authorization")
    ),
    
    // 多语言API
    path("api" / "i18n") {
      get {
        parameter("lang") { lang =>
          val trans = Translations.getTranslations(lang)
          complete(HttpEntity(ContentTypes.`application/json`, trans.toJson.prettyPrint))
        }
      }
    },
    
    // 存储管理API
    pathPrefix("api" / "storage") {
      path("volumes") {
        get {
          val volumes = storageManager.listVolumes()
          complete(ApiResponse(success = true, data = Some(volumes)))
        } ~
        post {
          entity(as[JsObject]) { json =>
            val name = json.fields("name").convertTo[String]
            val path = json.fields("path").convertTo[String]
            val quota = json.fields("quota").convertTo[Long]
            
            val result = storageManager.createVolume(name, path, quota)
            result.fold(
              error => complete(ApiResponse[Boolean](success = false, message = Some(error.getMessage))),
              volume => complete(ApiResponse[Volume](success = true, data = Some(volume)))
            )
          }
        }
      } ~
      path("volumes" / Segment) { id =>
        get {
          val volume = storageManager.getVolume(id)
          complete(ApiResponse(success = true, data = volume))
        } ~
        delete {
          val result = storageManager.deleteVolume(id)
          result.fold(
            error => complete(ApiResponse[Boolean](success = false, message = Some(error.getMessage))),
            _ => complete(ApiResponse[Boolean](success = true))
          )
        }
      }
    },
    
    // 用户管理API
    pathPrefix("api" / "users") {
      get {
        val users = userManager.listUsers()
        // 不返回密码哈希
        val safeUsers = users.map(u => u.copy(passwordHash = ""))
        complete(ApiResponse(success = true, data = Some(safeUsers)))
      } ~
      post {
        entity(as[JsObject]) { json =>
          val username = json.fields("username").convertTo[String]
          val password = json.fields("password").convertTo[String]
          val isAdmin = json.fields.get("isAdmin").map(_.convertTo[Boolean]).getOrElse(false)
          val quota = json.fields.get("quota").map(_.convertTo[Long]).getOrElse(10L)
          val homeDir = json.fields.get("homeDirectory").map(_.convertTo[String]).getOrElse(s"/home/$username")
          
          val result = userManager.createUser(username, password, isAdmin, quota, homeDir)
          result.fold(
            error => complete(ApiResponse[Boolean](success = false, message = Some(error.getMessage))),
            user => complete(ApiResponse[User](success = true, data = Some(user.copy(passwordHash = ""))))
          )
        }
      } ~
      path(Segment) { id =>
        get {
          val user = userManager.getUser(id)
          complete(ApiResponse(success = true, data = user.map(_.copy(passwordHash = ""))))
        } ~
        delete {
          val result = userManager.deleteUser(id)
          result.fold(
            error => complete(ApiResponse[Boolean](success = false, message = Some(error.getMessage))),
            _ => complete(ApiResponse[Boolean](success = true))
          )
        }
      }
    },
    
    // SMB共享管理API
    pathPrefix("api" / "smb") {
      path("shares") {
        get {
          val shares = smbManager.listShares()
          complete(ApiResponse(success = true, data = Some(shares)))
        } ~
        post {
          entity(as[JsObject]) { json =>
            val name = json.fields("name").convertTo[String]
            val path = json.fields("path").convertTo[String]
            val comment = json.fields.get("comment").map(_.convertTo[String]).getOrElse("")
            val readOnly = json.fields.get("readOnly").map(_.convertTo[Boolean]).getOrElse(false)
            val browseable = json.fields.get("browseable").map(_.convertTo[Boolean]).getOrElse(true)
            val guestAccess = json.fields.get("guestAccess").map(_.convertTo[Boolean]).getOrElse(false)
            
            val result = smbManager.createShare(name, path, comment, readOnly, browseable, guestAccess)
            result.fold(
              error => complete(ApiResponse[Boolean](success = false, message = Some(error.getMessage))),
              share => complete(ApiResponse[SMBShare](success = true, data = Some(share)))
            )
          }
        }
      } ~
      path("status") {
        get {
          val status = smbManager.getStatus()
          complete(HttpEntity(ContentTypes.`application/json`, status.toJson.prettyPrint))
        }
      } ~
      path("shares" / Segment) { id =>
        get {
          val share = smbManager.getShare(id)
          complete(ApiResponse(success = true, data = share))
        } ~
        delete {
          val result = smbManager.deleteShare(id)
          result.fold(
            error => complete(ApiResponse[Boolean](success = false, message = Some(error.getMessage))),
            _ => complete(ApiResponse[Boolean](success = true))
          )
        }
      }
    },
    
    // IP管理API
    pathPrefix("api" / "ip") {
      path("local") {
        get {
          val ips = IPManager.getLocalIPs()
          complete(ApiResponse(success = true, data = Some(ips)))
        }
      } ~
      path("scan") {
        get {
          parameter("port".as[Int].?) { portOpt =>
            val port = portOpt.getOrElse(8093)
            val devices = IPManager.scanLAN(port)
            complete(ApiResponse(success = true, data = Some(devices)))
          }
        }
      }
    },
    
    // 推送管理API
    pathPrefix("api" / "push") {
      path("targets") {
        get {
          val targets = pushManager.listTargets()
          complete(ApiResponse(success = true, data = Some(targets)))
        } ~
        post {
          entity(as[JsObject]) { json =>
            val name = json.fields("name").convertTo[String]
            val ip = json.fields("ip").convertTo[String]
            val port = json.fields.get("port").map(_.convertTo[Int]).getOrElse(8093)
            
            val result = pushManager.addTarget(name, ip, port)
            result.fold(
              error => complete(ApiResponse[Boolean](success = false, message = Some(error.getMessage))),
              target => complete(ApiResponse[PushTarget](success = true, data = Some(target)))
            )
          }
        }
      } ~
      path("targets" / Segment) { id =>
        delete {
          val result = pushManager.deleteTarget(id)
          result.fold(
            error => complete(ApiResponse[Boolean](success = false, message = Some(error.getMessage))),
            _ => complete(ApiResponse[Boolean](success = true))
          )
        }
      } ~
      path("history") {
        get {
          val history = pushManager.listHistory()
          complete(ApiResponse(success = true, data = Some(history)))
        }
      } ~
      path("folder") {
        post {
          entity(as[JsObject]) { json =>
            val sourceFolder = json.fields("sourceFolder").convertTo[String]
            val targetId = json.fields("targetId").convertTo[String]
            
            val result = pushManager.pushFolder(sourceFolder, targetId)
            result.fold(
              error => complete(ApiResponse[Boolean](success = false, message = Some(error.getMessage))),
              history => complete(ApiResponse[PushHistory](success = true, data = Some(history)))
            )
          }
        }
      }
    },
    
    // 系统信息API
    path("api" / "system" / "info") {
      get {
        val info = Map(
          "version" -> "2.0",
          "language" -> "Scala",
          "framework" -> "Akka HTTP",
          "port" -> 8093
        )
        complete(HttpEntity(ContentTypes.`application/json`, info.toJson.prettyPrint))
      }
    },
    
    // 健康检查
    path("api" / "health") {
      get {
        complete(ApiResponse(success = true, message = Some("OK")))
      }
    }
  )
}