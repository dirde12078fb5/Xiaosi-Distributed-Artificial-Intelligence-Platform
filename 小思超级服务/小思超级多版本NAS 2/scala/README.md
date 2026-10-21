# 小思超级多版本NAS服务 - Scala实现

## 项目简介

基于Akka HTTP框架的完整NAS服务实现，支持存储管理、用户管理、SMB共享、文件推送等功能。

## 技术栈

- **语言**: Scala 2.13.12
- **框架**: Akka HTTP 10.5.3
- **构建工具**: SBT 1.9.7
- **JSON处理**: Spray JSON
- **日志**: Logback

## 功能特性

✅ 完整的REST API接口  
✅ 28种语言翻译支持  
✅ 存储卷管理  
✅ 用户管理  
✅ SMB共享管理  
✅ 文件推送功能  
✅ IP地址扫描  
✅ config.json配置支持  
✅ 默认端口: 8093  

## 项目结构

```
scala/
├── build.sbt                          # SBT构建配置
├── start.bat                          # Windows启动脚本
├── project/
│   └── build.properties               # SBT版本配置
├── src/
│   ├── main/
│   │   ├── scala/
│   │   │   └── com/xiaosi/nas/
│   │   │       ├── NASServer.scala      # 主服务器
│   │   │       ├── config/
│   │   │       │   └── ConfigManager.scala  # 配置管理
│   │   │       ├── i18n/
│   │   │       │   └── Translations.scala   # 多语言支持
│   │   │       ├── managers/
│   │   │       │   ├── StorageManager.scala # 存储管理
│   │   │       │   ├── UserManager.scala    # 用户管理
│   │   │       │   ├── SMBManager.scala     # SMB管理
│   │   │       │   ├── PushManager.scala    # 推送管理
│   │   │       │   └── IPManager.scala      # IP管理
│   │   │       ├── models/
│   │   │       │   ├── Models.scala         # 数据模型
│   │   │       │   └── ModelsJsonProtocol.scala # JSON协议
│   │   │       └── routes/
│   │   │           └ Routes.scala          # API路由
│   │   └── resources/
│   │       ├── application.conf          # Akka配置
│   │       └── logback.xml               # 日志配置
```

## 快速启动

### 前置要求

1. **JDK 11+**: 确保Java环境已安装
2. **SBT**: Scala构建工具

### 安装SBT

```bash
# Windows (使用 scoop)
scoop install sbt

# 或手动安装
# 下载: https://www.scala-sbt.org/download.html
```

### 启动服务

**方式1: 使用启动脚本**
```bash
start.bat
```

**方式2: 手动启动**
```bash
cd scala
sbt run
```

### 编译打包

```bash
sbt package
sbt assembly  # 生成独立可执行jar
```

## API接口文档

### 存储管理
- `GET /api/storage/volumes` - 获取存储卷列表
- `POST /api/storage/volumes` - 创建存储卷
- `GET /api/storage/volumes/{id}` - 获取存储卷详情
- `DELETE /api/storage/volumes/{id}` - 删除存储卷

### 用户管理
- `GET /api/users` - 获取用户列表
- `POST /api/users` - 创建用户
- `GET /api/users/{id}` - 获取用户详情
- `DELETE /api/users/{id}` - 删除用户

### SMB共享管理
- `GET /api/smb/shares` - 获取共享列表
- `POST /api/smb/shares` - 创建共享
- `GET /api/smb/status` - 获取SMB状态
- `DELETE /api/smb/shares/{id}` - 删除共享

### IP管理
- `GET /api/ip/local` - 获取本机IP地址
- `GET /api/ip/scan?port={port}` - 扫描LAN设备

### 推送管理
- `GET /api/push/targets` - 获取推送目标列表
- `POST /api/push/targets` - 添加推送目标
- `DELETE /api/push/targets/{id}` - 删除推送目标
- `GET /api/push/history` - 获取推送历史
- `POST /api/push/folder` - 推送文件夹

### 多语言支持
- `GET /api/i18n?lang={lang}` - 获取指定语言翻译

### 其他
- `GET /api/system/info` - 获取系统信息
- `GET /api/health` - 健康检查

## 配置文件

配置文件位置: `../config/config.json`

```json
{
  "port": 8093,
  "language": "zh_CN",
  "dataDir": "./data",
  "volumes": [],
  "users": [],
  "shares": [],
  "pushTargets": [],
  "pushHistory": []
}
```

## 支持的语言

支持28种语言翻译，包括但不限于:
- 中文（简体/繁体）
- 英语
- 日语
- 韩语
- 德语
- 法语
- 西班牙语
- 俄语
- 阿拉伯语
- 印地语
- 以及更多...

## Scala最佳实践

本项目遵循以下Scala最佳实践:

1. **函数式编程**: 使用不可变数据结构、纯函数
2. **类型安全**: 强类型系统、case class
3. **模块化设计**: 清晰的包结构和职责分离
4. **错误处理**: 使用Try/Option进行安全的错误处理
5. **异步处理**: 基于Akka的异步IO
6. **JSON序列化**: Spray JSON自动类型推导
7. **配置管理**: Typesafe Config + 自定义JSON配置

## 开发指南

### 添加新功能

1. 在 `models/` 添加数据模型
2. 在 `managers/` 添加管理逻辑
3. 在 `routes/` 添加API路由
4. 在 `i18n/` 添加翻译支持

### 测试

```bash
sbt test
```

## 性能优化

- Akka HTTP高性能异步IO
- 非阻塞请求处理
- 高效的JSON序列化
- 内存友好的数据结构

## 许可证

MIT License

## 作者

小思团队

## 版本

第二代 - Version 2.0.0