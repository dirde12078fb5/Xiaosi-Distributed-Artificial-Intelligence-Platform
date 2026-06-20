<?php
/**
 * 小思超级NAS - PHP版本
 * 智能存储管理平台
 * 
 * 作者: 小思AI团队
 * 版本: 1.0.0
 * 
 * 运行: php -S 0.0.0.0:8080 server.php
 */

// ==================== 配置 ====================
$config = [
    'port' => getenv('PORT') ?: 8080,
    'host' => getenv('HOST') ?: '0.0.0.0',
    'storage_path' => getenv('STORAGE_PATH') ?: '../storage',
    'public_path' => getenv('PUBLIC_PATH') ?: '../public',
    'jwt_secret' => getenv('JWT_SECRET') ?: 'xiaosi-nas-php-secret-2024',
    'default_user' => getenv('DEFAULT_USER') ?: 'admin',
    'default_password' => getenv('DEFAULT_PASSWORD') ?: 'admin123'
];

// ==================== 用户数据 ====================
$users = [
    'admin' => [
        'id' => '1',
        'username' => 'admin',
        'email' => 'admin@xiaosi.com',
        'password' => 'admin123',
        'role' => 'admin',
        'storage_quota' => 10 * 1024 * 1024 * 1024,
        'created_at' => '2024-01-01 00:00:00',
        'last_login' => date('Y-m-d H:i:s')
    ],
    'zhangsan' => [
        'id' => '2',
        'username' => 'zhangsan',
        'email' => 'zhangsan@xiaosi.com',
        'password' => 'password',
        'role' => 'user',
        'storage_quota' => 1 * 1024 * 1024 * 1024,
        'created_at' => '2024-01-01 00:00:00',
        'last_login' => date('Y-m-d H:i:s')
    ]
];

// ==================== 初始化 ====================
initialize();

// ==================== 工具函数 ====================
function initialize() {
    global $config;
    
    // 创建必要目录
    $dirs = [$config['storage_path'], $config['public_path']];
    foreach ($dirs as $dir) {
        if (!file_exists($dir)) {
            mkdir($dir, 0755, true);
        }
    }
}

function getFileIcon($filename, $isDir = false) {
    if ($isDir) return '📁';
    
    $icons = [
        '.pdf' => '📄', '.doc' => '📝', '.docx' => '📝',
        '.xls' => '📊', '.xlsx' => '📊', '.ppt' => '📽️', '.pptx' => '📽️',
        '.jpg' => '🖼️', '.jpeg' => '🖼️', '.png' => '🖼️', '.gif' => '🖼️',
        '.mp4' => '🎬', '.avi' => '🎬', '.mp3' => '🎵', '.wav' => '🎵',
        '.zip' => '📦', '.rar' => '📦', '.7z' => '📦',
        '.js' => '💻', '.html' => '💻', '.css' => '💻', '.php' => '💻'
    ];
    
    $ext = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
    return $icons['.' . $ext] ?? '📄';
}

function jsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    header('Access-Control-Allow-Origin: *');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

// ==================== 路由处理 ====================
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];

// 允许跨域
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($method === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// API路由
if (strpos($uri, '/api/') === 0) {
    $path = substr($uri, 5);
    
    switch ($path) {
        case 'stats':
            jsonResponse([
                'success' => true,
                'data' => [
                    'storage' => [
                        'used' => 2.5 * 1024 * 1024 * 1024,
                        'total' => 4 * 1024 * 1024 * 1024,
                        'percentage' => 62.5
                    ],
                    'files' => [
                        'count' => 1284,
                        'recent' => [
                            ['name' => '项目报告.pdf', 'user' => 'admin', 'time' => '5分钟前'],
                            ['name' => '新用户注册', 'user' => 'system', 'time' => '15分钟前']
                        ]
                    ],
                    'users' => [
                        'total' => count($GLOBALS['users']),
                        'online' => 2
                    ]
                ]
            ]);
            break;
            
        case 'files':
            jsonResponse([
                'success' => true,
                'data' => [
                    ['id' => '1', 'name' => '项目文档', 'type' => 'folder', 'icon' => '📁', 'size' => 0],
                    ['id' => '2', 'name' => '照片备份', 'type' => 'folder', 'icon' => '📁', 'size' => 0],
                    ['id' => '3', 'name' => '项目报告.pdf', 'type' => 'file', 'icon' => '📄', 'size' => 2621440],
                    ['id' => '4', 'name' => '会议纪要.docx', 'type' => 'file', 'icon' => '📝', 'size' => 159744],
                    ['id' => '5', 'name' => '数据表格.xlsx', 'type' => 'file', 'icon' => '📊', 'size' => 911360]
                ]
            ]);
            break;
            
        case 'users':
            $userList = array_map(function($user) {
                return [
                    'id' => $user['id'],
                    'username' => $user['username'],
                    'email' => $user['email'],
                    'role' => $user['role'],
                    'storage_quota' => $user['storage_quota'],
                    'status' => 'online',
                    'last_login' => $user['last_login']
                ];
            }, $GLOBALS['users']);
            jsonResponse(['success' => true, 'data' => array_values($userList)]);
            break;
            
        case 'settings':
            jsonResponse([
                'success' => true,
                'data' => [
                    'general' => [
                        'system_name' => '小思超级NAS',
                        'timezone' => 'Asia/Shanghai',
                        'language' => 'zh-CN',
                        'theme' => 'dark'
                    ],
                    'network' => [
                        'ip' => $GLOBALS['config']['host'],
                        'port' => $GLOBALS['config']['port']
                    ]
                ]
            ]);
            break;
            
        case 'auth/login':
            if ($method === 'POST') {
                $input = json_decode(file_get_contents('php://input'), true);
                $username = $input['username'] ?? '';
                $password = $input['password'] ?? '';
                
                $users = $GLOBALS['users'];
                if (isset($users[$username]) && $users[$username]['password'] === $password) {
                    jsonResponse([
                        'success' => true,
                        'data' => [
                            'token' => 'jwt-token-' . uniqid(),
                            'user' => [
                                'id' => $users[$username]['id'],
                                'username' => $users[$username]['username'],
                                'role' => $users[$username]['role'],
                                'email' => $users[$username]['email']
                            ]
                        ]
                    ]);
                } else {
                    jsonResponse(['success' => false, 'message' => 'Invalid credentials'], 401);
                }
            }
            break;
            
        default:
            jsonResponse(['success' => false, 'message' => 'API endpoint not found'], 404);
    }
}

// 静态文件服务
if ($uri !== '/' && file_exists($config['public_path'] . $uri)) {
    $file = $config['public_path'] . $uri;
    $ext = pathinfo($file, PATHINFO_EXTENSION);
    
    $mimeTypes = [
        'html' => 'text/html',
        'css' => 'text/css',
        'js' => 'application/javascript',
        'json' => 'application/json',
        'png' => 'image/png',
        'jpg' => 'image/jpeg',
        'jpeg' => 'image/jpeg',
        'gif' => 'image/gif',
        'svg' => 'image/svg+xml'
    ];
    
    $mimeType = $mimeTypes[$ext] ?? 'application/octet-stream';
    header('Content-Type: ' . $mimeType);
    readfile($file);
    exit;
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小思超级NAS - PHP版本</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #0a0e17 0%, #1a1f2e 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            text-align: center;
            max-width: 700px;
            padding: 40px;
        }
        .logo { font-size: 80px; margin-bottom: 24px; }
        h1 {
            background: linear-gradient(135deg, #0066ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 42px;
            margin-bottom: 16px;
        }
        .subtitle { color: #9ca3af; font-size: 20px; margin-bottom: 40px; }
        .info-box {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 16px;
            padding: 32px;
            text-align: left;
            margin-bottom: 24px;
        }
        .info-box h3 { color: #0066ff; margin-bottom: 20px; }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #1f2937;
        }
        .info-row:last-child { border-bottom: none; }
        .info-label { color: #9ca3af; }
        .info-value { color: #10b981; font-weight: 600; }
        .tech-stack { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
        .tech-tag {
            background: linear-gradient(135deg, #0066ff, #7c3aed);
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }
        .port-note {
            margin-top: 24px;
            padding: 16px;
            background: rgba(0, 102, 255, 0.1);
            border-radius: 12px;
            color: #3385ff;
        }
        code { background: rgba(0,102,255,0.2); padding: 4px 8px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">💾</div>
        <h1>小思超级NAS</h1>
        <p class="subtitle">PHP 版本 - 高性能存储管理平台</p>
        
        <div class="info-box">
            <h3>📡 访问地址</h3>
            <div class="info-row">
                <span class="info-label">本地访问</span>
                <span class="info-value">http://localhost:<?php echo $config['port']; ?></span>
            </div>
            <div class="info-row">
                <span class="info-label">端口</span>
                <span class="info-value"><?php echo $config['port']; ?></span>
            </div>
        </div>
        
        <div class="info-box">
            <h3>👤 默认登录</h3>
            <div class="info-row">
                <span class="info-label">用户名</span>
                <span class="info-value">admin</span>
            </div>
            <div class="info-row">
                <span class="info-label">密码</span>
                <span class="info-value">admin123</span>
            </div>
        </div>
        
        <div class="tech-stack">
            <span class="tech-tag">PHP <?php echo phpversion(); ?></span>
            <span class="tech-tag">JSON</span>
            <span class="tech-tag">REST API</span>
        </div>
        
        <div class="port-note">
            💡 使用 <code>php -S <?php echo $config['host']; ?>:<?php echo $config['port']; ?> server.php</code> 启动
        </div>
    </div>
</body>
</html>
