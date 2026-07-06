package com.xiaosi.nas.models

/**
 * 数据模型定义
 */
case class Volume(
  id: String,
  name: String,
  path: String,
  quota: Long,  // GB
  used: Long,
  available: Long,
  created: Long
)

case class User(
  id: String,
  username: String,
  passwordHash: String,
  isAdmin: Boolean,
  storageQuota: Long,  // GB
  homeDirectory: String,
  created: Long
)

case class SMBShare(
  id: String,
  name: String,
  path: String,
  comment: String,
  readOnly: Boolean,
  browseable: Boolean,
  guestAccess: Boolean,
  created: Long
)

case class PushTarget(
  id: String,
  name: String,
  ip: String,
  port: Int,
  active: Boolean,
  created: Long
)

case class PushHistory(
  id: String,
  sourceFolder: String,
  targetId: String,
  targetName: String,
  fileCount: Int,
  totalSize: Long,
  status: String,
  timestamp: Long
)

case class Device(
  ip: String,
  port: Int,
  online: Boolean,
  hostname: Option[String]
)

// 配置模型
case class NASConfig(
  port: Int = 8093,
  language: String = "zh_CN",
  dataDir: String = "./data",
  volumes: List[Volume] = List.empty,
  users: List[User] = List.empty,
  shares: List[SMBShare] = List.empty,
  pushTargets: List[PushTarget] = List.empty,
  pushHistory: List[PushHistory] = List.empty
)

// API响应模型
case class ApiResponse[T](
  success: Boolean,
  message: Option[String] = None,
  data: Option[T] = None
)