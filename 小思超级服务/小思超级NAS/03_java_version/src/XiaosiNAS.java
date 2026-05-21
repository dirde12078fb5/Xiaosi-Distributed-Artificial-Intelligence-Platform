/**
 * 小思超级NAS - Java版本
 * 智能存储管理平台
 * 
 * 作者: 小思AI团队
 * 版本: 1.0.0
 * 
 * 使用JDK内置的com.sun.net.httpserver，无需额外依赖
 * 
 * 编译: javac XiaosiNAS.java
 * 运行: java XiaosiNAS
 */

package com.xiaosi.nas;

import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.*;

public class XiaosiNAS {
    
    // ==================== 配置 ====================
    private static final int PORT = 8080;
    private static final String HOST = "0.0.0.0";
    private static final String STATIC_DIR = "../public";
    private static final String STORAGE_DIR = "../storage";
    
    // 用户数据
    private static final Map<String, User> users = new HashMap<>();
    
    public static void main(String[] args) throws Exception {
        initUsers();
        startServer();
    }
    
    // ==================== 用户初始化 ====================
    private static void initUsers() {
        users.put("admin", new User("1", "admin", "admin@xiaosi.com", "admin123", "admin", 10L * 1024 * 1024 * 1024));
        users.put("zhangsan", new User("2", "zhangsan", "zhangsan@xiaosi.com", "password", "user", 1L * 1024 * 1024 * 1024));
        users.put("lisi", new User("3", "lisi", "lisi@xiaosi.com", "password", "user", 1L * 1024 * 1024 * 1024));
    }
    
    // ==================== 服务器启动 ====================
    private static void startServer() throws IOException {
        InetSocketAddress addr = new InetSocketAddress(PORT);
        HttpServer server = HttpServer.create(addr, 0);
        
        // 路由配置
        server.createContext("/", new StaticHandler());
        server.createContext("/api/stats", new StatsHandler());
        server.createContext("/api/files", new FilesHandler());
        server.createContext("/api/users", new UsersHandler());
        server.createContext("/api/settings", new SettingsHandler());
        server.createContext("/api/auth/login", new LoginHandler());
        
        server.setExecutor(Executors.newCachedThreadPool());
        server.start();
        
        printStartup();
        
        // 添加关闭钩子
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.out.println("\n正在关闭服务器...");
            server.stop(0);
        }));
    }
    
    // ==================== 用户类 ====================
    static class User {
        String id;
        String username;
        String email;
        String password;
        String role;
        long storageQuota;
        LocalDateTime lastLogin;
        
        User(String id, String username, String email, String password, String role, long storageQuota) {
            this.id = id;
            this.username = username;
            this.email = email;
            this.password = password;
            this.role = role;
            this.storageQuota = storageQuota;
            this.lastLogin = LocalDateTime.now();
        }
    }
    
    // ==================== 处理器 ====================
    
    // 静态文件处理器
    static class StaticHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String path = exchange.getRequestURI().getPath();
            if (path.equals("/")) path = "/index.html";
            
            File file = new File(STATIC_DIR + path);
            
            if (file.exists() && !file.isDirectory()) {
                String contentType = getContentType(path);
                exchange.getResponseHeaders().set("Content-Type", contentType);
                
                byte[] content = Files.readAllBytes(file.toPath());
                exchange.sendResponseHeaders(200, content.length);
                
                OutputStream os = exchange.getResponseBody();
                os.write(content);
                os.close();
            } else {
                String html = generateWelcomePage();
                exchange.getResponseHeaders().set("Content-Type", "text/html; charset=UTF-8");
                byte[] content = html.getBytes("UTF-8");
                exchange.sendResponseHeaders(200, content.length);
                OutputStream os = exchange.getResponseBody();
                os.write(content);
                os.close();
            }
        }
        
        private String getContentType(String path) {
            if (path.endsWith(".html")) return "text/html; charset=UTF-8";
            if (path.endsWith(".css")) return "text/css; charset=UTF-8";
            if (path.endsWith(".js")) return "application/javascript; charset=UTF-8";
            if (path.endsWith(".json")) return "application/json; charset=UTF-8";
            if (path.endsWith(".png")) return "image/png";
            if (path.endsWith(".jpg") || path.endsWith(".jpeg")) return "image/jpeg";
            return "application/octet-stream";
        }
        
        private String generateWelcomePage() {
            return "<!DOCTYPE html>" +
                "<html><head><meta charset='UTF-8'><title>小思超级NAS</title>" +
                "<style>" +
                "body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #0a0e17, #1a1f2e); color: #fff; min-height: 100vh; display: flex; align-items: center; justify-content: center; }" +
                ".container { text-align: center; max-width: 600px; padding: 40px; }" +
                ".logo { font-size: 80px; margin-bottom: 24px; }" +
                "h1 { background: linear-gradient(135deg, #0066ff, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 36px; margin-bottom: 16px; }" +
                "p { color: #9ca3af; font-size: 18px; margin-bottom: 32px; }" +
                ".info { background: #111827; border: 1px solid #1f2937; border-radius: 16px; padding: 32px; }" +
                ".info h3 { color: #0066ff; margin-bottom: 16px; }" +
                ".info p { font-size: 14px; margin-bottom: 8px; }" +
                "</style></head><body>" +
                "<div class='container'>" +
                "<div class='logo'>💾</div>" +
                "<h1>小思超级NAS</h1>" +
                "<p>Java 版本 - 企业级存储管理平台</p>" +
                "<div class='info'>" +
                "<h3>📡 访问地址</h3>" +
                "<p>本地访问: http://localhost:" + PORT + "</p>" +
                "<p>局域网访问: http://&lt;您的IP&gt;:" + PORT + "</p>" +
                "<br><h3>👤 默认登录</h3>" +
                "<p>用户名: admin</p>" +
                "<p>密码: admin123</p>" +
                "</div></div></body></html>";
        }
    }
    
    // 统计API处理器
    static class StatsHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String json = "{\"success\":true,\"data\":{" +
                "\"storage\":{\"used\":2684354560,\"total\":4294967296,\"percentage\":62.5}," +
                "\"files\":{\"count\":1284,\"recent\":[{\"name\":\"项目报告.pdf\",\"user\":\"admin\",\"time\":\"5分钟前\"}]}," +
                "\"users\":{\"total\":" + users.size() + ",\"online\":2}}}";
            
            sendJsonResponse(exchange, json);
        }
    }
    
    // 文件列表API处理器
    static class FilesHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String json = "{\"success\":true,\"data\":[" +
                "{\"id\":\"1\",\"name\":\"项目文档\",\"type\":\"folder\",\"icon\":\"📁\",\"size\":0}," +
                "{\"id\":\"2\",\"name\":\"照片备份\",\"type\":\"folder\",\"icon\":\"📁\",\"size\":0}," +
                "{\"id\":\"3\",\"name\":\"项目报告.pdf\",\"type\":\"file\",\"icon\":\"📄\",\"size\":2621440}," +
                "{\"id\":\"4\",\"name\":\"会议纪要.docx\",\"type\":\"file\",\"icon\":\"📝\",\"size\":159744}," +
                "{\"id\":\"5\",\"name\":\"数据表格.xlsx\",\"type\":\"file\",\"icon\":\"📊\",\"size\":911360}" +
                "]}";
            
            sendJsonResponse(exchange, json);
        }
    }
    
    // 用户列表API处理器
    static class UsersHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            StringBuilder json = new StringBuilder("{\"success\":true,\"data\":[");
            boolean first = true;
            for (User user : users.values()) {
                if (!first) json.append(",");
                json.append("{\"username\":\"").append(user.username).append("\",")
                   .append("\"email\":\"").append(user.email).append("\",")
                   .append("\"role\":\"").append(user.role).append("\",")
                   .append("\"status\":\"online\",")
                   .append("\"storage_quota\":").append(user.storageQuota).append("}");
                first = false;
            }
            json.append("]}");
            
            sendJsonResponse(exchange, json.toString());
        }
    }
    
    // 系统设置API处理器
    static class SettingsHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String json = "{\"success\":true,\"data\":{" +
                "\"general\":{\"system_name\":\"小思超级NAS\",\"timezone\":\"Asia/Shanghai\",\"language\":\"zh-CN\",\"theme\":\"dark\"}," +
                "\"network\":{\"ip\":\"" + HOST + "\",\"port\":" + PORT + "}}}";
            
            sendJsonResponse(exchange, json);
        }
    }
    
    // 登录API处理器
    static class LoginHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if ("POST".equals(exchange.getRequestMethod())) {
                String body = new String(exchange.getRequestBody().readAllBytes());
                System.out.println("Login attempt: " + body);
                
                String json = "{\"success\":true,\"data\":{" +
                    "\"token\":\"jwt-token-sample\"," +
                    "\"user\":{\"id\":\"1\",\"username\":\"admin\",\"role\":\"admin\"}}}";
                
                sendJsonResponse(exchange, json);
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
        }
    }
    
    // 发送JSON响应
    private static void sendJsonResponse(HttpExchange exchange, String json) throws IOException {
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
        exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        byte[] content = json.getBytes("UTF-8");
        exchange.sendResponseHeaders(200, content.length);
        OutputStream os = exchange.getResponseBody();
        os.write(content);
        os.close();
    }
    
    // 打印启动信息
    private static void printStartup() {
        System.out.println();
        System.out.println("============================================");
        System.out.println("   🚀 小思超级NAS (Java版本) 已启动！");
        System.out.println("============================================");
        System.out.println();
        System.out.println("📡 访问地址：");
        System.out.println("   本地访问：http://localhost:" + PORT);
        System.out.println("   局域网访问：http://<您的IP>:" + PORT);
        System.out.println();
        System.out.println("👤 默认登录：");
        System.out.println("   用户名：admin");
        System.out.println("   密码：admin123");
        System.out.println();
        System.out.println("============================================");
    }
}
