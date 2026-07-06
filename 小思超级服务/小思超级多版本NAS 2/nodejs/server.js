/**
 * 小思超级多版本NAS服务 - Node.js实现
 * 基于Express框架，支持完整NAS管理功能
 * 默认端口: 8081
 */

const express = require('express');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const os = require('os');
const http = require('http');
const { FormDataParser, FormDataBuilder } = require('./formdata');

const app = express();
const PORT = 8081;

// ==========================================
// 28种语言翻译支持
// ==========================================
const TRANSLATIONS = {
    zh_CN: {
        app_name: "小思超级NAS", dashboard: "控制台", storage: "存储管理",
        users: "用户管理", shares: "共享管理", push: "推送管理",
        settings: "设置", volumes: "存储卷", create: "创建", delete: "删除",
        edit: "编辑", save: "保存", cancel: "取消", name: "名称", path: "路径",
        quota: "配额", used: "已用", available: "可用", username: "用户名",
        password: "密码", admin: "管理员", storage_quota: "存储配额",
        home_directory: "主目录", smb_status: "SMB状态", smb_shares: "SMB共享",
        share_name: "共享名称", comment: "备注", read_only: "只读",
        browseable: "可浏览", guest_access: "访客访问", language: "语言",
        running: "运行中", stopped: "已停止", operation_success: "操作成功",
        operation_failed: "操作失败", confirm_delete: "确认删除", no_data: "暂无数据",
        create_volume: "创建存储卷", create_user: "创建用户", create_share: "创建共享",
        operation: "操作", yes: "是", no: "否", system_info: "系统信息",
        service_status: "服务状态", ip_address: "IP地址", push_targets: "推送目标",
        push_files: "推送文件", local_folder: "本地文件夹", target_device: "目标设备",
        add_target: "添加目标", target_name: "目标名称", target_ip: "目标IP",
        target_port: "目标端口", push_folder: "推送文件夹", select_folder: "选择文件夹",
        push_now: "立即推送", pushing: "推送中", push_history: "推送历史",
        scan_ip: "扫描IP", local_ips: "本机IP", scan: "扫描",
        found_devices: "发现设备", online: "在线", offline: "离线",
        send: "发送", receive: "接收", push_status: "推送状态",
        success: "成功", failed: "失败", progress: "进度",
        file_count: "文件数", total_size: "总大小"
    },
    zh_TW: {
        app_name: "小思超级NAS", dashboard: "控制台", storage: "儲存管理",
        users: "使用者管理", shares: "共用管理", push: "推送管理",
        settings: "設定", volumes: "儲存卷", create: "建立", delete: "刪除",
        edit: "編輯", save: "儲存", cancel: "取消", name: "名稱", path: "路徑",
        quota: "配額", used: "已用", available: "可用", username: "使用者名稱",
        password: "密碼", admin: "管理員", storage_quota: "儲存配額",
        home_directory: "主目錄", smb_status: "SMB狀態", smb_shares: "SMB共用",
        share_name: "共用名稱", comment: "備註", read_only: "唯讀",
        browseable: "可瀏覽", guest_access: "訪客存取", language: "語言",
        running: "執行中", stopped: "已停止", operation_success: "操作成功",
        operation_failed: "操作失敗", confirm_delete: "確認刪除", no_data: "暫無資料",
        create_volume: "建立儲存卷", create_user: "建立使用者", create_share: "建立共用",
        operation: "操作", yes: "是", no: "否", system_info: "系統資訊",
        service_status: "服務狀態", ip_address: "IP位址", push_targets: "推送目標",
        push_files: "推送檔案", local_folder: "本地資料夾", target_device: "目標裝置",
        add_target: "新增目標", target_name: "目標名稱", target_ip: "目標IP",
        target_port: "目標埠", push_folder: "推送資料夾", select_folder: "選擇資料夾",
        push_now: "立即推送", pushing: "推送中", push_history: "推送歷史",
        scan_ip: "掃描IP", local_ips: "本機IP", scan: "掃描",
        found_devices: "發現裝置", online: "線上", offline: "離線",
        send: "傳送", receive: "接收", push_status: "推送狀態",
        success: "成功", failed: "失敗", progress: "進度",
        file_count: "檔案數", total_size: "總大小"
    },
    en_US: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Storage",
        users: "Users", shares: "Shares", push: "Push Manager",
        settings: "Settings", volumes: "Volumes", create: "Create", delete: "Delete",
        edit: "Edit", save: "Save", cancel: "Cancel", name: "Name", path: "Path",
        quota: "Quota", used: "Used", available: "Available", username: "Username",
        password: "Password", admin: "Admin", storage_quota: "Storage Quota",
        home_directory: "Home Directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
        share_name: "Share Name", comment: "Comment", read_only: "Read Only",
        browseable: "Browseable", guest_access: "Guest Access", language: "Language",
        running: "Running", stopped: "Stopped", operation_success: "Success",
        operation_failed: "Failed", confirm_delete: "Confirm Delete", no_data: "No Data",
        create_volume: "Create Volume", create_user: "Create User", create_share: "Create Share",
        operation: "Action", yes: "Yes", no: "No", system_info: "System Info",
        service_status: "Service Status", ip_address: "IP Address", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Local Folder", target_device: "Target Device",
        add_target: "Add Target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
        found_devices: "Found Devices", online: "Online", offline: "Offline",
        send: "Send", receive: "Receive", push_status: "Push Status",
        success: "Success", failed: "Failed", progress: "Progress",
        file_count: "File Count", total_size: "Total Size"
    },
    en_GB: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Storage",
        users: "Users", shares: "Shares", push: "Push Manager",
        settings: "Settings", volumes: "Volumes", create: "Create", delete: "Delete",
        edit: "Edit", save: "Save", cancel: "Cancel", name: "Name", path: "Path",
        quota: "Quota", used: "Used", available: "Available", username: "Username",
        password: "Password", admin: "Admin", storage_quota: "Storage Quota",
        home_directory: "Home Directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
        share_name: "Share Name", comment: "Comment", read_only: "Read Only",
        browseable: "Browseable", guest_access: "Guest Access", language: "Language",
        running: "Running", stopped: "Stopped", operation_success: "Success",
        operation_failed: "Failed", confirm_delete: "Confirm Delete", no_data: "No Data",
        create_volume: "Create Volume", create_user: "Create User", create_share: "Create Share",
        operation: "Action", yes: "Yes", no: "No", system_info: "System Info",
        service_status: "Service Status", ip_address: "IP Address", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Local Folder", target_device: "Target Device",
        add_target: "Add Target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Scan IP", local_ips: "Local IPs", scan: "Scan",
        found_devices: "Found Devices", online: "Online", offline: "Offline",
        send: "Send", receive: "Receive", push_status: "Push Status",
        success: "Success", failed: "Failed", progress: "Progress",
        file_count: "File Count", total_size: "Total Size"
    },
    ja_JP: {
        app_name: "小思スーパーNAS", dashboard: "ダッシュボード", storage: "ストレージ",
        users: "ユーザー", shares: "共有", push: "プッシュ管理",
        settings: "設定", volumes: "ボリューム", create: "作成", delete: "削除",
        edit: "編集", save: "保存", cancel: "キャンセル", name: "名前", path: "パス",
        quota: "クォータ", used: "使用中", available: "利用可能", username: "ユーザー名",
        password: "パスワード", admin: "管理者", storage_quota: "ストレージクォータ",
        home_directory: "ホームディレクトリ", smb_status: "SMB状態", smb_shares: "SMB共有",
        share_name: "共有名", comment: "コメント", read_only: "読み取り専用",
        browseable: "参照可能", guest_access: "ゲストアクセス", language: "言語",
        running: "実行中", stopped: "停止中", operation_success: "操作成功",
        operation_failed: "操作失敗", confirm_delete: "削除の確認", no_data: "データなし",
        create_volume: "ボリューム作成", create_user: "ユーザー作成", create_share: "共有作成",
        operation: "操作", yes: "はい", no: "いいえ", system_info: "システム情報",
        service_status: "サービス状態", ip_address: "IPアドレス", push_targets: "プッシュ先",
        push_files: "ファイル送信", local_folder: "ローカルフォルダ", target_device: "対象デバイス",
        add_target: "対象を追加", target_name: "対象名", target_ip: "対象IP",
        target_port: "対象ポート", push_folder: "フォルダ送信", select_folder: "フォルダ選択",
        push_now: "今すぐ送信", pushing: "送信中", push_history: "送信履歴",
        scan_ip: "IPスキャン", local_ips: "ローカルIP", scan: "スキャン",
        found_devices: "発見デバイス", online: "オンライン", offline: "オフライン",
        send: "送信", receive: "受信", push_status: "送信状態",
        success: "成功", failed: "失敗", progress: "進捗",
        file_count: "ファイル数", total_size: "合計サイズ"
    },
    ko_KR: {
        app_name: "小思슈퍼 NAS", dashboard: "대시보드", storage: "저장소",
        users: "사용자", shares: "공유", push: "푸시 관리",
        settings: "설정", volumes: "볼륨", create: "생성", delete: "삭제",
        edit: "편집", save: "저장", cancel: "취소", name: "이름", path: "경로",
        quota: "할당량", used: "사용", available: "사용 가능", username: "사용자 이름",
        password: "비밀번호", admin: "관리자", storage_quota: "저장소 할당량",
        home_directory: "홈 디렉터리", smb_status: "SMB 상태", smb_shares: "SMB 공유",
        share_name: "공유 이름", comment: "설명", read_only: "읽기 전용",
        browseable: "검색 가능", guest_access: "게스트 접근", language: "언어",
        running: "실행 중", stopped: "중지됨", operation_success: "성공",
        operation_failed: "실패", confirm_delete: "삭제 확인", no_data: "데이터 없음",
        create_volume: "볼륨 생성", create_user: "사용자 생성", create_share: "공유 생성",
        operation: "작업", yes: "예", no: "아니요", system_info: "시스템 정보",
        service_status: "서비스 상태", ip_address: "IP 주소", push_targets: "푸시 대상",
        push_files: "파일 푸시", local_folder: "로컬 폴더", target_device: "대상 장치",
        add_target: "대상 추가", target_name: "대상 이름", target_ip: "대상 IP",
        target_port: "대상 포트", push_folder: "폴더 푸시", select_folder: "폴더 선택",
        push_now: "푸시 시작", pushing: "푸시 중", push_history: "푸시 기록",
        scan_ip: "IP 스캔", local_ips: "로컬 IP", scan: "스캔",
        found_devices: "발견된 장치", online: "온라인", offline: "오프라인",
        send: "보내기", receive: "받기", push_status: "푸시 상태",
        success: "성공", failed: "실패", progress: "진행률",
        file_count: "파일 수", total_size: "전체 크기"
    },
    fr_FR: {
        app_name: "Xiaosi Super NAS", dashboard: "Tableau de bord", storage: "Stockage",
        users: "Utilisateurs", shares: "Partages", push: "Gestion Push",
        settings: "Paramètres", volumes: "Volumes", create: "Créer", delete: "Supprimer",
        edit: "Modifier", save: "Enregistrer", cancel: "Annuler", name: "Nom", path: "Chemin",
        quota: "Quota", used: "Utilisé", available: "Disponible", username: "Nom d'utilisateur",
        password: "Mot de passe", admin: "Admin", storage_quota: "Quota stockage",
        home_directory: "Répertoire home", smb_status: "Statut SMB", smb_shares: "Partages SMB",
        share_name: "Nom du partage", comment: "Commentaire", read_only: "Lecture seule",
        browseable: "Navigable", guest_access: "Accès invité", language: "Langue",
        running: "En cours", stopped: "Arrêté", operation_success: "Succès",
        operation_failed: "Échec", confirm_delete: "Confirmer suppression", no_data: "Pas de données",
        create_volume: "Créer volume", create_user: "Créer utilisateur", create_share: "Créer partage",
        operation: "Action", yes: "Oui", no: "Non", system_info: "Infos système",
        service_status: "Statut service", ip_address: "Adresse IP", push_targets: "Cibles Push",
        push_files: "Fichiers Push", local_folder: "Dossier local", target_device: "Appareil cible",
        add_target: "Ajouter cible", target_name: "Nom cible", target_ip: "IP cible",
        target_port: "Port cible", push_folder: "Dossier Push", select_folder: "Sélectionner dossier",
        push_now: "Push maintenant", pushing: "Push en cours", push_history: "Historique Push",
        scan_ip: "Scanner IP", local_ips: "IPs locales", scan: "Scanner",
        found_devices: "Appareils trouvés", online: "En ligne", offline: "Hors ligne",
        send: "Envoyer", receive: "Recevoir", push_status: "Statut Push",
        success: "Succès", failed: "Échec", progress: "Progression",
        file_count: "Nombre fichiers", total_size: "Taille totale"
    },
    de_DE: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Speicher",
        users: "Benutzer", shares: "Freigaben", push: "Push-Manager",
        settings: "Einstellungen", volumes: "Volumes", create: "Erstellen", delete: "Löschen",
        edit: "Bearbeiten", save: "Speichern", cancel: "Abbrechen", name: "Name", path: "Pfad",
        quota: "Quota", used: "Verwendet", available: "Verfügbar", username: "Benutzername",
        password: "Passwort", admin: "Admin", storage_quota: "Speicher-Quota",
        home_directory: "Home-Verzeichnis", smb_status: "SMB-Status", smb_shares: "SMB-Freigaben",
        share_name: "Freigabename", comment: "Kommentar", read_only: "Schreibgeschützt",
        browseable: "Durchsuchbar", guest_access: "Gastzugriff", language: "Sprache",
        running: "Läuft", stopped: "Gestoppt", operation_success: "Erfolg",
        operation_failed: "Fehler", confirm_delete: "Löschen bestätigen", no_data: "Keine Daten",
        create_volume: "Volume erstellen", create_user: "Benutzer erstellen", create_share: "Freigabe erstellen",
        operation: "Aktion", yes: "Ja", no: "Nein", system_info: "Systeminfo",
        service_status: "Service-Status", ip_address: "IP-Adresse", push_targets: "Push-Ziele",
        push_files: "Push-Dateien", local_folder: "Lokaler Ordner", target_device: "Zielgerät",
        add_target: "Ziel hinzufügen", target_name: "Zielname", target_ip: "Ziel-IP",
        target_port: "Ziel-Port", push_folder: "Ordner pushen", select_folder: "Ordner wählen",
        push_now: "Jetzt pushen", pushing: "Pushing", push_history: "Push-Historie",
        scan_ip: "IP scannen", local_ips: "Lokale IPs", scan: "Scannen",
        found_devices: "Gefundene Geräte", online: "Online", offline: "Offline",
        send: "Senden", receive: "Empfangen", push_status: "Push-Status",
        success: "Erfolg", failed: "Fehler", progress: "Fortschritt",
        file_count: "Dateianzahl", total_size: "Gesamtgröße"
    },
    es_ES: {
        app_name: "Xiaosi Super NAS", dashboard: "Panel", storage: "Almacenamiento",
        users: "Usuarios", shares: "Compartidos", push: "Gestor Push",
        settings: "Configuración", volumes: "Volúmenes", create: "Crear", delete: "Eliminar",
        edit: "Editar", save: "Guardar", cancel: "Cancelar", name: "Nombre", path: "Ruta",
        quota: "Cuota", used: "Usado", available: "Disponible", username: "Usuario",
        password: "Contraseña", admin: "Admin", storage_quota: "Cuota almacenamiento",
        home_directory: "Directorio home", smb_status: "Estado SMB", smb_shares: "Compartidos SMB",
        share_name: "Nombre compartido", comment: "Comentario", read_only: "Solo lectura",
        browseable: "Navegable", guest_access: "Acceso invitado", language: "Idioma",
        running: "Ejecutando", stopped: "Detenido", operation_success: "Éxito",
        operation_failed: "Error", confirm_delete: "Confirmar eliminación", no_data: "Sin datos",
        create_volume: "Crear volumen", create_user: "Crear usuario", create_share: "Crear compartido",
        operation: "Acción", yes: "Sí", no: "No", system_info: "Info sistema",
        service_status: "Estado servicio", ip_address: "Dirección IP", push_targets: "Destinos Push",
        push_files: "Archivos Push", local_folder: "Carpeta local", target_device: "Dispositivo destino",
        add_target: "Agregar destino", target_name: "Nombre destino", target_ip: "IP destino",
        target_port: "Puerto destino", push_folder: "Carpeta Push", select_folder: "Seleccionar carpeta",
        push_now: "Push ahora", pushing: "Pushing", push_history: "Historial Push",
        scan_ip: "Escanear IP", local_ips: "IPs locales", scan: "Escanear",
        found_devices: "Dispositivos encontrados", online: "En línea", offline: "Fuera de línea",
        send: "Enviar", receive: "Recibir", push_status: "Estado Push",
        success: "Éxito", failed: "Error", progress: "Progreso",
        file_count: "Número archivos", total_size: "Tamaño total"
    },
    it_IT: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Archiviazione",
        users: "Utenti", shares: "Condivisioni", push: "Gestore Push",
        settings: "Impostazioni", volumes: "Volume", create: "Crea", delete: "Elimina",
        edit: "Modifica", save: "Salva", cancel: "Annulla", name: "Nome", path: "Percorso",
        quota: "Quota", used: "Usato", available: "Disponibile", username: "Nome utente",
        password: "Password", admin: "Admin", storage_quota: "Quota archiviazione",
        home_directory: "Directory home", smb_status: "Stato SMB", smb_shares: "Condivisioni SMB",
        share_name: "Nome condivisione", comment: "Commento", read_only: "Sola lettura",
        browseable: "Navigabile", guest_access: "Accesso guest", language: "Lingua",
        running: "In esecuzione", stopped: "Fermato", operation_success: "Successo",
        operation_failed: "Errore", confirm_delete: "Conferma eliminazione", no_data: "Nessun dato",
        create_volume: "Crea volume", create_user: "Crea utente", create_share: "Crea condivisione",
        operation: "Azione", yes: "Sì", no: "No", system_info: "Info sistema",
        service_status: "Stato servizio", ip_address: "Indirizzo IP", push_targets: "Destinazioni Push",
        push_files: "File Push", local_folder: "Cartella locale", target_device: "Dispositivo destinazione",
        add_target: "Aggiungi destinazione", target_name: "Nome destinazione", target_ip: "IP destinazione",
        target_port: "Porta destinazione", push_folder: "Cartella Push", select_folder: "Seleziona cartella",
        push_now: "Push ora", pushing: "Pushing", push_history: "Storia Push",
        scan_ip: "Scansiona IP", local_ips: "IP locali", scan: "Scansiona",
        found_devices: "Dispositivi trovati", online: "Online", offline: "Offline",
        send: "Invia", receive: "Ricevi", push_status: "Stato Push",
        success: "Successo", failed: "Errore", progress: "Progresso",
        file_count: "Numero file", total_size: "Dimensione totale"
    },
    pt_BR: {
        app_name: "Xiaosi Super NAS", dashboard: "Painel", storage: "Armazenamento",
        users: "Usuários", shares: "Compartilhamentos", push: "Gerenciador Push",
        settings: "Configurações", volumes: "Volumes", create: "Criar", delete: "Excluir",
        edit: "Editar", save: "Salvar", cancel: "Cancelar", name: "Nome", path: "Caminho",
        quota: "Cota", used: "Usado", available: "Disponível", username: "Nome de usuário",
        password: "Senha", admin: "Admin", storage_quota: "Cota de armazenamento",
        home_directory: "Diretório home", smb_status: "Status SMB", smb_shares: "Compartilhamentos SMB",
        share_name: "Nome do compartilhamento", comment: "Comentário", read_only: "Somente leitura",
        browseable: "Navegável", guest_access: "Acesso guest", language: "Idioma",
        running: "Executando", stopped: "Parado", operation_success: "Sucesso",
        operation_failed: "Erro", confirm_delete: "Confirmar exclusão", no_data: "Sem dados",
        create_volume: "Criar volume", create_user: "Criar usuário", create_share: "Criar compartilhamento",
        operation: "Ação", yes: "Sim", no: "Não", system_info: "Info sistema",
        service_status: "Status serviço", ip_address: "Endereço IP", push_targets: "Destinos Push",
        push_files: "Arquivos Push", local_folder: "Pasta local", target_device: "Dispositivo destino",
        add_target: "Adicionar destino", target_name: "Nome destino", target_ip: "IP destino",
        target_port: "Porta destino", push_folder: "Pasta Push", select_folder: "Selecionar pasta",
        push_now: "Push agora", pushing: "Pushing", push_history: "História Push",
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
        quota: "Квота", used: "Использовано", available: "Доступно", username: "Имя пользователя",
        password: "Пароль", admin: "Админ", storage_quota: "Квота хранилища",
        home_directory: "Домашний каталог", smb_status: "Статус SMB", smb_shares: "Ресурсы SMB",
        share_name: "Имя ресурса", comment: "Комментарий", read_only: "Только чтение",
        browseable: "Обзор", guest_access: "Гостевой доступ", language: "Язык",
        running: "Запущено", stopped: "Остановлено", operation_success: "Успех",
        operation_failed: "Ошибка", confirm_delete: "Подтвердить удаление", no_data: "Нет данных",
        create_volume: "Создать том", create_user: "Создать пользователя", create_share: "Создать ресурс",
        operation: "Действие", yes: "Да", no: "Нет", system_info: "Системная информация",
        service_status: "Статус сервиса", ip_address: "IP адрес", push_targets: "Push цели",
        push_files: "Push файлы", local_folder: "Локальная папка", target_device: "Целевое устройство",
        add_target: "Добавить цель", target_name: "Имя цели", target_ip: "IP цели",
        target_port: "Порт цели", push_folder: "Push папка", select_folder: "Выбрать папку",
        push_now: "Push сейчас", pushing: "Pushing", push_history: "История Push",
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
        operation_failed: "فشل", confirm_delete: "تأكيد الحذف", no_data: "لا بيانات",
        create_volume: "إنشاء حجم", create_user: "إنشاء مستخدم", create_share: "إنشاء مشاركة",
        operation: "عملية", yes: "نعم", no: "لا", system_info: "معلومات النظام",
        service_status: "حالة الخدمة", ip_address: "عنوان IP", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "المجلد المحلي", target_device: "الجهاز المستهدف",
        add_target: "إضافة هدف", target_name: "اسم الهدف", target_ip: "IP الهدف",
        target_port: "بوابة الهدف", push_folder: "Push Folder", select_folder: "اختر مجلد",
        push_now: "Push الآن", pushing: "Pushing", push_history: "Push History",
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
        operation_failed: "विफल", confirm_delete: "हटाने की पुष्टि", no_data: "कोई डेटा",
        create_volume: "Volume बनाएं", create_user: "उपयोगकर्ता बनाएं", create_share: "शेयर बनाएं",
        operation: "कार्य", yes: "हाँ", no: "नहीं", system_info: "सिस्टम जानकारी",
        service_status: "सेवा स्थिति", ip_address: "IP पता", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "लोकल फोल्डर", target_device: "Target Device",
        add_target: "Target जोड़ें", target_name: "Target नाम", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
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
        quota: "Kota", used: "Kullanılan", available: "Mevcut", username: "Kullanıcı adı",
        password: "Şifre", admin: "Admin", storage_quota: "Depolama kotası",
        home_directory: "Ana dizin", smb_status: "SMB Durumu", smb_shares: "SMB Paylaşımları",
        share_name: "Paylaşım adı", comment: "Yorum", read_only: "Salt okunur",
        browseable: "Taranabilir", guest_access: "Misafir erişimi", language: "Dil",
        running: "Çalışıyor", stopped: "Durduruldu", operation_success: "Başarılı",
        operation_failed: "Başarısız", confirm_delete: "Silmeyi onayla", no_data: "Veri yok",
        create_volume: "Volume oluştur", create_user: "Kullanıcı oluştur", create_share: "Paylaşım oluştur",
        operation: "İşlem", yes: "Evet", no: "Hayır", system_info: "Sistem bilgisi",
        service_status: "Servis durumu", ip_address: "IP adresi", push_targets: "Push hedefleri",
        push_files: "Push dosyaları", local_folder: "Yerel klasör", target_device: "Hedef cihaz",
        add_target: "Hedef ekle", target_name: "Hedef adı", target_ip: "Hedef IP",
        target_port: "Hedef port", push_folder: "Push klasörü", select_folder: "Klasör seç",
        push_now: "Şimdi push", pushing: "Pushing", push_history: "Push geçmişi",
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
        quota: "Quota", used: "ใช้แล้ว", available: "พร้อมใช้", username: "ชื่อผู้ใช้",
        password: "รหัสผ่าน", admin: "Admin", storage_quota: "Quota จัดเก็บ",
        home_directory: "โฮมไดเรกทอรี", smb_status: "สถานะ SMB", smb_shares: "SMB Shares",
        share_name: "ชื่อแชร์", comment: "ความคิดเห็น", read_only: "อ่านอย่างเดียว",
        browseable: "เรียกดูได้", guest_access: "Guest Access", language: "ภาษา",
        running: "กำลังทำงาน", stopped: "หยุด", operation_success: "สำเร็จ",
        operation_failed: "ล้มเหลว", confirm_delete: "ยืนยันการลบ", no_data: "ไม่มีข้อมูล",
        create_volume: "สร้าง Volume", create_user: "สร้างผู้ใช้", create_share: "สร้างแชร์",
        operation: "การดำเนินการ", yes: "ใช่", no: "ไม่", system_info: "ข้อมูลระบบ",
        service_status: "สถานะบริการ", ip_address: "IP Address", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "โฟลเดอร์ท้องถิ่น", target_device: "Target Device",
        add_target: "เพิ่ม Target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
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
        quota: "Quota", used: "Đã dùng", available: "Khả dụng", username: "Tên người dùng",
        password: "Mật khẩu", admin: "Admin", storage_quota: "Quota lưu trữ",
        home_directory: "Thư mục home", smb_status: "Trạng thái SMB", smb_shares: "SMB Shares",
        share_name: "Tên chia sẻ", comment: "Ghi chú", read_only: "Chỉ đọc",
        browseable: "Có thể duyệt", guest_access: "Guest Access", language: "Ngôn ngữ",
        running: "Chạy", stopped: "Dừng", operation_success: "Thành công",
        operation_failed: "Thất bại", confirm_delete: "Xác nhận xóa", no_data: "Không có dữ liệu",
        create_volume: "Tạo Volume", create_user: "Tạo người dùng", create_share: "Tạo chia sẻ",
        operation: "Thao tác", yes: "Có", no: "Không", system_info: "Thông tin hệ thống",
        service_status: "Trạng thái dịch vụ", ip_address: "Địa chỉ IP", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Thư mục cục bộ", target_device: "Target Device",
        add_target: "Thêm Target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
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
        quota: "Quota", used: "Digunakan", available: "Tersedia", username: "Nama pengguna",
        password: "Password", admin: "Admin", storage_quota: "Quota storage",
        home_directory: "Direktori home", smb_status: "Status SMB", smb_shares: "SMB Shares",
        share_name: "Nama share", comment: "Komentar", read_only: "Read only",
        browseable: "Browseable", guest_access: "Guest Access", language: "Bahasa",
        running: "Berjalan", stopped: "Berhenti", operation_success: "Sukses",
        operation_failed: "Gagal", confirm_delete: "Konfirmasi hapus", no_data: "Tidak ada data",
        create_volume: "Buat Volume", create_user: "Buat pengguna", create_share: "Buat share",
        operation: "Operasi", yes: "Ya", no: "Tidak", system_info: "Info sistem",
        service_status: "Status layanan", ip_address: "Alamat IP", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Folder lokal", target_device: "Target Device",
        add_target: "Tambah Target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
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
        quota: "Quota", used: "Gebruikt", available: "Beschikbaar", username: "Gebruikersnaam",
        password: "Wachtwoord", admin: "Admin", storage_quota: "Opslag quota",
        home_directory: "Home directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
        share_name: "Share naam", comment: "Commentaar", read_only: "Read only",
        browseable: "Browseable", guest_access: "Guest Access", language: "Taal",
        running: "Running", stopped: "Gestopt", operation_success: "Succes",
        operation_failed: "Mislukt", confirm_delete: "Bevestig verwijdering", no_data: "Geen data",
        create_volume: "Creëer Volume", create_user: "Creëer gebruiker", create_share: "Creëer share",
        operation: "Actie", yes: "Ja", no: "Nee", system_info: "Systeem info",
        service_status: "Service status", ip_address: "IP adres", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Lokale folder", target_device: "Target Device",
        add_target: "Target toevoegen", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Select Folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
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
        quota: "Quota", used: "Używane", available: "Dostępne", username: "Nazwa użytkownika",
        password: "Hasło", admin: "Admin", storage_quota: "Quota przechowywania",
        home_directory: "Katalog domowy", smb_status: "Status SMB", smb_shares: "SMB Shares",
        share_name: "Nazwa share", comment: "Komentarz", read_only: "Read only",
        browseable: "Browseable", guest_access: "Guest Access", language: "Język",
        running: "Uruchomiony", stopped: "Zatrzymany", operation_success: "Sukces",
        operation_failed: "Błąd", confirm_delete: "Potwierdź usunięcie", no_data: "Brak danych",
        create_volume: "Utwórz Volume", create_user: "Utwórz użytkownika", create_share: "Utwórz share",
        operation: "Operacja", yes: "Tak", no: "Nie", system_info: "Info systemowe",
        service_status: "Status serwisu", ip_address: "Adres IP", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Folder lokalny", target_device: "Target Device",
        add_target: "Dodaj target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Wybierz folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Skanuj IP", local_ips: "Lokalne IPs", scan: "Skanuj",
        found_devices: "Znalezione urządzenia", online: "Online", offline: "Offline",
        send: "Wyślij", receive: "Odbierz", push_status: "Status Push",
        success: "Sukces", failed: "Błąd", progress: "Progress",
        file_count: "Liczba plików", total_size: "Całkowity rozmiar"
    },
    sv_SE: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Lagring",
        users: "Användare", shares: "Shares", push: "Push Manager",
        settings: "Inställningar", volumes: "Volumes", create: "Skapa", delete: "Ta bort",
        edit: "Redigera", save: "Spara", cancel: "Avbryt", name: "Namn", path: "Sökväg",
        quota: "Quota", used: "Använd", available: "Tillgänglig", username: "Användarnamn",
        password: "Lösenord", admin: "Admin", storage_quota: "Lagrings quota",
        home_directory: "Hem directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
        share_name: "Share namn", comment: "Kommentar", read_only: "Read only",
        browseable: "Browseable", guest_access: "Guest Access", language: "Språk",
        running: "Körs", stopped: "Stoppad", operation_success: "Succé",
        operation_failed: "Misslyckades", confirm_delete: "Bekräfta borttagning", no_data: "Ingen data",
        create_volume: "Skapa Volume", create_user: "Skapa användare", create_share: "Skapa share",
        operation: "Åtgärd", yes: "Ja", no: "Nej", system_info: "Systeminfo",
        service_status: "Service status", ip_address: "IP adress", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Lokal folder", target_device: "Target Device",
        add_target: "Lägg till target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Välj folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Scanna IP", local_ips: "Lokala IPs", scan: "Scanna",
        found_devices: "Hittade enheter", online: "Online", offline: "Offline",
        send: "Skicka", receive: "Ta emot", push_status: "Push Status",
        success: "Succé", failed: "Misslyckades", progress: "Progress",
        file_count: "Filantal", total_size: "Total storlek"
    },
    da_DK: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Lagring",
        users: "Brugere", shares: "Shares", push: "Push Manager",
        settings: "Indstillinger", volumes: "Volumes", create: "Opret", delete: "Slet",
        edit: "Rediger", save: "Gem", cancel: "Annuller", name: "Navn", path: "Sti",
        quota: "Quota", used: "Brugt", available: "Tilgængelig", username: "Brugernavn",
        password: "Adgangskode", admin: "Admin", storage_quota: "Lagrings quota",
        home_directory: "Hjem directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
        share_name: "Share navn", comment: "Kommentar", read_only: "Read only",
        browseable: "Browseable", guest_access: "Guest Access", language: "Sprog",
        running: "Kører", stopped: "Stoppet", operation_success: "Succes",
        operation_failed: "Fejl", confirm_delete: "Bekræft sletning", no_data: "Ingen data",
        create_volume: "Opret Volume", create_user: "Opret bruger", create_share: "Opret share",
        operation: "Handling", yes: "Ja", no: "Nej", system_info: "Systeminfo",
        service_status: "Service status", ip_address: "IP adresse", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Lokal folder", target_device: "Target Device",
        add_target: "Tilføj target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Vælg folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Scan IP", local_ips: "Lokale IPs", scan: "Scan",
        found_devices: "Fundet enheder", online: "Online", offline: "Offline",
        send: "Send", receive: "Modtag", push_status: "Push Status",
        success: "Succes", failed: "Fejl", progress: "Progress",
        file_count: "Fil antal", total_size: "Total størrelse"
    },
    fi_FI: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Tallennus",
        users: "Käyttäjät", shares: "Shares", push: "Push Manager",
        settings: "Asetukset", volumes: "Volumes", create: "Luo", delete: "Poista",
        edit: "Muokkaa", save: "Tallenna", cancel: "Peruuta", name: "Nimi", path: "Polku",
        quota: "Quota", used: "Käytetty", available: "Saatavilla", username: "Käyttäjänimi",
        password: "Salasana", admin: "Admin", storage_quota: "Tallennus quota",
        home_directory: "Home directory", smb_status: "SMB Status", smb_shares: "SMB Shares",
        share_name: "Share nimi", comment: "Kommentti", read_only: "Read only",
        browseable: "Browseable", guest_access: "Guest Access", language: "Kieli",
        running: "Käynnissä", stopped: "Pysäytetty", operation_success: "Onnistui",
        operation_failed: "Epäonnistui", confirm_delete: "Vahvista poisto", no_data: "Ei dataa",
        create_volume: "Luo Volume", create_user: "Luo käyttäjä", create_share: "Luo share",
        operation: "Toiminto", yes: "Kyllä", no: "Ei", system_info: "Järjestelmäinfo",
        service_status: "Palvelun status", ip_address: "IP osoite", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Paikallinen folder", target_device: "Target Device",
        add_target: "Lisää target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Valitse folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Scan IP", local_ips: "Paikalliset IPs", scan: "Scan",
        found_devices: "Löydetyt laitteet", online: "Online", offline: "Offline",
        send: "Lähetä", receive: "Vastaanota", push_status: "Push Status",
        success: "Onnistui", failed: "Epäonnistui", progress: "Progress",
        file_count: "Tiedostojen määrä", total_size: "Yhteensä koko"
    },
    he_IL: {
        app_name: "Xiaosi Super NAS", dashboard: "לוח בקרה", storage: "אחסון",
        users: "משתמשים", shares: "שיתופים", push: "Push Manager",
        settings: "הגדרות", volumes: "Volumes", create: "צור", delete: "מחק",
        edit: "ערוך", save: "שמור", cancel: "בטל", name: "שם", path: "נתיב",
        quota: "Quota", used: "בשימוש", available: "זמין", username: "שם משתמש",
        password: "סיסמה", admin: "Admin", storage_quota: "Quota אחסון",
        home_directory: "ספריית home", smb_status: "סטטוס SMB", smb_shares: "שיתופי SMB",
        share_name: "שם שיתוף", comment: "הערה", read_only: "קריאה בלבד",
        browseable: "ניתן לעיון", guest_access: "גישת אורח", language: "שפה",
        running: "פועל", stopped: "עצור", operation_success: "הצלחה",
        operation_failed: "כשל", confirm_delete: "אשר מחיקה", no_data: "אין נתונים",
        create_volume: "צור Volume", create_user: "צור משתמש", create_share: "צור שיתוף",
        operation: "פעולה", yes: "כן", no: "לא", system_info: "מידע מערכת",
        service_status: "סטטוס שירות", ip_address: "כתובת IP", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "תיקייה מקומית", target_device: "Target Device",
        add_target: "הוסף Target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "בחר תיקייה",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Scan IP", local_ips: "IPs מקומיים", scan: "Scan",
        found_devices: "Found Devices", online: "Online", offline: "Offline",
        send: "שלח", receive: "קבל", push_status: "Push Status",
        success: "הצלחה", failed: "כשל", progress: "Progress",
        file_count: "ספירת קבצים", total_size: "גודל כולל"
    },
    hu_HU: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Tárolás",
        users: "Felhasználók", shares: "Megosztások", push: "Push Manager",
        settings: "Beállítások", volumes: "Volumes", create: "Létrehoz", delete: "Töröl",
        edit: "Szerkeszt", save: "Mentés", cancel: "Mégse", name: "Név", path: "Útvonal",
        quota: "Quota", used: "Használt", available: "Elérhető", username: "Felhasználónév",
        password: "Jelszó", admin: "Admin", storage_quota: "Tárolási quota",
        home_directory: "Home könyvtár", smb_status: "SMB Státusz", smb_shares: "SMB Megosztások",
        share_name: "Megosztás neve", comment: "Megjegyzés", read_only: "Read only",
        browseable: "Böngészhető", guest_access: "Guest Access", language: "Nyelv",
        running: "Fut", stopped: "Megállítva", operation_success: "Siker",
        operation_failed: "Hiba", confirm_delete: "Törlés megerősítése", no_data: "Nincs adat",
        create_volume: "Volume létrehozása", create_user: "Felhasználó létrehozása", create_share: "Megosztás létrehozása",
        operation: "Művelet", yes: "Igen", no: "Nem", system_info: "Rendszer info",
        service_status: "Szolgáltatás státusz", ip_address: "IP cím", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Helyi mappa", target_device: "Target Device",
        add_target: "Target hozzáadása", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Válassz mappát",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "IP Scan", local_ips: "Helyi IPs", scan: "Scan",
        found_devices: "Talált eszközök", online: "Online", offline: "Offline",
        send: "Küldés", receive: "Fogadás", push_status: "Push Státusz",
        success: "Siker", failed: "Hiba", progress: "Progress",
        file_count: "Fájlok száma", total_size: "Teljes méret"
    },
    cs_CZ: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Úložiště",
        users: "Uživatelé", shares: "Sdílení", push: "Push Manager",
        settings: "Nastavení", volumes: "Volumes", create: "Vytvořit", delete: "Smazat",
        edit: "Upravit", save: "Uložit", cancel: "Zrušit", name: "Název", path: "Cesta",
        quota: "Quota", used: "Použito", available: "Dostupné", username: "Uživatelské jméno",
        password: "Heslo", admin: "Admin", storage_quota: "Quota úložiště",
        home_directory: "Home adresář", smb_status: "SMB Status", smb_shares: "SMB Sdílení",
        share_name: "Název sdílení", comment: "Komentář", read_only: "Read only",
        browseable: "Prohlížitelné", guest_access: "Guest Access", language: "Jazyk",
        running: "Běží", stopped: "Zastaveno", operation_success: "Úspěch",
        operation_failed: "Chyba", confirm_delete: "Potvrdit smazání", no_data: "Žádné data",
        create_volume: "Vytvořit Volume", create_user: "Vytvořit uživatele", create_share: "Vytvořit sdílení",
        operation: "Operace", yes: "Ano", no: "Ne", system_info: "Systém info",
        service_status: "Status služby", ip_address: "IP adresa", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Místní složka", target_device: "Target Device",
        add_target: "Přidat target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Vybrat složku",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Scan IP", local_ips: "Místní IPs", scan: "Scan",
        found_devices: "Nalezené zařízení", online: "Online", offline: "Offline",
        send: "Odeslat", receive: "Přijmout", push_status: "Push Status",
        success: "Úspěch", failed: "Chyba", progress: "Progress",
        file_count: "Počet souborů", total_size: "Celková velikost"
    },
    uk_UA: {
        app_name: "Xiaosi Super NAS", dashboard: "Панель", storage: "Сховище",
        users: "Користувачі", shares: "Спільні ресурси", push: "Push Manager",
        settings: "Налаштування", volumes: "Volumes", create: "Створити", delete: "Видалити",
        edit: "Редагувати", save: "Зберегти", cancel: "Скасувати", name: "Назва", path: "Шлях",
        quota: "Quota", used: "Використано", available: "Доступно", username: "Ім'я користувача",
        password: "Пароль", admin: "Admin", storage_quota: "Quota сховища",
        home_directory: "Домашній каталог", smb_status: "Статус SMB", smb_shares: "SMB Shares",
        share_name: "Назва ресурсу", comment: "Коментар", read_only: "Read only",
        browseable: "Перегляд", guest_access: "Guest Access", language: "Мова",
        running: "Запущено", stopped: "Зупинено", operation_success: "Успіх",
        operation_failed: "Помилка", confirm_delete: "Підтвердити видалення", no_data: "Немає даних",
        create_volume: "Створити Volume", create_user: "Створити користувача", create_share: "Створити ресурс",
        operation: "Дія", yes: "Так", no: "Ні", system_info: "Системна інформація",
        service_status: "Статус сервісу", ip_address: "IP адреса", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Місцева папка", target_device: "Target Device",
        add_target: "Додати target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Вибрати папку",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Scan IP", local_ips: "Місцеві IPs", scan: "Scan",
        found_devices: "Знайдені пристрої", online: "Online", offline: "Offline",
        send: "Надіслати", receive: "Отримати", push_status: "Push Status",
        success: "Успіх", failed: "Помилка", progress: "Progress",
        file_count: "Кількість файлів", total_size: "Загальний розмір"
    },
    ro_RO: {
        app_name: "Xiaosi Super NAS", dashboard: "Dashboard", storage: "Stocare",
        users: "Utilizatori", shares: "Partajări", push: "Push Manager",
        settings: "Setări", volumes: "Volumes", create: "Creează", delete: "Șterge",
        edit: "Editează", save: "Salvează", cancel: "Anulează", name: "Nume", path: "Cale",
        quota: "Quota", used: "Utilizat", available: "Disponibil", username: "Nume utilizator",
        password: "Parolă", admin: "Admin", storage_quota: "Quota stocare",
        home_directory: "Director home", smb_status: "Status SMB", smb_shares: "Partajări SMB",
        share_name: "Nume partajare", comment: "Comentariu", read_only: "Read only",
        browseable: "Navigabil", guest_access: "Acces guest", language: "Limbă",
        running: "Rulează", stopped: "Oprit", operation_success: "Succes",
        operation_failed: "Eroare", confirm_delete: "Confirmă ștergerea", no_data: "Nu există date",
        create_volume: "Creează Volume", create_user: "Creează utilizator", create_share: "Creează partajare",
        operation: "Operație", yes: "Da", no: "Nu", system_info: "Info sistem",
        service_status: "Status serviciu", ip_address: "Adresă IP", push_targets: "Push Targets",
        push_files: "Push Files", local_folder: "Folder local", target_device: "Target Device",
        add_target: "Adaugă target", target_name: "Target Name", target_ip: "Target IP",
        target_port: "Target Port", push_folder: "Push Folder", select_folder: "Selectează folder",
        push_now: "Push Now", pushing: "Pushing", push_history: "Push History",
        scan_ip: "Scan IP", local_ips: "IPs locale", scan: "Scan",
        found_devices: "Device-uri găsite", online: "Online", offline: "Offline",
        send: "Trimite", receive: "Primește", push_status: "Push Status",
        success: "Succes", failed: "Eroare", progress: "Progress",
        file_count: "Număr fișiere", total_size: "Dimensiune totală"
    }
};

const LANG_NAMES = {
    zh_CN: "简体中文", zh_TW: "繁體中文", en_US: "English (US)", en_GB: "English (UK)",
    ja_JP: "日本語", ko_KR: "한국어", fr_FR: "Français", de_DE: "Deutsch",
    es_ES: "Español", it_IT: "Italiano", pt_BR: "Português (BR)", ru_RU: "Русский",
    ar_SA: "العربية", hi_IN: "हिन्दी", tr_TR: "Türkçe", th_TH: "ไทย",
    vi_VN: "Tiếng Việt", id_ID: "Bahasa Indonesia", nl_NL: "Nederlands", pl_PL: "Polski",
    sv_SE: "Svenska", da_DK: "Dansk", fi_FI: "Suomi", he_IL: "עברית",
    hu_HU: "Magyar", cs_CZ: "Čeština", uk_UA: "Українська", ro_RO: "Română"
};

// ==========================================
// 配置管理
// ==========================================
const configPath = path.join(__dirname, '..', 'config', 'config.json');
const dataDir = path.join(__dirname, '..', 'nas_data');
const receiveDir = path.join(dataDir, 'received');

let config = {
    volumes: [],
    users: [],
    shares: [],
    push_targets: [],
    server: { port: PORT, language: 'zh_CN' }
};

function loadConfig() {
    try {
        if (fs.existsSync(configPath)) {
            const data = fs.readFileSync(configPath, 'utf8');
            const parsed = JSON.parse(data);
            config.server = parsed.server || config.server;
            config.volumes = parsed.storage?.volumes || [];
            config.users = parsed.users || [];
            config.shares = parsed.smb?.shares || [];
            config.push_targets = parsed.push?.targets || [];
        }
    } catch (e) {
        console.log('Config load error:', e.message);
    }
    // 确保接收目录存在
    if (!fs.existsSync(receiveDir)) {
        fs.mkdirSync(receiveDir, { recursive: true });
    }
}

function saveConfig() {
    const data = {
        server: config.server,
        storage: { volumes: config.volumes },
        users: config.users,
        smb: { shares: config.shares },
        push: { targets: config.push_targets }
    };
    fs.writeFileSync(configPath, JSON.stringify(data, null, 2), 'utf8');
}

// ==========================================
// 数据管理
// ==========================================
let pushHistory = [];
let activePush = null;
let deviceId = null;

// 获取设备唯一ID
function getDeviceId() {
    if (!deviceId) {
        deviceId = `${os.hostname()}-${crypto.randomBytes(3).toString('hex')}`;
    }
    return deviceId;
}

// 获取本机IP地址
function getLocalIPs() {
    const ips = [];
    const interfaces = os.networkInterfaces();

    // 获取默认出口IP
    try {
        const socket = require('dgram').createSocket('udp4');
        socket.connect(80, '8.8.8.8', () => {
            const wanIp = socket.address().address;
            socket.close();
            if (wanIp && wanIp !== '127.0.0.1') {
                ips.push({
                    ip: wanIp,
                    type: 'wan',
                    name: `${os.hostname()} (出口)`,
                    adapter: '默认路由',
                    network: getNetworkType(wanIp),
                    device_id: getDeviceId()
                });
            }
        });
        socket.on('error', () => socket.close());
    } catch (e) { }

    // 获取所有网卡IP
    for (const [name, addrs] of Object.entries(interfaces)) {
        for (const addr of addrs) {
            if (addr.family === 'IPv4' && !addr.internal) {
                const ipStr = addr.address;
                if (!ips.some(i => i.ip === ipStr)) {
                    ips.push({
                        ip: ipStr,
                        type: 'lan',
                        name: name,
                        adapter: name,
                        network: getNetworkType(ipStr),
                        device_id: getDeviceId()
                    });
                }
            }
        }
    }

    if (ips.length === 0) {
        ips.push({
            ip: '127.0.0.1',
            type: 'loopback',
            name: 'localhost',
            adapter: 'loopback',
            network: 'Loopback',
            device_id: getDeviceId()
        });
    }

    return ips;
}

function getNetworkType(ip) {
    if (ip.startsWith('192.168.')) return 'LAN (私有)';
    if (ip.startsWith('10.')) return 'LAN (私有)';
    if (ip.startsWith('172.')) {
        const second = parseInt(ip.split('.')[1]);
        if (second >= 16 && second <= 31) return 'LAN (私有)';
    }
    if (ip.startsWith('127.')) return 'Loopback';
    return 'Public/WAN';
}

// ==========================================
// 用户管理
// ==========================================
function hashPassword(password) {
    return crypto.createHash('sha256').update(password).digest('hex');
}

function ensureAdminUser() {
    if (!config.users.some(u => u.username === 'admin')) {
        config.users.push({
            username: 'admin',
            password: hashPassword('admin'),
            is_admin: true,
            home_dir: '/mnt/data/admin',
            storage_quota_gb: 100
        });
        saveConfig();
    }
}

// ==========================================
// 推送功能
// ==========================================
async function scanLAN(port = PORT, timeout = 500) {
    const found = [];
    const localIPs = getLocalIPs();
    const localIPSet = new Set(localIPs.map(i => i.ip));

    // 收集私有IP段
    const prefixes = new Set();
    for (const ipInfo of localIPs) {
        const ip = ipInfo.ip;
        if (ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.')) {
            const parts = ip.split('.');
            if (parts.length === 4) {
                prefixes.add(`${parts[0]}.${parts[1]}.${parts[2]}`);
            }
        }
    }

    if (prefixes.size === 0) return found;

    // 扫描
    for (const prefix of prefixes) {
        for (let i = 1; i < 255; i++) {
            const ipStr = `${prefix}.${i}`;
            if (localIPSet.has(ipStr)) continue;

            try {
                const socket = new (require('net').Socket)();
                socket.setTimeout(timeout);

                await new Promise((resolve) => {
                    socket.connect(port, ipStr, () => {
                        socket.destroy();
                        found.push({
                            ip: ipStr,
                            port: port,
                            network: prefix,
                            status: 'online',
                            device_id: null,
                            is_self: false
                        });
                        resolve();
                    });
                    socket.on('error', () => {
                        socket.destroy();
                        resolve();
                    });
                    socket.on('timeout', () => {
                        socket.destroy();
                        resolve();
                    });
                });
            } catch (e) { }
        }
    }

    return found;
}

async function pushFolder(targetId, folderPath) {
    const target = config.push_targets.find(t => t.id === targetId);
    if (!target) return { success: false, message: 'Target not found' };
    if (!fs.existsSync(folderPath)) return { success: false, message: 'Folder not found' };

    folderPath = path.resolve(folderPath);
    const folderName = path.basename(folderPath);

    // 收集所有文件
    const allFiles = [];
    let totalSize = 0;

    const walkDir = (dir) => {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
            const fullPath = path.join(dir, entry.name);
            if (entry.isDirectory()) {
                walkDir(fullPath);
            } else {
                const stat = fs.statSync(fullPath);
                const relPath = path.relative(folderPath, fullPath);
                allFiles.push({ relPath, fullPath, size: stat.size });
                totalSize += stat.size;
            }
        }
    };

    walkDir(folderPath);

    activePush = {
        id: crypto.randomBytes(4).toString('hex'),
        target: target.name,
        folder: folderName,
        total_files: allFiles.length,
        total_size: totalSize,
        sent_files: 0,
        sent_size: 0,
        status: 'pushing'
    };

    // 发送文件
    for (const file of allFiles) {
        try {
            const fileData = fs.readFileSync(file.fullPath);
            const builder = new FormDataBuilder();
            builder.addField('folder', folderName);
            builder.addField('filepath', file.relPath);
            builder.addFile('file', path.basename(file.fullPath), fileData);

            const body = builder.build();

            const options = {
                hostname: target.ip,
                port: target.port,
                path: '/api/push/receive',
                method: 'POST',
                headers: {
                    'Content-Type': builder.getContentType(),
                    'Content-Length': body.length
                }
            };

            await new Promise((resolve, reject) => {
                const req = http.request(options, (res) => {
                    res.on('data', () => {});
                    res.on('end', resolve);
                });
                req.on('error', reject);
                req.write(body);
                req.end();
            });

            activePush.sent_files++;
            activePush.sent_size += file.size;
        } catch (e) {
            console.error(`Failed to push ${file.relPath}:`, e.message);
        }
    }

    activePush.status = 'success';
    pushHistory.push({
        ...activePush,
        time: new Date().toLocaleString('zh-CN')
    });

    const result = { ...activePush };
    activePush = null;
    return { success: true, message: 'Push complete', result };
}

function receiveFile(folderName, filepath, fileData) {
    const targetDir = path.join(receiveDir, folderName);
    const fullPath = path.join(targetDir, filepath);

    fs.mkdirSync(path.dirname(fullPath), { recursive: true });
    fs.writeFileSync(fullPath, fileData);

    return { success: true, size: fileData.length };
}

// ==========================================
// Express中间件
// ==========================================
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// CORS支持
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type');
    if (req.method === 'OPTIONS') return res.sendStatus(200);
    next();
});

// ==========================================
// API路由
// ==========================================

// 多语言
app.get('/api/i18n/', (req, res) => {
    const lang = req.query.lang || 'zh_CN';
    const trans = TRANSLATIONS[lang] || TRANSLATIONS['zh_CN'];
    res.json(trans);
});

// 存储管理
app.get('/api/storage/volumes', (req, res) => {
    res.json({ volumes: config.volumes });
});

app.post('/api/storage/volumes', (req, res) => {
    const { name, path: volPath, quota_gb } = req.body;
    if (config.volumes.some(v => v.name === name)) {
        return res.status(400).json({ message: 'Volume exists' });
    }
    config.volumes.push({ name, path: volPath, quota_gb });
    saveConfig();
    res.status(201).json({ message: 'Created' });
});

app.post('/api/storage/volumes/delete', (req, res) => {
    const { name } = req.body;
    config.volumes = config.volumes.filter(v => v.name !== name);
    saveConfig();
    res.json({ message: 'Deleted' });
});

// 用户管理
app.get('/api/users', (req, res) => {
    const users = config.users.map(u => ({
        username: u.username,
        is_admin: u.is_admin,
        home_dir: u.home_dir,
        storage_quota_gb: u.storage_quota_gb
    }));
    res.json({ users });
});

app.post('/api/users', (req, res) => {
    const { username, password, is_admin } = req.body;
    if (config.users.some(u => u.username === username)) {
        return res.status(400).json({ message: 'User exists' });
    }
    config.users.push({
        username,
        password: hashPassword(password),
        is_admin: is_admin || false,
        home_dir: `/mnt/data/${username}`,
        storage_quota_gb: 100
    });
    saveConfig();
    res.status(201).json({ message: 'Created' });
});

app.post('/api/users/delete', (req, res) => {
    const { username } = req.body;
    if (username === 'admin') {
        return res.status(400).json({ message: 'Cannot delete admin' });
    }
    config.users = config.users.filter(u => u.username !== username);
    saveConfig();
    res.json({ message: 'Deleted' });
});

// SMB管理
app.get('/api/smb/status', (req, res) => {
    res.json({ running: true, port: 445, workgroup: 'WORKGROUP' });
});

app.get('/api/smb/shares', (req, res) => {
    res.json({ shares: config.shares });
});

app.post('/api/smb/shares', (req, res) => {
    const { name, path: sharePath } = req.body;
    if (config.shares.some(s => s.name === name)) {
        return res.status(400).json({ message: 'Share exists' });
    }
    config.shares.push({
        name, path: sharePath, comment: '', read_only: false,
        browseable: true, guest_access: false
    });
    saveConfig();
    res.status(201).json({ message: 'Created' });
});

app.post('/api/smb/shares/delete', (req, res) => {
    const { name } = req.body;
    config.shares = config.shares.filter(s => s.name !== name);
    saveConfig();
    res.json({ message: 'Deleted' });
});

// IP管理
app.get('/api/ip/local', (req, res) => {
    res.json({ ips: getLocalIPs() });
});

app.get('/api/ip/scan', async (req, res) => {
    const port = parseInt(req.query.port) || PORT;
    const devices = await scanLAN(port);
    res.json({ devices });
});

// 推送管理
app.get('/api/push/targets', (req, res) => {
    res.json({ targets: config.push_targets });
});

app.post('/api/push/targets', (req, res) => {
    const { name, ip, port } = req.body;
    if (config.push_targets.some(t => t.ip === ip && t.port === port)) {
        return res.status(400).json({ message: 'Target exists' });
    }
    config.push_targets.push({
        id: crypto.randomBytes(4).toString('hex'),
        name, ip, port: port || PORT,
        status: 'unknown'
    });
    saveConfig();
    res.status(201).json({ message: 'Added' });
});

app.post('/api/push/targets/delete', (req, res) => {
    const { id } = req.body;
    config.push_targets = config.push_targets.filter(t => t.id !== id);
    saveConfig();
    res.json({ message: 'Deleted' });
});

app.post('/api/push/targets/check', (req, res) => {
    const { id } = req.body;
    const target = config.push_targets.find(t => t.id === id);
    if (!target) {
        return res.status(400).json({ success: false, status: 'Not found' });
    }

    const socket = new (require('net').Socket)();
    socket.setTimeout(2000);

    socket.connect(target.port, target.ip, () => {
        target.status = 'online';
        socket.destroy();
        res.json({ success: true, status: 'online' });
    });

    socket.on('error', () => {
        target.status = 'offline';
        res.json({ success: false, status: 'offline' });
    });

    socket.on('timeout', () => {
        target.status = 'offline';
        socket.destroy();
        res.json({ success: false, status: 'timeout' });
    });
});

app.post('/api/push/folder', async (req, res) => {
    const { target_id, folder_path } = req.body;

    // 异步推送
    pushFolder(target_id, folder_path).catch(e => {
        activePush = { ...activePush, status: 'failed', error: e.message };
        pushHistory.push({ ...activePush, time: new Date().toLocaleString('zh-CN') });
        activePush = null;
    });

    res.json({ message: 'Push started' });
});

app.get('/api/push/status', (req, res) => {
    res.json({
        active: activePush,
        history: pushHistory.slice(-20)
    });
});

// 接收推送
app.post('/api/push/receive', (req, res) => {
    const contentType = req.headers['content-type'];
    if (!contentType.includes('multipart/form-data')) {
        return res.status(400).json({ success: false, error: 'Invalid content type' });
    }

    const boundary = contentType.split('boundary=')[1];
    const chunks = [];

    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => {
        try {
            const body = Buffer.concat(chunks);
            const parsed = FormDataParser.parse(body, boundary);

            if (parsed.files.length > 0) {
                const file = parsed.files[0];
                const folder = parsed.fields.folder || 'upload';
                const filepath = parsed.fields.filepath || file.filename;

                receiveFile(folder, filepath, file.data);
                res.json({ success: true, size: file.data.length });
            } else {
                res.json({ success: true, message: 'No file data' });
            }
        } catch (e) {
            res.status(500).json({ success: false, error: e.message });
        }
    });
});

// ==========================================
// Web前端
// ==========================================
const INDEX_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小思超级NAS - 管理控制台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; }
        .lang-select { padding: 8px 12px; border-radius: 6px; border: none; cursor: pointer; }
        .container { display: flex; min-height: calc(100vh - 80px); }
        .sidebar { width: 220px; background: white; padding: 20px 0; box-shadow: 2px 0 8px rgba(0,0,0,0.05); }
        .nav-item { padding: 15px 25px; cursor: pointer; transition: all 0.3s; border-left: 4px solid transparent; }
        .nav-item:hover, .nav-item.active { background: #f8f9ff; border-left-color: #667eea; color: #667eea; }
        .main { flex: 1; padding: 30px; }
        .card { background: white; border-radius: 12px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
        .card-title { font-size: 18px; font-weight: 600; margin-bottom: 20px; color: #333; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; }
        .stat-card h3 { font-size: 14px; opacity: 0.9; margin-bottom: 8px; }
        .stat-card .value { font-size: 28px; font-weight: 600; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9ff; font-weight: 600; color: #555; }
        tr:hover { background: #fafafa; }
        .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: all 0.3s; }
        .btn-primary { background: #667eea; color: white; }
        .btn-primary:hover { background: #5568d3; }
        .btn-danger { background: #f56565; color: white; }
        .btn-danger:hover { background: #e53e3e; }
        .btn-success { background: #48bb78; color: white; }
        .btn-success:hover { background: #38a169; }
        .btn-sm { padding: 6px 12px; font-size: 12px; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); justify-content: center; align-items: center; z-index: 1000; }
        .modal.show { display: flex; }
        .modal-content { background: white; padding: 30px; border-radius: 12px; min-width: 400px; max-width: 600px; max-height: 80vh; overflow-y: auto; }
        .modal-title { font-size: 20px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 6px; color: #666; font-size: 14px; }
        .form-group input, .form-group select { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
        .form-row { display: flex; gap: 12px; }
        .form-row .form-group { flex: 1; }
        .form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
        .badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; }
        .badge-success { background: #c6f6d5; color: #276749; }
        .badge-warning { background: #fefcbf; color: #975a16; }
        .badge-danger { background: #fed7d7; color: #c53030; }
        .page { display: none; }
        .page.active { display: block; }
        .ip-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
        .ip-item { background: #f8faff; padding: 12px 16px; border-radius: 8px; border: 1px solid #e2e8f0; border-left: 4px solid #667eea; }
        .ip-item .ip { font-family: 'Consolas', 'Monaco', monospace; font-weight: 600; color: #2d3748; font-size: 15px; }
        .ip-item .type { font-size: 12px; color: #718096; }
        .progress-bar { width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; }
        .progress-bar .fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s; }
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 768px) { .two-col { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <h1 id="app-title">小思超级NAS 管理控制台</h1>
        <select class="lang-select" id="langSelect"></select>
    </div>
    <div class="container">
        <div class="sidebar">
            <div class="nav-item active" data-page="dashboard" data-i18n="dashboard">控制台</div>
            <div class="nav-item" data-page="storage" data-i18n="storage">存储管理</div>
            <div class="nav-item" data-page="users" data-i18n="users">用户管理</div>
            <div class="nav-item" data-page="shares" data-i18n="shares">共享管理</div>
            <div class="nav-item" data-page="push" data-i18n="push">推送管理</div>
        </div>
        <div class="main">
            <div class="page active" id="page-dashboard">
                <div class="stats-grid">
                    <div class="stat-card"><h3 data-i18n="volumes">存储卷</h3><div class="value" id="stat-volumes">0</div></div>
                    <div class="stat-card"><h3 data-i18n="users">用户</h3><div class="value" id="stat-users">0</div></div>
                    <div class="stat-card"><h3 data-i18n="smb_shares">SMB共享</h3><div class="value" id="stat-shares">0</div></div>
                    <div class="stat-card"><h3 data-i18n="service_status">服务状态</h3><div class="value" id="stat-status">-</div></div>
                </div>
                <div class="card">
                    <div class="card-title" data-i18n="local_ips">本机IP地址</div>
                    <div class="ip-list" id="local-ips"></div>
                    <button class="btn btn-primary btn-sm" onclick="loadLocalIPs()" data-i18n="scan_ip">扫描IP</button>
                </div>
            </div>
            <div class="page" id="page-storage">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <div class="card-title" style="margin-bottom:0;" data-i18n="volumes">存储卷</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('storage')" data-i18n="create">创建</button>
                    </div>
                    <table><thead><tr><th data-i18n="name">名称</th><th data-i18n="path">路径</th><th data-i18n="quota">配额(GB)</th><th data-i18n="operation">操作</th></tr></thead><tbody id="volumes-table"></tbody></table>
                </div>
            </div>
            <div class="page" id="page-users">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <div class="card-title" style="margin-bottom:0;" data-i18n="users">用户</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('user')" data-i18n="create">创建</button>
                    </div>
                    <table><thead><tr><th data-i18n="username">用户名</th><th data-i18n="home_directory">主目录</th><th data-i18n="storage_quota">配额(GB)</th><th data-i18n="admin">管理员</th><th data-i18n="operation">操作</th></tr></thead><tbody id="users-table"></tbody></table>
                </div>
            </div>
            <div class="page" id="page-shares">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <div class="card-title" style="margin-bottom:0;" data-i18n="shares">共享</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('share')" data-i18n="create">创建</button>
                    </div>
                    <table><thead><tr><th data-i18n="share_name">共享名称</th><th data-i18n="path">路径</th><th data-i18n="operation">操作</th></tr></thead><tbody id="shares-table"></tbody></table>
                </div>
            </div>
            <div class="page" id="page-push">
                <div class="two-col">
                    <div class="card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                            <div class="card-title" style="margin-bottom:0;" data-i18n="push_targets">推送目标</div>
                            <button class="btn btn-primary btn-sm" onclick="showModal('target')" data-i18n="add_target">添加目标</button>
                        </div>
                        <table><thead><tr><th data-i18n="name">名称</th><th data-i18n="ip_address">IP</th><th data-i18n="operation">操作</th></tr></thead><tbody id="targets-table"></tbody></table>
                    </div>
                    <div class="card">
                        <div class="card-title" data-i18n="found_devices">发现设备</div>
                        <div id="scan-result" style="margin-bottom:15px;"><span style="color:#999;">点击扫描按钮发现局域网内的设备</span></div>
                        <button class="btn btn-success btn-sm" onclick="scanLAN()" data-i18n="scan">扫描局域网</button>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title" data-i18n="push_folder">推送文件夹</div>
                    <div class="form-group"><label data-i18n="target_device">目标设备</label><select id="push-target-select"><option value="">请选择目标设备</option></select></div>
                    <div class="form-group"><label data-i18n="local_folder">本地文件夹路径</label><input type="text" id="push-folder-path" placeholder="例如: C:\\Users\\Documents"></div>
                    <div class="form-group"><label data-i18n="progress">进度</label><div class="progress-bar"><div class="fill" id="push-progress" style="width:0%"></div></div><div id="push-status-text" style="margin-top:8px;font-size:13px;color:#666;">等待推送</div></div>
                    <button class="btn btn-primary" onclick="startPush()" id="push-btn" data-i18n="push_now">立即推送</button>
                </div>
                <div class="card">
                    <div class="card-title" data-i18n="push_history">推送历史</div>
                    <table><thead><tr><th>时间</th><th>目标</th><th>文件夹</th><th>文件数</th><th>状态</th></tr></thead><tbody id="push-history"></tbody></table>
                </div>
            </div>
        </div>
    </div>
    <div class="modal" id="modal-storage"><div class="modal-content"><div class="modal-title" data-i18n="create_volume">创建存储卷</div><div class="form-group"><label data-i18n="name">名称</label><input type="text" id="storage-name"></div><div class="form-group"><label data-i18n="path">路径</label><input type="text" id="storage-path"></div><div class="form-group"><label data-i18n="quota">配额(GB)</label><input type="number" id="storage-quota" value="100"></div><div class="form-actions"><button class="btn" onclick="closeModal('storage')" data-i18n="cancel">取消</button><button class="btn btn-primary" onclick="createVolume()" data-i18n="save">保存</button></div></div></div>
    <div class="modal" id="modal-user"><div class="modal-content"><div class="modal-title" data-i18n="create_user">创建用户</div><div class="form-group"><label data-i18n="username">用户名</label><input type="text" id="user-name"></div><div class="form-group"><label data-i18n="password">密码</label><input type="password" id="user-password"></div><div class="form-actions"><button class="btn" onclick="closeModal('user')" data-i18n="cancel">取消</button><button class="btn btn-primary" onclick="createUser()" data-i18n="save">保存</button></div></div></div>
    <div class="modal" id="modal-share"><div class="modal-content"><div class="modal-title" data-i18n="create_share">创建共享</div><div class="form-group"><label data-i18n="share_name">共享名称</label><input type="text" id="share-name"></div><div class="form-group"><label data-i18n="path">路径</label><input type="text" id="share-path"></div><div class="form-actions"><button class="btn" onclick="closeModal('share')" data-i18n="cancel">取消</button><button class="btn btn-primary" onclick="createShare()" data-i18n="save">保存</button></div></div></div>
    <div class="modal" id="modal-target"><div class="modal-content"><div class="modal-title" data-i18n="add_target">添加推送目标</div><div class="form-group"><label data-i18n="target_name">目标名称</label><input type="text" id="target-name"></div><div class="form-row"><div class="form-group"><label data-i18n="target_ip">目标IP</label><input type="text" id="target-ip"></div><div class="form-group"><label data-i18n="target_port">目标端口</label><input type="number" id="target-port" value="8081"></div></div><div class="form-actions"><button class="btn" onclick="closeModal('target')" data-i18n="cancel">取消</button><button class="btn btn-primary" onclick="addTarget()" data-i18n="save">保存</button></div></div></div>
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
    if (translations['app_name']) {
        document.getElementById('app-title').textContent = translations['app_name'] + ' - ' + (translations['dashboard'] || '管理控制台');
    }
}
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        item.classList.add('active');
        document.getElementById('page-' + item.dataset.page).classList.add('active');
        if (item.dataset.page === 'push') { loadPushTargets(); updatePushTargetSelect(); loadPushHistory(); }
        else if (item.dataset.page === 'dashboard') { loadLocalIPs(); }
        else if (item.dataset.page === 'storage') { loadVolumes(); }
        else if (item.dataset.page === 'users') { loadUsers(); }
        else if (item.dataset.page === 'shares') { loadShares(); }
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
        document.getElementById('stat-status').textContent = smb.running ? (translations['running'] || '运行中') : (translations['stopped'] || '已停止');
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
                const typeColor = ip.type === 'wan' ? '#48bb78' : (ip.type === 'lan' ? '#4299e1' : '#a0aec0');
                const typeLabel = ip.type === 'wan' ? '出口' : (ip.type === 'lan' ? '局域网' : '本地');
                div.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;width:100%;"><div><div class="ip" style="font-size:16px;">' + ip.ip + '</div><div style="font-size:12px;color:#666;margin-top:2px;">' + (ip.name || ip.adapter) + ' | ' + (ip.network || '') + '</div></div><div style="display:flex;align-items:center;gap:8px;"><span style="background:' + typeColor + ';color:white;padding:2px 8px;border-radius:10px;font-size:11px;">' + typeLabel + '</span><span style="font-size:11px;color:#999;">ID:' + (ip.device_id || 'N/A') + '</span></div></div>';
                container.appendChild(div);
            });
        }
    } catch (e) { console.error(e); }
}
async function scanLAN() {
    const resultDiv = document.getElementById('scan-result');
    resultDiv.innerHTML = '<span style="color:#667eea;">正在扫描局域网设备...</span>';
    try {
        const res = await fetch('/api/ip/scan?port=8081');
        const data = await res.json();
        if (data.devices && data.devices.length) {
            let html = '<div style="margin-bottom:10px;font-weight:600;">发现 ' + data.devices.length + ' 台设备:</div>';
            data.devices.forEach(d => {
                html += '<div class="ip-item" style="margin-bottom:8px;display:inline-flex;align-items:center;gap:10px;"><div><div class="ip">' + d.ip + ':' + d.port + '</div><div class="type">' + (translations['online'] || '在线') + '</div></div><button class="btn btn-primary btn-sm" onclick="quickAddTarget(\'' + d.ip + '\', ' + d.port + ')">' + (translations['add_target'] || '添加') + '</button></div>';
            });
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = '<span style="color:#999;">未发现其他NAS设备</span>';
        }
    } catch (e) {
        resultDiv.innerHTML = '<span style="color:#f56565;">扫描失败</span>';
    }
}
function quickAddTarget(ip, port) {
    document.getElementById('target-name').value = 'NAS-' + ip.split('.')[3];
    document.getElementById('target-ip').value = ip;
    document.getElementById('target-port').value = port;
    showModal('target');
}
async function loadVolumes() {
    const t = translations;
    const res = await fetch('/api/storage/volumes');
    const data = await res.json();
    const tb = document.getElementById('volumes-table');
    tb.innerHTML = data.volumes && data.volumes.length ?
        data.volumes.map(v => '<tr><td>' + v.name + '</td><td>' + v.path + '</td><td>' + v.quota_gb + '</td><td><button class="btn btn-danger btn-sm" onclick="deleteVolume(\'' + v.name + '\')">' + (t.delete || '删除') + '</button></td></tr>').join('') :
        '<tr><td colspan="4" style="text-align:center;color:#999;">' + (t.no_data || '暂无数据') + '</td></tr>';
}
async function loadUsers() {
    const t = translations;
    const res = await fetch('/api/users');
    const data = await res.json();
    const tb = document.getElementById('users-table');
    tb.innerHTML = data.users && data.users.length ?
        data.users.map(u => '<tr><td>' + u.username + '</td><td>' + u.home_dir + '</td><td>' + u.storage_quota_gb + '</td><td><span class="badge ' + (u.is_admin ? 'badge-success' : 'badge-warning') + '">' + (u.is_admin ? (t.yes || '是') : (t.no || '否')) + '</span></td><td><button class="btn btn-danger btn-sm" onclick="deleteUser(\'' + u.username + '\')">' + (t.delete || '删除') + '</button></td></tr>').join('') :
        '<tr><td colspan="5" style="text-align:center;color:#999;">' + (t.no_data || '暂无数据') + '</td></tr>';
}
async function loadShares() {
    const t = translations;
    const res = await fetch('/api/smb/shares');
    const data = await res.json();
    const tb = document.getElementById('shares-table');
    tb.innerHTML = data.shares && data.shares.length ?
        data.shares.map(s => '<tr><td>' + s.name + '</td><td>' + s.path + '</td><td><button class="btn btn-danger btn-sm" onclick="deleteShare(\'' + s.name + '\')">' + (t.delete || '删除') + '</button></td></tr>').join('') :
        '<tr><td colspan="3" style="text-align:center;color:#999;">' + (t.no_data || '暂无数据') + '</td></tr>';
}
async function loadPushTargets() {
    const t = translations;
    const res = await fetch('/api/push/targets');
    const data = await res.json();
    const tb = document.getElementById('targets-table');
    tb.innerHTML = data.targets && data.targets.length ?
        data.targets.map(t => '<tr><td>' + t.name + '</td><td>' + t.ip + ':' + t.port + '</td><td><button class="btn btn-success btn-sm" onclick="checkTarget(\'' + t.id + '\')">' + (translations['scan'] || '检测') + '</button> <button class="btn btn-danger btn-sm" onclick="deleteTarget(\'' + t.id + '\')">' + (translations['delete'] || '删除') + '</button></td></tr>').join('') :
        '<tr><td colspan="3" style="text-align:center;color:#999;">' + (translations['no_data'] || '暂无数据') + '</td></tr>';
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
    btn.textContent = translations['pushing'] || '推送中...';
    document.getElementById('push-progress').style.width = '5%';
    document.getElementById('push-status-text').textContent = '准备推送...';
    try {
        await fetch('/api/push/folder', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({target_id: targetId, folder_path: folderPath}) });
        pollPushStatus();
    } catch (e) {
        btn.disabled = false;
        btn.textContent = translations['push_now'] || '立即推送';
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
                document.getElementById('push-status-text').textContent = translations['success'] || '推送完成';
                const btn = document.getElementById('push-btn');
                btn.disabled = false;
                btn.textContent = translations['push_now'] || '立即推送';
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
    const t = translations;
    const res = await fetch('/api/push/status');
    const data = await res.json();
    const tb = document.getElementById('push-history');
    if (data.history && data.history.length) {
        tb.innerHTML = data.history.map(h => '<tr><td>' + (h.time || '') + '</td><td>' + h.target + '</td><td>' + h.folder + '</td><td>' + h.sent_files + ' / ' + h.total_files + '</td><td><span class="badge ' + (h.status === 'success' ? 'badge-success' : 'badge-danger') + '">' + (h.status === 'success' ? (t['success'] || '成功') : (t['failed'] || '失败')) + '</span></td></tr>').join('');
    } else {
        tb.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">' + (t['no_data'] || '暂无数据') + '</td></tr>';
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
</html>`;

app.get('/', (req, res) => {
    res.send(INDEX_HTML);
});

app.get('/index.html', (req, res) => {
    res.send(INDEX_HTML);
});

// ==========================================
// 启动服务
// ==========================================
function startServer() {
    loadConfig();
    ensureAdminUser();

    const localIPs = getLocalIPs();

    console.log('='.repeat(50));
    console.log('  小思超级NAS服务启动 (Node.js)');
    console.log('='.repeat(50));
    console.log(`  本地访问: http://localhost:${PORT}`);
    for (const ipInfo of localIPs) {
        if (ipInfo.type !== 'loopback') {
            console.log(`  网络访问: http://${ipInfo.ip}:${PORT}`);
        }
    }
    console.log(`  接收目录: ${receiveDir}`);
    console.log('='.repeat(50));
    console.log('  按 Ctrl+C 停止服务');
    console.log('='.repeat(50));

    app.listen(PORT, '0.0.0.0');
}

startServer();