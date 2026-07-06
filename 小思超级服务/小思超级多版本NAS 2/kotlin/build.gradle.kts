plugins {
    kotlin("jvm") version "1.9.21"
    application
    id("io.ktor.plugin") version "2.3.7"
}

group = "com.xiaosi"
version = "1.0.0"

repositories {
    mavenCentral()
}

dependencies {
    implementation("io.ktor:ktor-server-core-jvm:2.3.7")
    implementation("io.ktor:ktor-server-netty-jvm:2.3.7")
    implementation("io.ktor:ktor-server-content-negotiation-jvm:2.3.7")
    implementation("io.ktor:ktor-serialization-kotlinx-json-jvm:2.3.7")
    implementation("io.ktor:ktor-server-cors-jvm:2.3.7")
    implementation("io.ktor:ktor-server-status-pages-jvm:2.3.7")

    implementation("ch.qos.logback:logback-classic:1.4.14")
    implementation("com.google.code.gson:gson:2.10.1")

    testImplementation("io.ktor:ktor-server-tests-jvm:2.3.7")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit:1.9.21")
}

kotlin {
    jvmToolchain(17)
}

application {
    mainClass.set("com.xiaosi.nas.ApplicationKt")
}

tasks.withType<Jar> {
    manifest {
        attributes["Main-Class"] = "com.xiaosi.nas.ApplicationKt"
    }
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
    from(configurations.runtimeClasspath.get().map { if (it.isDirectory) it else zipTree(it) })
}