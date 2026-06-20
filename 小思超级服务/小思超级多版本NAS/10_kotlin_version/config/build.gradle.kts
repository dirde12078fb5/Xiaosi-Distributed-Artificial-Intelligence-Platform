plugins {
    kotlin("jvm") version "1.9.22"
    kotlin("plugin.serialization") version "1.9.22"
    application
}

group = "com.xiaosi.nas"
version = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    // Ktor服务器核心依赖
    val ktorVersion = "2.3.7"
    
    // Ktor服务器引擎
    implementation("io.ktor:ktor-server-core-jvm:$ktorVersion")
    implementation("io.ktor:ktor-server-netty-jvm:$ktorVersion")
    
    // Ktor客户端 (可选)
    implementation("io.ktor:ktor-client-core-jvm:$ktorVersion")
    implementation("io.ktor:ktor-client-cio-jvm:$ktorVersion")
    
    // Ktor插件
    implementation("io.ktor:ktor-server-content-negotiation-jvm:$ktorVersion")
    implementation("io.ktor:ktor-serialization-kotlinx-json:$ktorVersion")
    implementation("io.ktor:ktor-server-auth-jvm:$ktorVersion")
    implementation("io.ktor:ktor-server-auth-jwt-jvm:$ktorVersion")
    
    // JSON序列化
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2")
    
    // JWT库
    implementation("io.jsonwebtoken:jjwt-api:0.12.3")
    runtimeOnly("io.jsonwebtoken:jjwt-impl:0.12.3")
    runtimeOnly("io.jsonwebtoken:jjwt-jackson:0.12.3")
    
    // 日志框架
    implementation("ch.qos.logback:logback-classic:1.4.14")
    
    // 测试依赖
    testImplementation(kotlin("test"))
    testImplementation("io.ktor:ktor-server-tests-jvm:$ktorVersion")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit:1.9.22")
}

kotlin {
    jvmToolchain(17)
}

application {
    mainClass.set("com.xiaosi.nas.MainKt")
}

tasks.withType<Jar> {
    manifest {
        attributes(
            "Main-Class" to "com.xiaosi.nas.MainKt"
        )
    }
    
    // 创建fat jar，包含所有依赖
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
    
    from(configurations.runtimeClasspath.get().map { if (it.isDirectory) it else zipTree(it) })
}
