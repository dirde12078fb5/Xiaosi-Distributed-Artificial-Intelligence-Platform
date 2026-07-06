#!/usr/bin/env ruby
# frozen_string_literal: true

require 'sinatra'
require 'sinatra/json'
require 'json'
require 'fileutils'
require 'socket'
require 'ipaddr'
require 'net/http'
require 'bcrypt'
require 'securerandom'
require 'digest'

# 配置
CONFIG_PATH = File.join(__dir__, '..', 'config', 'config.json')
BASE_DIR = File.join(__dir__, '..')

# 加载配置
def load_config
  return {} unless File.exist?(CONFIG_PATH)
  JSON.parse(File.read(CONFIG_PATH))
rescue StandardError => e
  puts "配置加载失败: #{e.message}"
  {}
end

# 保存配置
def save_config(config)
  FileUtils.mkdir_p(File.dirname(CONFIG_PATH))
  File.write(CONFIG_PATH, JSON.pretty_generate(config))
end

$config = load_config

# 初始化数据目录
DATA_DIR = $config.dig('data_dir') || 'nas_data'
RECEIVE_DIR = $config.dig('receive_dir') || File.join(DATA_DIR, 'received')
USERS_FILE = File.join(DATA_DIR, 'users.json')
SHARES_FILE = File.join(DATA_DIR, 'shares.json')
PUSH_HISTORY_FILE = File.join(DATA_DIR, 'push_history.json')

FileUtils.mkdir_p(DATA_DIR)
FileUtils.mkdir_p(RECEIVE_DIR)

# 初始化数据文件
def init_data_file(path, default = [])
  File.write(path, default.to_json) unless File.exist?(path)
end

init_data_file(USERS_FILE, [])
init_data_file(SHARES_FILE, [])
init_data_file(PUSH_HISTORY_FILE, [])

# 28种语言翻译
I18N = {
  zh_CN: {
    welcome: '欢迎使用小思NAS服务',
    storage_management: '存储管理',
    user_management: '用户管理',
    smb_shares: 'SMB共享',
    push_files: '文件推送',
    success: '操作成功',
    failed: '操作失败',
    not_found: '资源未找到',
    invalid_params: '参数无效',
    volume_created: '存储卷创建成功',
    volume_deleted: '存储卷删除成功',
    user_created: '用户创建成功',
    user_deleted: '用户删除成功',
    share_created: '共享创建成功',
    share_deleted: '共享删除成功',
    push_started: '推送已开始',
    push_completed: '推送完成',
    push_failed: '推送失败',
    file_received: '文件接收成功',
    scan_completed: '扫描完成',
    no_devices: '未发现设备'
  },
  zh_TW: {
    welcome: '歡迎使用小思NAS服務',
    storage_management: '存儲管理',
    user_management: '用戶管理',
    smb_shares: 'SMB共享',
    push_files: '文件推送',
    success: '操作成功',
    failed: '操作失敗',
    not_found: '資源未找到',
    invalid_params: '參數無效',
    volume_created: '存儲卷創建成功',
    volume_deleted: '存儲卷刪除成功',
    user_created: '用戶創建成功',
    user_deleted: '用戶刪除成功',
    share_created: '共享創建成功',
    share_deleted: '共享刪除成功',
    push_started: '推送已開始',
    push_completed: '推送完成',
    push_failed: '推送失敗',
    file_received: '文件接收成功',
    scan_completed: '掃描完成',
    no_devices: '未發現設備'
  },
  en_US: {
    welcome: 'Welcome to Xiaosi NAS Service',
    storage_management: 'Storage Management',
    user_management: 'User Management',
    smb_shares: 'SMB Shares',
    push_files: 'File Push',
    success: 'Operation successful',
    failed: 'Operation failed',
    not_found: 'Resource not found',
    invalid_params: 'Invalid parameters',
    volume_created: 'Storage volume created successfully',
    volume_deleted: 'Storage volume deleted successfully',
    user_created: 'User created successfully',
    user_deleted: 'User deleted successfully',
    share_created: 'Share created successfully',
    share_deleted: 'Share deleted successfully',
    push_started: 'Push started',
    push_completed: 'Push completed',
    push_failed: 'Push failed',
    file_received: 'File received successfully',
    scan_completed: 'Scan completed',
    no_devices: 'No devices found'
  },
  en_GB: {
    welcome: 'Welcome to Xiaosi NAS Service',
    storage_management: 'Storage Management',
    user_management: 'User Management',
    smb_shares: 'SMB Shares',
    push_files: 'File Push',
    success: 'Operation successful',
    failed: 'Operation failed',
    not_found: 'Resource not found',
    invalid_params: 'Invalid parameters',
    volume_created: 'Storage volume created successfully',
    volume_deleted: 'Storage volume deleted successfully',
    user_created: 'User created successfully',
    user_deleted: 'User deleted successfully',
    share_created: 'Share created successfully',
    share_deleted: 'Share deleted successfully',
    push_started: 'Push started',
    push_completed: 'Push completed',
    push_failed: 'Push failed',
    file_received: 'File received successfully',
    scan_completed: 'Scan completed',
    no_devices: 'No devices found'
  },
  ja: {
    welcome: 'Xiaosi NASサービスへようこそ',
    storage_management: 'ストレージ管理',
    user_management: 'ユーザー管理',
    smb_shares: 'SMB共有',
    push_files: 'ファイルプッシュ',
    success: '操作成功',
    failed: '操作失敗',
    not_found: 'リソースが見つかりません',
    invalid_params: '無効なパラメータ',
    volume_created: 'ストレージボリュームが作成されました',
    volume_deleted: 'ストレージボリュームが削除されました',
    user_created: 'ユーザーが作成されました',
    user_deleted: 'ユーザーが削除されました',
    share_created: '共有が作成されました',
    share_deleted: '共有が削除されました',
    push_started: 'プッシュ開始',
    push_completed: 'プッシュ完了',
    push_failed: 'プッシュ失敗',
    file_received: 'ファイル受信成功',
    scan_completed: 'スキャン完了',
    no_devices: 'デバイスが見つかりません'
  },
  ko: {
    welcome: 'Xiaosi NAS 서비스에 오신 것을 환영합니다',
    storage_management: '스토리지 관리',
    user_management: '사용자 관리',
    smb_shares: 'SMB 공유',
    push_files: '파일 푸시',
    success: '작업 성공',
    failed: '작업 실패',
    not_found: '리소스를 찾을 수 없습니다',
    invalid_params: '잘못된 매개변수',
    volume_created: '스토리지 볼륨 생성 성공',
    volume_deleted: '스토리지 볼륨 삭제 성공',
    user_created: '사용자 생성 성공',
    user_deleted: '사용자 삭제 성공',
    share_created: '공유 생성 성공',
    share_deleted: '공유 삭제 성공',
    push_started: '푸시 시작',
    push_completed: '푸시 완료',
    push_failed: '푸시 실패',
    file_received: '파일 수신 성공',
    scan_completed: '스캔 완료',
    no_devices: '장치를 찾을 수 없습니다'
  },
  de: {
    welcome: 'Willkommen beim Xiaosi NAS-Service',
    storage_management: 'Speicherverwaltung',
    user_management: 'Benutzerverwaltung',
    smb_shares: 'SMB-Freigaben',
    push_files: 'Datei-Push',
    success: 'Vorgang erfolgreich',
    failed: 'Vorgang fehlgeschlagen',
    not_found: 'Ressource nicht gefunden',
    invalid_params: 'Ungültige Parameter',
    volume_created: 'Speichervolume erfolgreich erstellt',
    volume_deleted: 'Speichervolume erfolgreich gelöscht',
    user_created: 'Benutzer erfolgreich erstellt',
    user_deleted: 'Benutzer erfolgreich gelöscht',
    share_created: 'Freigabe erfolgreich erstellt',
    share_deleted: 'Freigabe erfolgreich gelöscht',
    push_started: 'Push gestartet',
    push_completed: 'Push abgeschlossen',
    push_failed: 'Push fehlgeschlagen',
    file_received: 'Datei erfolgreich empfangen',
    scan_completed: 'Scan abgeschlossen',
    no_devices: 'Keine Geräte gefunden'
  },
  fr: {
    welcome: 'Bienvenue dans le service NAS Xiaosi',
    storage_management: 'Gestion du stockage',
    user_management: 'Gestion des utilisateurs',
    smb_shares: 'Partages SMB',
    push_files: 'Push de fichiers',
    success: 'Opération réussie',
    failed: 'Opération échouée',
    not_found: 'Ressource non trouvée',
    invalid_params: 'Paramètres invalides',
    volume_created: 'Volume de stockage créé avec succès',
    volume_deleted: 'Volume de stockage supprimé avec succès',
    user_created: 'Utilisateur créé avec succès',
    user_deleted: 'Utilisateur supprimé avec succès',
    share_created: 'Partage créé avec succès',
    share_deleted: 'Partage supprimé avec succès',
    push_started: 'Push démarré',
    push_completed: 'Push terminé',
    push_failed: 'Push échoué',
    file_received: 'Fichier reçu avec succès',
    scan_completed: 'Analyse terminée',
    no_devices: 'Aucun appareil trouvé'
  },
  es: {
    welcome: 'Bienvenido al servicio NAS Xiaosi',
    storage_management: 'Gestión de almacenamiento',
    user_management: 'Gestión de usuarios',
    smb_shares: 'Compartidos SMB',
    push_files: 'Envío de archivos',
    success: 'Operación exitosa',
    failed: 'Operación fallida',
    not_found: 'Recurso no encontrado',
    invalid_params: 'Parámetros inválidos',
    volume_created: 'Volumen de almacenamiento creado exitosamente',
    volume_deleted: 'Volumen de almacenamiento eliminado exitosamente',
    user_created: 'Usuario creado exitosamente',
    user_deleted: 'Usuario eliminado exitosamente',
    share_created: 'Recurso compartido creado exitosamente',
    share_deleted: 'Recurso compartido eliminado exitosamente',
    push_started: 'Envío iniciado',
    push_completed: 'Envío completado',
    push_failed: 'Envío fallido',
    file_received: 'Archivo recibido exitosamente',
    scan_completed: 'Escaneo completado',
    no_devices: 'No se encontraron dispositivos'
  },
  it: {
    welcome: 'Benvenuto nel servizio NAS Xiaosi',
    storage_management: 'Gestione archiviazione',
    user_management: 'Gestione utenti',
    smb_shares: 'Condivisioni SMB',
    push_files: 'Push file',
    success: 'Operazione riuscita',
    failed: 'Operazione fallita',
    not_found: 'Risorsa non trovata',
    invalid_params: 'Parametri non validi',
    volume_created: 'Volume di archiviazione creato con successo',
    volume_deleted: 'Volume di archiviazione eliminato con successo',
    user_created: 'Utente creato con successo',
    user_deleted: 'Utente eliminato con successo',
    share_created: 'Condivisione creata con successo',
    share_deleted: 'Condivisione eliminata con successo',
    push_started: 'Push avviato',
    push_completed: 'Push completato',
    push_failed: 'Push fallito',
    file_received: 'File ricevuto con successo',
    scan_completed: 'Scansione completata',
    no_devices: 'Nessun dispositivo trovato'
  },
  pt: {
    welcome: 'Bem-vindo ao serviço NAS Xiaosi',
    storage_management: 'Gerenciamento de armazenamento',
    user_management: 'Gerenciamento de usuários',
    smb_shares: 'Compartilhamentos SMB',
    push_files: 'Envio de arquivos',
    success: 'Operação bem-sucedida',
    failed: 'Operação falhou',
    not_found: 'Recurso não encontrado',
    invalid_params: 'Parâmetros inválidos',
    volume_created: 'Volume de armazenamento criado com sucesso',
    volume_deleted: 'Volume de armazenamento excluído com sucesso',
    user_created: 'Usuário criado com sucesso',
    user_deleted: 'Usuário excluído com sucesso',
    share_created: 'Compartilhamento criado com sucesso',
    share_deleted: 'Compartilhamento excluído com sucesso',
    push_started: 'Envio iniciado',
    push_completed: 'Envio concluído',
    push_failed: 'Envio falhou',
    file_received: 'Arquivo recebido com sucesso',
    scan_completed: 'Varredura concluída',
    no_devices: 'Nenhum dispositivo encontrado'
  },
  ru: {
    welcome: 'Добро пожаловать в сервис NAS Xiaosi',
    storage_management: 'Управление хранилищем',
    user_management: 'Управление пользователями',
    smb_shares: 'SMB-ресурсы',
    push_files: 'Отправка файлов',
    success: 'Операция успешна',
    failed: 'Операция не удалась',
    not_found: 'Ресурс не найден',
    invalid_params: 'Неверные параметры',
    volume_created: 'Том хранилища успешно создан',
    volume_deleted: 'Том хранилища успешно удален',
    user_created: 'Пользователь успешно создан',
    user_deleted: 'Пользователь успешно удален',
    share_created: 'Ресурс успешно создан',
    share_deleted: 'Ресурс успешно удален',
    push_started: 'Отправка началась',
    push_completed: 'Отправка завершена',
    push_failed: 'Отправка не удалась',
    file_received: 'Файл успешно получен',
    scan_completed: 'Сканирование завершено',
    no_devices: 'Устройства не найдены'
  },
  uk: {
    welcome: 'Ласкаво просимо до сервісу NAS Xiaosi',
    storage_management: 'Управління сховищем',
    user_management: 'Управління користувачами',
    smb_shares: 'SMB-ресурси',
    push_files: 'Відправка файлів',
    success: 'Операція успішна',
    failed: 'Операція не вдалася',
    not_found: 'Ресурс не знайдено',
    invalid_params: 'Невірні параметри',
    volume_created: 'Том сховища успішно створено',
    volume_deleted: 'Том сховища успішно видалено',
    user_created: 'Користувача успішно створено',
    user_deleted: 'Користувача успішно видалено',
    share_created: 'Ресурс успішно створено',
    share_deleted: 'Ресурс успішно видалено',
    push_started: 'Відправка почалася',
    push_completed: 'Відправка завершена',
    push_failed: 'Відправка не вдалася',
    file_received: 'Файл успішно отримано',
    scan_completed: 'Сканування завершено',
    no_devices: 'Пристрої не знайдено'
  },
  pl: {
    welcome: 'Witamy w usłudze NAS Xiaosi',
    storage_management: 'Zarządzanie pamięcią',
    user_management: 'Zarządzanie użytkownikami',
    smb_shares: 'Udziały SMB',
    push_files: 'Przesyłanie plików',
    success: 'Operacja zakończona sukcesem',
    failed: 'Operacja nie powiodła się',
    not_found: 'Zasób nie znaleziony',
    invalid_params: 'Nieprawidłowe parametry',
    volume_created: 'Wolumin pamięci został utworzony',
    volume_deleted: 'Wolumin pamięci został usunięty',
    user_created: 'Użytkownik został utworzony',
    user_deleted: 'Użytkownik został usunięty',
    share_created: 'Udział został utworzony',
    share_deleted: 'Udział został usunięty',
    push_started: 'Przesyłanie rozpoczęte',
    push_completed: 'Przesyłanie zakończone',
    push_failed: 'Przesyłanie nie powiodło się',
    file_received: 'Plik odebrany pomyślnie',
    scan_completed: 'Skanowanie zakończone',
    no_devices: 'Nie znaleziono urządzeń'
  },
  cs: {
    welcome: 'Vítejte ve službě NAS Xiaosi',
    storage_management: 'Správa úložiště',
    user_management: 'Správa uživatelů',
    smb_shares: 'SMB sdílení',
    push_files: 'Odesílání souborů',
    success: 'Operace úspěšná',
    failed: 'Operace selhala',
    not_found: 'Zdroj nenalezen',
    invalid_params: 'Neplatné parametry',
    volume_created: 'Svazek úložiště úspěšně vytvořen',
    volume_deleted: 'Svazek úložiště úspěšně smazán',
    user_created: 'Uživatel úspěšně vytvořen',
    user_deleted: 'Uživatel úspěšně smazán',
    share_created: 'Sdílení úspěšně vytvořeno',
    share_deleted: 'Sdílení úspěšně smazáno',
    push_started: 'Odesílání zahájeno',
    push_completed: 'Odesílání dokončeno',
    push_failed: 'Odesílání selhalo',
    file_received: 'Soubor úspěšně přijat',
    scan_completed: 'Skenování dokončeno',
    no_devices: 'Žádná zařízení nenalezena'
  },
  ar: {
    welcome: 'مرحبًا بك في خدمة NAS Xiaosi',
    storage_management: 'إدارة التخزين',
    user_management: 'إدارة المستخدمين',
    smb_shares: 'مشاركات SMB',
    push_files: 'إرسال الملفات',
    success: 'عملية ناجحة',
    failed: 'فشلت العملية',
    not_found: 'المورد غير موجود',
    invalid_params: 'معلمات غير صالحة',
    volume_created: 'تم إنشاء وحدة التخزين بنجاح',
    volume_deleted: 'تم حذف وحدة التخزين بنجاح',
    user_created: 'تم إنشاء المستخدم بنجاح',
    user_deleted: 'تم حذف المستخدم بنجاح',
    share_created: 'تم إنشاء المشاركة بنجاح',
    share_deleted: 'تم حذف المشاركة بنجاح',
    push_started: 'بدأ الإرسال',
    push_completed: 'اكتمل الإرسال',
    push_failed: 'فشل الإرسال',
    file_received: 'تم استلام الملف بنجاح',
    scan_completed: 'اكتمل المسح',
    no_devices: 'لم يتم العثور على أجهزة'
  },
  he: {
    welcome: 'ברוכים הבאים לשירות NAS של Xiaosi',
    storage_management: 'ניהול אחסון',
    user_management: 'ניהול משתמשים',
    smb_shares: 'שיתופי SMB',
    push_files: 'שליחת קבצים',
    success: 'הפעולה הצליחה',
    failed: 'הפעולה נכשלה',
    not_found: 'המשאב לא נמצא',
    invalid_params: 'פרמטרים לא חוקיים',
    volume_created: 'אחסון נוצר בהצלחה',
    volume_deleted: 'אחסון נמחק בהצלחה',
    user_created: 'משתמש נוצר בהצלחה',
    user_deleted: 'משתמש נמחק בהצלחה',
    share_created: 'שיתוף נוצר בהצלחה',
    share_deleted: 'שיתוף נמחק בהצלחה',
    push_started: 'השליחה החלה',
    push_completed: 'השליחה הושלמה',
    push_failed: 'השליחה נכשלה',
    file_received: 'הקובץ התקבל בהצלחה',
    scan_completed: 'הסריקה הושלמה',
    no_devices: 'לא נמצאו מכשירים'
  },
  tr: {
    welcome: 'Xiaosi NAS Hizmetine Hoş Geldiniz',
    storage_management: 'Depolama Yönetimi',
    user_management: 'Kullanıcı Yönetimi',
    smb_shares: 'SMB Paylaşımları',
    push_files: 'Dosya Gönderme',
    success: 'İşlem başarılı',
    failed: 'İşlem başarısız',
    not_found: 'Kaynak bulunamadı',
    invalid_params: 'Geçersiz parametreler',
    volume_created: 'Depolama birimi başarıyla oluşturuldu',
    volume_deleted: 'Depolama birimi başarıyla silindi',
    user_created: 'Kullanıcı başarıyla oluşturuldu',
    user_deleted: 'Kullanıcı başarıyla silindi',
    share_created: 'Paylaşım başarıyla oluşturuldu',
    share_deleted: 'Paylaşım başarıyla silindi',
    push_started: 'Gönderme başladı',
    push_completed: 'Gönderme tamamlandı',
    push_failed: 'Gönderme başarısız',
    file_received: 'Dosya başarıyla alındı',
    scan_completed: 'Tarama tamamlandı',
    no_devices: 'Cihaz bulunamadı'
  },
  hi: {
    welcome: 'Xiaosi NAS सेवा में आपका स्वागत है',
    storage_management: 'भंडारण प्रबंधन',
    user_management: 'उपयोगकर्ता प्रबंधन',
    smb_shares: 'SMB शेयर',
    push_files: 'फ़ाइल भेजें',
    success: 'ऑपरेशन सफल',
    failed: 'ऑपरेशन विफल',
    not_found: 'संसाधन नहीं मिला',
    invalid_params: 'अमान्य पैरामीटर',
    volume_created: 'भंडारण वॉल्यूम सफलतापूर्वक बनाया गया',
    volume_deleted: 'भंडारण वॉल्यूम सफलतापूर्वक हटाया गया',
    user_created: 'उपयोगकर्ता सफलतापूर्वक बनाया गया',
    user_deleted: 'उपयोगकर्ता सफलतापूर्वक हटाया गया',
    share_created: 'शेयर सफलतापूर्वक बनाया गया',
    share_deleted: 'शेयर सफलतापूर्वक हटाया गया',
    push_started: 'भेजना शुरू हुआ',
    push_completed: 'भेजना पूरा हुआ',
    push_failed: 'भेजना विफल',
    file_received: 'फ़ाइल सफलतापूर्वक प्राप्त हुई',
    scan_completed: 'स्कैन पूरा हुआ',
    no_devices: 'कोई डिवाइस नहीं मिला'
  },
  th: {
    welcome: 'ยินดีต้อนรับสู่บริการ NAS Xiaosi',
    storage_management: 'การจัดการพื้นที่จัดเก็ง',
    user_management: 'การจัดการผู้ใช้',
    smb_shares: 'การแชร์ SMB',
    push_files: 'ส่งไฟล์',
    success: 'ดำเนินการสำเร็จ',
    failed: 'ดำเนินการไม่สำเร็จ',
    not_found: 'ไม่พบทรัพยากร',
    invalid_params: 'พารามิเตอร์ไม่ถูกต้อง',
    volume_created: 'สร้างโวลุ่มจัดเก็งสำเร็จ',
    volume_deleted: 'ลบโวลุ่มจัดเก็งสำเร็จ',
    user_created: 'สร้างผู้ใช้สำเร็จ',
    user_deleted: 'ลบผู้ใช้สำเร็จ',
    share_created: 'สร้างการแชร์สำเร็จ',
    share_deleted: 'ลบการแชร์สำเร็จ',
    push_started: 'เริ่มส่งแล้ว',
    push_completed: 'ส่งเสร็จสมบูรณ์',
    push_failed: 'ส่งไม่สำเร็จ',
    file_received: 'รับไฟล์สำเร็จ',
    scan_completed: 'สแกนเสร็จสมบูรณ์',
    no_devices: 'ไม่พบอุปกรณ์'
  },
  vi: {
    welcome: 'Chào mừng đến với dịch vụ NAS Xiaosi',
    storage_management: 'Quản lý lưu trữ',
    user_management: 'Quản lý người dùng',
    smb_shares: 'Chia sẻ SMB',
    push_files: 'Gửi tệp',
    success: 'Thao tác thành công',
    failed: 'Thao tác thất bại',
    not_found: 'Không tìm thấy tài nguyên',
    invalid_params: 'Tham số không hợp lệ',
    volume_created: 'Tạo ổ lưu trữ thành công',
    volume_deleted: 'Xóa ổ lưu trữ thành công',
    user_created: 'Tạo người dùng thành công',
    user_deleted: 'Xóa người dùng thành công',
    share_created: 'Tạo chia sẻ thành công',
    share_deleted: 'Xóa chia sẻ thành công',
    push_started: 'Bắt đầu gửi',
    push_completed: 'Gửi hoàn tất',
    push_failed: 'Gửi thất bại',
    file_received: 'Nhận tệp thành công',
    scan_completed: 'Quét hoàn tất',
    no_devices: 'Không tìm thấy thiết bị'
  },
  id: {
    welcome: 'Selamat datang di layanan NAS Xiaosi',
    storage_management: 'Manajemen Penyimpanan',
    user_management: 'Manajemen Pengguna',
    smb_shares: 'Berbagi SMB',
    push_files: 'Kirim File',
    success: 'Operasi berhasil',
    failed: 'Operasi gagal',
    not_found: 'Sumber daya tidak ditemukan',
    invalid_params: 'Parameter tidak valid',
    volume_created: 'Volume penyimpanan berhasil dibuat',
    volume_deleted: 'Volume penyimpanan berhasil dihapus',
    user_created: 'Pengguna berhasil dibuat',
    user_deleted: 'Pengguna berhasil dihapus',
    share_created: 'Berbagi berhasil dibuat',
    share_deleted: 'Berbagi berhasil dihapus',
    push_started: 'Pengiriman dimulai',
    push_completed: 'Pengiriman selesai',
    push_failed: 'Pengiriman gagal',
    file_received: 'File berhasil diterima',
    scan_completed: 'Pemindaian selesai',
    no_devices: 'Tidak ada perangkat ditemukan'
  },
  nl: {
    welcome: 'Welkom bij de NAS-service van Xiaosi',
    storage_management: 'Opslagbeheer',
    user_management: 'Gebruikersbeheer',
    smb_shares: 'SMB-shares',
    push_files: 'Bestanden verzenden',
    success: 'Bewerking geslaagd',
    failed: 'Bewerking mislukt',
    not_found: 'Bron niet gevonden',
    invalid_params: 'Ongeldige parameters',
    volume_created: 'Opslagvolume succesvol aangemaakt',
    volume_deleted: 'Opslagvolume succesvol verwijderd',
    user_created: 'Gebruiker succesvol aangemaakt',
    user_deleted: 'Gebruiker succesvol verwijderd',
    share_created: 'Share succesvol aangemaakt',
    share_deleted: 'Share succesvol verwijderd',
    push_started: 'Verzenden gestart',
    push_completed: 'Verzenden voltooid',
    push_failed: 'Verzenden mislukt',
    file_received: 'Bestand succesvol ontvangen',
    scan_completed: 'Scan voltooid',
    no_devices: 'Geen apparaten gevonden'
  },
  sv: {
    welcome: 'Välkommen till Xiaosi NAS-tjänst',
    storage_management: 'Lagringshantering',
    user_management: 'Användarhantering',
    smb_shares: 'SMB-utdelningar',
    push_files: 'Skicka filer',
    success: 'Åtgärd lyckades',
    failed: 'Åtgärd misslyckades',
    not_found: 'Resursen hittades inte',
    invalid_params: 'Ogiltiga parametrar',
    volume_created: 'Lagringsvolym skapad',
    volume_deleted: 'Lagringsvolym borttagen',
    user_created: 'Användare skapad',
    user_deleted: 'Användare borttagen',
    share_created: 'Utdelning skapad',
    share_deleted: 'Utdelning borttagen',
    push_started: 'Sändning startad',
    push_completed: 'Sändning slutförd',
    push_failed: 'Sändning misslyckades',
    file_received: 'Fil mottagen',
    scan_completed: 'Skanning slutförd',
    no_devices: 'Inga enheter hittades'
  },
  da: {
    welcome: 'Velkommen til Xiaosi NAS-tjeneste',
    storage_management: 'Lagerstyring',
    user_management: 'Brugerstyring',
    smb_shares: 'SMB-delinger',
    push_files: 'Send filer',
    success: 'Handling lykkedes',
    failed: 'Handling mislykkedes',
    not_found: 'Ressource ikke fundet',
    invalid_params: 'Ugyldige parametre',
    volume_created: 'Lagervolume oprettet',
    volume_deleted: 'Lagervolume slettet',
    user_created: 'Bruger oprettet',
    user_deleted: 'Bruger slettet',
    share_created: 'Deling oprettet',
    share_deleted: 'Deling slettet',
    push_started: 'Afsendelse startet',
    push_completed: 'Afsendelse afsluttet',
    push_failed: 'Afsendelse mislykkedes',
    file_received: 'Fil modtaget',
    scan_completed: 'Scanning afsluttet',
    no_devices: 'Ingen enheder fundet'
  },
  fi: {
    welcome: 'Tervetuloa Xiaosi NAS-palveluun',
    storage_management: 'Tallennustilan hallinta',
    user_management: 'Käyttäjien hallinta',
    smb_shares: 'SMB-jaot',
    push_files: 'Lähetä tiedostoja',
    success: 'Toiminto onnistui',
    failed: 'Toiminto epäonnistui',
    not_found: 'Resurssia ei löydy',
    invalid_params: 'Virheelliset parametrit',
    volume_created: 'Tallennustilan asema luotu',
    volume_deleted: 'Tallennustilan asema poistettu',
    user_created: 'Käyttäjä luotu',
    user_deleted: 'Käyttäjä poistettu',
    share_created: 'Jako luotu',
    share_deleted: 'Jako poistettu',
    push_started: 'Lähetys aloitettu',
    push_completed: 'Lähetys valmis',
    push_failed: 'Lähetys epäonnistui',
    file_received: 'Tiedosto vastaanotettu',
    scan_completed: 'Skannaus valmis',
    no_devices: 'Laitteita ei löydy'
  },
  hu: {
    welcome: 'Üdvözöljük a Xiaosi NAS szolgáltatásban',
    storage_management: 'Tároláskezelés',
    user_management: 'Felhasználókezelés',
    smb_shares: 'SMB megosztások',
    push_files: 'Fájlküldés',
    success: 'Művelet sikeres',
    failed: 'Művelet sikertelen',
    not_found: 'Erőforrás nem található',
    invalid_params: 'Érvénytelen paraméterek',
    volume_created: 'Tárolókötet sikeresen létrehozva',
    volume_deleted: 'Tárolókötet sikeresen törölve',
    user_created: 'Felhasználó sikeresen létrehozva',
    user_deleted: 'Felhasználó sikeresen törölve',
    share_created: 'Megosztás sikeresen létrehozva',
    share_deleted: 'Megosztás sikeresen törölve',
    push_started: 'Küldés elindítva',
    push_completed: 'Küldés befejezve',
    push_failed: 'Küldés sikertelen',
    file_received: 'Fájl sikeresen fogadva',
    scan_completed: 'Beolvasás befejezve',
    no_devices: 'Nem található eszköz'
  },
  ro: {
    welcome: 'Bun venit la serviciul NAS Xiaosi',
    storage_management: 'Gestionare stocare',
    user_management: 'Gestionare utilizatori',
    smb_shares: 'Partajări SMB',
    push_files: 'Trimitere fișiere',
    success: 'Operație reușită',
    failed: 'Operație eșuată',
    not_found: 'Resursă negăsită',
    invalid_params: 'Parametri invalizi',
    volume_created: 'Volum de stocare creat cu succes',
    volume_deleted: 'Volum de stocare șters cu succes',
    user_created: 'Utilizator creat cu succes',
    user_deleted: 'Utilizator șters cu succes',
    share_created: 'Partajare creată cu succes',
    share_deleted: 'Partajare ștearsă cu succes',
    push_started: 'Trimitere începută',
    push_completed: 'Trimitere finalizată',
    push_failed: 'Trimitere eșuată',
    file_received: 'Fișier primit cu succes',
    scan_completed: 'Scanare finalizată',
    no_devices: 'Niciun dispozitiv găsit'
  }
}.freeze

# 获取翻译
def t(key, lang = nil)
  lang ||= $config.dig('server', 'language') || 'zh_CN'
  lang = lang.to_sym
  I18N.dig(lang, key.to_sym) || I18N.dig(:zh_CN, key.to_sym) || key.to_s
end

# 辅助方法
def json_response(success, message, data = nil)
  response = { success: success, message: message }
  response[:data] = data if data
  response
end

def read_json_file(path)
  return [] unless File.exist?(path)
  JSON.parse(File.read(path))
rescue StandardError
  []
end

def write_json_file(path, data)
  File.write(path, JSON.pretty_generate(data))
end

def get_local_ips
  ips = []
  Socket.getifaddrs.each do |ifaddr|
    next unless ifaddr.addr && ifaddr.addr.ipv4? && !ifaddr.addr.ipv4_loopback?
    ips << {
      interface: ifaddr.name,
      ip: ifaddr.addr.ip_address,
      netmask: ifaddr.netmask&.ip_address
    }
  end
  ips
end

def scan_network(port = 8080, timeout = 1)
  devices = []
  local_ips = get_local_ips

  local_ips.each do |ip_info|
    ip = ip_info[:ip]
    next unless ip

    begin
      ipaddr = IPAddr.new(ip)
      network = ipaddr.mask(ip_info[:netmask] || '255.255.255.0')

      (1..254).each do |i|
        host_ip = network.to_range.first.to_s.sub(/\.\d+$/, ".#{i}")
        next if host_ip == ip

        Thread.new do
          begin
            socket = TCPSocket.new(host_ip, port)
            socket.close
            devices << { ip: host_ip, port: port, status: 'online' }
          rescue StandardError
            # 忽略连接失败的设备
          end
        end
      end
    rescue StandardError
      next
    end
  end

  sleep(timeout)
  devices
rescue StandardError => e
  []
end

# Sinatra 配置
set :port, $config.dig('server', 'port') || 8087
set :bind, $config.dig('server', 'host') || '0.0.0.0'
set :public_folder, File.join(BASE_DIR, 'web')

# 中间件
before do
  content_type :json
end

# ==================== 首页和静态文件 ====================

get '/' do
  send_file File.join(settings.public_folder, 'index.html')
rescue StandardError
  json_response(true, t(:welcome), {
    service: 'Xiaosi NAS Service',
    version: '2.0.0',
    language: $config.dig('server', 'language') || 'zh_CN',
    endpoints: {
      storage: '/api/storage/volumes',
      users: '/api/users',
      smb: '/api/smb/shares',
      ip: '/api/ip/local',
      push: '/api/push/targets',
      i18n: '/api/i18n/'
    }
  })
end

# ==================== 存储管理 ====================

get '/api/storage/volumes' do
  volumes = $config.dig('storage', 'volumes') || []
  volumes.each do |vol|
    path = vol['path']
    if path && File.directory?(path)
      vol['exists'] = true
      vol['used_gb'] = `du -sb "#{path}" 2>/dev/null`.split.first.to_f / (1024**3)
    else
      vol['exists'] = false
      vol['used_gb'] = 0
    end
  end
  json_response(true, t(:success), volumes)
end

post '/api/storage/volumes' do
  begin
    data = JSON.parse(request.body.read)
    name = data['name']
    path = data['path']
    quota_gb = data['quota_gb'] || 100

    halt 400, json_response(false, t(:invalid_params)).to_json unless name && path

    $config['storage'] ||= {}
    $config['storage']['volumes'] ||= []

    volume = {
      'name' => name,
      'path' => path,
      'quota_gb' => quota_gb,
      'created_at' => Time.now.strftime('%Y-%m-%d %H:%M:%S')
    }

    $config['storage']['volumes'] << volume
    save_config($config)

    FileUtils.mkdir_p(path)

    json_response(true, t(:volume_created), volume)
  rescue StandardError => e
    json_response(false, "#{t(:failed)}: #{e.message}")
  end
end

post '/api/storage/volumes/delete' do
  begin
    data = JSON.parse(request.body.read)
    name = data['name']

    halt 400, json_response(false, t(:invalid_params)).to_json unless name

    volumes = $config.dig('storage', 'volumes') || []
    volume = volumes.find { |v| v['name'] == name }

    halt 404, json_response(false, t(:not_found)).to_json unless volume

    $config['storage']['volumes'].delete(volume)
    save_config($config)

    json_response(true, t(:volume_deleted))
  rescue StandardError => e
    json_response(false, "#{t(:failed)}: #{e.message}")
  end
end

# ==================== 用户管理 ====================

get '/api/users' do
  users = read_json_file(USERS_FILE)
  users.each { |u| u.delete('password') }
  json_response(true, t(:success), users)
end

post '/api/users' do
  begin
    data = JSON.parse(request.body.read)
    username = data['username']
    password = data['password']

    halt 400, json_response(false, t(:invalid_params)).to_json unless username && password

    users = read_json_file(USERS_FILE)

    halt 400, json_response(false, '用户已存在').to_json if users.any? { |u| u['username'] == username }

    user = {
      'id' => SecureRandom.uuid,
      'username' => username,
      'password' => BCrypt::Password.create(password),
      'created_at' => Time.now.strftime('%Y-%m-%d %H:%M:%S')
    }

    users << user
    write_json_file(USERS_FILE, users)

    user.delete('password')
    json_response(true, t(:user_created), user)
  rescue StandardError => e
    json_response(false, "#{t(:failed)}: #{e.message}")
  end
end

post '/api/users/delete' do
  begin
    data = JSON.parse(request.body.read)
    user_id = data['id'] || data['username']

    halt 400, json_response(false, t(:invalid_params)).to_json unless user_id

    users = read_json_file(USERS_FILE)
    user = users.find { |u| u['id'] == user_id || u['username'] == user_id }

    halt 404, json_response(false, t(:not_found)).to_json unless user

    users.delete(user)
    write_json_file(USERS_FILE, users)

    json_response(true, t(:user_deleted))
  rescue StandardError => e
    json_response(false, "#{t(:failed)}: #{e.message}")
  end
end

# ==================== SMB共享 ====================

get '/api/smb/shares' do
  shares = read_json_file(SHARES_FILE)
  json_response(true, t(:success), shares)
end

post '/api/smb/shares' do
  begin
    data = JSON.parse(request.body.read)
    name = data['name']
    path = data['path']

    halt 400, json_response(false, t(:invalid_params)).to_json unless name && path

    shares = read_json_file(SHARES_FILE)

    share = {
      'id' => SecureRandom.uuid,
      'name' => name,
      'path' => path,
      'comment' => data['comment'] || '',
      'read_only' => data['read_only'] || false,
      'browseable' => data['browseable'] || true,
      'created_at' => Time.now.strftime('%Y-%m-%d %H:%M:%S')
    }

    shares << share
    write_json_file(SHARES_FILE, shares)

    json_response(true, t(:share_created), share)
  rescue StandardError => e
    json_response(false, "#{t(:failed)}: #{e.message}")
  end
end

post '/api/smb/shares/delete' do
  begin
    data = JSON.parse(request.body.read)
    share_id = data['id'] || data['name']

    halt 400, json_response(false, t(:invalid_params)).to_json unless share_id

    shares = read_json_file(SHARES_FILE)
    share = shares.find { |s| s['id'] == share_id || s['name'] == share_id }

    halt 404, json_response(false, t(:not_found)).to_json unless share

    shares.delete(share)
    write_json_file(SHARES_FILE, shares)

    json_response(true, t(:share_deleted))
  rescue StandardError => e
    json_response(false, "#{t(:failed)}: #{e.message}")
  end
end

# ==================== IP与推送 ====================

get '/api/ip/local' do
  ips = get_local_ips
  json_response(true, t(:success), ips)
end

get '/api/ip/scan' do
  port = params['port']&.to_i || 8080
  devices = scan_network(port)
  json_response(true, t(:scan_completed), devices)
end

get '/api/push/targets' do
  targets = $config.dig('push', 'targets') || []
  json_response(true, t(:success), targets)
end

post '/api/push/targets' do
  begin
    data = JSON.parse(request.body.read)
    name = data['name']
    ip = data['ip']
    port = data['port'] || 8080

    halt 400, json_response(false, t(:invalid_params)).to_json unless name && ip

    $config['push'] ||= {}
    $config['push']['targets'] ||= []

    target = {
      'id' => SecureRandom.uuid,
      'name' => name,
      'ip' => ip,
      'port' => port,
      'created_at' => Time.now.strftime('%Y-%m-%d %H:%M:%S')
    }

    $config['push']['targets'] << target
    save_config($config)

    json_response(true, t(:success), target)
  rescue StandardError => e
    json_response(false, "#{t(:failed)}: #{e.message}")
  end
end

post '/api/push/folder' do
  begin
    data = JSON.parse(request.body.read)
    folder_path = data['folder_path']
    target_id = data['target_id']

    halt 400, json_response(false, t(:invalid_params)).to_json unless folder_path && target_id

    targets = $config.dig('push', 'targets') || []
    target = targets.find { |t| t['id'] == target_id }

    halt 404, json_response(false, t(:not_found)).to_json unless target

    unless File.directory?(folder_path)
      halt 400, json_response(false, '文件夹不存在').to_json
    end

    # 记录推送历史
    history = {
      'id' => SecureRandom.uuid,
      'folder_path' => folder_path,
      'target' => target,
      'status' => 'started',
      'started_at' => Time.now.strftime('%Y-%m-%d %H:%M:%S')
    }

    push_history = read_json_file(PUSH_HISTORY_FILE)
    push_history << history
    write_json_file(PUSH_HISTORY_FILE, push_history)

    # 执行推送（异步）
    Thread.new do
      begin
        files_count = 0
        folder_name = File.basename(folder_path)

        Dir.glob(File.join(folder_path, '**', '*')).each do |file|
          next unless File.file?(file)

          relative_path = file.sub(folder_path, '').gsub(/^\\/, '')
          files_count += 1

          # 这里应该实现实际的文件推送逻辑
          # 使用 HTTP multipart/form-data 发送文件
          uri = URI("http://#{target['ip']}:#{target['port']}/api/push/receive")

          boundary = "----XiaosiNASPush#{SecureRandom.hex(16)}"
          post_body = []
          post_body << "--#{boundary}\r\n"
          post_body << "Content-Disposition: form-data; name=\"folder\"\r\n\r\n#{folder_name}\r\n"
          post_body << "--#{boundary}\r\n"
          post_body << "Content-Disposition: form-data; name=\"filepath\"\r\n\r\n#{relative_path}\r\n"
          post_body << "--#{boundary}\r\n"
          post_body << "Content-Disposition: form-data; name=\"file\"; filename=\"#{File.basename(file)}\"\r\n"
          post_body << "Content-Type: application/octet-stream\r\n\r\n"
          post_body << File.binread(file)
          post_body << "\r\n--#{boundary}--\r\n"

          http = Net::HTTP.new(uri.host, uri.port)
          http.read_timeout = 300
          request = Net::HTTP::Post.new(uri.request_uri)
          request['Content-Type'] = "multipart/form-data; boundary=#{boundary}"
          request.body = post_body.join

          http.request(request)
        end

        # 更新推送状态
        push_history = read_json_file(PUSH_HISTORY_FILE)
        record = push_history.find { |h| h['id'] == history['id'] }
        if record
          record['status'] = 'completed'
          record['files_count'] = files_count
          record['completed_at'] = Time.now.strftime('%Y-%m-%d %H:%M:%S')
          write_json_file(PUSH_HISTORY_FILE, push_history)
        end
      rescue StandardError => e
        push_history = read_json_file(PUSH_HISTORY_FILE)
        record = push_history.find { |h| h['id'] == history['id'] }
        if record
          record['status'] = 'failed'
          record['error'] = e.message
          record['completed_at'] = Time.now.strftime('%Y-%m-%d %H:%M:%S')
          write_json_file(PUSH_HISTORY_FILE, push_history)
        end
      end
    end

    json_response(true, t(:push_started), history)
  rescue StandardError => e
    json_response(false, "#{t(:failed)}: #{e.message}")
  end
end

get '/api/push/status' do
  push_history = read_json_file(PUSH_HISTORY_FILE)
  json_response(true, t(:success), push_history.last(20))
end

post '/api/push/receive' do
  begin
    folder = params[:folder]
    filepath = params[:filepath]
    file = params[:file]

    halt 400, json_response(false, t(:invalid_params)).to_json unless folder && file

    # 创建接收目录
    receive_path = File.join(RECEIVE_DIR, folder)
    receive_path = File.join(receive_path, filepath) if filepath && !filepath.empty?
    FileUtils.mkdir_p(File.dirname(receive_path))

    # 保存文件
    if file[:tempfile]
      FileUtils.cp(file[:tempfile].path, receive_path)
    end

    json_response(true, t(:file_received), {
      folder: folder,
      filepath: filepath,
      filename: file[:filename],
      size: file[:tempfile] ? File.size(file[:tempfile].path) : 0
    })
  rescue StandardError => e
    json_response(false, "#{t(:failed)}: #{e.message}")
  end
end

# ==================== 多语言 ====================

get '/api/i18n/?' do
  lang = params[:lang] || $config.dig('server', 'language') || 'zh_CN'
  translations = I18N[lang.to_sym] || I18N[:zh_CN]
  json_response(true, t(:success), { language: lang, translations: translations })
end

# ==================== 错误处理 ====================

not_found do
  json_response(false, t(:not_found))
end

error do
  json_response(false, "#{t(:failed)}: #{env['sinatra.error'].message}")
end

# ==================== 启动信息 ====================

puts '=' * 60
puts "小思NAS服务 (Ruby版) v2.0.0"
puts '=' * 60
puts "监听地址: #{settings.bind}:#{settings.port}"
puts "配置文件: #{CONFIG_PATH}"
puts "数据目录: #{DATA_DIR}"
puts "接收目录: #{RECEIVE_DIR}"
puts '=' * 60