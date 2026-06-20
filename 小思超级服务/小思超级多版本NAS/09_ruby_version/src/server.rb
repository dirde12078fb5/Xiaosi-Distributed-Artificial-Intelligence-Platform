# frozen_string_literal: true

# 小思超级NAS - Ruby语言版本
# 智能存储管理平台
#
# 作者: 小思AI团队
# 版本: 1.0.0
#
# 运行: ruby server.rb

require 'sinatra'
require 'json'
require 'bcrypt'
require 'jwt'
require 'time'

# ==================== 配置 ====================
PORT = ENV.fetch('PORT', 8080).to_i
HOST = ENV.fetch('HOST', '0.0.0.0')
PUBLIC_PATH = ENV.fetch('PUBLIC_PATH', '../public')
STORAGE_PATH = ENV.fetch('STORAGE_PATH', '../storage')
JWT_SECRET = ENV.fetch('JWT_SECRET', 'xiaosi-nas-ruby-secret-2024')

# ==================== 用户数据 ====================
USERS = {
  'admin' => {
    id: '1',
    username: 'admin',
    email: 'admin@xiaosi.com',
    password_hash: BCrypt::Password.create('admin123'),
    role: 'admin',
    created_at: Time.now.utc.iso8601
  },
  'zhangsan' => {
    id: '2',
    username: 'zhangsan',
    email: 'zhangsan@xiaosi.com',
    password_hash: BCrypt::Password.create('password'),
    role: 'user',
    created_at: Time.now.utc.iso8601
  }
}.freeze

# ==================== 中间件 ====================
before do
  content_type :json
  headers['Access-Control-Allow-Origin'] = '*'
  headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
  headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

  if request.request_method == 'OPTIONS'
    status 200
    return
  end
end

# ==================== 辅助方法 ====================
def json_response(data:, status: 200)
  status status
  { success: true, data: data }.to_json
end

def error_response(message:, status: 400)
  status status
  { success: false, message: message }.to_json
end

def authenticate!
  auth_header = request.env['HTTP_AUTHORIZATION']
  
  unless auth_header
    halt 401, error_response(message: 'Authorization required', status: 401)
  end
  
  token = auth_header.gsub('Bearer ', '')
  
  begin
    decoded_token = JWT.decode(token, JWT_SECRET, true, algorithm: 'HS256')
    @current_user = decoded_token[0]
  rescue JWT::DecodeError
    halt 403, error_response(message: 'Invalid token', status: 403)
  end
end

# ==================== API路由 ====================

# 用户登录
post '/api/auth/login' do
  payload = JSON.parse(request.body.read)
  username = payload['username']
  password = payload['password']
  
  user = USERS[username]
  
  unless user && BCrypt::Password.new(user[:password_hash]) == password
    halt 401, error_response(message: 'Invalid credentials', status: 401)
  end
  
  exp_time = (Time.now + 24 * 60 * 60).to_i
  
  token = JWT.encode({
    sub: user[:id],
    user_id: user[:id],
    username: user[:username],
    role: user[:role],
    exp: exp_time
  }, JWT_SECRET, 'HS256')
  
  json_response(
    data: {
      token: token,
      user: {
        id: user[:id],
        username: user[:username],
        role: user[:role],
        email: user[:email]
      }
    }
  )
end

# 获取系统统计
get '/api/stats' do
  authenticate!
  
  json_response(
    data: {
      storage: {
        used: 2_684_354_560,
        total: 4_294_967_296,
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
        total: USERS.size,
        online: 2
      }
    }
  )
end

# 获取文件列表
get '/api/files' do
  authenticate!
  
  files = [
    { id: '1', name: '项目文档', type: 'folder', icon: '📁', size: 0 },
    { id: '2', name: '照片备份', type: 'folder', icon: '📁', size: 0 },
    { id: '3', name: '项目报告.pdf', type: 'file', icon: '📄', size: 2_621_440 },
    { id: '4', name: '会议纪要.docx', type: 'file', icon: '📝', size: 159_744 },
    { id: '5', name: '数据表格.xlsx', type: 'file', icon: '📊', size: 911_360 }
  ]
  
  json_response(data: files)
end

# 获取用户列表
get '/api/users' do
  authenticate!
  
  user_list = USERS.values.map do |user|
    {
      id: user[:id],
      username: user[:username],
      email: user[:email],
      role: user[:role],
      storage_quota: 10_737_418_240,
      status: 'online',
      last_login: user[:created_at]
    }
  end
  
  json_response(data: user_list)
end

# 获取系统设置
get '/api/settings' do
  authenticate!
  
  json_response(
    data: {
      general: {
        system_name: '小思超级NAS',
        timezone: 'Asia/Shanghai',
        language: 'zh-CN',
        theme: 'dark'
      },
      network: {
        ip: HOST,
        port: PORT
      }
    }
  )
end

# 静态文件服务
get '/' do
  content_type :html
  File.read(File.join(PUBLIC_PATH, 'index.html'))
rescue Errno::ENOENT
  generate_welcome_page
end

get '/styles.css' do
  content_type :css
  File.read(File.join(PUBLIC_PATH, 'styles.css'))
rescue Errno::ENOENT
  ''
end

get '/app.js' do
  content_type :javascript
  File.read(File.join(PUBLIC_PATH, 'app.js'))
rescue Errno::ENOENT
  ''
end

# ==================== 辅助方法 ====================
def generate_welcome_page
  <<~HTML
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>小思超级NAS - Ruby版本</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: linear-gradient(135deg, #0a0e17, #1a1f2e);
          color: #fff;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .container { text-align: center; max-width: 700px; padding: 40px; }
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
        .tech-stack { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
        .tech-tag {
          background: linear-gradient(135deg, #0066ff, #7c3aed);
          padding: 8px 20px;
          border-radius: 20px;
          font-size: 14px;
          font-weight: 600;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="logo">💾</div>
        <h1>小思超级NAS</h1>
        <p class="subtitle">Ruby 版本 - 优雅的存储管理平台</p>
        
        <div class="info-box">
          <h3>📡 访问地址</h3>
          <p>本地访问: http://localhost:#{PORT}</p>
        </div>
        
        <div class="tech-stack">
          <span class="tech-tag">Ruby #{RUBY_VERSION}</span>
          <span class="tech-tag">Sinatra</span>
          <span class="tech-tag">JWT</span>
          <span class="tech-tag">REST API</span>
        </div>
      </div>
    </body>
    </html>
  HTML
end

# ==================== 启动信息 ====================
puts "\n============================================"
puts "   🚀 小思超级NAS (Ruby版本) 已启动！"
puts "============================================"
puts "\n📡 访问地址："
puts "   本地访问：http://localhost:#{PORT}"
puts "   局域网访问：http://<您的IP>:#{PORT}"
puts "\n👤 默认登录："
puts "   用户名：admin"
puts "   密码：admin123"
puts "\n============================================\n"

Sinatra.run!(host: HOST, port: PORT)
