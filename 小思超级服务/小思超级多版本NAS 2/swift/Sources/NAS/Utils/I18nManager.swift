import Foundation

class I18nManager {
    static let shared = I18nManager()

    let supportedLanguages: [String] = [
        "zh_CN", "zh_TW", "en_US", "en_GB", "ja_JP", "ko_KR",
        "fr_FR", "de_DE", "es_ES", "it_IT", "pt_BR", "ru_RU",
        "ar_SA", "hi_IN", "tr_TR", "th_TH", "vi_VN", "id_ID",
        "nl_NL", "pl_PL", "sv_SE", "da_DK", "fi_FI", "he_IL",
        "hu_HU", "cs_CZ", "uk_UA", "ro_RO"
    ]

    private var translations: [String: [String: String]] = [:]

    private init() {
        loadTranslations()
    }

    private func loadTranslations() {
        translations = [
            "zh_CN": [
                "welcome": "欢迎使用小思NAS服务",
                "server_started": "服务器已启动",
                "volume_created": "存储卷创建成功",
                "volume_deleted": "存储卷删除成功",
                "user_created": "用户创建成功",
                "user_deleted": "用户删除成功",
                "share_created": "共享创建成功",
                "share_deleted": "共享删除成功",
                "push_success": "推送成功",
                "push_failed": "推送失败",
                "scan_complete": "扫描完成",
                "error": "错误",
                "success": "成功"
            ],
            "zh_TW": [
                "welcome": "歡迎使用小思NAS服務",
                "server_started": "伺服器已啟動",
                "volume_created": "儲存卷建立成功",
                "volume_deleted": "儲存卷刪除成功",
                "user_created": "使用者建立成功",
                "user_deleted": "使用者刪除成功",
                "share_created": "共享建立成功",
                "share_deleted": "共享刪除成功",
                "push_success": "推送成功",
                "push_failed": "推送失敗",
                "scan_complete": "掃描完成",
                "error": "錯誤",
                "success": "成功"
            ],
            "en_US": [
                "welcome": "Welcome to Xiaosi NAS Service",
                "server_started": "Server started",
                "volume_created": "Volume created successfully",
                "volume_deleted": "Volume deleted successfully",
                "user_created": "User created successfully",
                "user_deleted": "User deleted successfully",
                "share_created": "Share created successfully",
                "share_deleted": "Share deleted successfully",
                "push_success": "Push successful",
                "push_failed": "Push failed",
                "scan_complete": "Scan complete",
                "error": "Error",
                "success": "Success"
            ],
            "en_GB": [
                "welcome": "Welcome to Xiaosi NAS Service",
                "server_started": "Server started",
                "volume_created": "Volume created successfully",
                "volume_deleted": "Volume deleted successfully",
                "user_created": "User created successfully",
                "user_deleted": "User deleted successfully",
                "share_created": "Share created successfully",
                "share_deleted": "Share deleted successfully",
                "push_success": "Push successful",
                "push_failed": "Push failed",
                "scan_complete": "Scan complete",
                "error": "Error",
                "success": "Success"
            ],
            "ja_JP": [
                "welcome": "Xiaosi NASサービスへようこそ",
                "server_started": "サーバーが起動しました",
                "volume_created": "ボリュームが正常に作成されました",
                "volume_deleted": "ボリュームが正常に削除されました",
                "user_created": "ユーザーが正常に作成されました",
                "user_deleted": "ユーザーが正常に削除されました",
                "share_created": "共有が正常に作成されました",
                "share_deleted": "共有が正常に削除されました",
                "push_success": "プッシュ成功",
                "push_failed": "プッシュ失敗",
                "scan_complete": "スキャン完了",
                "error": "エラー",
                "success": "成功"
            ],
            "ko_KR": [
                "welcome": "Xiaosi NAS 서비스에 오신 것을 환영합니다",
                "server_started": "서버가 시작되었습니다",
                "volume_created": "볼륨이 성공적으로 생성되었습니다",
                "volume_deleted": "볼륨이 성공적으로 삭제되었습니다",
                "user_created": "사용자가 성공적으로 생성되었습니다",
                "user_deleted": "사용자가 성공적으로 삭제되었습니다",
                "share_created": "공유가 성공적으로 생성되었습니다",
                "share_deleted": "공유가 성공적으로 삭제되었습니다",
                "push_success": "푸시 성공",
                "push_failed": "푸시 실패",
                "scan_complete": "스캔 완료",
                "error": "오류",
                "success": "성공"
            ],
            "fr_FR": [
                "welcome": "Bienvenue dans le service NAS Xiaosi",
                "server_started": "Serveur démarré",
                "volume_created": "Volume créé avec succès",
                "volume_deleted": "Volume supprimé avec succès",
                "user_created": "Utilisateur créé avec succès",
                "user_deleted": "Utilisateur supprimé avec succès",
                "share_created": "Partage créé avec succès",
                "share_deleted": "Partage supprimé avec succès",
                "push_success": "Push réussi",
                "push_failed": "Push échoué",
                "scan_complete": "Analyse terminée",
                "error": "Erreur",
                "success": "Succès"
            ],
            "de_DE": [
                "welcome": "Willkommen beim Xiaosi NAS-Dienst",
                "server_started": "Server gestartet",
                "volume_created": "Volume erfolgreich erstellt",
                "volume_deleted": "Volume erfolgreich gelöscht",
                "user_created": "Benutzer erfolgreich erstellt",
                "user_deleted": "Benutzer erfolgreich gelöscht",
                "share_created": "Freigabe erfolgreich erstellt",
                "share_deleted": "Freigabe erfolgreich gelöscht",
                "push_success": "Push erfolgreich",
                "push_failed": "Push fehlgeschlagen",
                "scan_complete": "Scan abgeschlossen",
                "error": "Fehler",
                "success": "Erfolg"
            ],
            "es_ES": [
                "welcome": "Bienvenido al servicio NAS Xiaosi",
                "server_started": "Servidor iniciado",
                "volume_created": "Volumen creado con éxito",
                "volume_deleted": "Volumen eliminado con éxito",
                "user_created": "Usuario creado con éxito",
                "user_deleted": "Usuario eliminado con éxito",
                "share_created": "Recurso compartido creado con éxito",
                "share_deleted": "Recurso compartido eliminado con éxito",
                "push_success": "Push exitoso",
                "push_failed": "Push fallido",
                "scan_complete": "Escaneo completado",
                "error": "Error",
                "success": "Éxito"
            ],
            "it_IT": [
                "welcome": "Benvenuto nel servizio NAS Xiaosi",
                "server_started": "Server avviato",
                "volume_created": "Volume creato con successo",
                "volume_deleted": "Volume eliminato con successo",
                "user_created": "Utente creato con successo",
                "user_deleted": "Utente eliminato con successo",
                "share_created": "Condivisione creata con successo",
                "share_deleted": "Condivisione eliminata con successo",
                "push_success": "Push riuscito",
                "push_failed": "Push fallito",
                "scan_complete": "Scansione completata",
                "error": "Errore",
                "success": "Successo"
            ],
            "pt_BR": [
                "welcome": "Bem-vindo ao serviço NAS Xiaosi",
                "server_started": "Servidor iniciado",
                "volume_created": "Volume criado com sucesso",
                "volume_deleted": "Volume excluído com sucesso",
                "user_created": "Usuário criado com sucesso",
                "user_deleted": "Usuário excluído com sucesso",
                "share_created": "Compartilhamento criado com sucesso",
                "share_deleted": "Compartilhamento excluído com sucesso",
                "push_success": "Push bem-sucedido",
                "push_failed": "Push falhou",
                "scan_complete": "Verificação concluída",
                "error": "Erro",
                "success": "Sucesso"
            ],
            "ru_RU": [
                "welcome": "Добро пожаловать в сервис NAS Xiaosi",
                "server_started": "Сервер запущен",
                "volume_created": "Том успешно создан",
                "volume_deleted": "Том успешно удален",
                "user_created": "Пользователь успешно создан",
                "user_deleted": "Пользователь успешно удален",
                "share_created": "Общий ресурс успешно создан",
                "share_deleted": "Общий ресурс успешно удален",
                "push_success": "Push успешно отправлен",
                "push_failed": "Push не удался",
                "scan_complete": "Сканирование завершено",
                "error": "Ошибка",
                "success": "Успешно"
            ],
            "ar_SA": [
                "welcome": "مرحبًا بك في خدمة NAS Xiaosi",
                "server_started": "تم بدء الخادم",
                "volume_created": "تم إنشاء الحجم بنجاح",
                "volume_deleted": "تم حذف الحجم بنجاح",
                "user_created": "تم إنشاء المستخدم بنجاح",
                "user_deleted": "تم حذف المستخدم بنجاح",
                "share_created": "تم إنشاء المشاركة بنجاح",
                "share_deleted": "تم حذف المشاركة بنجاح",
                "push_success": "نجح الدفع",
                "push_failed": "فشل الدفع",
                "scan_complete": "اكتمل الفحص",
                "error": "خطأ",
                "success": "نجاح"
            ],
            "hi_IN": [
                "welcome": "Xiaosi NAS सेवा में आपका स्वागत है",
                "server_started": "सर्वर शुरू हो गया",
                "volume_created": "वॉल्यूम सफलतापूर्वक बनाया गया",
                "volume_deleted": "वॉल्यूम सफलतापूर्वक हटाया गया",
                "user_created": "उपयोगकर्ता सफलतापूर्वक बनाया गया",
                "user_deleted": "उपयोगकर्ता सफलतापूर्वक हटाया गया",
                "share_created": "शेयर सफलतापूर्वक बनाया गया",
                "share_deleted": "शेयर सफलतापूर्वक हटाया गया",
                "push_success": "पुश सफल",
                "push_failed": "पुश विफल",
                "scan_complete": "स्कैन पूर्ण",
                "error": "त्रुटि",
                "success": "सफलता"
            ],
            "tr_TR": [
                "welcome": "Xiaosi NAS hizmetine hoş geldiniz",
                "server_started": "Sunucu başlatıldı",
                "volume_created": "Birim başarıyla oluşturuldu",
                "volume_deleted": "Birim başarıyla silindi",
                "user_created": "Kullanıcı başarıyla oluşturuldu",
                "user_deleted": "Kullanıcı başarıyla silindi",
                "share_created": "Paylaşım başarıyla oluşturuldu",
                "share_deleted": "Paylaşım başarıyla silindi",
                "push_success": "Gönderme başarılı",
                "push_failed": "Gönderme başarısız",
                "scan_complete": "Tarama tamamlandı",
                "error": "Hata",
                "success": "Başarı"
            ],
            "th_TH": [
                "welcome": "ยินดีต้อนรับสู่บริการ NAS Xiaosi",
                "server_started": "เซิร์ฟเวอร์เริ่มทำงานแล้ว",
                "volume_created": "สร้างโวลุ่มสำเร็จแล้ว",
                "volume_deleted": "ลบโวลุ่มสำเร็จแล้ว",
                "user_created": "สร้างผู้ใช้สำเร็จแล้ว",
                "user_deleted": "ลบผู้ใช้สำเร็จแล้ว",
                "share_created": "สร้างการแชร์สำเร็จแล้ว",
                "share_deleted": "ลบการแชร์สำเร็จแล้ว",
                "push_success": "ส่งสำเร็จ",
                "push_failed": "ส่งล้มเหลว",
                "scan_complete": "สแกนเสร็จสมบูรณ์",
                "error": "ข้อผิดพลาด",
                "success": "สำเร็จ"
            ],
            "vi_VN": [
                "welcome": "Chào mừng đến với dịch vụ NAS Xiaosi",
                "server_started": "Máy chủ đã khởi động",
                "volume_created": "Tạo ổ đĩa thành công",
                "volume_deleted": "Xóa ổ đĩa thành công",
                "user_created": "Tạo người dùng thành công",
                "user_deleted": "Xóa người dùng thành công",
                "share_created": "Tạo chia sẻ thành công",
                "share_deleted": "Xóa chia sẻ thành công",
                "push_success": "Gửi thành công",
                "push_failed": "Gửi thất bại",
                "scan_complete": "Quét hoàn tất",
                "error": "Lỗi",
                "success": "Thành công"
            ],
            "id_ID": [
                "welcome": "Selamat datang di layanan NAS Xiaosi",
                "server_started": "Server dimulai",
                "volume_created": "Volume berhasil dibuat",
                "volume_deleted": "Volume berhasil dihapus",
                "user_created": "Pengguna berhasil dibuat",
                "user_deleted": "Pengguna berhasil dihapus",
                "share_created": "Berbagi berhasil dibuat",
                "share_deleted": "Berbagi berhasil dihapus",
                "push_success": "Push berhasil",
                "push_failed": "Push gagal",
                "scan_complete": "Pemindaian selesai",
                "error": "Kesalahan",
                "success": "Berhasil"
            ],
            "nl_NL": [
                "welcome": "Welkom bij de NAS-service van Xiaosi",
                "server_started": "Server gestart",
                "volume_created": "Volume succesvol aangemaakt",
                "volume_deleted": "Volume succesvol verwijderd",
                "user_created": "Gebruiker succesvol aangemaakt",
                "user_deleted": "Gebruiker succesvol verwijderd",
                "share_created": "Share succesvol aangemaakt",
                "share_deleted": "Share succesvol verwijderd",
                "push_success": "Push succesvol",
                "push_failed": "Push mislukt",
                "scan_complete": "Scan voltooid",
                "error": "Fout",
                "success": "Succes"
            ],
            "pl_PL": [
                "welcome": "Witamy w usłudze NAS Xiaosi",
                "server_started": "Serwer uruchomiony",
                "volume_created": "Wolumen został pomyślnie utworzony",
                "volume_deleted": "Wolumen został pomyślnie usunięty",
                "user_created": "Użytkownik został pomyślnie utworzony",
                "user_deleted": "Użytkownik został pomyślnie usunięty",
                "share_created": "Udział został pomyślnie utworzony",
                "share_deleted": "Udział został pomyślnie usunięty",
                "push_success": "Push pomyślny",
                "push_failed": "Push nie powiódł się",
                "scan_complete": "Skanowanie zakończone",
                "error": "Błąd",
                "success": "Sukces"
            ],
            "sv_SE": [
                "welcome": "Välkommen till Xiaosi NAS-tjänst",
                "server_started": "Server startad",
                "volume_created": "Volym skapad framgångsrikt",
                "volume_deleted": "Volym raderad framgångsrikt",
                "user_created": "Användare skapad framgångsrikt",
                "user_deleted": "Användare raderad framgångsrikt",
                "share_created": "Share skapad framgångsrikt",
                "share_deleted": "Share raderad framgångsrikt",
                "push_success": "Push framgångsrik",
                "push_failed": "Push misslyckades",
                "scan_complete": "Skanning slutförd",
                "error": "Fel",
                "success": "Framgång"
            ],
            "da_DK": [
                "welcome": "Velkommen til Xiaosi NAS-tjeneste",
                "server_started": "Server startet",
                "volume_created": "Volume oprettet succesfuldt",
                "volume_deleted": "Volume slettet succesfuldt",
                "user_created": "Bruger oprettet succesfuldt",
                "user_deleted": "Bruger slettet succesfuldt",
                "share_created": "Share oprettet succesfuldt",
                "share_deleted": "Share slettet succesfuldt",
                "push_success": "Push succesfuld",
                "push_failed": "Push mislykkedes",
                "scan_complete": "Scanning afsluttet",
                "error": "Fejl",
                "success": "Succes"
            ],
            "fi_FI": [
                "welcome": "Tervetuloa Xiaosi NAS-palveluun",
                "server_started": "Palvelin käynnistetty",
                "volume_created": "Taltio luotu onnistuneesti",
                "volume_deleted": "Taltio poistettu onnistuneesti",
                "user_created": "Käyttäjä luotu onnistuneesti",
                "user_deleted": "Käyttäjä poistettu onnistuneesti",
                "share_created": "Jako luotu onnistuneesti",
                "share_deleted": "Jako poistettu onnistuneesti",
                "push_success": "Push onnistui",
                "push_failed": "Push epäonnistui",
                "scan_complete": "Skannaus valmis",
                "error": "Virhe",
                "success": "Onnistui"
            ],
            "he_IL": [
                "welcome": "ברוכים הבאים לשירות NAS של Xiaosi",
                "server_started": "השרת הופעל",
                "volume_created": "האמצעי נוצר בהצלחה",
                "volume_deleted": "האמצעי נמחק בהצלחה",
                "user_created": "המשתמש נוצר בהצלחה",
                "user_deleted": "המשתמש נמחק בהצלחה",
                "share_created": "השיתוף נוצר בהצלחה",
                "share_deleted": "השיתוף נמחק בהצלחה",
                "push_success": "דחיפה הצליחה",
                "push_failed": "דחיפה נכשלה",
                "scan_complete": "הסריקה הושלמה",
                "error": "שגיאה",
                "success": "הצלחה"
            ],
            "hu_HU": [
                "welcome": "Üdvözöljük a Xiaosi NAS szolgáltatásban",
                "server_started": "Szerver elindítva",
                "volume_created": "Kötet sikeresen létrehozva",
                "volume_deleted": "Kötet sikeresen törölve",
                "user_created": "Felhasználó sikeresen létrehozva",
                "user_deleted": "Felhasználó sikeresen törölve",
                "share_created": "Megosztás sikeresen létrehozva",
                "share_deleted": "Megosztás sikeresen törölve",
                "push_success": "Push sikeres",
                "push_failed": "Push sikertelen",
                "scan_complete": "Vizsgálat befejezve",
                "error": "Hiba",
                "success": "Siker"
            ],
            "cs_CZ": [
                "welcome": "Vítejte ve službě NAS Xiaosi",
                "server_started": "Server spuštěn",
                "volume_created": "Svazek úspěšně vytvořen",
                "volume_deleted": "Svazek úspěšně smazán",
                "user_created": "Uživatel úspěšně vytvořen",
                "user_deleted": "Uživatel úspěšně smazán",
                "share_created": "Sdílení úspěšně vytvořeno",
                "share_deleted": "Sdílení úspěšně smazáno",
                "push_success": "Push úspěšný",
                "push_failed": "Push neúspěšný",
                "scan_complete": "Skenování dokončeno",
                "error": "Chyba",
                "success": "Úspěch"
            ],
            "uk_UA": [
                "welcome": "Ласкаво просимо до служби NAS Xiaosi",
                "server_started": "Сервер запущено",
                "volume_created": "Том успішно створено",
                "volume_deleted": "Том успішно видалено",
                "user_created": "Користувача успішно створено",
                "user_deleted": "Користувача успішно видалено",
                "share_created": "Спільний ресурс успішно створено",
                "share_deleted": "Спільний ресурс успішно видалено",
                "push_success": "Push успішно відправлено",
                "push_failed": "Push не вдався",
                "scan_complete": "Сканування завершено",
                "error": "Помилка",
                "success": "Успішно"
            ],
            "ro_RO": [
                "welcome": "Bine ați venit la serviciul NAS Xiaosi",
                "server_started": "Server pornit",
                "volume_created": "Volum creat cu succes",
                "volume_deleted": "Volum șters cu succes",
                "user_created": "Utilizator creat cu succes",
                "user_deleted": "Utilizator șters cu succes",
                "share_created": "Partajare creată cu succes",
                "share_deleted": "Partajare ștearsă cu succes",
                "push_success": "Push reușit",
                "push_failed": "Push eșuat",
                "scan_complete": "Scanare completă",
                "error": "Eroare",
                "success": "Succes"
            ]
        ]
    }

    func translate(_ key: String, lang: String? = nil) -> String {
        let language = lang ?? ConfigManager.shared.config.server.language
        if let trans = translations[language], let text = trans[key] {
            return text
        }
        if let trans = translations["en_US"], let text = trans[key] {
            return text
        }
        return key
    }

    func getAllTranslations(for lang: String) -> [String: String] {
        return translations[lang] ?? translations["en_US"] ?? [:]
    }
}