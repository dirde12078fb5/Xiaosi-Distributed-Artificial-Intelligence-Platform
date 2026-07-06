package com.xiaosi.nas.services

import com.xiaosi.nas.models.Language
import com.xiaosi.nas.models.Translation
import java.util.concurrent.ConcurrentHashMap

class TranslationService {
    private val translations = ConcurrentHashMap<String, MutableMap<String, String>>()

    // 28种语言支持
    private val supportedLanguages = listOf(
        Language("zh-CN", "Chinese (Simplified)", "简体中文"),
        Language("zh-TW", "Chinese (Traditional)", "繁體中文"),
        Language("en", "English", "English"),
        Language("ja", "Japanese", "日本語"),
        Language("ko", "Korean", "한국어"),
        Language("vi", "Vietnamese", "Tiếng Việt"),
        Language("th", "Thai", "ไทย"),
        Language("id", "Indonesian", "Bahasa Indonesia"),
        Language("ms", "Malay", "Bahasa Melayu"),
        Language("fil", "Filipino", "Filipino"),
        Language("hi", "Hindi", "हिन्दी"),
        Language("bn", "Bengali", "বাংলা"),
        Language("ta", "Tamil", "தமிழ்"),
        Language("te", "Telugu", "తెలుగు"),
        Language("mr", "Marathi", "मराठी"),
        Language("gu", "Gujarati", "ગુજરાતી"),
        Language("kn", "Kannada", "ಕನ್ನಡ"),
        Language("ml", "Malayalam", "മലയാളം"),
        Language("pa", "Punjabi", "ਪੰਜਾਬੀ"),
        Language("ar", "Arabic", "العربية"),
        Language("fa", "Persian", "فارسی"),
        Language("he", "Hebrew", "עברית"),
        Language("tr", "Turkish", "Türkçe"),
        Language("ru", "Russian", "Русский"),
        Language("uk", "Ukrainian", "Українська"),
        Language("pl", "Polish", "Polski"),
        Language("de", "German", "Deutsch"),
        Language("fr", "French", "Français")
    )

    init {
        initializeDefaultTranslations()
    }

    fun getSupportedLanguages(): List<Language> = supportedLanguages

    fun getTranslations(langCode: String): Map<String, String> {
        return translations[langCode] ?: emptyMap()
    }

    fun translate(key: String, langCode: String, vararg args: Any): String {
        val langTranslations = translations[langCode] ?: translations["en"] ?: return key
        var text = langTranslations[key] ?: translations["en"]?.get(key) ?: key

        args.forEachIndexed { index, arg ->
            text = text.replace("{$index}", arg.toString())
        }

        return text
    }

    fun addTranslation(key: String, langCode: String, text: String) {
        translations.getOrPut(langCode) { mutableMapOf() }[key] = text
    }

    fun addTranslations(translation: Translation) {
        translation.translations.forEach { (lang, text) ->
            translations.getOrPut(lang) { mutableMapOf() }[translation.key] = text
        }
    }

    private fun initializeDefaultTranslations() {
        // 常用翻译键
        val keys = listOf(
            "welcome" to mapOf(
                "zh-CN" to "欢迎使用小思NAS",
                "zh-TW" to "歡迎使用小思NAS",
                "en" to "Welcome to Xiaosi NAS",
                "ja" to "小思NASへようこそ",
                "ko" to "小思 NAS에 오신 것을 환영합니다",
                "vi" to "Chào mừng đến với Xiaosi NAS",
                "th" to "ยินดีต้อนรับสู่ Xiaosi NAS",
                "id" to "Selamat datang di Xiaosi NAS",
                "ms" to "Selamat datang ke Xiaosi NAS",
                "fil" to "Maligayang pagdating sa Xiaosi NAS",
                "hi" to "Xiaosi NAS में आपका स्वागत है",
                "bn" to "Xiaosi NAS-এ স্বাগতম",
                "ta" to "Xiaosi NASக்கு வரவேற்பு",
                "te" to "Xiaosi NASకి స్వాగతం",
                "mr" to "Xiaosi NAS में आपले स्वागत आहे",
                "gu" to "Xiaosi NASમાં સ્વાગત છે",
                "kn" to "Xiaosi NASಗೆ ಸ್ವಾಗತ",
                "ml" to "Xiaosi NAS-ലേക്ക് സ്വാഗതം",
                "pa" to "Xiaosi NAS ਵਿੱਚ ਸੁਆਗਤ ਹੈ",
                "ar" to "مرحباً بك في Xiaosi NAS",
                "fa" to "به Xiaosi NAS خوش آمدید",
                "he" to "ברוך הבא ל-Xiaosi NAS",
                "tr" to "Xiaosi NAS'ye hoş geldiniz",
                "ru" to "Добро пожаловать в Xiaosi NAS",
                "uk" to "Ласкаво просимо до Xiaosi NAS",
                "pl" to "Witamy w Xiaosi NAS",
                "de" to "Willkommen bei Xiaosi NAS",
                "fr" to "Bienvenue sur Xiaosi NAS"
            ),
            "file.upload" to mapOf(
                "zh-CN" to "文件上传成功",
                "zh-TW" to "檔案上傳成功",
                "en" to "File uploaded successfully",
                "ja" to "ファイルが正常にアップロードされました",
                "ko" to "파일이 성공적으로 업로드되었습니다",
                "vi" to "Tệp đã được tải lên thành công",
                "th" to "อัปโหลดไฟล์สำเร็จแล้ว",
                "id" to "File berhasil diunggah",
                "ms" to "Fail berjaya dimuat naik",
                "fil" to "Matagumpay na na-upload ang file",
                "hi" to "फ़ाइल सफलतापूर्वक अपलोड की गई",
                "bn" to "ফাইল সফলভাবে আপলোড হয়েছে",
                "ta" to "கோப்பு வெற்றிகரமாக பதிவேற்றப்பட்டது",
                "te" to "ఫైల్ విజయవంతంగా అప్‌లోడ్ చేయబడింది",
                "mr" to "फाइल यशस्वीरित्या अपलोड केली",
                "gu" to "ફાઇલ સફળતાપૂર્વક અપલોડ થઈ",
                "kn" to "ಫೈಲ್ ಯಶಸ್ವಿಯಾಗಿ ಅಪ್‌ಲೋಡ್ ಆಗಿದೆ",
                "ml" to "ഫയൽ വിജയകരമായി അപ്‌ലോഡുചെയ്‌തു",
                "pa" to "ਫਾਈਲ ਸਫਲਤਾਪੂਰਵਕ ਅਪਲੋਡ ਕੀਤੀ ਗਈ",
                "ar" to "تم رفع الملف بنجاح",
                "fa" to "فایل با موفقیت آپلود شد",
                "he" to "הקובץ הועלה בהצלחה",
                "tr" to "Dosya başarıyla yüklendi",
                "ru" to "Файл успешно загружен",
                "uk" to "Файл успішно завантажено",
                "pl" to "Plik został pomyślnie przesłany",
                "de" to "Datei erfolgreich hochgeladen",
                "fr" to "Fichier téléchargé avec succès"
            ),
            "file.download" to mapOf(
                "zh-CN" to "文件下载",
                "zh-TW" to "檔案下載",
                "en" to "File Download",
                "ja" to "ファイルダウンロード",
                "ko" to "파일 다운로드",
                "vi" to "Tải xuống tệp",
                "th" to "ดาวน์โหลดไฟล์",
                "id" to "Unduh File",
                "ms" to "Muat Turun Fail",
                "fil" to "I-download ang File",
                "hi" to "फ़ाइल डाउनलोड करें",
                "bn" to "ফাইল ডাউনলোড",
                "ta" to "கோப்பைப் பதிவிறக்கு",
                "te" to "ఫైల్‌ను డౌన్‌లోడ్ చేయండి",
                "mr" to "फाइल डाउनलोड करा",
                "gu" to "ફાઇલ ડાઉનલોડ કરો",
                "kn" to "ಫೈಲ್ ಅನ್ನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
                "ml" to "ഫയൽ ഡൗൺലോഡ് ചെയ്യുക",
                "pa" to "ਫਾਈਲ ਡਾਊਨਲੋਡ ਕਰੋ",
                "ar" to "تحميل الملف",
                "fa" to "دانلود فایل",
                "he" to "הורדת קובץ",
                "tr" to "Dosya İndir",
                "ru" to "Скачать файл",
                "uk" to "Завантажити файл",
                "pl" to "Pobierz plik",
                "de" to "Datei herunterladen",
                "fr" to "Télécharger le fichier"
            ),
            "file.delete" to mapOf(
                "zh-CN" to "文件删除成功",
                "zh-TW" to "檔案刪除成功",
                "en" to "File deleted successfully",
                "ja" to "ファイルが正常に削除されました",
                "ko" to "파일이 성공적으로 삭제되었습니다",
                "vi" to "Tệp đã được xóa thành công",
                "th" to "ลบไฟล์สำเร็จแล้ว",
                "id" to "File berhasil dihapus",
                "ms" to "Fail berjaya dipadam",
                "fil" to "Matagumpay na natanggal ang file",
                "hi" to "फ़ाइल सफलतापूर्वक हटाई गई",
                "bn" to "ফাইল সফলভাবে মুছে ফেলা হয়েছে",
                "ta" to "கோப்பு வெற்றிகரமாக நீக்கப்பட்டது",
                "te" to "ఫైల్ విజయవంతంగా తొలగించబడింది",
                "mr" to "फाइल यशस्वीरित्या हटवली",
                "gu" to "ફાઇલ સફળતાપૂર્વક કાઢી નાખવામાં આવી",
                "kn" to "ಫೈಲ್ ಯಶಸ್ವಿಯಾಗಿ ಅಳಿಸಲಾಗಿದೆ",
                "ml" to "ഫയൽ വിജയകരമായി ഇല്ലാതാക്കി",
                "pa" to "ਫਾਈਲ ਸਫਲਤਾਪੂਰਵਕ ਮਿਟਾਈ ਗਈ",
                "ar" to "تم حذف الملف بنجاح",
                "fa" to "فایل با موفقیت حذف شد",
                "he" to "הקובץ נמחק בהצלחה",
                "tr" to "Dosya başarıyla silindi",
                "ru" to "Файл успешно удален",
                "uk" to "Файл успішно видалено",
                "pl" to "Plik został pomyślnie usunięty",
                "de" to "Datei erfolgreich gelöscht",
                "fr" to "Fichier supprimé avec succès"
            ),
            "file.not_found" to mapOf(
                "zh-CN" to "文件未找到",
                "zh-TW" to "檔案未找到",
                "en" to "File not found",
                "ja" to "ファイルが見つかりません",
                "ko" to "파일을 찾을 수 없습니다",
                "vi" to "Không tìm thấy tệp",
                "th" to "ไม่พบไฟล์",
                "id" to "File tidak ditemukan",
                "ms" to "Fail tidak dijumpai",
                "fil" to "Hindi nahanap ang file",
                "hi" to "फ़ाइल नहीं मिली",
                "bn" to "ফাইল পাওয়া যায়নি",
                "ta" to "கோப்பு கிடைக்கவில்லை",
                "te" to "ఫైల్ కనుగొనబడలేదు",
                "mr" to "फाइल आढळली नाही",
                "gu" to "ફાઇલ મળી નથી",
                "kn" to "ಫೈಲ್ ಕಂಡುಬಂದಿಲ್ಲ",
                "ml" to "ഫയൽ കണ്ടെത്തിയില്ല",
                "pa" to "ਫਾਈਲ ਨਹੀਂ ਲੱਭੀ",
                "ar" to "الملف غير موجود",
                "fa" to "فایل یافت نشد",
                "he" to "הקובץ לא נמצא",
                "tr" to "Dosya bulunamadı",
                "ru" to "Файл не найден",
                "uk" to "Файл не знайдено",
                "pl" to "Plik nie znaleziony",
                "de" to "Datei nicht gefunden",
                "fr" to "Fichier non trouvé"
            ),
            "folder.create" to mapOf(
                "zh-CN" to "文件夹创建成功",
                "zh-TW" to "資料夾創建成功",
                "en" to "Folder created successfully",
                "ja" to "フォルダが正常に作成されました",
                "ko" to "폴더가 성공적으로 생성되었습니다",
                "vi" to "Thư mục đã được tạo thành công",
                "th" to "สร้างโฟลเดอร์สำเร็จแล้ว",
                "id" to "Folder berhasil dibuat",
                "ms" to "Folder berjaya dicipta",
                "fil" to "Matagumpay na nagawa ang folder",
                "hi" to "फ़ोल्डर सफलतापूर्वक बनाया गया",
                "bn" to "ফোল্ডার সফলভাবে তৈরি হয়েছে",
                "ta" to "கோப்புறை வெற்றிகரமாக உருவாக்கப்பட்டது",
                "te" to "ఫోల్డర్ విజయవంతంగా సృష్టించబడింది",
                "mr" to "फोल्डर यशस्वीरित्या तयार केला",
                "gu" to "ફોલ્ડર સફળતાપૂર્વક બનાવવામાં આવ્યું",
                "kn" to "ಫೋಲ್ಡರ್ ಯಶಸ್ವಿಯಾಗಿ ರಚಿಸಲಾಗಿದೆ",
                "ml" to "ഫോൾഡർ വിജയകരമായി സൃഷ്ടിച്ചു",
                "pa" to "ਫੋਲਡਰ ਸਫਲਤਾਪੂਰਵਕ ਬਣਾਇਆ ਗਿਆ",
                "ar" to "تم إنشاء المجلد بنجاح",
                "fa" to "پوشه با موفقیت ایجاد شد",
                "he" to "התיקייה נוצרה בהצלחה",
                "tr" to "Klasör başarıyla oluşturuldu",
                "ru" to "Папка успешно создана",
                "uk" to "Папку успішно створено",
                "pl" to "Folder został pomyślnie utworzony",
                "de" to "Ordner erfolgreich erstellt",
                "fr" to "Dossier créé avec succès"
            ),
            "error.invalid_path" to mapOf(
                "zh-CN" to "无效的路径",
                "zh-TW" to "無效的路徑",
                "en" to "Invalid path",
                "ja" to "無効なパス",
                "ko" to "잘못된 경로",
                "vi" to "Đường dẫn không hợp lệ",
                "th" to "เส้นทางไม่ถูกต้อง",
                "id" to "Jalur tidak valid",
                "ms" to "Laluan tidak sah",
                "fil" to "Di-wastong path",
                "hi" to "अमान्य पथ",
                "bn" to "অবৈধ পথ",
                "ta" to "தவறான பாதை",
                "te" to "చెల్లని మార్గం",
                "mr" to "अवैध मार्ग",
                "gu" to "અમાન્ય પાથ",
                "kn" to "ಅಮಾನ್ಯ ಮಾರ್ಗ",
                "ml" to "അസാധുവായ പാത്ത്",
                "pa" to "ਅਵੈਧ ਮਾਰਗ",
                "ar" to "مسار غير صالح",
                "fa" to "مسیر نامعتبر",
                "he" to "נתיב לא חוקי",
                "tr" to "Geçersiz yol",
                "ru" to "Неверный путь",
                "uk" to "Невірний шлях",
                "pl" to "Nieprawidłowa ścieżka",
                "de" to "Ungültiger Pfad",
                "fr" to "Chemin invalide"
            ),
            "storage.info" to mapOf(
                "zh-CN" to "存储信息",
                "zh-TW" to "儲存資訊",
                "en" to "Storage Information",
                "ja" to "ストレージ情報",
                "ko" to "저장소 정보",
                "vi" to "Thông tin lưu trữ",
                "th" to "ข้อมูลพื้นที่จัดเก็บ",
                "id" to "Informasi Penyimpanan",
                "ms" to "Maklumat Storan",
                "fil" to "Impormasyon sa Storage",
                "hi" to "भंडारण जानकारी",
                "bn" to "স্টোরেজ তথ্য",
                "ta" to "சேமிப்பு தகவல்",
                "te" to "నిల్వ సమాచారం",
                "mr" to "स्टोरेज माहिती",
                "gu" to "સ્ટોરેજ માહિતી",
                "kn" to "ಸಂಗ್ರಹಣೆ ಮಾಹಿತಿ",
                "ml" to "സ്റ്റോറേജ് വിവരം",
                "pa" to "ਸਟੋਰੇਜ ਜਾਣਕਾਰੀ",
                "ar" to "معلومات التخزين",
                "fa" to "اطلاعات ذخیره‌سازی",
                "he" to "מידע אחסון",
                "tr" to "Depolama Bilgileri",
                "ru" to "Информация о хранилище",
                "uk" to "Інформація про сховище",
                "pl" to "Informacje o pamięci",
                "de" to "Speicherinformationen",
                "fr" to "Informations de stockage"
            ),
            "search.results" to mapOf(
                "zh-CN" to "搜索结果",
                "zh-TW" to "搜尋結果",
                "en" to "Search Results",
                "ja" to "検索結果",
                "ko" to "검색 결과",
                "vi" to "Kết quả tìm kiếm",
                "th" to "ผลการค้นหา",
                "id" to "Hasil Pencarian",
                "ms" to "Hasil Carian",
                "fil" to "Mga Resulta ng Paghahanap",
                "hi" to "खोज परिणाम",
                "bn" to "অনুসন্ধান ফলাফল",
                "ta" to "தேடல் முடிவுகள்",
                "te" to "శోధన ఫలితాలు",
                "mr" to "शोध परिणाम",
                "gu" to "શોધ પરિણામો",
                "kn" to "ಹುಡುಕಾಟ ಫಲಿತಾಂಶಗಳು",
                "ml" to "തിരയൽ ഫലങ്ങൾ",
                "pa" to "ਖੋਜ ਨਤੀਜੇ",
                "ar" to "نتائج البحث",
                "fa" to "نتایج جستجو",
                "he" to "תוצאות חיפוש",
                "tr" to "Arama Sonuçları",
                "ru" to "Результаты поиска",
                "uk" to "Результати пошуку",
                "pl" to "Wyniki wyszukiwania",
                "de" to "Suchergebnisse",
                "fr" to "Résultats de recherche"
            )
        )

        keys.forEach { (key, translationsMap) ->
            translationsMap.forEach { (lang, text) ->
                translations.getOrPut(lang) { mutableMapOf() }[key] = text
            }
        }
    }
}