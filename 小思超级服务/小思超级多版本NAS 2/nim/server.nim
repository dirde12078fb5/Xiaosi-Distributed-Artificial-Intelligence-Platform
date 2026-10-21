# 小思超级多版本NAS服务 - Nim实现
# 高性能、轻量级的NAS解决方案

import jester, asyncdispatch, json, os, strutils, times, tables, hashes
import sequtils, unicode, re, base64, sha1, mimetypes

# 类型定义
type
  User = object
    username: string
    password: string
    is_admin: bool
    home_dir: string
    storage_quota_gb: int

  Volume = object
    name: string
    path: string
    quota_gb: int

  SMBShare = object
    name: string
    path: string
    comment: string
    read_only: bool
    browseable: bool
    guest_access: bool

  Config = object
    port: int
    language: string
    volumes: seq[Volume]
    users: seq[User]
    smb_shares: seq[SMBShare]
    data_dir: string
    receive_dir: string

# 全局变量
var
  config: Config
  sessions: Table[string, string]  # session_id -> username
  translations: Table[string, Table[string, string]]  # 语言 -> key -> value
  mimeTypes = newMimeTypes()

# 28种语言支持
const LANGUAGES = [
  "zh_CN", "zh_TW", "en_US", "en_GB", "ja_JP", "ko_KR",
  "de_DE", "fr_FR", "es_ES", "it_IT", "pt_PT", "pt_BR",
  "ru_RU", "nl_NL", "pl_PL", "tr_TR", "ar_SA", "he_IL",
  "th_TH", "vi_VN", "id_ID", "ms_MY", "cs_CZ", "hu_HU",
  "sv_SE", "no_NO", "da_DK", "fi_FI"
]

# 初始化翻译
proc initTranslations() =
  # 中文简体
  translations["zh_CN"] = {
    "welcome": "欢迎使用小思NAS系统",
    "login_success": "登录成功",
    "login_failed": "用户名或密码错误",
    "logout_success": "已成功登出",
    "file_uploaded": "文件上传成功",
    "file_deleted": "文件删除成功",
    "folder_created": "文件夹创建成功",
    "folder_deleted": "文件夹删除成功",
    "file_not_found": "文件不存在",
    "permission_denied": "权限不足",
    "storage_info": "存储信息",
    "user_list": "用户列表",
    "volume_list": "存储卷列表",
    "share_list": "共享列表",
    "settings_saved": "设置已保存",
    "error_occurred": "发生错误",
    "invalid_request": "无效请求",
    "session_expired": "会话已过期",
    "quota_exceeded": "存储配额已超限",
    "file_exists": "文件已存在",
    "invalid_path": "无效路径"
  }.toTable

  # 中文繁体
  translations["zh_TW"] = {
    "welcome": "歡迎使用小思NAS系統",
    "login_success": "登入成功",
    "login_failed": "使用者名稱或密碼錯誤",
    "logout_success": "已成功登出",
    "file_uploaded": "檔案上傳成功",
    "file_deleted": "檔案刪除成功",
    "folder_created": "資料夾建立成功",
    "folder_deleted": "資料夾刪除成功",
    "file_not_found": "檔案不存在",
    "permission_denied": "權限不足",
    "storage_info": "儲存資訊",
    "user_list": "使用者列表",
    "volume_list": "儲存磁碟區列表",
    "share_list": "共用列表",
    "settings_saved": "設定已儲存",
    "error_occurred": "發生錯誤",
    "invalid_request": "無效請求",
    "session_expired": "工作階段已過期",
    "quota_exceeded": "儲存配額已超限",
    "file_exists": "檔案已存在",
    "invalid_path": "無效路徑"
  }.toTable

  # 英语
  translations["en_US"] = {
    "welcome": "Welcome to Xiaosi NAS System",
    "login_success": "Login successful",
    "login_failed": "Invalid username or password",
    "logout_success": "Successfully logged out",
    "file_uploaded": "File uploaded successfully",
    "file_deleted": "File deleted successfully",
    "folder_created": "Folder created successfully",
    "folder_deleted": "Folder deleted successfully",
    "file_not_found": "File not found",
    "permission_denied": "Permission denied",
    "storage_info": "Storage Information",
    "user_list": "User List",
    "volume_list": "Volume List",
    "share_list": "Share List",
    "settings_saved": "Settings saved",
    "error_occurred": "An error occurred",
    "invalid_request": "Invalid request",
    "session_expired": "Session expired",
    "quota_exceeded": "Storage quota exceeded",
    "file_exists": "File already exists",
    "invalid_path": "Invalid path"
  }.toTable

  # 英语(英式)
  translations["en_GB"] = {
    "welcome": "Welcome to Xiaosi NAS System",
    "login_success": "Login successful",
    "login_failed": "Invalid username or password",
    "logout_success": "Successfully logged out",
    "file_uploaded": "File uploaded successfully",
    "file_deleted": "File deleted successfully",
    "folder_created": "Folder created successfully",
    "folder_deleted": "Folder deleted successfully",
    "file_not_found": "File not found",
    "permission_denied": "Permission denied",
    "storage_info": "Storage Information",
    "user_list": "User List",
    "volume_list": "Volume List",
    "share_list": "Share List",
    "settings_saved": "Settings saved",
    "error_occurred": "An error occurred",
    "invalid_request": "Invalid request",
    "session_expired": "Session expired",
    "quota_exceeded": "Storage quota exceeded",
    "file_exists": "File already exists",
    "invalid_path": "Invalid path"
  }.toTable

  # 日语
  translations["ja_JP"] = {
    "welcome": "小思NASシステムへようこそ",
    "login_success": "ログイン成功",
    "login_failed": "ユーザー名またはパスワードが正しくありません",
    "logout_success": "ログアウトしました",
    "file_uploaded": "ファイルのアップロードが完了しました",
    "file_deleted": "ファイルを削除しました",
    "folder_created": "フォルダを作成しました",
    "folder_deleted": "フォルダを削除しました",
    "file_not_found": "ファイルが見つかりません",
    "permission_denied": "権限がありません",
    "storage_info": "ストレージ情報",
    "user_list": "ユーザー一覧",
    "volume_list": "ボリューム一覧",
    "share_list": "共有一覧",
    "settings_saved": "設定を保存しました",
    "error_occurred": "エラーが発生しました",
    "invalid_request": "無効なリクエスト",
    "session_expired": "セッションが期限切れです",
    "quota_exceeded": "ストレージ容量を超えました",
    "file_exists": "ファイルは既に存在します",
    "invalid_path": "無効なパス"
  }.toTable

  # 韩语
  translations["ko_KR"] = {
    "welcome": "小思 NAS 시스템에 오신 것을 환영합니다",
    "login_success": "로그인 성공",
    "login_failed": "잘못된 사용자 이름 또는 비밀번호",
    "logout_success": "로그아웃 성공",
    "file_uploaded": "파일 업로드 성공",
    "file_deleted": "파일 삭제 성공",
    "folder_created": "폴더 생성 성공",
    "folder_deleted": "폴더 삭제 성공",
    "file_not_found": "파일을 찾을 수 없습니다",
    "permission_denied": "권한이 없습니다",
    "storage_info": "저장소 정보",
    "user_list": "사용자 목록",
    "volume_list": "볼륨 목록",
    "share_list": "공유 목록",
    "settings_saved": "설정이 저장되었습니다",
    "error_occurred": "오류가 발생했습니다",
    "invalid_request": "잘못된 요청",
    "session_expired": "세션이 만료되었습니다",
    "quota_exceeded": "저장 공간을 초과했습니다",
    "file_exists": "파일이 이미 존재합니다",
    "invalid_path": "잘못된 경로"
  }.toTable

  # 德语
  translations["de_DE"] = {
    "welcome": "Willkommen beim Xiaosi NAS System",
    "login_success": "Anmeldung erfolgreich",
    "login_failed": "Ungültiger Benutzername oder Passwort",
    "logout_success": "Erfolgreich abgemeldet",
    "file_uploaded": "Datei erfolgreich hochgeladen",
    "file_deleted": "Datei erfolgreich gelöscht",
    "folder_created": "Ordner erfolgreich erstellt",
    "folder_deleted": "Ordner erfolgreich gelöscht",
    "file_not_found": "Datei nicht gefunden",
    "permission_denied": "Zugriff verweigert",
    "storage_info": "Speicherinformationen",
    "user_list": "Benutzerliste",
    "volume_list": "Volumenliste",
    "share_list": "Freigabeliste",
    "settings_saved": "Einstellungen gespeichert",
    "error_occurred": "Ein Fehler ist aufgetreten",
    "invalid_request": "Ungültige Anfrage",
    "session_expired": "Sitzung abgelaufen",
    "quota_exceeded": "Speicherkontingent überschritten",
    "file_exists": "Datei bereits vorhanden",
    "invalid_path": "Ungültiger Pfad"
  }.toTable

  # 法语
  translations["fr_FR"] = {
    "welcome": "Bienvenue dans le système NAS Xiaosi",
    "login_success": "Connexion réussie",
    "login_failed": "Nom d'utilisateur ou mot de passe invalide",
    "logout_success": "Déconnexion réussie",
    "file_uploaded": "Fichier téléchargé avec succès",
    "file_deleted": "Fichier supprimé avec succès",
    "folder_created": "Dossier créé avec succès",
    "folder_deleted": "Dossier supprimé avec succès",
    "file_not_found": "Fichier non trouvé",
    "permission_denied": "Permission refusée",
    "storage_info": "Informations de stockage",
    "user_list": "Liste des utilisateurs",
    "volume_list": "Liste des volumes",
    "share_list": "Liste des partages",
    "settings_saved": "Paramètres enregistrés",
    "error_occurred": "Une erreur s'est produite",
    "invalid_request": "Requête invalide",
    "session_expired": "Session expirée",
    "quota_exceeded": "Quota de stockage dépassé",
    "file_exists": "Le fichier existe déjà",
    "invalid_path": "Chemin invalide"
  }.toTable

  # 西班牙语
  translations["es_ES"] = {
    "welcome": "Bienvenido al sistema NAS Xiaosi",
    "login_success": "Inicio de sesión exitoso",
    "login_failed": "Nombre de usuario o contraseña inválidos",
    "logout_success": "Sesión cerrada exitosamente",
    "file_uploaded": "Archivo subido exitosamente",
    "file_deleted": "Archivo eliminado exitosamente",
    "folder_created": "Carpeta creada exitosamente",
    "folder_deleted": "Carpeta eliminada exitosamente",
    "file_not_found": "Archivo no encontrado",
    "permission_denied": "Permiso denegado",
    "storage_info": "Información de almacenamiento",
    "user_list": "Lista de usuarios",
    "volume_list": "Lista de volúmenes",
    "share_list": "Lista de recursos compartidos",
    "settings_saved": "Configuración guardada",
    "error_occurred": "Ocurrió un error",
    "invalid_request": "Solicitud inválida",
    "session_expired": "Sesión expirada",
    "quota_exceeded": "Cuota de almacenamiento excedida",
    "file_exists": "El archivo ya existe",
    "invalid_path": "Ruta inválida"
  }.toTable

  # 意大利语
  translations["it_IT"] = {
    "welcome": "Benvenuto nel sistema NAS Xiaosi",
    "login_success": "Accesso riuscito",
    "login_failed": "Nome utente o password non validi",
    "logout_success": "Disconnessione riuscita",
    "file_uploaded": "File caricato con successo",
    "file_deleted": "File eliminato con successo",
    "folder_created": "Cartella creata con successo",
    "folder_deleted": "Cartella eliminata con successo",
    "file_not_found": "File non trovato",
    "permission_denied": "Permesso negato",
    "storage_info": "Informazioni di archiviazione",
    "user_list": "Elenco utenti",
    "volume_list": "Elenco volumi",
    "share_list": "Elenco condivisioni",
    "settings_saved": "Impostazioni salvate",
    "error_occurred": "Si è verificato un errore",
    "invalid_request": "Richiesta non valida",
    "session_expired": "Sessione scaduta",
    "quota_exceeded": "Quota di archiviazione superata",
    "file_exists": "Il file esiste già",
    "invalid_path": "Percorso non valido"
  }.toTable

  # 葡萄牙语(葡萄牙)
  translations["pt_PT"] = {
    "welcome": "Bem-vindo ao sistema NAS Xiaosi",
    "login_success": "Login bem-sucedido",
    "login_failed": "Nome de usuário ou senha inválidos",
    "logout_success": "Sessão encerrada com sucesso",
    "file_uploaded": "Arquivo enviado com sucesso",
    "file_deleted": "Arquivo excluído com sucesso",
    "folder_created": "Pasta criada com sucesso",
    "folder_deleted": "Pasta excluída com sucesso",
    "file_not_found": "Arquivo não encontrado",
    "permission_denied": "Permissão negada",
    "storage_info": "Informações de armazenamento",
    "user_list": "Lista de usuários",
    "volume_list": "Lista de volumes",
    "share_list": "Lista de compartilhamentos",
    "settings_saved": "Configurações salvas",
    "error_occurred": "Ocorreu um erro",
    "invalid_request": "Solicitação inválida",
    "session_expired": "Sessão expirada",
    "quota_exceeded": "Cota de armazenamento excedida",
    "file_exists": "O arquivo já existe",
    "invalid_path": "Caminho inválido"
  }.toTable

  # 葡萄牙语(巴西)
  translations["pt_BR"] = {
    "welcome": "Bem-vindo ao sistema NAS Xiaosi",
    "login_success": "Login bem-sucedido",
    "login_failed": "Nome de usuário ou senha inválidos",
    "logout_success": "Sessão encerrada com sucesso",
    "file_uploaded": "Arquivo enviado com sucesso",
    "file_deleted": "Arquivo excluído com sucesso",
    "folder_created": "Pasta criada com sucesso",
    "folder_deleted": "Pasta excluída com sucesso",
    "file_not_found": "Arquivo não encontrado",
    "permission_denied": "Permissão negada",
    "storage_info": "Informações de armazenamento",
    "user_list": "Lista de usuários",
    "volume_list": "Lista de volumes",
    "share_list": "Lista de compartilhamentos",
    "settings_saved": "Configurações salvas",
    "error_occurred": "Ocorreu um erro",
    "invalid_request": "Solicitação inválida",
    "session_expired": "Sessão expirada",
    "quota_exceeded": "Cota de armazenamento excedida",
    "file_exists": "O arquivo já existe",
    "invalid_path": "Caminho inválido"
  }.toTable

  # 俄语
  translations["ru_RU"] = {
    "welcome": "Добро пожаловать в систему NAS Xiaosi",
    "login_success": "Вход выполнен успешно",
    "login_failed": "Неверное имя пользователя или пароль",
    "logout_success": "Выход выполнен успешно",
    "file_uploaded": "Файл успешно загружен",
    "file_deleted": "Файл успешно удален",
    "folder_created": "Папка успешно создана",
    "folder_deleted": "Папка успешно удалена",
    "file_not_found": "Файл не найден",
    "permission_denied": "Доступ запрещен",
    "storage_info": "Информация о хранилище",
    "user_list": "Список пользователей",
    "volume_list": "Список томов",
    "share_list": "Список общих ресурсов",
    "settings_saved": "Настройки сохранены",
    "error_occurred": "Произошла ошибка",
    "invalid_request": "Неверный запрос",
    "session_expired": "Сессия истекла",
    "quota_exceeded": "Превышена квота хранилища",
    "file_exists": "Файл уже существует",
    "invalid_path": "Неверный путь"
  }.toTable

  # 荷兰语
  translations["nl_NL"] = {
    "welcome": "Welkom bij het Xiaosi NAS-systeem",
    "login_success": "Inloggen geslaagd",
    "login_failed": "Ongeldige gebruikersnaam of wachtwoord",
    "logout_success": "Succesvol uitgelogd",
    "file_uploaded": "Bestand succesvol geüpload",
    "file_deleted": "Bestand succesvol verwijderd",
    "folder_created": "Map succesvol aangemaakt",
    "folder_deleted": "Map succesvol verwijderd",
    "file_not_found": "Bestand niet gevonden",
    "permission_denied": "Toestemming geweigerd",
    "storage_info": "Opslaginformatie",
    "user_list": "Gebruikerslijst",
    "volume_list": "Volumelijst",
    "share_list": "Deellijst",
    "settings_saved": "Instellingen opgeslagen",
    "error_occurred": "Er is een fout opgetreden",
    "invalid_request": "Ongeldig verzoek",
    "session_expired": "Sessie verlopen",
    "quota_exceeded": "Opslaglimiet overschreden",
    "file_exists": "Bestand bestaat al",
    "invalid_path": "Ongeldig pad"
  }.toTable

  # 波兰语
  translations["pl_PL"] = {
    "welcome": "Witamy w systemie NAS Xiaosi",
    "login_success": "Logowanie udane",
    "login_failed": "Nieprawidłowa nazwa użytkownika lub hasło",
    "logout_success": "Wylogowanie udane",
    "file_uploaded": "Plik został pomyślnie przesłany",
    "file_deleted": "Plik został pomyślnie usunięty",
    "folder_created": "Folder został pomyślnie utworzony",
    "folder_deleted": "Folder został pomyślnie usunięty",
    "file_not_found": "Plik nie znaleziony",
    "permission_denied": "Brak uprawnień",
    "storage_info": "Informacje o pamięci",
    "user_list": "Lista użytkowników",
    "volume_list": "Lista wolumenów",
    "share_list": "Lista udziałów",
    "settings_saved": "Ustawienia zapisane",
    "error_occurred": "Wystąpił błąd",
    "invalid_request": "Nieprawidłowe żądanie",
    "session_expired": "Sesja wygasła",
    "quota_exceeded": "Przekroczony limit pamięci",
    "file_exists": "Plik już istnieje",
    "invalid_path": "Nieprawidłowa ścieżka"
  }.toTable

  # 土耳其语
  translations["tr_TR"] = {
    "welcome": "Xiaosi NAS Sistemine Hoş Geldiniz",
    "login_success": "Giriş başarılı",
    "login_failed": "Geçersiz kullanıcı adı veya şifre",
    "logout_success": "Başarıyla çıkış yapıldı",
    "file_uploaded": "Dosya başarıyla yüklendi",
    "file_deleted": "Dosya başarıyla silindi",
    "folder_created": "Klasör başarıyla oluşturuldu",
    "folder_deleted": "Klasör başarıyla silindi",
    "file_not_found": "Dosya bulunamadı",
    "permission_denied": "İzin reddedildi",
    "storage_info": "Depolama Bilgisi",
    "user_list": "Kullanıcı Listesi",
    "volume_list": "Birim Listesi",
    "share_list": "Paylaşım Listesi",
    "settings_saved": "Ayarlar kaydedildi",
    "error_occurred": "Bir hata oluştu",
    "invalid_request": "Geçersiz istek",
    "session_expired": "Oturum süresi doldu",
    "quota_exceeded": "Depolama kotası aşıldı",
    "file_exists": "Dosya zaten mevcut",
    "invalid_path": "Geçersiz yol"
  }.toTable

  # 阿拉伯语
  translations["ar_SA"] = {
    "welcome": "مرحباً بك في نظام التخزين الشبكي Xiaosi",
    "login_success": "تم تسجيل الدخول بنجاح",
    "login_failed": "اسم المستخدم أو كلمة المرور غير صالحة",
    "logout_success": "تم تسجيل الخروج بنجاح",
    "file_uploaded": "تم رفع الملف بنجاح",
    "file_deleted": "تم حذف الملف بنجاح",
    "folder_created": "تم إنشاء المجلد بنجاح",
    "folder_deleted": "تم حذف المجلد بنجاح",
    "file_not_found": "الملف غير موجود",
    "permission_denied": "تم رفض الإذن",
    "storage_info": "معلومات التخزين",
    "user_list": "قائمة المستخدمين",
    "volume_list": "قائمة الأحجام",
    "share_list": "قائمة المشاركات",
    "settings_saved": "تم حفظ الإعدادات",
    "error_occurred": "حدث خطأ",
    "invalid_request": "طلب غير صالح",
    "session_expired": "انتهت صلاحية الجلسة",
    "quota_exceeded": "تم تجاوز حصة التخزين",
    "file_exists": "الملف موجود بالفعل",
    "invalid_path": "مسار غير صالح"
  }.toTable

  # 希伯来语
  translations["he_IL"] = {
    "welcome": "ברוכים הבאים למערכת ה-NAS של Xiaosi",
    "login_success": "התחברות הצליחה",
    "login_failed": "שם משתמש או סיסמה לא חוקיים",
    "logout_success": "התנתקות הצליחה",
    "file_uploaded": "הקובץ הועלה בהצלחה",
    "file_deleted": "הקובץ נמחק בהצלחה",
    "folder_created": "התיקייה נוצרה בהצלחה",
    "folder_deleted": "התיקייה נמחקה בהצלחה",
    "file_not_found": "הקובץ לא נמצא",
    "permission_denied": "ההרשאה נדחתה",
    "storage_info": "מידע אחסון",
    "user_list": "רשימת משתמשים",
    "volume_list": "רשימת כרכים",
    "share_list": "רשימת שיתופים",
    "settings_saved": "ההגדרות נשמרו",
    "error_occurred": "אירעה שגיאה",
    "invalid_request": "בקשה לא חוקית",
    "session_expired": "ההפעלה פגה",
    "quota_exceeded": "חריגה ממכסת האחסון",
    "file_exists": "הקובץ כבר קיים",
    "invalid_path": "נתיב לא חוקי"
  }.toTable

  # 泰语
  translations["th_TH"] = {
    "welcome": "ยินดีต้อนรับสู่ระบบ NAS Xiaosi",
    "login_success": "เข้าสู่ระบบสำเร็จ",
    "login_failed": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
    "logout_success": "ออกจากระบบสำเร็จ",
    "file_uploaded": "อัปโหลดไฟล์สำเร็จ",
    "file_deleted": "ลบไฟล์สำเร็จ",
    "folder_created": "สร้างโฟลเดอร์สำเร็จ",
    "folder_deleted": "ลบโฟลเดอร์สำเร็จ",
    "file_not_found": "ไม่พบไฟล์",
    "permission_denied": "การอนุญาตถูกปฏิเสธ",
    "storage_info": "ข้อมูลการจัดเก็บ",
    "user_list": "รายการผู้ใช้",
    "volume_list": "รายการโวลุ่ม",
    "share_list": "รายการแชร์",
    "settings_saved": "บันทึกการตั้งค่าแล้ว",
    "error_occurred": "เกิดข้อผิดพลาด",
    "invalid_request": "คำขอไม่ถูกต้อง",
    "session_expired": "เซสชันหมดอายุ",
    "quota_exceeded": "เกินโควต้าการจัดเก็บ",
    "file_exists": "ไฟล์มีอยู่แล้ว",
    "invalid_path": "เส้นทางไม่ถูกต้อง"
  }.toTable

  # 越南语
  translations["vi_VN"] = {
    "welcome": "Chào mừng đến với hệ thống NAS Xiaosi",
    "login_success": "Đăng nhập thành công",
    "login_failed": "Tên người dùng hoặc mật khẩu không hợp lệ",
    "logout_success": "Đăng xuất thành công",
    "file_uploaded": "Tải lên tệp thành công",
    "file_deleted": "Xóa tệp thành công",
    "folder_created": "Tạo thư mục thành công",
    "folder_deleted": "Xóa thư mục thành công",
    "file_not_found": "Không tìm thấy tệp",
    "permission_denied": "Quyền bị từ chối",
    "storage_info": "Thông tin lưu trữ",
    "user_list": "Danh sách người dùng",
    "volume_list": "Danh sách ổ đĩa",
    "share_list": "Danh sách chia sẻ",
    "settings_saved": "Đã lưu cài đặt",
    "error_occurred": "Đã xảy ra lỗi",
    "invalid_request": "Yêu cầu không hợp lệ",
    "session_expired": "Phiên đã hết hạn",
    "quota_exceeded": "Đã vượt quá hạn mức lưu trữ",
    "file_exists": "Tệp đã tồn tại",
    "invalid_path": "Đường dẫn không hợp lệ"
  }.toTable

  # 印尼语
  translations["id_ID"] = {
    "welcome": "Selamat datang di sistem NAS Xiaosi",
    "login_success": "Login berhasil",
    "login_failed": "Username atau password tidak valid",
    "logout_success": "Logout berhasil",
    "file_uploaded": "File berhasil diunggah",
    "file_deleted": "File berhasil dihapus",
    "folder_created": "Folder berhasil dibuat",
    "folder_deleted": "Folder berhasil dihapus",
    "file_not_found": "File tidak ditemukan",
    "permission_denied": "Izin ditolak",
    "storage_info": "Informasi penyimpanan",
    "user_list": "Daftar pengguna",
    "volume_list": "Daftar volume",
    "share_list": "Daftar berbagi",
    "settings_saved": "Pengaturan disimpan",
    "error_occurred": "Terjadi kesalahan",
    "invalid_request": "Permintaan tidak valid",
    "session_expired": "Sesi kedaluwarsa",
    "quota_exceeded": "Kuota penyimpanan terlampaui",
    "file_exists": "File sudah ada",
    "invalid_path": "Jalur tidak valid"
  }.toTable

  # 马来语
  translations["ms_MY"] = {
    "welcome": "Selamat datang ke sistem NAS Xiaosi",
    "login_success": "Log masuk berjaya",
    "login_failed": "Nama pengguna atau kata laluan tidak sah",
    "logout_success": "Log keluar berjaya",
    "file_uploaded": "Fail berjaya dimuat naik",
    "file_deleted": "Fail berjaya dipadam",
    "folder_created": "Folder berjaya dicipta",
    "folder_deleted": "Folder berjaya dipadam",
    "file_not_found": "Fail tidak dijumpai",
    "permission_denied": "Kebenaran ditolak",
    "storage_info": "Maklumat storan",
    "user_list": "Senarai pengguna",
    "volume_list": "Senarai volum",
    "share_list": "Senarai perkongsian",
    "settings_saved": "Tetapan disimpan",
    "error_occurred": "Ralat berlaku",
    "invalid_request": "Permintaan tidak sah",
    "session_expired": "Sesi tamat tempoh",
    "quota_exceeded": "Kuota storan melebihi",
    "file_exists": "Fail sudah wujud",
    "invalid_path": "Laluan tidak sah"
  }.toTable

  # 捷克语
  translations["cs_CZ"] = {
    "welcome": "Vítejte v systému NAS Xiaosi",
    "login_success": "Přihlášení úspěšné",
    "login_failed": "Neplatné uživatelské jméno nebo heslo",
    "logout_success": "Odhlášení úspěšné",
    "file_uploaded": "Soubor úspěšně nahrán",
    "file_deleted": "Soubor úspěšně smazán",
    "folder_created": "Složka úspěšně vytvořena",
    "folder_deleted": "Složka úspěšně smazána",
    "file_not_found": "Soubor nenalezen",
    "permission_denied": "Přístup odepřen",
    "storage_info": "Informace o úložišti",
    "user_list": "Seznam uživatelů",
    "volume_list": "Seznam svazků",
    "share_list": "Seznam sdílení",
    "settings_saved": "Nastavení uložena",
    "error_occurred": "Došlo k chybě",
    "invalid_request": "Neplatný požadavek",
    "session_expired": "Relace vypršela",
    "quota_exceeded": "Kvóta úložiště překročena",
    "file_exists": "Soubor již existuje",
    "invalid_path": "Neplatná cesta"
  }.toTable

  # 匈牙利语
  translations["hu_HU"] = {
    "welcome": "Üdvözöljük a Xiaosi NAS rendszerben",
    "login_success": "Sikeres bejelentkezés",
    "login_failed": "Érvénytelen felhasználónév vagy jelszó",
    "logout_success": "Sikeres kijelentkezés",
    "file_uploaded": "Fájl sikeresen feltöltve",
    "file_deleted": "Fájl sikeresen törölve",
    "folder_created": "Mappa sikeresen létrehozva",
    "folder_deleted": "Mappa sikeresen törölve",
    "file_not_found": "Fájl nem található",
    "permission_denied": "Hozzáférés megtagadva",
    "storage_info": "Tárolási információk",
    "user_list": "Felhasználói lista",
    "volume_list": "Kötetlista",
    "share_list": "Megosztási lista",
    "settings_saved": "Beállítások elmentve",
    "error_occurred": "Hiba történt",
    "invalid_request": "Érvénytelen kérés",
    "session_expired": "A munkamenet lejárt",
    "quota_exceeded": "Tárolási kvóta túllépve",
    "file_exists": "A fájl már létezik",
    "invalid_path": "Érvénytelen útvonal"
  }.toTable

  # 瑞典语
  translations["sv_SE"] = {
    "welcome": "Välkommen till Xiaosi NAS-system",
    "login_success": "Inloggning lyckades",
    "login_failed": "Ogiltigt användarnamn eller lösenord",
    "logout_success": "Utloggning lyckades",
    "file_uploaded": "Filen har laddats upp",
    "file_deleted": "Filen har raderats",
    "folder_created": "Mappen har skapats",
    "folder_deleted": "Mappen har raderats",
    "file_not_found": "Filen hittades inte",
    "permission_denied": "Åtkomst nekad",
    "storage_info": "Lagringsinformation",
    "user_list": "Användarlista",
    "volume_list": "Volymlista",
    "share_list": "Delningslista",
    "settings_saved": "Inställningar sparade",
    "error_occurred": "Ett fel uppstod",
    "invalid_request": "Ogiltig begäran",
    "session_expired": "Sessionen har löpt ut",
    "quota_exceeded": "Lagringskvot överskriden",
    "file_exists": "Filen finns redan",
    "invalid_path": "Ogiltig sökväg"
  }.toTable

  # 挪威语
  translations["no_NO"] = {
    "welcome": "Velkommen til Xiaosi NAS-system",
    "login_success": "Innlogging vellykket",
    "login_failed": "Ugyldig brukernavn eller passord",
    "logout_success": "Utlogging vellykket",
    "file_uploaded": "Filen er lastet opp",
    "file_deleted": "Filen er slettet",
    "folder_created": "Mappen er opprettet",
    "folder_deleted": "Mappen er slettet",
    "file_not_found": "Filen ble ikke funnet",
    "permission_denied": "Tilgang nektet",
    "storage_info": "Lagringsinformasjon",
    "user_list": "Brukerliste",
    "volume_list": "Volumliste",
    "share_list": "Delingsliste",
    "settings_saved": "Innstillinger lagret",
    "error_occurred": "Det oppstod en feil",
    "invalid_request": "Ugyldig forespørsel",
    "session_expired": "Økten har utløpt",
    "quota_exceeded": "Lagringskvote overskredet",
    "file_exists": "Filen eksisterer allerede",
    "invalid_path": "Ugyldig bane"
  }.toTable

  # 丹麦语
  translations["da_DK"] = {
    "welcome": "Velkommen til Xiaosi NAS-system",
    "login_success": "Login vellykket",
    "login_failed": "Ugyldigt brugernavn eller adgangskode",
    "logout_success": "Logout vellykket",
    "file_uploaded": "Filen er uploadet",
    "file_deleted": "Filen er slettet",
    "folder_created": "Mappen er oprettet",
    "folder_deleted": "Mappen er slettet",
    "file_not_found": "Filen blev ikke fundet",
    "permission_denied": "Adgang nægtet",
    "storage_info": "Lagerinformation",
    "user_list": "Brugerliste",
    "volume_list": "Volumenliste",
    "share_list": "Delingsliste",
    "settings_saved": "Indstillinger gemt",
    "error_occurred": "Der opstod en fejl",
    "invalid_request": "Ugyldig anmodning",
    "session_expired": "Sessionen er udløbet",
    "quota_exceeded": "Lagerkvote overskredet",
    "file_exists": "Filen eksisterer allerede",
    "invalid_path": "Ugyldig sti"
  }.toTable

  # 芬兰语
  translations["fi_FI"] = {
    "welcome": "Tervetuloa Xiaosi NAS-järjestelmään",
    "login_success": "Kirjautuminen onnistui",
    "login_failed": "Virheellinen käyttäjätunnus tai salasana",
    "logout_success": "Uloskirjautuminen onnistui",
    "file_uploaded": "Tiedosto ladattu onnistuneesti",
    "file_deleted": "Tiedosto poistettu onnistuneesti",
    "folder_created": "Kansio luotu onnistuneesti",
    "folder_deleted": "Kansio poistettu onnistuneesti",
    "file_not_found": "Tiedostoa ei löytynyt",
    "permission_denied": "Käyttöoikeus evätty",
    "storage_info": "Tallennustiedot",
    "user_list": "Käyttäjälista",
    "volume_list": "Taltiolista",
    "share_list": "Jakolista",
    "settings_saved": "Asetukset tallennettu",
    "error_occurred": "Tapahtui virhe",
    "invalid_request": "Virheellinen pyyntö",
    "session_expired": "Istunto on vanhentunut",
    "quota_exceeded": "Tallennuskiintiö ylitetty",
    "file_exists": "Tiedosto on jo olemassa",
    "invalid_path": "Virheellinen polku"
  }.toTable

# 获取翻译
proc t(key: string, lang: string = "zh_CN"): string =
  if translations.hasKey(lang) and translations[lang].hasKey(key):
    return translations[lang][key]
  elif translations.hasKey("en_US") and translations["en_US"].hasKey(key):
    return translations["en_US"][key]
  return key

# 加载配置文件
proc loadConfig(path: string): Config =
  var cfg = Config(
    port: 8097,
    language: "zh_CN",
    data_dir: "nas_data",
    receive_dir: "nas_data/received"
  )

  if fileExists(path):
    try:
      let jsonData = parseFile(path)
      if jsonData.hasKey("server"):
        if jsonData["server"].hasKey("port"):
          cfg.port = jsonData["server"]["port"].getInt()
        if jsonData["server"].hasKey("language"):
          cfg.language = jsonData["server"]["language"].getStr()

      if jsonData.hasKey("storage") and jsonData["storage"].hasKey("volumes"):
        for vol in jsonData["storage"]["volumes"]:
          cfg.volumes.add(Volume(
            name: vol["name"].getStr(),
            path: vol["path"].getStr(),
            quota_gb: vol["quota_gb"].getInt()
          ))

      if jsonData.hasKey("users"):
        for user in jsonData["users"]:
          cfg.users.add(User(
            username: user["username"].getStr(),
            password: user["password"].getStr(),
            is_admin: user["is_admin"].getBool(),
            home_dir: user["home_dir"].getStr(),
            storage_quota_gb: user["storage_quota_gb"].getInt()
          ))

      if jsonData.hasKey("smb") and jsonData["smb"].hasKey("shares"):
        for share in jsonData["smb"]["shares"]:
          cfg.smb_shares.add(SMBShare(
            name: share["name"].getStr(),
            path: share["path"].getStr(),
            comment: share["comment"].getStr(),
            read_only: share["read_only"].getBool(),
            browseable: share["browseable"].getBool(),
            guest_access: share["guest_access"].getBool()
          ))

      if jsonData.hasKey("data_dir"):
        cfg.data_dir = jsonData["data_dir"].getStr()
      if jsonData.hasKey("receive_dir"):
        cfg.receive_dir = jsonData["receive_dir"].getStr()

    except:
      echo "警告: 无法加载配置文件，使用默认配置"
  else:
    echo "警告: 配置文件不存在，使用默认配置"

  return cfg

# 生成会话ID
proc generateSessionId(username: string): string =
  let timestamp = $getTime().toUnix()
  let data = username & timestamp & $rand(1000000)
  return secureHash(data).toHex().toLowerAscii()

# 密码哈希
proc hashPassword(password: string): string =
  return secureHash(password).toHex().toLowerAscii()

# 验证用户
proc authenticateUser(username, password: string): bool =
  let hashedPass = hashPassword(password)
  for user in config.users:
    if user.username == username and user.password == hashedPass:
      return true
  return false

# 检查会话
proc checkSession(sessionId: string): string =
  if sessions.hasKey(sessionId):
    return sessions[sessionId]
  return ""

# 获取文件大小
proc getFileSize(path: string): int64 =
  if fileExists(path):
    return getFileSize(path)
  return 0

# 获取目录大小
proc getDirSize(path: string): int64 =
  result = 0
  for kind, file in walkDir(path, true):
    if kind == pcFile:
      result += getFileSize(file)
    elif kind == pcDir:
      result += getDirSize(file)

# 创建目录
proc ensureDir(path: string) =
  if not dirExists(path):
    createDir(path)

# API响应
proc jsonResponse(data: JsonNode, success: bool = true, message: string = ""): string =
  %*{
    "success": success,
    "message": message,
    "data": data
  }.pretty()

proc errorResponse(message: string, code: int = 400): string =
  %*{
    "success": false,
    "message": message,
    "code": code
  }.pretty()

# Jester路由
routes:
  # 首页
  get "/":
    resp jsonResponse(%*{
      "name": "小思超级多版本NAS",
      "version": "2.0.0",
      "language": config.language,
      "languages": LANGUAGES,
      "message": t("welcome", config.language)
    })

  # 系统状态
  get "/api/status":
    let totalSpace = 1000000000'i64 * 500  # 500GB示例
    let usedSpace = getDirSize(config.data_dir)
    resp jsonResponse(%*{
      "status": "running",
      "uptime": $getTime().toUnix(),
      "storage": {
        "total": totalSpace,
        "used": usedSpace,
        "free": totalSpace - usedSpace
      },
      "volumes": config.volumes.len,
      "users": config.users.len,
      "shares": config.smb_shares.len
    })

  # 登录
  post "/api/login":
    let body = request.body
    try:
      let json = parseJson(body)
      let username = json["username"].getStr()
      let password = json["password"].getStr()
      let lang = if json.hasKey("language"): json["language"].getStr() else: config.language

      if authenticateUser(username, password):
        let sessionId = generateSessionId(username)
        sessions[sessionId] = username
        resp jsonResponse(%*{
          "session_id": sessionId,
          "username": username
        }, true, t("login_success", lang))
      else:
        resp errorResponse(t("login_failed", lang), 401)
    except:
      resp errorResponse(t("invalid_request", config.language))

  # 登出
  post "/api/logout":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    if sessionId.len > 0 and sessions.hasKey(sessionId):
      sessions.del(sessionId)
      resp jsonResponse(%*{}, true, t("logout_success", lang))
    else:
      resp errorResponse(t("invalid_request", lang))

  # 文件列表
  get "/api/files":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    let username = checkSession(sessionId)

    if username.len == 0:
      resp errorResponse(t("session_expired", lang), 401)
      halt()

    let path = request.params.getOrDefault("path", "/")
    let realPath = if path == "/": config.data_dir else: config.data_dir / path

    if not dirExists(realPath):
      resp errorResponse(t("invalid_path", lang), 404)
      halt()

    var files: seq[JsonNode] = @[]
    for kind, file in walkDir(realPath):
      files.add(%*{
        "name": file.extractFilename(),
        "type": if kind == pcDir: "directory" else: "file",
        "size": if kind == pcFile: getFileSize(file) else: getDirSize(file),
        "modified": $file.getLastModificationTime()
      })

    resp jsonResponse(%*{
      "path": path,
      "files": files
    })

  # 上传文件
  post "/api/files/upload":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    let username = checkSession(sessionId)

    if username.len == 0:
      resp errorResponse(t("session_expired", lang), 401)
      halt()

    try:
      let body = parseJson(request.body)
      let path = body["path"].getStr()
      let filename = body["filename"].getStr()
      let content = body["content"].getStr()  # Base64编码的内容

      let realPath = config.data_dir / path / filename
      ensureDir(parentDir(realPath))

      # 解码Base64并写入文件
      let decoded = decode(content)
      writeFile(realPath, decoded)

      resp jsonResponse(%*{
        "path": path / filename,
        "size": decoded.len
      }, true, t("file_uploaded", lang))
    except:
      resp errorResponse(t("error_occurred", lang))

  # 删除文件
  delete "/api/files":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    let username = checkSession(sessionId)

    if username.len == 0:
      resp errorResponse(t("session_expired", lang), 401)
      halt()

    try:
      let body = parseJson(request.body)
      let path = body["path"].getStr()
      let realPath = config.data_dir / path

      if fileExists(realPath):
        removeFile(realPath)
        resp jsonResponse(%*{}, true, t("file_deleted", lang))
      elif dirExists(realPath):
        removeDir(realPath)
        resp jsonResponse(%*{}, true, t("folder_deleted", lang))
      else:
        resp errorResponse(t("file_not_found", lang), 404)
    except:
      resp errorResponse(t("error_occurred", lang))

  # 创建文件夹
  post "/api/folders":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    let username = checkSession(sessionId)

    if username.len == 0:
      resp errorResponse(t("session_expired", lang), 401)
      halt()

    try:
      let body = parseJson(request.body)
      let path = body["path"].getStr()
      let name = body["name"].getStr()
      let realPath = config.data_dir / path / name

      if dirExists(realPath):
        resp errorResponse(t("file_exists", lang), 409)
      else:
        createDir(realPath)
        resp jsonResponse(%*{
          "path": path / name
        }, true, t("folder_created", lang))
    except:
      resp errorResponse(t("error_occurred", lang))

  # 用户列表
  get "/api/users":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    let username = checkSession(sessionId)

    if username.len == 0:
      resp errorResponse(t("session_expired", lang), 401)
      halt()

    var users: seq[JsonNode] = @[]
    for user in config.users:
      users.add(%*{
        "username": user.username,
        "is_admin": user.is_admin,
        "home_dir": user.home_dir,
        "storage_quota_gb": user.storage_quota_gb
      })

    resp jsonResponse(%*{
      "users": users
    }, true, t("user_list", lang))

  # 存储卷列表
  get "/api/volumes":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    let username = checkSession(sessionId)

    if username.len == 0:
      resp errorResponse(t("session_expired", lang), 401)
      halt()

    var volumes: seq[JsonNode] = @[]
    for vol in config.volumes:
      volumes.add(%*{
        "name": vol.name,
        "path": vol.path,
        "quota_gb": vol.quota_gb,
        "used_gb": getDirSize(vol.path) div (1024 * 1024 * 1024)
      })

    resp jsonResponse(%*{
      "volumes": volumes
    }, true, t("volume_list", lang))

  # 共享列表
  get "/api/shares":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    let username = checkSession(sessionId)

    if username.len == 0:
      resp errorResponse(t("session_expired", lang), 401)
      halt()

    var shares: seq[JsonNode] = @[]
    for share in config.smb_shares:
      shares.add(%*{
        "name": share.name,
        "path": share.path,
        "comment": share.comment,
        "read_only": share.read_only,
        "browseable": share.browseable,
        "guest_access": share.guest_access
      })

    resp jsonResponse(%*{
      "shares": shares
    }, true, t("share_list", lang))

  # 获取配置
  get "/api/config":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    let username = checkSession(sessionId)

    if username.len == 0:
      resp errorResponse(t("session_expired", lang), 401)
      halt()

    resp jsonResponse(%*{
      "port": config.port,
      "language": config.language,
      "data_dir": config.data_dir,
      "receive_dir": config.receive_dir
    })

  # 更新配置
  put "/api/config":
    let sessionId = request.headers.getOrDefault("X-Session-ID", "")
    let lang = request.headers.getOrDefault("Accept-Language", config.language)
    let username = checkSession(sessionId)

    if username.len == 0:
      resp errorResponse(t("session_expired", lang), 401)
      halt()

    try:
      let body = parseJson(request.body)
      if body.hasKey("language"):
        let newLang = body["language"].getStr()
        if newLang in LANGUAGES:
          config.language = newLang

      resp jsonResponse(%*{}, true, t("settings_saved", lang))
    except:
      resp errorResponse(t("error_occurred", lang))

  # 翻译接口
  get "/api/i18n/@lang":
    let lang = @"lang"
    if lang in LANGUAGES:
      if translations.hasKey(lang):
        resp jsonResponse(%*{
          "language": lang,
          "translations": translations[lang]
        })
      else:
        resp errorResponse("Language not available", 404)
    else:
      resp errorResponse("Unsupported language", 400)

  # 支持的语言列表
  get "/api/languages":
    resp jsonResponse(%*{
      "languages": LANGUAGES,
      "current": config.language
    })

# 主程序入口
when isMainModule:
  echo "=========================================="
  echo "小思超级多版本NAS系统 v2.0"
  echo "=========================================="
  echo ""

  # 初始化翻译
  echo "正在加载翻译文件..."
  initTranslations()
  echo "已加载 28 种语言支持"

  # 加载配置
  let configPath = "../config/config.json"
  echo "正在加载配置文件: " & configPath
  config = loadConfig(configPath)
  echo "配置加载完成"

  # 确保数据目录存在
  ensureDir(config.data_dir)
  ensureDir(config.receive_dir)

  echo ""
  echo "服务器信息:"
  echo "  端口: " & $config.port
  echo "  语言: " & config.language
  echo "  数据目录: " & config.data_dir
  echo "  接收目录: " & config.receive_dir
  echo ""
  echo "支持的API接口:"
  echo "  GET  /                    - 首页"
  echo "  GET  /api/status          - 系统状态"
  echo "  POST /api/login           - 用户登录"
  echo "  POST /api/logout          - 用户登出"
  echo "  GET  /api/files           - 文件列表"
  echo "  POST /api/files/upload   - 上传文件"
  echo "  DELETE /api/files         - 删除文件"
  echo "  POST /api/folders         - 创建文件夹"
  echo "  GET  /api/users           - 用户列表"
  echo "  GET  /api/volumes         - 存储卷列表"
  echo "  GET  /api/shares          - 共享列表"
  echo "  GET  /api/config          - 获取配置"
  echo "  PUT  /api/config          - 更新配置"
  echo "  GET  /api/i18n/:lang      - 获取翻译"
  echo "  GET  /api/languages       - 支持的语言"
  echo ""
  echo "服务器启动中..."
  echo ""

  # 启动服务器
  runForever(port = Port(config.port))