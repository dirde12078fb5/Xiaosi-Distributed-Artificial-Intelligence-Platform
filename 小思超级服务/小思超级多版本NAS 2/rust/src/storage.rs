use std::path::{Path, PathBuf};
use std::sync::Arc;
use parking_lot::RwLock;
use walkdir::WalkDir;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use sha2::{Sha256, Digest};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileInfo {
    pub name: String,
    pub path: String,
    pub size: u64,
    pub is_dir: bool,
    pub modified: DateTime<Utc>,
    pub hash: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StorageStats {
    pub total_size: u64,
    pub file_count: u64,
    pub dir_count: u64,
    pub available_space: u64,
}

pub struct StorageManager {
    base_path: PathBuf,
    max_storage_bytes: Arc<RwLock<u64>>,
}

impl StorageManager {
    pub fn new(base_path: String, max_storage_gb: u64) -> Self {
        let path = PathBuf::from(&base_path);
        if !path.exists() {
            std::fs::create_dir_all(&path).ok();
        }
        
        Self {
            base_path: path,
            max_storage_bytes: Arc::new(RwLock::new(max_storage_gb * 1024 * 1024 * 1024)),
        }
    }

    pub fn list_files(&self, relative_path: &str) -> Result<Vec<FileInfo>, String> {
        let full_path = self.base_path.join(relative_path.trim_start_matches('/'));
        
        if !full_path.exists() {
            return Ok(vec![]);
        }

        let mut files = Vec::new();
        
        for entry in std::fs::read_dir(&full_path)
            .map_err(|e| format!("Failed to read directory: {}", e))? 
        {
            let entry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
            let path = entry.path();
            let metadata = entry.metadata()
                .map_err(|e| format!("Failed to read metadata: {}", e))?;
            
            let relative = path.strip_prefix(&self.base_path)
                .unwrap_or(&path)
                .to_string_lossy()
                .to_string();
            
            files.push(FileInfo {
                name: entry.file_name().to_string_lossy().to_string(),
                path: relative,
                size: metadata.len(),
                is_dir: metadata.is_dir(),
                modified: metadata.modified()
                    .map(|t| DateTime::from(t))
                    .unwrap_or_else(|_| Utc::now()),
                hash: None,
            });
        }

        Ok(files)
    }

    pub fn get_file(&self, relative_path: &str) -> Result<Vec<u8>, String> {
        let full_path = self.base_path.join(relative_path.trim_start_matches('/'));
        
        if !full_path.exists() {
            return Err("File not found".to_string());
        }
        
        std::fs::read(&full_path)
            .map_err(|e| format!("Failed to read file: {}", e))
    }

    pub fn save_file(&self, relative_path: &str, content: &[u8]) -> Result<FileInfo, String> {
        let full_path = self.base_path.join(relative_path.trim_start_matches('/'));
        
        if let Some(parent) = full_path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("Failed to create directories: {}", e))?;
        }
        
        std::fs::write(&full_path, content)
            .map_err(|e| format!("Failed to write file: {}", e))?;
        
        let hash = self.calculate_hash(content);
        
        Ok(FileInfo {
            name: full_path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown")
                .to_string(),
            path: relative_path.to_string(),
            size: content.len() as u64,
            is_dir: false,
            modified: Utc::now(),
            hash: Some(hash),
        })
    }

    pub fn delete_file(&self, relative_path: &str) -> Result<(), String> {
        let full_path = self.base_path.join(relative_path.trim_start_matches('/'));
        
        if !full_path.exists() {
            return Err("File not found".to_string());
        }
        
        if full_path.is_dir() {
            std::fs::remove_dir_all(&full_path)
                .map_err(|e| format!("Failed to remove directory: {}", e))?;
        } else {
            std::fs::remove_file(&full_path)
                .map_err(|e| format!("Failed to remove file: {}", e))?;
        }
        
        Ok(())
    }

    pub fn create_directory(&self, relative_path: &str) -> Result<FileInfo, String> {
        let full_path = self.base_path.join(relative_path.trim_start_matches('/'));
        
        std::fs::create_dir_all(&full_path)
            .map_err(|e| format!("Failed to create directory: {}", e))?;
        
        Ok(FileInfo {
            name: full_path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown")
                .to_string(),
            path: relative_path.to_string(),
            size: 0,
            is_dir: true,
            modified: Utc::now(),
            hash: None,
        })
    }

    pub fn move_file(&self, from: &str, to: &str) -> Result<FileInfo, String> {
        let from_path = self.base_path.join(from.trim_start_matches('/'));
        let to_path = self.base_path.join(to.trim_start_matches('/'));
        
        if !from_path.exists() {
            return Err("Source file not found".to_string());
        }
        
        if let Some(parent) = to_path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("Failed to create target directory: {}", e))?;
        }
        
        std::fs::rename(&from_path, &to_path)
            .map_err(|e| format!("Failed to move file: {}", e))?;
        
        let metadata = std::fs::metadata(&to_path)
            .map_err(|e| format!("Failed to read metadata: {}", e))?;
        
        Ok(FileInfo {
            name: to_path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown")
                .to_string(),
            path: to.to_string(),
            size: metadata.len(),
            is_dir: metadata.is_dir(),
            modified: Utc::now(),
            hash: None,
        })
    }

    pub fn copy_file(&self, from: &str, to: &str) -> Result<FileInfo, String> {
        let from_path = self.base_path.join(from.trim_start_matches('/'));
        let to_path = self.base_path.join(to.trim_start_matches('/'));
        
        if !from_path.exists() {
            return Err("Source file not found".to_string());
        }
        
        if let Some(parent) = to_path.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|e| format!("Failed to create target directory: {}", e))?;
        }
        
        std::fs::copy(&from_path, &to_path)
            .map_err(|e| format!("Failed to copy file: {}", e))?;
        
        let metadata = std::fs::metadata(&to_path)
            .map_err(|e| format!("Failed to read metadata: {}", e))?;
        
        Ok(FileInfo {
            name: to_path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown")
                .to_string(),
            path: to.to_string(),
            size: metadata.len(),
            is_dir: metadata.is_dir(),
            modified: Utc::now(),
            hash: None,
        })
    }

    pub fn get_stats(&self) -> Result<StorageStats, String> {
        let mut total_size = 0u64;
        let mut file_count = 0u64;
        let mut dir_count = 0u64;

        for entry in WalkDir::new(&self.base_path)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            if entry.file_type().is_file() {
                file_count += 1;
                total_size += entry.metadata()
                    .map(|m| m.len())
                    .unwrap_or(0);
            } else if entry.file_type().is_dir() {
                dir_count += 1;
            }
        }

        let available = self.max_storage_bytes.read().saturating_sub(total_size);

        Ok(StorageStats {
            total_size,
            file_count,
            dir_count,
            available_space: available,
        })
    }

    fn calculate_hash(&self, content: &[u8]) -> String {
        let mut hasher = Sha256::new();
        hasher.update(content);
        format!("{:x}", hasher.finalize())
    }
}