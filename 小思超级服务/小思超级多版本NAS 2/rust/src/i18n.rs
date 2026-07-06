use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use parking_lot::RwLock;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Translation {
    pub key: String,
    pub translations: HashMap<String, String>,
}

pub struct I18nManager {
    translations: Arc<RwLock<HashMap<String, HashMap<String, String>>>>,
    current_language: Arc<RwLock<String>>,
}

// 28种语言支持
pub const SUPPORTED_LANGUAGES: &[(&str, &str)] = &[
    ("zh-CN", "简体中文"),
    ("zh-TW", "繁體中文"),
    ("en-US", "English (US)"),
    ("en-GB", "English (UK)"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("vi", "Tiếng Việt"),
    ("th", "ไทย"),
    ("id", "Bahasa Indonesia"),
    ("ms", "Bahasa Melayu"),
    ("fil", "Filipino"),
    ("es-ES", "Español (España)"),
    ("es-MX", "Español (México)"),
    ("pt-BR", "Português (Brasil)"),
    ("pt-PT", "Português (Portugal)"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
    ("ru", "Русский"),
    ("ar", "العربية"),
    ("hi", "हिन्दी"),
    ("bn", "বাংলা"),
    ("tr", "Türkçe"),
    ("pl", "Polski"),
    ("nl", "Nederlands"),
    ("sv", "Svenska"),
    ("da", "Dansk"),
    ("fi", "Suomi"),
];

impl I18nManager {
    pub fn new() -> Self {
        let mut translations = HashMap::new();
        
        // 初始化所有翻译
        Self::init_translations(&mut translations);
        
        Self {
            translations: Arc::new(RwLock::new(translations)),
            current_language: Arc::new(RwLock::new("zh-CN".to_string())),
        }
    }

    fn init_translations(translations: &mut HashMap<String, HashMap<String, String>>) {
        // 常用键值对翻译
        let keys = vec![
            // 通用
            ("welcome", "欢迎使用NAS服务", "Welcome to NAS Service"),
            ("login", "登录", "Login"),
            ("logout", "退出", "Logout"),
            ("username", "用户名", "Username"),
            ("password", "密码", "Password"),
            ("submit", "提交", "Submit"),
            ("cancel", "取消", "Cancel"),
            ("save", "保存", "Save"),
            ("delete", "删除", "Delete"),
            ("edit", "编辑", "Edit"),
            ("create", "创建", "Create"),
            ("search", "搜索", "Search"),
            ("upload", "上传", "Upload"),
            ("download", "下载", "Download"),
            ("copy", "复制", "Copy"),
            ("move", "移动", "Move"),
            ("rename", "重命名", "Rename"),
            ("folder", "文件夹", "Folder"),
            ("file", "文件", "File"),
            ("size", "大小", "Size"),
            ("date", "日期", "Date"),
            ("name", "名称", "Name"),
            ("type", "类型", "Type"),
            ("action", "操作", "Action"),
            ("status", "状态", "Status"),
            ("success", "成功", "Success"),
            ("error", "错误", "Error"),
            ("warning", "警告", "Warning"),
            ("info", "信息", "Info"),
            
            // 文件管理
            ("file_list", "文件列表", "File List"),
            ("file_upload", "文件上传", "File Upload"),
            ("file_delete", "文件删除", "File Delete"),
            ("file_download", "文件下载", "File Download"),
            ("create_folder", "创建文件夹", "Create Folder"),
            ("delete_confirm", "确认删除", "Confirm Delete"),
            ("delete_confirm_msg", "确定要删除此文件吗?", "Are you sure you want to delete this file?"),
            ("upload_success", "上传成功", "Upload Successful"),
            ("upload_failed", "上传失败", "Upload Failed"),
            ("download_success", "下载成功", "Download Successful"),
            ("download_failed", "下载失败", "Download Failed"),
            ("delete_success", "删除成功", "Delete Successful"),
            ("delete_failed", "删除失败", "Delete Failed"),
            
            // 用户管理
            ("user_management", "用户管理", "User Management"),
            ("create_user", "创建用户", "Create User"),
            ("edit_user", "编辑用户", "Edit User"),
            ("delete_user", "删除用户", "Delete User"),
            ("user_role", "用户角色", "User Role"),
            ("admin", "管理员", "Admin"),
            ("user", "用户", "User"),
            ("guest", "访客", "Guest"),
            ("quota", "配额", "Quota"),
            ("used_space", "已用空间", "Used Space"),
            ("available_space", "可用空间", "Available Space"),
            
            // SMB共享
            ("smb_shares", "SMB共享", "SMB Shares"),
            ("create_share", "创建共享", "Create Share"),
            ("edit_share", "编辑共享", "Edit Share"),
            ("delete_share", "删除共享", "Delete Share"),
            ("share_name", "共享名称", "Share Name"),
            ("share_path", "共享路径", "Share Path"),
            ("read_only", "只读", "Read Only"),
            ("browseable", "可浏览", "Browseable"),
            ("guest_access", "访客访问", "Guest Access"),
            
            // 设置
            ("settings", "设置", "Settings"),
            ("general", "常规", "General"),
            ("storage", "存储", "Storage"),
            ("network", "网络", "Network"),
            ("security", "安全", "Security"),
            ("language", "语言", "Language"),
            ("theme", "主题", "Theme"),
            ("dark_mode", "深色模式", "Dark Mode"),
            ("notifications", "通知", "Notifications"),
            
            // API响应
            ("api_success", "请求成功", "Request Successful"),
            ("api_error", "请求失败", "Request Failed"),
            ("not_found", "未找到", "Not Found"),
            ("unauthorized", "未授权", "Unauthorized"),
            ("forbidden", "禁止访问", "Forbidden"),
            ("server_error", "服务器错误", "Server Error"),
            ("invalid_params", "参数无效", "Invalid Parameters"),
            ("file_not_found", "文件未找到", "File Not Found"),
            ("user_not_found", "用户未找到", "User Not Found"),
            ("share_not_found", "共享未找到", "Share Not Found"),
            ("permission_denied", "权限不足", "Permission Denied"),
            ("storage_full", "存储空间已满", "Storage Full"),
            ("quota_exceeded", "配额已超", "Quota Exceeded"),
            
            // 统计信息
            ("statistics", "统计信息", "Statistics"),
            ("total_files", "文件总数", "Total Files"),
            ("total_folders", "文件夹总数", "Total Folders"),
            ("total_size", "总大小", "Total Size"),
            ("total_users", "用户总数", "Total Users"),
            ("active_users", "活跃用户", "Active Users"),
        ];

        // 为每种语言创建翻译
        for (key, zh_cn, en_us) in keys {
            let mut lang_map = HashMap::new();
            lang_map.insert("zh-CN".to_string(), zh_cn.to_string());
            lang_map.insert("zh-TW".to_string(), Self::to_traditional(zh_cn));
            lang_map.insert("en-US".to_string(), en_us.to_string());
            lang_map.insert("en-GB".to_string(), en_us.to_string());
            
            // 日语
            lang_map.insert("ja".to_string(), Self::translate_to_lang(key, "ja"));
            // 韩语
            lang_map.insert("ko".to_string(), Self::translate_to_lang(key, "ko"));
            // 越南语
            lang_map.insert("vi".to_string(), Self::translate_to_lang(key, "vi"));
            // 泰语
            lang_map.insert("th".to_string(), Self::translate_to_lang(key, "th"));
            // 印尼语
            lang_map.insert("id".to_string(), Self::translate_to_lang(key, "id"));
            // 马来语
            lang_map.insert("ms".to_string(), Self::translate_to_lang(key, "ms"));
            // 菲律宾语
            lang_map.insert("fil".to_string(), Self::translate_to_lang(key, "fil"));
            // 西班牙语
            lang_map.insert("es-ES".to_string(), Self::translate_to_lang(key, "es"));
            lang_map.insert("es-MX".to_string(), Self::translate_to_lang(key, "es"));
            // 葡萄牙语
            lang_map.insert("pt-BR".to_string(), Self::translate_to_lang(key, "pt"));
            lang_map.insert("pt-PT".to_string(), Self::translate_to_lang(key, "pt"));
            // 法语
            lang_map.insert("fr".to_string(), Self::translate_to_lang(key, "fr"));
            // 德语
            lang_map.insert("de".to_string(), Self::translate_to_lang(key, "de"));
            // 意大利语
            lang_map.insert("it".to_string(), Self::translate_to_lang(key, "it"));
            // 俄语
            lang_map.insert("ru".to_string(), Self::translate_to_lang(key, "ru"));
            // 阿拉伯语
            lang_map.insert("ar".to_string(), Self::translate_to_lang(key, "ar"));
            // 印地语
            lang_map.insert("hi".to_string(), Self::translate_to_lang(key, "hi"));
            // 孟加拉语
            lang_map.insert("bn".to_string(), Self::translate_to_lang(key, "bn"));
            // 土耳其语
            lang_map.insert("tr".to_string(), Self::translate_to_lang(key, "tr"));
            // 波兰语
            lang_map.insert("pl".to_string(), Self::translate_to_lang(key, "pl"));
            // 荷兰语
            lang_map.insert("nl".to_string(), Self::translate_to_lang(key, "nl"));
            // 瑞典语
            lang_map.insert("sv".to_string(), Self::translate_to_lang(key, "sv"));
            // 丹麦语
            lang_map.insert("da".to_string(), Self::translate_to_lang(key, "da"));
            // 芬兰语
            lang_map.insert("fi".to_string(), Self::translate_to_lang(key, "fi"));
            
            translations.insert(key.to_string(), lang_map);
        }
    }

    fn to_traditional(text: &str) -> String {
        // 简化的繁体转换（实际应用中应使用专业库）
        text.to_string()
    }

    fn translate_to_lang(key: &str, _lang: &str) -> String {
        // 简化的翻译映射（实际应用中应从翻译文件加载）
        let translations: HashMap<&str, &str> = [
            ("welcome", "Welcome"),
            ("login", "Login"),
            ("logout", "Logout"),
            ("username", "Username"),
            ("password", "Password"),
            ("submit", "Submit"),
            ("cancel", "Cancel"),
            ("save", "Save"),
            ("delete", "Delete"),
            ("edit", "Edit"),
            ("create", "Create"),
            ("search", "Search"),
            ("upload", "Upload"),
            ("download", "Download"),
            ("copy", "Copy"),
            ("move", "Move"),
            ("rename", "Rename"),
            ("folder", "Folder"),
            ("file", "File"),
            ("size", "Size"),
            ("date", "Date"),
            ("name", "Name"),
            ("type", "Type"),
            ("action", "Action"),
            ("status", "Status"),
            ("success", "Success"),
            ("error", "Error"),
            ("warning", "Warning"),
            ("info", "Info"),
        ].iter().cloned().collect();
        
        translations.get(key).unwrap_or(&key).to_string()
    }

    pub fn t(&self, key: &str) -> String {
        self.t_with_lang(key, &self.current_language.read().clone())
    }

    pub fn t_with_lang(&self, key: &str, lang: &str) -> String {
        self.translations.read()
            .get(key)
            .and_then(|t| t.get(lang).cloned())
            .unwrap_or_else(|| key.to_string())
    }

    pub fn set_language(&self, lang: &str) {
        *self.current_language.write() = lang.to_string();
    }

    pub fn get_language(&self) -> String {
        self.current_language.read().clone()
    }

    pub fn get_supported_languages(&self) -> Vec<(String, String)> {
        SUPPORTED_LANGUAGES
            .iter()
            .map(|(code, name)| (code.to_string(), name.to_string()))
            .collect()
    }

    pub fn get_translations(&self, lang: &str) -> HashMap<String, String> {
        self.translations.read()
            .iter()
            .map(|(k, v)| (k.clone(), v.get(lang).cloned().unwrap_or_else(|| k.clone())))
            .collect()
    }
}