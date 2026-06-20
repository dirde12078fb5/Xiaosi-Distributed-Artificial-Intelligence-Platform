package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/dgrijalva/jwt-go"
	"github.com/gorilla/mux"
	"golang.org/x/crypto/bcrypt"
)

// ==================== 配置 ====================
type Config struct {
	Port         int
	Host         string
	PublicPath   string
	StoragePath  string
	JWTSecret    string
	DefaultUser  string
	DefaultPass  string
}

var config = Config{
	Port:         8080,
	Host:         "0.0.0.0",
	PublicPath:   "../public",
	StoragePath:  "../storage",
	JWTSecret:    "xiaosi-nas-go-secret-2024",
	DefaultUser:  "admin",
	DefaultPass:  "admin123",
}

// ==================== 用户模型 ====================
type User struct {
	ID           string `json:"id"`
	Username     string `json:"username"`
	Email        string `json:"email"`
	PasswordHash string `json:"-"`
	Role         string `json:"role"`
	CreatedAt    time.Time `json:"created_at"`
}

var users = map[string]User{
	"admin": {
		ID:       "1",
		Username: "admin",
		Email:    "admin@xiaosi.com",
		Role:     "admin",
	},
	"zhangsan": {
		ID:       "2",
		Username: "zhangsan",
		Email:    "zhangsan@xiaosi.com",
		Role:     "user",
	},
}

func init() {
	hashed, _ := bcrypt.GenerateFromPassword([]byte(config.DefaultPass), bcrypt.DefaultCost)
	users["admin"].PasswordHash = string(hashed)
	users["admin"].CreatedAt = time.Now()

	hashed2, _ := bcrypt.GenerateFromPassword([]byte("password"), bcrypt.DefaultCost)
	users["zhangsan"].PasswordHash = string(hashed2)
	users["zhangsan"].CreatedAt = time.Now()
}

// ==================== JWT中间件 ====================
func authMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			http.Error(w, `{"success":false,"message":"Authorization required"}`, http.StatusUnauthorized)
			return
		}

		tokenString := strings.Replace(authHeader, "Bearer ", "", 1)
		token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
			return []byte(config.JWTSecret), nil
		})

		if err != nil || !token.Valid {
			http.Error(w, `{"success":false,"message":"Invalid token"}`, http.StatusUnauthorized)
			return
		}

		next.ServeHTTP(w, r)
	}
}

// ==================== API处理器 ====================

func loginHandler(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}

	json.NewDecoder(r.Body).Decode(&req)

	user, exists := users[req.Username]
	if !exists {
		http.Error(w, `{"success":false,"message":"Invalid credentials"}`, http.StatusUnauthorized)
		return
	}

	err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password))
	if err != nil {
		http.Error(w, `{"success":false,"message":"Invalid credentials"}`, http.StatusUnauthorized)
		return
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"user_id": user.ID,
		"username": user.Username,
		"role":     user.Role,
		"exp":      time.Now().Add(24 * time.Hour).Unix(),
	})

	tokenString, _ := token.SignedString([]byte(config.JWT_SECRET))

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"data": map[string]interface{}{
			"token": tokenString,
			"user": map[string]string{
				"id":       user.ID,
				"username": user.Username,
				"role":     user.Role,
				"email":    user.Email,
			},
		},
	})
}

func statsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"data": map[string]interface{}{
			"storage": map[string]interface{}{
				"used":       2684354560,
				"total":      4294967296,
				"percentage": 62.5,
			},
			"files": map[string]interface{}{
				"count": 1284,
				"recent": []interface{}{
					map[string]string{
						"name": "项目报告.pdf",
						"user": "admin",
						"time": "5分钟前",
					},
					map[string]string{
						"name": "新用户注册",
						"user": "system",
						"time": "15分钟前",
					},
				},
			},
			"users": map[string]interface{}{
				"total":  len(users),
				"online": 2,
			},
		},
	})
}

func filesHandler(w http.ResponseWriter, r *http.Request) {
	files := []map[string]interface{}{
		{
			"id":         "1",
			"name":       "项目文档",
			"type":       "folder",
			"icon":       "📁",
			"size":       0,
			"modified_at": time.Now().Format(time.RFC3339),
		},
		{
			"id":         "2",
			"name":       "照片备份",
			"type":       "folder",
			"icon":       "📁",
			"size":       0,
			"modified_at": time.Now().Format(time.RFC3339),
		},
		{
			"id":         "3",
			"name":       "项目报告.pdf",
			"type":       "file",
			"icon":       "📄",
			"size":       2621440,
			"modified_at": time.Now().Format(time.RFC3339),
		},
		{
			"id":         "4",
			"name":       "会议纪要.docx",
			"type":       "file",
			"icon":       "📝",
			"size":       159744,
			"modified_at": time.Now().Format(time.RFC3339),
		},
		{
			"id":         "5",
			"name":       "数据表格.xlsx",
			"type":       "file",
			"icon":       "📊",
			"size":       911360,
			"modified_at": time.Now().Format(time.RFC3339),
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"data":    files,
	})
}

func usersHandler(w http.ResponseWriter, r *http.Request) {
	userList := make([]map[string]interface{}, 0)
	for _, user := range users {
		status := "offline"
		if time.Since(user.CreatedAt) < time.Hour {
			status = "online"
		}
		userList = append(userList, map[string]interface{}{
			"id":            user.ID,
			"username":      user.Username,
			"email":         user.Email,
			"role":          user.Role,
			"storage_quota": 10737418240,
			"status":        status,
			"last_login":    user.CreatedAt.Format(time.RFC3339),
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"data":    userList,
	})
}

func settingsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"data": map[string]interface{}{
			"general": map[string]string{
				"system_name": "小思超级NAS",
				"timezone":    "Asia/Shanghai",
				"language":    "zh-CN",
				"theme":       "dark",
			},
			"network": map[string]interface{}{
				"ip":   config.Host,
				"port": config.Port,
			},
		},
	})
}

// ==================== 静态文件服务 ====================
func staticFileServer(w http.ResponseWriter, r *http.Request) {
	path := filepath.Join(config.PublicPath, r.URL.Path)
	
	if _, err := os.Stat(path); os.IsNotExist(err) {
		path = filepath.Join(config.PublicPath, "index.html")
	}

	http.ServeFile(w, r, path)
}

func uploadFileHandler(w http.ResponseWriter, r *http.Request) {
	r.ParseMultipartForm(32 << 20)
	file, handler, err := r.FormFile("file")
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	defer file.Close()

	targetDir := config.StoragePath
	os.MkdirAll(targetDir, 0755)

	filePath := filepath.Join(targetDir, handler.Filename)
	f, err := os.Create(filePath)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer f.Close()

	io.Copy(f, file)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": fmt.Sprintf("文件 %s 上传成功", handler.Filename),
		"data": map[string]interface{}{
			"name": handler.Filename,
			"size": handler.Size,
			"path": "/storage/" + handler.Filename,
		},
	})
}

// ==================== 主函数 ====================
func main() {
	router := mux.NewRouter()
	
	api := router.PathPrefix("/api").Subrouter()
	
	api.HandleFunc("/auth/login", loginHandler).Methods("POST")
	api.HandleFunc("/stats", authMiddleware(statsHandler)).Methods("GET")
	api.HandleFunc("/files", authMiddleware(filesHandler)).Methods("GET")
	api.HandleFunc("/files/upload", authMiddleware(uploadFileHandler)).Methods("POST")
	api.HandleFunc("/users", authMiddleware(usersHandler)).Methods("GET")
	api.HandleFunc("/settings", authMiddleware(settingsHandler)).Methods("GET")

	router.PathPrefix("/").HandlerFunc(staticFileServer)

	fmt.Println("\n============================================")
	fmt.Println("   🚀 小思超级NAS (Go版本) 已启动！")
	fmt.Println("============================================")
	fmt.Println("\n📡 访问地址：")
	fmt.Printf("   本地访问：http://localhost:%d\n", config.Port)
	fmt.Println("   局域网访问：http://<您的IP>:", config.Port)
	fmt.Println("\n👤 默认登录：")
	fmt.Println("   用户名：admin")
	fmt.Println("   密码：admin123")
	fmt.Println("\n============================================\n")

	log.Fatal(http.ListenAndServe(fmt.Sprintf("%s:%d", config.Host, config.Port), router))
}
