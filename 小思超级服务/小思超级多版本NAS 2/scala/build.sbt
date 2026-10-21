name := "xiaosi-nas-scala"
version := "2.0.0"
scalaVersion := "2.13.12"

// Akka HTTP 依赖
libraryDependencies ++= Seq(
  "com.typesafe.akka" %% "akka-http" % "10.5.3",
  "com.typesafe.akka" %% "akka-http-spray-json" % "10.5.3",
  "com.typesafe.akka" %% "akka-stream" % "2.8.5",
  "com.typesafe.akka" %% "akka-actor-typed" % "2.8.5",
  // JSON处理
  "io.spray" %% "spray-json" % "1.3.6",
  // 日志
  "com.typesafe.akka" %% "akka-slf4j" % "2.8.5",
  "ch.qos.logback" % "logback-classic" % "1.4.11",
  // 配置文件
  "com.typesafe" % "config" % "1.4.3"
)

// 编译选项
scalacOptions ++= Seq(
  "-deprecation",
  "-encoding", "UTF-8",
  "-feature",
  "-unchecked",
  "-Xlint:_",
  "-Ywarn-dead-code",
  "-Ywarn-numeric-widen"
)

// 运行设置
Compile / mainClass := Some("com.xiaosi.nas.NASServer")
run / fork := true