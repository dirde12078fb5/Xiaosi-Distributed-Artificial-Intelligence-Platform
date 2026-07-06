mod config;
mod storage;
mod user;
mod smb;
mod push;
mod i18n;
mod api;

use actix_web::{web, App, HttpServer};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // 初始化日志
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
    
    log::info!("正在初始化NAS服务...");
    
    // 加载配置
    let config_manager = config::ConfigManager::new();
    let config = config_manager.get_config();
    
    log::info!("配置加载完成 - 端口: {}, 语言: {}", config.port, config.language);
    
    let port = config.port;
    let host = config.host.clone();
    let storage_path = config.storage_path.clone();
    let max_storage_gb = config.max_storage_gb;
    let push_config = config.push_config.clone();
    let language = config.language.clone();
    
    log::info!("NAS服务启动于 {}:{}", host, port);
    log::info!("支持的28种语言: 中文、英文、日语、韩语等");
    log::info!("API端点:");
    log::info!("  - 文件管理: /api/files/*");
    log::info!("  - 用户管理: /api/users/*");
    log::info!("  - SMB共享: /api/smb/*");
    log::info!("  - 推送通知: /api/push/*");
    log::info!("  - 配置管理: /api/config/*");
    log::info!("  - 国际化: /api/i18n/*");
    
    HttpServer::new(|| {
        let config_manager = config::ConfigManager::new();
        let cfg = config_manager.get_config();
        
        let i18n = i18n::I18nManager::new();
        i18n.set_language(&cfg.language);
        
        App::new()
            .app_data(web::Data::new(api::AppState {
                config: config_manager,
                storage: storage::StorageManager::new(cfg.storage_path.clone(), cfg.max_storage_gb),
                users: user::UserManager::new(),
                smb: smb::SmbManager::new(),
                push: push::PushManager::new(cfg.push_config.clone()),
                i18n,
            }))
            // 系统API
            .route("/health", web::get().to(api::health_check))
            .route("/api/system", web::get().to(api::get_system_info))
            
            // 文件管理API
            .route("/api/files", web::get().to(api::list_files))
            .route("/api/files/download", web::get().to(api::get_file))
            .route("/api/files/upload", web::post().to(api::upload_file))
            .route("/api/files/delete", web::delete().to(api::delete_file))
            .route("/api/files/mkdir", web::post().to(api::create_directory))
            .route("/api/files/move", web::post().to(api::move_file))
            .route("/api/files/copy", web::post().to(api::copy_file))
            .route("/api/files/stats", web::get().to(api::get_storage_stats))
            
            // 用户管理API
            .route("/api/users/login", web::post().to(api::login))
            .route("/api/users", web::get().to(api::list_users))
            .route("/api/users", web::post().to(api::create_user))
            .route("/api/users/{id}", web::get().to(api::get_user))
            .route("/api/users/{id}", web::put().to(api::update_user))
            .route("/api/users/{id}", web::delete().to(api::delete_user))
            
            // SMB共享API
            .route("/api/smb", web::get().to(api::list_shares))
            .route("/api/smb", web::post().to(api::create_share))
            .route("/api/smb/{id}", web::get().to(api::get_share))
            .route("/api/smb/{id}", web::put().to(api::update_share))
            .route("/api/smb/{id}", web::delete().to(api::delete_share))
            .route("/api/smb/status", web::get().to(api::get_smb_status))
            .route("/api/smb/config", web::get().to(api::export_smb_config))
            
            // 推送通知API
            .route("/api/push", web::post().to(api::send_notification))
            .route("/api/push", web::get().to(api::list_notifications))
            .route("/api/push/config", web::get().to(api::get_push_config))
            .route("/api/push/config", web::put().to(api::update_push_config))
            
            // 配置API
            .route("/api/config", web::get().to(api::get_config))
            .route("/api/config", web::put().to(api::update_config))
            
            // 国际化API
            .route("/api/i18n/translations", web::get().to(api::get_translations))
            .route("/api/i18n/languages", web::get().to(api::get_supported_languages))
            .route("/api/i18n/language", web::post().to(api::set_language))
    })
    .bind((host.as_str(), port))?
    .run()
    .await
}