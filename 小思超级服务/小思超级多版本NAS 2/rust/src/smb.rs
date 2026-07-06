use serde::{Deserialize, Serialize};
use std::sync::Arc;
use parking_lot::RwLock;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SmbShare {
    pub id: String,
    pub name: String,
    pub path: String,
    pub comment: String,
    pub read_only: bool,
    pub browseable: bool,
    pub guest_ok: bool,
    pub allowed_users: Vec<String>,
    pub created_at: DateTime<Utc>,
    pub is_active: bool,
}

#[derive(Debug, Deserialize)]
pub struct CreateSmbShareRequest {
    pub name: String,
    pub path: String,
    pub comment: Option<String>,
    pub read_only: bool,
    pub browseable: bool,
    pub guest_ok: bool,
    pub allowed_users: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateSmbShareRequest {
    pub name: Option<String>,
    pub path: Option<String>,
    pub comment: Option<String>,
    pub read_only: Option<bool>,
    pub browseable: Option<bool>,
    pub guest_ok: Option<bool>,
    pub allowed_users: Option<Vec<String>>,
    pub is_active: Option<bool>,
}

#[derive(Debug, Serialize)]
pub struct SmbStatus {
    pub service_running: bool,
    pub shares_count: usize,
    pub connections: Vec<SmbConnection>,
}

#[derive(Debug, Serialize)]
pub struct SmbConnection {
    pub share_name: String,
    pub user: String,
    pub client_ip: String,
    pub connected_at: DateTime<Utc>,
}

pub struct SmbManager {
    shares: Arc<RwLock<Vec<SmbShare>>>,
}

impl SmbManager {
    pub fn new() -> Self {
        Self {
            shares: Arc::new(RwLock::new(vec![])),
        }
    }

    pub fn create_share(&self, req: CreateSmbShareRequest) -> Result<SmbShare, String> {
        let mut shares = self.shares.write();
        
        if shares.iter().any(|s| s.name == req.name) {
            return Err("Share name already exists".to_string());
        }
        
        let share = SmbShare {
            id: uuid::Uuid::new_v4().to_string(),
            name: req.name,
            path: req.path,
            comment: req.comment.unwrap_or_default(),
            read_only: req.read_only,
            browseable: req.browseable,
            guest_ok: req.guest_ok,
            allowed_users: req.allowed_users,
            created_at: Utc::now(),
            is_active: true,
        };
        
        shares.push(share.clone());
        Ok(share)
    }

    pub fn get_share(&self, id: &str) -> Option<SmbShare> {
        self.shares.read()
            .iter()
            .find(|s| s.id == id)
            .cloned()
    }

    pub fn list_shares(&self) -> Vec<SmbShare> {
        self.shares.read().clone()
    }

    pub fn update_share(&self, id: &str, updates: UpdateSmbShareRequest) -> Result<SmbShare, String> {
        let mut shares = self.shares.write();
        
        if let Some(share) = shares.iter_mut().find(|s| s.id == id) {
            if let Some(name) = updates.name {
                if shares.iter().any(|s| s.name == name && s.id != id) {
                    return Err("Share name already exists".to_string());
                }
                share.name = name;
            }
            if let Some(path) = updates.path {
                share.path = path;
            }
            if let Some(comment) = updates.comment {
                share.comment = comment;
            }
            if let Some(read_only) = updates.read_only {
                share.read_only = read_only;
            }
            if let Some(browseable) = updates.browseable {
                share.browseable = browseable;
            }
            if let Some(guest_ok) = updates.guest_ok {
                share.guest_ok = guest_ok;
            }
            if let Some(allowed_users) = updates.allowed_users {
                share.allowed_users = allowed_users;
            }
            if let Some(is_active) = updates.is_active {
                share.is_active = is_active;
            }
            return Ok(share.clone());
        }
        
        Err("Share not found".to_string())
    }

    pub fn delete_share(&self, id: &str) -> Result<(), String> {
        let mut shares = self.shares.write();
        let len_before = shares.len();
        shares.retain(|s| s.id != id);
        
        if shares.len() < len_before {
            Ok(())
        } else {
            Err("Share not found".to_string())
        }
    }

    pub fn get_status(&self) -> SmbStatus {
        let shares = self.shares.read();
        SmbStatus {
            service_running: true,
            shares_count: shares.len(),
            connections: vec![], // Would be populated from actual SMB service
        }
    }

    pub fn export_config(&self) -> String {
        let shares = self.shares.read();
        let mut config = String::new();
        
        for share in shares.iter() {
            config.push_str(&format!(
                "[{}]\n   path = {}\n   comment = {}\n   read only = {}\n   browseable = {}\n   guest ok = {}\n",
                share.name,
                share.path,
                share.comment,
                share.read_only ? "yes" : "no",
                share.browseable ? "yes" : "no",
                share.guest_ok ? "yes" : "no"
            ));
            
            if !share.allowed_users.is_empty() {
                config.push_str(&format!("   valid users = {}\n", share.allowed_users.join(", ")));
            }
            config.push('\n');
        }
        
        config
    }
}