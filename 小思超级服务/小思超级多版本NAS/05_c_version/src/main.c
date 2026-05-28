/*
 * 小思超级NAS - C语言版本
 * 智能存储管理平台
 * 
 * 作者: 小思AI团队
 * 版本: 1.0.0
 * 
 * 编译(Windows): gcc main.c -o xiaosi-nas-c.exe -lws2_32
 * 编译(Linux):   gcc main.c -o xiaosi-nas-c -lpthread
 * 运行:          ./xiaosi-nas-c
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    typedef int socklen_t;
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    typedef int SOCKET;
    #define closesocket close
    #define SOCKET_ERROR (-1)
#endif

// ==================== 配置 ====================
#define PORT 8080
#define BUFFER_SIZE 65536
#define ROOT_DIR "../public"

// ==================== 用户数据 ====================
typedef struct {
    char username[64];
    char password[64];
    char role[32];
} User;

User users[] = {
    {"admin", "admin123", "admin"},
    {"zhangsan", "password", "user"},
    {"lisi", "password", "user"}
};
int user_count = sizeof(users) / sizeof(users[0]);

// ==================== 工具函数 ====================
const char* get_mime_type(const char *path) {
    const char *ext = strrchr(path, '.');
    if (!ext) return "application/octet-stream";
    
    if (strcmp(ext, ".html") == 0) return "text/html; charset=UTF-8";
    if (strcmp(ext, ".css") == 0) return "text/css; charset=UTF-8";
    if (strcmp(ext, ".js") == 0) return "application/javascript; charset=UTF-8";
    if (strcmp(ext, ".json") == 0) return "application/json; charset=UTF-8";
    if (strcmp(ext, ".png") == 0) return "image/png";
    if (strcmp(ext, ".jpg") == 0 || strcmp(ext, ".jpeg") == 0) return "image/jpeg";
    if (strcmp(ext, ".gif") == 0) return "image/gif";
    
    return "application/octet-stream";
}

void send_response(SOCKET client_fd, const char *content, const char *content_type, int status_code) {
    char header[1024];
    snprintf(header, sizeof(header),
        "HTTP/1.1 %d\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %ld\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Connection: close\r\n"
        "\r\n",
        status_code, content_type, strlen(content));
    
    send(client_fd, header, strlen(header), 0);
    send(client_fd, content, strlen(content), 0);
}

void send_file(SOCKET client_fd, const char *filepath) {
    FILE *f = fopen(filepath, "rb");
    if (!f) {
        const char *not_found = "404 Not Found";
        send_response(client_fd, not_found, "text/plain", 404);
        return;
    }
    
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    char *content = malloc(size + 1);
    fread(content, 1, size, f);
    content[size] = '\0';
    fclose(f);
    
    send_response(client_fd, content, get_mime_type(filepath), 200);
    free(content);
}

void generate_welcome_page(char *buffer, size_t size) {
    snprintf(buffer, size,
        "<!DOCTYPE html>"
        "<html><head><meta charset='UTF-8'><title>小思超级NAS</title>"
        "<style>"
        "body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #0a0e17, #1a1f2e); color: #fff; min-height: 100vh; display: flex; align-items: center; justify-content: center; }"
        ".container { text-align: center; max-width: 600px; padding: 40px; }"
        ".logo { font-size: 80px; margin-bottom: 24px; }"
        "h1 { background: linear-gradient(135deg, #0066ff, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 36px; margin-bottom: 16px; }"
        "p { color: #9ca3af; font-size: 18px; margin-bottom: 32px; }"
        ".info { background: #111827; border: 1px solid #1f2937; border-radius: 16px; padding: 32px; }"
        ".info h3 { color: #0066ff; margin-bottom: 16px; }"
        ".info p { font-size: 14px; margin-bottom: 8px; }"
        ".tech { display: flex; gap: 12px; justify-content: center; margin-top: 24px; }"
        ".tech span { background: linear-gradient(135deg, #0066ff, #7c3aed); padding: 8px 20px; border-radius: 20px; font-size: 14px; }"
        "</style></head><body>"
        "<div class='container'>"
        "<div class='logo'>💾</div>"
        "<h1>小思超级NAS</h1>"
        "<p>C 语言版本 - 高性能存储管理平台</p>"
        "<div class='info'>"
        "<h3>📡 访问地址</h3>"
        "<p>本地访问: http://localhost:%d</p>"
        "<p>局域网访问: http://&lt;您的IP&gt;:%d</p>"
        "<br><h3>👤 默认登录</h3>"
        "<p>用户名: admin</p>"
        "<p>密码: admin123</p>"
        "<div class='tech'><span>C</span><span>libmicrohttpd</span><span>libuv</span></div>"
        "</div></div></body></html>", PORT, PORT);
}

// ==================== 请求处理 ====================
void handle_request(SOCKET client_fd, const char *request) {
    char method[16], url[256], version[16];
    sscanf(request, "%s %s %s", method, url, version);
    
    printf("[C-NAS] %s: %s\n", method, url);
    
    // 首页
    if (strcmp(url, "/") == 0 || strcmp(url, "/index.html") == 0) {
        char filepath[512];
        snprintf(filepath, sizeof(filepath), "%s/index.html", ROOT_DIR);
        
        FILE *f = fopen(filepath, "r");
        if (f) {
            fseek(f, 0, SEEK_END);
            long size = ftell(f);
            fseek(f, 0, SEEK_SET);
            
            char *content = malloc(size + 1);
            fread(content, 1, size, f);
            content[size] = '\0';
            fclose(f);
            
            send_response(client_fd, content, "text/html; charset=UTF-8", 200);
            free(content);
        } else {
            char welcome[8192];
            generate_welcome_page(welcome, sizeof(welcome));
            send_response(client_fd, welcome, "text/html; charset=UTF-8", 200);
        }
    }
    // API端点
    else if (strcmp(url, "/api/stats") == 0) {
        const char *json = "{\"success\":true,\"data\":{\"storage\":{\"used\":2684354560,\"total\":4294967296,\"percentage\":62.5},\"files\":{\"count\":1284},\"users\":{\"total\":3,\"online\":2}}}";
        send_response(client_fd, json, "application/json", 200);
    }
    else if (strcmp(url, "/api/files") == 0) {
        const char *json = "{\"success\":true,\"data\":[{\"id\":\"1\",\"name\":\"项目文档\",\"type\":\"folder\",\"icon\":\"📁\"},{\"id\":\"2\",\"name\":\"照片备份\",\"type\":\"folder\",\"icon\":\"📁\"},{\"id\":\"3\",\"name\":\"项目报告.pdf\",\"type\":\"file\",\"icon\":\"📄\",\"size\":2621440}]}";
        send_response(client_fd, json, "application/json", 200);
    }
    else if (strcmp(url, "/api/users") == 0) {
        const char *json = "{\"success\":true,\"data\":[{\"username\":\"admin\",\"role\":\"admin\",\"status\":\"online\"},{\"username\":\"zhangsan\",\"role\":\"user\",\"status\":\"online\"}]}";
        send_response(client_fd, json, "application/json", 200);
    }
    // 静态文件
    else {
        char filepath[512];
        snprintf(filepath, sizeof(filepath), "%s%s", ROOT_DIR, url);
        
        FILE *f = fopen(filepath, "rb");
        if (f) {
            fclose(f);
            send_file(client_fd, filepath);
        } else {
            const char *not_found = "404 Not Found";
            send_response(client_fd, not_found, "text/plain", 404);
        }
    }
}

// ==================== 主程序 ====================
int main() {
    #ifdef _WIN32
        WSADATA wsa;
        WSAStartup(MAKEWORD(2, 2), &wsa);
    #endif
    
    SOCKET server_fd, client_fd;
    struct sockaddr_in address;
    int opt = 1;
    socklen_t addrlen = sizeof(address);
    
    // 创建socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) {
        perror("socket failed");
        return 1;
    }
    
    // 设置socket选项
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    // 绑定地址
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) == -1) {
        perror("bind failed");
        return 1;
    }
    
    // 监听
    if (listen(server_fd, 10) == -1) {
        perror("listen failed");
        return 1;
    }
    
    printf("\n");
    printf("============================================\n");
    printf("   🚀 小思超级NAS (C语言版本) 已启动！\n");
    printf("============================================\n");
    printf("\n📡 访问地址：\n");
    printf("   本地访问：http://localhost:%d\n", PORT);
    printf("   局域网访问：http://<您的IP>:%d\n", PORT);
    printf("\n👤 默认登录：\n");
    printf("   用户名：admin\n");
    printf("   密码：admin123\n");
    printf("\n============================================\n");
    printf("\n按 Ctrl+C 停止服务器...\n\n");
    
    // 接受连接
    while (1) {
        client_fd = accept(server_fd, (struct sockaddr *)&address, &addrlen);
        if (client_fd == -1) {
            perror("accept failed");
            continue;
        }
        
        char buffer[BUFFER_SIZE] = {0};
        int bytes = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);
        
        if (bytes > 0) {
            handle_request(client_fd, buffer);
        }
        
        closesocket(client_fd);
    }
    
    closesocket(server_fd);
    #ifdef _WIN32
        WSACleanup();
    #endif
    
    return 0;
}
