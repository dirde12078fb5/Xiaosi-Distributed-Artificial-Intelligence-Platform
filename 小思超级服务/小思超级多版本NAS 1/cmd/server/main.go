package main

import (
	"fmt"
	"log"
	"os"

	"xiaosi-nas/internal/config"
	"xiaosi-nas/internal/smb"
	"xiaosi-nas/internal/storage"
	"xiaosi-nas/internal/user"
	"xiaosi-nas/internal/web"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

func main() {
	// 加载配置
	cfg, err := config.Load("config.json")
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// 初始化组件
	storageMgr := storage.NewManager(&cfg.Storage)
	userMgr := user.NewManager()
	smbServer := smb.NewServer(&cfg.SMB)

	// 启动SMB服务
	if cfg.SMB.Enabled {
		if err := smbServer.Start(); err != nil {
			log.Printf("SMB server start failed: %v", err)
		} else {
			log.Println("SMB server started")
		}
	}

	// 创建Echo实例
	e := echo.New()

	// 中间件
	e.Use(middleware.Logger())
	e.Use(middleware.Recover())
	e.Use(middleware.CORS())

	// 初始化Web API
	webHandler := web.NewHandler(storageMgr, userMgr, smbServer, cfg)
	webHandler.RegisterRoutes(e)

	// 启动服务器
	addr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)
	log.Printf("小思超级NAS服务启动: %s", addr)
	if err := e.Start(addr); err != nil && err != os.ErrExit {
		log.Fatalf("Server error: %v", err)
	}
}
