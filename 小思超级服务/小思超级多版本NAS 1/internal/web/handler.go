package web

import (
	"net/http"

	"xiaosi-nas/internal/config"
	"xiaosi-nas/internal/i18n"
	"xiaosi-nas/internal/smb"
	"xiaosi-nas/internal/storage"
	"xiaosi-nas/internal/user"

	"github.com/labstack/echo/v4"
)

type Handler struct {
	storageMgr *storage.Manager
	userMgr    *user.Manager
	smbServer  *smb.Server
	i18nMgr    *i18n.Manager
	cfg        *config.Config
}

func NewHandler(storageMgr *storage.Manager, userMgr *user.Manager, smbServer *smb.Server, cfg *config.Config) *Handler {
	return &Handler{
		storageMgr: storageMgr,
		userMgr:    userMgr,
		smbServer:  smbServer,
		i18nMgr:    i18n.NewManager(cfg.I18n.Supported, cfg.Server.Language),
		cfg:        cfg,
	}
}

func (h *Handler) RegisterRoutes(e *echo.Echo) {
	// API路由组
	api := e.Group("/api")

	// 存储管理
	api.GET("/storage/volumes", h.ListVolumes)
	api.POST("/storage/volumes", h.CreateVolume)
	api.GET("/storage/volumes/:name", h.GetVolume)
	api.DELETE("/storage/volumes/:name", h.DeleteVolume)
	api.PUT("/storage/volumes/:name/quota", h.UpdateQuota)
	api.GET("/storage/volumes/:name/stats", h.GetStorageStats)

	// 用户管理
	api.GET("/users", h.ListUsers)
	api.POST("/users", h.CreateUser)
	api.GET("/users/:username", h.GetUser)
	api.DELETE("/users/:username", h.DeleteUser)
	api.PUT("/users/:username/password", h.UpdatePassword)
	api.PUT("/users/:username/quota", h.SetUserQuota)

	// SMB共享
	api.GET("/smb/status", h.GetSMBStatus)
	api.GET("/smb/shares", h.ListShares)
	api.POST("/smb/shares", h.CreateShare)
	api.DELETE("/smb/shares/:name", h.DeleteShare)
	api.PUT("/smb/shares/:name", h.UpdateShare)

	// 多语言
	api.GET("/i18n/:lang", h.GetTranslations)

	// Web前端
	e.GET("/", h.Index)
	e.GET("/static/*", echo.StaticFileHandler("web"))
}

// 存储管理API

func (h *Handler) ListVolumes(c echo.Context) error {
	volumes := h.storageMgr.ListVolumes()
	return c.JSON(http.StatusOK, map[string]interface{}{
		"volumes": volumes,
	})
}

func (h *Handler) CreateVolume(c echo.Context) error {
	var req struct {
		Name    string `json:"name"`
		Path    string `json:"path"`
		QuotaGB int    `json:"quota_gb"`
	}
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}

	if err := h.storageMgr.CreateVolume(req.Name, req.Path, req.QuotaGB); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusCreated, map[string]string{"message": "volume created"})
}

func (h *Handler) GetVolume(c echo.Context) error {
	name := c.Param("name")
	vol, err := h.storageMgr.GetVolume(name)
	if err != nil {
		return c.JSON(http.StatusNotFound, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, vol)
}

func (h *Handler) DeleteVolume(c echo.Context) error {
	name := c.Param("name")
	if err := h.storageMgr.DeleteVolume(name); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, map[string]string{"message": "volume deleted"})
}

func (h *Handler) UpdateQuota(c echo.Context) error {
	name := c.Param("name")
	var req struct {
		QuotaGB int `json:"quota_gb"`
	}
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}

	if err := h.storageMgr.UpdateQuota(name, req.QuotaGB); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, map[string]string{"message": "quota updated"})
}

func (h *Handler) GetStorageStats(c echo.Context) error {
	name := c.Param("name")
	used, available, err := h.storageMgr.GetStorageStats(name)
	if err != nil {
		return c.JSON(http.StatusNotFound, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, map[string]interface{}{
		"used":      used,
		"available": available,
	})
}

// 用户管理API

func (h *Handler) ListUsers(c echo.Context) error {
	users := h.userMgr.ListUsers()
	return c.JSON(http.StatusOK, map[string]interface{}{
		"users": users,
	})
}

func (h *Handler) CreateUser(c echo.Context) error {
	var req struct {
		Username string `json:"username"`
		Password string `json:"password"`
		IsAdmin  bool   `json:"is_admin"`
	}
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}

	if err := h.userMgr.CreateUser(req.Username, req.Password, req.IsAdmin); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusCreated, map[string]string{"message": "user created"})
}

func (h *Handler) GetUser(c echo.Context) error {
	username := c.Param("username")
	u, err := h.userMgr.GetUser(username)
	if err != nil {
		return c.JSON(http.StatusNotFound, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, u)
}

func (h *Handler) DeleteUser(c echo.Context) error {
	username := c.Param("username")
	if err := h.userMgr.DeleteUser(username); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, map[string]string{"message": "user deleted"})
}

func (h *Handler) UpdatePassword(c echo.Context) error {
	username := c.Param("username")
	var req struct {
		Password string `json:"password"`
	}
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}

	if err := h.userMgr.UpdatePassword(username, req.Password); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, map[string]string{"message": "password updated"})
}

func (h *Handler) SetUserQuota(c echo.Context) error {
	username := c.Param("username")
	var req struct {
		QuotaGB int `json:"quota_gb"`
	}
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}

	if err := h.userMgr.SetStorageQuota(username, req.QuotaGB); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, map[string]string{"message": "quota updated"})
}

// SMB API

func (h *Handler) GetSMBStatus(c echo.Context) error {
	return c.JSON(http.StatusOK, h.smbServer.GetStatus())
}

func (h *Handler) ListShares(c echo.Context) error {
	shares := h.smbServer.ListShares()
	return c.JSON(http.StatusOK, map[string]interface{}{
		"shares": shares,
	})
}

func (h *Handler) CreateShare(c echo.Context) error {
	var req struct {
		Name string `json:"name"`
		Path string `json:"path"`
	}
	if err := c.Bind(&req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}

	if err := h.smbServer.CreateShare(req.Name, req.Path); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusCreated, map[string]string{"message": "share created"})
}

func (h *Handler) DeleteShare(c echo.Context) error {
	name := c.Param("name")
	if err := h.smbServer.DeleteShare(name); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, map[string]string{"message": "share deleted"})
}

func (h *Handler) UpdateShare(c echo.Context) error {
	name := c.Param("name")
	var updates map[string]interface{}
	if err := c.Bind(&updates); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}

	if err := h.smbServer.UpdateShare(name, updates); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}
	return c.JSON(http.StatusOK, map[string]string{"message": "share updated"})
}

// 多语言API

func (h *Handler) GetTranslations(c echo.Context) error {
	lang := c.Param("lang")
	translations := h.i18nMgr.GetTranslations(lang)
	return c.JSON(http.StatusOK, translations)
}

// Web首页

func (h *Handler) Index(c echo.Context) error {
	return c.HTML(http.StatusOK, indexHTML)
}

const indexHTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小思超级NAS - 管理控制台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; }
        .header-right { display: flex; align-items: center; gap: 15px; }
        .lang-select { padding: 8px 12px; border-radius: 6px; border: none; cursor: pointer; }
        
        .container { display: flex; min-height: calc(100vh - 80px); }
        .sidebar { width: 220px; background: white; padding: 20px 0; box-shadow: 2px 0 8px rgba(0,0,0,0.05); }
        .nav-item { padding: 15px 25px; cursor: pointer; transition: all 0.3s; border-left: 4px solid transparent; }
        .nav-item:hover, .nav-item.active { background: #f8f9ff; border-left-color: #667eea; color: #667eea; }
        
        .main { flex: 1; padding: 30px; }
        .card { background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
        .card-title { font-size: 18px; font-weight: 600; margin-bottom: 20px; color: #333; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; }
        .stat-card h3 { font-size: 14px; opacity: 0.9; margin-bottom: 8px; }
        .stat-card .value { font-size: 28px; font-weight: 600; }
        
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9ff; font-weight: 600; color: #555; }
        tr:hover { background: #fafafa; }
        
        .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: all 0.3s; }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; }
        .btn-danger { background: #f56565; color: white; }
        .btn-danger:hover { background: #e53e3e; }
        .btn-sm { padding: 6px 12px; font-size: 12px; }
        
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); justify-content: center; align-items: center; z-index: 1000; }
        .modal.show { display: flex; }
        .modal-content { background: white; padding: 30px; border-radius: 12px; min-width: 400px; max-width: 90%; }
        .modal-title { font-size: 20px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 6px; color: #666; font-size: 14px; }
        .form-group input, .form-group select { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
        .form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
        
        .badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; }
        .badge-success { background: #c6f6d5; color: #276749; }
        .badge-danger { background: #fed7d7; color: #c53030; }
        .badge-warning { background: #fefcbf; color: #975a16; }
        
        .page { display: none; }
        .page.active { display: block; }
    </style>
</head>
<body>
    <div class="header">
        <h1>小思超级NAS 管理控制台</h1>
        <div class="header-right">
            <select class="lang-select" id="langSelect">
                <option value="zh_CN">简体中文</option>
                <option value="zh_TW">繁體中文</option>
                <option value="en_US">English (US)</option>
                <option value="en_GB">English (UK)</option>
                <option value="ja_JP">日本語</option>
                <option value="ko_KR">한국어</option>
                <option value="fr_FR">Français</option>
                <option value="de_DE">Deutsch</option>
                <option value="es_ES">Español</option>
                <option value="it_IT">Italiano</option>
                <option value="pt_BR">Português (BR)</option>
                <option value="ru_RU">Русский</option>
                <option value="ar_SA">العربية</option>
                <option value="hi_IN">हिन्दी</option>
                <option value="tr_TR">Türkçe</option>
                <option value="th_TH">ไทย</option>
                <option value="vi_VN">Tiếng Việt</option>
                <option value="id_ID">Bahasa Indonesia</option>
                <option value="nl_NL">Nederlands</option>
                <option value="pl_PL">Polski</option>
                <option value="sv_SE">Svenska</option>
                <option value="da_DK">Dansk</option>
                <option value="fi_FI">Suomi</option>
                <option value="he_IL">עברית</option>
                <option value="hu_HU">Magyar</option>
                <option value="cs_CZ">Čeština</option>
                <option value="uk_UA">Українська</option>
                <option value="ro_RO">Română</option>
            </select>
        </div>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <div class="nav-item active" data-page="dashboard" data-i18n="dashboard">控制台</div>
            <div class="nav-item" data-page="storage" data-i18n="storage">存储管理</div>
            <div class="nav-item" data-page="users" data-i18n="users">用户管理</div>
            <div class="nav-item" data-page="shares" data-i18n="shares">共享管理</div>
        </div>
        
        <div class="main">
            <!-- 控制台页面 -->
            <div class="page active" id="page-dashboard">
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3 data-i18n="volumes">存储卷</h3>
                        <div class="value" id="stat-volumes">0</div>
                    </div>
                    <div class="stat-card">
                        <h3 data-i18n="users">用户</h3>
                        <div class="value" id="stat-users">0</div>
                    </div>
                    <div class="stat-card">
                        <h3 data-i18n="smb_shares">SMB共享</h3>
                        <div class="value" id="stat-shares">0</div>
                    </div>
                    <div class="stat-card">
                        <h3 data-i18n="smb_status">服务状态</h3>
                        <div class="value" id="stat-status">-</div>
                    </div>
                </div>
            </div>
            
            <!-- 存储管理页面 -->
            <div class="page" id="page-storage">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <div class="card-title" style="margin-bottom: 0;" data-i18n="volumes">存储卷</div>
                        <button class="btn btn-primary btn-sm" onclick="showStorageModal()" data-i18n="create">创建</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th data-i18n="name">名称</th>
                                <th data-i18n="path">路径</th>
                                <th data-i18n="quota">配额 (GB)</th>
                                <th data-i18n="used">已用</th>
                                <th data-i18n="available">可用</th>
                                <th data-i18n="operation">操作</th>
                            </tr>
                        </thead>
                        <tbody id="volumes-table"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 用户管理页面 -->
            <div class="page" id="page-users">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <div class="card-title" style="margin-bottom: 0;" data-i18n="users">用户</div>
                        <button class="btn btn-primary btn-sm" onclick="showUserModal()" data-i18n="create">创建</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th data-i18n="username">用户名</th>
                                <th data-i18n="home_directory">主目录</th>
                                <th data-i18n="storage_quota">存储配额 (GB)</th>
                                <th data-i18n="admin">管理员</th>
                                <th data-i18n="operation">操作</th>
                            </tr>
                        </thead>
                        <tbody id="users-table"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 共享管理页面 -->
            <div class="page" id="page-shares">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <div class="card-title" style="margin-bottom: 0;" data-i18n="shares">共享</div>
                        <button class="btn btn-primary btn-sm" onclick="showShareModal()" data-i18n="create">创建</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th data-i18n="share_name">共享名称</th>
                                <th data-i18n="path">路径</th>
                                <th data-i18n="comment">备注</th>
                                <th data-i18n="read_only">只读</th>
                                <th data-i18n="browseable">可浏览</th>
                                <th data-i18n="operation">操作</th>
                            </tr>
                        </thead>
                        <tbody id="shares-table"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 创建存储卷模态框 -->
    <div class="modal" id="storage-modal">
        <div class="modal-content">
            <div class="modal-title" data-i18n="create_volume">创建存储卷</div>
            <div class="form-group">
                <label data-i18n="name">名称</label>
                <input type="text" id="storage-name">
            </div>
            <div class="form-group">
                <label data-i18n="path">路径</label>
                <input type="text" id="storage-path">
            </div>
            <div class="form-group">
                <label data-i18n="quota">配额 (GB)</label>
                <input type="number" id="storage-quota" value="100">
            </div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('storage-modal')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createVolume()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>
    
    <!-- 创建用户模态框 -->
    <div class="modal" id="user-modal">
        <div class="modal-content">
            <div class="modal-title" data-i18n="create_user">创建用户</div>
            <div class="form-group">
                <label data-i18n="username">用户名</label>
                <input type="text" id="user-name">
            </div>
            <div class="form-group">
                <label data-i18n="password">密码</label>
                <input type="password" id="user-password">
            </div>
            <div class="form-group">
                <label data-i18n="storage_quota">存储配额 (GB)</label>
                <input type="number" id="user-quota" value="100">
            </div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('user-modal')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createUser()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>
    
    <!-- 创建共享模态框 -->
    <div class="modal" id="share-modal">
        <div class="modal-content">
            <div class="modal-title" data-i18n="create_share">创建共享</div>
            <div class="form-group">
                <label data-i18n="share_name">共享名称</label>
                <input type="text" id="share-name">
            </div>
            <div class="form-group">
                <label data-i18n="path">路径</label>
                <input type="text" id="share-path">
            </div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('share-modal')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createShare()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>

    <script>
        let translations = {};
        
        // 页面导航
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
                item.classList.add('active');
                document.getElementById('page-' + item.dataset.page).classList.add('active');
                loadPageData(item.dataset.page);
            });
        });
        
        // 语言切换
        document.getElementById('langSelect').addEventListener('change', (e) => {
            loadTranslations(e.target.value);
        });
        
        // 加载翻译
        async function loadTranslations(lang) {
            try {
                const res = await fetch('/api/i18n/' + lang);
                translations = await res.json();
                applyTranslations();
            } catch (e) {
                console.error('Failed to load translations');
            }
        }
        
        // 应用翻译
        function applyTranslations() {
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.dataset.i18n;
                if (translations[key]) {
                    el.textContent = translations[key];
                }
            });
        }
        
        // 加载页面数据
        async function loadPageData(page) {
            if (page === 'dashboard') {
                await loadDashboard();
            } else if (page === 'storage') {
                await loadVolumes();
            } else if (page === 'users') {
                await loadUsers();
            } else if (page === 'shares') {
                await loadShares();
            }
        }
        
        async function loadDashboard() {
            try {
                const [volumes, users, shares, smbStatus] = await Promise.all([
                    fetch('/api/storage/volumes').then(r => r.json()),
                    fetch('/api/users').then(r => r.json()),
                    fetch('/api/smb/shares').then(r => r.json()),
                    fetch('/api/smb/status').then(r => r.json())
                ]);
                
                document.getElementById('stat-volumes').textContent = volumes.volumes ? volumes.volumes.length : 0;
                document.getElementById('stat-users').textContent = users.users ? users.users.length : 0;
                document.getElementById('stat-shares').textContent = shares.shares ? shares.shares.length : 0;
                document.getElementById('stat-status').textContent = smbStatus.running ? '运行中' : '已停止';
            } catch (e) {
                console.error('Failed to load dashboard data');
            }
        }
        
        async function loadVolumes() {
            try {
                const res = await fetch('/api/storage/volumes');
                const data = await res.json();
                const tbody = document.getElementById('volumes-table');
                tbody.innerHTML = '';
                
                if (data.volumes && data.volumes.length > 0) {
                    data.volumes.forEach(vol => {
                        tbody.innerHTML += '<tr><td>' + vol.name + '</td><td>' + vol.path + '</td><td>' + vol.quota_gb + '</td><td>-</td><td>-</td><td><button class="btn btn-danger btn-sm" onclick="deleteVolume(\'' + vol.name + '\')">删除</button></td></tr>';
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">暂无数据</td></tr>';
                }
            } catch (e) {
                console.error('Failed to load volumes');
            }
        }
        
        async function loadUsers() {
            try {
                const res = await fetch('/api/users');
                const data = await res.json();
                const tbody = document.getElementById('users-table');
                tbody.innerHTML = '';
                
                if (data.users && data.users.length > 0) {
                    data.users.forEach(user => {
                        tbody.innerHTML += '<tr><td>' + user.username + '</td><td>' + user.home_dir + '</td><td>' + user.storage_quota_gb + '</td><td><span class="badge ' + (user.is_admin ? 'badge-success' : 'badge-warning') + '">' + (user.is_admin ? '是' : '否') + '</span></td><td><button class="btn btn-danger btn-sm" onclick="deleteUser(\'' + user.username + '\')">删除</button></td></tr>';
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">暂无数据</td></tr>';
                }
            } catch (e) {
                console.error('Failed to load users');
            }
        }
        
        async function loadShares() {
            try {
                const res = await fetch('/api/smb/shares');
                const data = await res.json();
                const tbody = document.getElementById('shares-table');
                tbody.innerHTML = '';
                
                if (data.shares && data.shares.length > 0) {
                    data.shares.forEach(share => {
                        tbody.innerHTML += '<tr><td>' + share.name + '</td><td>' + share.path + '</td><td>' + (share.comment || '-') + '</td><td><span class="badge ' + (share.read_only ? 'badge-warning' : 'badge-success') + '">' + (share.read_only ? '是' : '否') + '</span></td><td><span class="badge ' + (share.browseable ? 'badge-success' : 'badge-warning') + '">' + (share.browseable ? '是' : '否') + '</span></td><td><button class="btn btn-danger btn-sm" onclick="deleteShare(\'' + share.name + '\')">删除</button></td></tr>';
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">暂无数据</td></tr>';
                }
            } catch (e) {
                console.error('Failed to load shares');
            }
        }
        
        // 模态框操作
        function showStorageModal() { document.getElementById('storage-modal').classList.add('show'); }
        function showUserModal() { document.getElementById('user-modal').classList.add('show'); }
        function showShareModal() { document.getElementById('share-modal').classList.add('show'); }
        function closeModal(id) { document.getElementById(id).classList.remove('show'); }
        
        async function createVolume() {
            const name = document.getElementById('storage-name').value;
            const path = document.getElementById('storage-path').value;
            const quota = parseInt(document.getElementById('storage-quota').value);
            
            await fetch('/api/storage/volumes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, path, quota_gb: quota })
            });
            
            closeModal('storage-modal');
            loadVolumes();
        }
        
        async function createUser() {
            const name = document.getElementById('user-name').value;
            const password = document.getElementById('user-password').value;
            const quota = parseInt(document.getElementById('user-quota').value);
            
            await fetch('/api/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: name, password, is_admin: false })
            });
            
            closeModal('user-modal');
            loadUsers();
        }
        
        async function createShare() {
            const name = document.getElementById('share-name').value;
            const path = document.getElementById('share-path').value;
            
            await fetch('/api/smb/shares', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, path })
            });
            
            closeModal('share-modal');
            loadShares();
        }
        
        async function deleteVolume(name) {
            if (confirm('确认删除存储卷 ' + name + '?')) {
                await fetch('/api/storage/volumes/' + name, { method: 'DELETE' });
                loadVolumes();
            }
        }
        
        async function deleteUser(username) {
            if (confirm('确认删除用户 ' + username + '?')) {
                await fetch('/api/users/' + username, { method: 'DELETE' });
                loadUsers();
            }
        }
        
        async function deleteShare(name) {
            if (confirm('确认删除共享 ' + name + '?')) {
                await fetch('/api/smb/shares/' + name, { method: 'DELETE' });
                loadShares();
            }
        }
        
        // 初始化
        loadTranslations('zh_CN');
        loadDashboard();
    </script>
</body>
</html>`
