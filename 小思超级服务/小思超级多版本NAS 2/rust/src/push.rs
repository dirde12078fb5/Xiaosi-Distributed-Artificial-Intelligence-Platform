use serde::{Deserialize, Serialize};
use std::sync::Arc;
use parking_lot::RwLock;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PushConfig {
    pub enabled: bool,
    pub webhook_url: Option<String>,
    pub email_recipients: Vec<String>,
    pub notify_on_upload: bool,
    pub notify_on_delete: bool,
    pub notify_on_error: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PushNotification {
    pub id: String,
    pub event_type: PushEventType,
    pub message: String,
    pub details: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub sent: bool,
    pub error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PushEventType {
    FileUploaded,
    FileDeleted,
    FileModified,
    UserCreated,
    UserDeleted,
    ShareCreated,
    ShareDeleted,
    Error,
    StorageWarning,
    QuotaExceeded,
}

#[derive(Debug, Deserialize)]
pub struct SendNotificationRequest {
    pub event_type: PushEventType,
    pub message: String,
    pub details: serde_json::Value,
    pub recipients: Option<Vec<String>>,
}

pub struct PushManager {
    config: Arc<RwLock<PushConfig>>,
    notifications: Arc<RwLock<Vec<PushNotification>>>,
}

impl PushManager {
    pub fn new(config: PushConfig) -> Self {
        Self {
            config: Arc::new(RwLock::new(config)),
            notifications: Arc::new(RwLock::new(vec![])),
        }
    }

    pub fn send_notification(&self, req: SendNotificationRequest) -> Result<PushNotification, String> {
        let config = self.config.read();
        
        if !config.enabled {
            return Err("Push notifications are disabled".to_string());
        }
        
        let notification = PushNotification {
            id: uuid::Uuid::new_v4().to_string(),
            event_type: req.event_type,
            message: req.message.clone(),
            details: req.details,
            created_at: Utc::now(),
            sent: false,
            error: None,
        };
        
        // Try to send webhook
        let mut notification = notification;
        if let Some(ref webhook_url) = config.webhook_url {
            match self.send_webhook(webhook_url, &notification) {
                Ok(_) => {
                    notification.sent = true;
                }
                Err(e) => {
                    notification.error = Some(e);
                }
            }
        }
        
        self.notifications.write().push(notification.clone());
        Ok(notification)
    }

    fn send_webhook(&self, url: &str, notification: &PushNotification) -> Result<(), String> {
        let client = reqwest::blocking::Client::new();
        let body = serde_json::to_string(notification)
            .map_err(|e| format!("Failed to serialize notification: {}", e))?;
        
        client.post(url)
            .header("Content-Type", "application/json")
            .body(body)
            .send()
            .map_err(|e| format!("Failed to send webhook: {}", e))?;
        
        Ok(())
    }

    pub fn get_config(&self) -> PushConfig {
        self.config.read().clone()
    }

    pub fn update_config(&self, config: PushConfig) {
        *self.config.write() = config;
    }

    pub fn list_notifications(&self) -> Vec<PushNotification> {
        self.notifications.read().clone()
    }

    pub fn get_notification(&self, id: &str) -> Option<PushNotification> {
        self.notifications.read()
            .iter()
            .find(|n| n.id == id)
            .cloned()
    }

    pub fn clear_notifications(&self) {
        self.notifications.write().clear();
    }

    pub fn notify_upload(&self, filename: &str, user: &str, size: u64) {
        let config = self.config.read();
        if config.enabled && config.notify_on_upload {
            let _ = self.send_notification(SendNotificationRequest {
                event_type: PushEventType::FileUploaded,
                message: format!("File '{}' uploaded by {}", filename, user),
                details: serde_json::json!({
                    "filename": filename,
                    "user": user,
                    "size": size,
                }),
                recipients: Some(config.email_recipients.clone()),
            });
        }
    }

    pub fn notify_delete(&self, filename: &str, user: &str) {
        let config = self.config.read();
        if config.enabled && config.notify_on_delete {
            let _ = self.send_notification(SendNotificationRequest {
                event_type: PushEventType::FileDeleted,
                message: format!("File '{}' deleted by {}", filename, user),
                details: serde_json::json!({
                    "filename": filename,
                    "user": user,
                }),
                recipients: Some(config.email_recipients.clone()),
            });
        }
    }

    pub fn notify_error(&self, error_message: &str, context: &str) {
        let config = self.config.read();
        if config.enabled && config.notify_on_error {
            let _ = self.send_notification(SendNotificationRequest {
                event_type: PushEventType::Error,
                message: error_message.to_string(),
                details: serde_json::json!({
                    "context": context,
                    "error": error_message,
                }),
                recipients: Some(config.email_recipients.clone()),
            });
        }
    }

    pub fn notify_storage_warning(&self, used_percent: f64, available_gb: u64) {
        let config = self.config.read();
        if config.enabled {
            let _ = self.send_notification(SendNotificationRequest {
                event_type: PushEventType::StorageWarning,
                message: format!("Storage usage at {:.1}%", used_percent),
                details: serde_json::json!({
                    "used_percent": used_percent,
                    "available_gb": available_gb,
                }),
                recipients: Some(config.email_recipients.clone()),
            });
        }
    }

    pub fn notify_quota_exceeded(&self, user: &str, quota_gb: u64) {
        let config = self.config.read();
        if config.enabled {
            let _ = self.send_notification(SendNotificationRequest {
                event_type: PushEventType::QuotaExceeded,
                message: format!("User {} exceeded quota of {}GB", user, quota_gb),
                details: serde_json::json!({
                    "user": user,
                    "quota_gb": quota_gb,
                }),
                recipients: Some(config.email_recipients.clone()),
            });
        }
    }
}