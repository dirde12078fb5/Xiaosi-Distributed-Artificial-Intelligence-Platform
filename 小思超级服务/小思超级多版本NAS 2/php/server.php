<?php
/**
 * 小思超级NAS服务 - PHP版本
 * 版本: 2.0
 * 默认端口: 8088
 */

// 错误处理
error_reporting(E_ALL);
ini_set('display_errors', 1);

// 定义常量
define('ROOT_DIR', dirname(dirname(__FILE__)));
define('CONFIG_FILE', ROOT_DIR . '/config/config.json');
define('I18N_DIR', ROOT_DIR . '/config/i18n');
define('DATA_DIR', ROOT_DIR . '/nas_data');

// 加载配置
function loadConfig() {
    if (!file_exists(CONFIG_FILE)) {
        return [
            'server' => ['host' => '0.0.0.0', 'port' => 8088, 'language' => 'zh_CN'],
            'storage' => ['volumes' => []],
            'smb' => ['enabled' => true, 'port' => 445, 'workgroup' => 'WORKGROUP'],
            'push' => ['targets' => []],
            'data_dir' => 'nas_data',
            'receive_dir' => 'nas_data/received'
        ];
    }
    return json_decode(file_get_contents(CONFIG_FILE), true);
}

// 加载翻译
function loadTranslation($lang) {
    $file = I18N_DIR . '/' . $lang . '.json';
    if (file_exists($file)) {
        return json_decode(file_get_contents($file), true);
    }
    return json_decode(file_get_contents(I18N_DIR . '/zh_CN.json'), true);
}

// JSON响应
function jsonResponse($success, $data = null, $message = '', $code = 200) {
    header('Content-Type: application/json; charset=utf-8');
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    
    http_response_code($code);
    echo json_encode([
        'success' => $success,
        'data' => $data,
        'message' => $message,
        'timestamp' => time()
    ], JSON_UNESCAPED_UNICODE);
}

// 获取POST数据
function getPostData() {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    if ($data === null) {
        $data = $_POST;
    }
    return $data;
}

// 存储卷管理
class StorageManager {
    private $config;
    
    public function __construct($config) {
        $this->config = $config;
    }
    
    public function getVolumes() {
        return $this->config['storage']['volumes'] ?? [];
    }
    
    public function createVolume($name, $path, $quotaGb) {
        $volume = [
            'name' => $name,
            'path' => $path,
            'quota_gb' => $quotaGb,
            'created_at' => time()
        ];
        
        $this->config['storage']['volumes'][] = $volume;
        $this->saveConfig();
        
        // 创建目录
        $fullPath = ROOT_DIR . '/' . $path;
        if (!file_exists($fullPath)) {
            mkdir($fullPath, 0755, true);
        }
        
        return $volume;
    }
    
    public function deleteVolume($name) {
        $volumes = &$this->config['storage']['volumes'];
        foreach ($volumes as $i => $vol) {
            if ($vol['name'] === $name) {
                array_splice($volumes, $i, 1);
                $this->saveConfig();
                return true;
            }
        }
        return false;
    }
    
    private function saveConfig() {
        file_put_contents(CONFIG_FILE, json_encode($this->config, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }
}

// 用户管理
class UserManager {
    private $dataFile;
    
    public function __construct() {
        $this->dataFile = DATA_DIR . '/users.json';
        if (!file_exists($this->dataFile)) {
            file_put_contents($this->dataFile, json_encode([]));
        }
    }
    
    public function getUsers() {
        return json_decode(file_get_contents($this->dataFile), true) ?: [];
    }
    
    public function createUser($username, $password) {
        $users = $this->getUsers();
        
        // 检查是否已存在
        foreach ($users as $user) {
            if ($user['username'] === $username) {
                return false;
            }
        }
        
        $users[] = [
            'username' => $username,
            'password' => password_hash($password, PASSWORD_DEFAULT),
            'created_at' => time()
        ];
        
        file_put_contents($this->dataFile, json_encode($users, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        return true;
    }
    
    public function deleteUser($username) {
        $users = $this->getUsers();
        $found = false;
        
        $users = array_filter($users, function($user) use ($username, &$found) {
            if ($user['username'] === $username) {
                $found = true;
                return false;
            }
            return true;
        });
        
        if ($found) {
            file_put_contents($this->dataFile, json_encode(array_values($users), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
            return true;
        }
        
        return false;
    }
}

// SMB共享管理
class SMBManager {
    private $dataFile;
    
    public function __construct() {
        $this->dataFile = DATA_DIR . '/smb_shares.json';
        if (!file_exists($this->dataFile)) {
            file_put_contents($this->dataFile, json_encode([]));
        }
    }
    
    public function getShares() {
        return json_decode(file_get_contents($this->dataFile), true) ?: [];
    }
    
    public function createShare($name, $path, $permissions) {
        $shares = $this->getShares();
        
        $shares[] = [
            'name' => $name,
            'path' => $path,
            'permissions' => $permissions,
            'created_at' => time()
        ];
        
        file_put_contents($this->dataFile, json_encode($shares, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        return true;
    }
    
    public function deleteShare($name) {
        $shares = $this->getShares();
        $found = false;
        
        $shares = array_filter($shares, function($share) use ($name, &$found) {
            if ($share['name'] === $name) {
                $found = true;
                return false;
            }
            return true;
        });
        
        if ($found) {
            file_put_contents($this->dataFile, json_encode(array_values($shares), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
            return true;
        }
        
        return false;
    }
}

// IP检测
class IPManager {
    public function getLocalIPs() {
        $ips = [];
        
        // Windows系统
        if (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') {
            exec('ipconfig', $output);
            foreach ($output as $line) {
                if (preg_match('/IPv4 Address[\. :]+([0-9\.]+)/', $line, $matches)) {
                    $ips[] = $matches[1];
                }
            }
        } else {
            // Linux/Mac系统
            exec('ifconfig | grep "inet " | grep -v 127.0.0.1', $output);
            foreach ($output as $line) {
                if (preg_match('/inet ([0-9\.]+)/', $line, $matches)) {
                    $ips[] = $matches[1];
                }
            }
        }
        
        return $ips;
    }
    
    public function scanDevices($port) {
        // 简单的局域网扫描（仅检测常见IP段）
        $devices = [];
        $localIPs = $this->getLocalIPs();
        
        foreach ($localIPs as $ip) {
            $parts = explode('.', $ip);
            if (count($parts) === 4) {
                $subnet = $parts[0] . '.' . $parts[1] . '.' . $parts[2] . '.';
                
                // 扫描部分IP范围
                for ($i = 1; $i <= 10; $i++) {
                    $targetIP = $subnet . $i;
                    if ($targetIP !== $ip) {
                        $fp = @fsockopen($targetIP, $port, $errno, $errstr, 1);
                        if ($fp) {
                            fclose($fp);
                            $devices[] = [
                                'ip' => $targetIP,
                                'port' => $port,
                                'status' => 'online'
                            ];
                        }
                    }
                }
            }
        }
        
        return $devices;
    }
}

// 推送服务
class PushManager {
    private $config;
    private $historyFile;
    
    public function __construct($config) {
        $this->config = $config;
        $this->historyFile = DATA_DIR . '/push_history.json';
        if (!file_exists($this->historyFile)) {
            file_put_contents($this->historyFile, json_encode([]));
        }
    }
    
    public function getTargets() {
        return $this->config['push']['targets'] ?? [];
    }
    
    public function addTarget($ip, $port) {
        $target = [
            'ip' => $ip,
            'port' => $port,
            'added_at' => time()
        ];
        
        $this->config['push']['targets'][] = $target;
        $this->saveConfig();
        
        return $target;
    }
    
    public function pushFolder($folderPath, $targetIP, $targetPort) {
        $result = [
            'folder' => $folderPath,
            'target' => $targetIP . ':' . $targetPort,
            'status' => 'pending',
            'timestamp' => time()
        ];
        
        // 简单的推送实现（实际应使用HTTP multipart）
        $url = "http://{$targetIP}:{$targetPort}/api/push/receive";
        
        // 记录推送历史
        $history = json_decode(file_get_contents($this->historyFile), true) ?: [];
        $history[] = $result;
        file_put_contents($this->historyFile, json_encode($history, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        
        return $result;
    }
    
    public function getPushHistory() {
        return json_decode(file_get_contents($this->historyFile), true) ?: [];
    }
    
    public function receiveFile() {
        $receiveDir = ROOT_DIR . '/' . $this->config['receive_dir'];
        if (!file_exists($receiveDir)) {
            mkdir($receiveDir, 0755, true);
        }
        
        // 处理multipart数据
        if (isset($_FILES['file'])) {
            $folder = isset($_POST['folder']) ? $_POST['folder'] : 'unknown';
            $filepath = isset($_POST['filepath']) ? $_POST['filepath'] : '';
            
            $targetDir = $receiveDir . '/' . $folder;
            if (!file_exists($targetDir)) {
                mkdir($targetDir, 0755, true);
            }
            
            if ($filepath) {
                $subDir = $targetDir . '/' . dirname($filepath);
                if (!file_exists($subDir)) {
                    mkdir($subDir, 0755, true);
                }
            }
            
            $fileName = basename($filepath ?: $_FILES['file']['name']);
            $targetFile = $targetDir . '/' . ($filepath ? $filepath : $fileName);
            
            if (move_uploaded_file($_FILES['file']['tmp_name'], $targetFile)) {
                return [
                    'success' => true,
                    'file' => $targetFile,
                    'folder' => $folder
                ];
            }
        }
        
        return ['success' => false, 'message' => 'No file received'];
    }
    
    private function saveConfig() {
        file_put_contents(CONFIG_FILE, json_encode($this->config, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }
}

// 主程序
$config = loadConfig();
$i18n = loadTranslation($config['server']['language']);

$storageManager = new StorageManager($config);
$userManager = new UserManager();
$smbManager = new SMBManager();
$ipManager = new IPManager();
$pushManager = new PushManager($config);

// 路由处理
$uri = $_SERVER['REQUEST_URI'];
$method = $_SERVER['REQUEST_METHOD'];

// 处理OPTIONS请求
if ($method === 'OPTIONS') {
    jsonResponse(true);
    exit;
}

// API路由
try {
    // 存储管理
    if (preg_match('#^/api/storage/volumes$#', $uri)) {
        if ($method === 'GET') {
            jsonResponse(true, $storageManager->getVolumes(), $i18n['success']);
        } elseif ($method === 'POST') {
            $data = getPostData();
            if (isset($data['name']) && isset($data['path']) && isset($data['quota_gb'])) {
                $volume = $storageManager->createVolume($data['name'], $data['path'], $data['quota_gb']);
                jsonResponse(true, $volume, $i18n['success']);
            } else {
                jsonResponse(false, null, $i18n['error_params'], 400);
            }
        }
    }
    
    elseif (preg_match('#^/api/storage/volumes/delete$#', $uri)) {
        if ($method === 'POST') {
            $data = getPostData();
            if (isset($data['name'])) {
                if ($storageManager->deleteVolume($data['name'])) {
                    jsonResponse(true, null, $i18n['success']);
                } else {
                    jsonResponse(false, null, $i18n['error_not_found'], 404);
                }
            } else {
                jsonResponse(false, null, $i18n['error_params'], 400);
            }
        }
    }
    
    // 用户管理
    elseif (preg_match('#^/api/users$#', $uri)) {
        if ($method === 'GET') {
            jsonResponse(true, $userManager->getUsers(), $i18n['success']);
        } elseif ($method === 'POST') {
            $data = getPostData();
            if (isset($data['username']) && isset($data['password'])) {
                if ($userManager->createUser($data['username'], $data['password'])) {
                    jsonResponse(true, null, $i18n['success']);
                } else {
                    jsonResponse(false, null, 'User already exists', 400);
                }
            } else {
                jsonResponse(false, null, $i18n['error_params'], 400);
            }
        }
    }
    
    elseif (preg_match('#^/api/users/delete$#', $uri)) {
        if ($method === 'POST') {
            $data = getPostData();
            if (isset($data['username'])) {
                if ($userManager->deleteUser($data['username'])) {
                    jsonResponse(true, null, $i18n['success']);
                } else {
                    jsonResponse(false, null, $i18n['error_not_found'], 404);
                }
            } else {
                jsonResponse(false, null, $i18n['error_params'], 400);
            }
        }
    }
    
    // SMB共享
    elseif (preg_match('#^/api/smb/shares$#', $uri)) {
        if ($method === 'GET') {
            jsonResponse(true, $smbManager->getShares(), $i18n['success']);
        } elseif ($method === 'POST') {
            $data = getPostData();
            if (isset($data['name']) && isset($data['path']) && isset($data['permissions'])) {
                $smbManager->createShare($data['name'], $data['path'], $data['permissions']);
                jsonResponse(true, null, $i18n['success']);
            } else {
                jsonResponse(false, null, $i18n['error_params'], 400);
            }
        }
    }
    
    elseif (preg_match('#^/api/smb/shares/delete$#', $uri)) {
        if ($method === 'POST') {
            $data = getPostData();
            if (isset($data['name'])) {
                if ($smbManager->deleteShare($data['name'])) {
                    jsonResponse(true, null, $i18n['success']);
                } else {
                    jsonResponse(false, null, $i18n['error_not_found'], 404);
                }
            } else {
                jsonResponse(false, null, $i18n['error_params'], 400);
            }
        }
    }
    
    // IP检测
    elseif (preg_match('#^/api/ip/local$#', $uri)) {
        if ($method === 'GET') {
            jsonResponse(true, $ipManager->getLocalIPs(), $i18n['success']);
        }
    }
    
    elseif (preg_match('#^/api/ip/scan#', $uri)) {
        if ($method === 'GET') {
            $port = isset($_GET['port']) ? intval($_GET['port']) : 8088;
            jsonResponse(true, $ipManager->scanDevices($port), $i18n['success']);
        }
    }
    
    // 推送服务
    elseif (preg_match('#^/api/push/targets$#', $uri)) {
        if ($method === 'GET') {
            jsonResponse(true, $pushManager->getTargets(), $i18n['success']);
        } elseif ($method === 'POST') {
            $data = getPostData();
            if (isset($data['ip']) && isset($data['port'])) {
                $target = $pushManager->addTarget($data['ip'], $data['port']);
                jsonResponse(true, $target, $i18n['success']);
            } else {
                jsonResponse(false, null, $i18n['error_params'], 400);
            }
        }
    }
    
    elseif (preg_match('#^/api/push/folder$#', $uri)) {
        if ($method === 'POST') {
            $data = getPostData();
            if (isset($data['folder_path']) && isset($data['target_ip']) && isset($data['target_port'])) {
                $result = $pushManager->pushFolder($data['folder_path'], $data['target_ip'], $data['target_port']);
                jsonResponse(true, $result, $i18n['success']);
            } else {
                jsonResponse(false, null, $i18n['error_params'], 400);
            }
        }
    }
    
    elseif (preg_match('#^/api/push/status$#', $uri)) {
        if ($method === 'GET') {
            jsonResponse(true, $pushManager->getPushHistory(), $i18n['success']);
        }
    }
    
    elseif (preg_match('#^/api/push/receive$#', $uri)) {
        if ($method === 'POST') {
            $result = $pushManager->receiveFile();
            if ($result['success']) {
                jsonResponse(true, $result, $i18n['success']);
            } else {
                jsonResponse(false, null, $result['message'], 400);
            }
        }
    }
    
    // 多语言
    elseif (preg_match('#^/api/i18n#', $uri)) {
        if ($method === 'GET') {
            $lang = isset($_GET['lang']) ? $_GET['lang'] : $config['server']['language'];
            $translation = loadTranslation($lang);
            jsonResponse(true, $translation, $i18n['success']);
        }
    }
    
    // 首页
    elseif ($uri === '/' || $uri === '/index.html') {
        echo '<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>' . $i18n['app_name'] . '</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .api-list { background: #f5f5f5; padding: 20px; border-radius: 5px; margin-top: 20px; }
        .api-item { margin: 10px 0; }
        .api-method { color: #007bff; font-weight: bold; }
        .api-path { color: #666; }
    </style>
</head>
<body>
    <h1>' . $i18n['welcome'] . '</h1>
    <p>PHP版本 - 端口: ' . $config['server']['port'] . '</p>
    
    <div class="api-list">
        <h2>API接口列表</h2>
        <div class="api-item"><span class="api-method">GET</span> <span class="api-path">/api/storage/volumes</span></div>
        <div class="api-item"><span class="api-method">POST</span> <span class="api-path">/api/storage/volumes</span></div>
        <div class="api-item"><span class="api-method">POST</span> <span class="api-path">/api/storage/volumes/delete</span></div>
        <div class="api-item"><span class="api-method">GET</span> <span class="api-path">/api/users</span></div>
        <div class="api-item"><span class="api-method">POST</span> <span class="api-path">/api/users</span></div>
        <div class="api-item"><span class="api-method">POST</span> <span class="api-path">/api/users/delete</span></div>
        <div class="api-item"><span class="api-method">GET</span> <span class="api-path">/api/smb/shares</span></div>
        <div class="api-item"><span class="api-method">POST</span> <span class="api-path">/api/smb/shares</span></div>
        <div class="api-item"><span class="api-method">POST</span> <span class="api-path">/api/smb/shares/delete</span></div>
        <div class="api-item"><span class="api-method">GET</span> <span class="api-path">/api/ip/local</span></div>
        <div class="api-item"><span class="api-method">GET</span> <span class="api-path">/api/ip/scan?port=8088</span></div>
        <div class="api-item"><span class="api-method">GET</span> <span class="api-path">/api/push/targets</span></div>
        <div class="api-item"><span class="api-method">POST</span> <span class="api-path">/api/push/targets</span></div>
        <div class="api-item"><span class="api-method">POST</span> <span class="api-path">/api/push/folder</span></div>
        <div class="api-item"><span class="api-method">GET</span> <span class="api-path">/api/push/status</span></div>
        <div class="api-item"><span class="api-method">POST</span> <span class="api-path">/api/push/receive</span></div>
        <div class="api-item"><span class="api-method">GET</span> <span class="api-path">/api/i18n/?lang=zh_CN</span></div>
    </div>
</body>
</html>';
    }
    
    else {
        jsonResponse(false, null, $i18n['error_not_found'], 404);
    }
    
} catch (Exception $e) {
    jsonResponse(false, null, $i18n['error_server'] . ': ' . $e->getMessage(), 500);
}