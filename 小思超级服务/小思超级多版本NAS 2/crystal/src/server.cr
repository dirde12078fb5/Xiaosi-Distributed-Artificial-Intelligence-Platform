require "kemal"
require "json"
require "file_utils"
require "socket"
require "digest/sha2"
require "random/secure"
require "time"

# ==================== 常量定义 ====================
BASE_DIR = File.dirname(File.dirname(__DIR__))
CONFIG_PATH = File.join(BASE_DIR, "config", "config.json")
DATA_DIR = File.join(BASE_DIR, "nas_data")
RECEIVE_DIR = File.join(DATA_DIR, "received")
I18N_DIR = File.join(BASE_DIR, "config", "i18n")

# ==================== 配置加载 ====================
def load_config : JSON::Any
  if File.exists?(CONFIG_PATH)
    JSON.parse(File.read(CONFIG_PATH))
  else
    JSON.parse({
      "server" => {"port" => 8096, "language" => "zh_CN"},
      "storage" => {"volumes" => []},
      "users" => [] of JSON::Any,
      "smb" => {"shares" => [] of JSON::Any},
      "push" => {"targets" => [] of JSON::Any},
      "data_dir" => "nas_data",
      "receive_dir" => "nas_data/received"
    }.to_json)
  end
end

def save_config(config : JSON::Any)
  File.write(CONFIG_PATH, config.to_json)
end

CONFIG = load_config

# ==================== I18N翻译系统（28种语言） ====================
I18N = {
  zh_CN: {
    welcome: "欢迎使用小思NAS服务",
    storage_management: "存储管理",
    user_management: "用户管理",
    smb_shares: "SMB共享",
    push_files: "推送文件",
    success: "操作成功",
    failed: "操作失败",
    not_found: "资源未找到",
    invalid_params: "参数无效",
    volume_created: "存储卷创建成功",
    volume_deleted: "存储卷删除成功",
    user_created: "用户创建成功",
    user_deleted: "用户删除成功",
    share_created: "共享创建成功",
    share_deleted: "共享删除成功",
    push_started: "推送启动",
    push_completed: "推送完成",
    push_failed: "推送失败",
    file_received: "文件接收成功",
    scan_completed: "扫描完成",
    no_devices: "未发现设备",
    running: "运行中",
    stopped: "已停止",
    yes: "是",
    no: "否",
    delete: "删除",
    no_data: "暂无数据",
    online: "在线",
    add_target: "添加",
    pushing: "推送中",
    push_now: "立即推送",
    app_name: "小思超级NAS"
  },
  zh_TW: {
    welcome: "歡迎使用小思NAS服務",
    storage_management: "存儲管理",
    user_management: "用戶管理",
    smb_shares: "SMB共享",
    push_files: "推送文件",
    success: "操作成功",
    failed: "操作失敗",
    not_found: "資源未找到",
    invalid_params: "參數無效",
    volume_created: "存儲卷創建成功",
    volume_deleted: "存儲卷刪除成功",
    user_created: "用戶創建成功",
    user_deleted: "用戶刪除成功",
    share_created: "共享創建成功",
    share_deleted: "共享刪除成功",
    push_started: "推送啟動",
    push_completed: "推送完成",
    push_failed: "推送失敗",
    file_received: "文件接收成功",
    scan_completed: "掃描完成",
    no_devices: "未發現設備"
  },
  en_US: {
    welcome: "Welcome to Xiaosi NAS Service",
    storage_management: "Storage Management",
    user_management: "User Management",
    smb_shares: "SMB Shares",
    push_files: "Push Files",
    success: "Operation successful",
    failed: "Operation failed",
    not_found: "Resource not found",
    invalid_params: "Invalid parameters",
    volume_created: "Storage volume created",
    volume_deleted: "Storage volume deleted",
    user_created: "User created",
    user_deleted: "User deleted",
    share_created: "Share created",
    share_deleted: "Share deleted",
    push_started: "Push started",
    push_completed: "Push completed",
    push_failed: "Push failed",
    file_received: "File received",
    scan_completed: "Scan completed",
    no_devices: "No devices found"
  },
  en_GB: {
    welcome: "Welcome to Xiaosi NAS Service",
    storage_management: "Storage Management",
    user_management: "User Management",
    smb_shares: "SMB Shares",
    push_files: "Push Files",
    success: "Operation successful",
    failed: "Operation failed",
    not_found: "Resource not found",
    invalid_params: "Invalid parameters",
    volume_created: "Storage volume created",
    volume_deleted: "Storage volume deleted",
    user_created: "User created",
    user_deleted: "User deleted",
    share_created: "Share created",
    share_deleted: "Share deleted",
    push_started: "Push started",
    push_completed: "Push completed",
    push_failed: "Push failed",
    file_received: "File received",
    scan_completed: "Scan completed",
    no_devices: "No devices found"
  },
  ja_JP: {
    welcome: "Xiaosi NASサービスへようこそ",
    storage_management: "ストレージ管理",
    user_management: "ユーザー管理",
    smb_shares: "SMB共有",
    push_files: "ファイル送信",
    success: "操作成功",
    failed: "操作失敗",
    not_found: "リソースが見つかりません",
    invalid_params: "無効なパラメータ",
    volume_created: "ストレージボリューム作成成功",
    volume_deleted: "ストレージボリューム削除成功",
    user_created: "ユーザー作成成功",
    user_deleted: "ユーザー削除成功",
    share_created: "共有作成成功",
    share_deleted: "共有削除成功",
    push_started: "送信開始",
    push_completed: "送信完了",
    push_failed: "送信失敗",
    file_received: "ファイル受信成功",
    scan_completed: "スキャン完了",
    no_devices: "デバイス未検出"
  },
  ko_KR: {
    welcome: "Xiaosi NAS 서비스에 오신 것을 환영합니다",
    storage_management: "저장소 관리",
    user_management: "사용자 관리",
    smb_shares: "SMB 공유",
    push_files: "파일 전송",
    success: "작업 성공",
    failed: "작업 실패",
    not_found: "리소스를 찾을 수 없습니다",
    invalid_params: "잘못된 매개변수",
    volume_created: "저장소 볼륨 생성 성공",
    volume_deleted: "저장소 볼륨 삭제 성공",
    user_created: "사용자 생성 성공",
    user_deleted: "사용자 삭제 성공",
    share_created: "공유 생성 성공",
    share_deleted: "공유 삭제 성공",
    push_started: "전송 시작",
    push_completed: "전송 완료",
    push_failed: "전송 실패",
    file_received: "파일 수신 성공",
    scan_completed: "스캔 완료",
    no_devices: "장치를 찾을 수 없습니다"
  },
  fr_FR: {
    welcome: "Bienvenue dans le service NAS Xiaosi",
    storage_management: "Gestion du stockage",
    user_management: "Gestion des utilisateurs",
    smb_shares: "Partages SMB",
    push_files: "Push fichiers",
    success: "Opération réussie",
    failed: "Opération échouée",
    not_found: "Ressource non trouvée",
    invalid_params: "Paramètres invalides",
    volume_created: "Volume de stockage créé",
    volume_deleted: "Volume de stockage supprimé",
    user_created: "Utilisateur créé",
    user_deleted: "Utilisateur supprimé",
    share_created: "Partage créé",
    share_deleted: "Partage supprimé",
    push_started: "Push commencé",
    push_completed: "Push terminé",
    push_failed: "Push échoué",
    file_received: "Fichier reçu",
    scan_completed: "Scan terminé",
    no_devices: "Aucun appareil détecté"
  },
  de_DE: {
    welcome: "Willkommen beim Xiaosi NAS-Service",
    storage_management: "Speicherverwaltung",
    user_management: "Benutzerverwaltung",
    smb_shares: "SMB-Freigaben",
    push_files: "Dateien senden",
    success: "Operation erfolgreich",
    failed: "Operation fehlgeschlagen",
    not_found: "Ressource nicht gefunden",
    invalid_params: "Ungültige Parameter",
    volume_created: "Speichervolume erstellt",
    volume_deleted: "Speichervolume gelöscht",
    user_created: "Benutzer erstellt",
    user_deleted: "Benutzer gelöscht",
    share_created: "Freigabe erstellt",
    share_deleted: "Freigabe gelöscht",
    push_started: "Push gestartet",
    push_completed: "Push abgeschlossen",
    push_failed: "Push fehlgeschlagen",
    file_received: "Datei empfangen",
    scan_completed: "Scan abgeschlossen",
    no_devices: "Keine Geräte gefunden"
  },
  es_ES: {
    welcome: "Bienvenido al servicio NAS Xiaosi",
    storage_management: "Gestión de almacenamiento",
    user_management: "Gestión de usuarios",
    smb_shares: "Compartidos SMB",
    push_files: "Enviar archivos",
    success: "Operación exitosa",
    failed: "Operación fallida",
    not_found: "Recurso no encontrado",
    invalid_params: "Parámetros inválidos",
    volume_created: "Volumen de almacenamiento creado",
    volume_deleted: "Volumen de almacenamiento eliminado",
    user_created: "Usuario creado",
    user_deleted: "Usuario eliminado",
    share_created: "Compartido creado",
    share_deleted: "Compartido eliminado",
    push_started: "Push iniciado",
    push_completed: "Push completado",
    push_failed: "Push fallido",
    file_received: "Archivo recibido",
    scan_completed: "Escaneo completado",
    no_devices: "No se encontraron dispositivos"
  },
  it_IT: {
    welcome: "Benvenuto nel servizio NAS Xiaosi",
    storage_management: "Gestione storage",
    user_management: "Gestione utenti",
    smb_shares: "Condivisioni SMB",
    push_files: "Invia file",
    success: "Operazione riuscita",
    failed: "Operazione fallita",
    not_found: "Risorsa non trovata",
    invalid_params: "Parametri non validi",
    volume_created: "Volume storage creato",
    volume_deleted: "Volume storage eliminato",
    user_created: "Utente creato",
    user_deleted: "Utente eliminato",
    share_created: "Condivisione creata",
    share_deleted: "Condivisione eliminata",
    push_started: "Push iniziato",
    push_completed: "Push completato",
    push_failed: "Push fallito",
    file_received: "File ricevuto",
    scan_completed: "Scansione completata",
    no_devices: "Nessun dispositivo trovato"
  },
  pt_PT: {
    welcome: "Bem-vindo ao serviço NAS Xiaosi",
    storage_management: "Gestão de armazenamento",
    user_management: "Gestão de usuários",
    smb_shares: "Partilhas SMB",
    push_files: "Enviar arquivos",
    success: "Operação bem-sucedida",
    failed: "Operação falhou",
    not_found: "Recurso não encontrado",
    invalid_params: "Parâmetros inválidos",
    volume_created: "Volume de armazenamento criado",
    volume_deleted: "Volume de armazenamento eliminado",
    user_created: "Usuário criado",
    user_deleted: "Usuário eliminado",
    share_created: "Partilha criada",
    share_deleted: "Partilha eliminada",
    push_started: "Push iniciado",
    push_completed: "Push concluído",
    push_failed: "Push falhou",
    file_received: "Arquivo recebido",
    scan_completed: "Scan concluído",
    no_devices: "Nenhum dispositivo encontrado"
  },
  ru_RU: {
    welcome: "Добро пожаловать в сервис NAS Xiaosi",
    storage_management: "Управление хранилищем",
    user_management: "Управление пользователями",
    smb_shares: "SMB-ресурсы",
    push_files: "Отправка файлов",
    success: "Операция успешна",
    failed: "Операция не удалась",
    not_found: "Ресурс не найден",
    invalid_params: "Неверные параметры",
    volume_created: "Объем хранилища создан",
    volume_deleted: "Объем хранилища удален",
    user_created: "Пользователь создан",
    user_deleted: "Пользователь удален",
    share_created: "Ресурс создан",
    share_deleted: "Ресурс удален",
    push_started: "Отправка началась",
    push_completed: "Отправка завершена",
    push_failed: "Отправка не удалась",
    file_received: "Файл получен",
    scan_completed: "Сканирование завершено",
    no_devices: "Устройства не найдены"
  },
  ar_SA: {
    welcome: "مرحباً بك في خدمة NAS Xiaosi",
    storage_management: "إدارة التخزين",
    user_management: "إدارة المستخدمين",
    smb_shares: "مشاركات SMB",
    push_files: "إرسال الملفات",
    success: "تمت العملية بنجاح",
    failed: "فشلت العملية",
    not_found: "المورد غير موجود",
    invalid_params: "معاملات غير صالحة",
    volume_created: "تم إنشاء حجم التخزين",
    volume_deleted: "تم حذف حجم التخزين",
    user_created: "تم إنشاء المستخدم",
    user_deleted: "تم حذف المستخدم",
    share_created: "تم إنشاء المشاركة",
    share_deleted: "تم حذف المشاركة",
    push_started: "بدء الإرسال",
    push_completed: "تم الإرسال",
    push_failed: "فشل الإرسال",
    file_received: "تم استلام الملف",
    scan_completed: "تم الفحص",
    no_devices: "لم يتم العثور على أجهزة"
  },
  hi_IN: {
    welcome: "Xiaosi NAS सेवा में आपका स्वागत है",
    storage_management: "संग्रह प्रबंधन",
    user_management: "उपयोगकर्ता प्रबंधन",
    smb_shares: "SMB शेयर",
    push_files: "फ़ाइलें भेजें",
    success: "ऑपरेशन सफल",
    failed: "ऑपरेशन विफल",
    not_found: "संसाधन नहीं मिला",
    invalid_params: "अमान्य पैरामीटर",
    volume_created: "संग्रह वॉल्यूम बनाया गया",
    volume_deleted: "संग्रह वॉल्यूम हटाया गया",
    user_created: "उपयोगकर्ता बनाया गया",
    user_deleted: "उपयोगकर्ता हटाया गया",
    share_created: "शेयर बनाया गया",
    share_deleted: "शेयर हटाया गया",
    push_started: "पुश शुरू हुआ",
    push_completed: "पुश पूर्ण",
    push_failed: "पुश विफल",
    file_received: "फ़ाइल प्राप्त",
    scan_completed: "स्कैन पूर्ण",
    no_devices: "कोई डिवाइस नहीं मिला"
  },
  tr_TR: {
    welcome: "Xiaosi NAS Hizmetine Hoş Geldiniz",
    storage_management: "Depolama Yönetimi",
    user_management: "Kullanıcı Yönetimi",
    smb_shares: "SMB Paylaşımları",
    push_files: "Dosya Gönder",
    success: "İşlem başarılı",
    failed: "İşlem başarısız",
    not_found: "Kaynak bulunamadı",
    invalid_params: "Geçersiz parametreler",
    volume_created: "Depolama hacmi oluşturuldu",
    volume_deleted: "Depolama hacmi silindi",
    user_created: "Kullanıcı oluşturuldu",
    user_deleted: "Kullanıcı silindi",
    share_created: "Paylaşım oluşturuldu",
    share_deleted: "Paylaşım silindi",
    push_started: "Gönderme başladı",
    push_completed: "Gönderme tamamlandı",
    push_failed: "Gönderme başarısız",
    file_received: "Dosya alındı",
    scan_completed: "Tarama tamamlandı",
    no_devices: "Cihaz bulunamadı"
  },
  th_TH: {
    welcome: "ยินดีต้อนรับสู่บริการ NAS Xiaosi",
    storage_management: "การจัดการพื้นที่จัดเก็บ",
    user_management: "การจัดการผู้ใช้",
    smb_shares: "การแชร์ SMB",
    push_files: "ส่งไฟล์",
    success: "ดำเนินการสำเร็จ",
    failed: "ดำเนินการไม่สำเร็จ",
    not_found: "ไม่พบทรัพยากร",
    invalid_params: "พารามิเตอร์ไม่ถูกต้อง",
    volume_created: "สร้างพื้นที่จัดเก็บสำเร็จ",
    volume_deleted: "ลบพื้นที่จัดเก็บสำเร็จ",
    user_created: "สร้างผู้ใช้สำเร็จ",
    user_deleted: "ลบผู้ใช้สำเร็จ",
    share_created: "สร้างการแชร์สำเร็จ",
    share_deleted: "ลบการแชร์สำเร็จ",
    push_started: "เริ่มส่ง",
    push_completed: "ส่งเสร็จสิ้น",
    push_failed: "ส่งไม่สำเร็จ",
    file_received: "ไฟล์ได้รับ",
    scan_completed: "สแกนเสร็จสิ้น",
    no_devices: "ไม่พบอุปกรณ์"
  },
  vi_VN: {
    welcome: "Chào mừng đến với dịch vụ NAS Xiaosi",
    storage_management: "Quản lý lưu trữ",
    user_management: "Quản lý người dùng",
    smb_shares: "Chia sẻ SMB",
    push_files: "Gửi tệp",
    success: "Thao tác thành công",
    failed: "Thao tác thất bại",
    not_found: "Không tìm thấy tài nguyên",
    invalid_params: "Tham số không hợp lệ",
    volume_created: "Tạo volume lưu trữ thành công",
    volume_deleted: "Xóa volume lưu trữ thành công",
    user_created: "Tạo người dùng thành công",
    user_deleted: "Xóa người dùng thành công",
    share_created: "Tạo chia sẻ thành công",
    share_deleted: "Xóa chia sẻ thành công",
    push_started: "Bắt đầu gửi",
    push_completed: "Gửi hoàn tất",
    push_failed: "Gửi thất bại",
    file_received: "Tệp đã nhận",
    scan_completed: "Quét hoàn tất",
    no_devices: "Không tìm thấy thiết bị"
  },
  id_ID: {
    welcome: "Selamat datang di layanan NAS Xiaosi",
    storage_management: "Manajemen Storage",
    user_management: "Manajemen Pengguna",
    smb_shares: "Share SMB",
    push_files: "Kirim File",
    success: "Operasi berhasil",
    failed: "Operasi gagal",
    not_found: "Resource tidak ditemukan",
    invalid_params: "Parameter tidak valid",
    volume_created: "Volume storage berhasil dibuat",
    volume_deleted: "Volume storage berhasil dihapus",
    user_created: "Pengguna berhasil dibuat",
    user_deleted: "Pengguna berhasil dihapus",
    share_created: "Share berhasil dibuat",
    share_deleted: "Share berhasil dihapus",
    push_started: "Push dimulai",
    push_completed: "Push selesai",
    push_failed: "Push gagal",
    file_received: "File diterima",
    scan_completed: "Scan selesai",
    no_devices: "Tidak ada device ditemukan"
  },
  nl_NL: {
    welcome: "Welkom bij de Xiaosi NAS-service",
    storage_management: "Opslagbeheer",
    user_management: "Gebruikersbeheer",
    smb_shares: "SMB-shares",
    push_files: "Bestanden verzenden",
    success: "Operatie succesvol",
    failed: "Operatie mislukt",
    not_found: "Resource niet gevonden",
    invalid_params: "Ongeldige parameters",
    volume_created: "Opslagvolume succesvol gemaakt",
    volume_deleted: "Opslagvolume succesvol verwijderd",
    user_created: "Gebruiker succesvol gemaakt",
    user_deleted: "Gebruiker succesvol verwijderd",
    share_created: "Share succesvol gemaakt",
    share_deleted: "Share succesvol verwijderd",
    push_started: "Verzenden gestart",
    push_completed: "Verzenden voltooid",
    push_failed: "Verzenden mislukt",
    file_received: "Bestand succesvol ontvangen",
    scan_completed: "Scan voltooid",
    no_devices: "Geen apparaten gevonden"
  },
  pl_PL: {
    welcome: "Witamy w usłudze NAS Xiaosi",
    storage_management: "Zarządzanie przechowywaniem",
    user_management: "Zarządzanie użytkownikami",
    smb_shares: "Udziały SMB",
    push_files: "Wyślij pliki",
    success: "Operacja zakończona sukcesem",
    failed: "Operacja nie powiodła się",
    not_found: "Nie znaleziono zasobu",
    invalid_params: "Nieprawidłowe parametry",
    volume_created: "Wolumin przechowywania utworzony",
    volume_deleted: "Wolumin przechowywania usunięty",
    user_created: "Użytkownik utworzony",
    user_deleted: "Użytkownik usunięty",
    share_created: "Udział utworzony",
    share_deleted: "Udział usunięty",
    push_started: "Wysyłanie rozpoczęte",
    push_completed: "Wysyłanie zakończone",
    push_failed: "Wysyłanie nie powiodło się",
    file_received: "Plik odebrany",
    scan_completed: "Skanowanie zakończone",
    no_devices: "Nie znaleziono urządzeń"
  },
  uk_UA: {
    welcome: "Ласкаво просимо до сервісу NAS Xiaosi",
    storage_management: "Управління сховищем",
    user_management: "Управління користувачами",
    smb_shares: "SMB-ресурси",
    push_files: "Надсилання файлів",
    success: "Операція успішна",
    failed: "Операція не вдалася",
    not_found: "Ресурс не знайдено",
    invalid_params: "Невірні параметри",
    volume_created: "Обсяг сховища створено",
    volume_deleted: "Обсяг сховища видалено",
    user_created: "Користувач створений",
    user_deleted: "Користувач видалений",
    share_created: "Ресурс створено",
    share_deleted: "Ресурс видалено",
    push_started: "Надсилання почалось",
    push_completed: "Надсилання завершено",
    push_failed: "Надсилання не вдалось",
    file_received: "Файл отримано",
    scan_completed: "Сканування завершено",
    no_devices: "Пристрої не знайдені"
  },
  cs_CZ: {
    welcome: "Vítejte ve službě NAS Xiaosi",
    storage_management: "Správa úložiště",
    user_management: "Správa uživatelů",
    smb_shares: "SMB sdílení",
    push_files: "Odeslat soubory",
    success: "Operace úspěšná",
    failed: "Operace neúspěšná",
    not_found: "Zdroj nenalezen",
    invalid_params: "Neplatné parametry",
    volume_created: "Svazek úložiště vytvořen",
    volume_deleted: "Svazek úložiště odstraněn",
    user_created: "Uživatel vytvořen",
    user_deleted: "Uživatel odstraněn",
    share_created: "Sdílení vytvořeno",
    share_deleted: "Sdílení odstraněno",
    push_started: "Odesílání zahájeno",
    push_completed: "Odesílání dokončeno",
    push_failed: "Odesílání selhalo",
    file_received: "Soubor přijat",
    scan_completed: "Skenování dokončeno",
    no_devices: "Žádné zařízení nenalezeno"
  },
  sv_SE: {
    welcome: "Välkommen till Xiaosi NAS-tjänst",
    storage_management: "Lagringshantering",
    user_management: "Användarhantering",
    smb_shares: "SMB-utdelningar",
    push_files: "Skicka filer",
    success: "Åtgärd lyckades",
    failed: "Åtgärd misslyckades",
    not_found: "Resursen hittades inte",
    invalid_params: "Ogiltiga parametrar",
    volume_created: "Lagringsvolym skapad",
    volume_deleted: "Lagringsvolym borttagen",
    user_created: "Användare skapad",
    user_deleted: "Användare borttagen",
    share_created: "Utdelning skapad",
    share_deleted: "Utdelning borttagen",
    push_started: "Sändning startad",
    push_completed: "Sändning slutförd",
    push_failed: "Sändning misslyckades",
    file_received: "Fil mottagen",
    scan_completed: "Skanning slutförd",
    no_devices: "Inga enheter hittades"
  },
  da_DK: {
    welcome: "Velkommen til Xiaosi NAS-tjeneste",
    storage_management: "Lagerstyring",
    user_management: "Brugerstyring",
    smb_shares: "SMB-delinger",
    push_files: "Send filer",
    success: "Handling lykkedes",
    failed: "Handling mislykkedes",
    not_found: "Ressource ikke fundet",
    invalid_params: "Ugyldige parametre",
    volume_created: "Lagervolume oprettet",
    volume_deleted: "Lagervolume slettet",
    user_created: "Bruger oprettet",
    user_deleted: "Bruger slettet",
    share_created: "Deling oprettet",
    share_deleted: "Deling slettet",
    push_started: "Afsendelse startet",
    push_completed: "Afsendelse afsluttet",
    push_failed: "Afsendelse mislykkedes",
    file_received: "Fil modtaget",
    scan_completed: "Scanning afsluttet",
    no_devices: "Ingen enheder fundet"
  },
  fi_FI: {
    welcome: "Tervetuloa Xiaosi NAS-palveluun",
    storage_management: "Tallennustilan hallinta",
    user_management: "Käyttäjien hallinta",
    smb_shares: "SMB-jaot",
    push_files: "Lähetä tiedostoja",
    success: "Toiminto onnistui",
    failed: "Toiminto epäonnistui",
    not_found: "Resurssia ei löydy",
    invalid_params: "Virheelliset parametrit",
    volume_created: "Tallennustilan asema luotu",
    volume_deleted: "Tallennustilan asema poistettu",
    user_created: "Käyttäjä luotu",
    user_deleted: "Käyttäjä poistettu",
    share_created: "Jako luotu",
    share_deleted: "Jako poistettu",
    push_started: "Lähetys aloitettu",
    push_completed: "Lähetys valmis",
    push_failed: "Lähetys epäonnistui",
    file_received: "Tiedosto vastaanotettu",
    scan_completed: "Skannaus valmis",
    no_devices: "Laitteita ei löydy"
  },
  he_IL: {
    welcome: "ברוכים הבאים לשירות NAS של Xiaosi",
    storage_management: "ניהול אחסון",
    user_management: "ניהול משתמשים",
    smb_shares: "שיתוף SMB",
    push_files: "שלח קבצים",
    success: "הפעולה הצליחה",
    failed: "הפעולה נכשלה",
    not_found: "המשאב לא נמצא",
    invalid_params: "פרמטרים לא תקינים",
    volume_created: "נפח אחסון נוצר",
    volume_deleted: "נפח אחסון נמחק",
    user_created: "משתמש נוצר",
    user_deleted: "משתמש נמחק",
    share_created: "שיתוף נוצר",
    share_deleted: "שיתוף נמחק",
    push_started: "השליחה התחילה",
    push_completed: "השליחה הושלמה",
    push_failed: "השליחה נכשלה",
    file_received: "קובץ התקבל",
    scan_completed: "הסריקה הושלמה",
    no_devices: "לא נמצאו מכשירים"
  },
  hu_HU: {
    welcome: "Üdvözöljük a Xiaosi NAS szolgáltatásban",
    storage_management: "Tároláskezelés",
    user_management: "Felhasználókezelés",
    smb_shares: "SMB megosztások",
    push_files: "Fájlküldés",
    success: "Művelet sikeres",
    failed: "Művelet sikertelen",
    not_found: "Erőforrás nem található",
    invalid_params: "Érvénytelen paraméterek",
    volume_created: "Tárolókötet sikeresen létrehozva",
    volume_deleted: "Tárolókötet sikeresen törölve",
    user_created: "Felhasználó sikeresen létrehozva",
    user_deleted: "Felhasználó sikeresen törölve",
    share_created: "Megosztás sikeresen létrehozva",
    share_deleted: "Megosztás sikeresen törölve",
    push_started: "Küldés elindítva",
    push_completed: "Küldés befejezve",
    push_failed: "Küldés sikertelen",
    file_received: "Fájl sikeresen fogadva",
    scan_completed: "Beolvasás befejezve",
    no_devices: "Nem található eszköz"
  },
  ro_RO: {
    welcome: "Bun venit la serviciul NAS Xiaosi",
    storage_management: "Gestionare stocare",
    user_management: "Gestionare utilizatori",
    smb_shares: "Partajări SMB",
    push_files: "Trimitere fișiere",
    success: "Operație reușită",
    failed: "Operație eșuată",
    not_found: "Resursă negăsită",
    invalid_params: "Parametri invalizi",
    volume_created: "Volum de stocare creat cu succes",
    volume_deleted: "Volum de stocare șters cu succes",
    user_created: "Utilizator creat cu succes",
    user_deleted: "Utilizator șters cu succes",
    share_created: "Partajare creată cu succes",
    share_deleted: "Partajare ștersă cu succes",
    push_started: "Trimitere începută",
    push_completed: "Trimitere finalizată",
    push_failed: "Trimitere eșuată",
    file_received: "Fișier primit cu succes",
    scan_completed: "Scanare finalizată",
    no_devices: "Niciun dispozitiv găsit"
  }
}

def t(key : String, lang : String = CONFIG.dig("server", "language").as_s) : String
  lang_sym = lang.gsub("_", "").to_sym
  translations = I18N[lang_sym]?
  if translations && translations[key.to_sym]?
    translations[key.to_sym].to_s
  else
    # 回退到zh_CN
    I18N[:zh_CN][key.to_sym]?.to_s || key
  end
end

# ==================== 辅助方法 ====================
def json_response(success : Bool, message : String, data = nil) : String
  response = {"success" => success, "message" => message}
  if data
    response = response.merge({"data" => data})
  end
  response.to_json
end

def read_json_file(path : String) : Array(JSON::Any)
  return [] of JSON::Any unless File.exists?(path)
  JSON.parse(File.read(path)).as_a
rescue
  [] of JSON::Any
end

def write_json_file(path : String, data : Array(JSON::Any))
  File.write(path, data.to_json)
end

def get_local_ips : Array(Hash(String, String))
  ips = [] of Hash(String, String)
  Socket.getifaddrs.each do |ifaddr|
    if ifaddr.addr && ifaddr.addr.family == Socket::Family::INET && !ifaddr.addr.ip_address.starts_with?("127.")
      ips << {
        "interface" => ifaddr.name.to_s,
        "ip" => ifaddr.addr.ip_address.to_s,
        "netmask" => ifaddr.netmask?.try(&.ip_address.to_s) || "255.255.255.0"
      }
    end
  end
  ips
end

def scan_network(port : Int32 = 8080, timeout : Float64 = 1.0) : Array(Hash(String, String | Int32))
  devices = [] of Hash(String, String | Int32)
  local_ips = get_local_ips

  local_ips.each do |ip_info|
    ip = ip_info["ip"]
    next unless ip

    begin
      ipaddr = Socket::IPAddress.new(ip, 0)
      netmask = ip_info["netmask"]

      # 简化扫描：只扫描同一网段
      ip_parts = ip.split(".")
      if ip_parts.size == 4
        (1..254).each do |i|
          host_ip = "#{ip_parts[0]}.#{ip_parts[1]}.#{ip_parts[2]}.#{i}"
          next if host_ip == ip

          spawn do
            begin
              socket = TCPSocket.new(host_ip, port, connect_timeout: timeout)
              socket.close
              devices << {"ip" => host_ip, "port" => port, "status" => "online"}
            rescue
              # 连接失败，忽略
            end
          end
        end
      end
    rescue
      next
    end
  end

  sleep(timeout)
  devices
end

def sha256_password(password : String) : String
  Digest::SHA256.hexdigest(password)
end

def generate_uuid : String
  Random::Secure.hex(16)
end

# ==================== 数据文件路径 ====================
USERS_FILE = File.join(DATA_DIR, "users.json")
SHARES_FILE = File.join(DATA_DIR, "shares.json")
PUSH_HISTORY_FILE = File.join(DATA_DIR, "push_history.json")

# 确保目录存在
FileUtils.mkdir_p(DATA_DIR) unless Dir.exists?(DATA_DIR)
FileUtils.mkdir_p(RECEIVE_DIR) unless Dir.exists?(RECEIVE_DIR)

# ==================== Kemal配置 ====================
port CONFIG.dig("server", "port").as_i || 8096

# 全局设置
before_all do |env|
  env.response.content_type = "application/json"
end

# ==================== 首页 ====================
get "/" do |env|
  web_path = File.join(BASE_DIR, "web", "index.html")
  if File.exists?(web_path)
    env.response.content_type = "text/html"
    File.read(web_path)
  else
    json_response(true, t("welcome"), {
      "service" => "Xiaosi NAS Service",
      "version" => "2.0.0",
      "language" => CONFIG.dig("server", "language").as_s,
      "endpoints" => {
        "storage" => "/api/storage/volumes",
        "users" => "/api/users",
        "smb" => "/api/smb/shares",
        "ip" => "/api/ip/local",
        "push" => "/api/push/targets",
        "i18n" => "/api/i18n/"
      }
    })
  end
end

# ==================== 存储管理 ====================
get "/api/storage/volumes" do |env|
  volumes = CONFIG.dig("storage", "volumes").as_a
  volumes.each do |vol|
    path = vol["path"].as_s
    if Dir.exists?(path)
      vol = vol.merge({"exists" => true})
      # 计算已使用空间（简化版）
      vol = vol.merge({"used_gb" => 0.0})
    else
      vol = vol.merge({"exists" => false, "used_gb" => 0.0})
    end
  end
  json_response(true, t("success"), volumes)
end

post "/api/storage/volumes" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)

    name = data["name"]?.try(&.as_s)
    path = data["path"]?.try(&.as_s)
    quota_gb = data["quota_gb"]?.try(&.as_i) || 100

    unless name && path
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    volumes = CONFIG["storage"]["volumes"].as_a

    volume = {
      "name" => name,
      "path" => path,
      "quota_gb" => quota_gb,
      "created_at" => Time.local.to_s
    }.to_json

    volumes << JSON.parse(volume)

    new_config = CONFIG.as_h.merge({"storage" => {"volumes" => volumes}})
    save_config(JSON.parse(new_config.to_json))

    # 创建目录
    FileUtils.mkdir_p(path) unless Dir.exists?(path)

    json_response(true, t("volume_created"), JSON.parse(volume))
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

post "/api/storage/volumes/delete" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)
    name = data["name"]?.try(&.as_s)

    unless name
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    volumes = CONFIG["storage"]["volumes"].as_a
    volume = volumes.find { |v| v["name"].as_s == name }

    unless volume
      halt env, status_code: 404, response: json_response(false, t("not_found"))
    end

    volumes.delete(volume)

    new_config = CONFIG.as_h.merge({"storage" => {"volumes" => volumes}})
    save_config(JSON.parse(new_config.to_json))

    json_response(true, t("volume_deleted"))
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

# ==================== 用户管理 ====================
get "/api/users" do |env|
  users = read_json_file(USERS_FILE)
  # 移除密码字段
  users.each { |u| u.as_h.delete("password") }
  json_response(true, t("success"), users)
end

post "/api/users" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)

    username = data["username"]?.try(&.as_s)
    password = data["password"]?.try(&.as_s)

    unless username && password
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    users = read_json_file(USERS_FILE)

    if users.any? { |u| u["username"]?.try(&.as_s) == username }
      halt env, status_code: 400, response: json_response(false, "用户已存在")
    end

    user = {
      "id" => generate_uuid,
      "username" => username,
      "password" => sha256_password(password),
      "created_at" => Time.local.to_s
    }.to_json

    users << JSON.parse(user)
    write_json_file(USERS_FILE, users)

    user_json = JSON.parse(user)
    user_json.as_h.delete("password")

    json_response(true, t("user_created"), user_json)
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

post "/api/users/delete" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)
    user_id = data["id"]?.try(&.as_s) || data["username"]?.try(&.as_s)

    unless user_id
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    users = read_json_file(USERS_FILE)
    user = users.find { |u| u["id"]?.try(&.as_s) == user_id || u["username"]?.try(&.as_s) == user_id }

    unless user
      halt env, status_code: 404, response: json_response(false, t("not_found"))
    end

    users.delete(user)
    write_json_file(USERS_FILE, users)

    json_response(true, t("user_deleted"))
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

# ==================== SMB共享 ====================
get "/api/smb/shares" do |env|
  shares = read_json_file(SHARES_FILE)
  json_response(true, t("success"), shares)
end

post "/api/smb/shares" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)

    name = data["name"]?.try(&.as_s)
    path = data["path"]?.try(&.as_s)

    unless name && path
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    shares = read_json_file(SHARES_FILE)

    share = {
      "id" => generate_uuid,
      "name" => name,
      "path" => path,
      "comment" => data["comment"]?.try(&.as_s) || "",
      "read_only" => data["read_only"]?.try(&.as_bool) || false,
      "browseable" => data["browseable"]?.try(&.as_bool) || true,
      "created_at" => Time.local.to_s
    }.to_json

    shares << JSON.parse(share)
    write_json_file(SHARES_FILE, shares)

    json_response(true, t("share_created"), JSON.parse(share))
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

post "/api/smb/shares/delete" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)
    share_id = data["id"]?.try(&.as_s) || data["name"]?.try(&.as_s)

    unless share_id
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    shares = read_json_file(SHARES_FILE)
    share = shares.find { |s| s["id"]?.try(&.as_s) == share_id || s["name"]?.try(&.as_s) == share_id }

    unless share
      halt env, status_code: 404, response: json_response(false, t("not_found"))
    end

    shares.delete(share)
    write_json_file(SHARES_FILE, shares)

    json_response(true, t("share_deleted"))
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

get "/api/smb/status" do |env|
  json_response(true, t("success"), {"running" => false})
end

# ==================== IP与推送 ====================
get "/api/ip/local" do |env|
  ips = get_local_ips
  json_response(true, t("success"), {"ips" => ips})
end

get "/api/ip/scan" do |env|
  port_param = env.params.query["port"]?.try(&.to_i) || 8080
  devices = scan_network(port_param)
  json_response(true, t("scan_completed"), {"devices" => devices})
end

get "/api/push/targets" do |env|
  targets = CONFIG.dig("push", "targets").as_a
  json_response(true, t("success"), {"targets" => targets})
end

post "/api/push/targets" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)

    name = data["name"]?.try(&.as_s)
    ip = data["ip"]?.try(&.as_s)
    port = data["port"]?.try(&.as_i) || 8080

    unless name && ip
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    targets = CONFIG["push"]["targets"].as_a

    target = {
      "id" => generate_uuid,
      "name" => name,
      "ip" => ip,
      "port" => port,
      "created_at" => Time.local.to_s
    }.to_json

    targets << JSON.parse(target)

    new_config = CONFIG.as_h.merge({"push" => {"targets" => targets}})
    save_config(JSON.parse(new_config.to_json))

    json_response(true, t("success"), JSON.parse(target))
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

post "/api/push/targets/delete" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)
    target_id = data["id"]?.try(&.as_s)

    unless target_id
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    targets = CONFIG["push"]["targets"].as_a
    target = targets.find { |t| t["id"]?.try(&.as_s) == target_id }

    unless target
      halt env, status_code: 404, response: json_response(false, t("not_found"))
    end

    targets.delete(target)

    new_config = CONFIG.as_h.merge({"push" => {"targets" => targets}})
    save_config(JSON.parse(new_config.to_json))

    json_response(true, t("success"))
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

post "/api/push/targets/check" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)
    target_id = data["id"]?.try(&.as_s)

    unless target_id
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    targets = CONFIG["push"]["targets"].as_a
    target = targets.find { |t| t["id"]?.try(&.as_s) == target_id }

    unless target
      halt env, status_code: 404, response: json_response(false, t("not_found"))
    end

    ip = target["ip"].as_s
    port = target["port"].as_i

    # 尝试连接
    begin
      socket = TCPSocket.new(ip, port, connect_timeout: 2.0)
      socket.close
      json_response(true, "设备在线", {"online" => true})
    rescue
      json_response(false, "设备离线", {"online" => false})
    end
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

post "/api/push/folder" do |env|
  begin
    data = JSON.parse(env.request.body.not_nil!.gets_to_end)

    folder_path = data["folder_path"]?.try(&.as_s)
    target_id = data["target_id"]?.try(&.as_s)

    unless folder_path && target_id
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    targets = CONFIG["push"]["targets"].as_a
    target = targets.find { |t| t["id"]?.try(&.as_s) == target_id }

    unless target
      halt env, status_code: 404, response: json_response(false, t("not_found"))
    end

    unless Dir.exists?(folder_path)
      halt env, status_code: 400, response: json_response(false, "文件夹不存在")
    end

    # 记录推送历史
    history = {
      "id" => generate_uuid,
      "folder_path" => folder_path,
      "target" => target.to_json,
      "status" => "started",
      "started_at" => Time.local.to_s,
      "sent_files" => 0,
      "total_files" => 0
    }.to_json

    push_history = read_json_file(PUSH_HISTORY_FILE)
    push_history << JSON.parse(history)
    write_json_file(PUSH_HISTORY_FILE, push_history)

    # 异步推送（简化实现）
    spawn do
      begin
        files_count = 0
        folder_name = File.basename(folder_path)
        ip = target["ip"].as_s
        port = target["port"].as_i

        # 统计文件总数
        total_files = Dir.glob(File.join(folder_path, "**", "*")).count { |f| File.file?(f) }

        # 更新历史记录
        push_history = read_json_file(PUSH_HISTORY_FILE)
        record_idx = push_history.index { |h| h["id"]?.try(&.as_s) == JSON.parse(history)["id"].as_s }

        if record_idx
          push_history[record_idx] = push_history[record_idx].merge({"total_files" => total_files})
          write_json_file(PUSH_HISTORY_FILE, push_history)
        end

        # 推送每个文件
        Dir.glob(File.join(folder_path, "**", "*")).each do |file|
          next unless File.file?(file)

          relative_path = file.sub(folder_path, "").gsub(/^\/|^\\/, "")
          files_count += 1

          # 使用HTTP multipart推送文件（简化版）
          begin
            client = HTTP::Client.new(ip, port)
            boundary = "----XiaosiNASPush#{Random::Secure.hex(16)}"

            body = String.build do |str|
              str << "--#{boundary}\r\n"
              str << "Content-Disposition: form-data; name=\"folder\"\r\n\r\n#{folder_name}\r\n"
              str << "--#{boundary}\r\n"
              str << "Content-Disposition: form-data; name=\"filepath\"\r\n\r\n#{relative_path}\r\n"
              str << "--#{boundary}\r\n"
              str << "Content-Disposition: form-data; name=\"file\"; filename=\"#{File.basename(file)}\"\r\n"
              str << "Content-Type: application/octet-stream\r\n\r\n"
              str << File.read(file)
              str << "\r\n--#{boundary}--\r\n"
            end

            headers = HTTP::Headers{"Content-Type" => "multipart/form-data; boundary=#{boundary}"}
            client.post("/api/push/receive", headers: headers, body: body)
            client.close

            # 更新进度
            push_history = read_json_file(PUSH_HISTORY_FILE)
            record_idx = push_history.index { |h| h["id"]?.try(&.as_s) == JSON.parse(history)["id"].as_s }

            if record_idx
              push_history[record_idx] = push_history[record_idx].merge({"sent_files" => files_count})
              write_json_file(PUSH_HISTORY_FILE, push_history)
            end
          rescue
            # 单个文件推送失败，继续
          end
        end

        # 更新最终状态
        push_history = read_json_file(PUSH_HISTORY_FILE)
        record_idx = push_history.index { |h| h["id"]?.try(&.as_s) == JSON.parse(history)["id"].as_s }

        if record_idx
          push_history[record_idx] = push_history[record_idx].merge({
            "status" => "completed",
            "sent_files" => files_count,
            "completed_at" => Time.local.to_s
          })
          write_json_file(PUSH_HISTORY_FILE, push_history)
        end
      rescue ex
        # 推送失败
        push_history = read_json_file(PUSH_HISTORY_FILE)
        record_idx = push_history.index { |h| h["id"]?.try(&.as_s) == JSON.parse(history)["id"].as_s }

        if record_idx
          push_history[record_idx] = push_history[record_idx].merge({
            "status" => "failed",
            "error" => ex.message.to_s,
            "completed_at" => Time.local.to_s
          })
          write_json_file(PUSH_HISTORY_FILE, push_history)
        end
      end
    end

    json_response(true, t("push_started"), JSON.parse(history))
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

get "/api/push/status" do |env|
  push_history = read_json_file(PUSH_HISTORY_FILE)
  # 返回最后20条记录
  recent_history = push_history.last(20)

  # 检查是否有正在进行的推送
  active = push_history.find { |h| h["status"]?.try(&.as_s) == "started" }

  json_response(true, t("success"), {
    "history" => recent_history,
    "active" => active
  })
end

post "/api/push/receive" do |env|
  begin
    # 处理multipart/form-data
    content_type = env.request.headers["Content-Type"]?

    unless content_type && content_type.includes?("multipart/form-data")
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    # 简化处理：解析multipart数据
    boundary = content_type.split("boundary=").last.strip
    body = env.request.body.not_nil!.gets_to_end

    folder = ""
    filepath = ""
    file_content = ""
    filename = ""

    # 解析multipart（简化版）
    parts = body.split("--#{boundary}")

    parts.each do |part|
      next if part.empty? || part.includes?("--")

      if part.includes?("name=\"folder\"")
        folder = part.split("\r\n\r\n").last.strip
      elsif part.includes?("name=\"filepath\"")
        filepath = part.split("\r\n\r\n").last.strip
      elsif part.includes?("name=\"file\"")
        filename_match = part.match(/filename="([^"]+)"/)
        filename = filename_match ? filename_match[1] : "unknown"
        # 提取文件内容（简化）
        content_start = part.index("\r\n\r\n")
        if content_start
          file_content = part[(content_start + 4)..(part.size - 3)]
        end
      end
    end

    unless folder && filename
      halt env, status_code: 400, response: json_response(false, t("invalid_params"))
    end

    # 创建接收目录
    receive_path = File.join(RECEIVE_DIR, folder)
    if filepath && !filepath.empty?
      receive_path = File.join(receive_path, filepath)
    end

    FileUtils.mkdir_p(File.dirname(receive_path)) unless Dir.exists?(File.dirname(receive_path))

    # 保存文件
    File.write(receive_path, file_content)

    json_response(true, t("file_received"), {
      "folder" => folder,
      "filepath" => filepath,
      "filename" => filename,
      "size" => file_content.size
    })
  rescue ex
    json_response(false, "#{t("failed")}: #{ex.message}")
  end
end

# ==================== 多语言 ====================
get "/api/i18n" do |env|
  lang = env.params.query["lang"]?.try(&.to_s) || CONFIG.dig("server", "language").as_s
  lang_sym = lang.gsub("_", "").to_sym

  translations = I18N[lang_sym]? || I18N[:zh_CN]

  json_response(true, t("success"), {
    "language" => lang,
    "translations" => translations.to_json
  })
end

# ==================== 错误处理 ====================
error 404 do |env|
  json_response(false, t("not_found"))
end

error 500 do |env|
  json_response(false, "#{t("failed")}: #{env.response.status_message}")
end

# ==================== 启动 ====================
Kemal.run do
  puts "=" * 60
  puts "  小思NAS服务 (Crystal版) v2.0.0"
  puts "=" * 60
  puts "  Ruby语法 · C性能"
  puts "  语言支持: 28种语言"
  puts "=" * 60
  puts "  监听地址: 0.0.0.0:#{Kemal.config.port}"
  puts "  配置文件: #{CONFIG_PATH}"
  puts "  数据目录: #{DATA_DIR}"
  puts "  接收目录: #{RECEIVE_DIR}"
  puts "=" * 60

  # 显示本地IP
  get_local_ips.each do |ip_info|
    unless ip_info["ip"].starts_with?("127.")
      puts "  网络访问: http://#{ip_info['ip']}:#{Kemal.config.port}"
    end
  end

  puts "=" * 60
  puts "  按 Ctrl+C 停止服务"
  puts "=" * 60
end