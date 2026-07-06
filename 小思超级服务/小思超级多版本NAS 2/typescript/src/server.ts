import express, { Request, Response, Application } from 'express';
import cors from 'cors';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import * as os from 'os';
import * as http from 'http';

// ==========================================
// 类型定义
// ==========================================

interface Volume {
  name: string;
  path: string;
  quota_gb: number;
}

interface User {
  username: string;
  password: string;
  is_admin: boolean;
  home_dir: string;
  storage_quota_gb: number;
}

interface SMBShare {
  name: string;
  path: string;
  comment: string;
  read_only: boolean;
  browseable: boolean;
  guest_access: boolean;
}

interface PushTarget {
  id: string;
  name: string;
  ip: string;
  port: number;
}

interface PushStatus {
  active?: {
    target_id: string;
    folder: string;
    total_files: number;
    sent_files: number;
    start_time: string;
  };
  history: PushHistoryItem[];
}

interface PushHistoryItem {
  time: string;
  target: string;
  folder: string;
  sent_files: number;
  total_files: number;
  status: 'success' | 'failed';
}

interface Config {
  server: {
    port: number;
    language: string;
  };
  storage: {
    volumes: Volume[];
  };
  users: User[];
  smb: {
    shares: SMBShare[];
  };
  push: {
    targets: PushTarget[];
  };
  data_dir: string;
  receive_dir: string;
}

interface IPInfo {
  ip: string;
  name?: string;
  adapter?: string;
  type: 'wan' | 'lan' | 'loopback' | 'local';
  network?: string;
  device_id?: string;
}

interface DeviceInfo {
  ip: string;
  port: number;
  online: boolean;
}

interface TranslationDict {
  [key: string]: string;
}

interface Translations {
  [lang: string]: TranslationDict;
}

// ==========================================
// 常量和配置
// ==========================================

const PORT: number = 8091;
const CONFIG_PATH: string = path.join(__dirname, '../../config/config.json');
const LANG_NAMES: { [code: string]: string } = {
  zh_CN: '简体中文', zh_TW: '繁體中文', en_US: 'English', ja_JP: '日本語',
  ko_KR: '한국어', es_ES: 'Español', fr_FR: 'Français', de_DE: 'Deutsch',
  it_IT: 'Italiano', pt_PT: 'Português', ru_RU: 'Русский', ar_SA: 'العربية',
  hi_IN: 'हिन्दी', tr_TR: 'Türkçe', th_TH: 'ภาษาไทย', vi_VN: 'Tiếng Việt',
  id_ID: 'Bahasa Indonesia', nl_NL: 'Nederlands', pl_PL: 'Polski',
  sv_SE: 'Svenska', da_DK: 'Dansk', no_NO: 'Norsk', fi_FI: 'Suomi',
  cs_CZ: 'Čeština', sk_SK: 'Slovenčina', hu_HU: 'Magyar', ro_RO: 'Română',
  bg_BG: 'Български', uk_UA: 'Українська'
};

// ==========================================
// 全局状态
// ==========================================

let config: Config;
let pushStatus: PushStatus = { history: [] };
let receiveDir: string = 'nas_data/received';

// ==========================================
// 28种语言翻译
// ==========================================

const TRANSLATIONS: Translations = {
  zh_CN: {
    app_name: "小思超级NAS", dashboard: "管理控制台", storage: "存储管理",
    users: "用户管理", shares: "共享管理", push: "推送管理",
    settings: "系统设置", volumes: "存储卷", create: "创建", delete: "删除",
    edit: "编辑", save: "保存", cancel: "取消", name: "名称", path: "路径",
    quota: "配额(GB)", used: "已用", available: "可用", username: "用户名",
    password: "密码", admin: "管理员", storage_quota: "存储配额",
    home_directory: "主目录", smb_status: "SMB状态", smb_shares: "SMB共享",
    share_name: "共享名", comment: "备注", read_only: "只读",
    browseable: "可浏览", guest_access: "访客访问", language: "语言",
    running: "运行中", stopped: "已停止", operation_success: "操作成功",
    operation_failed: "操作失败", confirm_delete: "确认删除?", no_data: "暂无数据",
    create_volume: "创建存储卷", create_user: "创建用户", create_share: "创建共享",
    operation: "操作", yes: "是", no: "否", system_info: "系统信息",
    service_status: "服务状态", ip_address: "IP地址", push_targets: "推送目标",
    push_files: "推送文件", local_folder: "本地文件夹", target_device: "目标设备",
    add_target: "添加目标", target_name: "目标名称", target_ip: "目标IP",
    target_port: "目标端口", push_folder: "推送文件夹", select_folder: "选择文件夹",
    push_now: "立即推送", pushing: "推送中...", push_history: "推送历史",
    scan_ip: "扫描IP", local_ips: "本地IP列表", scan: "扫描",
    found_devices: "发现的设备", online: "在线", offline: "离线",
    send: "发送", receive: "接收", push_status: "推送状态",
    success: "成功", failed: "失败", progress: "进度",
    file_count: "文件数量", total_size: "总大小"
  },
  zh_TW: {
    app_name: "小思超级NAS", dashboard: "管理控制台", storage: "儲存管理",
    users: "使用者管理", shares: "共享管理", push: "推送管理",
    settings: "系統設定", volumes: "儲存卷", create: "建立", delete: "刪除",
    edit: "編輯", save: "儲存", cancel: "取消", name: "名稱", path: "路徑",
    quota: "配額(GB)", used: "已用", available: "可用", username: "使用者名稱",
    password: "密碼", admin: "管理員", storage_quota: "儲存配額",
    home_directory: "主目錄", smb_status: "SMB狀態", smb_shares: "SMB共享",
    share_name: "共享名", comment: "備註", read_only: "唯讀",
    browseable: "可瀏覽", guest_access: "訪客存取", language: "語言",
    running: "執行中", stopped: "已停止", operation_success: "操作成功",
    operation_failed: "操作失敗", confirm_delete: "確認刪除?", no_data: "暫無資料",
    create_volume: "建立儲存卷", create_user: "建立使用者", create_share: "建立共享",
    operation: "操作", yes: "是", no: "否", system_info: "系統資訊",
    service_status: "服務狀態", ip_address: "IP位址", push_targets: "推送目標",
    push_files: "推送檔案", local_folder: "本地資料夾", target_device: "目標裝置",
    add_target: "新增目標", target_name: "目標名稱", target_ip: "目標IP",
    target_port: "目標埠", push_folder: "推送資料夾", select_folder: "選擇資料夾",
    push_now: "立即推送", pushing: "推送中...", push_history: "推送歷史",
    scan_ip: "掃描IP", local_ips: "本地IP列表", scan: "掃描",
    found_devices: "發現的裝置", online: "線上", offline: "離線",
    send: "傳送", receive: "接收", push_status: "推送狀態",
    success: "成功", failed: "失敗", progress: "進度",
    file_count: "檔案數量", total_size: "總大小"
  },
  en_US: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Storage",
    users: "Users", shares: "Shares", push: "Push Manager",
    settings: "Settings", volumes: "Volumes", create: "Create", delete: "Delete",
    edit: "Edit", save: "Save", cancel: "Cancel", name: "Name", path: "Path",
    quota: "Quota(GB)", used: "Used", available: "Available", username: "Username",
    password: "Password", admin: "Admin", storage_quota: "Storage Quota",
    home_directory: "Home Directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
    share_name: "Share Name", comment: "Comment", read_only: "Read Only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Language",
    running: "Running", stopped: "Stopped", operation_success: "Success",
    operation_failed: "Failed", confirm_delete: "Confirm delete?", no_data: "No data",
    create_volume: "Create Volume", create_user: "Create User", create_share: "Create Share",
    operation: "Operation", yes: "Yes", no: "No", system_info: "System Info",
    service_status: "Service Status", ip_address: "IP Address", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Local Folder", target_device: "Target Device",
    add_target: "Add Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Success", failed: "Failed", progress: "Progress",
    file_count: "File Count", total_size: "Total Size"
  },
  ja_JP: {
    app_name: "Xiaosi Super NAS", dashboard: "ダッシュボード", storage: "ストレージ",
    users: "ユーザー", shares: "共有", push: "Pushマネージャー",
    settings: "設定", volumes: "ボリューム", create: "作成", delete: "削除",
    edit: "編集", save: "保存", cancel: "キャンセル", name: "名前", path: "パス",
    quota: "クォータ(GB)", used: "使用済み", available: "利用可能", username: "ユーザー名",
    password: "パスワード", admin: "管理者", storage_quota: "ストレージクォータ",
    home_directory: "ホームディレクトリ", smb_status: "SMB状態", smb_shares: "SMB共有",
    share_name: "共有名", comment: "コメント", read_only: "読み取り専用",
    browseable: "ブラウズ可能", guest_access: "ゲストアクセス", language: "言語",
    running: "実行中", stopped: "停止", operation_success: "成功",
    operation_failed: "失敗", confirm_delete: "削除確認?", no_data: "データなし",
    create_volume: "ボリューム作成", create_user: "ユーザー作成", create_share: "共有作成",
    operation: "操作", yes: "はい", no: "いいえ", system_info: "システム情報",
    service_status: "サービス状態", ip_address: "IPアドレス", push_targets: "Pushターゲット",
    push_files: "Pushファイル", local_folder: "ローカルフォルダ", target_device: "ターゲットデバイス",
    add_target: "ターゲット追加", target_name: "ターゲット名", target_ip: "ターゲットIP",
    target_port: "ターゲットポート", push_folder: "Pushフォルダ", select_folder: "フォルダ選択",
    push_now: "今すぐPush", pushing: "Push中...", push_history: "Push履歴",
    scan_ip: "IPスキャン", local_ips: "ローカルIP", scan: "スキャン",
    found_devices: "発見デバイス", online: "オンライン", offline: "オフライン",
    send: "送信", receive: "受信", push_status: "Push状態",
    success: "成功", failed: "失敗", progress: "進捗",
    file_count: "ファイル数", total_size: "合計サイズ"
  },
  ko_KR: {
    app_name: "Xiaosi Super NAS", dashboard: "대시보드", storage: "스토리지",
    users: "사용자", shares: "공유", push: "Push 관리자",
    settings: "설정", volumes: "볼륨", create: "생성", delete: "삭제",
    edit: "편집", save: "저장", cancel: "취소", name: "이름", path: "경로",
    quota: "쿼타(GB)", used: "사용됨", available: "가능", username: "사용자 이름",
    password: "비밀번호", admin: "관리자", storage_quota: "스토리지 쿼타",
    home_directory: "홈 디렉토리", smb_status: "SMB 상태", smb_shares: "SMB 공유",
    share_name: "공유 이름", comment: "주석", read_only: "읽기 전용",
    browseable: "검색 가능", guest_access: "게스트 접근", language: "언어",
    running: "실행 중", stopped: "중지됨", operation_success: "성공",
    operation_failed: "실패", confirm_delete: "삭제 확인?", no_data: "데이터 없음",
    create_volume: "볼륨 생성", create_user: "사용자 생성", create_share: "공유 생성",
    operation: "작업", yes: "예", no: "아니오", system_info: "시스템 정보",
    service_status: "서비스 상태", ip_address: "IP 주소", push_targets: "Push 타겟",
    push_files: "Push 파일", local_folder: "로컬 폴더", target_device: "타겟 디바이스",
    add_target: "타겟 추가", target_name: "타겟 이름", target_ip: "타겟 IP",
    target_port: "타겟 포트", push_folder: "Push 폴더", select_folder: "폴더 선택",
    push_now: "Push 지금", pushing: "Push 중...", push_history: "Push 역사",
    scan_ip: "IP 스캔", local_ips: "로컬 IPs", scan: "스캔",
    found_devices: "발견 디바이스", online: "온라인", offline: "오프라인",
    send: "보내기", receive: "받기", push_status: "Push 상태",
    success: "성공", failed: "실패", progress: "진행",
    file_count: "파일 수", total_size: "전체 크기"
  },
  es_ES: {
    app_name: "Xiaosi Super NAS", dashboard: "Panel", storage: "Almacenamiento",
    users: "Usuarios", shares: "Compartidos", push: "Manager Push",
    settings: "Configuración", volumes: "Volúmenes", create: "Crear", delete: "Eliminar",
    edit: "Editar", save: "Guardar", cancel: "Cancelar", name: "Nombre", path: "Ruta",
    quota: "Cuota(GB)", used: "Usado", available: "Disponible", username: "Usuario",
    password: "Contraseña", admin: "Admin", storage_quota: "Cuota almacenamiento",
    home_directory: "Directorio principal", smb_status: "Estado SMB", smb_shares: "Compartidos SMB",
    share_name: "Nombre compartido", comment: "Comentario", read_only: "Solo lectura",
    browseable: "Navegable", guest_access: "Acceso invitado", language: "Idioma",
    running: "Ejecutando", stopped: "Detenido", operation_success: "Éxito",
    operation_failed: "Error", confirm_delete: "Confirmar eliminación?", no_data: "Sin datos",
    create_volume: "Crear volumen", create_user: "Crear usuario", create_share: "Crear compartido",
    operation: "Operación", yes: "Sí", no: "No", system_info: "Info sistema",
    service_status: "Estado servicio", ip_address: "Dirección IP", push_targets: "Destinos Push",
    push_files: "Archivos Push", local_folder: "Carpeta local", target_device: "Dispositivo destino",
    add_target: "Agregar destino", target_name: "Nombre destino", target_ip: "IP destino",
    target_port: "Puerto destino", push_folder: "Carpeta Push", select_folder: "Seleccionar carpeta",
    push_now: "Push ahora", pushing: "Pushing...", push_history: "Historia Push",
    scan_ip: "Escanear IP", local_ips: "IPs locales", scan: "Escanear",
    found_devices: "Dispositivos encontrados", online: "Online", offline: "Offline",
    send: "Enviar", receive: "Recibir", push_status: "Estado Push",
    success: "Éxito", failed: "Error", progress: "Progreso",
    file_count: "Número archivos", total_size: "Tamaño total"
  },
  fr_FR: {
    app_name: "Xiaosi Super NAS", dashboard: "Tableau de bord", storage: "Stockage",
    users: "Utilisateurs", shares: "Partages", push: "Manager Push",
    settings: "Paramètres", volumes: "Volumes", create: "Créer", delete: "Supprimer",
    edit: "Modifier", save: "Sauvegarder", cancel: "Annuler", name: "Nom", path: "Chemin",
    quota: "Quota(GB)", used: "Utilisé", available: "Disponible", username: "Nom d'utilisateur",
    password: "Mot de passe", admin: "Admin", storage_quota: "Quota stockage",
    home_directory: "Répertoire principal", smb_status: "Statut SMB", smb_shares: "Partages SMB",
    share_name: "Nom du partage", comment: "Commentaire", read_only: "Lecture seule",
    browseable: "Navigable", guest_access: "Accès invité", language: "Langue",
    running: "En cours", stopped: "Arrêté", operation_success: "Succès",
    operation_failed: "Échec", confirm_delete: "Confirmer suppression?", no_data: "Pas de données",
    create_volume: "Créer volume", create_user: "Créer utilisateur", create_share: "Créer partage",
    operation: "Opération", yes: "Oui", no: "Non", system_info: "Info système",
    service_status: "Statut service", ip_address: "Adresse IP", push_targets: "Cibles Push",
    push_files: "Fichiers Push", local_folder: "Dossier local", target_device: "Dispositif cible",
    add_target: "Ajouter cible", target_name: "Nom cible", target_ip: "IP cible",
    target_port: "Port cible", push_folder: "Dossier Push", select_folder: "Sélectionner dossier",
    push_now: "Push maintenant", pushing: "Pushing...", push_history: "Historique Push",
    scan_ip: "Scanner IP", local_ips: "IPs locales", scan: "Scanner",
    found_devices: "Dispositifs trouvés", online: "Online", offline: "Offline",
    send: "Envoyer", receive: "Recevoir", push_status: "Statut Push",
    success: "Succès", failed: "Échec", progress: "Progression",
    file_count: "Nombre fichiers", total_size: "Taille totale"
  },
  de_DE: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Speicher",
    users: "Benutzer", shares: "Freigaben", push: "Push Manager",
    settings: "Einstellungen", volumes: "Volumes", create: "Erstellen", delete: "Löschen",
    edit: "Bearbeiten", save: "Speichern", cancel: "Abbrechen", name: "Name", path: "Pfad",
    quota: "Quota(GB)", used: "Verwendet", available: "Verfügbar", username: "Benutzername",
    password: "Passwort", admin: "Admin", storage_quota: "Speicher-Quota",
    home_directory: "Home-Verzeichnis", smb_status: "SMB-Status", smb_shares: "SMB-Freigaben",
    share_name: "Freigabe-Name", comment: "Kommentar", read_only: "Lesen-only",
    browseable: "Durchsuchbar", guest_access: "Gast-Zugriff", language: "Sprache",
    running: "Läuft", stopped: "Gestoppt", operation_success: "Erfolg",
    operation_failed: "Fehler", confirm_delete: "Löschen bestätigen?", no_data: "Keine Daten",
    create_volume: "Volume erstellen", create_user: "Benutzer erstellen", create_share: "Freigabe erstellen",
    operation: "Operation", yes: "Ja", no: "Nein", system_info: "System-Info",
    service_status: "Service-Status", ip_address: "IP-Adresse", push_targets: "Push-Ziele",
    push_files: "Push-Dateien", local_folder: "Lokaler Ordner", target_device: "Zielgerät",
    add_target: "Ziel hinzufügen", target_name: "Ziel-Name", target_ip: "Ziel-IP",
    target_port: "Ziel-Port", push_folder: "Push-Ordner", select_folder: "Ordner auswählen",
    push_now: "Jetzt Push", pushing: "Pushing...", push_history: "Push-Historie",
    scan_ip: "IP-Scan", local_ips: "Lokale IPs", scan: "Scannen",
    found_devices: "Gefundene Geräte", online: "Online", offline: "Offline",
    send: "Senden", receive: "Empfangen", push_status: "Push-Status",
    success: "Erfolg", failed: "Fehler", progress: "Fortschritt",
    file_count: "Dateianzahl", total_size: "Gesamtgröße"
  },
  it_IT: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Archiviazione",
    users: "Utenti", shares: "Condivisioni", push: "Push Manager",
    settings: "Impostazioni", volumes: "Volumes", create: "Creare", delete: "Eliminare",
    edit: "Modificare", save: "Salvare", cancel: "Annullare", name: "Nome", path: "Percorso",
    quota: "Quota(GB)", used: "Usato", available: "Disponibile", username: "Nome utente",
    password: "Password", admin: "Admin", storage_quota: "Quota archiviazione",
    home_directory: "Directory home", smb_status: "Stato SMB", smb_shares: "Condivisioni SMB",
    share_name: "Nome condivisione", comment: "Commento", read_only: "Sola lettura",
    browseable: "Navigabile", guest_access: "Accesso ospiti", language: "Linguaggio",
    running: "In esecuzione", stopped: "Fermato", operation_success: "Successo",
    operation_failed: "Fallito", confirm_delete: "Conferma eliminazione?", no_data: "Nessun dato",
    create_volume: "Creare Volume", create_user: "Creare utente", create_share: "Creare condivisione",
    operation: "Operazione", yes: "Sì", no: "No", system_info: "Info sistema",
    service_status: "Stato servizio", ip_address: "Indirizzo IP", push_targets: "Obiettivi Push",
    push_files: "File Push", local_folder: "Cartella locale", target_device: "Dispositivo target",
    add_target: "Aggiungere obiettivo", target_name: "Nome obiettivo", target_ip: "IP obiettivo",
    target_port: "Porta obiettivo", push_folder: "Cartella Push", select_folder: "Selezionare cartella",
    push_now: "Push ora", pushing: "Pushing...", push_history: "Storia Push",
    scan_ip: "Scansionare IP", local_ips: "IPs locali", scan: "Scansionare",
    found_devices: "Dispositivi trovati", online: "Online", offline: "Offline",
    send: "Inviare", receive: "Ricevere", push_status: "Stato Push",
    success: "Successo", failed: "Fallito", progress: "Progresso",
    file_count: "Numero file", total_size: "Dimensione totale"
  },
  pt_PT: {
    app_name: "Xiaosi Super NAS", dashboard: "Painel", storage: "Armazenamento",
    users: "Usuários", shares: "Compartilhamentos", push: "Gerenciador Push",
    settings: "Configurações", volumes: "Volumes", create: "Criar", delete: "Excluir",
    edit: "Editar", save: "Salvar", cancel: "Cancelar", name: "Nome", path: "Caminho",
    quota: "Quota(GB)", used: "Usado", available: "Disponível", username: "Nome de usuário",
    password: "Senha", admin: "Admin", storage_quota: "Quota armazenamento",
    home_directory: "Diretório home", smb_status: "Status SMB", smb_shares: "Compartilhamentos SMB",
    share_name: "Nome compartilhamento", comment: "Comentário", read_only: "Somente leitura",
    browseable: "Navegável", guest_access: "Acesso guest", language: "Idioma",
    running: "Executando", stopped: "Parado", operation_success: "Sucesso",
    operation_failed: "Falhou", confirm_delete: "Confirmar exclusão?", no_data: "Sem dados",
    create_volume: "Criar Volume", create_user: "Criar usuário", create_share: "Criar compartilhamento",
    operation: "Operação", yes: "Sim", no: "Não", system_info: "Info sistema",
    service_status: "Status serviço", ip_address: "Endereço IP", push_targets: "Destinos Push",
    push_files: "Arquivos Push", local_folder: "Pasta local", target_device: "Dispositivo destino",
    add_target: "Adicionar destino", target_name: "Nome destino", target_ip: "IP destino",
    target_port: "Porta destino", push_folder: "Pasta Push", select_folder: "Selecionar pasta",
    push_now: "Push agora", pushing: "Pushing...", push_history: "História Push",
    scan_ip: "Escanear IP", local_ips: "IPs locais", scan: "Escanear",
    found_devices: "Dispositivos encontrados", online: "Online", offline: "Offline",
    send: "Enviar", receive: "Receber", push_status: "Status Push",
    success: "Sucesso", failed: "Erro", progress: "Progresso",
    file_count: "Número arquivos", total_size: "Tamanho total"
  },
  ru_RU: {
    app_name: "Xiaosi Super NAS", dashboard: "Панель", storage: "Хранилище",
    users: "Пользователи", shares: "Общие ресурсы", push: "Менеджер Push",
    settings: "Настройки", volumes: "Тома", create: "Создать", delete: "Удалить",
    edit: "Редактировать", save: "Сохранить", cancel: "Отмена", name: "Имя", path: "Путь",
    quota: "Квота(GB)", used: "Использовано", available: "Доступно", username: "Имя пользователя",
    password: "Пароль", admin: "Админ", storage_quota: "Квота хранилища",
    home_directory: "Домашний каталог", smb_status: "Статус SMB", smb_shares: "Ресурсы SMB",
    share_name: "Имя ресурса", comment: "Комментарий", read_only: "Только чтение",
    browseable: "Обзор", guest_access: "Гостевой доступ", language: "Язык",
    running: "Запущено", stopped: "Остановлено", operation_success: "Успех",
    operation_failed: "Ошибка", confirm_delete: "Подтвердить удаление?", no_data: "Нет данных",
    create_volume: "Создать том", create_user: "Создать пользователя", create_share: "Создать ресурс",
    operation: "Действие", yes: "Да", no: "Нет", system_info: "Системная информация",
    service_status: "Статус сервиса", ip_address: "IP адрес", push_targets: "Push цели",
    push_files: "Push файлы", local_folder: "Локальная папка", target_device: "Целевое устройство",
    add_target: "Добавить цель", target_name: "Имя цели", target_ip: "IP цели",
    target_port: "Порт цели", push_folder: "Push папка", select_folder: "Выбрать папку",
    push_now: "Push сейчас", pushing: "Pushing...", push_history: "История Push",
    scan_ip: "Сканировать IP", local_ips: "Локальные IP", scan: "Сканировать",
    found_devices: "Найденные устройства", online: "Онлайн", offline: "Оффлайн",
    send: "Отправить", receive: "Получить", push_status: "Статус Push",
    success: "Успех", failed: "Ошибка", progress: "Прогресс",
    file_count: "Количество файлов", total_size: "Общий размер"
  },
  ar_SA: {
    app_name: "Xiaosi Super NAS", dashboard: "لوحة التحكم", storage: "التخزين",
    users: "المستخدمين", shares: "المشاركات", push: "مدير Push",
    settings: "الإعدادات", volumes: "Volumes", create: "إنشاء", delete: "حذف",
    edit: "تعديل", save: "حفظ", cancel: "إلغاء", name: "الاسم", path: "المسار",
    quota: "الحصة", used: "مستخدم", available: "متاح", username: "اسم المستخدم",
    password: "كلمة المرور", admin: "مدير", storage_quota: "حصة التخزين",
    home_directory: "الدليل الرئيسي", smb_status: "حالة SMB", smb_shares: "مشاركات SMB",
    share_name: "اسم المشاركة", comment: "تعليق", read_only: "قراءة فقط",
    browseable: "يمكن التصفح", guest_access: "دخول الضيف", language: "اللغة",
    running: "جاري", stopped: "متوقف", operation_success: "نجاح",
    operation_failed: "فشل", confirm_delete: "تأكيد الحذف?", no_data: "لا بيانات",
    create_volume: "إنشاء حجم", create_user: "إنشاء مستخدم", create_share: "إنشاء مشاركة",
    operation: "عملية", yes: "نعم", no: "لا", system_info: "معلومات النظام",
    service_status: "حالة الخدمة", ip_address: "عنوان IP", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "المجلد المحلي", target_device: "الجهاز المستهدف",
    add_target: "إضافة هدف", target_name: "اسم الهدف", target_ip: "IP الهدف",
    target_port: "بوابة الهدف", push_folder: "Push Folder", select_folder: "اختر مجلد",
    push_now: "Push الآن", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Success", failed: "Failed", progress: "Progress",
    file_count: "File Count", total_size: "Total Size"
  },
  hi_IN: {
    app_name: "Xiaosi Super NAS", dashboard: "डैशबोर्ड", storage: "स्टोरेज",
    users: "उपयोगकर्ता", shares: "शेयर", push: "Push मैनेजर",
    settings: "सेटिंग्स", volumes: "Volumes", create: "बनाएं", delete: "हटाएं",
    edit: "संपादित", save: "सहेजें", cancel: "कैंसल", name: "नाम", path: "पथ",
    quota: "क्वोटा", used: "प्रयुक्त", available: "उपलब्ध", username: "उपयोगकर्ता नाम",
    password: "पासवर्ड", admin: "Admin", storage_quota: "स्टोरेज क्वोटा",
    home_directory: "होम डायरेक्टरी", smb_status: "SMB स्थिति", smb_shares: "SMB शेयर",
    share_name: "शेयर नाम", comment: "टिप्पणी", read_only: "पढ़ने के लिए",
    browseable: "ब्रॉउज़ करने योग्य", guest_access: "गuest एक्सेस", language: "भाषा",
    running: "चल रहा", stopped: "रुका हुआ", operation_success: "सफल",
    operation_failed: "विफल", confirm_delete: "हटाने की पुष्टि?", no_data: "कोई डेटा",
    create_volume: "Volume बनाएं", create_user: "उपयोगकर्ता बनाएं", create_share: "शेयर बनाएं",
    operation: "कार्य", yes: "हाँ", no: "नहीं", system_info: "सिस्टम जानकारी",
    service_status: "सेवा स्थिति", ip_address: "IP पता", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "लोकल फोल्डर", target_device: "Target Device",
    add_target: "Target जोड़ें", target_name: "Target नाम", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Success", failed: "Failed", progress: "Progress",
    file_count: "File Count", total_size: "Total Size"
  },
  tr_TR: {
    app_name: "Xiaosi Super NAS", dashboard: "Kontrol Paneli", storage: "Depolama",
    users: "Kullanıcılar", shares: "Paylaşımlar", push: "Push Yönetici",
    settings: "Ayarlar", volumes: "Volumes", create: "Oluştur", delete: "Sil",
    edit: "Düzenle", save: "Kaydet", cancel: "İptal", name: "İsim", path: "Yol",
    quota: "Kota(GB)", used: "Kullanılan", available: "Mevcut", username: "Kullanıcı adı",
    password: "Şifre", admin: "Admin", storage_quota: "Depolama kotası",
    home_directory: "Ana dizin", smb_status: "SMB Durumu", smb_shares: "SMB Paylaşımları",
    share_name: "Paylaşım adı", comment: "Yorum", read_only: "Salt okunur",
    browseable: "Taranabilir", guest_access: "Misafir erişimi", language: "Dil",
    running: "Çalışıyor", stopped: "Durduruldu", operation_success: "Başarılı",
    operation_failed: "Başarısız", confirm_delete: "Silmeyi onayla?", no_data: "Veri yok",
    create_volume: "Volume oluştur", create_user: "Kullanıcı oluştur", create_share: "Paylaşım oluştur",
    operation: "İşlem", yes: "Evet", no: "Hayır", system_info: "Sistem bilgisi",
    service_status: "Servis durumu", ip_address: "IP adresi", push_targets: "Push hedefleri",
    push_files: "Push dosyaları", local_folder: "Yerel klasör", target_device: "Hedef cihaz",
    add_target: "Hedef ekle", target_name: "Hedef adı", target_ip: "Hedef IP",
    target_port: "Hedef port", push_folder: "Push klasörü", select_folder: "Klasör seç",
    push_now: "Şimdi push", pushing: "Pushing...", push_history: "Push geçmişi",
    scan_ip: "IP tara", local_ips: "Yerel IPs", scan: "Tara",
    found_devices: "Bulunan cihazlar", online: "Online", offline: "Offline",
    send: "Gönder", receive: "Al", push_status: "Push durumu",
    success: "Başarılı", failed: "Başarısız", progress: "İlerleme",
    file_count: "Dosya sayısı", total_size: "Toplam boyut"
  },
  th_TH: {
    app_name: "Xiaosi Super NAS", dashboard: "แดชบอร์ด", storage: "จัดเก็บ",
    users: "ผู้ใช้", shares: "แชร์", push: "Push Manager",
    settings: "การตั้งค่า", volumes: "Volumes", create: "สร้าง", delete: "ลบ",
    edit: "แก้ไข", save: "บันทึก", cancel: "ยกเลิก", name: "ชื่อ", path: "เส้นทาง",
    quota: "Quota(GB)", used: "ใช้แล้ว", available: "พร้อมใช้", username: "ชื่อผู้ใช้",
    password: "รหัสผ่าน", admin: "Admin", storage_quota: "Quota จัดเก็บ",
    home_directory: "โฮมไดเรกทอรี", smb_status: "สถานะ SMB", smb_shares: "SMB Shares",
    share_name: "ชื่อแชร์", comment: "ความคิดเห็น", read_only: "อ่านอย่างเดียว",
    browseable: "เรียกดูได้", guest_access: "Guest Access", language: "ภาษา",
    running: "กำลังทำงาน", stopped: "หยุด", operation_success: "สำเร็จ",
    operation_failed: "ล้มเหลว", confirm_delete: "ยืนยันการลบ?", no_data: "ไม่มีข้อมูล",
    create_volume: "สร้าง Volume", create_user: "สร้างผู้ใช้", create_share: "สร้างแชร์",
    operation: "การดำเนินการ", yes: "ใช่", no: "ไม่", system_info: "ข้อมูลระบบ",
    service_status: "สถานะบริการ", ip_address: "IP Address", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "โฟลเดอร์ท้องถิ่น", target_device: "Target Device",
    add_target: "เพิ่ม Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Success", failed: "Failed", progress: "Progress",
    file_count: "File Count", total_size: "Total Size"
  },
  vi_VN: {
    app_name: "Xiaosi Super NAS", dashboard: "Bảng điều khiển", storage: "Lưu trữ",
    users: "Người dùng", shares: "Chia sẻ", push: "Push Manager",
    settings: "Cài đặt", volumes: "Volumes", create: "Tạo", delete: "Xóa",
    edit: "Sửa", save: "Lưu", cancel: "Hủy", name: "Tên", path: "Đường dẫn",
    quota: "Quota(GB)", used: "Đã dùng", available: "Khả dụng", username: "Tên người dùng",
    password: "Mật khẩu", admin: "Admin", storage_quota: "Quota lưu trữ",
    home_directory: "Thư mục home", smb_status: "Trạng thái SMB", smb_shares: "SMB Shares",
    share_name: "Tên chia sẻ", comment: "Ghi chú", read_only: "Chỉ đọc",
    browseable: "Có thể duyệt", guest_access: "Guest Access", language: "Ngôn ngữ",
    running: "Chạy", stopped: "Dừng", operation_success: "Thành công",
    operation_failed: "Thất bại", confirm_delete: "Xác nhận xóa?", no_data: "Không có dữ liệu",
    create_volume: "Tạo Volume", create_user: "Tạo người dùng", create_share: "Tạo chia sẻ",
    operation: "Thao tác", yes: "Có", no: "Không", system_info: "Thông tin hệ thống",
    service_status: "Trạng thái dịch vụ", ip_address: "Địa chỉ IP", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Thư mục cục bộ", target_device: "Target Device",
    add_target: "Thêm Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "IP cục bộ", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Success", failed: "Failed", progress: "Progress",
    file_count: "File Count", total_size: "Total Size"
  },
  id_ID: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Storage",
    users: "Pengguna", shares: "Share", push: "Push Manager",
    settings: "Pengaturan", volumes: "Volumes", create: "Buat", delete: "Hapus",
    edit: "Edit", save: "Simpan", cancel: "Batal", name: "Nama", path: "Path",
    quota: "Quota(GB)", used: "Digunakan", available: "Tersedia", username: "Nama pengguna",
    password: "Password", admin: "Admin", storage_quota: "Quota storage",
    home_directory: "Direktori home", smb_status: "Status SMB", smb_shares: "SMB Shares",
    share_name: "Nama share", comment: "Komentar", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Bahasa",
    running: "Berjalan", stopped: "Berhenti", operation_success: "Sukses",
    operation_failed: "Gagal", confirm_delete: "Konfirmasi hapus?", no_data: "Tidak ada data",
    create_volume: "Buat Volume", create_user: "Buat pengguna", create_share: "Buat share",
    operation: "Operasi", yes: "Ya", no: "Tidak", system_info: "Info sistem",
    service_status: "Status layanan", ip_address: "Alamat IP", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Folder lokal", target_device: "Target Device",
    add_target: "Tambah Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "IP lokal", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Sukses", failed: "Gagal", progress: "Progress",
    file_count: "Jumlah file", total_size: "Total ukuran"
  },
  nl_NL: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Opslag",
    users: "Gebruikers", shares: "Shares", push: "Push Manager",
    settings: "Instellingen", volumes: "Volumes", create: "Creëer", delete: "Verwijder",
    edit: "Bewerk", save: "Opslaan", cancel: "Annuleren", name: "Naam", path: "Pad",
    quota: "Quota(GB)", used: "Gebruikt", available: "Beschikbaar", username: "Gebruikersnaam",
    password: "Wachtwoord", admin: "Admin", storage_quota: "Opslag quota",
    home_directory: "Home directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
    share_name: "Share naam", comment: "Commentaar", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Taal",
    running: "Running", stopped: "Gestopt", operation_success: "Succes",
    operation_failed: "Mislukt", confirm_delete: "Bevestig verwijdering?", no_data: "Geen data",
    create_volume: "Creëer Volume", create_user: "Creëer gebruiker", create_share: "Creëer share",
    operation: "Actie", yes: "Ja", no: "Nee", system_info: "Systeem info",
    service_status: "Service status", ip_address: "IP adres", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Lokale folder", target_device: "Target Device",
    add_target: "Target toevoegen", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Lokale IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Succes", failed: "Mislukt", progress: "Progress",
    file_count: "Bestandsaantal", total_size: "Totale grootte"
  },
  pl_PL: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Przechowywanie",
    users: "Użytkownicy", shares: "Shares", push: "Push Manager",
    settings: "Ustawienia", volumes: "Volumes", create: "Utwórz", delete: "Usuń",
    edit: "Edytuj", save: "Zapisz", cancel: "Anuluj", name: "Nazwa", path: "Ścieżka",
    quota: "Quota(GB)", used: "Używane", available: "Dostępne", username: "Nazwa użytkownika",
    password: "Hasło", admin: "Admin", storage_quota: "Quota przechowywania",
    home_directory: "Katalog domowy", smb_status: "Status SMB", smb_shares: "SMB Shares",
    share_name: "Nazwa share", comment: "Komentarz", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Język",
    running: "Running", stopped: "Zatrzymano", operation_success: "Sukces",
    operation_failed: "Niepowodzenie", confirm_delete: "Potwierdź usunięcie?", no_data: "Brak danych",
    create_volume: "Utwórz Volume", create_user: "Utwórz użytkownika", create_share: "Utwórz share",
    operation: "Operacja", yes: "Tak", no: "Nie", system_info: "Info system",
    service_status: "Status serwisu", ip_address: "Adres IP", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Lokalny folder", target_device: "Target Device",
    add_target: "Dodaj Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Sukces", failed: "Niepowodzenie", progress: "Progress",
    file_count: "Liczba plików", total_size: "Całkowity rozmiar"
  },
  sv_SE: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Lagring",
    users: "Användare", shares: "Shares", push: "Push Manager",
    settings: "Inställningar", volumes: "Volumes", create: "Skapa", delete: "Ta bort",
    edit: "Redigera", save: "Spara", cancel: "Avbryt", name: "Namn", path: "Sökväg",
    quota: "Quota(GB)", used: "Använd", available: "Tillgänglig", username: "Användarnamn",
    password: "Lösenord", admin: "Admin", storage_quota: "Lagrings quota",
    home_directory: "Hem directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
    share_name: "Share namn", comment: "Kommentar", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Språk",
    running: "Running", stopped: "Stoppad", operation_success: "Succes",
    operation_failed: "Misslyckad", confirm_delete: "Bekräfta borttagning?", no_data: "Ingen data",
    create_volume: "Skapa Volume", create_user: "Skapa användare", create_share: "Skapa share",
    operation: "Operation", yes: "Ja", no: "Nej", system_info: "System info",
    service_status: "Service status", ip_address: "IP adress", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Lokal folder", target_device: "Target Device",
    add_target: "Lägg till Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Succes", failed: "Misslyckad", progress: "Progress",
    file_count: "Fil antal", total_size: "Total storlek"
  },
  da_DK: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Lager",
    users: "Brugere", shares: "Shares", push: "Push Manager",
    settings: "Indstillinger", volumes: "Volumes", create: "Opret", delete: "Slet",
    edit: "Rediger", save: "Gem", cancel: "Annuller", name: "Navn", path: "Sti",
    quota: "Quota(GB)", used: "Brugt", available: "Tilgængelig", username: "Brugernavn",
    password: "Kodeord", admin: "Admin", storage_quota: "Lager quota",
    home_directory: "Hjem directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
    share_name: "Share navn", comment: "Kommentar", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Sprog",
    running: "Running", stopped: "Stoppet", operation_success: "Succes",
    operation_failed: "Fejl", confirm_delete: "Bekræft sletning?", no_data: "Ingen data",
    create_volume: "Opret Volume", create_user: "Opret bruger", create_share: "Opret share",
    operation: "Operation", yes: "Ja", no: "Nej", system_info: "System info",
    service_status: "Service status", ip_address: "IP adresse", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Lokal folder", target_device: "Target Device",
    add_target: "Tilføj Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Succes", failed: "Fejl", progress: "Progress",
    file_count: "Fil antal", total_size: "Total størrelse"
  },
  no_NO: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Lagring",
    users: "Brukere", shares: "Shares", push: "Push Manager",
    settings: "Innstillinger", volumes: "Volumes", create: "Opprett", delete: "Slett",
    edit: "Rediger", save: "Lagre", cancel: "Avbryt", name: "Navn", path: "Sti",
    quota: "Quota(GB)", used: "Brukt", available: "Tilgjengelig", username: "Brukernavn",
    password: "Passord", admin: "Admin", storage_quota: "Lagrings quota",
    home_directory: "Hjem directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
    share_name: "Share navn", comment: "Kommentar", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Språk",
    running: "Running", stopped: "Stoppet", operation_success: "Suksess",
    operation_failed: "Feilet", confirm_delete: "Bekreft sletting?", no_data: "Ingen data",
    create_volume: "Opprett Volume", create_user: "Opprett bruker", create_share: "Opprett share",
    operation: "Operasjon", yes: "Ja", no: "Nei", system_info: "System info",
    service_status: "Service status", ip_address: "IP adresse", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Lokal folder", target_device: "Target Device",
    add_target: "Legg til Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Suksess", failed: "Feilet", progress: "Progress",
    file_count: "Fil antall", total_size: "Total størrelse"
  },
  fi_FI: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Tallennus",
    users: "Käyttäjät", shares: "Shares", push: "Push Manager",
    settings: "Asetukset", volumes: "Volumes", create: "Luo", delete: "Poista",
    edit: "Muokkaa", save: "Tallenna", cancel: "Peruuta", name: "Nimi", path: "Polku",
    quota: "Quota(GB)", used: "Käytetty", available: "Saatavilla", username: "Käyttäjänimi",
    password: "Salasana", admin: "Admin", storage_quota: "Tallennus quota",
    home_directory: "Koti directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
    share_name: "Share nimi", comment: "Kommentti", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Kieli",
    running: "Running", stopped: "Pysäytetty", operation_success: "Onnistui",
    operation_failed: "Epäonnistui", confirm_delete: "Vahvista poisto?", no_data: "Ei dataa",
    create_volume: "Luo Volume", create_user: "Luo käyttäjä", create_share: "Luo share",
    operation: "Operaatio", yes: "Kyllä", no: "Ei", system_info: "System info",
    service_status: "Service status", ip_address: "IP osoite", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Paikallinen folder", target_device: "Target Device",
    add_target: "Lisää Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Onnistui", failed: "Epäonnistui", progress: "Progress",
    file_count: "Tiedosto määrä", total_size: "Yhteensä koko"
  },
  cs_CZ: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Uložení",
    users: "Uživatelé", shares: "Shares", push: "Push Manager",
    settings: "Nastavení", volumes: "Volumes", create: "Vytvořit", delete: "Smazat",
    edit: "Upravit", save: "Uložit", cancel: "Zrušit", name: "Název", path: "Cesta",
    quota: "Quota(GB)", used: "Použito", available: "Dostupné", username: "Uživatelské jméno",
    password: "Heslo", admin: "Admin", storage_quota: "Uložení quota",
    home_directory: "Domovský directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
    share_name: "Share název", comment: "Komentář", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Jazyk",
    running: "Running", stopped: "Zastaveno", operation_success: "Úspěch",
    operation_failed: "Neúspěch", confirm_delete: "Potvrdit smazání?", no_data: "Žádná data",
    create_volume: "Vytvořit Volume", create_user: "Vytvořit uživatele", create_share: "Vytvořit share",
    operation: "Operace", yes: "Ano", no: "Ne", system_info: "System info",
    service_status: "Service status", ip_address: "IP adresa", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Místní folder", target_device: "Target Device",
    add_target: "Přidat Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Úspěch", failed: "Neúspěch", progress: "Progress",
    file_count: "Počet souborů", total_size: "Celková velikost"
  },
  sk_SK: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Ukladanie",
    users: "Užívatelia", shares: "Shares", push: "Push Manager",
    settings: "Nastavenia", volumes: "Volumes", create: "Vytvoriť", delete: "Zmazať",
    edit: "Upraviť", save: "Uložiť", cancel: "Zrušiť", name: "Názov", path: "Cesta",
    quota: "Quota(GB)", used: "Použité", available: "Dostupné", username: "Užívateľské meno",
    password: "Heslo", admin: "Admin", storage_quota: "Ukladanie quota",
    home_directory: "Domovský directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
    share_name: "Share názov", comment: "Komentár", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Jazyk",
    running: "Running", stopped: "Zastavené", operation_success: "Úspech",
    operation_failed: "Neúspech", confirm_delete: "Potvrdiť zmazanie?", no_data: "Žiadne dáta",
    create_volume: "Vytvoriť Volume", create_user: "Vytvoriť užívateľa", create_share: "Vytvoriť share",
    operation: "Operácia", yes: "Áno", no: "Ne", system_info: "System info",
    service_status: "Service status", ip_address: "IP adresa", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Miestny folder", target_device: "Target Device",
    add_target: "Pridať Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Úspech", failed: "Neúspech", progress: "Progress",
    file_count: "Počet súborov", total_size: "Celková veľkosť"
  },
  hu_HU: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Tárolás",
    users: "Felhasználók", shares: "Shares", push: "Push Manager",
    settings: "Beállítások", volumes: "Volumes", create: "Létrehoz", delete: "Töröl",
    edit: "Szerkeszt", save: "Ment", cancel: "Mégse", name: "Név", path: "Útvonal",
    quota: "Quota(GB)", used: "Használt", available: "Elérhető", username: "Felhasználónév",
    password: "Jelszó", admin: "Admin", storage_quota: "Tárolási quota",
    home_directory: "Home directory", smb_status: "SMB Státusz", smb_shares: "SMB Shares",
    share_name: "Share név", comment: "Komment", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Nyelv",
    running: "Running", stopped: "Leállítva", operation_success: "Siker",
    operation_failed: "Hiba", confirm_delete: "Törlés megerősítése?", no_data: "Nincs adat",
    create_volume: "Volume létrehoz", create_user: "Felhasználó létrehoz", create_share: "Share létrehoz",
    operation: "Művelet", yes: "Igen", no: "Nem", system_info: "System info",
    service_status: "Service státusz", ip_address: "IP cím", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Helyi folder", target_device: "Target Device",
    add_target: "Target hozzáad", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Siker", failed: "Hiba", progress: "Progress",
    file_count: "Fájl szám", total_size: "Teljes méret"
  },
  ro_RO: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Stocare",
    users: "Utilizatori", shares: "Shares", push: "Push Manager",
    settings: "Setări", volumes: "Volumes", create: "Creează", delete: "Șterge",
    edit: "Editează", save: "Salvează", cancel: "Anulează", name: "Nume", path: "Cale",
    quota: "Quota(GB)", used: "Folosit", available: "Disponibil", username: "Nume utilizator",
    password: "Parolă", admin: "Admin", storage_quota: "Quota stocare",
    home_directory: "Home directory", smb_status: "Status SMB", smb_shares: "SMB Shares",
    share_name: "Share nume", comment: "Comentariu", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Limbă",
    running: "Running", stopped: "Oprit", operation_success: "Succes",
    operation_failed: "Eșec", confirm_delete: "Confirmă ștergere?", no_data: "Nu există date",
    create_volume: "Creează Volume", create_user: "Creează utilizator", create_share: "Creează share",
    operation: "Operațiune", yes: "Da", no: "Nu", system_info: "System info",
    service_status: "Status serviciu", ip_address: "Adresă IP", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Folder local", target_device: "Target Device",
    add_target: "Adaugă Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Succes", failed: "Eșec", progress: "Progress",
    file_count: "Număr fișiere", total_size: "Mărime totală"
  },
  bg_BG: {
    app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Съхранение",
    users: "Потребители", shares: "Shares", push: "Push Manager",
    settings: "Настройки", volumes: "Volumes", create: "Създай", delete: "Изтрий",
    edit: "Редактирай", save: "Запази", cancel: "Отказ", name: "Име", path: "Път",
    quota: "Quota(GB)", used: "Използвано", available: "Достъпно", username: "Потребител",
    password: "Парола", admin: "Admin", storage_quota: "Quota съхранение",
    home_directory: "Home directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
    share_name: "Share име", comment: "Коментар", read_only: "Read only",
    browseable: "Browseable", guest_access: "Guest Access", language: "Език",
    running: "Running", stopped: "Спрян", operation_success: "Успех",
    operation_failed: "Неуспех", confirm_delete: "Потвърди изтриване?", no_data: "Няма данни",
    create_volume: "Създай Volume", create_user: "Създай потребител", create_share: "Създай share",
    operation: "Операция", yes: "Да", no: "Не", system_info: "System info",
    service_status: "Service статус", ip_address: "IP адрес", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Местна folder", target_device: "Target Device",
    add_target: "Добави Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Успех", failed: "Неуспех", progress: "Progress",
    file_count: "Брой файлове", total_size: "Общ размер"
  },
  uk_UA: {
    app_name: "Xiaosi Super NAS", dashboard: "Панель", storage: "Сховище",
    users: "Користувачі", shares: "Спільні", push: "Push Manager",
    settings: "Налаштування", volumes: "Volumes", create: "Створити", delete: "Вилучити",
    edit: "Редагувати", save: "Зберегти", cancel: "Скасувати", name: "Назва", path: "Шлях",
    quota: "Quota(GB)", used: "Використано", available: "Доступно", username: "Ім'я користувача",
    password: "Пароль", admin: "Адмін", storage_quota: "Quota сховища",
    home_directory: "Домашній каталог", smb_status: "Статус SMB", smb_shares: "SMB Shares",
    share_name: "Назва спільного", comment: "Коментар", read_only: "Тільки читання",
    browseable: "Можна переглядати", guest_access: "Гостьовий доступ", language: "Мова",
    running: "Працює", stopped: "Зупинено", operation_success: "Успіх",
    operation_failed: "Невдача", confirm_delete: "Підтвердити вилучення?", no_data: "Немає даних",
    create_volume: "Створити Volume", create_user: "Створити користувача", create_share: "Створити share",
    operation: "Операція", yes: "Так", no: "Ні", system_info: "System info",
    service_status: "Статус сервісу", ip_address: "IP адреса", push_targets: "Push Targets",
    push_files: "Push Files", local_folder: "Місцева folder", target_device: "Target Device",
    add_target: "Додати Target", target_name: "Target Name", target_ip: "Target IP",
    target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
    push_now: "Push Now", pushing: "Pushing...", push_history: "Push History",
    scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
    found_devices: "Found Devices", online: "Online", offline: "Offline",
    send: "Send", receive: "Receive", push_status: "Push Status",
    success: "Успіх", failed: "Невдача", progress: "Progress",
    file_count: "Кількість файлів", total_size: "Загальний розмір"
  }
};

// ==========================================
// Express 应用
// ==========================================

const app: Application = express();
app.use(cors());
app.use(express.json());

// ==========================================
// 辅助函数
// ==========================================

function loadConfig(): void {
  try {
    if (fs.existsSync(CONFIG_PATH)) {
      const content = fs.readFileSync(CONFIG_PATH, 'utf-8');
      config = JSON.parse(content);
      receiveDir = config.receive_dir || 'nas_data/received';
    } else {
      config = {
        server: { port: PORT, language: 'zh_CN' },
        storage: { volumes: [] },
        users: [],
        smb: { shares: [] },
        push: { targets: [] },
        data_dir: 'nas_data',
        receive_dir: 'nas_data/received'
      };
      saveConfig();
    }
  } catch {
    config = {
      server: { port: PORT, language: 'zh_CN' },
      storage: { volumes: [] },
      users: [],
      smb: { shares: [] },
      push: { targets: [] },
      data_dir: 'nas_data',
      receive_dir: 'nas_data/received'
    };
  }
}

function saveConfig(): void {
  try {
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf-8');
  } catch (error) {
    console.error('Failed to save config:', error);
  }
}

function ensureAdminUser(): void {
  const adminExists: boolean = config.users.some(u => u.username === 'admin');
  if (!adminExists) {
    config.users.push({
      username: 'admin',
      password: crypto.createHash('sha256').update('admin').digest('hex'),
      is_admin: true,
      home_dir: '/mnt/data/admin',
      storage_quota_gb: 0
    });
    saveConfig();
  }
}

function sha256Hash(text: string): string {
  return crypto.createHash('sha256').update(text).digest('hex');
}

function getLocalIPs(): IPInfo[] {
  const ips: IPInfo[] = [];
  const interfaces = os.networkInterfaces();

  Object.entries(interfaces).forEach(([name, nets]) => {
    if (!nets) return;
    nets.forEach(net => {
      if (net.family === 'IPv4' && !net.internal) {
        const ip = net.address;
        let type: 'wan' | 'lan' | 'loopback' | 'local' = 'lan';
        if (ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.')) {
          type = 'lan';
        }
        ips.push({
          ip,
          name,
          adapter: name,
          type,
          network: net.cidr || '',
          device_id: crypto.randomBytes(4).toString('hex')
        });
      }
    });
  });

  ips.push({
    ip: '127.0.0.1',
    name: 'localhost',
    adapter: 'Loopback',
    type: 'loopback',
    device_id: 'loopback'
  });

  return ips;
}

function generateId(): string {
  return crypto.randomBytes(8).toString('hex');
}

function ensureDir(dir: string): void {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

// ==========================================
// API 接口
// ==========================================

// 存储管理 API
app.get('/api/storage/volumes', (req: Request, res: Response): void => {
  res.json({ volumes: config.storage.volumes });
});

app.post('/api/storage/volumes', (req: Request, res: Response): void => {
  const { name, path, quota_gb }: { name: string; path: string; quota_gb: number } = req.body;
  config.storage.volumes.push({ name, path, quota_gb });
  saveConfig();
  ensureDir(path);
  res.json({ success: true, message: 'Volume created' });
});

app.post('/api/storage/volumes/delete', (req: Request, res: Response): void => {
  const { name }: { name: string } = req.body;
  config.storage.volumes = config.storage.volumes.filter(v => v.name !== name);
  saveConfig();
  res.json({ success: true, message: 'Volume deleted' });
});

// 用户管理 API
app.get('/api/users', (req: Request, res: Response): void => {
  res.json({ users: config.users });
});

app.post('/api/users', (req: Request, res: Response): void => {
  const { username, password, is_admin, home_dir, storage_quota_gb }: User = req.body;
  config.users.push({
    username,
    password: sha256Hash(password),
    is_admin: is_admin || false,
    home_dir: home_dir || `/mnt/data/${username}`,
    storage_quota_gb: storage_quota_gb || 0
  });
  saveConfig();
  res.json({ success: true, message: 'User created' });
});

app.post('/api/users/delete', (req: Request, res: Response): void => {
  const { username }: { username: string } = req.body;
  config.users = config.users.filter(u => u.username !== username);
  saveConfig();
  res.json({ success: true, message: 'User deleted' });
});

// SMB共享管理 API
app.get('/api/smb/shares', (req: Request, res: Response): void => {
  res.json({ shares: config.smb.shares });
});

app.post('/api/smb/shares', (req: Request, res: Response): void => {
  const { name, path, comment, read_only, browseable, guest_access }: SMBShare = req.body;
  config.smb.shares.push({
    name,
    path,
    comment: comment || '',
    read_only: read_only || false,
    browseable: browseable || true,
    guest_access: guest_access || false
  });
  saveConfig();
  ensureDir(path);
  res.json({ success: true, message: 'Share created' });
});

app.post('/api/smb/shares/delete', (req: Request, res: Response): void => {
  const { name }: { name: string } = req.body;
  config.smb.shares = config.smb.shares.filter(s => s.name !== name);
  saveConfig();
  res.json({ success: true, message: 'Share deleted' });
});

app.get('/api/smb/status', (req: Request, res: Response): void => {
  res.json({ running: false, message: 'SMB service status (mock)' });
});

app.post('/api/smb/start', (req: Request, res: Response): void => {
  res.json({ success: true, message: 'SMB service started (mock)' });
});

app.post('/api/smb/stop', (req: Request, res: Response): void => {
  res.json({ success: true, message: 'SMB service stopped (mock)' });
});

// 推送管理 API
app.get('/api/push/targets', (req: Request, res: Response): void => {
  res.json({ targets: config.push.targets });
});

app.post('/api/push/targets', (req: Request, res: Response): void => {
  const { name, ip, port }: { name: string; ip: string; port: number } = req.body;
  const target: PushTarget = { id: generateId(), name, ip, port };
  config.push.targets.push(target);
  saveConfig();
  res.json({ success: true, message: 'Target added', target });
});

app.post('/api/push/targets/delete', (req: Request, res: Response): void => {
  const { id }: { id: string } = req.body;
  config.push.targets = config.push.targets.filter(t => t.id !== id);
  saveConfig();
  res.json({ success: true, message: 'Target deleted' });
});

app.post('/api/push/targets/check', (req: Request, res: Response): void => {
  const { id }: { id: string } = req.body;
  const target: PushTarget | undefined = config.push.targets.find(t => t.id === id);
  if (target) {
    res.json({ status: 'online', message: 'Target reachable (mock)' });
  } else {
    res.json({ status: 'offline', message: 'Target not found' });
  }
});

app.post('/api/push/folder', (req: Request, res: Response): void => {
  const { target_id, folder_path }: { target_id: string; folder_path: string } = req.body;
  const target: PushTarget | undefined = config.push.targets.find(t => t.id === target_id);

  if (!target) {
    res.json({ success: false, message: 'Target not found' });
    return;
  }

  pushStatus.active = {
    target_id,
    folder: folder_path,
    total_files: 100,
    sent_files: 0,
    start_time: new Date().toISOString()
  };

  res.json({ success: true, message: 'Push started' });

  // 模拟推送过程
  setTimeout(() => {
    if (pushStatus.active) {
      pushStatus.active.sent_files = 50;
    }
  }, 2000);

  setTimeout(() => {
    if (pushStatus.active) {
      pushStatus.history.push({
        time: pushStatus.active.start_time,
        target: target.name,
        folder: pushStatus.active.folder,
        sent_files: pushStatus.active.total_files,
        total_files: pushStatus.active.total_files,
        status: 'success'
      });
      pushStatus.active = undefined;
    }
  }, 5000);
});

app.get('/api/push/status', (req: Request, res: Response): void => {
  res.json(pushStatus);
});

// 接收推送 API
app.post('/api/receive/push', (req: Request, res: Response): void => {
  ensureDir(receiveDir);
  const { files, source }: { files: string[]; source: string } = req.body;
  const receivedPath: string = path.join(receiveDir, source);
  ensureDir(receivedPath);
  res.json({ success: true, message: 'Files received', count: files.length });
});

app.get('/api/receive/files', (req: Request, res: Response): void => {
  ensureDir(receiveDir);
  const files: string[] = [];
  if (fs.existsSync(receiveDir)) {
    const dirs: string[] = fs.readdirSync(receiveDir);
    dirs.forEach(dir => {
      const dirPath: string = path.join(receiveDir, dir);
      if (fs.statSync(dirPath).isDirectory()) {
        const subFiles: string[] = fs.readdirSync(dirPath);
        subFiles.forEach(f => files.push(path.join(dir, f)));
      }
    });
  }
  res.json({ files, count: files.length });
});

// IP管理 API
app.get('/api/ip/local', (req: Request, res: Response): void => {
  res.json({ ips: getLocalIPs() });
});

app.get('/api/ip/scan', async (req: Request, res: Response): void => {
  const port: number = parseInt(req.query.port as string) || 8081;
  const devices: DeviceInfo[] = [];

  // 模拟扫描局域网
  const ips: IPInfo[] = getLocalIPs();
  ips.forEach(ipInfo => {
    if (ipInfo.type === 'lan') {
      devices.push({
        ip: ipInfo.ip,
        port,
        online: true
      });
    }
  });

  res.json({ devices, count: devices.length });
});

// 国际化 API
app.get('/api/i18n/', (req: Request, res: Response): void => {
  const lang: string = (req.query.lang as string) || 'zh_CN';
  const translations: TranslationDict = TRANSLATIONS[lang] || TRANSLATIONS['zh_CN'];
  res.json(translations);
});

app.get('/api/i18n/languages', (req: Request, res: Response): void => {
  res.json(LANG_NAMES);
});

// 系统信息 API
app.get('/api/system/info', (req: Request, res: Response): void => {
  res.json({
    version: '1.0.0',
    platform: os.platform(),
    arch: os.arch(),
    cpus: os.cpus().length,
    memory: os.totalmem(),
    uptime: os.uptime()
  });
});

// 主页面 HTML
const INDEX_HTML: string = `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>小思超级NAS - TypeScript版</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
.header { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.header h1 { color: #667eea; font-size: 24px; }
.header p { color: #666; margin-top: 5px; }
.nav { display: flex; gap: 10px; margin-top: 20px; }
.nav-item { padding: 10px 20px; background: #f5f5f5; border-radius: 5px; cursor: pointer; transition: all 0.3s; }
.nav-item.active, .nav-item:hover { background: #667eea; color: white; }
.content { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.page { display: none; }
.page.active { display: block; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
th { background: #667eea; color: white; }
.btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; transition: all 0.3s; }
.btn-primary { background: #667eea; color: white; }
.btn-danger { background: #f56565; color: white; }
.btn-success { background: #48bb78; color: white; }
.btn:hover { opacity: 0.8; }
.stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 10px; }
.stat-card h3 { font-size: 18px; margin-bottom: 10px; }
.stat-card p { font-size: 32px; font-weight: bold; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; color: #666; }
.form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
.modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
.modal.show { display: flex; justify-content: center; align-items: center; }
.modal-content { background: white; padding: 20px; border-radius: 10px; width: 400px; }
.modal-title { font-size: 20px; color: #667eea; margin-bottom: 20px; }
.form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
.ip-item { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
.badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.badge-success { background: #48bb78; color: white; }
.badge-warning { background: #ed8936; color: white; }
.badge-danger { background: #f56565; color: white; }
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1 id="app-title">小思超级NAS - TypeScript版</h1>
<p>TypeScript实现的高性能NAS管理系统</p>
<div class="nav">
<div class="nav-item active" data-page="dashboard">控制台</div>
<div class="nav-item" data-page="storage">存储</div>
<div class="nav-item" data-page="users">用户</div>
<div class="nav-item" data-page="shares">共享</div>
<div class="nav-item" data-page="push">推送</div>
<div class="nav-item" data-page="settings">设置</div>
</div>
</div>
<div class="content">
<div class="page active" id="page-dashboard">
<h2>系统概览</h2>
<div class="stats-grid">
<div class="stat-card"><h3>存储卷</h3><p id="stat-volumes">0</p></div>
<div class="stat-card"><h3>用户数</h3><p id="stat-users">0</p></div>
<div class="stat-card"><h3>共享数</h3><p id="stat-shares">0</p></div>
<div class="stat-card"><h3>SMB状态</h3><p id="stat-status">停止</p></div>
</div>
<h3 style="margin-top:20px;">本地IP地址</h3>
<div id="local-ips"></div>
</div>
<div class="page" id="page-storage">
<h2>存储卷管理</h2>
<button class="btn btn-primary" onclick="showModal('storage')">创建存储卷</button>
<table id="volumes-table"><tr><th>名称</th><th>路径</th><th>配额(GB)</th><th>操作</th></tr></table>
</div>
<div class="page" id="page-users">
<h2>用户管理</h2>
<button class="btn btn-primary" onclick="showModal('user')">创建用户</button>
<table id="users-table"><tr><th>用户名</th><th>主目录</th><th>配额</th><th>管理员</th><th>操作</th></tr></table>
</div>
<div class="page" id="page-shares">
<h2>SMB共享管理</h2>
<button class="btn btn-primary" onclick="showModal('share')">创建共享</button>
<table id="shares-table"><tr><th>名称</th><th>路径</th><th>操作</th></tr></table>
</div>
<div class="page" id="page-push">
<h2>推送管理</h2>
<div style="display:flex;gap:20px;">
<div style="flex:1;">
<h3>推送目标</h3>
<button class="btn btn-primary" onclick="showModal('target')">添加目标</button>
<table id="targets-table"><tr><th>名称</th><th>地址</th><th>操作</th></tr></table>
</div>
<div style="flex:1;">
<h3>推送文件</h3>
<div class="form-group"><label>目标设备</label><select id="push-target-select"></select></div>
<div class="form-group"><label>文件夹路径</label><input type="text" id="push-folder-path" placeholder="/mnt/data/files"></div>
<button class="btn btn-primary" id="push-btn" onclick="startPush()">立即推送</button>
<div style="margin-top:20px;"><div style="background:#eee;height:20px;border-radius:10px;"><div id="push-progress" style="background:#48bb78;height:20px;border-radius:10px;width:0%;"></div></div><p id="push-status-text" style="margin-top:10px;color:#666;"></p></div>
</div>
</div>
<h3 style="margin-top:20px;">推送历史</h3>
<table id="push-history"><tr><th>时间</th><th>目标</th><th>文件夹</th><th>文件数</th><th>状态</th></tr></table>
</div>
<div class="page" id="page-settings">
<h2>系统设置</h2>
<div class="form-group"><label>语言</label><select id="langSelect" onchange="loadTranslations(this.value)"></select></div>
<div class="form-group"><label>服务端口</label><input type="number" value="${PORT}" readonly></div>
<div class="form-group"><label>版本</label><input type="text" value="1.0.0 (TypeScript)" readonly></div>
</div>
</div>
</div>
<div class="modal" id="modal-storage"><div class="modal-content"><div class="modal-title">创建存储卷</div><div class="form-group"><label>名称</label><input type="text" id="storage-name"></div><div class="form-group"><label>路径</label><input type="text" id="storage-path"></div><div class="form-group"><label>配额(GB)</label><input type="number" id="storage-quota" value="100"></div><div class="form-actions"><button class="btn" onclick="closeModal('storage')">取消</button><button class="btn btn-primary" onclick="createVolume()">保存</button></div></div></div>
<div class="modal" id="modal-user"><div class="modal-content"><div class="modal-title">创建用户</div><div class="form-group"><label>用户名</label><input type="text" id="user-name"></div><div class="form-group"><label>密码</label><input type="password" id="user-password"></div><div class="form-actions"><button class="btn" onclick="closeModal('user')">取消</button><button class="btn btn-primary" onclick="createUser()">保存</button></div></div></div>
<div class="modal" id="modal-share"><div class="modal-content"><div class="modal-title">创建共享</div><div class="form-group"><label>共享名称</label><input type="text" id="share-name"></div><div class="form-group"><label>路径</label><input type="text" id="share-path"></div><div class="form-actions"><button class="btn" onclick="closeModal('share')">取消</button><button class="btn btn-primary" onclick="createShare()">保存</button></div></div></div>
<div class="modal" id="modal-target"><div class="modal-content"><div class="modal-title">添加推送目标</div><div class="form-group"><label>目标名称</label><input type="text" id="target-name"></div><div class="form-row"><div class="form-group"><label>目标IP</label><input type="text" id="target-ip"></div><div class="form-group"><label>目标端口</label><input type="number" id="target-port" value="8091"></div></div><div class="form-actions"><button class="btn" onclick="closeModal('target')">取消</button><button class="btn btn-primary" onclick="addTarget()">保存</button></div></div></div>
<script>
const LANG_NAMES = ${JSON.stringify(LANG_NAMES)};
let translations = {}, currentLang = 'zh_CN';
function initLangSelect() {
    const sel = document.getElementById('langSelect');
    Object.entries(LANG_NAMES).forEach(([code, name]) => {
        const opt = document.createElement('option');
        opt.value = code; opt.textContent = name;
        if (code === currentLang) opt.selected = true;
        sel.appendChild(opt);
    });
    sel.addEventListener('change', () => loadTranslations(sel.value));
}
async function loadTranslations(lang) {
    currentLang = lang;
    try {
        const res = await fetch('/api/i18n/?lang=' + lang);
        translations = await res.json();
        applyTranslations();
    } catch (e) { console.error('Failed to load translations'); }
}
function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (translations[key]) el.textContent = translations[key];
    });
}
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        item.classList.add('active');
        document.getElementById('page-' + item.dataset.page).classList.add('active');
        if (item.dataset.page === 'push') { loadPushTargets(); updatePushTargetSelect(); loadPushHistory(); }
        else if (item.dataset.page === 'dashboard') { loadDashboard(); loadLocalIPs(); }
        else if (item.dataset.page === 'storage') loadVolumes();
        else if (item.dataset.page === 'users') loadUsers();
        else if (item.dataset.page === 'shares') loadShares();
    });
});
async function loadDashboard() {
    try {
        const [v, u, s, smb] = await Promise.all([
            fetch('/api/storage/volumes').then(r => r.json()),
            fetch('/api/users').then(r => r.json()),
            fetch('/api/smb/shares').then(r => r.json()),
            fetch('/api/smb/status').then(r => r.json())
        ]);
        document.getElementById('stat-volumes').textContent = v.volumes ? v.volumes.length : 0;
        document.getElementById('stat-users').textContent = u.users ? u.users.length : 0;
        document.getElementById('stat-shares').textContent = s.shares ? s.shares.length : 0;
        document.getElementById('stat-status').textContent = smb.running ? '运行中' : '已停止';
    } catch (e) { console.error(e); }
}
async function loadLocalIPs() {
    try {
        const res = await fetch('/api/ip/local');
        const data = await res.json();
        const container = document.getElementById('local-ips');
        container.innerHTML = '';
        if (data.ips && data.ips.length) {
            data.ips.forEach(ip => {
                const div = document.createElement('div');
                div.className = 'ip-item';
                div.innerHTML = '<strong>' + ip.ip + '</strong> (' + ip.type + ') - ' + (ip.name || ip.adapter);
                container.appendChild(div);
            });
        }
    } catch (e) { console.error(e); }
}
async function loadVolumes() {
    const res = await fetch('/api/storage/volumes');
    const data = await res.json();
    const tb = document.getElementById('volumes-table');
    tb.innerHTML = '<tr><th>名称</th><th>路径</th><th>配额(GB)</th><th>操作</th></tr>' + (data.volumes && data.volumes.length ?
        data.volumes.map(v => '<tr><td>' + v.name + '</td><td>' + v.path + '</td><td>' + v.quota_gb + '</td><td><button class="btn btn-danger btn-sm" onclick="deleteVolume(\'' + v.name + '\')">删除</button></td></tr>').join('') :
        '<tr><td colspan="4" style="text-align:center;color:#999;">暂无数据</td></tr>');
}
async function loadUsers() {
    const res = await fetch('/api/users');
    const data = await res.json();
    const tb = document.getElementById('users-table');
    tb.innerHTML = '<tr><th>用户名</th><th>主目录</th><th>配额</th><th>管理员</th><th>操作</th></tr>' + (data.users && data.users.length ?
        data.users.map(u => '<tr><td>' + u.username + '</td><td>' + u.home_dir + '</td><td>' + u.storage_quota_gb + '</td><td><span class="badge ' + (u.is_admin ? 'badge-success' : 'badge-warning') + '">' + (u.is_admin ? '是' : '否') + '</span></td><td><button class="btn btn-danger btn-sm" onclick="deleteUser(\'' + u.username + '\')">删除</button></td></tr>').join('') :
        '<tr><td colspan="5" style="text-align:center;color:#999;">暂无数据</td></tr>');
}
async function loadShares() {
    const res = await fetch('/api/smb/shares');
    const data = await res.json();
    const tb = document.getElementById('shares-table');
    tb.innerHTML = '<tr><th>名称</th><th>路径</th><th>操作</th></tr>' + (data.shares && data.shares.length ?
        data.shares.map(s => '<tr><td>' + s.name + '</td><td>' + s.path + '</td><td><button class="btn btn-danger btn-sm" onclick="deleteShare(\'' + s.name + '\')">删除</button></td></tr>').join('') :
        '<tr><td colspan="3" style="text-align:center;color:#999;">暂无数据</td></tr>');
}
async function loadPushTargets() {
    const res = await fetch('/api/push/targets');
    const data = await res.json();
    const tb = document.getElementById('targets-table');
    tb.innerHTML = '<tr><th>名称</th><th>地址</th><th>操作</th></tr>' + (data.targets && data.targets.length ?
        data.targets.map(t => '<tr><td>' + t.name + '</td><td>' + t.ip + ':' + t.port + '</td><td><button class="btn btn-success btn-sm" onclick="checkTarget(\'' + t.id + '\')">检测</button> <button class="btn btn-danger btn-sm" onclick="deleteTarget(\'' + t.id + '\')">删除</button></td></tr>').join('') :
        '<tr><td colspan="3" style="text-align:center;color:#999;">暂无数据</td></tr>');
}
async function updatePushTargetSelect() {
    const res = await fetch('/api/push/targets');
    const data = await res.json();
    const sel = document.getElementById('push-target-select');
    sel.innerHTML = '<option value="">请选择目标设备</option>';
    if (data.targets) {
        data.targets.forEach(t => {
            sel.innerHTML += '<option value="' + t.id + '">' + t.name + ' (' + t.ip + ':' + t.port + ')</option>';
        });
    }
}
async function checkTarget(id) {
    const res = await fetch('/api/push/targets/check', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id}) });
    const data = await res.json();
    alert(data.status);
}
async function addTarget() {
    const name = document.getElementById('target-name').value;
    const ip = document.getElementById('target-ip').value;
    const port = parseInt(document.getElementById('target-port').value);
    if (!name || !ip) { alert('请填写名称和IP'); return; }
    await fetch('/api/push/targets', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name, ip, port}) });
    closeModal('target');
    loadPushTargets();
    updatePushTargetSelect();
}
async function deleteTarget(id) {
    if (confirm('确认删除此目标?')) {
        await fetch('/api/push/targets/delete', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id}) });
        loadPushTargets();
        updatePushTargetSelect();
    }
}
async function startPush() {
    const targetId = document.getElementById('push-target-select').value;
    const folderPath = document.getElementById('push-folder-path').value;
    if (!targetId) { alert('请选择目标设备'); return; }
    if (!folderPath) { alert('请输入文件夹路径'); return; }
    const btn = document.getElementById('push-btn');
    btn.disabled = true;
    btn.textContent = '推送中...';
    document.getElementById('push-progress').style.width = '5%';
    document.getElementById('push-status-text').textContent = '准备推送...';
    try {
        await fetch('/api/push/folder', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target_id: targetId, folder_path: folderPath}) });
        pollPushStatus();
    } catch (e) {
        btn.disabled = false;
        btn.textContent = '立即推送';
        alert('推送启动失败');
    }
}
function pollPushStatus() {
    let count = 0;
    const interval = setInterval(async () => {
        try {
            const res = await fetch('/api/push/status');
            const data = await res.json();
            if (data.active) {
                const pct = Math.round((data.active.sent_files / data.active.total_files) * 100);
                document.getElementById('push-progress').style.width = pct + '%';
                document.getElementById('push-status-text').textContent = data.active.sent_files + ' / ' + data.active.total_files + ' 个文件';
            } else {
                clearInterval(interval);
                document.getElementById('push-progress').style.width = '100%';
                document.getElementById('push-status-text').textContent = '推送完成';
                const btn = document.getElementById('push-btn');
                btn.disabled = false;
                btn.textContent = '立即推送';
                loadPushHistory();
            }
            count++;
            if (count > 600) clearInterval(interval);
        } catch (e) {
            clearInterval(interval);
        }
    }, 1000);
}
async function loadPushHistory() {
    const res = await fetch('/api/push/status');
    const data = await res.json();
    const tb = document.getElementById('push-history');
    tb.innerHTML = '<tr><th>时间</th><th>目标</th><th>文件夹</th><th>文件数</th><th>状态</th></tr>';
    if (data.history && data.history.length) {
        tb.innerHTML += data.history.map(h => '<tr><td>' + (h.time || '') + '</td><td>' + h.target + '</td><td>' + h.folder + '</td><td>' + h.sent_files + ' / ' + h.total_files + '</td><td><span class="badge ' + (h.status === 'success' ? 'badge-success' : 'badge-danger') + '">' + (h.status === 'success' ? '成功' : '失败') + '</span></td></tr>').join('');
    } else {
        tb.innerHTML += '<tr><td colspan="5" style="text-align:center;color:#999;">暂无数据</td></tr>';
    }
}
function showModal(type) { document.getElementById('modal-' + type).classList.add('show'); }
function closeModal(type) { document.getElementById('modal-' + type).classList.remove('show'); }
async function createVolume() {
    const name = document.getElementById('storage-name').value;
    const path = document.getElementById('storage-path').value;
    const quota = parseInt(document.getElementById('storage-quota').value);
    await fetch('/api/storage/volumes', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name, path, quota_gb: quota}) });
    closeModal('storage'); loadVolumes(); loadDashboard();
}
async function createUser() {
    const name = document.getElementById('user-name').value;
    const password = document.getElementById('user-password').value;
    await fetch('/api/users', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({username: name, password}) });
    closeModal('user'); loadUsers(); loadDashboard();
}
async function createShare() {
    const name = document.getElementById('share-name').value;
    const path = document.getElementById('share-path').value;
    await fetch('/api/smb/shares', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name, path}) });
    closeModal('share'); loadShares(); loadDashboard();
}
async function deleteVolume(name) {
    if (confirm('确认删除 ' + name + '?')) {
        await fetch('/api/storage/volumes/delete', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name}) });
        loadVolumes(); loadDashboard();
    }
}
async function deleteUser(username) {
    if (confirm('确认删除 ' + username + '?')) {
        await fetch('/api/users/delete', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({username}) });
        loadUsers(); loadDashboard();
    }
}
async function deleteShare(name) {
    if (confirm('确认删除 ' + name + '?')) {
        await fetch('/api/smb/shares/delete', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name}) });
        loadShares(); loadDashboard();
    }
}
initLangSelect();
loadTranslations('zh_CN');
loadDashboard();
loadLocalIPs();
</script>
</body>
</html>
`;

app.get('/', (req: Request, res: Response): void => {
  res.send(INDEX_HTML);
});

app.get('/index.html', (req: Request, res: Response): void => {
  res.send(INDEX_HTML);
});

// ==========================================
// 启动服务
// ==========================================

function startServer(): void {
  loadConfig();
  ensureAdminUser();

  const localIPs: IPInfo[] = getLocalIPs();

  console.log('='.repeat(50));
  console.log('  小思超级NAS服务启动 (TypeScript)');
  console.log('='.repeat(50));
  console.log(`  本地访问: http://localhost:${PORT}`);
  localIPs.forEach(ipInfo => {
    if (ipInfo.type !== 'loopback') {
      console.log(`  网络访问: http://${ipInfo.ip}:${PORT}`);
    }
  });
  console.log(`  接收目录: ${receiveDir}`);
  console.log('='.repeat(50));
  console.log('  按 Ctrl+C 停止服务');
  console.log('='.repeat(50));

  app.listen(PORT, '0.0.0.0', (): void => {
    console.log(`Server is running on port ${PORT}`);
  });
}

startServer();