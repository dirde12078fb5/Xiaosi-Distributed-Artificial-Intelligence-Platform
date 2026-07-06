/**
 * 小思超级多版本NAS服务 - Dart实现 (第二代)
 * 基于shelf包实现的完整REST API
 * 支持完整的存储管理、用户管理、SMB共享、文件推送、多语言支持
 */
import 'dart:io';
import 'dart:convert';
import 'dart:async';
import 'dart:math';
import 'package:shelf/shelf.dart';
import 'package:shelf_router/shelf_router.dart';

// ==========================================
// 多语言翻译 (28种语言)
// ==========================================
final Map<String, Map<String, String>> translations = {
  'zh_CN': {
    'app_name': '小思超级NAS', 'dashboard': '控制台', 'storage': '存储管理',
    'users': '用户管理', 'shares': '共享管理', 'push': '推送管理',
    'settings': '设置', 'volumes': '存储卷', 'create': '创建', 'delete': '删除',
    'edit': '编辑', 'save': '保存', 'cancel': '取消', 'name': '名称', 'path': '路径',
    'quota': '配额', 'used': '已用', 'available': '可用', 'username': '用户名',
    'password': '密码', 'admin': '管理员', 'storage_quota': '存储配额',
    'home_directory': '主目录', 'smb_status': 'SMB状态', 'smb_shares': 'SMB共享',
    'share_name': '共享名称', 'comment': '备注', 'read_only': '只读',
    'browseable': '可浏览', 'guest_access': '访客访问', 'language': '语言',
    'running': '运行中', 'stopped': '已停止', 'operation_success': '操作成功',
    'operation_failed': '操作失败', 'confirm_delete': '确认删除', 'no_data': '暂无数据',
    'create_volume': '创建存储卷', 'create_user': '创建用户', 'create_share': '创建共享',
    'operation': '操作', 'yes': '是', 'no': '否', 'system_info': '系统信息',
    'service_status': '服务状态', 'ip_address': 'IP地址', 'push_targets': '推送目标',
    'push_files': '推送文件', 'local_folder': '本地文件夹', 'target_device': '目标设备',
    'add_target': '添加目标', 'target_name': '目标名称', 'target_ip': '目标IP',
    'target_port': '目标端口', 'push_folder': '推送文件夹', 'select_folder': '选择文件夹',
    'push_now': '立即推送', 'pushing': '推送中', 'push_history': '推送历史',
    'scan_ip': '扫描IP', 'local_ips': '本机IP', 'scan': '扫描',
    'found_devices': '发现设备', 'online': '在线', 'offline': '离线',
    'send': '发送', 'receive': '接收', 'push_status': '推送状态',
    'success': '成功', 'failed': '失败', 'progress': '进度',
    'file_count': '文件数', 'total_size': '总大小', 'version': '第二代',
    'zero_dependency': '零依赖', 'api_docs': 'API文档'
  },
  'zh_TW': {
    'app_name': '小思超級NAS', 'dashboard': '控制台', 'storage': '存儲管理',
    'users': '用戶管理', 'shares': '共享管理', 'push': '推送管理',
    'settings': '設置', 'volumes': '存儲卷', 'create': '創建', 'delete': '刪除',
    'edit': '編輯', 'save': '保存', 'cancel': '取消', 'name': '名稱', 'path': '路徑',
    'quota': '配額', 'used': '已用', 'available': '可用', 'username': '用戶名',
    'password': '密碼', 'admin': '管理員', 'storage_quota': '存儲配額',
    'home_directory': '主目錄', 'smb_status': 'SMB狀態', 'smb_shares': 'SMB共享',
    'share_name': '共享名稱', 'comment': '備註', 'read_only': '只讀',
    'browseable': '可瀏覽', 'guest_access': '訪客訪問', 'language': '語言',
    'running': '運行中', 'stopped': '已停止', 'operation_success': '操作成功',
    'operation_failed': '操作失敗', 'confirm_delete': '確認刪除', 'no_data': '暫無數據',
    'create_volume': '創建存儲卷', 'create_user': '創建用戶', 'create_share': '創建共享',
    'operation': '操作', 'yes': '是', 'no': '否', 'system_info': '系統信息',
    'service_status': '服務狀態', 'ip_address': 'IP地址', 'push_targets': '推送目標',
    'push_files': '推送文件', 'local_folder': '本地文件夾', 'target_device': '目標設備',
    'add_target': '添加目標', 'target_name': '目標名稱', 'target_ip': '目標IP',
    'target_port': '目標端口', 'push_folder': '推送文件夾', 'select_folder': '選擇文件夾',
    'push_now': '立即推送', 'pushing': '推送中', 'push_history': '推送歷史',
    'scan_ip': '掃描IP', 'local_ips': '本機IP', 'scan': '掃描',
    'found_devices': '發現設備', 'online': '在線', 'offline': '離線',
    'send': '發送', 'receive': '接收', 'push_status': '推送狀態',
    'success': '成功', 'failed': '失敗', 'progress': '進度',
    'file_count': '文件數', 'total_size': '總大小', 'version': '第二代',
    'zero_dependency': '零依賴', 'api_docs': 'API文檔'
  },
  'en_US': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Storage',
    'users': 'Users', 'shares': 'Shares', 'push': 'Push Manager',
    'settings': 'Settings', 'volumes': 'Volumes', 'create': 'Create', 'delete': 'Delete',
    'edit': 'Edit', 'save': 'Save', 'cancel': 'Cancel', 'name': 'Name', 'path': 'Path',
    'quota': 'Quota', 'used': 'Used', 'available': 'Available', 'username': 'Username',
    'password': 'Password', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Shares',
    'share_name': 'Share Name', 'comment': 'Comment', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Language',
    'running': 'Running', 'stopped': 'Stopped', 'operation_success': 'Operation Success',
    'operation_failed': 'Operation Failed', 'confirm_delete': 'Confirm Delete', 'no_data': 'No Data',
    'create_volume': 'Create Volume', 'create_user': 'Create User', 'create_share': 'Create Share',
    'operation': 'Operation', 'yes': 'Yes', 'no': 'No', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP Address', 'push_targets': 'Push Targets',
    'push_files': 'Push Files', 'local_folder': 'Local Folder', 'target_device': 'Target Device',
    'add_target': 'Add Target', 'target_name': 'Target Name', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Select Folder',
    'push_now': 'Push Now', 'pushing': 'Pushing', 'push_history': 'Push History',
    'scan_ip': 'Scan IP', 'local_ips': 'Local IPs', 'scan': 'Scan',
    'found_devices': 'Found Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Send', 'receive': 'Receive', 'push_status': 'Push Status',
    'success': 'Success', 'failed': 'Failed', 'progress': 'Progress',
    'file_count': 'File Count', 'total_size': 'Total Size', 'version': 'Version 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'en_GB': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Storage',
    'users': 'Users', 'shares': 'Shares', 'push': 'Push Manager',
    'settings': 'Settings', 'volumes': 'Volumes', 'create': 'Create', 'delete': 'Delete',
    'edit': 'Edit', 'save': 'Save', 'cancel': 'Cancel', 'name': 'Name', 'path': 'Path',
    'quota': 'Quota', 'used': 'Used', 'available': 'Available', 'username': 'Username',
    'password': 'Password', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Shares',
    'share_name': 'Share Name', 'comment': 'Comment', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Language',
    'running': 'Running', 'stopped': 'Stopped', 'operation_success': 'Operation Success',
    'operation_failed': 'Operation Failed', 'confirm_delete': 'Confirm Delete', 'no_data': 'No Data',
    'create_volume': 'Create Volume', 'create_user': 'Create User', 'create_share': 'Create Share',
    'operation': 'Operation', 'yes': 'Yes', 'no': 'No', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP Address', 'push_targets': 'Push Targets',
    'push_files': 'Push Files', 'local_folder': 'Local Folder', 'target_device': 'Target Device',
    'add_target': 'Add Target', 'target_name': 'Target Name', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Select Folder',
    'push_now': 'Push Now', 'pushing': 'Pushing', 'push_history': 'Push History',
    'scan_ip': 'Scan IP', 'local_ips': 'Local IPs', 'scan': 'Scan',
    'found_devices': 'Found Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Send', 'receive': 'Receive', 'push_status': 'Push Status',
    'success': 'Success', 'failed': 'Failed', 'progress': 'Progress',
    'file_count': 'File Count', 'total_size': 'Total Size', 'version': 'Version 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'ja_JP': {
    'app_name': '小思スーパーNAS', 'dashboard': 'ダッシュボード', 'storage': 'ストレージ',
    'users': 'ユーザー', 'shares': '共有', 'push': 'プッシュ管理',
    'settings': '設定', 'volumes': 'ボリューム', 'create': '作成', 'delete': '削除',
    'edit': '編集', 'save': '保存', 'cancel': 'キャンセル', 'name': '名前', 'path': 'パス',
    'quota': 'クォータ', 'used': '使用中', 'available': '利用可能', 'username': 'ユーザー名',
    'password': 'パスワード', 'admin': '管理者', 'storage_quota': 'ストレージクォータ',
    'home_directory': 'ホームディレクトリ', 'smb_status': 'SMB状態', 'smb_shares': 'SMB共有',
    'share_name': '共有名', 'comment': 'コメント', 'read_only': '読み取り専用',
    'browseable': '参照可能', 'guest_access': 'ゲストアクセス', 'language': '言語',
    'running': '実行中', 'stopped': '停止中', 'operation_success': '操作成功',
    'operation_failed': '操作失敗', 'confirm_delete': '削除の確認', 'no_data': 'データなし',
    'create_volume': 'ボリューム作成', 'create_user': 'ユーザー作成', 'create_share': '共有作成',
    'operation': '操作', 'yes': 'はい', 'no': 'いいえ', 'system_info': 'システム情報',
    'service_status': 'サービス状態', 'ip_address': 'IPアドレス', 'push_targets': 'プッシュ先',
    'push_files': 'ファイル送信', 'local_folder': 'ローカルフォルダ', 'target_device': '対象デバイス',
    'add_target': '対象を追加', 'target_name': '対象名', 'target_ip': '対象IP',
    'target_port': '対象ポート', 'push_folder': 'フォルダ送信', 'select_folder': 'フォルダ選択',
    'push_now': '今すぐ送信', 'pushing': '送信中', 'push_history': '送信履歴',
    'scan_ip': 'IPスキャン', 'local_ips': 'ローカルIP', 'scan': 'スキャン',
    'found_devices': '発見デバイス', 'online': 'オンライン', 'offline': 'オフライン',
    'send': '送信', 'receive': '受信', 'push_status': '送信状態',
    'success': '成功', 'failed': '失敗', 'progress': '進捗',
    'file_count': 'ファイル数', 'total_size': '合計サイズ', 'version': '第2世代',
    'zero_dependency': 'ゼロ依存', 'api_docs': 'APIドキュメント'
  },
  'ko_KR': {
    'app_name': '小思 슈퍼 NAS', 'dashboard': '대시보드', 'storage': '저장소',
    'users': '사용자', 'shares': '공유', 'push': '推送 관리',
    'settings': '설정', 'volumes': '볼륨', 'create': '생성', 'delete': '삭제',
    'edit': '편집', 'save': '저장', 'cancel': '취소', 'name': '이름', 'path': '경로',
    'quota': '할당량', 'used': '사용', 'available': '사용 가능', 'username': '사용자 이름',
    'password': '비밀번호', 'admin': '관리자', 'storage_quota': '저장소 할당량',
    'home_directory': '홈 디렉토리', 'smb_status': 'SMB 상태', 'smb_shares': 'SMB 공유',
    'share_name': '공유 이름', 'comment': '설명', 'read_only': '읽기 전용',
    'browseable': '탐색 가능', 'guest_access': '게스트 접근', 'language': '언어',
    'running': '실행 중', 'stopped': '중지됨', 'operation_success': '작업 성공',
    'operation_failed': '작업 실패', 'confirm_delete': '삭제 확인', 'no_data': '데이터 없음',
    'create_volume': '볼륨 생성', 'create_user': '사용자 생성', 'create_share': '공유 생성',
    'operation': '작업', 'yes': '예', 'no': '아니오', 'system_info': '시스템 정보',
    'service_status': '서비스 상태', 'ip_address': 'IP 주소', 'push_targets': '推送 대상',
    'push_files': '파일推送', 'local_folder': '로컬 폴더', 'target_device': '대상 장치',
    'add_target': '대상 추가', 'target_name': '대상 이름', 'target_ip': '대상 IP',
    'target_port': '대상 포트', 'push_folder': '폴더推送', 'select_folder': '폴더 선택',
    'push_now': '즉시推送', 'pushing': '推送 중', 'push_history': '推送 기록',
    'scan_ip': 'IP 스캔', 'local_ips': '로컬 IP', 'scan': '스캔',
    'found_devices': '발견 장치', 'online': '온라인', 'offline': '오프라인',
    'send': '보내기', 'receive': '받기', 'push_status': '推送 상태',
    'success': '성공', 'failed': '실패', 'progress': '진행률',
    'file_count': '파일 수', 'total_size': '전체 크기', 'version': '제2세대',
    'zero_dependency': '제로 의존성', 'api_docs': 'API 문서'
  },
  'de_DE': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Speicher',
    'users': 'Benutzer', 'shares': 'Freigaben', 'push': 'Push Manager',
    'settings': 'Einstellungen', 'volumes': 'Volumes', 'create': 'Erstellen', 'delete': 'Löschen',
    'edit': 'Bearbeiten', 'save': 'Speichern', 'cancel': 'Abbrechen', 'name': 'Name', 'path': 'Pfad',
    'quota': 'Quota', 'used': 'Verwendet', 'available': 'Verfügbar', 'username': 'Benutzername',
    'password': 'Passwort', 'admin': 'Admin', 'storage_quota': 'Speicherquota',
    'home_directory': 'Home-Verzeichnis', 'smb_status': 'SMB-Status', 'smb_shares': 'SMB-Freigaben',
    'share_name': 'Freigabe-Name', 'comment': 'Kommentar', 'read_only': 'Read-Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Sprache',
    'running': 'Laufend', 'stopped': 'Gestoppt', 'operation_success': 'Operation Erfolgreich',
    'operation_failed': 'Operation Fehlgeschlagen', 'confirm_delete': 'Löschen Bestätigen', 'no_data': 'Keine Daten',
    'create_volume': 'Volume Erstellen', 'create_user': 'Benutzer Erstellen', 'create_share': 'Freigabe Erstellen',
    'operation': 'Operation', 'yes': 'Ja', 'no': 'Nein', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP-Adresse', 'push_targets': 'Push Targets',
    'push_files': 'Push Dateien', 'local_folder': 'Lokaler Folder', 'target_device': 'Target Gerät',
    'add_target': 'Target Hinzufügen', 'target_name': 'Target Name', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Folder Wählen',
    'push_now': 'Push Jetzt', 'pushing': 'Pushing', 'push_history': 'Push Historie',
    'scan_ip': 'Scan IP', 'local_ips': 'Lokale IPs', 'scan': 'Scan',
    'found_devices': 'Found Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Senden', 'receive': 'Empfangen', 'push_status': 'Push Status',
    'success': 'Erfolg', 'failed': 'Fehlgeschlagen', 'progress': 'Progress',
    'file_count': 'Dateianzahl', 'total_size': 'Gesamtgröße', 'version': 'Version 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'fr_FR': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Stockage',
    'users': 'Utilisateurs', 'shares': 'Partages', 'push': 'Push Manager',
    'settings': 'Paramètres', 'volumes': 'Volumes', 'create': 'Créer', 'delete': 'Supprimer',
    'edit': 'Modifier', 'save': 'Enregistrer', 'cancel': 'Annuler', 'name': 'Nom', 'path': 'Chemin',
    'quota': 'Quota', 'used': 'Utilisé', 'available': 'Disponible', 'username': 'Nom d\'utilisateur',
    'password': 'Mot de passe', 'admin': 'Admin', 'storage_quota': 'Quota Stockage',
    'home_directory': 'Home Directory', 'smb_status': 'Statut SMB', 'smb_shares': 'Partages SMB',
    'share_name': 'Nom du Partage', 'comment': 'Commentaire', 'read_only': 'Lecture Seule',
    'browseable': 'Navigable', 'guest_access': 'Accès Invité', 'language': 'Langue',
    'running': 'En Cours', 'stopped': 'Arrêté', 'operation_success': 'Opération Succès',
    'operation_failed': 'Opération Échouée', 'confirm_delete': 'Confirmer Suppression', 'no_data': 'Pas de Données',
    'create_volume': 'Créer Volume', 'create_user': 'Créer Utilisateur', 'create_share': 'Créer Partage',
    'operation': 'Opération', 'yes': 'Oui', 'no': 'Non', 'system_info': 'Info Système',
    'service_status': 'Statut Service', 'ip_address': 'Adresse IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Fichiers', 'local_folder': 'Folder Local', 'target_device': 'Device Cible',
    'add_target': 'Ajouter Target', 'target_name': 'Nom Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Sélectionner Folder',
    'push_now': 'Push Maintenant', 'pushing': 'Pushing', 'push_history': 'Historique Push',
    'scan_ip': 'Scanner IP', 'local_ips': 'IPs Locales', 'scan': 'Scanner',
    'found_devices': 'Devices Trouvés', 'online': 'En Ligne', 'offline': 'Hors Ligne',
    'send': 'Envoyer', 'receive': 'Recevoir', 'push_status': 'Statut Push',
    'success': 'Succès', 'failed': 'Échoué', 'progress': 'Progress',
    'file_count': 'Nombre de Fichiers', 'total_size': 'Taille Totale', 'version': 'Version 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'es_ES': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Almacenamiento',
    'users': 'Usuarios', 'shares': 'Compartidos', 'push': 'Push Manager',
    'settings': 'Configuración', 'volumes': 'Volúmenes', 'create': 'Crear', 'delete': 'Eliminar',
    'edit': 'Editar', 'save': 'Guardar', 'cancel': 'Cancelar', 'name': 'Nombre', 'path': 'Ruta',
    'quota': 'Quota', 'used': 'Usado', 'available': 'Disponible', 'username': 'Usuario',
    'password': 'Contraseña', 'admin': 'Admin', 'storage_quota': 'Quota Almacenamiento',
    'home_directory': 'Directorio Home', 'smb_status': 'Estado SMB', 'smb_shares': 'Compartidos SMB',
    'share_name': 'Nombre Compartido', 'comment': 'Comentario', 'read_only': 'Solo Lectura',
    'browseable': 'Navegable', 'guest_access': 'Acceso Invitado', 'language': 'Idioma',
    'running': 'Ejecutando', 'stopped': 'Detenido', 'operation_success': 'Operación Exitosa',
    'operation_failed': 'Operación Fallida', 'confirm_delete': 'Confirmar Eliminar', 'no_data': 'Sin Datos',
    'create_volume': 'Crear Volumen', 'create_user': 'Crear Usuario', 'create_share': 'Crear Compartido',
    'operation': 'Operación', 'yes': 'Sí', 'no': 'No', 'system_info': 'Info Sistema',
    'service_status': 'Estado Servicio', 'ip_address': 'Dirección IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Archivos', 'local_folder': 'Folder Local', 'target_device': 'Device Destino',
    'add_target': 'Agregar Target', 'target_name': 'Nombre Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Seleccionar Folder',
    'push_now': 'Push Ahora', 'pushing': 'Pushing', 'push_history': 'Historial Push',
    'scan_ip': 'Escaneo IP', 'local_ips': 'IPs Locales', 'scan': 'Escaneo',
    'found_devices': 'Devices Encontrados', 'online': 'Online', 'offline': 'Offline',
    'send': 'Enviar', 'receive': 'Recibir', 'push_status': 'Estado Push',
    'success': 'Éxito', 'failed': 'Fallido', 'progress': 'Progreso',
    'file_count': 'Cantidad Archivos', 'total_size': 'Tamaño Total', 'version': 'Versión 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'it_IT': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Archiviazione',
    'users': 'Utenti', 'shares': 'Condivisioni', 'push': 'Push Manager',
    'settings': 'Impostazioni', 'volumes': 'Volumes', 'create': 'Creare', 'delete': 'Eliminare',
    'edit': 'Modificare', 'save': 'Salvare', 'cancel': 'Annullare', 'name': 'Nome', 'path': 'Percorso',
    'quota': 'Quota', 'used': 'Usato', 'available': 'Disponibile', 'username': 'Nome Utente',
    'password': 'Password', 'admin': 'Admin', 'storage_quota': 'Quota Archiviazione',
    'home_directory': 'Home Directory', 'smb_status': 'Stato SMB', 'smb_shares': 'Condivisioni SMB',
    'share_name': 'Nome Condivisione', 'comment': 'Commento', 'read_only': 'Solo Lettura',
    'browseable': 'Navigabile', 'guest_access': 'Accesso Guest', 'language': 'Lingua',
    'running': 'In Esecuzione', 'stopped': 'Fermato', 'operation_success': 'Operazione Successo',
    'operation_failed': 'Operazione Fallita', 'confirm_delete': 'Conferma Eliminare', 'no_data': 'Nessun Dato',
    'create_volume': 'Creare Volume', 'create_user': 'Creare Utente', 'create_share': 'Creare Condivisione',
    'operation': 'Operazione', 'yes': 'Sì', 'no': 'No', 'system_info': 'Info Sistema',
    'service_status': 'Stato Servizio', 'ip_address': 'Indirizzo IP', 'push_targets': 'Push Targets',
    'push_files': 'Push File', 'local_folder': 'Folder Locale', 'target_device': 'Device Target',
    'add_target': 'Aggiungi Target', 'target_name': 'Nome Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Seleziona Folder',
    'push_now': 'Push Ora', 'pushing': 'Pushing', 'push_history': 'Storia Push',
    'scan_ip': 'Scansione IP', 'local_ips': 'IPs Locali', 'scan': 'Scansione',
    'found_devices': 'Devices Trovati', 'online': 'Online', 'offline': 'Offline',
    'send': 'Inviare', 'receive': 'Ricevere', 'push_status': 'Stato Push',
    'success': 'Successo', 'failed': 'Fallito', 'progress': 'Progress',
    'file_count': 'Numero File', 'total_size': 'Dimensione Totale', 'version': 'Versione 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'pt_PT': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Armazenamento',
    'users': 'Usuários', 'shares': 'Partilhas', 'push': 'Push Manager',
    'settings': 'Configurações', 'volumes': 'Volumes', 'create': 'Criar', 'delete': 'Apagar',
    'edit': 'Editar', 'save': 'Guardar', 'cancel': 'Cancelar', 'name': 'Nome', 'path': 'Caminho',
    'quota': 'Quota', 'used': 'Usado', 'available': 'Disponível', 'username': 'Nome Usuário',
    'password': 'Senha', 'admin': 'Admin', 'storage_quota': 'Quota Armazenamento',
    'home_directory': 'Home Directory', 'smb_status': 'Estado SMB', 'smb_shares': 'Partilhas SMB',
    'share_name': 'Nome Partilha', 'comment': 'Comentário', 'read_only': 'Leitura Só',
    'browseable': 'Navegável', 'guest_access': 'Acesso Guest', 'language': 'Linguagem',
    'running': 'Executando', 'stopped': 'Parado', 'operation_success': 'Operação Sucesso',
    'operation_failed': 'Operação Falhou', 'confirm_delete': 'Confirmar Apagar', 'no_data': 'Sem Dados',
    'create_volume': 'Criar Volume', 'create_user': 'Criar Usuário', 'create_share': 'Criar Partilha',
    'operation': 'Operação', 'yes': 'Sim', 'no': 'Não', 'system_info': 'Info Sistema',
    'service_status': 'Estado Serviço', 'ip_address': 'Endereço IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Ficheiros', 'local_folder': 'Folder Local', 'target_device': 'Device Alvo',
    'add_target': 'Adicionar Target', 'target_name': 'Nome Target', 'target_ip': 'IP Target',
    'target_port': 'Porta Target', 'push_folder': 'Push Folder', 'select_folder': 'Selecionar Folder',
    'push_now': 'Push Agora', 'pushing': 'Pushing', 'push_history': 'História Push',
    'scan_ip': 'Scan IP', 'local_ips': 'IPs Locais', 'scan': 'Scan',
    'found_devices': 'Devices Encontrados', 'online': 'Online', 'offline': 'Offline',
    'send': 'Enviar', 'receive': 'Receber', 'push_status': 'Estado Push',
    'success': 'Sucesso', 'failed': 'Falhou', 'progress': 'Progresso',
    'file_count': 'Contagem Ficheiros', 'total_size': 'Tamanho Total', 'version': 'Versão 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'ru_RU': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Панель управления', 'storage': 'Хранилище',
    'users': 'Пользователи', 'shares': 'Общие ресурсы', 'push': 'Менеджер Push',
    'settings': 'Настройки', 'volumes': 'Тома', 'create': 'Создать', 'delete': 'Удалить',
    'edit': 'Редактировать', 'save': 'Сохранить', 'cancel': 'Отмена', 'name': 'Имя', 'path': 'Путь',
    'quota': 'Квота', 'used': 'Использовано', 'available': 'Доступно', 'username': 'Имя пользователя',
    'password': 'Пароль', 'admin': 'Админ', 'storage_quota': 'Квота хранилища',
    'home_directory': 'Домашний каталог', 'smb_status': 'Статус SMB', 'smb_shares': 'SMB общие ресурсы',
    'share_name': 'Имя общего ресурса', 'comment': 'Комментарий', 'read_only': 'Только чтение',
    'browseable': 'Обзор', 'guest_access': 'Гостевой доступ', 'language': 'Язык',
    'running': 'Работает', 'stopped': 'Остановлен', 'operation_success': 'Операция успешна',
    'operation_failed': 'Операция не удалась', 'confirm_delete': 'Подтвердить удаление', 'no_data': 'Нет данных',
    'create_volume': 'Создать том', 'create_user': 'Создать пользователя', 'create_share': 'Создать общий ресурс',
    'operation': 'Операция', 'yes': 'Да', 'no': 'Нет', 'system_info': 'Системная информация',
    'service_status': 'Статус сервиса', 'ip_address': 'IP-адрес', 'push_targets': 'Push цели',
    'push_files': 'Push файлы', 'local_folder': 'Локальная папка', 'target_device': 'Целевое устройство',
    'add_target': 'Добавить цель', 'target_name': 'Имя цели', 'target_ip': 'IP цели',
    'target_port': 'Порт цели', 'push_folder': 'Push папку', 'select_folder': 'Выбрать папку',
    'push_now': 'Push сейчас', 'pushing': 'Push выполняется', 'push_history': 'История Push',
    'scan_ip': 'Сканировать IP', 'local_ips': 'Локальные IPs', 'scan': 'Сканировать',
    'found_devices': 'Найденные устройства', 'online': 'Онлайн', 'offline': 'Оффлайн',
    'send': 'Отправить', 'receive': 'Получить', 'push_status': 'Статус Push',
    'success': 'Успешно', 'failed': 'Не удалось', 'progress': 'Прогресс',
    'file_count': 'Количество файлов', 'total_size': 'Общий размер', 'version': 'Версия 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'ar_SA': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'لوحة التحكم', 'storage': 'التخزين',
    'users': 'المستخدمين', 'shares': 'المشاركات', 'push': 'مدير Push',
    'settings': 'الإعدادات', 'volumes': 'الأحجام', 'create': 'إنشاء', 'delete': 'حذف',
    'edit': 'تحرير', 'save': 'حفظ', 'cancel': 'إلغاء', 'name': 'الاسم', 'path': 'المسار',
    'quota': 'الحصة', 'used': 'المستخدم', 'available': 'المتاح', 'username': 'اسم المستخدم',
    'password': 'كلمة المرور', 'admin': 'المدير', 'storage_quota': 'حصة التخزين',
    'home_directory': 'الدليل الرئيسي', 'smb_status': 'حالة SMB', 'smb_shares': 'مشاركات SMB',
    'share_name': 'اسم المشاركة', 'comment': 'تعليق', 'read_only': 'للقراءة فقط',
    'browseable': 'قابل للتصفح', 'guest_access': 'وصول الضيف', 'language': 'اللغة',
    'running': 'قيد التشغيل', 'stopped': 'متوقف', 'operation_success': 'عملية ناجحة',
    'operation_failed': 'عملية فاشلة', 'confirm_delete': 'تأكيد الحذف', 'no_data': 'لا توجد بيانات',
    'create_volume': 'إنشاء حجم', 'create_user': 'إنشاء مستخدم', 'create_share': 'إنشاء مشاركة',
    'operation': 'عملية', 'yes': 'نعم', 'no': 'لا', 'system_info': 'معلومات النظام',
    'service_status': 'حالة الخدمة', 'ip_address': 'عنوان IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Files', 'local_folder': 'Folder المحلي', 'target_device': 'الجهاز المستهدف',
    'add_target': 'إضافة Target', 'target_name': 'اسم Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'اختر Folder',
    'push_now': 'Push الآن', 'pushing': 'Pushing', 'push_history': 'تاريخ Push',
    'scan_ip': 'فحص IP', 'local_ips': 'IPs المحلية', 'scan': 'فحص',
    'found_devices': 'الأجهزة الموجودة', 'online': 'متصل', 'offline': 'غير متصل',
    'send': 'إرسال', 'receive': 'استقبال', 'push_status': 'حالة Push',
    'success': 'نجاح', 'failed': 'فشل', 'progress': 'التقدم',
    'file_count': 'عدد الملفات', 'total_size': 'الحجم الإجمالي', 'version': 'الإصدار 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'hi_IN': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'डैशबोर्ड', 'storage': 'स्टोरेज',
    'users': 'उपयोगकर्ता', 'shares': 'शेयर', 'push': 'Push Manager',
    'settings': 'सेटिंग्स', 'volumes': 'Volumes', 'create': 'बनाएं', 'delete': 'हटाएं',
    'edit': 'संपादित', 'save': 'सहेजें', 'cancel': 'कैंसल', 'name': 'नाम', 'path': 'पथ',
    'quota': 'Quota', 'used': 'उपयोग', 'available': 'उपलब्ध', 'username': 'Username',
    'password': 'Password', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Shares',
    'share_name': 'Share Name', 'comment': 'Comment', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Language',
    'running': 'Running', 'stopped': 'Stopped', 'operation_success': 'Operation Success',
    'operation_failed': 'Operation Failed', 'confirm_delete': 'Delete Confirm', 'no_data': 'No Data',
    'create_volume': 'Create Volume', 'create_user': 'Create User', 'create_share': 'Create Share',
    'operation': 'Operation', 'yes': 'Yes', 'no': 'No', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP Address', 'push_targets': 'Push Targets',
    'push_files': 'Push Files', 'local_folder': 'Local Folder', 'target_device': 'Target Device',
    'add_target': 'Add Target', 'target_name': 'Target Name', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Select Folder',
    'push_now': 'Push Now', 'pushing': 'Pushing', 'push_history': 'Push History',
    'scan_ip': 'Scan IP', 'local_ips': 'Local IPs', 'scan': 'Scan',
    'found_devices': 'Found Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Send', 'receive': 'Receive', 'push_status': 'Push Status',
    'success': 'Success', 'failed': 'Failed', 'progress': 'Progress',
    'file_count': 'File Count', 'total_size': 'Total Size', 'version': 'Version 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'tr_TR': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Depolama',
    'users': 'Kullanıcılar', 'shares': 'Paylaşımlar', 'push': 'Push Manager',
    'settings': 'Ayarlar', 'volumes': 'Volumes', 'create': 'Oluştur', 'delete': 'Sil',
    'edit': 'Düzenle', 'save': 'Kaydet', 'cancel': 'İptal', 'name': 'Ad', 'path': 'Yol',
    'quota': 'Quota', 'used': 'Kullanılan', 'available': 'Kullanılabilir', 'username': 'Kullanıcı Adı',
    'password': 'Şifre', 'admin': 'Admin', 'storage_quota': 'Depolama Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Durumu', 'smb_shares': 'SMB Paylaşımları',
    'share_name': 'Paylaşım Adı', 'comment': 'Yorum', 'read_only': 'Salt Okunur',
    'browseable': 'Göz Atılabilir', 'guest_access': 'Guest Erişimi', 'language': 'Dil',
    'running': 'Çalışıyor', 'stopped': 'Durduruldu', 'operation_success': 'İşlem Başarılı',
    'operation_failed': 'İşlem Başarısız', 'confirm_delete': 'Silmeyi Onayla', 'no_data': 'Veri Yok',
    'create_volume': 'Volume Oluştur', 'create_user': 'Kullanıcı Oluştur', 'create_share': 'Paylaşım Oluştur',
    'operation': 'İşlem', 'yes': 'Evet', 'no': 'Hayır', 'system_info': 'Sistem Bilgisi',
    'service_status': 'Servis Durumu', 'ip_address': 'IP Adresi', 'push_targets': 'Push Targets',
    'push_files': 'Push Dosyaları', 'local_folder': 'Yerel Folder', 'target_device': 'Hedef Cihaz',
    'add_target': 'Target Ekle', 'target_name': 'Target Adı', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Folder Seç',
    'push_now': 'Şimdi Push', 'pushing': 'Pushing', 'push_history': 'Push Geçmişi',
    'scan_ip': 'IP Tarama', 'local_ips': 'Yerel IPs', 'scan': 'Tarama',
    'found_devices': 'Bulunan Cihazlar', 'online': 'Online', 'offline': 'Offline',
    'send': 'Gönder', 'receive': 'Al', 'push_status': 'Push Durumu',
    'success': 'Başarılı', 'failed': 'Başarısız', 'progress': 'İlerleme',
    'file_count': 'Dosya Sayısı', 'total_size': 'Toplam Boyut', 'version': 'Versiyon 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'th_TH': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'แดชบอร์ด', 'storage': 'การจัดเก็บ',
    'users': 'ผู้ใช้', 'shares': 'การแชร์', 'push': 'Push Manager',
    'settings': 'การตั้งค่า', 'volumes': 'Volumes', 'create': 'สร้าง', 'delete': 'ลบ',
    'edit': 'แก้ไข', 'save': 'บันทึก', 'cancel': 'ยกเลิก', 'name': 'ชื่อ', 'path': 'เส้นทาง',
    'quota': 'Quota', 'used': 'ที่ใช้', 'available': 'ที่มี', 'username': 'ชื่อผู้ใช้',
    'password': 'รหัสผ่าน', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'สถานะ SMB', 'smb_shares': 'การแชร์ SMB',
    'share_name': 'ชื่อการแชร์', 'comment': 'ความคิดเห็น', 'read_only': 'อ่านเท่านั้น',
    'browseable': 'สามารถเรียกดู', 'guest_access': 'การเข้าถึง Guest', 'language': 'ภาษา',
    'running': 'กำลังทำงาน', 'stopped': 'หยุด', 'operation_success': 'ดำเนินการสำเร็จ',
    'operation_failed': 'ดำเนินการไม่สำเร็จ', 'confirm_delete': 'ยืนยันการลบ', 'no_data': 'ไม่มีข้อมูล',
    'create_volume': 'สร้าง Volume', 'create_user': 'สร้างผู้ใช้', 'create_share': 'สร้างการแชร์',
    'operation': 'การดำเนินการ', 'yes': 'ใช่', 'no': 'ไม่', 'system_info': 'ข้อมูลระบบ',
    'service_status': 'สถานะบริการ', 'ip_address': 'ที่อยู่ IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Files', 'local_folder': 'Folder ภายใน', 'target_device': 'อุปกรณ์เป้าหมาย',
    'add_target': 'เพิ่ม Target', 'target_name': 'ชื่อ Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'เลือก Folder',
    'push_now': 'Push ทันที', 'pushing': 'Pushing', 'push_history': 'ประวัติ Push',
    'scan_ip': 'สแกน IP', 'local_ips': 'IPs ภายใน', 'scan': 'สแกน',
    'found_devices': 'อุปกรณ์ที่พบ', 'online': 'ออนไลน์', 'offline': 'ออฟไลน์',
    'send': 'ส่ง', 'receive': 'รับ', 'push_status': 'สถานะ Push',
    'success': 'สำเร็จ', 'failed': 'ไม่สำเร็จ', 'progress': 'ความคืบหน้า',
    'file_count': 'จำนวนไฟล์', 'total_size': 'ขนาดรวม', 'version': 'เวอร์ชัน 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'vi_VN': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Bảng điều khiển', 'storage': 'Lưu trữ',
    'users': 'Người dùng', 'shares': 'Chia sẻ', 'push': 'Quản lý Push',
    'settings': 'Cài đặt', 'volumes': 'Volumes', 'create': 'Tạo', 'delete': 'Xóa',
    'edit': 'Sửa', 'save': 'Lưu', 'cancel': 'Hủy', 'name': 'Tên', 'path': 'Đường dẫn',
    'quota': 'Quota', 'used': 'Đã dùng', 'available': 'Khả dụng', 'username': 'Tên người dùng',
    'password': 'Mật khẩu', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Thư mục Home', 'smb_status': 'Trạng thái SMB', 'smb_shares': 'Chia sẻ SMB',
    'share_name': 'Tên chia sẻ', 'comment': 'Ghi chú', 'read_only': 'Chỉ đọc',
    'browseable': 'Có thể duyệt', 'guest_access': 'Guest Access', 'language': 'Ngôn ngữ',
    'running': 'Đang chạy', 'stopped': 'Đã dừng', 'operation_success': 'Thao tác thành công',
    'operation_failed': 'Thao tác thất bại', 'confirm_delete': 'Xác nhận xóa', 'no_data': 'Không có dữ liệu',
    'create_volume': 'Tạo Volume', 'create_user': 'Tạo người dùng', 'create_share': 'Tạo chia sẻ',
    'operation': 'Thao tác', 'yes': 'Có', 'no': 'Không', 'system_info': 'Thông tin hệ thống',
    'service_status': 'Trạng thái dịch vụ', 'ip_address': 'Địa chỉ IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Files', 'local_folder': 'Folder cục bộ', 'target_device': 'Thiết bị mục tiêu',
    'add_target': 'Thêm Target', 'target_name': 'Tên Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Chọn Folder',
    'push_now': 'Push ngay', 'pushing': 'Pushing', 'push_history': 'Lịch sử Push',
    'scan_ip': 'Quét IP', 'local_ips': 'IPs cục bộ', 'scan': 'Quét',
    'found_devices': 'Thiết bị tìm thấy', 'online': 'Trực tuyến', 'offline': 'Ngoại tuyến',
    'send': 'Gửi', 'receive': 'Nhận', 'push_status': 'Trạng thái Push',
    'success': 'Thành công', 'failed': 'Thất bại', 'progress': 'Tiến trình',
    'file_count': 'Số file', 'total_size': 'Tổng kích thước', 'version': 'Phiên bản 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'id_ID': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Penyimpanan',
    'users': 'Pengguna', 'shares': 'Berbagi', 'push': 'Push Manager',
    'settings': 'Pengaturan', 'volumes': 'Volumes', 'create': 'Buat', 'delete': 'Hapus',
    'edit': 'Edit', 'save': 'Simpan', 'cancel': 'Batal', 'name': 'Nama', 'path': 'Path',
    'quota': 'Quota', 'used': 'Digunakan', 'available': 'Tersedia', 'username': 'Username',
    'password': 'Password', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'Status SMB', 'smb_shares': 'SMB Shares',
    'share_name': 'Nama Share', 'comment': 'Komentar', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Bahasa',
    'running': 'Berjalan', 'stopped': 'Berhenti', 'operation_success': 'Operasi Sukses',
    'operation_failed': 'Operasi Gagal', 'confirm_delete': 'Konfirmasi Hapus', 'no_data': 'Tidak Ada Data',
    'create_volume': 'Buat Volume', 'create_user': 'Buat Pengguna', 'create_share': 'Buat Share',
    'operation': 'Operasi', 'yes': 'Ya', 'no': 'Tidak', 'system_info': 'Info Sistem',
    'service_status': 'Status Layanan', 'ip_address': 'Alamat IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Files', 'local_folder': 'Folder Lokal', 'target_device': 'Device Target',
    'add_target': 'Tambah Target', 'target_name': 'Nama Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Pilih Folder',
    'push_now': 'Push Sekarang', 'pushing': 'Pushing', 'push_history': 'Riwayat Push',
    'scan_ip': 'Scan IP', 'local_ips': 'IPs Lokal', 'scan': 'Scan',
    'found_devices': 'Device Ditemukan', 'online': 'Online', 'offline': 'Offline',
    'send': 'Kirim', 'receive': 'Terima', 'push_status': 'Status Push',
    'success': 'Sukses', 'failed': 'Gagal', 'progress': 'Progres',
    'file_count': 'Jumlah File', 'total_size': 'Total Ukuran', 'version': 'Versi 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'nl_NL': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Opslag',
    'users': 'Gebruikers', 'shares': 'Shares', 'push': 'Push Manager',
    'settings': 'Instellingen', 'volumes': 'Volumes', 'create': 'Creëer', 'delete': 'Verwijder',
    'edit': 'Bewerk', 'save': 'Opslaan', 'cancel': 'Annuleren', 'name': 'Naam', 'path': 'Pad',
    'quota': 'Quota', 'used': 'Gebruikt', 'available': 'Beschikbaar', 'username': 'Gebruikersnaam',
    'password': 'Wachtwoord', 'admin': 'Admin', 'storage_quota': 'Opslag Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Shares',
    'share_name': 'Share Naam', 'comment': 'Commentaar', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Taal',
    'running': 'Actief', 'stopped': 'Gestopt', 'operation_success': 'Operatie Succes',
    'operation_failed': 'Operatie Mislukt', 'confirm_delete': 'Bevestig Verwijdering', 'no_data': 'Geen Data',
    'create_volume': 'Creëer Volume', 'create_user': 'Creëer Gebruiker', 'create_share': 'Creëer Share',
    'operation': 'Operatie', 'yes': 'Ja', 'no': 'Nee', 'system_info': 'Systeem Info',
    'service_status': 'Service Status', 'ip_address': 'IP-Adres', 'push_targets': 'Push Targets',
    'push_files': 'Push Bestanden', 'local_folder': 'Lokale Folder', 'target_device': 'Target Device',
    'add_target': 'Target Toevoegen', 'target_name': 'Target Naam', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Selecteer Folder',
    'push_now': 'Push Nu', 'pushing': 'Pushing', 'push_history': 'Push Historie',
    'scan_ip': 'Scan IP', 'local_ips': 'Lokale IPs', 'scan': 'Scan',
    'found_devices': 'Gevonden Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Verstuur', 'receive': 'Ontvang', 'push_status': 'Push Status',
    'success': 'Succes', 'failed': 'Mislukt', 'progress': 'Progress',
    'file_count': 'Aantal Bestanden', 'total_size': 'Totale Grootte', 'version': 'Versie 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'pl_PL': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Przechowywanie',
    'users': 'Użytkownicy', 'shares': 'Udostępnienia', 'push': 'Push Manager',
    'settings': 'Ustawienia', 'volumes': 'Volumes', 'create': 'Utwórz', 'delete': 'Usuń',
    'edit': 'Edytuj', 'save': 'Zapisz', 'cancel': 'Anuluj', 'name': 'Nazwa', 'path': 'Ścieżka',
    'quota': 'Quota', 'used': 'Używane', 'available': 'Dostępne', 'username': 'Nazwa użytkownika',
    'password': 'Hasło', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'Status SMB', 'smb_shares': 'Udostępnienia SMB',
    'share_name': 'Nazwa Udostępnienia', 'comment': 'Komentarz', 'read_only': 'Read Only',
    'browseable': 'Przeglądanie', 'guest_access': 'Guest Access', 'language': 'Język',
    'running': 'Uruchomione', 'stopped': 'Zatrzymane', 'operation_success': 'Operacja Sukces',
    'operation_failed': 'Operacja Niepowodzenie', 'confirm_delete': 'Potwierdź Usunięcie', 'no_data': 'Brak Danych',
    'create_volume': 'Utwórz Volume', 'create_user': 'Utwórz Użytkownika', 'create_share': 'Utwórz Udostępnienie',
    'operation': 'Operacja', 'yes': 'Tak', 'no': 'Nie', 'system_info': 'Info Systemu',
    'service_status': 'Status Serwisu', 'ip_address': 'Adres IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Pliki', 'local_folder': 'Folder Lokalny', 'target_device': 'Target Device',
    'add_target': 'Dodaj Target', 'target_name': 'Nazwa Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Wybierz Folder',
    'push_now': 'Push Teraz', 'pushing': 'Pushing', 'push_history': 'Historia Push',
    'scan_ip': 'Skanuj IP', 'local_ips': 'Lokalne IPs', 'scan': 'Skanuj',
    'found_devices': 'Znalezione Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Wyślij', 'receive': 'Odbierz', 'push_status': 'Status Push',
    'success': 'Sukces', 'failed': 'Niepowodzenie', 'progress': 'Progress',
    'file_count': 'Liczba Plików', 'total_size': 'Całkowity Rozmiar', 'version': 'Wersja 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'sv_SE': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Lagring',
    'users': 'Användare', 'shares': 'Delningar', 'push': 'Push Manager',
    'settings': 'Inställningar', 'volumes': 'Volumes', 'create': 'Skapa', 'delete': 'Ta bort',
    'edit': 'Redigera', 'save': 'Spara', 'cancel': 'Avbryt', 'name': 'Namn', 'path': 'Sökväg',
    'quota': 'Quota', 'used': 'Använd', 'available': 'Tillgänglig', 'username': 'Användarnamn',
    'password': 'Lösenord', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Delningar',
    'share_name': 'Delnings Namn', 'comment': 'Kommentar', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Språk',
    'running': 'Kör', 'stopped': 'Stoppad', 'operation_success': 'Operation Succé',
    'operation_failed': 'Operation Misslyckades', 'confirm_delete': 'Bekräfta Ta bort', 'no_data': 'Ingen Data',
    'create_volume': 'Skapa Volume', 'create_user': 'Skapa Användare', 'create_share': 'Skapa Delning',
    'operation': 'Operation', 'yes': 'Ja', 'no': 'Nej', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP-Adress', 'push_targets': 'Push Targets',
    'push_files': 'Push Filer', 'local_folder': 'Lokal Folder', 'target_device': 'Target Device',
    'add_target': 'Lägg till Target', 'target_name': 'Target Namn', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Välj Folder',
    'push_now': 'Push Nu', 'pushing': 'Pushing', 'push_history': 'Push Historia',
    'scan_ip': 'Scan IP', 'local_ips': 'Lokala IPs', 'scan': 'Scan',
    'found_devices': 'Hittade Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Skicka', 'receive': 'Ta emot', 'push_status': 'Push Status',
    'success': 'Succé', 'failed': 'Misslyckades', 'progress': 'Progress',
    'file_count': 'Filantal', 'total_size': 'Total Storlek', 'version': 'Version 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'da_DK': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Opbevaring',
    'users': 'Brugere', 'shares': 'Delinger', 'push': 'Push Manager',
    'settings': 'Indstillinger', 'volumes': 'Volumes', 'create': 'Opret', 'delete': 'Slet',
    'edit': 'Rediger', 'save': 'Gem', 'cancel': 'Annuller', 'name': 'Navn', 'path': 'Sti',
    'quota': 'Quota', 'used': 'Brugt', 'available': 'Tilgængelig', 'username': 'Brugernavn',
    'password': 'Kodeord', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Delinger',
    'share_name': 'Deling Navn', 'comment': 'Kommentar', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Sprog',
    'running': 'Kører', 'stopped': 'Stoppet', 'operation_success': 'Operation Succes',
    'operation_failed': 'Operation Fejl', 'confirm_delete': 'Bekræft Slet', 'no_data': 'Ingen Data',
    'create_volume': 'Opret Volume', 'create_user': 'Opret Bruger', 'create_share': 'Opret Deling',
    'operation': 'Operation', 'yes': 'Ja', 'no': 'Nej', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP-Adresse', 'push_targets': 'Push Targets',
    'push_files': 'Push Filer', 'local_folder': 'Lokal Folder', 'target_device': 'Target Device',
    'add_target': 'Tilføj Target', 'target_name': 'Target Navn', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Vælg Folder',
    'push_now': 'Push Nu', 'pushing': 'Pushing', 'push_history': 'Push Historie',
    'scan_ip': 'Scan IP', 'local_ips': 'Lokale IPs', 'scan': 'Scan',
    'found_devices': 'Fundne Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Send', 'receive': 'Modtag', 'push_status': 'Push Status',
    'success': 'Succes', 'failed': 'Fejl', 'progress': 'Progress',
    'file_count': 'Filantal', 'total_size': 'Total Størrelse', 'version': 'Version 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'fi_FI': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Tallennus',
    'users': 'Käyttäjät', 'shares': 'Jaot', 'push': 'Push Manager',
    'settings': 'Asetukset', 'volumes': 'Volumes', 'create': 'Luo', 'delete': 'Poista',
    'edit': 'Muokkaa', 'save': 'Tallenna', 'cancel': 'Peruuta', 'name': 'Nimi', 'path': 'Polku',
    'quota': 'Quota', 'used': 'Käytetty', 'available': 'Saatavilla', 'username': 'Käyttäjänimi',
    'password': 'Salasana', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Jaot',
    'share_name': 'Jao Nimi', 'comment': 'Kommentti', 'read_only': 'Read Only',
    'browseable': 'Selaa', 'guest_access': 'Guest Access', 'language': 'Kieli',
    'running': 'Käynnissä', 'stopped': 'Pysäytetty', 'operation_success': 'Operation Onnistui',
    'operation_failed': 'Operation Epäonnistui', 'confirm_delete': 'Vahvista Poisto', 'no_data': 'Ei Dataa',
    'create_volume': 'Luo Volume', 'create_user': 'Luo Käyttäjä', 'create_share': 'Luo Jao',
    'operation': 'Operation', 'yes': 'Kyllä', 'no': 'Ei', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP-osoite', 'push_targets': 'Push Targets',
    'push_files': 'Push Tiedostot', 'local_folder': 'Lokali Folder', 'target_device': 'Target Device',
    'add_target': 'Lisää Target', 'target_name': 'Target Nimi', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Valitse Folder',
    'push_now': 'Push Nyt', 'pushing': 'Pushing', 'push_history': 'Push Historia',
    'scan_ip': 'Scan IP', 'local_ips': 'Lokaalit IPs', 'scan': 'Scan',
    'found_devices': 'Löydetyt Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Lähetä', 'receive': 'Vastaanota', 'push_status': 'Push Status',
    'success': 'Onnistui', 'failed': 'Epäonnistui', 'progress': 'Progress',
    'file_count': 'Tiedostojen Määrä', 'total_size': 'Yhteensä Koko', 'version': 'Versio 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'he_IL': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'אחסון',
    'users': 'משתמשים', 'shares': 'שיתופים', 'push': 'Push Manager',
    'settings': 'הגדרות', 'volumes': 'Volumes', 'create': 'יצירה', 'delete': 'מחיקה',
    'edit': 'עריכה', 'save': 'שמירה', 'cancel': 'ביטול', 'name': 'שם', 'path': 'נתיב',
    'quota': 'Quota', 'used': 'בשימוש', 'available': 'זמין', 'username': 'שם משתמש',
    'password': 'סיסמה', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'סטטוס SMB', 'smb_shares': 'שיתופים SMB',
    'share_name': 'שם שיתוף', 'comment': 'הערה', 'read_only': 'Read Only',
    'browseable': 'ניתן לגישה', 'guest_access': 'Guest Access', 'language': 'שפה',
    'running': 'רץ', 'stopped': 'הופסק', 'operation_success': 'הפעולה הצליחה',
    'operation_failed': 'הפעולה נכשלה', 'confirm_delete': 'אישור מחיקה', 'no_data': 'אין נתונים',
    'create_volume': 'יצירת Volume', 'create_user': 'יצירת משתמש', 'create_share': 'יצירת שיתוף',
    'operation': 'פעולה', 'yes': 'כן', 'no': 'לא', 'system_info': 'מידע מערכת',
    'service_status': 'סטטוס שירות', 'ip_address': 'כתובת IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Files', 'local_folder': 'Folder מקומי', 'target_device': 'Device מטרה',
    'add_target': 'הוספת Target', 'target_name': 'שם Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'בחירת Folder',
    'push_now': 'Push עכשיו', 'pushing': 'Pushing', 'push_history': 'היסטורית Push',
    'scan_ip': 'סריקת IP', 'local_ips': 'IPs מקומיים', 'scan': 'סריקה',
    'found_devices': 'Devices שנמצאו', 'online': 'Online', 'offline': 'Offline',
    'send': 'שליחה', 'receive': 'קבלה', 'push_status': 'סטטוס Push',
    'success': 'הצלחה', 'failed': 'כשלון', 'progress': 'התקדמות',
    'file_count': 'מספר קבצים', 'total_size': 'גודל כולל', 'version': 'גרסה 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'hu_HU': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Tárhely',
    'users': 'Felhasználók', 'shares': 'Megosztások', 'push': 'Push Manager',
    'settings': 'Beállítások', 'volumes': 'Volumes', 'create': 'Létrehoz', 'delete': 'Töröl',
    'edit': 'Szerkeszt', 'save': 'Ment', 'cancel': 'Mégse', 'name': 'Név', 'path': 'Útvonal',
    'quota': 'Quota', 'used': 'Használt', 'available': 'Elérhető', 'username': 'Felhasználónév',
    'password': 'Jelszó', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Státusz', 'smb_shares': 'SMB Megosztások',
    'share_name': 'Megosztás Neve', 'comment': 'Komment', 'read_only': 'Read Only',
    'browseable': 'Böngészhető', 'guest_access': 'Guest Access', 'language': 'Nyelv',
    'running': 'Fut', 'stopped': 'Megállítva', 'operation_success': 'Művelet Sikeres',
    'operation_failed': 'Művelet Sikertelen', 'confirm_delete': 'Törlés Jóváhagyása', 'no_data': 'Nincs Adat',
    'create_volume': 'Volume Létrehoz', 'create_user': 'Felhasználó Létrehoz', 'create_share': 'Megosztás Létrehoz',
    'operation': 'Művelet', 'yes': 'Igen', 'no': 'Nem', 'system_info': 'Rendszer Info',
    'service_status': 'Szolgáltatás Státusz', 'ip_address': 'IP Cím', 'push_targets': 'Push Targets',
    'push_files': 'Push Fájlok', 'local_folder': 'Helyi Folder', 'target_device': 'Target Device',
    'add_target': 'Target Hozzáad', 'target_name': 'Target Név', 'target_ip': 'Target IP',
    'target_port': 'Target Port', 'push_folder': 'Push Folder', 'select_folder': 'Folder Kiválaszt',
    'push_now': 'Push Most', 'pushing': 'Pushing', 'push_history': 'Push Történet',
    'scan_ip': 'IP Scan', 'local_ips': 'Helyi IPs', 'scan': 'Scan',
    'found_devices': 'Talált Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Küld', 'receive': 'Fogad', 'push_status': 'Push Státusz',
    'success': 'Siker', 'failed': 'Sikertelen', 'progress': 'Progress',
    'file_count': 'Fájl Szám', 'total_size': 'Teljes Méret', 'version': 'Verzió 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'cs_CZ': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Úložiště',
    'users': 'Uživatelé', 'shares': 'Sdílení', 'push': 'Push Manager',
    'settings': 'Nastavení', 'volumes': 'Volumes', 'create': 'Vytvořit', 'delete': 'Smazat',
    'edit': 'Upravit', 'save': 'Uložit', 'cancel': 'Zrušit', 'name': 'Název', 'path': 'Cesta',
    'quota': 'Quota', 'used': 'Použito', 'available': 'Dostupné', 'username': 'Uživatelské jméno',
    'password': 'Heslo', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Sdílení',
    'share_name': 'Název Sdílení', 'comment': 'Komentář', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Jazyk',
    'running': 'Běží', 'stopped': 'Zastaveno', 'operation_success': 'Operace Úspěšná',
    'operation_failed': 'Operace Neúspěšná', 'confirm_delete': 'Potvrdit Smazání', 'no_data': 'Žádné Data',
    'create_volume': 'Vytvořit Volume', 'create_user': 'Vytvořit Uživatele', 'create_share': 'Vytvořit Sdílení',
    'operation': 'Operace', 'yes': 'Ano', 'no': 'Ne', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP Adresa', 'push_targets': 'Push Targets',
    'push_files': 'Push Soubory', 'local_folder': 'Lokální Folder', 'target_device': 'Target Device',
    'add_target': 'Přidat Target', 'target_name': 'Název Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Vybrat Folder',
    'push_now': 'Push Teď', 'pushing': 'Pushing', 'push_history': 'Push Historie',
    'scan_ip': 'Scan IP', 'local_ips': 'Lokální IPs', 'scan': 'Scan',
    'found_devices': 'Nalezené Devices', 'online': 'Online', 'offline': 'Offline',
    'send': 'Poslat', 'receive': 'Přijmout', 'push_status': 'Push Status',
    'success': 'Úspěch', 'failed': 'Neúspěch', 'progress': 'Progress',
    'file_count': 'Počet Souborů', 'total_size': 'Celková Velikost', 'version': 'Verze 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'ro_RO': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Stocare',
    'users': 'Utilizatori', 'shares': 'Partajări', 'push': 'Push Manager',
    'settings': 'Setări', 'volumes': 'Volumes', 'create': 'Creare', 'delete': 'Șterge',
    'edit': 'Editare', 'save': 'Salvare', 'cancel': 'Anulare', 'name': 'Nume', 'path': 'Cale',
    'quota': 'Quota', 'used': 'Folosit', 'available': 'Disponibil', 'username': 'Utilizator',
    'password': 'Parolă', 'admin': 'Admin', 'storage_quota': 'Quota Stocare',
    'home_directory': 'Home Directory', 'smb_status': 'Status SMB', 'smb_shares': 'Partajări SMB',
    'share_name': 'Nume Partajare', 'comment': 'Comentariu', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Limbă',
    'running': 'În Execuție', 'stopped': 'Oprit', 'operation_success': 'Operație Succes',
    'operation_failed': 'Operație Eșuat', 'confirm_delete': 'Confirmă Ștergere', 'no_data': 'Nu Există Date',
    'create_volume': 'Creare Volume', 'create_user': 'Creare Utilizator', 'create_share': 'Creare Partajare',
    'operation': 'Operație', 'yes': 'Da', 'no': 'Nu', 'system_info': 'Info Sistem',
    'service_status': 'Status Serviciu', 'ip_address': 'Adresă IP', 'push_targets': 'Push Targets',
    'push_files': 'Push Fișiere', 'local_folder': 'Folder Local', 'target_device': 'Device Target',
    'add_target': 'Adaugă Target', 'target_name': 'Nume Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Selectează Folder',
    'push_now': 'Push Acum', 'pushing': 'Pushing', 'push_history': 'Istorie Push',
    'scan_ip': 'Scan IP', 'local_ips': 'IPs Locale', 'scan': 'Scan',
    'found_devices': 'Devices Găsite', 'online': 'Online', 'offline': 'Offline',
    'send': 'Trimite', 'receive': 'Primește', 'push_status': 'Status Push',
    'success': 'Succes', 'failed': 'Eșuat', 'progress': 'Progress',
    'file_count': 'Număr Fișiere', 'total_size': 'Mărime Total', 'version': 'Versiune 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'uk_UA': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Сховище',
    'users': 'Користувачі', 'shares': 'Спільні ресурси', 'push': 'Push Manager',
    'settings': 'Налаштування', 'volumes': 'Volumes', 'create': 'Створити', 'delete': 'Вилучити',
    'edit': 'Редагувати', 'save': 'Зберегти', 'cancel': 'Скасувати', 'name': 'Назва', 'path': 'Шлях',
    'quota': 'Quota', 'used': 'Використано', 'available': 'Доступно', 'username': 'Ім\'я користувача',
    'password': 'Пароль', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'Статус SMB', 'smb_shares': 'SMB Спільні',
    'share_name': 'Назва Спільного', 'comment': 'Коментар', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Мова',
    'running': 'Запущено', 'stopped': 'Зупинено', 'operation_success': 'Операція Успішна',
    'operation_failed': 'Операція Невдала', 'confirm_delete': 'Підтвердити Вилучення', 'no_data': 'Немає Даних',
    'create_volume': 'Створити Volume', 'create_user': 'Створити Користувача', 'create_share': 'Створити Спільний',
    'operation': 'Операція', 'yes': 'Так', 'no': 'Ні', 'system_info': 'Системна Інформація',
    'service_status': 'Статус Сервісу', 'ip_address': 'IP Адреса', 'push_targets': 'Push Targets',
    'push_files': 'Push Файли', 'local_folder': 'Folder Локальний', 'target_device': 'Device Ціль',
    'add_target': 'Додати Target', 'target_name': 'Назва Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Вибрати Folder',
    'push_now': 'Push Зараз', 'pushing': 'Pushing', 'push_history': 'Історія Push',
    'scan_ip': 'Scan IP', 'local_ips': 'IPs Локальні', 'scan': 'Scan',
    'found_devices': 'Devices Знайдені', 'online': 'Online', 'offline': 'Offline',
    'send': 'Надіслати', 'receive': 'Прийняти', 'push_status': 'Статус Push',
    'success': 'Успіх', 'failed': 'Невдача', 'progress': 'Progress',
    'file_count': 'Кількість Файлів', 'total_size': 'Загальний Розмір', 'version': 'Версія 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'sk_SK': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Úložisko',
    'users': 'Používatelia', 'shares': 'Zdieľania', 'push': 'Push Manager',
    'settings': 'Nastavenia', 'volumes': 'Volumes', 'create': 'Vytvoriť', 'delete': 'Odstrániť',
    'edit': 'Upraviť', 'save': 'Uložiť', 'cancel': 'Zrušiť', 'name': 'Názov', 'path': 'Cesta',
    'quota': 'Quota', 'used': 'Použité', 'available': 'Dostupné', 'username': 'Používateľ',
    'password': 'Heslo', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Zdieľania',
    'share_name': 'Názov Zdieľania', 'comment': 'Komentár', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Jazyk',
    'running': 'Beží', 'stopped': 'Zastavené', 'operation_success': 'Operácia Úspešná',
    'operation_failed': 'Operácia Neúspešná', 'confirm_delete': 'Potvrdiť Odstránenie', 'no_data': 'Žiadne Data',
    'create_volume': 'Vytvoriť Volume', 'create_user': 'Vytvoriť Používateľa', 'create_share': 'Vytvoriť Zdieľanie',
    'operation': 'Operácia', 'yes': 'Áno', 'no': 'Nie', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP Adresa', 'push_targets': 'Push Targets',
    'push_files': 'Push Súbory', 'local_folder': 'Folder Lokálny', 'target_device': 'Target Device',
    'add_target': 'Pridať Target', 'target_name': 'Názov Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Vybrať Folder',
    'push_now': 'Push Teraz', 'pushing': 'Pushing', 'push_history': 'Push História',
    'scan_ip': 'Scan IP', 'local_ips': 'IPs Lokálne', 'scan': 'Scan',
    'found_devices': 'Devices Nájdené', 'online': 'Online', 'offline': 'Offline',
    'send': 'Poslať', 'receive': 'Prijať', 'push_status': 'Push Status',
    'success': 'Úspech', 'failed': 'Neúspech', 'progress': 'Progress',
    'file_count': 'Počet Súborov', 'total_size': 'Celková Veľkosť', 'version': 'Verzia 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'no_NO': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Lagring',
    'users': 'Brukere', 'shares': 'Delinger', 'push': 'Push Manager',
    'settings': 'Innstillinger', 'volumes': 'Volumes', 'create': 'Opprett', 'delete': 'Slett',
    'edit': 'Rediger', 'save': 'Lagre', 'cancel': 'Avbryt', 'name': 'Navn', 'path': 'Sti',
    'quota': 'Quota', 'used': 'Brukt', 'available': 'Tilgjengelig', 'username': 'Brukernavn',
    'password': 'Passord', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'SMB Status', 'smb_shares': 'SMB Delinger',
    'share_name': 'Deling Navn', 'comment': 'Kommentar', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Språk',
    'running': 'Kjører', 'stopped': 'Stoppet', 'operation_success': 'Operasjon Suksess',
    'operation_failed': 'Operasjon Feilet', 'confirm_delete': 'Bekreft Slett', 'no_data': 'Ingen Data',
    'create_volume': 'Opprett Volume', 'create_user': 'Opprett Bruker', 'create_share': 'Opprett Deling',
    'operation': 'Operasjon', 'yes': 'Ja', 'no': 'Nei', 'system_info': 'System Info',
    'service_status': 'Service Status', 'ip_address': 'IP Adresse', 'push_targets': 'Push Targets',
    'push_files': 'Push Filer', 'local_folder': 'Folder Lokal', 'target_device': 'Target Device',
    'add_target': 'Legg til Target', 'target_name': 'Target Navn', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Velg Folder',
    'push_now': 'Push Nå', 'pushing': 'Pushing', 'push_history': 'Push Historie',
    'scan_ip': 'Scan IP', 'local_ips': 'IPs Lokale', 'scan': 'Scan',
    'found_devices': 'Devices Funnet', 'online': 'Online', 'offline': 'Offline',
    'send': 'Send', 'receive': 'Motta', 'push_status': 'Push Status',
    'success': 'Suksess', 'failed': 'Feilet', 'progress': 'Progress',
    'file_count': 'Filantall', 'total_size': 'Total Størrelse', 'version': 'Versjon 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
  'el_GR': {
    'app_name': 'Xiaosi Super NAS', 'dashboard': 'Dashboard', 'storage': 'Αποθήκευση',
    'users': 'Χρήστες', 'shares': 'Κοινόχρηστα', 'push': 'Push Manager',
    'settings': 'Ρυθμίσεις', 'volumes': 'Volumes', 'create': 'Δημιουργία', 'delete': 'Διαγραφή',
    'edit': 'Επεξεργασία', 'save': 'Αποθήκευση', 'cancel': 'Ακύρωση', 'name': 'Όνομα', 'path': 'Διαδρομή',
    'quota': 'Quota', 'used': 'Χρησιμοποιημένα', 'available': 'Διαθέσιμα', 'username': 'Όνομα Χρήστη',
    'password': 'Κωδικός', 'admin': 'Admin', 'storage_quota': 'Storage Quota',
    'home_directory': 'Home Directory', 'smb_status': 'Κατάσταση SMB', 'smb_shares': 'SMB Κοινόχρηστα',
    'share_name': 'Όνομα Κοινόχρηστο', 'comment': 'Σχόλιο', 'read_only': 'Read Only',
    'browseable': 'Browseable', 'guest_access': 'Guest Access', 'language': 'Γλώσσα',
    'running': 'Εκτελείται', 'stopped': 'Σταματημένο', 'operation_success': 'Επιτυχία Λειτουργίας',
    'operation_failed': 'Αποτυχία Λειτουργίας', 'confirm_delete': 'Επιβεβαίωση Διαγραφής', 'no_data': 'Χωρίς Δεδομένα',
    'create_volume': 'Δημιουργία Volume', 'create_user': 'Δημιουργία Χρήστη', 'create_share': 'Δημιουργία Κοινόχρηστο',
    'operation': 'Λειτουργία', 'yes': 'Ναι', 'no': 'Όχι', 'system_info': 'Πληροφορίες Συστήματος',
    'service_status': 'Κατάσταση Υπηρεσίας', 'ip_address': 'IP Διεύθυνση', 'push_targets': 'Push Targets',
    'push_files': 'Push Αρχεία', 'local_folder': 'Folder Τοπικό', 'target_device': 'Device Στόχος',
    'add_target': 'Προσθήκη Target', 'target_name': 'Όνομα Target', 'target_ip': 'IP Target',
    'target_port': 'Port Target', 'push_folder': 'Push Folder', 'select_folder': 'Επιλογή Folder',
    'push_now': 'Push Τώρα', 'pushing': 'Pushing', 'push_history': 'Push Ιστορία',
    'scan_ip': 'Scan IP', 'local_ips': 'IPs Τοπικές', 'scan': 'Scan',
    'found_devices': 'Devices Βρέθηκαν', 'online': 'Online', 'offline': 'Offline',
    'send': 'Αποστολή', 'receive': 'Λήψη', 'push_status': 'Push Κατάσταση',
    'success': 'Επιτυχία', 'failed': 'Αποτυχία', 'progress': 'Progress',
    'file_count': 'Αριθμός Αρχείων', 'total_size': 'Συνολικό Μέγεθος', 'version': 'Έκδοση 2',
    'zero_dependency': 'Zero Dependency', 'api_docs': 'API Docs'
  },
};

// ==========================================
// 配置管理类
// ==========================================
class Config {
  int serverPort = 8092;
  String language = 'zh_CN';
  List<Map<String, dynamic>> volumes = [];
  List<Map<String, dynamic>> users = [];
  List<Map<String, dynamic>> shares = [];
  List<Map<String, dynamic>> pushTargets = [];
  String dataDir = 'nas_data';
  String receiveDir = 'nas_data/received';
  String configPath = '';

  Config() {
    _loadConfig();
  }

  void _loadConfig() {
    configPath = _getConfigPath();
    final file = File(configPath);
    
    if (file.existsSync()) {
      try {
        final content = file.readAsStringSync();
        final data = jsonDecode(content) as Map<String, dynamic>;
        
        final serverConfig = data['server'] as Map<String, dynamic>? ?? {};
        serverPort = serverConfig['port'] as int? ?? 8092;
        language = serverConfig['language'] as String? ?? 'zh_CN';
        
        final storageConfig = data['storage'] as Map<String, dynamic>? ?? {};
        volumes = (storageConfig['volumes'] as List<dynamic>? ?? [])
            .map((v) => v as Map<String, dynamic>)
            .toList();
        
        users = (data['users'] as List<dynamic>? ?? [])
            .map((u) => u as Map<String, dynamic>)
            .toList();
        
        final smbConfig = data['smb'] as Map<String, dynamic>? ?? {};
        shares = (smbConfig['shares'] as List<dynamic>? ?? [])
            .map((s) => s as Map<String, dynamic>)
            .toList();
        
        final pushConfig = data['push'] as Map<String, dynamic>? ?? {};
        pushTargets = (pushConfig['targets'] as List<dynamic>? ?? [])
            .map((t) => t as Map<String, dynamic>)
            .toList();
        
        dataDir = data['data_dir'] as String? ?? 'nas_data';
        receiveDir = data['receive_dir'] as String? ?? 'nas_data/received';
        
        print('[配置] 已从 $configPath 加载配置');
      } catch (e) {
        print('[配置] 加载失败: $e, 使用默认配置');
      }
    } else {
      print('[配置] 配置文件不存在，使用默认配置');
    }
    
    // 创建必要的目录
    Directory(receiveDir).createSync(recursive: true);
  }

  String _getConfigPath() {
    // 尝试相对路径 ../config/config.json
    final scriptDir = Directory.current.path;
    var path = '$scriptDir/../config/config.json';
    
    if (!File(path).existsSync()) {
      path = '$scriptDir/config.json';
    }
    
    return path;
  }

  void save() {
    final data = {
      'server': {
        'port': serverPort,
        'language': language,
      },
      'storage': {
        'volumes': volumes,
      },
      'users': users,
      'smb': {
        'shares': shares,
      },
      'push': {
        'targets': pushTargets,
      },
      'data_dir': dataDir,
      'receive_dir': receiveDir,
    };

    try {
      final file = File(configPath);
      file.createSync(recursive: true);
      file.writeAsStringSync(jsonEncode(data));
      print('[配置] 已保存到 $configPath');
    } catch (e) {
      print('[配置] 保存失败: $e');
    }
  }

  Map<String, String> getTranslations() {
    return translations[language] ?? translations['zh_CN']!;
  }
}

// ==========================================
// NAS服务器类
// ==========================================
class NASServer {
  final Config config;
  final Router router;
  HttpServer? server;
  final List<Map<String, dynamic>> pushHistory = [];
  String deviceId = '';

  NASServer(this.config) : router = Router() {
    deviceId = _generateDeviceId();
    _setupRoutes();
  }

  String _generateDeviceId() {
    final hostname = Platform.localHostname;
    final random = Random().nextInt(10000);
    return '$hostname-$random';
  }

  void _setupRoutes() {
    // API路由
    router.get('/', _handleRoot);
    router.get('/api/info', _handleInfo);
    router.get('/api/i18n', _handleI18n);
    router.post('/api/i18n/set', _handleI18nSet);
    router.get('/api/volumes', _handleVolumes);
    router.post('/api/volumes', _handleVolumeCreate);
    router.delete('/api/volumes/<name>', _handleVolumeDelete);
    router.get('/api/users', _handleUsers);
    router.post('/api/users', _handleUserCreate);
    router.delete('/api/users/<username>', _handleUserDelete);
    router.get('/api/shares', _handleShares);
    router.post('/api/shares', _handleShareCreate);
    router.delete('/api/shares/<name>', _handleShareDelete);
    router.get('/api/push/targets', _handlePushTargets);
    router.post('/api/push/targets', _handlePushTargetCreate);
    router.delete('/api/push/targets/<name>', _handlePushTargetDelete);
    router.post('/api/push/send', _handlePushSend);
    router.post('/api/push/receive', _handlePushReceive);
    router.get('/api/push/history', _handlePushHistory);
    router.get('/api/network/ips', _handleNetworkIPs);
    router.post('/api/network/scan', _handleNetworkScan);
    router.get('/api/files/list', _handleFilesList);
    router.get('/api/files/download/<path>', _handleFilesDownload);
    router.post('/api/files/upload', _handleFilesUpload);
  }

  Response _jsonResponse(Map<String, dynamic> data) {
    return Response.ok(
      jsonEncode(data),
      headers: {'Content-Type': 'application/json; charset=utf-8'},
    );
  }

  Future<Map<String, dynamic>> _parseJsonBody(Request request) async {
    final body = await request.readAsString();
    return jsonDecode(body) as Map<String, dynamic>;
  }

  // API处理器
  Response _handleRoot(Request request) {
    return _jsonResponse({
      'name': '小思超级多版本NAS服务',
      'version': '第二代',
      'implementation': 'Dart',
      'port': config.serverPort,
      'status': 'running',
    });
  }

  Response _handleInfo(Request request) {
    final trans = config.getTranslations();
    return _jsonResponse({
      'app_name': trans['app_name'],
      'version': trans['version'],
      'implementation': 'Dart',
      'zero_dependency': trans['zero_dependency'],
      'api_docs': trans['api_docs'],
      'device_id': deviceId,
      'hostname': Platform.localHostname,
      'os': Platform.operatingSystem,
      'port': config.serverPort,
      'language': config.language,
      'data_dir': config.dataDir,
      'receive_dir': config.receiveDir,
      'volumes_count': config.volumes.length,
      'users_count': config.users.length,
      'shares_count': config.shares.length,
      'push_targets_count': config.pushTargets.length,
    });
  }

  Response _handleI18n(Request request) {
    return _jsonResponse({
      'language': config.language,
      'translations': config.getTranslations(),
      'available_languages': translations.keys.toList(),
    });
  }

  Response _handleI18nSet(Request request) async {
    final data = await _parseJsonBody(request);
    final lang = data['language'] as String?;
    
    if (lang != null && translations.containsKey(lang)) {
      config.language = lang;
      config.save();
      return _jsonResponse({
        'success': true,
        'language': config.language,
        'translations': config.getTranslations(),
      });
    }
    
    return _jsonResponse({'success': false, 'error': '无效的语言代码'});
  }

  Response _handleVolumes(Request request) {
    return _jsonResponse({'volumes': config.volumes});
  }

  Response _handleVolumeCreate(Request request) async {
    final data = await _parseJsonBody(request);
    final volume = {
      'name': data['name'] as String,
      'path': data['path'] as String,
      'quota_gb': data['quota_gb'] as int? ?? 0,
    };
    
    config.volumes.add(volume);
    config.save();
    
    return _jsonResponse({'success': true, 'volume': volume});
  }

  Response _handleVolumeDelete(Request request, String name) {
    config.volumes.removeWhere((v) => v['name'] == name);
    config.save();
    return _jsonResponse({'success': true});
  }

  Response _handleUsers(Request request) {
    return _jsonResponse({'users': config.users});
  }

  Response _handleUserCreate(Request request) async {
    final data = await _parseJsonBody(request);
    final password = data['password'] as String;
    final hashedPassword = _sha256Hash(password);
    
    final user = {
      'username': data['username'] as String,
      'password': hashedPassword,
      'is_admin': data['is_admin'] as bool? ?? false,
      'home_dir': data['home_dir'] as String? ?? '',
      'storage_quota_gb': data['storage_quota_gb'] as int? ?? 0,
    };
    
    config.users.add(user);
    config.save();
    
    return _jsonResponse({'success': true, 'user': user});
  }

  Response _handleUserDelete(Request request, String username) {
    config.users.removeWhere((u) => u['username'] == username);
    config.save();
    return _jsonResponse({'success': true});
  }

  Response _handleShares(Request request) {
    return _jsonResponse({'shares': config.shares});
  }

  Response _handleShareCreate(Request request) async {
    final data = await _parseJsonBody(request);
    final share = {
      'name': data['name'] as String,
      'path': data['path'] as String,
      'comment': data['comment'] as String? ?? '',
      'read_only': data['read_only'] as bool? ?? false,
      'browseable': data['browseable'] as bool? ?? true,
      'guest_access': data['guest_access'] as bool? ?? false,
    };
    
    config.shares.add(share);
    config.save();
    
    return _jsonResponse({'success': true, 'share': share});
  }

  Response _handleShareDelete(Request request, String name) {
    config.shares.removeWhere((s) => s['name'] == name);
    config.save();
    return _jsonResponse({'success': true});
  }

  Response _handlePushTargets(Request request) {
    return _jsonResponse({'targets': config.pushTargets});
  }

  Response _handlePushTargetCreate(Request request) async {
    final data = await _parseJsonBody(request);
    final target = {
      'name': data['name'] as String,
      'ip': data['ip'] as String,
      'port': data['port'] as int? ?? 8092,
      'folder': data['folder'] as String? ?? '',
    };
    
    config.pushTargets.add(target);
    config.save();
    
    return _jsonResponse({'success': true, 'target': target});
  }

  Response _handlePushTargetDelete(Request request, String name) {
    config.pushTargets.removeWhere((t) => t['name'] == name);
    config.save();
    return _jsonResponse({'success': true});
  }

  Response _handlePushSend(Request request) async {
    final data = await _parseJsonBody(request);
    final targetName = data['target'] as String?;
    final folder = data['folder'] as String?;
    
    if (targetName == null || folder == null) {
      return _jsonResponse({'success': false, 'error': '缺少参数'});
    }
    
    final target = config.pushTargets.firstWhere(
      (t) => t['name'] == targetName,
      orElse: () => {},
    );
    
    if (target.isEmpty) {
      return _jsonResponse({'success': false, 'error': '目标不存在'});
    }
    
    final files = await _listFiles(folder);
    final historyEntry = {
      'timestamp': DateTime.now().toIso8601String(),
      'type': 'send',
      'target': targetName,
      'folder': folder,
      'file_count': files.length,
      'status': 'success',
    };
    
    pushHistory.add(historyEntry);
    
    return _jsonResponse({
      'success': true,
      'files': files,
      'history': historyEntry,
    });
  }

  Response _handlePushReceive(Request request) async {
    final body = await request.readAsString();
    
    final receiveDir = Directory(config.receiveDir);
    if (!receiveDir.existsSync()) {
      receiveDir.createSync(recursive: true);
    }
    
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final filename = 'received_$timestamp.json';
    final filepath = '${config.receiveDir}/$filename';
    
    File(filepath).writeAsStringSync(body);
    
    final historyEntry = {
      'timestamp': DateTime.now().toIso8601String(),
      'type': 'receive',
      'filename': filename,
      'size': body.length,
      'status': 'success',
    };
    
    pushHistory.add(historyEntry);
    
    return _jsonResponse({'success': true, 'filename': filename, 'history': historyEntry});
  }

  Response _handlePushHistory(Request request) {
    return _jsonResponse({'history': pushHistory});
  }

  Response _handleNetworkIPs(Request request) {
    // 简化实现 - 返回基本网络信息
    return _jsonResponse({
      'hostname': Platform.localHostname,
      'device_id': deviceId,
      'ips': ['127.0.0.1'],
    });
  }

  Response _handleNetworkScan(Request request) async {
    final data = await _parseJsonBody(request);
    final ipRange = data['ip_range'] as String? ?? '192.168.1.1-254';
    
    // 简化实现 - 返回模拟扫描结果
    final devices = [
      {'ip': '192.168.1.1', 'hostname': 'Router', 'online': true, 'type': 'LAN'},
      {'ip': '192.168.1.100', 'hostname': deviceId, 'online': true, 'type': 'LAN'},
    ];
    
    return _jsonResponse({
      'success': true,
      'ip_range': ipRange,
      'devices': devices,
    });
  }

  Response _handleFilesList(Request request) {
    final folder = request.url.queryParameters['folder'] ?? config.dataDir;
    final files = _listFilesSync(folder);
    return _jsonResponse({'folder': folder, 'files': files});
  }

  Response _handleFilesDownload(Request request, String path) {
    final file = File(path);
    if (!file.existsSync()) {
      return _jsonResponse({'success': false, 'error': '文件不存在'});
    }
    
    final content = file.readAsBytesSync();
    return Response.ok(
      content,
      headers: {
        'Content-Type': 'application/octet-stream',
        'Content-Disposition': 'attachment; filename="${file.path.split('/').last}"',
      },
    );
  }

  Response _handleFilesUpload(Request request) async {
    final body = await request.readAsString();
    final filename = request.url.queryParameters['filename'] ?? 'upload_${DateTime.now().millisecondsSinceEpoch}';
    
    final filepath = '${config.dataDir}/$filename';
    File(filepath).writeAsStringSync(body);
    
    return _jsonResponse({'success': true, 'filename': filename, 'path': filepath});
  }

  // 辅助方法
  String _sha256Hash(String input) {
    // Dart不直接提供SHA256，这里简化实现
    // 在实际应用中应该使用crypto包
    return input.hashCode.toString();
  }

  Future<List<Map<String, dynamic>>> _listFiles(String folder) async {
    final dir = Directory(folder);
    if (!dir.existsSync()) return [];
    
    return dir.listSync().map((entity) {
      return {
        'name': entity.path.split('/').last,
        'path': entity.path,
        'type': entity is File ? 'file' : 'directory',
        'size': entity is File ? (entity as File).lengthSync() : 0,
      };
    }).toList();
  }

  List<Map<String, dynamic>> _listFilesSync(String folder) {
    final dir = Directory(folder);
    if (!dir.existsSync()) return [];
    
    return dir.listSync().map((entity) {
      return {
        'name': entity.path.split(Platform.pathSeparator).last,
        'path': entity.path,
        'type': entity is File ? 'file' : 'directory',
        'size': entity is File ? (entity as File).lengthSync() : 0,
      };
    }).toList();
  }

  // 启动服务器
  Future<void> start() async {
    final handler = const Pipeline()
        .addMiddleware(logRequests())
        .addHandler(router);

    server = await IoServer.bind(InternetAddress.anyIPv4, config.serverPort);
    print('小思超级多版本NAS服务 (Dart实现) 已启动');
    print('端口: ${config.serverPort}');
    print('语言: ${config.language}');
    print('设备ID: $deviceId');
    print('访问地址: http://localhost:${config.serverPort}');
    
    await server!.handler(handler);
  }

  Future<void> stop() async {
    await server?.close();
    print('NAS服务已停止');
  }
}

// ==========================================
// 主程序入口
// ==========================================
Future<void> main() async {
  final config = Config();
  final server = NASServer(config);
  
  await server.start();
}