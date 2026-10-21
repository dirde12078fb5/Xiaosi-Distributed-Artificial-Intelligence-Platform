package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"

	"xiaosi-nas/internal/config"
	"xiaosi-nas/internal/push"
	"xiaosi-nas/internal/smb"
	"xiaosi-nas/internal/storage"
	"xiaosi-nas/internal/user"
	"xiaosi-nas/internal/web"
)

func main() {
	// 获取配置文件路径
	configPath := getConfigPath()
	log.Printf("配置文件路径: %s", configPath)

	// 加载配置
	cfg, err := config.Load(configPath)
	if err != nil {
		log.Printf("加载配置失败: %v，使用默认配置", err)
		cfg = config.DefaultConfig()
		// 保存默认配置
		if err := cfg.Save(configPath); err != nil {
			log.Printf("保存默认配置失败: %v", err)
		}
	}

	// 初始化组件
	storageMgr := storage.NewManager(&cfg.Storage)
	userMgr := user.NewManager()
	smbServer := smb.NewServer(&cfg.SMB)
	pushMgr := push.NewManager(&cfg.Push)

	// 启动SMB服务
	if cfg.SMB.Enabled {
		if err := smbServer.Start(); err != nil {
			log.Printf("SMB服务启动失败: %v", err)
		} else {
			log.Println("SMB服务已启动")
		}
	}

	// 创建数据目录
	dataPath := filepath.Join(filepath.Dir(filepath.Dir(configPath)), "data")
	if err := os.MkdirAll(dataPath, 0755); err != nil {
		log.Printf("创建数据目录失败: %v", err)
	}
	log.Printf("数据目录: %s", dataPath)

	// 初始化Web Handler
	handler := web.NewHandler(storageMgr, userMgr, smbServer, pushMgr, cfg)

	// 创建HTTP服务器
	server := &http.Server{
		Addr:    fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port),
		Handler: handler,
	}

	// 启动服务器
	log.Printf("小思超级NAS服务启动: http://%s:%d", cfg.Server.Host, cfg.Server.Port)
	log.Println("默认管理员账号: admin / admin")

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("服务器启动失败: %v", err)
	}
}

func getConfigPath() string {
	// 尝试多个配置路径
	paths := []string{
		// 从go目录向上查找
		filepath.Join("..", "..", "config", "config.json"),
		// 当前目录
		"config.json",
		// 相对于可执行文件
		getExecConfigPath(),
	}

	for _, path := range paths {
		if _, err := os.Stat(path); err == nil {
			return path
		}
	}

	// 默认使用相对路径
	return filepath.Join("..", "..", "config", "config.json")
}

func getExecConfigPath() string {
	execPath, err := os.Executable()
	if err != nil {
		return "config.json"
	}
	baseDir := filepath.Dir(filepath.Dir(execPath))
	return filepath.Join(baseDir, "config", "config.json")
}