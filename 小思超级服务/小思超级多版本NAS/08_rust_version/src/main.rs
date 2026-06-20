//! 小思超级NAS - Rust语言版本
//! 智能存储管理平台
//!
//! 作者: 小思AI团队
//! 版本: 1.0.0
//!
//! 运行: cargo run --release

use actix_web::{web, App, HttpResponse, HttpServer, middleware};
use actix_cors::Cors;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;
use chrono::Utc;
use jsonwebtoken::{encode, decode, Header, Validation, EncodingKey, DecodingKey};
use jsonwebtoken::errors::ErrorKind;

// ==================== 配置 ====================
struct AppState {
    users: Mutex<HashMap<String, UserInfo>>,
}

#[derive(Clone, Serialize, Deserialize)]
struct UserInfo {
    id: String,
    username: String,
    email: String,
    password_hash: String,
    role: String,
    created_at: String,
}

#[derive(Serialize, Deserialize)]
struct Claims {
    sub: String,
    user_id: String,
    username: String,
    role: String,
    exp: usize,
}

// ==================== 响应结构体 ====================
#[derive(Serialize)]
struct ApiResponse<T> {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    message: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    data: Option<T>,
}

// ==================== 请求结构体 ====================
#[derive(Deserialize)]
struct LoginRequest {
    username: String,
    password: String,
}

// ==================== 初始化用户数据 ====================
fn init_users() -> HashMap<String, UserInfo> {
    let mut users = HashMap::new();
    
    // 管理员用户
    users.insert("admin".to_string(), UserInfo {
        id: "1".to_string(),
        username: "admin".to_string(),
        email: "admin@xiaosi.com".to_string(),
        password_hash: bcrypt::hash("admin123", bcrypt::DEFAULT_COST).unwrap(),
        role: "admin".to_string(),
        created_at: Utc::now().to_rfc3339(),
    });
    
    // 测试用户
    users.insert("zhangsan".to_string(), UserInfo {
        id: "2".to_string(),
        username: "zhangsan".to_string(),
        email: "zhangsan@xiaosi.com".to_string(),
        password_hash: bcrypt::hash("password", bcrypt::DEFAULT_COST).unwrap(),
        role: "user".to_string(),
        created_at: Utc::now().to_rfc3339(),
    });
    
    users
}

// ==================== API处理器 ====================

async fn login(
    data: web::Json<LoginRequest>,
    state: web::Data<AppState>,
) -> HttpResponse {
    let users = state.users.lock().unwrap();
    
    match users.get(&data.username) {
        Some(user) => {
            if bcrypt::verify(&data.password, &user.password_hash).unwrap_or(false) {
                let now = Utc::now().timestamp() as usize;
                let claims = Claims {
                    sub: user.id.clone(),
                    user_id: user.id.clone(),
                    username: user.username.clone(),
                    role: user.role.clone(),
                    exp: now + (24 * 60 * 60),
                };
                
                let token = encode(
                    &Header::default(),
                    &claims,
                    &EncodingKey::from_secret(b"xiaosi-nas-rust-secret-2024"),
                ).unwrap();
                
                HttpResponse::Ok().json(ApiResponse {
                    success: true,
                    message: None,
                    data: Some(serde_json::json!({
                        "token": token,
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "role": user.role,
                            "email": user.email
                        }
                    })),
                })
            } else {
                HttpResponse::Unauthorized().json(ApiResponse::<()> {
                    success: false,
                    message: Some("Invalid credentials".to_string()),
                    data: None,
                })
            }
        }
        None => {
            HttpResponse::Unauthorized().json(ApiResponse::<()> {
                success: false,
                message: Some("User not found".to_string()),
                data: None,
            })
        }
    }
}

async fn get_stats(state: web::Data<AppState>) -> HttpResponse {
    let users = state.users.lock().unwrap();
    
    HttpResponse::Ok().json(ApiResponse {
        success: true,
        message: None,
        data: Some(serde_json::json!({
            "storage": {
                "used": 2684354560u64,
                "total": 4294967296u64,
                "percentage": 62.5f64
            },
            "files": {
                "count": 1284i32,
                "recent": [
                    {"name": "项目报告.pdf", "user": "admin", "time": "5分钟前"},
                    {"name": "新用户注册", "user": "system", "time": "15分钟前"}
                ]
            },
            "users": {
                "total": users.len(),
                "online": 2i32
            }
        })),
    })
}

async fn get_files() -> HttpResponse {
    let files = vec![
        serde_json::json!({"id": "1", "name": "项目文档", "type": "folder", "icon": "📁", "size": 0}),
        serde_json::json!({"id": "2", "name": "照片备份", "type": "folder", "icon": "📁", "size": 0}),
        serde_json::json!({"id": "3", "name": "项目报告.pdf", "type": "file", "icon": "📄", "size": 2621440}),
        serde_json::json!({"id": "4", "name": "会议纪要.docx", "type": "file", "icon": "📝", "size": 159744}),
        serde_json::json!({"id": "5", "name": "数据表格.xlsx", "type": "file", "icon": "📊", "size": 911360}),
    ];
    
    HttpResponse::Ok().json(ApiResponse {
        success: true,
        message: None,
        data: Some(files),
    })
}

async fn get_users(state: web::Data<AppState>) -> HttpResponse {
    let users = state.users.lock().unwrap();
    let user_list: Vec<serde_json::Value> = users.values().map(|user| {
        serde_json::json!({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "storage_quota": 10737418240u64,
            "status": "online",
            "last_login": user.created_at
        })
    }).collect();
    
    HttpResponse::Ok().json(ApiResponse {
        success: true,
        message: None,
        data: Some(user_list),
    })
}

async fn get_settings() -> HttpResponse {
    HttpResponse::Ok().json(ApiResponse {
        success: true,
        message: None,
        data: Some(serde_json::json!({
            "general": {
                "system_name": "小思超级NAS",
                "timezone": "Asia/Shanghai",
                "language": "zh-CN",
                "theme": "dark"
            },
            "network": {
                "ip": "0.0.0.0",
                "port": 8080
            }
        })),
    })
}

// ==================== 静态文件服务 ====================
async fn serve_static(path: web::Path<String>) -> HttpResponse {
    let public_dir = PathBuf::from("../public");
    let file_path = public_dir.join(&*path);
    
    if file_path.exists() && file_path.is_file() {
        match fs::read(&file_path) {
            Ok(content) => {
                let content_type = get_content_type(&file_path);
                HttpResponse::Ok()
                    .content_type(content_type)
                    .body(content)
            }
            Err(_) => HttpResponse::NotFound().finish()
        }
    } else {
        let index_path = public_dir.join("index.html");
        if index_path.exists() {
            match fs::read(index_path) {
                Ok(content) => HttpResponse::Ok()
                    .content_type("text/html")
                    .body(content),
                Err(_) => HttpResponse::NotFound().finish()
            }
        } else {
            HttpResponse::NotFound().finish()
        }
    }
}

fn get_content_type(path: &PathBuf) -> &'static str {
    match path.extension().and_then(|e| e.to_str()) {
        Some("html") => "text/html; charset=utf-8",
        Some("css") => "text/css; charset=utf-8",
        Some("js") => "application/javascript; charset=utf-8",
        Some("json") => "application/json; charset=utf-8",
        Some("png") => "image/png",
        Some("jpg") | Some("jpeg") => "image/jpeg",
        _ => "application/octet-stream",
    }
}

// ==================== 主函数 ====================
#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("\n============================================");
    println!("   🚀 小思超级NAS (Rust版本) 已启动！");
    println!("============================================");
    println!("\n📡 访问地址：");
    println!("   本地访问：http://localhost:8080");
    println!("   局域网访问：http://<您的IP>:8080");
    println!("\n👤 默认登录：");
    println!("   用户名：admin");
    println!("   密码：admin123");
    println!("\n============================================\n");

    let app_state = web::Data::new(AppState {
        users: Mutex::new(init_users()),
    });

    HttpServer::new(move || {
        App::new()
            .app_data(app_state.clone())
            .wrap(Cors::permissive())
            .wrap(middleware::Logger::default("%a \"%r\" %s %b %D"))
            .service(web::resource("/api/auth/login").route(web::post().to(login)))
            .service(web::resource("/api/stats").route(web::get().to(get_stats)))
            .service(web::resource("/api/files").route(web::get().to(get_files)))
            .service(web::resource("/api/users").route(web::get().to(get_users)))
            .service(web::resource("/api/settings").route(web::get().to(get_settings)))
            .service(web::resource("/{path:.*}").route(web::get().to(serve_static)))
    })
    .bind("0.0.0.0:8080")?
    .workers(4)
    .run()
    .await
}
