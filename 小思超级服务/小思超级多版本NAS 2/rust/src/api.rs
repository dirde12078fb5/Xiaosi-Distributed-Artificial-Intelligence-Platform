use actix_web::{web, HttpResponse, HttpRequest};
use serde::{Deserialize, Serialize};
use crate::config::ConfigManager;
use crate::storage::{StorageManager, FileInfo, StorageStats};
use crate::user::{UserManager, User, UserRole, CreateUserRequest, LoginRequest, LoginResponse, UserUpdate};
use crate::smb::{SmbManager, CreateSmbShareRequest, UpdateSmbShareRequest, SmbShare};
use crate::push::{PushManager, PushConfig, PushEventType, SendNotificationRequest};
use crate::i18n::I18nManager;

#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub message: String,
    pub data: Option<T>,
}

impl<T: Serialize> ApiResponse<T> {
    pub fn success(data: T, message: &str) -> Self {
        Self {
            success: true,
            message: message.to_string(),
            data: Some(data),
        }
    }

    pub fn error(message: &str) -> Self {
        Self {
            success: false,
            message: message.to_string(),
            data: None,
        }
    }
}

pub struct AppState {
    pub config: ConfigManager,
    pub storage: StorageManager,
    pub users: UserManager,
    pub smb: SmbManager,
    pub push: PushManager,
    pub i18n: I18nManager,
}

// ==================== 文件API ====================

#[derive(Deserialize)]
pub struct ListFilesQuery {
    pub path: Option<String>,
}

pub async fn list_files(
    state: web::Data<AppState>,
    query: web::Query<ListFilesQuery>,
) -> HttpResponse {
    let path = query.path.as_deref().unwrap_or("");
    match state.storage.list_files(path) {
        Ok(files) => HttpResponse::Ok().json(ApiResponse::success(files, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

#[derive(Deserialize)]
pub struct FilePath {
    pub path: String,
}

pub async fn get_file(
    state: web::Data<AppState>,
    path: web::Query<FilePath>,
) -> HttpResponse {
    match state.storage.get_file(&path.path) {
        Ok(content) => HttpResponse::Ok()
            .content_type("application/octet-stream")
            .body(content),
        Err(e) => HttpResponse::NotFound().json(ApiResponse::<()>::error(&e)),
    }
}

pub async fn upload_file(
    state: web::Data<AppState>,
    path: web::Query<FilePath>,
    body: web::Bytes,
) -> HttpResponse {
    match state.storage.save_file(&path.path, &body) {
        Ok(info) => {
            state.push.notify_upload(&info.name, "system", info.size);
            HttpResponse::Ok().json(ApiResponse::success(info, &state.i18n.t("upload_success")))
        }
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

pub async fn delete_file(
    state: web::Data<AppState>,
    path: web::Query<FilePath>,
) -> HttpResponse {
    match state.storage.delete_file(&path.path) {
        Ok(_) => {
            state.push.notify_delete(&path.path, "system");
            HttpResponse::Ok().json(ApiResponse::success(true, &state.i18n.t("delete_success")))
        }
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

#[derive(Deserialize)]
pub struct CreateDirRequest {
    pub path: String,
}

pub async fn create_directory(
    state: web::Data<AppState>,
    body: web::Json<CreateDirRequest>,
) -> HttpResponse {
    match state.storage.create_directory(&body.path) {
        Ok(info) => HttpResponse::Ok().json(ApiResponse::success(info, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

#[derive(Deserialize)]
pub struct MoveRequest {
    pub from: String,
    pub to: String,
}

pub async fn move_file(
    state: web::Data<AppState>,
    body: web::Json<MoveRequest>,
) -> HttpResponse {
    match state.storage.move_file(&body.from, &body.to) {
        Ok(info) => HttpResponse::Ok().json(ApiResponse::success(info, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

#[derive(Deserialize)]
pub struct CopyRequest {
    pub from: String,
    pub to: String,
}

pub async fn copy_file(
    state: web::Data<AppState>,
    body: web::Json<CopyRequest>,
) -> HttpResponse {
    match state.storage.copy_file(&body.from, &body.to) {
        Ok(info) => HttpResponse::Ok().json(ApiResponse::success(info, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

pub async fn get_storage_stats(state: web::Data<AppState>) -> HttpResponse {
    match state.storage.get_stats() {
        Ok(stats) => HttpResponse::Ok().json(ApiResponse::success(stats, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

// ==================== 用户API ====================

pub async fn login(
    state: web::Data<AppState>,
    body: web::Json<LoginRequest>,
) -> HttpResponse {
    match state.users.login(&body.username, &body.password) {
        Some(response) => HttpResponse::Ok().json(ApiResponse::success(response, &state.i18n.t("api_success"))),
        None => HttpResponse::Unauthorized().json(ApiResponse::<()>::error(&state.i18n.t("unauthorized"))),
    }
}

pub async fn list_users(state: web::Data<AppState>) -> HttpResponse {
    let users = state.users.list_users();
    HttpResponse::Ok().json(ApiResponse::success(users, &state.i18n.t("api_success")))
}

pub async fn get_user(
    state: web::Data<AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    match state.users.get_user(&path) {
        Some(user) => HttpResponse::Ok().json(ApiResponse::success(user, &state.i18n.t("api_success"))),
        None => HttpResponse::NotFound().json(ApiResponse::<()>::error(&state.i18n.t("user_not_found"))),
    }
}

pub async fn create_user(
    state: web::Data<AppState>,
    body: web::Json<CreateUserRequest>,
) -> HttpResponse {
    match state.users.create_user(body.into_inner()) {
        Ok(user) => HttpResponse::Ok().json(ApiResponse::success(user, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

pub async fn update_user(
    state: web::Data<AppState>,
    path: web::Path<String>,
    body: web::Json<UserUpdate>,
) -> HttpResponse {
    match state.users.update_user(&path, body.into_inner()) {
        Ok(user) => HttpResponse::Ok().json(ApiResponse::success(user, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

pub async fn delete_user(
    state: web::Data<AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    match state.users.delete_user(&path) {
        Ok(_) => HttpResponse::Ok().json(ApiResponse::success(true, &state.i18n.t("delete_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

// ==================== SMB共享API ====================

pub async fn list_shares(state: web::Data<AppState>) -> HttpResponse {
    let shares = state.smb.list_shares();
    HttpResponse::Ok().json(ApiResponse::success(shares, &state.i18n.t("api_success")))
}

pub async fn get_share(
    state: web::Data<AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    match state.smb.get_share(&path) {
        Some(share) => HttpResponse::Ok().json(ApiResponse::success(share, &state.i18n.t("api_success"))),
        None => HttpResponse::NotFound().json(ApiResponse::<()>::error(&state.i18n.t("share_not_found"))),
    }
}

pub async fn create_share(
    state: web::Data<AppState>,
    body: web::Json<CreateSmbShareRequest>,
) -> HttpResponse {
    match state.smb.create_share(body.into_inner()) {
        Ok(share) => HttpResponse::Ok().json(ApiResponse::success(share, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

pub async fn update_share(
    state: web::Data<AppState>,
    path: web::Path<String>,
    body: web::Json<UpdateSmbShareRequest>,
) -> HttpResponse {
    match state.smb.update_share(&path, body.into_inner()) {
        Ok(share) => HttpResponse::Ok().json(ApiResponse::success(share, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

pub async fn delete_share(
    state: web::Data<AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    match state.smb.delete_share(&path) {
        Ok(_) => HttpResponse::Ok().json(ApiResponse::success(true, &state.i18n.t("delete_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

pub async fn get_smb_status(state: web::Data<AppState>) -> HttpResponse {
    let status = state.smb.get_status();
    HttpResponse::Ok().json(ApiResponse::success(status, &state.i18n.t("api_success")))
}

pub async fn export_smb_config(state: web::Data<AppState>) -> HttpResponse {
    let config = state.smb.export_config();
    HttpResponse::Ok()
        .content_type("text/plain")
        .body(config)
}

// ==================== 推送通知API ====================

#[derive(Deserialize)]
pub struct NotificationRequest {
    pub event_type: PushEventType,
    pub message: String,
    pub details: serde_json::Value,
    pub recipients: Option<Vec<String>>,
}

pub async fn send_notification(
    state: web::Data<AppState>,
    body: web::Json<NotificationRequest>,
) -> HttpResponse {
    match state.push.send_notification(SendNotificationRequest {
        event_type: body.event_type.clone(),
        message: body.message.clone(),
        details: body.details.clone(),
        recipients: body.recipients.clone(),
    }) {
        Ok(notification) => HttpResponse::Ok().json(ApiResponse::success(notification, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

pub async fn list_notifications(state: web::Data<AppState>) -> HttpResponse {
    let notifications = state.push.list_notifications();
    HttpResponse::Ok().json(ApiResponse::success(notifications, &state.i18n.t("api_success")))
}

pub async fn update_push_config(
    state: web::Data<AppState>,
    body: web::Json<PushConfig>,
) -> HttpResponse {
    state.push.update_config(body.into_inner());
    HttpResponse::Ok().json(ApiResponse::success(true, &state.i18n.t("api_success")))
}

pub async fn get_push_config(state: web::Data<AppState>) -> HttpResponse {
    let config = state.push.get_config();
    HttpResponse::Ok().json(ApiResponse::success(config, &state.i18n.t("api_success")))
}

// ==================== 配置API ====================

pub async fn get_config(state: web::Data<AppState>) -> HttpResponse {
    let config = state.config.get_config();
    HttpResponse::Ok().json(ApiResponse::success(config, &state.i18n.t("api_success")))
}

pub async fn update_config(
    state: web::Data<AppState>,
    body: web::Json<crate::config::NasConfig>,
) -> HttpResponse {
    match state.config.update_config(body.into_inner()) {
        Ok(_) => HttpResponse::Ok().json(ApiResponse::success(true, &state.i18n.t("api_success"))),
        Err(e) => HttpResponse::BadRequest().json(ApiResponse::<()>::error(&e)),
    }
}

// ==================== 国际化API ====================

#[derive(Deserialize)]
pub struct LanguageQuery {
    pub lang: Option<String>,
}

pub async fn get_translations(
    state: web::Data<AppState>,
    query: web::Query<LanguageQuery>,
) -> HttpResponse {
    let lang = query.lang.as_deref().unwrap_or(&state.i18n.get_language());
    let translations = state.i18n.get_translations(lang);
    HttpResponse::Ok().json(ApiResponse::success(translations, &state.i18n.t("api_success")))
}

pub async fn get_supported_languages(state: web::Data<AppState>) -> HttpResponse {
    let languages = state.i18n.get_supported_languages();
    HttpResponse::Ok().json(ApiResponse::success(languages, &state.i18n.t("api_success")))
}

pub async fn set_language(
    state: web::Data<AppState>,
    body: web::Json<LanguageQuery>,
) -> HttpResponse {
    if let Some(lang) = &body.lang {
        state.i18n.set_language(lang);
        HttpResponse::Ok().json(ApiResponse::success(true, &state.i18n.t("api_success")))
    } else {
        HttpResponse::BadRequest().json(ApiResponse::<()>::error(&state.i18n.t("invalid_params")))
    }
}

// ==================== 系统API ====================

pub async fn health_check() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "healthy",
        "timestamp": chrono::Utc::now().to_rfc3339()
    }))
}

pub async fn get_system_info(state: web::Data<AppState>) -> HttpResponse {
    let stats = state.storage.get_stats().ok();
    HttpResponse::Ok().json(ApiResponse::success(serde_json::json!({
        "version": env!("CARGO_PKG_VERSION"),
        "uptime": chrono::Utc::now().to_rfc3339(),
        "storage_stats": stats,
    }), &state.i18n.t("api_success")))
}