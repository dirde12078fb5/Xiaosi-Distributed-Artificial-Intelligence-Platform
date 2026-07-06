package com.xiaosi.nas.managers

import java.net.{InetAddress, NetworkInterface, Socket}
import scala.collection.JavaConverters._

/**
 * IP地址管理器
 */
object IPManager {
  
  def getLocalIPs(): List[String] = {
    Try {
      NetworkInterface.getNetworkInterfaces.asScala.toList
        .filter(_.isUp)
        .flatMap(_.getInetAddresses.asScala.toList)
        .filter(addr => addr.isInstanceOf[InetAddress] && addr.getHostAddress.contains("."))
        .map(_.getHostAddress)
        .distinct
    }.getOrElse(List("127.0.0.1"))
  }
  
  def scanLAN(port: Int = 8093): List[Device] = {
    val localIPs = getLocalIPs()
    val baseIPs = localIPs.map(ip => ip.split(".").take(3).mkString("."))
    
    baseIPs.flatMap { baseIP =>
      (1 to 254).flatMap { i =>
        val testIP = s"$baseIP.$i"
        if (!localIPs.contains(testIP)) {
          checkDevice(testIP, port)
        } else None
      }
    }.distinct
  }
  
  private def checkDevice(ip: String, port: Int): Option[Device] = {
    Try {
      val socket = new Socket()
      socket.connect(new java.net.InetSocketAddress(ip, port), 1000)
      socket.close()
      
      Some(Device(
        ip = ip,
        port = port,
        online = true,
        hostname = getHostname(ip)
      ))
    }.toOption
  }
  
  private def getHostname(ip: String): Option[String] = {
    Try {
      val addr = InetAddress.getByName(ip)
      val hostname = addr.getHostName
      if (hostname != ip) Some(hostname) else None
    }.toOption.flatten
  }
}

import scala.util.Try
import com.xiaosi.nas.models.Device