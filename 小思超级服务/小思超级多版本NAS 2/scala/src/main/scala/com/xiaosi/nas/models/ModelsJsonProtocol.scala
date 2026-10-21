package com.xiaosi.nas.models

import spray.json._

/**
 * JSON序列化协议
 */
trait ModelsJsonProtocol extends DefaultJsonProtocol {
  implicit val volumeFormat: JsonFormat[Volume] = jsonFormat7(Volume)
  implicit val userFormat: JsonFormat[User] = jsonFormat7(User)
  implicit val smbShareFormat: JsonFormat[SMBShare] = jsonFormat8(SMBShare)
  implicit val pushTargetFormat: JsonFormat[PushTarget] = jsonFormat6(PushTarget)
  implicit val pushHistoryFormat: JsonFormat[PushHistory] = jsonFormat8(PushHistory)
  implicit val deviceFormat: JsonFormat[Device] = jsonFormat4(Device)
  implicit val nasConfigFormat: JsonFormat[NASConfig] = jsonFormat8(NASConfig)
  
  // ApiResponse的特殊处理（因为Option字段）
  implicit def apiResponseFormat[T: JsonFormat]: JsonFormat[ApiResponse[T]] = new JsonFormat[ApiResponse[T]] {
    def write(response: ApiResponse[T]): JsValue = {
      val fields = List(
        "success" -> JsBoolean(response.success),
        "message" -> response.message.map(JsString).getOrElse(JsNull),
        "data" -> response.data.map(_.toJson).getOrElse(JsNull)
      ).filterNot(_._2 == JsNull)
      JsObject(fields.toMap)
    }
    
    def read(value: JsValue): ApiResponse[T] = {
      val obj = value.asJsObject
      ApiResponse[T](
        success = obj.fields("success").convertTo[Boolean],
        message = obj.fields.get("message").map(_.convertTo[String]),
        data = obj.fields.get("data").map(_.convertTo[T])
      )
    }
  }
}

object ModelsJsonProtocol extends ModelsJsonProtocol