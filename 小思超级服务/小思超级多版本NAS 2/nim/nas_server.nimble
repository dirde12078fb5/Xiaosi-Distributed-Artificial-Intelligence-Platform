# Package信息
version       = "2.0.0"
author        = "Xiaosi Team"
description   = "小思超级多版本NAS服务 - Nim高性能实现"
license       = "MIT"
srcDir        = "."

# 依赖包
requires "nim >= 1.6.0"
requires "jester >= 0.5.0"
requires "mimetypes >= 1.0.0"

# 任务定义
task run, "编译并运行NAS服务器":
  exec "nim c -r server.nim"

task build, "编译生产版本":
  exec "nim c -d:release -d:ssl server.nim"

task clean, "清理编译文件":
  exec "del server.exe"
  exec "del *.pdb"

task install, "安装依赖":
  exec "nimble install jester -y"
  exec "nimble install mimetypes -y"