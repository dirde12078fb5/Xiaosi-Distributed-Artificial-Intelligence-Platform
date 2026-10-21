package web

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"strings"

	"xiaosi-nas/internal/config"
	"xiaosi-nas/internal/i18n"
	"xiaosi-nas/internal/push"
	"xiaosi-nas/internal/smb"
	"xiaosi-nas/internal/storage"
	"xiaosi-nas/internal/user"
)

type Handler struct {
	storageMgr *storage.Manager
	userMgr    *user.Manager
	smbServer  *smb.Server
	pushMgr    *push.Manager
	i18nMgr    *i18n.Manager
	cfg        *config.Config
}

func NewHandler(
	storageMgr *storage.Manager,
	userMgr *user.Manager,
	smbServer *smb.Server,
	pushMgr *push.Manager,
	cfg *config.Config,
) *Handler {
	return &Handler{
		storageMgr: storageMgr,
		userMgr:    userMgr,
		smbServer:  smbServer,
		pushMgr:    pushMgr,
		i18nMgr:    i18n.NewManager(&cfg.I18n),
		cfg:        cfg,
	}
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path

	// CORS headers
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	// API路由
	if strings.HasPrefix(path, "/api/") {
		h.handleAPI(w, r)
		return
	}

	// 首页
	if path == "/" {
		h.index(w, r)
		return
	}

	http.NotFound(w, r)
}

func (h *Handler) handleAPI(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Path
	method := r.Method

	var response interface{}
	var err error

	// 存储API
	if strings.HasPrefix(path, "/api/storage/") {
		response, err = h.handleStorage(path, method, r)
	} else if strings.HasPrefix(path, "/api/users") {
		response, err = h.handleUsers(path, method, r)
	} else if strings.HasPrefix(path, "/api/smb/") {
		response, err = h.handleSMB(path, method, r)
	} else if strings.HasPrefix(path, "/api/push/") {
		response, err = h.handlePush(path, method, r)
	} else if strings.HasPrefix(path, "/api/i18n/") {
		response, err = h.handleI18n(path, method, r)
	} else if path == "/api/config" {
		response, err = h.handleConfig(method, r)
	} else {
		http.NotFound(w, r)
		return
	}

	h.sendJSON(w, response, err)
}

func (h *Handler) handleStorage(path, method string, r *http.Request) (interface{}, error) {
	if path == "/api/storage/volumes" {
		if method == "GET" {
			return map[string]interface{}{"volumes": h.storageMgr.ListVolumes()}, nil
		}
		if method == "POST" {
			var req struct {
				Name    string `json:"name"`
				Path    string `json:"path"`
				QuotaGB int    `json:"quota_gb"`
			}
			if err := h.parseJSON(r, &req); err != nil {
				return nil, err
			}
			return map[string]string{"message": "volume created"}, h.storageMgr.CreateVolume(req.Name, req.Path, req.QuotaGB)
		}
	}

	// /api/storage/volumes/:name
	name := strings.TrimPrefix(path, "/api/storage/volumes/")
	if name != "" && !strings.Contains(name, "/") {
		if method == "GET" {
			return h.storageMgr.GetVolume(name)
		}
		if method == "DELETE" {
			return map[string]string{"message": "volume deleted"}, h.storageMgr.DeleteVolume(name)
		}
		if method == "PUT" && strings.HasSuffix(path, "/quota") {
			var req struct {
				QuotaGB int `json:"quota_gb"`
			}
			if err := h.parseJSON(r, &req); err != nil {
				return nil, err
			}
			return map[string]string{"message": "quota updated"}, h.storageMgr.UpdateQuota(name, req.QuotaGB)
		}
	}

	// /api/storage/volumes/:name/stats
	if strings.HasSuffix(path, "/stats") {
		name := strings.TrimSuffix(strings.TrimPrefix(path, "/api/storage/volumes/"), "/stats")
		used, available, err := h.storageMgr.GetStorageStats(name)
		return map[string]interface{}{"used": used, "available": available}, err
	}

	return nil, nil
}

func (h *Handler) handleUsers(path, method string, r *http.Request) (interface{}, error) {
	if path == "/api/users" {
		if method == "GET" {
			return map[string]interface{}{"users": h.userMgr.ListUsers()}, nil
		}
		if method == "POST" {
			var req struct {
				Username string `json:"username"`
				Password string `json:"password"`
				IsAdmin  bool   `json:"is_admin"`
			}
			if err := h.parseJSON(r, &req); err != nil {
				return nil, err
			}
			return map[string]string{"message": "user created"}, h.userMgr.CreateUser(req.Username, req.Password, req.IsAdmin)
		}
	}

	// /api/users/:username
	username := strings.TrimPrefix(path, "/api/users/")
	if username != "" && !strings.Contains(username, "/") {
		if method == "GET" {
			return h.userMgr.GetUser(username)
		}
		if method == "DELETE" {
			return map[string]string{"message": "user deleted"}, h.userMgr.DeleteUser(username)
		}
	}

	// /api/users/:username/password
	if strings.HasSuffix(path, "/password") {
		username := strings.TrimSuffix(strings.TrimPrefix(path, "/api/users/"), "/password")
		var req struct {
			Password string `json:"password"`
		}
		if err := h.parseJSON(r, &req); err != nil {
			return nil, err
		}
		return map[string]string{"message": "password updated"}, h.userMgr.UpdatePassword(username, req.Password)
	}

	// /api/users/:username/quota
	if strings.HasSuffix(path, "/quota") {
		username := strings.TrimSuffix(strings.TrimPrefix(path, "/api/users/"), "/quota")
		var req struct {
			QuotaGB int `json:"quota_gb"`
		}
		if err := h.parseJSON(r, &req); err != nil {
			return nil, err
		}
		return map[string]string{"message": "quota updated"}, h.userMgr.SetStorageQuota(username, req.QuotaGB)
	}

	return nil, nil
}

func (h *Handler) handleSMB(path, method string, r *http.Request) (interface{}, error) {
	if path == "/api/smb/status" {
		return h.smbServer.GetStatus(), nil
	}

	if path == "/api/smb/shares" {
		if method == "GET" {
			return map[string]interface{}{"shares": h.smbServer.ListShares()}, nil
		}
		if method == "POST" {
			var req struct {
				Name string `json:"name"`
				Path string `json:"path"`
			}
			if err := h.parseJSON(r, &req); err != nil {
				return nil, err
			}
			return map[string]string{"message": "share created"}, h.smbServer.CreateShare(req.Name, req.Path)
		}
	}

	// /api/smb/shares/:name
	name := strings.TrimPrefix(path, "/api/smb/shares/")
	if name != "" {
		if method == "DELETE" {
			return map[string]string{"message": "share deleted"}, h.smbServer.DeleteShare(name)
		}
		if method == "PUT" {
			var share smb.Share
			if err := h.parseJSON(r, &share); err != nil {
				return nil, err
			}
			return map[string]string{"message": "share updated"}, h.smbServer.UpdateShare(name, &share)
		}
	}

	// SMB服务控制
	if strings.HasSuffix(path, "/start") && method == "POST" {
		return map[string]string{"message": "SMB started"}, h.smbServer.Start()
	}
	if strings.HasSuffix(path, "/stop") && method == "POST" {
		return map[string]string{"message": "SMB stopped"}, h.smbServer.Stop()
	}

	return nil, nil
}

func (h *Handler) handlePush(path, method string, r *http.Request) (interface{}, error) {
	if path == "/api/push/status" {
		return h.pushMgr.GetStatus(), nil
	}

	if path == "/api/push/clients" && method == "GET" {
		return map[string]interface{}{"clients": h.pushMgr.ListClients()}, nil
	}

	if path == "/api/push/messages" {
		if method == "GET" {
			unreadOnly := r.URL.Query().Get("unread") == "true"
			return map[string]interface{}{"messages": h.pushMgr.ListMessages(unreadOnly)}, nil
		}
		if method == "POST" {
			var req struct {
				Type    string                 `json:"type"`
				Title   string                 `json:"title"`
				Content string                 `json:"content"`
				Data    map[string]interface{} `json:"data"`
			}
			if err := h.parseJSON(r, &req); err != nil {
				return nil, err
			}
			return map[string]string{"message": "push sent"}, h.pushMgr.PushMessage(req.Type, req.Title, req.Content, req.Data)
		}
		if method == "DELETE" {
			h.pushMgr.ClearMessages()
			return map[string]string{"message": "messages cleared"}, nil
		}
	}

	// /api/push/messages/:id/read
	if strings.HasSuffix(path, "/read") && method == "POST" {
		id := strings.TrimSuffix(strings.TrimPrefix(path, "/api/push/messages/"), "/read")
		return map[string]string{"message": "marked as read"}, h.pushMgr.MarkRead(id)
	}

	return nil, nil
}

func (h *Handler) handleI18n(path, method string, r *http.Request) (interface{}, error) {
	lang := strings.TrimPrefix(path, "/api/i18n/")
	if lang != "" && method == "GET" {
		return h.i18nMgr.GetTranslations(lang), nil
	}

	if path == "/api/i18n/supported" && method == "GET" {
		return map[string]interface{}{"languages": h.i18nMgr.GetSupportedLanguages()}, nil
	}

	return nil, nil
}

func (h *Handler) handleConfig(method string, r *http.Request) (interface{}, error) {
	if method == "GET" {
		return h.cfg, nil
	}
	if method == "PUT" {
		var cfg config.Config
		if err := h.parseJSON(r, &cfg); err != nil {
			return nil, err
		}
		*h.cfg = cfg
		return map[string]string{"message": "config updated"}, nil
	}
	return nil, nil
}

func (h *Handler) index(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write([]byte(indexHTML))
}

func (h *Handler) parseJSON(r *http.Request, v interface{}) error {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return err
	}
	return json.Unmarshal(body, v)
}

func (h *Handler) sendJSON(w http.ResponseWriter, response interface{}, err error) {
	w.Header().Set("Content-Type", "application/json")

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(map[string]string{"error": err.Error()})
		return
	}

	json.NewEncoder(w).Encode(response)
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
            <div class="nav-item" data-page="push" data-i18n="push_notifications">推送通知</div>
        </div>

        <div class="main">
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

            <div class="page" id="page-storage">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <div class="card-title" style="margin-bottom: 0;" data-i18n="volumes">存储卷</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('storage')" data-i18n="create">创建</button>
                    </div>
                    <table>
                        <thead><tr><th data-i18n="name">名称</th><th data-i18n="path">路径</th><th data-i18n="quota">配额(GB)</th><th data-i18n="operation">操作</th></tr></thead>
                        <tbody id="volumes-table"></tbody>
                    </table>
                </div>
            </div>

            <div class="page" id="page-users">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <div class="card-title" style="margin-bottom: 0;" data-i18n="users">用户</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('user')" data-i18n="create">创建</button>
                    </div>
                    <table>
                        <thead><tr><th data-i18n="username">用户名</th><th data-i18n="home_directory">主目录</th><th data-i18n="admin">管理员</th><th data-i18n="operation">操作</th></tr></thead>
                        <tbody id="users-table"></tbody>
                    </table>
                </div>
            </div>

            <div class="page" id="page-shares">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <div class="card-title" style="margin-bottom: 0;" data-i18n="shares">共享</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('share')" data-i18n="create">创建</button>
                    </div>
                    <table>
                        <thead><tr><th data-i18n="share_name">共享名称</th><th data-i18n="path">路径</th><th data-i18n="read_only">只读</th><th data-i18n="operation">操作</th></tr></thead>
                        <tbody id="shares-table"></tbody>
                    </table>
                </div>
            </div>

            <div class="page" id="page-push">
                <div class="card">
                    <div class="card-title" data-i18n="messages">消息</div>
                    <button class="btn btn-danger btn-sm" onclick="clearMessages()" data-i18n="clear_all">清空全部</button>
                    <div id="messages-list" style="margin-top: 20px;"></div>
                </div>
            </div>
        </div>
    </div>

    <div class="modal" id="storage-modal">
        <div class="modal-content">
            <div class="modal-title" data-i18n="create_volume">创建存储卷</div>
            <div class="form-group"><label data-i18n="name">名称</label><input type="text" id="storage-name"></div>
            <div class="form-group"><label data-i18n="path">路径</label><input type="text" id="storage-path"></div>
            <div class="form-group"><label data-i18n="quota">配额(GB)</label><input type="number" id="storage-quota" value="100"></div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('storage')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createVolume()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>

    <div class="modal" id="user-modal">
        <div class="modal-content">
            <div class="modal-title" data-i18n="create_user">创建用户</div>
            <div class="form-group"><label data-i18n="username">用户名</label><input type="text" id="user-name"></div>
            <div class="form-group"><label data-i18n="password">密码</label><input type="password" id="user-password"></div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('user')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createUser()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>

    <div class="modal" id="share-modal">
        <div class="modal-content">
            <div class="modal-title" data-i18n="create_share">创建共享</div>
            <div class="form-group"><label data-i18n="share_name">共享名称</label><input type="text" id="share-name"></div>
            <div class="form-group"><label data-i18n="path">路径</label><input type="text" id="share-path"></div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('share')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createShare()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>

    <script>
        let translations = {};

        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
                item.classList.add('active');
                document.getElementById('page-' + item.dataset.page).classList.add('active');
                loadData(item.dataset.page);
            });
        });

        document.getElementById('langSelect').addEventListener('change', (e) => {
            loadTranslations(e.target.value);
        });

        async function loadTranslations(lang) {
            try {
                const res = await fetch('/api/i18n/' + lang);
                translations = await res.json();
                applyTranslations();
            } catch (e) {
                log.Println('Failed to load translations');
            }
        }

        function applyTranslations() {
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.dataset.i18n;
                if (translations[key]) {
                    el.textContent = translations[key];
                }
            });
        }

        async function loadData(page) {
            if (page === 'dashboard') await loadDashboard();
            else if (page === 'storage') await loadVolumes();
            else if (page === 'users') await loadUsers();
            else if (page === 'shares') await loadShares();
            else if (page === 'push') await loadMessages();
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
                log.Println('Failed to load dashboard');
            }
        }

        async function loadVolumes() {
            try {
                const res = await fetch('/api/storage/volumes');
                const data = await res.json();
                const tbody = document.getElementById('volumes-table');
                tbody.innerHTML = '';
                (data.volumes || []).forEach(vol => {
                    tbody.innerHTML += '<tr><td>' + vol.name + '</td><td>' + vol.path + '</td><td>' + vol.quota_gb + '</td><td><button class="btn btn-danger btn-sm" onclick="deleteVolume(\'' + vol.name + '\')">删除</button></td></tr>';
                });
            } catch (e) {
                log.Println('Failed to load volumes');
            }
        }

        async function loadUsers() {
            try {
                const res = await fetch('/api/users');
                const data = await res.json();
                const tbody = document.getElementById('users-table');
                tbody.innerHTML = '';
                (data.users || []).forEach(user => {
                    tbody.innerHTML += '<tr><td>' + user.username + '</td><td>' + user.home_dir + '</td><td>' + (user.is_admin ? '是' : '否') + '</td><td><button class="btn btn-danger btn-sm" onclick="deleteUser(\'' + user.username + '\')">删除</button></td></tr>';
                });
            } catch (e) {
                log.Println('Failed to load users');
            }
        }

        async function loadShares() {
            try {
                const res = await fetch('/api/smb/shares');
                const data = await res.json();
                const tbody = document.getElementById('shares-table');
                tbody.innerHTML = '';
                (data.shares || []).forEach(share => {
                    tbody.innerHTML += '<tr><td>' + share.name + '</td><td>' + share.path + '</td><td>' + (share.read_only ? '是' : '否') + '</td><td><button class="btn btn-danger btn-sm" onclick="deleteShare(\'' + share.name + '\')">删除</button></td></tr>';
                });
            } catch (e) {
                log.Println('Failed to load shares');
            }
        }

        async function loadMessages() {
            try {
                const res = await fetch('/api/push/messages');
                const data = await res.json();
                const list = document.getElementById('messages-list');
                list.innerHTML = '';
                (data.messages || []).forEach(msg => {
                    list.innerHTML += '<div style="padding: 10px; margin: 10px 0; background: #f8f9ff; border-radius: 6px;"><strong>' + msg.title + '</strong> - ' + msg.content + '</div>';
                });
            } catch (e) {
                log.Println('Failed to load messages');
            }
        }

        function showModal(type) { document.getElementById(type + '-modal').classList.add('show'); }
        function closeModal(type) { document.getElementById(type + '-modal').classList.remove('show'); }

        async function createVolume() {
            await fetch('/api/storage/volumes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: document.getElementById('storage-name').value, path: document.getElementById('storage-path').value, quota_gb: parseInt(document.getElementById('storage-quota').value) })
            });
            closeModal('storage');
            loadVolumes();
        }

        async function createUser() {
            await fetch('/api/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: document.getElementById('user-name').value, password: document.getElementById('user-password').value, is_admin: false })
            });
            closeModal('user');
            loadUsers();
        }

        async function createShare() {
            await fetch('/api/smb/shares', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: document.getElementById('share-name').value, path: document.getElementById('share-path').value })
            });
            closeModal('share');
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

        async function clearMessages() {
            await fetch('/api/push/messages', { method: 'DELETE' });
            loadMessages();
        }

        loadTranslations('zh_CN');
        loadDashboard();
    </script>
</body>
</html>`