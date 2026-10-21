use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Arc;
use parking_lot::RwLock;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NasConfig {
    pub port: u16,
    pub host: String,
    pub storage_path: String,
    pub max_storage_gb: u64,
    pub users: Vec<UserConfig>,
    pub smb_shares: Vec<SmbShareConfig>,
    pub push_config: PushConfig,
    pub language: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserConfig {
    pub id: String,
    pub username: String,
    pub password_hash: String,
    pub role: UserRole,
    pub quota_gb: u64,
    pub created_at: DateTime<Utc>,
    pub is_active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum UserRole {
    Admin,
    User,
    Guest,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmbShareConfig {
    pub name: String,
    pub path: String,
    pub read_only: bool,
    pub allowed_users: Vec<String>,
    pub browseable: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PushConfig {
    pub enabled: bool,
    pub webhook_url: Option<String>,
    pub email_recipients: Vec<String>,
    pub notify_on_upload: bool,
    pub notify_on_delete: bool,
    pub notify_on_error: bool,
}

impl Default for NasConfig {
    fn default() -> Self {
        Self {
            port: 8084,
            host: "0.0.0.0".to_string(),
            storage_path: "./storage".to_string(),
            max_storage_gb: 1000,
            users: vec![],
            smb_shares: vec![],
            push_config: PushConfig::default(),
            language: "zh-CN".to_string(),
        }
    }
}

impl Default for PushConfig {
    fn default() -> Self {
        Self {
            enabled: false,
            webhook_url: None,
            email_recipients: vec![],
            notify_on_upload: true,
            notify_on_delete: true,
            notify_on_error: true,
        }
    }
}

pub struct ConfigManager {
    config: Arc<RwLock<NasConfig>>,
    config_path: PathBuf,
}

impl ConfigManager {
    pub fn new() -> Self {
        let config_path = PathBuf::from("../config/config.json");
        let config = Self::load_config(&config_path).unwrap_or_else(|_| {
            log::warn!("Config file not found, using defaults");
            NasConfig::default()
        });
        
        Self {
            config: Arc::new(RwLock::new(config)),
            config_path,
        }
    }

    fn load_config(path: &PathBuf) -> Result<NasConfig, String> {
        if !path.exists() {
            return Err("Config file not found".to_string());
        }
        let content = std::fs::read_to_string(path)
            .map_err(|e| format!("Failed to read config: {}", e))?;
        serde_json::from_str(&content)
            .map_err(|e| format!("Failed to parse config: {}", e))
    }

    pub fn get_config(&self) -> NasConfig {
        self.config.read().clone()
    }

    pub fn update_config(&self, new_config: NasConfig) -> Result<(), String> {
        let content = serde_json::to_string_pretty(&new_config)
            .map_err(|e| format!("Failed to serialize config: {}", e))?;
        
        if let Some(parent) = self.config_path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("Failed to create config dir: {}", e))?;
        }
        
        std::fs::write(&self.config_path, &content)
            .map_err(|e| format!("Failed to write config: {}", e))?;
        
        *self.config.write() = new_config;
        Ok(())
    }

    pub fn get_port(&self) -> u16 {
        self.config.read().port
    }

    pub fn get_language(&self) -> String {
        self.config.read().language.clone()
    }
}