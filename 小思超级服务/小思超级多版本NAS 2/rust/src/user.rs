use std::sync::Arc;
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use sha2::{Sha256, Digest};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: String,
    pub username: String,
    pub password_hash: String,
    pub role: UserRole,
    pub quota_gb: u64,
    pub used_bytes: u64,
    pub created_at: DateTime<Utc>,
    pub last_login: Option<DateTime<Utc>>,
    pub is_active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum UserRole {
    Admin,
    User,
    Guest,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LoginRequest {
    pub username: String,
    pub password: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LoginResponse {
    pub token: String,
    pub user: User,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreateUserRequest {
    pub username: String,
    pub password: String,
    pub role: UserRole,
    pub quota_gb: u64,
}

pub struct UserManager {
    users: Arc<RwLock<Vec<User>>>,
}

impl UserManager {
    pub fn new() -> Self {
        Self {
            users: Arc::new(RwLock::new(vec![
                // Default admin user
                User {
                    id: Uuid::new_v4().to_string(),
                    username: "admin".to_string(),
                    password_hash: Self::hash_password("admin123"),
                    role: UserRole::Admin,
                    quota_gb: 100,
                    used_bytes: 0,
                    created_at: Utc::now(),
                    last_login: None,
                    is_active: true,
                },
            ])),
        }
    }

    pub fn login(&self, username: &str, password: &str) -> Option<LoginResponse> {
        let mut users = self.users.write();
        let password_hash = Self::hash_password(password);
        
        for user in users.iter_mut() {
            if user.username == username && user.password_hash == password_hash && user.is_active {
                user.last_login = Some(Utc::now());
                let token = Self::generate_token(&user.id);
                return Some(LoginResponse {
                    token,
                    user: user.clone(),
                });
            }
        }
        None
    }

    pub fn create_user(&self, req: CreateUserRequest) -> Result<User, String> {
        let mut users = self.users.write();
        
        if users.iter().any(|u| u.username == req.username) {
            return Err("Username already exists".to_string());
        }
        
        let user = User {
            id: Uuid::new_v4().to_string(),
            username: req.username,
            password_hash: Self::hash_password(&req.password),
            role: req.role,
            quota_gb: req.quota_gb,
            used_bytes: 0,
            created_at: Utc::now(),
            last_login: None,
            is_active: true,
        };
        
        users.push(user.clone());
        Ok(user)
    }

    pub fn get_user(&self, id: &str) -> Option<User> {
        self.users.read()
            .iter()
            .find(|u| u.id == id)
            .cloned()
    }

    pub fn get_user_by_username(&self, username: &str) -> Option<User> {
        self.users.read()
            .iter()
            .find(|u| u.username == username)
            .cloned()
    }

    pub fn list_users(&self) -> Vec<User> {
        self.users.read().clone()
    }

    pub fn update_user(&self, id: &str, updates: UserUpdate) -> Result<User, String> {
        let mut users = self.users.write();
        
        if let Some(user) = users.iter_mut().find(|u| u.id == id) {
            if let Some(username) = updates.username {
                if users.iter().any(|u| u.username == username && u.id != id) {
                    return Err("Username already exists".to_string());
                }
                user.username = username;
            }
            if let Some(password) = updates.password {
                user.password_hash = Self::hash_password(&password);
            }
            if let Some(role) = updates.role {
                user.role = role;
            }
            if let Some(quota_gb) = updates.quota_gb {
                user.quota_gb = quota_gb;
            }
            if let Some(is_active) = updates.is_active {
                user.is_active = is_active;
            }
            return Ok(user.clone());
        }
        
        Err("User not found".to_string())
    }

    pub fn delete_user(&self, id: &str) -> Result<(), String> {
        let mut users = self.users.write();
        let len_before = users.len();
        users.retain(|u| u.id != id);
        
        if users.len() < len_before {
            Ok(())
        } else {
            Err("User not found".to_string())
        }
    }

    pub fn update_used_storage(&self, id: &str, bytes: u64) {
        if let Some(user) = self.users.write().iter_mut().find(|u| u.id == id) {
            user.used_bytes = bytes;
        }
    }

    pub fn check_quota(&self, id: &str, additional_bytes: u64) -> bool {
        self.users.read()
            .iter()
            .find(|u| u.id == id)
            .map(|u| u.used_bytes + additional_bytes <= u.quota_gb * 1024 * 1024 * 1024)
            .unwrap_or(false)
    }

    fn hash_password(password: &str) -> String {
        let mut hasher = Sha256::new();
        hasher.update(password.as_bytes());
        format!("{:x}", hasher.finalize())
    }

    fn generate_token(user_id: &str) -> String {
        let timestamp = Utc::now().timestamp();
        let data = format!("{}:{}", user_id, timestamp);
        let mut hasher = Sha256::new();
        hasher.update(data.as_bytes());
        format!("{:x}", hasher.finalize())
    }
}

#[derive(Debug, Deserialize)]
pub struct UserUpdate {
    pub username: Option<String>,
    pub password: Option<String>,
    pub role: Option<UserRole>,
    pub quota_gb: Option<u64>,
    pub is_active: Option<bool>,
}