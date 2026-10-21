/**
 * 小思超级多版本NAS服务 - C++版本
 * 支持完整的API接口、28种语言翻译、文件管理等功能
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <filesystem>
#include <algorithm>
#include <chrono>
#include <ctime>
#include <mutex>
#include <regex>
#include <functional>

// 第三方库头文件 (使用cpp-httplib)
#define CPPHTTPLIB_USE_POLL
#include "httplib.h"

// JSON库 (使用nlohmann/json)
#include "json.hpp"

using json = nlohmann::json;
namespace fs = std::filesystem;

// 配置结构
struct ServerConfig {
    int port = 8086;
    std::string host = "0.0.0.0";
    std::string data_dir = "./data";
    std::string upload_dir = "./uploads";
    std::string log_level = "info";
    int max_upload_size = 100 * 1024 * 1024; // 100MB
};

// 翻译数据
const std::map<std::string, std::map<std::string, std::string>> translations = {
    {"zh-CN", {
        {"welcome", "欢迎使用小思超级多版本NAS服务"},
        {"error", "错误"},
        {"success", "成功"},
        {"file_not_found", "文件未找到"},
        {"upload_success", "上传成功"},
        {"download_success", "下载成功"},
        {"delete_success", "删除成功"},
        {"create_success", "创建成功"},
        {"invalid_request", "无效的请求"},
        {"server_error", "服务器内部错误"}
    }},
    {"zh-TW", {
        {"welcome", "歡迎使用小思超級多版本NAS服務"},
        {"error", "錯誤"},
        {"success", "成功"},
        {"file_not_found", "文件未找到"},
        {"upload_success", "上傳成功"},
        {"download_success", "下載成功"},
        {"delete_success", "刪除成功"},
        {"create_success", "創建成功"},
        {"invalid_request", "無效的請求"},
        {"server_error", "服務器內部錯誤"}
    }},
    {"en", {
        {"welcome", "Welcome to Xiaosi Super Multi-Version NAS Service"},
        {"error", "Error"},
        {"success", "Success"},
        {"file_not_found", "File not found"},
        {"upload_success", "Upload successful"},
        {"download_success", "Download successful"},
        {"delete_success", "Delete successful"},
        {"create_success", "Create successful"},
        {"invalid_request", "Invalid request"},
        {"server_error", "Internal server error"}
    }},
    {"ja", {
        {"welcome", "小思スーパー多版NASサービスへようこそ"},
        {"error", "エラー"},
        {"success", "成功"},
        {"file_not_found", "ファイルが見つかりません"},
        {"upload_success", "アップロード成功"},
        {"download_success", "ダウンロード成功"},
        {"delete_success", "削除成功"},
        {"create_success", "作成成功"},
        {"invalid_request", "無効なリクエスト"},
        {"server_error", "サーバー内部エラー"}
    }},
    {"ko", {
        {"welcome", "샤오시 슈퍼 멀티 버전 NAS 서비스에 오신 것을 환영합니다"},
        {"error", "오류"},
        {"success", "성공"},
        {"file_not_found", "파일을 찾을 수 없습니다"},
        {"upload_success", "업로드 성공"},
        {"download_success", "다운로드 성공"},
        {"delete_success", "삭제 성공"},
        {"create_success", "생성 성공"},
        {"invalid_request", "잘못된 요청"},
        {"server_error", "서버 내부 오류"}
    }},
    {"fr", {
        {"welcome", "Bienvenue dans le service NAS multi-version super Xiaosi"},
        {"error", "Erreur"},
        {"success", "Succès"},
        {"file_not_found", "Fichier non trouvé"},
        {"upload_success", "Téléchargement réussi"},
        {"download_success", "Téléchargement réussi"},
        {"delete_success", "Suppression réussie"},
        {"create_success", "Création réussie"},
        {"invalid_request", "Requête invalide"},
        {"server_error", "Erreur interne du serveur"}
    }},
    {"de", {
        {"welcome", "Willkommen beim Xiaosi Super Multi-Version NAS-Service"},
        {"error", "Fehler"},
        {"success", "Erfolg"},
        {"file_not_found", "Datei nicht gefunden"},
        {"upload_success", "Upload erfolgreich"},
        {"download_success", "Download erfolgreich"},
        {"delete_success", "Löschen erfolgreich"},
        {"create_success", "Erstellung erfolgreich"},
        {"invalid_request", "Ungültige Anfrage"},
        {"server_error", "Interner Serverfehler"}
    }},
    {"es", {
        {"welcome", "Bienvenido al servicio NAS de múltiples versiones super Xiaosi"},
        {"error", "Error"},
        {"success", "Éxito"},
        {"file_not_found", "Archivo no encontrado"},
        {"upload_success", "Carga exitosa"},
        {"download_success", "Descarga exitosa"},
        {"delete_success", "Eliminación exitosa"},
        {"create_success", "Creación exitosa"},
        {"invalid_request", "Solicitud inválida"},
        {"server_error", "Error interno del servidor"}
    }},
    {"it", {
        {"welcome", "Benvenuto nel servizio NAS multi-versione super Xiaosi"},
        {"error", "Errore"},
        {"success", "Successo"},
        {"file_not_found", "File non trovato"},
        {"upload_success", "Caricamento riuscito"},
        {"download_success", "Download riuscito"},
        {"delete_success", "Eliminazione riuscita"},
        {"create_success", "Creazione riuscita"},
        {"invalid_request", "Richiesta non valida"},
        {"server_error", "Errore interno del server"}
    }},
    {"pt", {
        {"welcome", "Bem-vindo ao serviço NAS de múltiplas versões super Xiaosi"},
        {"error", "Erro"},
        {"success", "Sucesso"},
        {"file_not_found", "Arquivo não encontrado"},
        {"upload_success", "Upload bem-sucedido"},
        {"download_success", "Download bem-sucedido"},
        {"delete_success", "Exclusão bem-sucedida"},
        {"create_success", "Criação bem-sucedida"},
        {"invalid_request", "Solicitação inválida"},
        {"server_error", "Erro interno do servidor"}
    }},
    {"ru", {
        {"welcome", "Добро пожаловать в службу NAS супер мульти-версии Xiaosi"},
        {"error", "Ошибка"},
        {"success", "Успех"},
        {"file_not_found", "Файл не найден"},
        {"upload_success", "Загрузка успешна"},
        {"download_success", "Скачивание успешно"},
        {"delete_success", "Удаление успешно"},
        {"create_success", "Создание успешно"},
        {"invalid_request", "Неверный запрос"},
        {"server_error", "Внутренняя ошибка сервера"}
    }},
    {"ar", {
        {"welcome", "مرحباً بك في خدمة NAS متعددة الإصدارات الفائقة من Xiaosi"},
        {"error", "خطأ"},
        {"success", "نجاح"},
        {"file_not_found", "الملف غير موجود"},
        {"upload_success", "تم الرفع بنجاح"},
        {"download_success", "تم التحميل بنجاح"},
        {"delete_success", "تم الحذف بنجاح"},
        {"create_success", "تم الإنشاء بنجاح"},
        {"invalid_request", "طلب غير صالح"},
        {"server_error", "خطأ داخلي في الخادم"}
    }},
    {"hi", {
        {"welcome", "Xiaosi सुपर मल्टी-वर्जन NAS सेवा में आपका स्वागत है"},
        {"error", "त्रुटि"},
        {"success", "सफलता"},
        {"file_not_found", "फ़ाइल नहीं मिली"},
        {"upload_success", "अपलोड सफल"},
        {"download_success", "डाउनलोड सफल"},
        {"delete_success", "हटाना सफल"},
        {"create_success", "बनाना सफल"},
        {"invalid_request", "अमान्य अनुरोध"},
        {"server_error", "सर्वर आंतरिक त्रुटि"}
    }},
    {"th", {
        {"welcome", "ยินดีต้อนรับสู่บริการ NAS หลายเวอร์ชันซุปเปอร์ Xiaosi"},
        {"error", "ข้อผิดพลาด"},
        {"success", "สำเร็จ"},
        {"file_not_found", "ไม่พบไฟล์"},
        {"upload_success", "อัปโหลดสำเร็จ"},
        {"download_success", "ดาวน์โหลดสำเร็จ"},
        {"delete_success", "ลบสำเร็จ"},
        {"create_success", "สร้างสำเร็จ"},
        {"invalid_request", "คำขอไม่ถูกต้อง"},
        {"server_error", "ข้อผิดพลาดภายในเซิร์ฟเวอร์"}
    }},
    {"vi", {
        {"welcome", "Chào mừng đến với dịch vụ NAS đa phiên bản siêu Xiaosi"},
        {"error", "Lỗi"},
        {"success", "Thành công"},
        {"file_not_found", "Không tìm thấy tệp"},
        {"upload_success", "Tải lên thành công"},
        {"download_success", "Tải xuống thành công"},
        {"delete_success", "Xóa thành công"},
        {"create_success", "Tạo thành công"},
        {"invalid_request", "Yêu cầu không hợp lệ"},
        {"server_error", "Lỗi máy chủ nội bộ"}
    }},
    {"id", {
        {"welcome", "Selamat datang di layanan NAS multi-versi super Xiaosi"},
        {"error", "Kesalahan"},
        {"success", "Sukses"},
        {"file_not_found", "File tidak ditemukan"},
        {"upload_success", "Unggah berhasil"},
        {"download_success", "Unduh berhasil"},
        {"delete_success", "Hapus berhasil"},
        {"create_success", "Buat berhasil"},
        {"invalid_request", "Permintaan tidak valid"},
        {"server_error", "Kesalahan server internal"}
    }},
    {"ms", {
        {"welcome", "Selamat datang ke perkhidmatan NAS pelbagai versi super Xiaosi"},
        {"error", "Ralat"},
        {"success", "Berjaya"},
        {"file_not_found", "Fail tidak dijumpai"},
        {"upload_success", "Muat naik berjaya"},
        {"download_success", "Muat turun berjaya"},
        {"delete_success", "Padam berjaya"},
        {"create_success", "Cipta berjaya"},
        {"invalid_request", "Permintaan tidak sah"},
        {"server_error", "Ralat pelayan dalaman"}
    }},
    {"tr", {
        {"welcome", "Xiaosi Süper Çok Sürüm NAS Hizmetine Hoş Geldiniz"},
        {"error", "Hata"},
        {"success", "Başarılı"},
        {"file_not_found", "Dosya bulunamadı"},
        {"upload_success", "Yükleme başarılı"},
        {"download_success", "İndirme başarılı"},
        {"delete_success", "Silme başarılı"},
        {"create_success", "Oluşturma başarılı"},
        {"invalid_request", "Geçersiz istek"},
        {"server_error", "Dahili sunucu hatası"}
    }},
    {"pl", {
        {"welcome", "Witamy w usłudze NAS super wielu wersji Xiaosi"},
        {"error", "Błąd"},
        {"success", "Sukces"},
        {"file_not_found", "Plik nie znaleziony"},
        {"upload_success", "Przesyłanie udane"},
        {"download_success", "Pobieranie udane"},
        {"delete_success", "Usuwanie udane"},
        {"create_success", "Tworzenie udane"},
        {"invalid_request", "Nieprawidłowe żądanie"},
        {"server_error", "Wewnętrzny błąd serwera"}
    }},
    {"nl", {
        {"welcome", "Welkom bij de Xiaosi Super Multi-Versie NAS-service"},
        {"error", "Fout"},
        {"success", "Succes"},
        {"file_not_found", "Bestand niet gevonden"},
        {"upload_success", "Upload succesvol"},
        {"download_success", "Download succesvol"},
        {"delete_success", "Verwijdering succesvol"},
        {"create_success", "Aanmaak succesvol"},
        {"invalid_request", "Ongeldig verzoek"},
        {"server_error", "Interne serverfout"}
    }},
    {"sv", {
        {"welcome", "Välkommen till Xiaosi Super Multi-Version NAS-tjänst"},
        {"error", "Fel"},
        {"success", "Framgång"},
        {"file_not_found", "Filen hittades inte"},
        {"upload_success", "Uppladdning lyckades"},
        {"download_success", "Nedladdning lyckades"},
        {"delete_success", "Radering lyckades"},
        {"create_success", "Skapande lyckades"},
        {"invalid_request", "Ogiltig begäran"},
        {"server_error", "Internt serverfel"}
    }},
    {"no", {
        {"welcome", "Velkommen til Xiaosi Super Multi-Version NAS-tjeneste"},
        {"error", "Feil"},
        {"success", "Suksess"},
        {"file_not_found", "Fil ikke funnet"},
        {"upload_success", "Opplasting vellykket"},
        {"download_success", "Nedlasting vellykket"},
        {"delete_success", "Sletting vellykket"},
        {"create_success", "Opprettelse vellykket"},
        {"invalid_request", "Ugyldig forespørsel"},
        {"server_error", "Intern serverfeil"}
    }},
    {"da", {
        {"welcome", "Velkommen til Xiaosi Super Multi-Version NAS-tjeneste"},
        {"error", "Fejl"},
        {"success", "Succes"},
        {"file_not_found", "Fil ikke fundet"},
        {"upload_success", "Upload lykkedes"},
        {"download_success", "Download lykkedes"},
        {"delete_success", "Sletning lykkedes"},
        {"create_success", "Oprettelse lykkedes"},
        {"invalid_request", "Ugyldig anmodning"},
        {"server_error", "Intern serverfejl"}
    }},
    {"fi", {
        {"welcome", "Tervetuloa Xiaosi Super Multi-Version NAS-palveluun"},
        {"error", "Virhe"},
        {"success", "Onnistui"},
        {"file_not_found", "Tiedostoa ei löydy"},
        {"upload_success", "Lataus onnistui"},
        {"download_success", "Lataus onnistui"},
        {"delete_success", "Poisto onnistui"},
        {"create_success", "Luonti onnistui"},
        {"invalid_request", "Virheellinen pyyntö"},
        {"server_error", "Sisäinen palvelinvirhe"}
    }},
    {"cs", {
        {"welcome", "Vítejte ve službě NAS super multi-verze Xiaosi"},
        {"error", "Chyba"},
        {"success", "Úspěch"},
        {"file_not_found", "Soubor nenalezen"},
        {"upload_success", "Nahrání úspěšné"},
        {"download_success", "Stažení úspěšné"},
        {"delete_success", "Smazání úspěšné"},
        {"create_success", "Vytvoření úspěšné"},
        {"invalid_request", "Neplatný požadavek"},
        {"server_error", "Interní chyba serveru"}
    }},
    {"hu", {
        {"welcome", "Üdvözöljük a Xiaosi Szuper Többverziós NAS szolgáltatásban"},
        {"error", "Hiba"},
        {"success", "Siker"},
        {"file_not_found", "Fájl nem található"},
        {"upload_success", "Feltöltés sikeres"},
        {"download_success", "Letöltés sikeres"},
        {"delete_success", "Törlés sikeres"},
        {"create_success", "Létrehozás sikeres"},
        {"invalid_request", "Érvénytelen kérés"},
        {"server_error", "Belső szerver hiba"}
    }},
    {"ro", {
        {"welcome", "Bine ați venit la serviciul NAS super multi-versiune Xiaosi"},
        {"error", "Eroare"},
        {"success", "Succes"},
        {"file_not_found", "Fișier nu a fost găsit"},
        {"upload_success", "Încărcare reușită"},
        {"download_success", "Descărcare reușită"},
        {"delete_success", "Ștergere reușită"},
        {"create_success", "Creare reușită"},
        {"invalid_request", "Cerere invalidă"},
        {"server_error", "Eroare internă a serverului"}
    }},
    {"uk", {
        {"welcome", "Ласкаво просимо до служби NAS супер мульти-версії Xiaosi"},
        {"error", "Помилка"},
        {"success", "Успіх"},
        {"file_not_found", "Файл не знайдено"},
        {"upload_success", "Завантаження успішне"},
        {"download_success", "Завантаження успішне"},
        {"delete_success", "Видалення успішне"},
        {"create_success", "Створення успішне"},
        {"invalid_request", "Невірний запит"},
        {"server_error", "Внутрішня помилка сервера"}
    }},
    {"el", {
        {"welcome", "Καλώς ήρθατε στην υπηρεσία NAS υπερ πολλαπλής έκδοσης Xiaosi"},
        {"error", "Σφάλμα"},
        {"success", "Επιτυχία"},
        {"file_not_found", "Το αρχείο δεν βρέθηκε"},
        {"upload_success", "Η μεταφόρτωση ήταν επιτυχής"},
        {"download_success", "Η λήψη ήταν επιτυχής"},
        {"delete_success", "Η διαγραφή ήταν επιτυχής"},
        {"create_success", "Η δημιουργία ήταν επιτυχής"},
        {"invalid_request", "Μη έγκυρο αίτημα"},
        {"server_error", "Εσωτερικό σφάλμα διακομιστή"}
    }}
};

// 全局配置
ServerConfig g_config;
std::mutex g_mutex;

// 工具函数
std::string get_current_time() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    return ss.str();
}

std::string get_translation(const std::string& lang, const std::string& key) {
    auto lang_it = translations.find(lang);
    if (lang_it != translations.end()) {
        auto key_it = lang_it->second.find(key);
        if (key_it != lang_it->second.end()) {
            return key_it->second;
        }
    }
    // 默认返回中文
    auto zh_it = translations.find("zh-CN");
    if (zh_it != translations.end()) {
        auto key_it = zh_it->second.find(key);
        if (key_it != zh_it->second.end()) {
            return key_it->second;
        }
    }
    return key;
}

json create_response(bool success, const std::string& message, const json& data = json::object()) {
    json response;
    response["success"] = success;
    response["message"] = message;
    response["timestamp"] = get_current_time();
    response["data"] = data;
    return response;
}

// 文件工具类
class FileManager {
public:
    static bool create_directory(const fs::path& path) {
        try {
            return fs::create_directories(path);
        } catch (const std::exception& e) {
            std::cerr << "Create directory error: " << e.what() << std::endl;
            return false;
        }
    }

    static bool delete_file(const fs::path& path) {
        try {
            return fs::remove(path);
        } catch (const std::exception& e) {
            std::cerr << "Delete file error: " << e.what() << std::endl;
            return false;
        }
    }

    static bool exists(const fs::path& path) {
        return fs::exists(path);
    }

    static bool is_directory(const fs::path& path) {
        return fs::is_directory(path);
    }

    static json list_directory(const fs::path& path) {
        json files = json::array();
        try {
            for (const auto& entry : fs::directory_iterator(path)) {
                json file_info;
                file_info["name"] = entry.path().filename().string();
                file_info["path"] = entry.path().string();
                file_info["is_directory"] = entry.is_directory();
                file_info["size"] = entry.is_directory() ? 0 : fs::file_size(entry.path());
                
                auto ftime = fs::last_write_time(entry.path());
                auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
                    ftime - fs::file_time_type::clock::now() + std::chrono::system_clock::now());
                auto time_t = std::chrono::system_clock::to_time_t(sctp);
                std::stringstream ss;
                ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
                file_info["modified_time"] = ss.str();
                
                files.push_back(file_info);
            }
        } catch (const std::exception& e) {
            std::cerr << "List directory error: " << e.what() << std::endl;
        }
        return files;
    }

    static bool copy_file(const fs::path& from, const fs::path& to) {
        try {
            fs::copy_file(from, to, fs::copy_options::overwrite_existing);
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Copy file error: " << e.what() << std::endl;
            return false;
        }
    }

    static bool move_file(const fs::path& from, const fs::path& to) {
        try {
            fs::rename(from, to);
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Move file error: " << e.what() << std::endl;
            return false;
        }
    }
};

// 配置加载器
class ConfigLoader {
public:
    static ServerConfig load_config(const std::string& config_path) {
        ServerConfig config;
        
        try {
            std::ifstream file(config_path);
            if (!file.is_open()) {
                std::cerr << "Cannot open config file: " << config_path << std::endl;
                std::cerr << "Using default configuration" << std::endl;
                return config;
            }
            
            json config_json;
            file >> config_json;
            
            if (config_json.contains("port")) {
                config.port = config_json["port"];
            }
            if (config_json.contains("host")) {
                config.host = config_json["host"];
            }
            if (config_json.contains("data_dir")) {
                config.data_dir = config_json["data_dir"];
            }
            if (config_json.contains("upload_dir")) {
                config.upload_dir = config_json["upload_dir"];
            }
            if (config_json.contains("log_level")) {
                config.log_level = config_json["log_level"];
            }
            if (config_json.contains("max_upload_size")) {
                config.max_upload_size = config_json["max_upload_size"];
            }
            
            std::cout << "Configuration loaded from: " << config_path << std::endl;
            
        } catch (const std::exception& e) {
            std::cerr << "Load config error: " << e.what() << std::endl;
            std::cerr << "Using default configuration" << std::endl;
        }
        
        return config;
    }
};

// 主服务类
class NASServer {
private:
    httplib::Server server_;
    ServerConfig config_;

public:
    NASServer(const ServerConfig& config) : config_(config) {
        setup_routes();
        ensure_directories();
    }

    void ensure_directories() {
        FileManager::create_directory(config_.data_dir);
        FileManager::create_directory(config_.upload_dir);
    }

    void setup_routes() {
        // CORS支持
        server_.set_default_headers({
            {"Access-Control-Allow-Origin", "*"},
            {"Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"},
            {"Access-Control-Allow-Headers", "Content-Type, Authorization"}
        });

        // OPTIONS请求处理
        server_.Options(R"(.*)", [](const httplib::Request& req, httplib::Response& res) {
            res.status = 200;
        });

        // ==================== 核心API ====================

        // 健康检查
        server_.Get("/api/health", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            json data;
            data["status"] = "healthy";
            data["version"] = "2.0.0";
            data["uptime"] = get_current_time();
            
            res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
        });

        // 欢迎信息
        server_.Get("/api/", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            json data;
            data["message"] = get_translation(lang, "welcome");
            data["version"] = "2.0.0";
            data["language"] = lang;
            data["supported_languages"] = get_supported_languages();
            
            res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
        });

        // ==================== 文件操作API ====================

        // 列出文件
        server_.Get("/api/files", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            std::string path = req.get_param_value("path");
            
            if (path.empty()) {
                path = config_.data_dir;
            }
            
            if (!FileManager::exists(path)) {
                res.status = 404;
                res.set_content(create_response(false, get_translation(lang, "file_not_found")).dump(), "application/json");
                return;
            }
            
            json data;
            data["path"] = path;
            data["files"] = FileManager::list_directory(path);
            
            res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
        });

        // 上传文件
        server_.Post("/api/files/upload", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            
            if (!req.has_file("file")) {
                res.status = 400;
                res.set_content(create_response(false, get_translation(lang, "invalid_request")).dump(), "application/json");
                return;
            }
            
            const auto& file = req.get_file_value("file");
            std::string upload_path = config_.upload_dir + "/" + file.filename;
            
            std::ofstream out_file(upload_path, std::ios::binary);
            out_file.write(file.content.data(), file.content.size());
            out_file.close();
            
            json data;
            data["filename"] = file.filename;
            data["size"] = file.content.size();
            data["path"] = upload_path;
            
            res.set_content(create_response(true, get_translation(lang, "upload_success"), data).dump(), "application/json");
        });

        // 下载文件
        server_.Get("/api/files/download", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            std::string path = req.get_param_value("path");
            
            if (path.empty() || !FileManager::exists(path)) {
                res.status = 404;
                res.set_content(create_response(false, get_translation(lang, "file_not_found")).dump(), "application/json");
                return;
            }
            
            std::ifstream file(path, std::ios::binary);
            std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
            
            res.set_content(content, "application/octet-stream");
        });

        // 创建文件夹
        server_.Post("/api/files/mkdir", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            
            try {
                json body = json::parse(req.body);
                std::string path = body["path"];
                
                if (FileManager::create_directory(path)) {
                    json data;
                    data["path"] = path;
                    res.set_content(create_response(true, get_translation(lang, "create_success"), data).dump(), "application/json");
                } else {
                    res.status = 500;
                    res.set_content(create_response(false, get_translation(lang, "server_error")).dump(), "application/json");
                }
            } catch (const std::exception& e) {
                res.status = 400;
                res.set_content(create_response(false, get_translation(lang, "invalid_request")).dump(), "application/json");
            }
        });

        // 删除文件
        server_.Delete("/api/files", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            std::string path = req.get_param_value("path");
            
            if (path.empty()) {
                res.status = 400;
                res.set_content(create_response(false, get_translation(lang, "invalid_request")).dump(), "application/json");
                return;
            }
            
            if (!FileManager::exists(path)) {
                res.status = 404;
                res.set_content(create_response(false, get_translation(lang, "file_not_found")).dump(), "application/json");
                return;
            }
            
            if (FileManager::delete_file(path)) {
                json data;
                data["path"] = path;
                res.set_content(create_response(true, get_translation(lang, "delete_success"), data).dump(), "application/json");
            } else {
                res.status = 500;
                res.set_content(create_response(false, get_translation(lang, "server_error")).dump(), "application/json");
            }
        });

        // 复制文件
        server_.Post("/api/files/copy", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            
            try {
                json body = json::parse(req.body);
                std::string from = body["from"];
                std::string to = body["to"];
                
                if (FileManager::copy_file(from, to)) {
                    json data;
                    data["from"] = from;
                    data["to"] = to;
                    res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
                } else {
                    res.status = 500;
                    res.set_content(create_response(false, get_translation(lang, "server_error")).dump(), "application/json");
                }
            } catch (const std::exception& e) {
                res.status = 400;
                res.set_content(create_response(false, get_translation(lang, "invalid_request")).dump(), "application/json");
            }
        });

        // 移动文件
        server_.Post("/api/files/move", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            
            try {
                json body = json::parse(req.body);
                std::string from = body["from"];
                std::string to = body["to"];
                
                if (FileManager::move_file(from, to)) {
                    json data;
                    data["from"] = from;
                    data["to"] = to;
                    res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
                } else {
                    res.status = 500;
                    res.set_content(create_response(false, get_translation(lang, "server_error")).dump(), "application/json");
                }
            } catch (const std::exception& e) {
                res.status = 400;
                res.set_content(create_response(false, get_translation(lang, "invalid_request")).dump(), "application/json");
            }
        });

        // ==================== 系统信息API ====================

        // 获取系统信息
        server_.Get("/api/system/info", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            
            json data;
            data["version"] = "2.0.0";
            data["uptime"] = get_current_time();
            data["data_dir"] = config_.data_dir;
            data["upload_dir"] = config_.upload_dir;
            data["port"] = config_.port;
            data["supported_languages_count"] = 28;
            
            res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
        });

        // 获取存储统计
        server_.Get("/api/system/storage", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            
            json data;
            uintmax_t total_size = 0;
            size_t file_count = 0;
            
            try {
                for (const auto& entry : fs::recursive_directory_iterator(config_.data_dir)) {
                    if (!entry.is_directory()) {
                        total_size += fs::file_size(entry.path());
                        file_count++;
                    }
                }
            } catch (const std::exception& e) {
                // 忽略错误
            }
            
            data["total_size"] = total_size;
            data["file_count"] = file_count;
            data["data_dir"] = config_.data_dir;
            
            res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
        });

        // ==================== 翻译API ====================

        // 获取支持的语言列表
        server_.Get("/api/i18n/languages", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            
            json data;
            data["languages"] = get_supported_languages();
            data["current_language"] = lang;
            
            res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
        });

        // 获取翻译
        server_.Get("/api/i18n/translations", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            
            auto lang_it = translations.find(lang);
            if (lang_it != translations.end()) {
                json data;
                data["language"] = lang;
                data["translations"] = lang_it->second;
                res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
            } else {
                res.status = 404;
                res.set_content(create_response(false, "Language not found").dump(), "application/json");
            }
        });

        // ==================== 搜索API ====================

        // 搜索文件
        server_.Get("/api/search", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            std::string query = req.get_param_value("q");
            std::string search_path = req.get_param_value("path");
            
            if (search_path.empty()) {
                search_path = config_.data_dir;
            }
            
            json results = json::array();
            
            if (!query.empty()) {
                try {
                    std::regex pattern(query, std::regex_constants::icase);
                    
                    for (const auto& entry : fs::recursive_directory_iterator(search_path)) {
                        std::string filename = entry.path().filename().string();
                        if (std::regex_search(filename, pattern)) {
                            json file_info;
                            file_info["name"] = filename;
                            file_info["path"] = entry.path().string();
                            file_info["is_directory"] = entry.is_directory();
                            results.push_back(file_info);
                        }
                    }
                } catch (const std::exception& e) {
                    res.status = 400;
                    res.set_content(create_response(false, "Invalid search pattern").dump(), "application/json");
                    return;
                }
            }
            
            json data;
            data["query"] = query;
            data["path"] = search_path;
            data["results"] = results;
            data["count"] = results.size();
            
            res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
        });

        // ==================== 配置API ====================

        // 获取配置
        server_.Get("/api/config", [this](const httplib::Request& req, httplib::Response& res) {
            std::string lang = get_language(req);
            
            json data;
            data["port"] = config_.port;
            data["host"] = config_.host;
            data["data_dir"] = config_.data_dir;
            data["upload_dir"] = config_.upload_dir;
            data["log_level"] = config_.log_level;
            data["max_upload_size"] = config_.max_upload_size;
            
            res.set_content(create_response(true, get_translation(lang, "success"), data).dump(), "application/json");
        });
    }

    std::string get_language(const httplib::Request& req) {
        // 优先从Header获取
        if (req.has_header("Accept-Language")) {
            std::string lang = req.get_header_value("Accept-Language");
            if (translations.find(lang) != translations.end()) {
                return lang;
            }
        }
        
        // 从查询参数获取
        if (req.has_param("lang")) {
            std::string lang = req.get_param_value("lang");
            if (translations.find(lang) != translations.end()) {
                return lang;
            }
        }
        
        // 默认中文
        return "zh-CN";
    }

    json get_supported_languages() {
        json langs = json::array();
        for (const auto& pair : translations) {
            langs.push_back(pair.first);
        }
        return langs;
    }

    bool start() {
        std::cout << "Starting NAS Server on " << config_.host << ":" << config_.port << std::endl;
        std::cout << "Data directory: " << config_.data_dir << std::endl;
        std::cout << "Upload directory: " << config_.upload_dir << std::endl;
        std::cout << "Supported languages: " << translations.size() << std::endl;
        
        return server_.listen(config_.host, config_.port);
    }

    void stop() {
        server_.stop();
    }
};

int main() {
    // 加载配置
    std::string config_path = "../config/config.json";
    g_config = ConfigLoader::load_config(config_path);
    
    // 创建并启动服务器
    NASServer server(g_config);
    
    std::cout << "====================================" << std::endl;
    std::cout << "小思超级多版本NAS服务 - C++版本" << std::endl;
    std::cout << "====================================" << std::endl;
    std::cout << "Server started at: " << get_current_time() << std::endl;
    
    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }
    
    return 0;
}