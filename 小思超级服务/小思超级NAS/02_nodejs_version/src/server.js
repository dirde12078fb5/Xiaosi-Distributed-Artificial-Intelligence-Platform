/**
 * 小思超级NAS - Node.js版本
 * 智能存储管理平台
 * 
 * 作者: 小思AI团队
 * 版本: 1.0.0
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');

// ==================== 配置 ====================
const config = {
    port: process.env.PORT || 8080,
    host: process.env.HOST || '0.0.0.0',
    jwtSecret: process.env.JWT_SECRET || 'xiaosi-nas-node-secret-2024',
    storagePath: process.env.STORAGE_PATH || '../storage',
    publicPath: process.env.PUBLIC_PATH || '../public',
    maxFileSize: parseInt(process.env.MAX_FILE_SIZE) || 1024 * 1024 * 1024,
    defaultUser: process.env.DEFAULT_USER || 'admin',
    defaultPassword: process.env.DEFAULT_PASSWORD || 'admin123'
};

// ==================== 应用初始化 ====================
const app = express();

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.static(config.publicPath));

// ==================== 数据存储 ====================
const users = new Map([
    ['admin', {
        id: '1',
        username: 'admin',
        email: 'admin@xiaosi.com',
        password: bcrypt.hashSync('admin123', 10),
        role: 'admin',
        storageQuota: 10 * 1024 * 1024 * 1024,
        createdAt: new Date(),
        lastLogin: new Date()
    }],
    ['zhangsan', {
        id: '2',
        username: 'zhangsan',
        email: 'zhangsan@xiaosi.com',
        password: bcrypt.hashSync('password', 10),
        role: 'user',
        storageQuota: 1 * 1024 * 1024 * 1024,
        createdAt: new Date(),
        lastLogin: new Date()
    }],
    ['lisi', {
        id: '3',
        username: 'lisi',
        email: 'lisi@xiaosi.com',
        password: bcrypt.hashSync('password', 10),
        role: 'user',
        storageQuota: 1 * 1024 * 1024 * 1024,
        createdAt: new Date(),
        lastLogin: new Date()
    }]
]);

// ==================== 工具函数 ====================
function getFileIcon(filename, isDir) {
    if (isDir) return '📁';
    
    const icons = {
        '.pdf': '📄', '.doc': '📝', '.docx': '📝',
        '.xls': '📊', '.xlsx': '📊', '.ppt': '📽️', '.pptx': '📽️',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
        '.mp4': '🎬', '.avi': '🎬', '.mp3': '🎵', '.wav': '🎵',
        '.zip': '📦', '.rar': '📦', '.7z': '📦',
        '.js': '💻', '.html': '💻', '.css': '💻'
    };
    
    const ext = path.extname(filename).toLowerCase();
    return icons[ext] || '📄';
}

function getLocalIPs() {
    const nets = require('os').networkInterfaces();
    const ips = [];
    
    for (const name of Object.keys(nets)) {
        for (const net of nets[name]) {
            if (net.family === 'IPv4' && !net.internal) {
                ips.push(net.address);
            }
        }
    }
    
    return ips;
}

// ==================== 认证中间件 ====================
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ success: false, message: 'Authorization required' });
    }
    
    jwt.verify(token, config.jwtSecret, (err, user) => {
        if (err) {
            return res.status(403).json({ success: false, message: 'Invalid token' });
        }
        req.user = user;
        next();
    });
}

// ==================== API路由 ====================

// 用户登录
app.post('/api/auth/login', (req, res) => {
    const { username, password } = req.body;
    const user = users.get(username);
    
    if (!user || !bcrypt.compareSync(password, user.password)) {
        return res.json({ success: false, message: 'Invalid credentials' });
    }
    
    const token = jwt.sign(
        { userId: user.id, username: user.username, role: user.role },
        config.jwtSecret,
        { expiresIn: '24h' }
    );
    
    user.lastLogin = new Date();
    
    res.json({
        success: true,
        data: {
            token,
            user: {
                id: user.id,
                username: user.username,
                role: user.role,
                email: user.email
            }
        }
    });
});

// 获取系统统计
app.get('/api/stats', authenticateToken, (req, res) => {
    res.json({
        success: true,
        data: {
            storage: {
                used: 2.5 * 1024 * 1024 * 1024,
                total: 4 * 1024 * 1024 * 1024,
                percentage: 62.5
            },
            files: {
                count: 1284,
                recent: [
                    { name: '项目报告.pdf', user: 'admin', time: '5分钟前' },
                    { name: '新用户注册', user: 'system', time: '15分钟前' }
                ]
            },
            users: {
                total: users.size,
                online: 2
            }
        }
    });
});

// 获取文件列表
app.get('/api/files', authenticateToken, (req, res) => {
    const files = [
        { id: '1', name: '项目文档', type: 'folder', icon: '📁', size: 0, modifiedAt: new Date().toISOString() },
        { id: '2', name: '照片备份', type: 'folder', icon: '📁', size: 0, modifiedAt: new Date().toISOString() },
        { id: '3', name: '项目报告.pdf', type: 'file', icon: '📄', size: 2621440, modifiedAt: new Date().toISOString() },
        { id: '4', name: '会议纪要.docx', type: 'file', icon: '📝', size: 159744, modifiedAt: new Date().toISOString() },
        { id: '5', name: '数据表格.xlsx', type: 'file', icon: '📊', size: 911360, modifiedAt: new Date().toISOString() }
    ];
    
    res.json({ success: true, data: files });
});

// 获取用户列表
app.get('/api/users', authenticateToken, (req, res) => {
    const userList = Array.from(users.values()).map(u => ({
        id: u.id,
        username: u.username,
        email: u.email,
        role: u.role,
        storageQuota: u.storageQuota,
        status: new Date() - u.lastLogin < 3600000 ? 'online' : 'offline',
        lastLogin: u.lastLogin
    }));
    
    res.json({ success: true, data: userList });
});

// 获取系统设置
app.get('/api/settings', authenticateToken, (req, res) => {
    res.json({
        success: true,
        data: {
            general: {
                systemName: '小思超级NAS',
                timezone: 'Asia/Shanghai',
                language: 'zh-CN',
                theme: 'dark'
            },
            network: {
                ip: config.host,
                port: config.port
            }
        }
    });
});

// 首页
app.get('/', (req, res) => {
    const indexPath = path.join(__dirname, config.publicPath, 'index.html');
    if (fs.existsSync(indexPath)) {
        res.sendFile(indexPath);
    } else {
        res.send(generateWelcomePage());
    }
});

function generateWelcomePage() {
    return `<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>小思超级NAS - Node.js版本</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #0a0e17, #1a1f2e); 
            color: #fff; 
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
        }
        .container { text-align: center; max-width: 600px; padding: 40px; }
        .logo { font-size: 80px; margin-bottom: 24px; }
        h1 { 
            background: linear-gradient(135deg, #0066ff, #7c3aed); 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            font-size: 36px; 
            margin-bottom: 16px; 
        }
        p { color: #9ca3af; font-size: 18px; margin-bottom: 32px; }
        .info { background: #111827; border: 1px solid #1f2937; border-radius: 16px; padding: 32px; }
        .info h3 { margin-bottom: 16px; color: #0066ff; }
        .info p { font-size: 14px; margin-bottom: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">💾</div>
        <h1>小思超级NAS</h1>
        <p>Node.js 版本 - 高性能存储管理平台</p>
        <div class="info">
            <h3>📡 访问地址</h3>
            <p>本地访问: http://localhost:${config.port}</p>
            <p>局域网访问: http://&lt;您的IP&gt;:${config.port}</p>
            <br>
            <h3>👤 默认登录</h3>
            <p>用户名: admin</p>
            <p>密码: admin123</p>
        </div>
    </div>
</body>
</html>`;
}

// ==================== 启动服务器 ====================
const localIPs = getLocalIPs();

console.log('\n============================================');
console.log('   🚀 小思超级NAS (Node.js版本) 已启动！');
console.log('============================================');
console.log('\n📡 访问地址：');
console.log(`   本地访问：http://localhost:${config.port}`);
localIPs.forEach(ip => console.log(`   局域网访问：http://${ip}:${config.port}`));
console.log('\n👤 默认登录：');
console.log('   用户名：admin');
console.log('   密码：admin123');
console.log('\n============================================\n');

app.listen(config.port, config.host, () => {
    console.log('✅ 服务器正在运行...');
});
