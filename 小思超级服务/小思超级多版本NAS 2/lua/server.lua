--[[
    NAS Service - Lua Implementation
    Version: 2.0
    Default Port: 8094
    Supports 28 languages
]]

local socket = require("socket")
local json = require("dkjson") or {}
local http = require("socket.http")
local ltn12 = require("ltn12")

-- Configuration
local CONFIG_PATH = "../config/config.json"
local DEFAULT_PORT = 8094
local HOST = "0.0.0.0"

-- Language translations (28 languages)
local TRANSLATIONS = {
    zh = { name = "中文", welcome = "欢迎使用NAS服务", error = "错误", success = "成功" },
    en = { name = "English", welcome = "Welcome to NAS Service", error = "Error", success = "Success" },
    ja = { name = "日本語", welcome = "NASサービスへようこそ", error = "エラー", success = "成功" },
    ko = { name = "한국어", welcome = "NAS 서비스에 오신 것을 환영합니다", error = "오류", success = "성공" },
    de = { name = "Deutsch", welcome = "Willkommen beim NAS-Service", error = "Fehler", success = "Erfolg" },
    fr = { name = "Français", welcome = "Bienvenue au service NAS", error = "Erreur", success = "Succès" },
    es = { name = "Español", welcome = "Bienvenido al servicio NAS", error = "Error", success = "Éxito" },
    pt = { name = "Português", welcome = "Bem-vindo ao serviço NAS", error = "Erro", success = "Sucesso" },
    ru = { name = "Русский", welcome = "Добро пожаловать в службу NAS", error = "Ошибка", success = "Успех" },
    it = { name = "Italiano", welcome = "Benvenuto nel servizio NAS", error = "Errore", success = "Successo" },
    nl = { name = "Nederlands", welcome = "Welkom bij NAS-service", error = "Fout", success = "Succes" },
    pl = { name = "Polski", welcome = "Witamy w usłudze NAS", error = "Błąd", success = "Sukces" },
    tr = { name = "Türkçe", welcome = "NAS hizmetine hoş geldiniz", error = "Hata", success = "Başarı" },
    ar = { name = "العربية", welcome = "مرحباً بك في خدمة NAS", error = "خطأ", success = "نجاح" },
    th = { name = "ไทย", welcome = "ยินดีต้อนรับสู่บริการ NAS", error = "ข้อผิดพลาด", success = "สำเร็จ" },
    vi = { name = "Tiếng Việt", welcome = "Chào mừng đến với dịch vụ NAS", error = "Lỗi", success = "Thành công" },
    id = { name = "Bahasa Indonesia", welcome = "Selamat datang di layanan NAS", error = "Kesalahan", success = "Sukses" },
    ms = { name = "Bahasa Melayu", welcome = "Selamat datang ke perkhidmatan NAS", error = "Ralat", success = "Berjaya" },
    hi = { name = "हिन्दी", welcome = "NAS सेवा में आपका स्वागत है", error = "त्रुटि", success = "सफलता" },
    bn = { name = "বাংলা", welcome = "NAS পরিষেবায় স্বাগতম", error = "ত্রুটি", success = "সাফল্য" },
    ur = { name = "اردو", welcome = "NAS سروس میں خوش آمدید", error = "خرابی", success = "کامیابی" },
    fa = { name = "فارسی", welcome = "به سرویس NAS خوش آمدید", error = "خطا", success = "موفقیت" },
    he = { name = "עברית", welcome = "ברוכים הבאים לשירות NAS", error = "שגיאה", success = "הצלחה" },
    sv = { name = "Svenska", welcome = "Välkommen till NAS-tjänsten", error = "Fel", success = "Framgång" },
    no = { name = "Norsk", welcome = "Velkommen til NAS-tjenesten", error = "Feil", success = "Suksess" },
    da = { name = "Dansk", welcome = "Velkommen til NAS-tjenesten", error = "Fejl", success = "Succes" },
    fi = { name = "Suomi", welcome = "Tervetuloa NAS-palveluun", error = "Virhe", success = "Onnistui" },
    cs = { name = "Čeština", welcome = "Vítejte ve službě NAS", error = "Chyba", success = "Úspěch" }
}

-- Global state
local config = {}
local storage_path = "./storage"
local files_metadata = {}

-- Utility functions
local function load_config()
    local file = io.open(CONFIG_PATH, "r")
    if file then
        local content = file:read("*all")
        file:close()
        local decoded = json.decode(content)
        if decoded then
            config = decoded
            if config.storage_path then
                storage_path = config.storage_path
            end
        end
    end
    config.port = config.port or DEFAULT_PORT
    config.host = config.host or HOST
    config.max_connections = config.max_connections or 100
    config.timeout = config.timeout or 30
end

local function json_response(data, status_code)
    status_code = status_code or 200
    local body = json.encode(data) or "{}"
    return "HTTP/1.1 " .. status_code .. " OK\r\n" ..
           "Content-Type: application/json; charset=utf-8\r\n" ..
           "Content-Length: " .. #body .. "\r\n" ..
           "Access-Control-Allow-Origin: *\r\n" ..
           "Connection: close\r\n\r\n" .. body
end

local function parse_request(request)
    local method, path, params = request:match("^(%w+)%s+([^%s?]+)%s*.*\r?\n")
    local headers = {}
    local body_start = request:find("\r\n\r\n")
    local body = body_start and request:sub(body_start + 4) or ""
    
    for key, value in request:gmatch("([^:]+):%s*([^\r\n]+)\r?\n") do
        headers[key:lower()] = value
    end
    
    -- Parse query parameters
    local query_params = {}
    if path and path:find("?") then
        local query = path:match("%?(.+)$")
        path = path:match("^([^?]+)")
        if query then
            for key, value in query:gmatch("([^&=]+)=([^&]*)") do
                query_params[key] = value
            end
        end
    end
    
    return {
        method = method,
        path = path,
        headers = headers,
        body = body,
        params = query_params
    }
end

-- File operations
local function ensure_storage_dir()
    os.execute('mkdir -p "' .. storage_path .. '" 2>/dev/null')
end

local function list_files()
    local files = {}
    local p = io.popen('dir /b "' .. storage_path .. '" 2>nul')
    if p then
        for file in p:lines() do
            table.insert(files, file)
        end
        p:close()
    end
    return files
end

local function read_file(filename)
    local filepath = storage_path .. "/" .. filename
    local file = io.open(filepath, "rb")
    if file then
        local content = file:read("*all")
        file:close()
        return content
    end
    return nil
end

local function write_file(filename, content)
    ensure_storage_dir()
    local filepath = storage_path .. "/" .. filename
    local file = io.open(filepath, "wb")
    if file then
        file:write(content)
        file:close()
        return true
    end
    return false
end

local function delete_file(filename)
    local filepath = storage_path .. "/" .. filename
    return os.remove(filepath) ~= nil
end

-- API Handlers
local handlers = {}

-- GET / - Welcome
handlers["GET /"] = function(req)
    local lang = req.params.lang or "en"
    local t = TRANSLATIONS[lang] or TRANSLATIONS.en
    return json_response({
        status = "ok",
        service = "NAS Service",
        version = "2.0",
        message = t.welcome,
        languages = 28
    })
end

-- GET /api/languages - List all languages
handlers["GET /api/languages"] = function(req)
    local languages = {}
    for code, data in pairs(TRANSLATIONS) do
        table.insert(languages, { code = code, name = data.name })
    end
    return json_response({ status = "ok", languages = languages })
end

-- GET /api/translate - Translate text
handlers["GET /api/translate"] = function(req)
    local lang = req.params.lang or "en"
    local key = req.params.key or "welcome"
    local t = TRANSLATIONS[lang] or TRANSLATIONS.en
    local text = t[key] or t.welcome
    return json_response({ status = "ok", language = lang, text = text })
end

-- GET /api/files - List files
handlers["GET /api/files"] = function(req)
    local files = list_files()
    return json_response({ status = "ok", files = files, count = #files })
end

-- GET /api/file - Read file
handlers["GET /api/file"] = function(req)
    local filename = req.params.name
    if not filename or filename == "" then
        return json_response({ status = "error", message = "Filename required" }, 400)
    end
    
    local content = read_file(filename)
    if content then
        return json_response({ status = "ok", filename = filename, content = content })
    else
        return json_response({ status = "error", message = "File not found" }, 404)
    end
end

-- POST /api/file - Write file
handlers["POST /api/file"] = function(req)
    local data = json.decode(req.body) or {}
    local filename = data.name or data.filename
    local content = data.content or ""
    
    if not filename or filename == "" then
        return json_response({ status = "error", message = "Filename required" }, 400)
    end
    
    if write_file(filename, content) then
        return json_response({ status = "ok", message = "File saved", filename = filename })
    else
        return json_response({ status = "error", message = "Failed to save file" }, 500)
    end
end

-- DELETE /api/file - Delete file
handlers["DELETE /api/file"] = function(req)
    local data = json.decode(req.body) or {}
    local filename = data.name or data.filename or req.params.name
    
    if not filename or filename == "" then
        return json_response({ status = "error", message = "Filename required" }, 400)
    end
    
    if delete_file(filename) then
        return json_response({ status = "ok", message = "File deleted" })
    else
        return json_response({ status = "error", message = "Failed to delete file" }, 500)
    end
end

-- GET /api/status - Service status
handlers["GET /api/status"] = function(req)
    return json_response({
        status = "ok",
        uptime = os.time(),
        storage_path = storage_path,
        config = config
    })
end

-- GET /api/config - Get config
handlers["GET /api/config"] = function(req)
    return json_response({ status = "ok", config = config })
end

-- POST /api/config - Update config
handlers["POST /api/config"] = function(req)
    local data = json.decode(req.body) or {}
    for k, v in pairs(data) do
        config[k] = v
    end
    return json_response({ status = "ok", message = "Config updated" })
end

-- 404 handler
local function not_found_handler(req)
    return json_response({ status = "error", message = "Not Found", path = req.path }, 404)
end

-- Request router
local function route_request(req)
    local key = req.method .. " " .. (req.path or "/")
    
    -- Exact match
    if handlers[key] then
        return handlers[key](req)
    end
    
    -- Prefix match for dynamic routes
    for pattern, handler in pairs(handlers) do
        if key:find(pattern:gsub("%*", ".*")) == 1 then
            return handler(req)
        end
    end
    
    return not_found_handler(req)
end

-- Main server loop
local function start_server()
    load_config()
    ensure_storage_dir()
    
    local server = assert(socket.bind(config.host, config.port))
    server:settimeout(0)
    
    print(string.format("[NAS Service] Starting on %s:%d", config.host, config.port))
    print("[NAS Service] Supporting 28 languages")
    print("[NAS Service] Press Ctrl+C to stop")
    
    local clients = {}
    
    while true do
        local client = server:accept()
        if client then
            client:settimeout(config.timeout)
            local request, err = client:receive("*a")
            if request and #request > 0 then
                local req = parse_request(request)
                local response = route_request(req)
                client:send(response)
            end
            client:close()
        else
            socket.select({server}, nil, 0.1)
        end
    end
end

-- Error handling
local ok, err = pcall(start_server)
if not ok then
    print("[ERROR] " .. tostring(err))
    os.exit(1)
end