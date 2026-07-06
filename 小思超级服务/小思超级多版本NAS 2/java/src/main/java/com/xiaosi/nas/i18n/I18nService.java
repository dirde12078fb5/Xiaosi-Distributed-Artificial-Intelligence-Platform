package com.xiaosi.nas.i18n;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.*;
import jakarta.annotation.PostConstruct;

@Slf4j
@Service
public class I18nService {

    private static final String LANGUAGES_PATH = "/languages/";
    private static final List<String> SUPPORTED_LANGUAGES = Arrays.asList(
        "zh-CN", "zh-TW", "en-US", "en-GB", "ja-JP", "ko-KR", "vi-VN",
        "th-TH", "id-ID", "ms-MY", "fil-PH", "hi-IN", "bn-IN", "ta-IN",
        "te-IN", "mr-IN", "gu-IN", "kn-IN", "ur-PK", "fa-IR", "ar-SA",
        "he-IL", "ru-RU", "uk-UA", "pl-PL", "de-DE", "fr-FR", "es-ES",
        "pt-PT", "it-IT", "nl-NL", "sv-SE", "no-NO", "da-DK", "fi-FI",
        "tr-TR", "hu-HU", "cs-CZ", "ro-RO", "bg-BG", "el-GR", "sr-RS",
        "sk-SK", "hr-HR", "sl-SI", "et-EE", "lv-LV", "lt-LT"
    );

    private final Map<String, Map<String, String>> translations = new HashMap<>();
    private String defaultLanguage = "zh-CN";

    @PostConstruct
    public void init() {
        for (String lang : SUPPORTED_LANGUAGES) {
            loadTranslations(lang);
        }
        log.info("已加载 {} 种语言翻译", translations.size());
    }

    private void loadTranslations(String language) {
        String filename = LANGUAGES_PATH + language + ".properties";
        try (InputStream is = getClass().getResourceAsStream(filename)) {
            if (is != null) {
                Properties props = new Properties();
                props.load(is);
                Map<String, String> langMap = new HashMap<>();
                props.forEach((k, v) -> langMap.put(k.toString(), v.toString()));
                translations.put(language, langMap);
                log.info("加载语言文件: {}", language);
            } else {
                // 如果文件不存在，创建默认翻译
                Map<String, String> defaultTranslations = getDefaultTranslations(language);
                translations.put(language, defaultTranslations);
                log.warn("语言文件不存在，使用默认翻译: {}", language);
            }
        } catch (IOException e) {
            log.error("加载语言文件失败: {}", language, e);
        }
    }

    public String translate(String key, String language) {
        Map<String, String> langMap = translations.get(language);
        if (langMap == null) {
            langMap = translations.get(defaultLanguage);
        }
        return langMap != null ? langMap.getOrDefault(key, key) : key;
    }

    public String translate(String key, String language, Object... args) {
        String template = translate(key, language);
        return String.format(template, args);
    }

    public List<String> getSupportedLanguages() {
        return SUPPORTED_LANGUAGES;
    }

    public boolean isLanguageSupported(String language) {
        return SUPPORTED_LANGUAGES.contains(language);
    }

    public void setDefaultLanguage(String language) {
        if (isLanguageSupported(language)) {
            defaultLanguage = language;
        }
    }

    public String getDefaultLanguage() {
        return defaultLanguage;
    }

    private Map<String, String> getDefaultTranslations(String language) {
        Map<String, String> defaults = new HashMap<>();
        
        // 基础翻译
        defaults.put("nas.title", "小思NAS");
        defaults.put("nas.welcome", "欢迎使用小思NAS服务");
        defaults.put("nas.error", "发生错误");
        defaults.put("nas.success", "操作成功");
        defaults.put("nas.loading", "正在加载...");
        
        // 用户相关
        defaults.put("user.login", "登录");
        defaults.put("user.logout", "注销");
        defaults.put("user.register", "注册");
        defaults.put("user.username", "用户名");
        defaults.put("user.password", "密码");
        defaults.put("user.role", "角色");
        defaults.put("user.storage", "存储配额");
        defaults.put("user.language", "语言");
        defaults.put("user.created", "用户创建成功");
        defaults.put("user.deleted", "用户删除成功");
        defaults.put("user.updated", "用户更新成功");
        defaults.put("user.notfound", "用户不存在");
        defaults.put("user.alreadyexists", "用户名已存在");
        defaults.put("user.invalidcredentials", "用户名或密码错误");
        
        // 存储相关
        defaults.put("storage.volume", "存储卷");
        defaults.put("storage.create", "创建存储卷");
        defaults.put("storage.delete", "删除存储卷");
        defaults.put("storage.files", "文件列表");
        defaults.put("storage.directory", "目录");
        defaults.put("storage.upload", "上传文件");
        defaults.put("storage.download", "下载文件");
        defaults.put("storage.usage", "存储使用情况");
        defaults.put("storage.available", "可用空间");
        defaults.put("storage.used", "已用空间");
        defaults.put("storage.total", "总空间");
        defaults.put("storage.notfound", "存储卷不存在");
        defaults.put("storage.created", "存储卷创建成功");
        
        // 共享相关
        defaults.put("share.title", "共享");
        defaults.put("share.create", "创建共享");
        defaults.put("share.delete", "删除共享");
        defaults.put("share.public", "公开共享");
        defaults.put("share.private", "私有共享");
        defaults.put("share.password", "访问密码");
        defaults.put("share.valid", "共享有效");
        defaults.put("share.notfound", "共享不存在");
        defaults.put("share.created", "共享创建成功");
        
        // SMB相关
        defaults.put("smb.title", "SMB服务");
        defaults.put("smb.config", "SMB配置");
        defaults.put("smb.active", "激活配置");
        defaults.put("smb.workgroup", "工作组");
        defaults.put("smb.protocol", "协议版本");
        
        // 推送相关
        defaults.put("push.title", "通知");
        defaults.put("push.unread", "未读通知");
        defaults.put("push.read", "已读通知");
        defaults.put("push.clear", "清除通知");
        defaults.put("push.broadcast", "广播通知");
        
        // 系统相关
        defaults.put("system.info", "系统信息");
        defaults.put("system.cpu", "CPU使用率");
        defaults.put("system.memory", "内存使用率");
        defaults.put("system.disk", "磁盘信息");
        defaults.put("system.network", "网络信息");
        defaults.put("system.metrics", "系统指标");
        
        // 配置相关
        defaults.put("config.title", "配置");
        defaults.put("config.reload", "重新加载配置");
        defaults.put("config.update", "更新配置");
        defaults.put("config.saved", "配置已保存");
        
        return defaults;
    }
}