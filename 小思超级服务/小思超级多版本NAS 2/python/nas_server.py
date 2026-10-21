"""
小思超级多版本NAS服务 - Python实现 (第二代)
基于http.server模块实现的完整REST API
零依赖方案 - 仅使用Python标准库
支持完整的存储管理、用户管理、SMB共享、文件推送、多语言支持
"""
import os
import sys
import json
import hashlib
import socket
import uuid
import time
import shutil
import threading
import platform
import subprocess
import re
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Tuple, Optional, Any

# ==========================================
# 多语言翻译 (28种语言)
# ==========================================
TRANSLATIONS = {
    "zh_CN": {
        "app_name": "小思超级NAS", "dashboard": "控制台", "storage": "存储管理",
        "users": "用户管理", "shares": "共享管理", "push": "推送管理",
        "settings": "设置", "volumes": "存储卷", "create": "创建", "delete": "删除",
        "edit": "编辑", "save": "保存", "cancel": "取消", "name": "名称", "path": "路径",
        "quota": "配额", "used": "已用", "available": "可用", "username": "用户名",
        "password": "密码", "admin": "管理员", "storage_quota": "存储配额",
        "home_directory": "主目录", "smb_status": "SMB状态", "smb_shares": "SMB共享",
        "share_name": "共享名称", "comment": "备注", "read_only": "只读",
        "browseable": "可浏览", "guest_access": "访客访问", "language": "语言",
        "running": "运行中", "stopped": "已停止", "operation_success": "操作成功",
        "operation_failed": "操作失败", "confirm_delete": "确认删除", "no_data": "暂无数据",
        "create_volume": "创建存储卷", "create_user": "创建用户", "create_share": "创建共享",
        "operation": "操作", "yes": "是", "no": "否", "system_info": "系统信息",
        "service_status": "服务状态", "ip_address": "IP地址", "push_targets": "推送目标",
        "push_files": "推送文件", "local_folder": "本地文件夹", "target_device": "目标设备",
        "add_target": "添加目标", "target_name": "目标名称", "target_ip": "目标IP",
        "target_port": "目标端口", "push_folder": "推送文件夹", "select_folder": "选择文件夹",
        "push_now": "立即推送", "pushing": "推送中", "push_history": "推送历史",
        "scan_ip": "扫描IP", "local_ips": "本机IP", "scan": "扫描",
        "found_devices": "发现设备", "online": "在线", "offline": "离线",
        "send": "发送", "receive": "接收", "push_status": "推送状态",
        "success": "成功", "failed": "失败", "progress": "进度",
        "file_count": "文件数", "total_size": "总大小", "version": "第二代",
        "zero_dependency": "零依赖", "api_docs": "API文档"
    },
    "zh_TW": {
        "app_name": "小思超級NAS", "dashboard": "控制台", "storage": "存儲管理",
        "users": "用戶管理", "shares": "共享管理", "push": "推送管理",
        "settings": "設置", "volumes": "存儲卷", "create": "創建", "delete": "刪除",
        "edit": "編輯", "save": "保存", "cancel": "取消", "name": "名稱", "path": "路徑",
        "quota": "配額", "used": "已用", "available": "可用", "username": "用戶名",
        "password": "密碼", "admin": "管理員", "storage_quota": "存儲配額",
        "home_directory": "主目錄", "smb_status": "SMB狀態", "smb_shares": "SMB共享",
        "share_name": "共享名稱", "comment": "備註", "read_only": "只讀",
        "browseable": "可瀏覽", "guest_access": "訪客訪問", "language": "語言",
        "running": "運行中", "stopped": "已停止", "operation_success": "操作成功",
        "operation_failed": "操作失敗", "confirm_delete": "確認刪除", "no_data": "暫無數據",
        "create_volume": "創建存儲卷", "create_user": "創建用戶", "create_share": "創建共享",
        "operation": "操作", "yes": "是", "no": "否", "system_info": "系統信息",
        "service_status": "服務狀態", "ip_address": "IP地址", "push_targets": "推送目標",
        "push_files": "推送文件", "local_folder": "本地文件夾", "target_device": "目標設備",
        "add_target": "添加目標", "target_name": "目標名稱", "target_ip": "目標IP",
        "target_port": "目標端口", "push_folder": "推送文件夾", "select_folder": "選擇文件夾",
        "push_now": "立即推送", "pushing": "推送中", "push_history": "推送歷史",
        "scan_ip": "掃描IP", "local_ips": "本機IP", "scan": "掃描",
        "found_devices": "發現設備", "online": "在線", "offline": "離線",
        "send": "發送", "receive": "接收", "push_status": "推送狀態",
        "success": "成功", "failed": "失敗", "progress": "進度",
        "file_count": "文件數", "total_size": "總大小", "version": "第二代",
        "zero_dependency": "零依賴", "api_docs": "API文檔"
    },
    "en_US": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Storage",
        "users": "Users", "shares": "Shares", "push": "Push Manager",
        "settings": "Settings", "volumes": "Volumes", "create": "Create", "delete": "Delete",
        "edit": "Edit", "save": "Save", "cancel": "Cancel", "name": "Name", "path": "Path",
        "quota": "Quota", "used": "Used", "available": "Available", "username": "Username",
        "password": "Password", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Shares",
        "share_name": "Share Name", "comment": "Comment", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Language",
        "running": "Running", "stopped": "Stopped", "operation_success": "Operation Success",
        "operation_failed": "Operation Failed", "confirm_delete": "Confirm Delete", "no_data": "No Data",
        "create_volume": "Create Volume", "create_user": "Create User", "create_share": "Create Share",
        "operation": "Operation", "yes": "Yes", "no": "No", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP Address", "push_targets": "Push Targets",
        "push_files": "Push Files", "local_folder": "Local Folder", "target_device": "Target Device",
        "add_target": "Add Target", "target_name": "Target Name", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Select Folder",
        "push_now": "Push Now", "pushing": "Pushing", "push_history": "Push History",
        "scan_ip": "Scan IP", "local_ips": "Local IPs", "scan": "Scan",
        "found_devices": "Found Devices", "online": "Online", "offline": "Offline",
        "send": "Send", "receive": "Receive", "push_status": "Push Status",
        "success": "Success", "failed": "Failed", "progress": "Progress",
        "file_count": "File Count", "total_size": "Total Size", "version": "Version 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "en_GB": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Storage",
        "users": "Users", "shares": "Shares", "push": "Push Manager",
        "settings": "Settings", "volumes": "Volumes", "create": "Create", "delete": "Delete",
        "edit": "Edit", "save": "Save", "cancel": "Cancel", "name": "Name", "path": "Path",
        "quota": "Quota", "used": "Used", "available": "Available", "username": "Username",
        "password": "Password", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Shares",
        "share_name": "Share Name", "comment": "Comment", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Language",
        "running": "Running", "stopped": "Stopped", "operation_success": "Operation Success",
        "operation_failed": "Operation Failed", "confirm_delete": "Confirm Delete", "no_data": "No Data",
        "create_volume": "Create Volume", "create_user": "Create User", "create_share": "Create Share",
        "operation": "Operation", "yes": "Yes", "no": "No", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP Address", "push_targets": "Push Targets",
        "push_files": "Push Files", "local_folder": "Local Folder", "target_device": "Target Device",
        "add_target": "Add Target", "target_name": "Target Name", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Select Folder",
        "push_now": "Push Now", "pushing": "Pushing", "push_history": "Push History",
        "scan_ip": "Scan IP", "local_ips": "Local IPs", "scan": "Scan",
        "found_devices": "Found Devices", "online": "Online", "offline": "Offline",
        "send": "Send", "receive": "Receive", "push_status": "Push Status",
        "success": "Success", "failed": "Failed", "progress": "Progress",
        "file_count": "File Count", "total_size": "Total Size", "version": "Version 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "ja_JP": {
        "app_name": "小思スーパーNAS", "dashboard": "ダッシュボード", "storage": "ストレージ",
        "users": "ユーザー", "shares": "共有", "push": "プッシュ管理",
        "settings": "設定", "volumes": "ボリューム", "create": "作成", "delete": "削除",
        "edit": "編集", "save": "保存", "cancel": "キャンセル", "name": "名前", "path": "パス",
        "quota": "クォータ", "used": "使用中", "available": "利用可能", "username": "ユーザー名",
        "password": "パスワード", "admin": "管理者", "storage_quota": "ストレージクォータ",
        "home_directory": "ホームディレクトリ", "smb_status": "SMB状態", "smb_shares": "SMB共有",
        "share_name": "共有名", "comment": "コメント", "read_only": "読み取り専用",
        "browseable": "参照可能", "guest_access": "ゲストアクセス", "language": "言語",
        "running": "実行中", "stopped": "停止中", "operation_success": "操作成功",
        "operation_failed": "操作失敗", "confirm_delete": "削除の確認", "no_data": "データなし",
        "create_volume": "ボリューム作成", "create_user": "ユーザー作成", "create_share": "共有作成",
        "operation": "操作", "yes": "はい", "no": "いいえ", "system_info": "システム情報",
        "service_status": "サービス状態", "ip_address": "IPアドレス", "push_targets": "プッシュ先",
        "push_files": "ファイル送信", "local_folder": "ローカルフォルダ", "target_device": "対象デバイス",
        "add_target": "対象を追加", "target_name": "対象名", "target_ip": "対象IP",
        "target_port": "対象ポート", "push_folder": "フォルダ送信", "select_folder": "フォルダ選択",
        "push_now": "今すぐ送信", "pushing": "送信中", "push_history": "送信履歴",
        "scan_ip": "IPスキャン", "local_ips": "ローカルIP", "scan": "スキャン",
        "found_devices": "発見デバイス", "online": "オンライン", "offline": "オフライン",
        "send": "送信", "receive": "受信", "push_status": "送信状態",
        "success": "成功", "failed": "失敗", "progress": "進捗",
        "file_count": "ファイル数", "total_size": "合計サイズ", "version": "第2世代",
        "zero_dependency": "ゼロ依存", "api_docs": "APIドキュメント"
    },
    "ko_KR": {
        "app_name": "小思 슈퍼 NAS", "dashboard": "대시보드", "storage": "저장소",
        "users": "사용자", "shares": "공유", "push": "推送 관리",
        "settings": "설정", "volumes": "볼륨", "create": "생성", "delete": "삭제",
        "edit": "편집", "save": "저장", "cancel": "취소", "name": "이름", "path": "경로",
        "quota": "할당량", "used": "사용", "available": "사용 가능", "username": "사용자 이름",
        "password": "비밀번호", "admin": "관리자", "storage_quota": "저장소 할당량",
        "home_directory": "홈 디렉토리", "smb_status": "SMB 상태", "smb_shares": "SMB 공유",
        "share_name": "공유 이름", "comment": "설명", "read_only": "읽기 전용",
        "browseable": "탐색 가능", "guest_access": "게스트 접근", "language": "언어",
        "running": "실행 중", "stopped": "중지됨", "operation_success": "작업 성공",
        "operation_failed": "작업 실패", "confirm_delete": "삭제 확인", "no_data": "데이터 없음",
        "create_volume": "볼륨 생성", "create_user": "사용자 생성", "create_share": "공유 생성",
        "operation": "작업", "yes": "예", "no": "아니오", "system_info": "시스템 정보",
        "service_status": "서비스 상태", "ip_address": "IP 주소", "push_targets": "推送 대상",
        "push_files": "파일推送", "local_folder": "로컬 폴더", "target_device": "대상 장치",
        "add_target": "대상 추가", "target_name": "대상 이름", "target_ip": "대상 IP",
        "target_port": "대상 포트", "push_folder": "폴더推送", "select_folder": "폴더 선택",
        "push_now": "즉시推送", "pushing": "推送 중", "push_history": "推送 기록",
        "scan_ip": "IP 스캔", "local_ips": "로컬 IP", "scan": "스캔",
        "found_devices": "발견 장치", "online": "온라인", "offline": "오프라인",
        "send": "보내기", "receive": "받기", "push_status": "推送 상태",
        "success": "성공", "failed": "실패", "progress": "진행률",
        "file_count": "파일 수", "total_size": "전체 크기", "version": "제2세대",
        "zero_dependency": "제로 의존성", "api_docs": "API 문서"
    },
    "de_DE": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Speicher",
        "users": "Benutzer", "shares": "Freigaben", "push": "Push Manager",
        "settings": "Einstellungen", "volumes": "Volumes", "create": "Erstellen", "delete": "Löschen",
        "edit": "Bearbeiten", "save": "Speichern", "cancel": "Abbrechen", "name": "Name", "path": "Pfad",
        "quota": "Quota", "used": "Verwendet", "available": "Verfügbar", "username": "Benutzername",
        "password": "Passwort", "admin": "Admin", "storage_quota": "Speicherquota",
        "home_directory": "Home-Verzeichnis", "smb_status": "SMB-Status", "smb_shares": "SMB-Freigaben",
        "share_name": "Freigabe-Name", "comment": "Kommentar", "read_only": "Read-Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Sprache",
        "running": "Laufend", "stopped": "Gestoppt", "operation_success": "Operation Erfolgreich",
        "operation_failed": "Operation Fehlgeschlagen", "confirm_delete": "Löschen Bestätigen", "no_data": "Keine Daten",
        "create_volume": "Volume Erstellen", "create_user": "Benutzer Erstellen", "create_share": "Freigabe Erstellen",
        "operation": "Operation", "yes": "Ja", "no": "Nein", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP-Adresse", "push_targets": "Push Targets",
        "push_files": "Push Dateien", "local_folder": "Lokaler Folder", "target_device": "Target Gerät",
        "add_target": "Target Hinzufügen", "target_name": "Target Name", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Folder Auswählen",
        "push_now": "Jetzt Push", "pushing": "Pushing", "push_history": "Push Historie",
        "scan_ip": "IP Scannen", "local_ips": "Lokale IPs", "scan": "Scannen",
        "found_devices": "Gefundene Geräte", "online": "Online", "offline": "Offline",
        "send": "Senden", "receive": "Empfangen", "push_status": "Push Status",
        "success": "Erfolg", "failed": "Fehlgeschlagen", "progress": "Fortschritt",
        "file_count": "Datei-Anzahl", "total_size": "Gesamt-Größe", "version": "Version 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "fr_FR": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Tableau de bord", "storage": "Stockage",
        "users": "Utilisateurs", "shares": "Partages", "push": "Gestion Push",
        "settings": "Paramètres", "volumes": "Volumes", "create": "Créer", "delete": "Supprimer",
        "edit": "Modifier", "save": "Sauvegarder", "cancel": "Annuler", "name": "Nom", "path": "Chemin",
        "quota": "Quota", "used": "Utilisé", "available": "Disponible", "username": "Nom d'utilisateur",
        "password": "Mot de passe", "admin": "Admin", "storage_quota": "Quota de Stockage",
        "home_directory": "Répertoire Home", "smb_status": "Statut SMB", "smb_shares": "Partages SMB",
        "share_name": "Nom du Partage", "comment": "Commentaire", "read_only": "Lecture Seule",
        "browseable": "Navigable", "guest_access": "Accès Invité", "language": "Langue",
        "running": "En cours", "stopped": "Arrêté", "operation_success": "Opération Réussie",
        "operation_failed": "Opération échouée", "confirm_delete": "Confirmer Suppression", "no_data": "Pas de Données",
        "create_volume": "Créer Volume", "create_user": "Créer Utilisateur", "create_share": "Créer Partage",
        "operation": "Opération", "yes": "Oui", "no": "Non", "system_info": "Info Système",
        "service_status": "Statut Service", "ip_address": "Adresse IP", "push_targets": "Push Targets",
        "push_files": "Push Fichiers", "local_folder": "Dossier Local", "target_device": "Appareil Cible",
        "add_target": "Ajouter Target", "target_name": "Nom du Target", "target_ip": "IP du Target",
        "target_port": "Port du Target", "push_folder": "Push Dossier", "select_folder": "Sélectionner Dossier",
        "push_now": "Pusher Maintenant", "pushing": "Push en cours", "push_history": "Historique Push",
        "scan_ip": "Scanner IP", "local_ips": "IPs Locales", "scan": "Scanner",
        "found_devices": "Appareils Trouvés", "online": "En ligne", "offline": "Hors ligne",
        "send": "Envoyer", "receive": "Recevoir", "push_status": "Statut Push",
        "success": "Succès", "failed": "échoué", "progress": "Progression",
        "file_count": "Nombre de Fichiers", "total_size": "Taille Totale", "version": "Version 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "es_ES": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Tablero", "storage": "Almacenamiento",
        "users": "Usuarios", "shares": "Compartidos", "push": "Gestión Push",
        "settings": "Configuración", "volumes": "Volúmenes", "create": "Crear", "delete": "Eliminar",
        "edit": "Editar", "save": "Guardar", "cancel": "Cancelar", "name": "Nombre", "path": "Ruta",
        "quota": "Cuota", "used": "Usado", "available": "Disponible", "username": "Nombre de Usuario",
        "password": "Contraseña", "admin": "Admin", "storage_quota": "Cuota de Almacenamiento",
        "home_directory": "Directorio Home", "smb_status": "Estado SMB", "smb_shares": "Compartidos SMB",
        "share_name": "Nombre del Compartido", "comment": "Comentario", "read_only": "Solo Lectura",
        "browseable": "Navegable", "guest_access": "Acceso de Invitado", "language": "Idioma",
        "running": "Ejecutando", "stopped": "Detenido", "operation_success": "Operación Exitosa",
        "operation_failed": "Operación Fallida", "confirm_delete": "Confirmar Eliminación", "no_data": "Sin Datos",
        "create_volume": "Crear Volúmen", "create_user": "Crear Usuario", "create_share": "Crear Compartido",
        "operation": "Operación", "yes": "Sí", "no": "No", "system_info": "Info del Sistema",
        "service_status": "Estado del Servicio", "ip_address": "Dirección IP", "push_targets": "Push Targets",
        "push_files": "Push Archivos", "local_folder": "Folder Local", "target_device": "Dispositivo Target",
        "add_target": "Agregar Target", "target_name": "Nombre del Target", "target_ip": "IP del Target",
        "target_port": "Puerto del Target", "push_folder": "Push Folder", "select_folder": "Seleccionar Folder",
        "push_now": "Push Ahora", "pushing": "Push en curso", "push_history": "Historial Push",
        "scan_ip": "Escanear IP", "local_ips": "IPs Locales", "scan": "Escanear",
        "found_devices": "Dispositivos Encontrados", "online": "En línea", "offline": "Fuera de línea",
        "send": "Enviar", "receive": "Recibir", "push_status": "Estado Push",
        "success": "Éxito", "failed": "Fallido", "progress": "Progreso",
        "file_count": "Cantidad de Archivos", "total_size": "Tamaño Total", "version": "Versión 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "it_IT": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Archiviazione",
        "users": "Utenti", "shares": "Condivisioni", "push": "Gestione Push",
        "settings": "Impostazioni", "volumes": "Volume", "create": "Creare", "delete": "Eliminare",
        "edit": "Modificare", "save": "Salvare", "cancel": "Annullare", "name": "Nome", "path": "Percorso",
        "quota": "Quota", "used": "Usato", "available": "Disponibile", "username": "Nome Utente",
        "password": "Password", "admin": "Admin", "storage_quota": "Quota Archiviazione",
        "home_directory": "Directory Home", "smb_status": "Stato SMB", "smb_shares": "Condivisioni SMB",
        "share_name": "Nome Condivisione", "comment": "Commento", "read_only": "Sola Lettura",
        "browseable": "Navigabile", "guest_access": "Accesso Guest", "language": "Linguaggio",
        "running": "In Esecuzione", "stopped": "Fermato", "operation_success": "Operazione Successo",
        "operation_failed": "Operazione Fallita", "confirm_delete": "Conferma Eliminazione", "no_data": "Nessun Dato",
        "create_volume": "Creare Volume", "create_user": "Creare Utente", "create_share": "Creare Condivisione",
        "operation": "Operazione", "yes": "Sì", "no": "No", "system_info": "Info Sistema",
        "service_status": "Stato Servizio", "ip_address": "Indirizzo IP", "push_targets": "Push Targets",
        "push_files": "Push File", "local_folder": "Folder Locale", "target_device": "Dispositivo Target",
        "add_target": "Aggiungere Target", "target_name": "Nome Target", "target_ip": "IP Target",
        "target_port": "Porta Target", "push_folder": "Push Folder", "select_folder": "Seleziona Folder",
        "push_now": "Push Ora", "pushing": "Pushing", "push_history": "Storia Push",
        "scan_ip": "Scansionare IP", "local_ips": "IP Locali", "scan": "Scansionare",
        "found_devices": "Dispositivi Trovati", "online": "Online", "offline": "Offline",
        "send": "Inviare", "receive": "Ricevere", "push_status": "Stato Push",
        "success": "Successo", "failed": "Fallito", "progress": "Progresso",
        "file_count": "Conteggio File", "total_size": "Dimensione Totale", "version": "Versione 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "pt_BR": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Painel", "storage": "Armazenamento",
        "users": "Usuários", "shares": "Compartilhamentos", "push": "Gestão Push",
        "settings": "Configurações", "volumes": "Volumes", "create": "Criar", "delete": "Excluir",
        "edit": "Editar", "save": "Salvar", "cancel": "Cancelar", "name": "Nome", "path": "Caminho",
        "quota": "Quota", "used": "Usado", "available": "Disponível", "username": "Nome de Usuário",
        "password": "Senha", "admin": "Admin", "storage_quota": "Quota de Armazenamento",
        "home_directory": "Diretório Home", "smb_status": "Status SMB", "smb_shares": "Compartilhamentos SMB",
        "share_name": "Nome do Compartilhamento", "comment": "Comentário", "read_only": "Somente Leitura",
        "browseable": "Navegável", "guest_access": "Acesso Guest", "language": "Idioma",
        "running": "Executando", "stopped": "Parado", "operation_success": "Operação Sucesso",
        "operation_failed": "Operação Falhou", "confirm_delete": "Confirmar Exclusão", "no_data": "Sem Dados",
        "create_volume": "Criar Volume", "create_user": "Criar Usuário", "create_share": "Criar Compartilhamento",
        "operation": "Operação", "yes": "Sim", "no": "Não", "system_info": "Info do Sistema",
        "service_status": "Status do Serviço", "ip_address": "Endereço IP", "push_targets": "Push Targets",
        "push_files": "Push Arquivos", "local_folder": "Folder Local", "target_device": "Dispositivo Target",
        "add_target": "Adicionar Target", "target_name": "Nome do Target", "target_ip": "IP do Target",
        "target_port": "Porta do Target", "push_folder": "Push Folder", "select_folder": "Selecionar Folder",
        "push_now": "Push Agora", "pushing": "Push em curso", "push_history": "Histórico Push",
        "scan_ip": "Escanear IP", "local_ips": "IPs Locais", "scan": "Escanear",
        "found_devices": "Dispositivos Encontrados", "online": "Online", "offline": "Offline",
        "send": "Enviar", "receive": "Receber", "push_status": "Status Push",
        "success": "Sucesso", "failed": "Falhou", "progress": "Progresso",
        "file_count": "Contagem de Arquivos", "total_size": "Tamanho Total", "version": "Versão 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "ru_RU": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Панель управления", "storage": "Хранилище",
        "users": "Пользователи", "shares": "Общие ресурсы", "push": "Менеджер Push",
        "settings": "Настройки", "volumes": "Тома", "create": "Создать", "delete": "Удалить",
        "edit": "Редактировать", "save": "Сохранить", "cancel": "Отмена", "name": "Имя", "path": "Путь",
        "quota": "Квота", "used": "Использовано", "available": "Доступно", "username": "Имя пользователя",
        "password": "Пароль", "admin": "Админ", "storage_quota": "Квота хранилища",
        "home_directory": "Домашний каталог", "smb_status": "Статус SMB", "smb_shares": "SMB общие ресурсы",
        "share_name": "Имя общего ресурса", "comment": "Комментарий", "read_only": "Только чтение",
        "browseable": "Обзор", "guest_access": "Гостевой доступ", "language": "Язык",
        "running": "Работает", "stopped": "Остановлен", "operation_success": "Операция успешна",
        "operation_failed": "Операция не удалась", "confirm_delete": "Подтвердить удаление", "no_data": "Нет данных",
        "create_volume": "Создать том", "create_user": "Создать пользователя", "create_share": "Создать общий ресурс",
        "operation": "Операция", "yes": "Да", "no": "Нет", "system_info": "Системная информация",
        "service_status": "Статус сервиса", "ip_address": "IP-адрес", "push_targets": "Push цели",
        "push_files": "Push файлы", "local_folder": "Локальная папка", "target_device": "Целевое устройство",
        "add_target": "Добавить цель", "target_name": "Имя цели", "target_ip": "IP цели",
        "target_port": "Порт цели", "push_folder": "Push папку", "select_folder": "Выбрать папку",
        "push_now": "Push сейчас", "pushing": "Push выполняется", "push_history": "История Push",
        "scan_ip": "Сканировать IP", "local_ips": "Локальные IPs", "scan": "Сканировать",
        "found_devices": "Найденные устройства", "online": "Онлайн", "offline": "Оффлайн",
        "send": "Отправить", "receive": "Получить", "push_status": "Статус Push",
        "success": "Успешно", "failed": "Не удалось", "progress": "Прогресс",
        "file_count": "Количество файлов", "total_size": "Общий размер", "version": "Версия 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "ar_SA": {
        "app_name": "Xiaosi Super NAS", "dashboard": "لوحة التحكم", "storage": "التخزين",
        "users": "المستخدمين", "shares": "المشاركات", "push": "مدير Push",
        "settings": "الإعدادات", "volumes": "الأحجام", "create": "إنشاء", "delete": "حذف",
        "edit": "تحرير", "save": "حفظ", "cancel": "إلغاء", "name": "الاسم", "path": "المسار",
        "quota": "الحصة", "used": "المستخدم", "available": "المتاح", "username": "اسم المستخدم",
        "password": "كلمة المرور", "admin": "المدير", "storage_quota": "حصة التخزين",
        "home_directory": "الدليل الرئيسي", "smb_status": "حالة SMB", "smb_shares": "مشاركات SMB",
        "share_name": "اسم المشاركة", "comment": "تعليق", "read_only": "للقراءة فقط",
        "browseable": "قابل للتصفح", "guest_access": "وصول الضيف", "language": "اللغة",
        "running": "قيد التشغيل", "stopped": "متوقف", "operation_success": "عملية ناجحة",
        "operation_failed": "عملية فاشلة", "confirm_delete": "تأكيد الحذف", "no_data": "لا توجد بيانات",
        "create_volume": "إنشاء حجم", "create_user": "إنشاء مستخدم", "create_share": "إنشاء مشاركة",
        "operation": "عملية", "yes": "نعم", "no": "لا", "system_info": "معلومات النظام",
        "service_status": "حالة الخدمة", "ip_address": "عنوان IP", "push_targets": "Push Targets",
        "push_files": "Push Files", "local_folder": "Folder المحلي", "target_device": "الجهاز المستهدف",
        "add_target": "إضافة Target", "target_name": "اسم Target", "target_ip": "IP Target",
        "target_port": "Port Target", "push_folder": "Push Folder", "select_folder": "اختر Folder",
        "push_now": "Push الآن", "pushing": "Pushing", "push_history": "تاريخ Push",
        "scan_ip": "فحص IP", "local_ips": "IPs المحلية", "scan": "فحص",
        "found_devices": "الأجهزة الموجودة", "online": "متصل", "offline": "غير متصل",
        "send": "إرسال", "receive": "استقبال", "push_status": "حالة Push",
        "success": "نجاح", "failed": "فشل", "progress": "التقدم",
        "file_count": "عدد الملفات", "total_size": "الحجم الإجمالي", "version": "الإصدار 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "hi_IN": {
        "app_name": "Xiaosi Super NAS", "dashboard": "डैशबोर्ड", "storage": "स्टोरेज",
        "users": "उपयोगकर्ता", "shares": "शेयर", "push": "Push Manager",
        "settings": "सेटिंग्स", "volumes": "Volumes", "create": "बनाएं", "delete": "हटाएं",
        "edit": "संपादित", "save": "सहेजें", "cancel": "कैंसल", "name": "नाम", "path": "पथ",
        "quota": "Quota", "used": "उपयोग", "available": "उपलब्ध", "username": "Username",
        "password": "Password", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Shares",
        "share_name": "Share Name", "comment": "Comment", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Language",
        "running": "Running", "stopped": "Stopped", "operation_success": "Operation Success",
        "operation_failed": "Operation Failed", "confirm_delete": "Delete Confirm", "no_data": "No Data",
        "create_volume": "Create Volume", "create_user": "Create User", "create_share": "Create Share",
        "operation": "Operation", "yes": "Yes", "no": "No", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP Address", "push_targets": "Push Targets",
        "push_files": "Push Files", "local_folder": "Local Folder", "target_device": "Target Device",
        "add_target": "Add Target", "target_name": "Target Name", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Select Folder",
        "push_now": "Push Now", "pushing": "Pushing", "push_history": "Push History",
        "scan_ip": "Scan IP", "local_ips": "Local IPs", "scan": "Scan",
        "found_devices": "Found Devices", "online": "Online", "offline": "Offline",
        "send": "Send", "receive": "Receive", "push_status": "Push Status",
        "success": "Success", "failed": "Failed", "progress": "Progress",
        "file_count": "File Count", "total_size": "Total Size", "version": "Version 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "tr_TR": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Depolama",
        "users": "Kullanıcılar", "shares": "Paylaşımlar", "push": "Push Manager",
        "settings": "Ayarlar", "volumes": "Volumes", "create": "Oluştur", "delete": "Sil",
        "edit": "Düzenle", "save": "Kaydet", "cancel": "İptal", "name": "Ad", "path": "Yol",
        "quota": "Quota", "used": "Kullanılan", "available": "Kullanılabilir", "username": "Kullanıcı Adı",
        "password": "Şifre", "admin": "Admin", "storage_quota": "Depolama Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Durumu", "smb_shares": "SMB Paylaşımları",
        "share_name": "Paylaşım Adı", "comment": "Yorum", "read_only": "Salt Okunur",
        "browseable": "Göz Atılabilir", "guest_access": "Guest Erişimi", "language": "Dil",
        "running": "Çalışıyor", "stopped": "Durduruldu", "operation_success": "İşlem Başarılı",
        "operation_failed": "İşlem Başarısız", "confirm_delete": "Silmeyi Onayla", "no_data": "Veri Yok",
        "create_volume": "Volume Oluştur", "create_user": "Kullanıcı Oluştur", "create_share": "Paylaşım Oluştur",
        "operation": "İşlem", "yes": "Evet", "no": "Hayır", "system_info": "Sistem Bilgisi",
        "service_status": "Servis Durumu", "ip_address": "IP Adresi", "push_targets": "Push Targets",
        "push_files": "Push Dosyaları", "local_folder": "Yerel Folder", "target_device": "Hedef Cihaz",
        "add_target": "Target Ekle", "target_name": "Target Adı", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Folder Seç",
        "push_now": "Şimdi Push", "pushing": "Pushing", "push_history": "Push Geçmişi",
        "scan_ip": "IP Tarama", "local_ips": "Yerel IPs", "scan": "Tarama",
        "found_devices": "Bulunan Cihazlar", "online": "Online", "offline": "Offline",
        "send": "Gönder", "receive": "Al", "push_status": "Push Durumu",
        "success": "Başarılı", "failed": "Başarısız", "progress": "İlerleme",
        "file_count": "Dosya Sayısı", "total_size": "Toplam Boyut", "version": "Versiyon 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "th_TH": {
        "app_name": "Xiaosi Super NAS", "dashboard": "แดชบอร์ด", "storage": "การจัดเก็บ",
        "users": "ผู้ใช้", "shares": "การแชร์", "push": "Push Manager",
        "settings": "การตั้งค่า", "volumes": "Volumes", "create": "สร้าง", "delete": "ลบ",
        "edit": "แก้ไข", "save": "บันทึก", "cancel": "ยกเลิก", "name": "ชื่อ", "path": "เส้นทาง",
        "quota": "Quota", "used": "ที่ใช้", "available": "ที่มี", "username": "ชื่อผู้ใช้",
        "password": "รหัสผ่าน", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "สถานะ SMB", "smb_shares": "การแชร์ SMB",
        "share_name": "ชื่อการแชร์", "comment": "ความคิดเห็น", "read_only": "อ่านเท่านั้น",
        "browseable": "สามารถเรียกดู", "guest_access": "การเข้าถึง Guest", "language": "ภาษา",
        "running": "กำลังทำงาน", "stopped": "หยุด", "operation_success": "ดำเนินการสำเร็จ",
        "operation_failed": "ดำเนินการไม่สำเร็จ", "confirm_delete": "ยืนยันการลบ", "no_data": "ไม่มีข้อมูล",
        "create_volume": "สร้าง Volume", "create_user": "สร้างผู้ใช้", "create_share": "สร้างการแชร์",
        "operation": "การดำเนินการ", "yes": "ใช่", "no": "ไม่", "system_info": "ข้อมูลระบบ",
        "service_status": "สถานะบริการ", "ip_address": "ที่อยู่ IP", "push_targets": "Push Targets",
        "push_files": "Push Files", "local_folder": "Folder ภายใน", "target_device": "อุปกรณ์เป้าหมาย",
        "add_target": "เพิ่ม Target", "target_name": "ชื่อ Target", "target_ip": "IP Target",
        "target_port": "Port Target", "push_folder": "Push Folder", "select_folder": "เลือก Folder",
        "push_now": "Push ทันที", "pushing": "Pushing", "push_history": "ประวัติ Push",
        "scan_ip": "สแกน IP", "local_ips": "IPs ภายใน", "scan": "สแกน",
        "found_devices": "อุปกรณ์ที่พบ", "online": "ออนไลน์", "offline": "ออฟไลน์",
        "send": "ส่ง", "receive": "รับ", "push_status": "สถานะ Push",
        "success": "สำเร็จ", "failed": "ไม่สำเร็จ", "progress": "ความคืบหน้า",
        "file_count": "จำนวนไฟล์", "total_size": "ขนาดรวม", "version": "เวอร์ชัน 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "vi_VN": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Bảng điều khiển", "storage": "Lưu trữ",
        "users": "Người dùng", "shares": "Chia sẻ", "push": "Quản lý Push",
        "settings": "Cài đặt", "volumes": "Volumes", "create": "Tạo", "delete": "Xóa",
        "edit": "Sửa", "save": "Lưu", "cancel": "Hủy", "name": "Tên", "path": "Đường dẫn",
        "quota": "Quota", "used": "Đã dùng", "available": "Khả dụng", "username": "Tên người dùng",
        "password": "Mật khẩu", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Thư mục Home", "smb_status": "Trạng thái SMB", "smb_shares": "Chia sẻ SMB",
        "share_name": "Tên chia sẻ", "comment": "Ghi chú", "read_only": "Chỉ đọc",
        "browseable": "Có thể duyệt", "guest_access": "Guest Access", "language": "Ngôn ngữ",
        "running": "Đang chạy", "stopped": "Đã dừng", "operation_success": "Thao tác thành công",
        "operation_failed": "Thao tác thất bại", "confirm_delete": "Xác nhận xóa", "no_data": "Không có dữ liệu",
        "create_volume": "Tạo Volume", "create_user": "Tạo người dùng", "create_share": "Tạo chia sẻ",
        "operation": "Thao tác", "yes": "Có", "no": "Không", "system_info": "Thông tin hệ thống",
        "service_status": "Trạng thái dịch vụ", "ip_address": "Địa chỉ IP", "push_targets": "Push Targets",
        "push_files": "Push Files", "local_folder": "Folder cục bộ", "target_device": "Thiết bị mục tiêu",
        "add_target": "Thêm Target", "target_name": "Tên Target", "target_ip": "IP Target",
        "target_port": "Port Target", "push_folder": "Push Folder", "select_folder": "Chọn Folder",
        "push_now": "Push ngay", "pushing": "Pushing", "push_history": "Lịch sử Push",
        "scan_ip": "Quét IP", "local_ips": "IPs cục bộ", "scan": "Quét",
        "found_devices": "Thiết bị tìm thấy", "online": "Trực tuyến", "offline": "Ngoại tuyến",
        "send": "Gửi", "receive": "Nhận", "push_status": "Trạng thái Push",
        "success": "Thành công", "failed": "Thất bại", "progress": "Tiến trình",
        "file_count": "Số file", "total_size": "Tổng kích thước", "version": "Phiên bản 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "id_ID": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Penyimpanan",
        "users": "Pengguna", "shares": "Berbagi", "push": "Push Manager",
        "settings": "Pengaturan", "volumes": "Volumes", "create": "Buat", "delete": "Hapus",
        "edit": "Edit", "save": "Simpan", "cancel": "Batal", "name": "Nama", "path": "Path",
        "quota": "Quota", "used": "Digunakan", "available": "Tersedia", "username": "Username",
        "password": "Password", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "Status SMB", "smb_shares": "SMB Shares",
        "share_name": "Nama Share", "comment": "Komentar", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Bahasa",
        "running": "Berjalan", "stopped": "Berhenti", "operation_success": "Operasi Sukses",
        "operation_failed": "Operasi Gagal", "confirm_delete": "Konfirmasi Hapus", "no_data": "Tidak Ada Data",
        "create_volume": "Buat Volume", "create_user": "Buat Pengguna", "create_share": "Buat Share",
        "operation": "Operasi", "yes": "Ya", "no": "Tidak", "system_info": "Info Sistem",
        "service_status": "Status Layanan", "ip_address": "Alamat IP", "push_targets": "Push Targets",
        "push_files": "Push Files", "local_folder": "Folder Lokal", "target_device": "Device Target",
        "add_target": "Tambah Target", "target_name": "Nama Target", "target_ip": "IP Target",
        "target_port": "Port Target", "push_folder": "Push Folder", "select_folder": "Pilih Folder",
        "push_now": "Push Sekarang", "pushing": "Pushing", "push_history": "Riwayat Push",
        "scan_ip": "Scan IP", "local_ips": "IPs Lokal", "scan": "Scan",
        "found_devices": "Device Ditemukan", "online": "Online", "offline": "Offline",
        "send": "Kirim", "receive": "Terima", "push_status": "Status Push",
        "success": "Sukses", "failed": "Gagal", "progress": "Progres",
        "file_count": "Jumlah File", "total_size": "Total Ukuran", "version": "Versi 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "nl_NL": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Opslag",
        "users": "Gebruikers", "shares": "Shares", "push": "Push Manager",
        "settings": "Instellingen", "volumes": "Volumes", "create": "Creëer", "delete": "Verwijder",
        "edit": "Bewerk", "save": "Opslaan", "cancel": "Annuleren", "name": "Naam", "path": "Pad",
        "quota": "Quota", "used": "Gebruikt", "available": "Beschikbaar", "username": "Gebruikersnaam",
        "password": "Wachtwoord", "admin": "Admin", "storage_quota": "Opslag Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Shares",
        "share_name": "Share Naam", "comment": "Commentaar", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Taal",
        "running": "Actief", "stopped": "Gestopt", "operation_success": "Operatie Succes",
        "operation_failed": "Operatie Mislukt", "confirm_delete": "Bevestig Verwijdering", "no_data": "Geen Data",
        "create_volume": "Creëer Volume", "create_user": "Creëer Gebruiker", "create_share": "Creëer Share",
        "operation": "Operatie", "yes": "Ja", "no": "Nee", "system_info": "Systeem Info",
        "service_status": "Service Status", "ip_address": "IP-Adres", "push_targets": "Push Targets",
        "push_files": "Push Bestanden", "local_folder": "Lokale Folder", "target_device": "Target Device",
        "add_target": "Target Toevoegen", "target_name": "Target Naam", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Selecteer Folder",
        "push_now": "Push Nu", "pushing": "Pushing", "push_history": "Push Historie",
        "scan_ip": "Scan IP", "local_ips": "Lokale IPs", "scan": "Scan",
        "found_devices": "Gevonden Devices", "online": "Online", "offline": "Offline",
        "send": "Verstuur", "receive": "Ontvang", "push_status": "Push Status",
        "success": "Succes", "failed": "Mislukt", "progress": "Progress",
        "file_count": "Aantal Bestanden", "total_size": "Totale Grootte", "version": "Versie 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "pl_PL": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Przechowywanie",
        "users": "Użytkownicy", "shares": "Udostępnienia", "push": "Push Manager",
        "settings": "Ustawienia", "volumes": "Volumes", "create": "Utwórz", "delete": "Usuń",
        "edit": "Edytuj", "save": "Zapisz", "cancel": "Anuluj", "name": "Nazwa", "path": "Ścieżka",
        "quota": "Quota", "used": "Używane", "available": "Dostępne", "username": "Nazwa użytkownika",
        "password": "Hasło", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "Status SMB", "smb_shares": "Udostępnienia SMB",
        "share_name": "Nazwa Udostępnienia", "comment": "Komentarz", "read_only": "Read Only",
        "browseable": "Przeglądanie", "guest_access": "Guest Access", "language": "Język",
        "running": "Uruchomione", "stopped": "Zatrzymane", "operation_success": "Operacja Sukces",
        "operation_failed": "Operacja Niepowodzenie", "confirm_delete": "Potwierdź Usunięcie", "no_data": "Brak Danych",
        "create_volume": "Utwórz Volume", "create_user": "Utwórz Użytkownika", "create_share": "Utwórz Udostępnienie",
        "operation": "Operacja", "yes": "Tak", "no": "Nie", "system_info": "Info Systemu",
        "service_status": "Status Serwisu", "ip_address": "Adres IP", "push_targets": "Push Targets",
        "push_files": "Push Pliki", "local_folder": "Folder Lokalny", "target_device": "Target Device",
        "add_target": "Dodaj Target", "target_name": "Nazwa Target", "target_ip": "IP Target",
        "target_port": "Port Target", "push_folder": "Push Folder", "select_folder": "Wybierz Folder",
        "push_now": "Push Teraz", "pushing": "Pushing", "push_history": "Historia Push",
        "scan_ip": "Skanuj IP", "local_ips": "Lokalne IPs", "scan": "Skanuj",
        "found_devices": "Znalezione Devices", "online": "Online", "offline": "Offline",
        "send": "Wyślij", "receive": "Odbierz", "push_status": "Status Push",
        "success": "Sukces", "failed": "Niepowodzenie", "progress": "Progress",
        "file_count": "Liczba Plików", "total_size": "Całkowity Rozmiar", "version": "Wersja 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "sv_SE": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Lagring",
        "users": "Användare", "shares": "Delningar", "push": "Push Manager",
        "settings": "Inställningar", "volumes": "Volumes", "create": "Skapa", "delete": "Ta bort",
        "edit": "Redigera", "save": "Spara", "cancel": "Avbryt", "name": "Namn", "path": "Sökväg",
        "quota": "Quota", "used": "Använd", "available": "Tillgänglig", "username": "Användarnamn",
        "password": "Lösenord", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Delningar",
        "share_name": "Delnings Namn", "comment": "Kommentar", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Språk",
        "running": "Kör", "stopped": "Stoppad", "operation_success": "Operation Succé",
        "operation_failed": "Operation Misslyckades", "confirm_delete": "Bekräfta Ta bort", "no_data": "Ingen Data",
        "create_volume": "Skapa Volume", "create_user": "Skapa Användare", "create_share": "Skapa Delning",
        "operation": "Operation", "yes": "Ja", "no": "Nej", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP-Adress", "push_targets": "Push Targets",
        "push_files": "Push Filer", "local_folder": "Lokal Folder", "target_device": "Target Device",
        "add_target": "Lägg till Target", "target_name": "Target Namn", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Välj Folder",
        "push_now": "Push Nu", "pushing": "Pushing", "push_history": "Push Historia",
        "scan_ip": "Scan IP", "local_ips": "Lokala IPs", "scan": "Scan",
        "found_devices": "Hittade Devices", "online": "Online", "offline": "Offline",
        "send": "Skicka", "receive": "Ta emot", "push_status": "Push Status",
        "success": "Succé", "failed": "Misslyckades", "progress": "Progress",
        "file_count": "Filantal", "total_size": "Total Storlek", "version": "Version 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "da_DK": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Opbevaring",
        "users": "Brugere", "shares": "Delinger", "push": "Push Manager",
        "settings": "Indstillinger", "volumes": "Volumes", "create": "Opret", "delete": "Slet",
        "edit": "Rediger", "save": "Gem", "cancel": "Annuller", "name": "Navn", "path": "Sti",
        "quota": "Quota", "used": "Brugt", "available": "Tilgængelig", "username": "Brugernavn",
        "password": "Kodeord", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Delinger",
        "share_name": "Deling Navn", "comment": "Kommentar", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Sprog",
        "running": "Kører", "stopped": "Stoppet", "operation_success": "Operation Succes",
        "operation_failed": "Operation Fejl", "confirm_delete": "Bekræft Slet", "no_data": "Ingen Data",
        "create_volume": "Opret Volume", "create_user": "Opret Bruger", "create_share": "Opret Deling",
        "operation": "Operation", "yes": "Ja", "no": "Nej", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP-Adresse", "push_targets": "Push Targets",
        "push_files": "Push Filer", "local_folder": "Lokal Folder", "target_device": "Target Device",
        "add_target": "Tilføj Target", "target_name": "Target Navn", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Vælg Folder",
        "push_now": "Push Nu", "pushing": "Pushing", "push_history": "Push Historie",
        "scan_ip": "Scan IP", "local_ips": "Lokale IPs", "scan": "Scan",
        "found_devices": "Fundne Devices", "online": "Online", "offline": "Offline",
        "send": "Send", "receive": "Modtag", "push_status": "Push Status",
        "success": "Succes", "failed": "Fejl", "progress": "Progress",
        "file_count": "Filantal", "total_size": "Total Størrelse", "version": "Version 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "fi_FI": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Tallennus",
        "users": "Käyttäjät", "shares": "Jaot", "push": "Push Manager",
        "settings": "Asetukset", "volumes": "Volumes", "create": "Luo", "delete": "Poista",
        "edit": "Muokkaa", "save": "Tallenna", "cancel": "Peruuta", "name": "Nimi", "path": "Polku",
        "quota": "Quota", "used": "Käytetty", "available": "Saatavilla", "username": "Käyttäjänimi",
        "password": "Salasana", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Jaot",
        "share_name": "Jao Nimi", "comment": "Kommentti", "read_only": "Read Only",
        "browseable": "Selaa", "guest_access": "Guest Access", "language": "Kieli",
        "running": "Käynnissä", "stopped": "Pysäytetty", "operation_success": "Operation Onnistui",
        "operation_failed": "Operation Epäonnistui", "confirm_delete": "Vahvista Poisto", "no_data": "Ei Dataa",
        "create_volume": "Luo Volume", "create_user": "Luo Käyttäjä", "create_share": "Luo Jao",
        "operation": "Operation", "yes": "Kyllä", "no": "Ei", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP-osoite", "push_targets": "Push Targets",
        "push_files": "Push Tiedostot", "local_folder": "Lokali Folder", "target_device": "Target Device",
        "add_target": "Lisää Target", "target_name": "Target Nimi", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Valitse Folder",
        "push_now": "Push Nyt", "pushing": "Pushing", "push_history": "Push Historia",
        "scan_ip": "Scan IP", "local_ips": "Lokaalit IPs", "scan": "Scan",
        "found_devices": "Löydetyt Devices", "online": "Online", "offline": "Offline",
        "send": "Lähetä", "receive": "Vastaanota", "push_status": "Push Status",
        "success": "Onnistui", "failed": "Epäonnistui", "progress": "Progress",
        "file_count": "Tiedostojen Määrä", "total_size": "Yhteensä Koko", "version": "Versio 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "he_IL": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "אחסון",
        "users": "משתמשים", "shares": "שיתופים", "push": "Push Manager",
        "settings": "הגדרות", "volumes": "Volumes", "create": "יצירה", "delete": "מחיקה",
        "edit": "עריכה", "save": "שמירה", "cancel": "ביטול", "name": "שם", "path": "נתיב",
        "quota": "Quota", "used": "בשימוש", "available": "זמין", "username": "שם משתמש",
        "password": "סיסמה", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "סטטוס SMB", "smb_shares": "שיתופים SMB",
        "share_name": "שם שיתוף", "comment": "הערה", "read_only": "Read Only",
        "browseable": "ניתן לגישה", "guest_access": "Guest Access", "language": "שפה",
        "running": "רץ", "stopped": "הופסק", "operation_success": "הפעולה הצליחה",
        "operation_failed": "הפעולה נכשלה", "confirm_delete": "אישור מחיקה", "no_data": "אין נתונים",
        "create_volume": "יצירת Volume", "create_user": "יצירת משתמש", "create_share": "יצירת שיתוף",
        "operation": "פעולה", "yes": "כן", "no": "לא", "system_info": "מידע מערכת",
        "service_status": "סטטוס שירות", "ip_address": "כתובת IP", "push_targets": "Push Targets",
        "push_files": "Push Files", "local_folder": "Folder מקומי", "target_device": "Device מטרה",
        "add_target": "הוספת Target", "target_name": "שם Target", "target_ip": "IP Target",
        "target_port": "Port Target", "push_folder": "Push Folder", "select_folder": "בחירת Folder",
        "push_now": "Push עכשיו", "pushing": "Pushing", "push_history": "היסטורית Push",
        "scan_ip": "סריקת IP", "local_ips": "IPs מקומיים", "scan": "סריקה",
        "found_devices": "Devices שנמצאו", "online": "Online", "offline": "Offline",
        "send": "שליחה", "receive": "קבלה", "push_status": "סטטוס Push",
        "success": "הצלחה", "failed": "כשלון", "progress": "התקדמות",
        "file_count": "מספר קבצים", "total_size": "גודל כולל", "version": "גרסה 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "hu_HU": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Tárhely",
        "users": "Felhasználók", "shares": "Megosztások", "push": "Push Manager",
        "settings": "Beállítások", "volumes": "Volumes", "create": "Létrehoz", "delete": "Töröl",
        "edit": "Szerkeszt", "save": "Ment", "cancel": "Mégse", "name": "Név", "path": "Útvonal",
        "quota": "Quota", "used": "Használt", "available": "Elérhető", "username": "Felhasználónév",
        "password": "Jelszó", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Státusz", "smb_shares": "SMB Megosztások",
        "share_name": "Megosztás Neve", "comment": "Komment", "read_only": "Read Only",
        "browseable": "Böngészhető", "guest_access": "Guest Access", "language": "Nyelv",
        "running": "Fut", "stopped": "Megállítva", "operation_success": "Művelet Sikeres",
        "operation_failed": "Művelet Sikertelen", "confirm_delete": "Törlés Jóváhagyása", "no_data": "Nincs Adat",
        "create_volume": "Volume Létrehoz", "create_user": "Felhasználó Létrehoz", "create_share": "Megosztás Létrehoz",
        "operation": "Művelet", "yes": "Igen", "no": "Nem", "system_info": "Rendszer Info",
        "service_status": "Szolgáltatás Státusz", "ip_address": "IP Cím", "push_targets": "Push Targets",
        "push_files": "Push Fájlok", "local_folder": "Helyi Folder", "target_device": "Target Device",
        "add_target": "Target Hozzáad", "target_name": "Target Név", "target_ip": "Target IP",
        "target_port": "Target Port", "push_folder": "Push Folder", "select_folder": "Folder Kiválaszt",
        "push_now": "Push Most", "pushing": "Pushing", "push_history": "Push Történet",
        "scan_ip": "IP Scan", "local_ips": "Helyi IPs", "scan": "Scan",
        "found_devices": "Talált Devices", "online": "Online", "offline": "Offline",
        "send": "Küld", "receive": "Fogad", "push_status": "Push Státusz",
        "success": "Siker", "failed": "Sikertelen", "progress": "Progress",
        "file_count": "Fájl Szám", "total_size": "Teljes Méret", "version": "Verzió 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "cs_CZ": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Úložiště",
        "users": "Uživatelé", "shares": "Sdílení", "push": "Push Manager",
        "settings": "Nastavení", "volumes": "Volumes", "create": "Vytvořit", "delete": "Smazat",
        "edit": "Upravit", "save": "Uložit", "cancel": "Zrušit", "name": "Název", "path": "Cesta",
        "quota": "Quota", "used": "Použito", "available": "Dostupné", "username": "Uživatelské jméno",
        "password": "Heslo", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Sdílení",
        "share_name": "Název Sdílení", "comment": "Komentář", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Jazyk",
        "running": "Běží", "stopped": "Zastaveno", "operation_success": "Operace Úspěšná",
        "operation_failed": "Operace Neúspěšná", "confirm_delete": "Potvrdit Smazání", "no_data": "Žádné Data",
        "create_volume": "Vytvořit Volume", "create_user": "Vytvořit Uživatele", "create_share": "Vytvořit Sdílení",
        "operation": "Operace", "yes": "Ano", "no": "Ne", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP Adresa", "push_targets": "Push Targets",
        "push_files": "Push Soubory", "local_folder": "Lokální Folder", "target_device": "Target Device",
        "add_target": "Přidat Target", "target_name": "Název Target", "target_ip": "IP Target",
        "target_port": "Port Target", "push_folder": "Push Folder", "select_folder": "Vybrat Folder",
        "push_now": "Push Teď", "pushing": "Pushing", "push_history": "Push Historie",
        "scan_ip": "Scan IP", "local_ips": "Lokální IPs", "scan": "Scan",
        "found_devices": "Nalezené Devices", "online": "Online", "offline": "Offline",
        "send": "Poslat", "receive": "Přijmout", "push_status": "Push Status",
        "success": "Úspěch", "failed": "Neúspěch", "progress": "Progress",
        "file_count": "Počet Souborů", "total_size": "Celková Velikost", "version": "Verze 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "uk_UA": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Панель управління", "storage": "Зберігання",
        "users": "Користувачі", "shares": "Спільні ресурси", "push": "Push Manager",
        "settings": "Налаштування", "volumes": "Volumes", "create": "Створити", "delete": "Видалити",
        "edit": "Редагувати", "save": "Зберегти", "cancel": "Скасувати", "name": "Ім'я", "path": "Шлях",
        "quota": "Quota", "used": "Використано", "available": "Доступно", "username": "Ім'я користувача",
        "password": "Пароль", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Спільні ресурси",
        "share_name": "Назва спільного ресурсу", "comment": "Коментар", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Мова",
        "running": "Запущено", "stopped": "Зупинено", "operation_success": "Операція Успішна",
        "operation_failed": "Операція Неуспішна", "confirm_delete": "Підтвердити Видалення", "no_data": "Немає Даних",
        "create_volume": "Створити Volume", "create_user": "Створити Користувача", "create_share": "Створити Спільний ресурс",
        "operation": "Операція", "yes": "Так", "no": "Ні", "system_info": "System Info",
        "service_status": "Service Status", "ip_address": "IP Адреса", "push_targets": "Push Targets",
        "push_files": "Push Файли", "local_folder": "Локальний Folder", "target_device": "Target Device",
        "add_target": "Додати Target", "target_name": "Назва Target", "target_ip": "IP Target",
        "target_port": "Port Target", "push_folder": "Push Folder", "select_folder": "Вибрати Folder",
        "push_now": "Push Зараз", "pushing": "Pushing", "push_history": "Push Історія",
        "scan_ip": "Scan IP", "local_ips": "Локальні IPs", "scan": "Scan",
        "found_devices": "Знайдені Devices", "online": "Online", "offline": "Offline",
        "send": "Надіслати", "receive": "Прийняти", "push_status": "Push Status",
        "success": "Успіх", "failed": "Неуспіх", "progress": "Progress",
        "file_count": "Кількість Файлів", "total_size": "Загальний Розмір", "version": "Версія 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    },
    "ro_RO": {
        "app_name": "Xiaosi Super NAS", "dashboard": "Dashboard", "storage": "Stocare",
        "users": "Utilizatori", "shares": "Partajări", "push": "Push Manager",
        "settings": "Setări", "volumes": "Volumes", "create": "Creează", "delete": "Șterge",
        "edit": "Editează", "save": "Salvează", "cancel": "Anulează", "name": "Nume", "path": "Cale",
        "quota": "Quota", "used": "Folosit", "available": "Disponibil", "username": "Nume utilizator",
        "password": "Parolă", "admin": "Admin", "storage_quota": "Storage Quota",
        "home_directory": "Home Directory", "smb_status": "SMB Status", "smb_shares": "SMB Partajări",
        "share_name": "Nume Partajare", "comment": "Comentariu", "read_only": "Read Only",
        "browseable": "Browseable", "guest_access": "Guest Access", "language": "Limbă",
        "running": "Rulează", "stopped": "Oprit", "operation_success": "Operație Succes",
        "operation_failed": "Operație Eșuată", "confirm_delete": "Confirmă Ștergere", "no_data": "Nu există date",
        "create_volume": "Creează Volume", "create_user": "Creează Utilizator", "create_share": "Creează Partajare",
        "operation": "Operație", "yes": "Da", "no": "Nu", "system_info": "Info Sistem",
        "service_status": "Status Serviciu", "ip_address": "Adresă IP", "push_targets": "Push Targets",
        "push_files": "Push Fișiere", "local_folder": "Folder Local", "target_device": "Device Target",
        "add_target": "Adaugă Target", "target_name": "Nume Target", "target_ip": "IP Target",
        "target_port": "Port Target", "push_folder": "Push Folder", "select_folder": "Selectează Folder",
        "push_now": "Push Acum", "pushing": "Pushing", "push_history": "Istorie Push",
        "scan_ip": "Scan IP", "local_ips": "IPs Locale", "scan": "Scan",
        "found_devices": "Devices Găsite", "online": "Online", "offline": "Offline",
        "send": "Trimite", "receive": "Primește", "push_status": "Status Push",
        "success": "Succes", "failed": "Eșuat", "progress": "Progres",
        "file_count": "Număr Fișiere", "total_size": "Dimensiune Totală", "version": "Versiune 2",
        "zero_dependency": "Zero Dependency", "api_docs": "API Docs"
    }
}

LANG_NAMES = {
    "zh_CN": "简体中文", "zh_TW": "繁體中文", "en_US": "English (US)", "en_GB": "English (UK)",
    "ja_JP": "日本語", "ko_KR": "한국어", "fr_FR": "Français", "de_DE": "Deutsch",
    "es_ES": "Español", "it_IT": "Italiano", "pt_BR": "Português (BR)", "ru_RU": "Русский",
    "ar_SA": "العربية", "hi_IN": "हिन्दी", "tr_TR": "Türkçe", "th_TH": "ไทย",
    "vi_VN": "Tiếng Việt", "id_ID": "Bahasa Indonesia", "nl_NL": "Nederlands", "pl_PL": "Polski",
    "sv_SE": "Svenska", "da_DK": "Dansk", "fi_FI": "Suomi", "he_IL": "עברית",
    "hu_HU": "Magyar", "cs_CZ": "Čeština", "uk_UA": "Українська", "ro_RO": "Română"
}


# ==========================================
# 配置管理类
# ==========================================
class Config:
    """配置管理类 - 支持从../config/config.json加载配置"""
    
    def __init__(self):
        self.volumes: List[Dict] = []
        self.users: List[Dict] = []
        self.shares: List[Dict] = []
        self.push_targets: List[Dict] = []
        self.server_port: int = 8080
        self.language: str = "zh_CN"
        self.data_dir: str = "nas_data"
        self.receive_dir: str = "nas_data/received"
        self._load()
    
    def _load(self):
        """从配置文件加载配置"""
        config_path = self._get_config_path()
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # 服务器配置
                    server_config = data.get("server", {})
                    self.server_port = server_config.get("port", 8080)
                    self.language = server_config.get("language", "zh_CN")
                    
                    # 存储配置
                    storage_config = data.get("storage", {})
                    self.volumes = storage_config.get("volumes", [])
                    
                    # 用户配置
                    self.users = data.get("users", [])
                    
                    # SMB配置
                    smb_config = data.get("smb", {})
                    self.shares = smb_config.get("shares", [])
                    
                    # Push配置
                    push_config = data.get("push", {})
                    self.push_targets = push_config.get("targets", [])
                    
                    # 数据目录
                    self.data_dir = data.get("data_dir", "nas_data")
                    self.receive_dir = data.get("receive_dir", "nas_data/received")
                    
                print(f"[配置] 已从 {config_path} 加载配置")
            else:
                print(f"[配置] 配置文件不存在，使用默认配置")
        except Exception as e:
            print(f"[配置] 加载失败: {e}, 使用默认配置")
        
        # 创建必要的目录
        os.makedirs(self.receive_dir, exist_ok=True)
    
    def _get_config_path(self) -> str:
        """获取配置文件路径"""
        # 尝试相对路径 ../config/config.json
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "..", "config", "config.json")
        
        # 如果不存在，尝试当前目录的 config.json
        if not os.path.exists(config_path):
            config_path = "config.json"
        
        return config_path
    
    def save(self):
        """保存配置到文件"""
        config_path = self._get_config_path()
        
        # 确保配置目录存在
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        data = {
            "server": {
                "port": self.server_port,
                "language": self.language
            },
            "storage": {
                "volumes": self.volumes
            },
            "users": self.users,
            "smb": {
                "shares": self.shares
            },
            "push": {
                "targets": self.push_targets
            },
            "data_dir": self.data_dir,
            "receive_dir": self.receive_dir
        }
        
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[配置] 已保存到 {config_path}")
        except Exception as e:
            print(f"[配置] 保存失败: {e}")


# ==========================================
# IP地址管理类
# ==========================================
class IPManager:
    """IP地址管理类 - 支持本机IP检测和局域网扫描"""
    
    # 设备唯一标识
    DEVICE_ID: Optional[str] = None
    
    @classmethod
    def get_device_id(cls) -> str:
        """获取设备唯一ID"""
        if cls.DEVICE_ID is None:
            hostname = socket.gethostname()
            cls.DEVICE_ID = f"{hostname}-{uuid.uuid4().hex[:8]}"
        return cls.DEVICE_ID
    
    @staticmethod
    def get_network_type(ip: str) -> str:
        """判断IP网络类型"""
        if ip.startswith("192.168.") or ip.startswith("10."):
            return "LAN (私有)"
        elif ip.startswith("172."):
            parts = ip.split(".")
            if len(parts) >= 2 and 16 <= int(parts[1]) <= 31:
                return "LAN (私有)"
        elif ip.startswith("127."):
            return "Loopback"
        elif ip.startswith("255."):
            return "Broadcast"
        return "Public/WAN"
    
    @classmethod
    def get_local_ips(cls) -> List[Dict]:
        """获取本机所有IP地址"""
        ips: List[Dict] = []
        hostname = socket.gethostname()
        device_id = cls.get_device_id()
        
        # 方法1: UDP连接获取出口IP（最可靠）
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            wan_ip = s.getsockname()[0]
            s.close()
            
            if wan_ip and wan_ip != "127.0.0.1":
                ips.append({
                    "ip": wan_ip,
                    "type": "wan",
                    "name": f"{hostname} (出口)",
                    "adapter": "默认路由",
                    "network": cls.get_network_type(wan_ip),
                    "device_id": device_id
                })
        except Exception:
            pass
        
        # 方法2: 根据操作系统获取详细网卡信息
        system = platform.system()
        
        if system == "Windows":
            cls._get_windows_ips(ips, hostname, device_id)
        elif system in ("Linux", "Darwin"):
            cls._get_unix_ips(ips, hostname, device_id)
        
        # 去重
        unique_ips = []
        seen = set()
        for ip in ips:
            if ip["ip"] not in seen:
                seen.add(ip["ip"])
                unique_ips.append(ip)
        
        # 如果没有找到IP，添加localhost
        if not unique_ips:
            unique_ips.append({
                "ip": "127.0.0.1",
                "type": "loopback",
                "name": "localhost",
                "adapter": "loopback",
                "network": "Loopback",
                "device_id": device_id
            })
        
        return unique_ips
    
    @classmethod
    def _get_windows_ips(cls, ips: List[Dict], hostname: str, device_id: str):
        """Windows系统IP获取"""
        try:
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            current_adapter = "Unknown"
            for line in result.stdout.split("\n"):
                line = line.strip()
                
                # 检测网卡名称
                if "adapter" in line.lower() or "适配器" in line:
                    current_adapter = line.split(":")[0].strip()
                    for prefix in ["适配器", "adapter", "Adapter"]:
                        if current_adapter.startswith(prefix):
                            current_adapter = current_adapter[len(prefix):].strip()
                    if current_adapter.startswith("."):
                        current_adapter = current_adapter[1:].strip()
                
                # 检测IPv4地址
                elif "IPv4" in line or "IPv4 地址" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        ip = parts[-1].strip()
                        if ip and "." in ip and not ip.startswith("127."):
                            if not any(i["ip"] == ip for i in ips):
                                ips.append({
                                    "ip": ip,
                                    "type": "lan",
                                    "name": current_adapter,
                                    "adapter": current_adapter,
                                    "network": cls.get_network_type(ip),
                                    "device_id": device_id
                                })
        except Exception as e:
            print(f"[IP检测] Windows ipconfig失败: {e}")
    
    @classmethod
    def _get_unix_ips(cls, ips: List[Dict], hostname: str, device_id: str):
        """Unix/Linux系统IP获取"""
        try:
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            current_iface = ""
            for line in result.stdout.split("\n"):
                line = line.strip()
                
                # 检测接口名称
                if re.match(r'^[a-zA-Z0-9]+:', line):
                    current_iface = re.match(r'^([a-zA-Z0-9]+):', line).group(1)
                
                # 检测inet地址
                match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    if ip and not ip.startswith("127."):
                        if not any(i["ip"] == ip for i in ips):
                            ips.append({
                                "ip": ip,
                                "type": "lan",
                                "name": current_iface,
                                "adapter": current_iface,
                                "network": cls.get_network_type(ip),
                                "device_id": device_id
                            })
        except Exception as e:
            print(f"[IP检测] Unix ifconfig失败: {e}")
    
    @classmethod
    def scan_lan(cls, port: int = 8080, timeout: float = 0.3) -> List[Dict]:
        """扫描局域网设备"""
        found: List[Dict] = []
        local_ips = cls.get_local_ips()
        
        if not local_ips:
            return found
        
        # 收集所有私有IP段
        prefixes = set()
        for ip_info in local_ips:
            ip = ip_info["ip"]
            if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                parts = ip.split(".")
                if len(parts) == 4:
                    prefixes.add(".".join(parts[:3]))
        
        if not prefixes:
            return found
        
        # 多线程扫描
        threads: List[threading.Thread] = []
        
        def check_device(ip_str: str):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip_str, port))
                sock.close()
                
                if result == 0:
                    # 获取设备信息
                    device_info = {
                        "ip": ip_str,
                        "port": port,
                        "status": "online",
                        "is_self": ip_str in [i["ip"] for i in local_ips]
                    }
                    
                    # 尝试获取设备ID
                    try:
                        import urllib.request
                        resp = urllib.request.urlopen(
                            f"http://{ip_str}:{port}/api/ip/local",
                            timeout=2
                        )
                        data = json.loads(resp.read().decode())
                        if data.get("ips"):
                            device_info["device_id"] = data["ips"][0].get("device_id", "unknown")
                    except Exception:
                        device_info["device_id"] = "unknown"
                    
                    found.append(device_info)
            except Exception:
                pass
        
        # 扫描每个网段
        for prefix in prefixes:
            for i in range(1, 255):
                ip_str = f"{prefix}.{i}"
                # 排除本机IP
                if not any(ip_str == ip_info["ip"] for ip_info in local_ips):
                    t = threading.Thread(target=check_device, args=(ip_str,))
                    threads.append(t)
                    t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join(timeout=timeout + 1)
        
        return found


# ==========================================
# 推送管理器类
# ==========================================
class PushManager:
    """推送管理器 - 支持文件夹推送和接收"""
    
    def __init__(self, config: Config):
        self.targets = config.push_targets
        self.config = config
        self.push_history: List[Dict] = []
        self.active_push: Optional[Dict] = None
    
    def list_targets(self) -> List[Dict]:
        """列出所有推送目标"""
        return self.targets
    
    def add_target(self, name: str, ip: str, port: int = 8080) -> Tuple[bool, str]:
        """添加推送目标"""
        # 检查是否已存在
        for t in self.targets:
            if t["ip"] == ip and t["port"] == port:
                return False, "Target already exists"
        
        self.targets.append({
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "ip": ip,
            "port": port,
            "status": "unknown"
        })
        
        self.config.push_targets = self.targets
        self.config.save()
        return True, "Target added successfully"
    
    def delete_target(self, target_id: str) -> Tuple[bool, str]:
        """删除推送目标"""
        self.targets = [t for t in self.targets if t.get("id") != target_id]
        self.config.push_targets = self.targets
        self.config.save()
        return True, "Target deleted"
    
    def check_target(self, target_id: str) -> Tuple[bool, str]:
        """检查目标设备状态"""
        target = next((t for t in self.targets if t.get("id") == target_id), None)
        if not target:
            return False, "Target not found"
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((target["ip"], target["port"]))
            sock.close()
            
            status = "online" if result == 0 else "offline"
            target["status"] = status
            return True, status
        except Exception as e:
            target["status"] = "offline"
            return False, str(e)
    
    def push_folder(self, target_id: str, folder_path: str) -> Tuple[bool, str]:
        """推送文件夹到目标设备"""
        target = next((t for t in self.targets if t.get("id") == target_id), None)
        if not target:
            return False, "Target not found"
        
        if not os.path.exists(folder_path):
            return False, "Folder not found"
        
        folder_path = os.path.abspath(folder_path)
        folder_name = os.path.basename(folder_path)
        
        # 收集所有文件
        all_files: List[Tuple[str, str, int]] = []
        total_size = 0
        
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                fpath = os.path.join(root, f)
                try:
                    size = os.path.getsize(fpath)
                    rel_path = os.path.relpath(fpath, folder_path)
                    all_files.append((rel_path, fpath, size))
                    total_size += size
                except Exception:
                    pass
        
        push_id = str(uuid.uuid4())[:8]
        self.active_push = {
            "id": push_id,
            "target": target["name"],
            "folder": folder_name,
            "total_files": len(all_files),
            "total_size": total_size,
            "sent_files": 0,
            "sent_size": 0,
            "status": "pushing",
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 推送文件
        try:
            import urllib.request
            
            for idx, (rel_path, fpath, size) in enumerate(all_files):
                try:
                    with open(fpath, "rb") as f:
                        file_data = f.read()
                    
                    # 构建multipart/form-data请求
                    boundary = "----XiaosiNASPush" + str(uuid.uuid4().hex)
                    
                    body = b""
                    body += f"--{boundary}\r\n".encode()
                    body += b'Content-Disposition: form-data; name="folder"\r\n\r\n'
                    body += folder_name.encode() + b"\r\n"
                    body += f"--{boundary}\r\n".encode()
                    body += b'Content-Disposition: form-data; name="filepath"\r\n\r\n'
                    body += rel_path.encode() + b"\r\n"
                    body += f"--{boundary}\r\n".encode()
                    body += f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(fpath)}"\r\n'.encode()
                    body += b"Content-Type: application/octet-stream\r\n\r\n"
                    body += file_data + b"\r\n"
                    body += f"--{boundary}--\r\n".encode()
                    
                    # 发送请求
                    url = f"http://{target['ip']}:{target['port']}/api/push/receive"
                    req = urllib.request.Request(url, data=body)
                    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
                    req.add_header("Content-Length", str(len(body)))
                    
                    resp = urllib.request.urlopen(req, timeout=30)
                    resp.read()
                    
                    # 更新进度
                    self.active_push["sent_files"] = idx + 1
                    self.active_push["sent_size"] += size
                    
                except Exception as e:
                    print(f"[推送] 文件 {rel_path} 失败: {e}")
            
            # 推送完成
            self.active_push["status"] = "success"
            self.active_push["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.push_history.append(dict(self.active_push))
            self.active_push = None
            
            return True, f"Successfully pushed {len(all_files)} files"
            
        except Exception as e:
            if self.active_push:
                self.active_push["status"] = "failed"
                self.active_push["error"] = str(e)
                self.active_push["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                self.push_history.append(dict(self.active_push))
                self.active_push = None
            
            return False, str(e)
    
    def receive_file(self, folder_name: str, filepath: str, file_data: bytes) -> Tuple[bool, int]:
        """接收推送的文件"""
        target_dir = os.path.join(self.config.receive_dir, folder_name)
        full_path = os.path.join(target_dir, filepath)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 写入文件
        with open(full_path, "wb") as f:
            f.write(file_data)
        
        return True, len(file_data)
    
    def get_push_status(self) -> Dict:
        """获取推送状态"""
        return {
            "active": self.active_push,
            "history": self.push_history[-20:] if len(self.push_history) > 20 else self.push_history
        }


# ==========================================
# 存储管理器类
# ==========================================
class StorageManager:
    """存储管理器 - 管理存储卷"""
    
    def __init__(self, config: Config):
        self.volumes = config.volumes
    
    def list_volumes(self) -> List[Dict]:
        """列出所有存储卷"""
        return self.volumes
    
    def create_volume(self, name: str, path: str, quota_gb: int) -> Tuple[bool, str]:
        """创建存储卷"""
        # 检查是否已存在
        for v in self.volumes:
            if v["name"] == name:
                return False, "Volume already exists"
        
        self.volumes.append({
            "name": name,
            "path": path,
            "quota_gb": quota_gb,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return True, "Volume created successfully"
    
    def delete_volume(self, name: str) -> Tuple[bool, str]:
        """删除存储卷"""
        self.volumes = [v for v in self.volumes if v["name"] != name]
        return True, "Volume deleted"


# ==========================================
# 用户管理器类
# ==========================================
class UserManager:
    """用户管理器 - 管理NAS用户"""
    
    def __init__(self, config: Config):
        self.users = config.users
        self._ensure_admin_user()
    
    def _ensure_admin_user(self):
        """确保存在管理员用户"""
        if not any(u.get("username") == "admin" for u in self.users):
            self.users.append({
                "username": "admin",
                "password": self._hash_password("admin"),
                "is_admin": True,
                "home_dir": "/mnt/data/admin",
                "storage_quota_gb": 0,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def list_users(self) -> List[Dict]:
        """列出所有用户（不包含密码）"""
        return [
            {
                "username": u["username"],
                "is_admin": u.get("is_admin", False),
                "home_dir": u.get("home_dir", ""),
                "storage_quota_gb": u.get("storage_quota_gb", 100)
            }
            for u in self.users
        ]
    
    def create_user(self, username: str, password: str, is_admin: bool = False) -> Tuple[bool, str]:
        """创建用户"""
        # 检查是否已存在
        for u in self.users:
            if u["username"] == username:
                return False, "User already exists"
        
        self.users.append({
            "username": username,
            "password": self._hash_password(password),
            "is_admin": is_admin,
            "home_dir": f"/mnt/data/{username}",
            "storage_quota_gb": 100,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return True, "User created successfully"
    
    def delete_user(self, username: str) -> Tuple[bool, str]:
        """删除用户"""
        if username == "admin":
            return False, "Cannot delete admin user"
        
        self.users = [u for u in self.users if u["username"] != username]
        return True, "User deleted"


# ==========================================
# SMB管理器类
# ==========================================
class SMBManager:
    """SMB管理器 - 管理SMB共享"""
    
    def __init__(self, config: Config):
        self.shares = config.shares
        self.running = True
    
    def list_shares(self) -> List[Dict]:
        """列出所有SMB共享"""
        return self.shares
    
    def create_share(self, name: str, path: str) -> Tuple[bool, str]:
        """创建SMB共享"""
        # 检查是否已存在
        for s in self.shares:
            if s["name"] == name:
                return False, "Share already exists"
        
        self.shares.append({
            "name": name,
            "path": path,
            "comment": "",
            "read_only": False,
            "browseable": True,
            "guest_access": False,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return True, "Share created successfully"
    
    def delete_share(self, name: str) -> Tuple[bool, str]:
        """删除SMB共享"""
        self.shares = [s for s in self.shares if s["name"] != name]
        return True, "Share deleted"
    
    def get_status(self) -> Dict:
        """获取SMB服务状态"""
        return {
            "running": self.running,
            "port": 445,
            "workgroup": "WORKGROUP"
        }


# ==========================================
# HTTP请求处理器
# ==========================================
class NASHandler(BaseHTTPRequestHandler):
    """NAS REST API处理器"""
    
    # 全局管理器实例（将在main中设置）
    config: Config = None
    storage_mgr: StorageManager = None
    user_mgr: UserManager = None
    smb_mgr: SMBManager = None
    ip_mgr: IPManager = None
    push_mgr: PushManager = None
    
    def send_json(self, data: Dict, status: int = 200):
        """发送JSON响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    
    def send_error_json(self, message: str, status: int = 400):
        """发送错误JSON响应"""
        self.send_json({"success": False, "message": message}, status)
    
    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)
        
        try:
            # API路由
            if path == "/api/i18n":
                lang = query.get("lang", ["zh_CN"])[0]
                trans = TRANSLATIONS.get(lang, TRANSLATIONS.get("zh_CN", {}))
                self.send_json(trans)
            
            elif path == "/api/storage/volumes":
                volumes = self.storage_mgr.list_volumes()
                self.send_json({"success": True, "volumes": volumes})
            
            elif path == "/api/users":
                users = self.user_mgr.list_users()
                self.send_json({"success": True, "users": users})
            
            elif path == "/api/smb/shares":
                shares = self.smb_mgr.list_shares()
                self.send_json({"success": True, "shares": shares})
            
            elif path == "/api/smb/status":
                status = self.smb_mgr.get_status()
                self.send_json({"success": True, **status})
            
            elif path == "/api/ip/local":
                ips = IPManager.get_local_ips()
                self.send_json({"success": True, "ips": ips})
            
            elif path == "/api/ip/scan":
                port = int(query.get("port", ["8080"])[0])
                devices = IPManager.scan_lan(port=port)
                self.send_json({"success": True, "devices": devices})
            
            elif path == "/api/push/targets":
                targets = self.push_mgr.list_targets()
                self.send_json({"success": True, "targets": targets})
            
            elif path == "/api/push/status":
                status = self.push_mgr.get_push_status()
                self.send_json({"success": True, **status})
            
            elif path == "/" or path == "/index.html":
                self.send_html(INDEX_HTML)
            
            else:
                self.send_error_json("API endpoint not found", 404)
        
        except Exception as e:
            self.send_error_json(f"Internal error: {str(e)}", 500)
    
    def do_POST(self):
        """处理POST请求"""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        content_type = self.headers.get("Content-Type", "")
        
        try:
            # 处理multipart/form-data（文件接收）
            if "multipart/form-data" in content_type:
                if path == "/api/push/receive":
                    self._handle_file_receive()
                    return
                else:
                    self.send_error_json("multipart/form-data only supported for /api/push/receive", 400)
                    return
            
            # 解析JSON请求体
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self.send_error_json("Invalid JSON", 400)
                return
            
            # API路由
            if path == "/api/storage/volumes":
                name = data.get("name", "")
                path_v = data.get("path", "")
                quota = data.get("quota_gb", 100)
                
                if not name or not path_v:
                    self.send_error_json("Name and path required")
                    return
                
                ok, msg = self.storage_mgr.create_volume(name, path_v, quota)
                self.send_json({"success": ok, "message": msg}, 201 if ok else 400)
            
            elif path == "/api/storage/volumes/delete":
                name = data.get("name", "")
                if not name:
                    self.send_error_json("Volume name required")
                    return
                
                ok, msg = self.storage_mgr.delete_volume(name)
                self.send_json({"success": ok, "message": msg})
            
            elif path == "/api/users":
                username = data.get("username", "")
                password = data.get("password", "")
                is_admin = data.get("is_admin", False)
                
                if not username or not password:
                    self.send_error_json("Username and password required")
                    return
                
                ok, msg = self.user_mgr.create_user(username, password, is_admin)
                self.send_json({"success": ok, "message": msg}, 201 if ok else 400)
            
            elif path == "/api/users/delete":
                username = data.get("username", "")
                if not username:
                    self.send_error_json("Username required")
                    return
                
                ok, msg = self.user_mgr.delete_user(username)
                self.send_json({"success": ok, "message": msg})
            
            elif path == "/api/smb/shares":
                name = data.get("name", "")
                share_path = data.get("path", "")
                
                if not name or not share_path:
                    self.send_error_json("Share name and path required")
                    return
                
                ok, msg = self.smb_mgr.create_share(name, share_path)
                self.send_json({"success": ok, "message": msg}, 201 if ok else 400)
            
            elif path == "/api/smb/shares/delete":
                name = data.get("name", "")
                if not name:
                    self.send_error_json("Share name required")
                    return
                
                ok, msg = self.smb_mgr.delete_share(name)
                self.send_json({"success": ok, "message": msg})
            
            elif path == "/api/push/targets":
                name = data.get("name", "")
                ip = data.get("ip", "")
                port = data.get("port", 8080)
                
                if not name or not ip:
                    self.send_error_json("Target name and IP required")
                    return
                
                ok, msg = self.push_mgr.add_target(name, ip, port)
                self.send_json({"success": ok, "message": msg}, 201 if ok else 400)
            
            elif path == "/api/push/targets/delete":
                target_id = data.get("id", "")
                if not target_id:
                    self.send_error_json("Target ID required")
                    return
                
                ok, msg = self.push_mgr.delete_target(target_id)
                self.send_json({"success": ok, "message": msg})
            
            elif path == "/api/push/targets/check":
                target_id = data.get("id", "")
                if not target_id:
                    self.send_error_json("Target ID required")
                    return
                
                ok, msg = self.push_mgr.check_target(target_id)
                self.send_json({"success": ok, "status": msg})
            
            elif path == "/api/push/folder":
                target_id = data.get("target_id", "")
                folder_path = data.get("folder_path", "")
                
                if not target_id or not folder_path:
                    self.send_error_json("Target ID and folder path required")
                    return
                
                # 异步推送
                def push_task():
                    ok, msg = self.push_mgr.push_folder(target_id, folder_path)
                    print(f"[推送] 完成: {msg}")
                
                t = threading.Thread(target=push_task)
                t.daemon = True
                t.start()
                
                self.send_json({"success": True, "message": "Push started"})
            
            else:
                self.send_error_json("API endpoint not found", 404)
        
        except Exception as e:
            self.send_error_json(f"Internal error: {str(e)}", 500)
    
    def _handle_file_receive(self):
        """处理文件接收（multipart/form-data）"""
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            # 解析multipart/form-data
            boundary = content_type.split("boundary=")[1].strip()
            parts = body.split(f"--{boundary}".encode())
            
            folder_name = "upload"
            filepath = "file"
            file_data = b""
            
            for part in parts:
                if not part.strip():
                    continue
                
                # 提取folder字段
                if b'name="folder"' in part:
                    lines = part.split(b"\r\n")
                    if len(lines) >= 4:
                        folder_name = lines[3].decode().strip()
                
                # 提取filepath字段
                elif b'name="filepath"' in part:
                    lines = part.split(b"\r\n")
                    if len(lines) >= 4:
                        filepath = lines[3].decode().strip()
                
                # 提取file字段
                elif b'name="file"' in part:
                    idx = part.find(b"\r\n\r\n")
                    if idx >= 0:
                        file_data = part[idx+4:].rstrip(b"\r\n")
            
            if file_data:
                ok, size = self.push_mgr.receive_file(folder_name, filepath, file_data)
                self.send_json({"success": ok, "size": size})
            else:
                self.send_json({"success": True, "message": "No file data"})
        
        except Exception as e:
            self.send_error_json(f"Receive error: {str(e)}", 500)
    
    def send_html(self, html: str):
        """发送HTML响应"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
    
    def log_message(self, format: str, *args):
        """自定义日志格式"""
        print(f"[NAS API] {args[0]}")


# ==========================================
# Web前端界面
# ==========================================
INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小思超级NAS - 管理控制台 (第二代)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 24px; }
        .header-info { font-size: 13px; opacity: 0.9; margin-left: 20px; }
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
        <div style="display:flex;align-items:center;">
            <h1 id="app-title">小思超级NAS 管理控制台</h1>
            <div class="header-info">第二代 · 零依赖 · Python</div>
        </div>
        <div>
            <select class="lang-select" id="langSelect"></select>
        </div>
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
            <!-- 控制台 -->
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
                    <button class="btn btn-primary btn-sm" onclick="loadLocalIPs()" data-i18n="scan">扫描</button>
                </div>
            </div>
            
            <!-- 存储管理 -->
            <div class="page" id="page-storage">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <div class="card-title" style="margin-bottom:0;" data-i18n="volumes">存储卷</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('storage')" data-i18n="create">创建</button>
                    </div>
                    <table>
                        <thead><tr><th data-i18n="name">名称</th><th data-i18n="path">路径</th><th data-i18n="quota">配额(GB)</th><th data-i18n="operation">操作</th></tr></thead>
                        <tbody id="volumes-table"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 用户管理 -->
            <div class="page" id="page-users">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <div class="card-title" style="margin-bottom:0;" data-i18n="users">用户</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('user')" data-i18n="create">创建</button>
                    </div>
                    <table>
                        <thead><tr><th data-i18n="username">用户名</th><th data-i18n="home_directory">主目录</th><th data-i18n="storage_quota">配额(GB)</th><th data-i18n="admin">管理员</th><th data-i18n="operation">操作</th></tr></thead>
                        <tbody id="users-table"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 共享管理 -->
            <div class="page" id="page-shares">
                <div class="card">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <div class="card-title" style="margin-bottom:0;" data-i18n="shares">共享</div>
                        <button class="btn btn-primary btn-sm" onclick="showModal('share')" data-i18n="create">创建</button>
                    </div>
                    <table>
                        <thead><tr><th data-i18n="share_name">共享名称</th><th data-i18n="path">路径</th><th data-i18n="operation">操作</th></tr></thead>
                        <tbody id="shares-table"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 推送管理 -->
            <div class="page" id="page-push">
                <div class="two-col">
                    <div class="card">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                            <div class="card-title" style="margin-bottom:0;" data-i18n="push_targets">推送目标</div>
                            <button class="btn btn-primary btn-sm" onclick="showModal('target')" data-i18n="add_target">添加目标</button>
                        </div>
                        <table>
                            <thead><tr><th data-i18n="name">名称</th><th data-i18n="ip_address">IP</th><th data-i18n="operation">操作</th></tr></thead>
                            <tbody id="targets-table"></tbody>
                        </table>
                    </div>
                    
                    <div class="card">
                        <div class="card-title" data-i18n="found_devices">发现设备</div>
                        <div id="scan-result" style="margin-bottom:15px;">
                            <span style="color:#999;">点击扫描按钮发现局域网内的设备</span>
                        </div>
                        <button class="btn btn-success btn-sm" onclick="scanLAN()" data-i18n="scan">扫描局域网</button>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title" data-i18n="push_folder">推送文件夹</div>
                    <div class="form-group">
                        <label data-i18n="target_device">目标设备</label>
                        <select id="push-target-select"><option value="">请选择目标设备</option></select>
                    </div>
                    <div class="form-group">
                        <label data-i18n="local_folder">本地文件夹路径</label>
                        <input type="text" id="push-folder-path" placeholder="例如: C:\\Users\\Documents">
                    </div>
                    <div class="form-group">
                        <label data-i18n="progress">进度</label>
                        <div class="progress-bar"><div class="fill" id="push-progress" style="width:0%"></div></div>
                        <div id="push-status-text" style="margin-top:8px;font-size:13px;color:#666;">等待推送</div>
                    </div>
                    <button class="btn btn-primary" onclick="startPush()" id="push-btn" data-i18n="push_now">立即推送</button>
                </div>
                
                <div class="card">
                    <div class="card-title" data-i18n="push_history">推送历史</div>
                    <table>
                        <thead><tr><th>时间</th><th>目标</th><th>文件夹</th><th>文件数</th><th>状态</th></tr></thead>
                        <tbody id="push-history"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 创建存储卷 -->
    <div class="modal" id="modal-storage">
        <div class="modal-content">
            <div class="modal-title" data-i18n="create_volume">创建存储卷</div>
            <div class="form-group"><label data-i18n="name">名称</label><input type="text" id="storage-name"></div>
            <div class="form-group"><label data-i18n="path">路径</label><input type="text" id="storage-path"></div>
            <div class="form-group"><label data-i18n="quota">配额(GB)</label><input type="number" id="storage-quota" value="100"></div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('storage')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createVolume()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>
    
    <!-- 创建用户 -->
    <div class="modal" id="modal-user">
        <div class="modal-content">
            <div class="modal-title" data-i18n="create_user">创建用户</div>
            <div class="form-group"><label data-i18n="username">用户名</label><input type="text" id="user-name"></div>
            <div class="form-group"><label data-i18n="password">密码</label><input type="password" id="user-password"></div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('user')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createUser()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>
    
    <!-- 创建共享 -->
    <div class="modal" id="modal-share">
        <div class="modal-content">
            <div class="modal-title" data-i18n="create_share">创建共享</div>
            <div class="form-group"><label data-i18n="share_name">共享名称</label><input type="text" id="share-name"></div>
            <div class="form-group"><label data-i18n="path">路径</label><input type="text" id="share-path"></div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('share')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="createShare()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>
    
    <!-- 添加推送目标 -->
    <div class="modal" id="modal-target">
        <div class="modal-content">
            <div class="modal-title" data-i18n="add_target">添加推送目标</div>
            <div class="form-group"><label data-i18n="target_name">目标名称</label><input type="text" id="target-name"></div>
            <div class="form-row">
                <div class="form-group"><label data-i18n="target_ip">目标IP</label><input type="text" id="target-ip"></div>
                <div class="form-group"><label data-i18n="target_port">目标端口</label><input type="number" id="target-port" value="8080"></div>
            </div>
            <div class="form-actions">
                <button class="btn" onclick="closeModal('target')" data-i18n="cancel">取消</button>
                <button class="btn btn-primary" onclick="addTarget()" data-i18n="save">保存</button>
            </div>
        </div>
    </div>
    
<script>
const LANG_NAMES = {
    "zh_CN": "简体中文", "zh_TW": "繁體中文", "en_US": "English (US)", "en_GB": "English (UK)",
    "ja_JP": "日本語", "ko_KR": "한국어", "fr_FR": "Français", "de_DE": "Deutsch",
    "es_ES": "Español", "it_IT": "Italiano", "pt_BR": "Português (BR)", "ru_RU": "Русский",
    "ar_SA": "العربية", "hi_IN": "हिन्दी", "tr_TR": "Türkçe", "th_TH": "ไทย",
    "vi_VN": "Tiếng Việt", "id_ID": "Bahasa Indonesia", "nl_NL": "Nederlands", "pl_PL": "Polski",
    "sv_SE": "Svenska", "da_DK": "Dansk", "fi_FI": "Suomi", "he_IL": "עברית",
    "hu_HU": "Magyar", "cs_CZ": "Čeština", "uk_UA": "Українська", "ro_RO": "Română"
};

let translations = {};
let currentLang = 'zh_CN';

function initLangSelect() {
    const sel = document.getElementById('langSelect');
    Object.entries(LANG_NAMES).forEach(([code, name]) => {
        const opt = document.createElement('option');
        opt.value = code;
        opt.textContent = name;
        if (code === currentLang) opt.selected = true;
        sel.appendChild(opt);
    });
    sel.addEventListener('change', () => loadTranslations(sel.value));
}

async function loadTranslations(lang) {
    currentLang = lang;
    try {
        const res = await fetch('/api/i18n?lang=' + lang);
        translations = await res.json();
        applyTranslations();
    } catch (e) {
        console.error('Failed to load translations');
    }
}

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        if (translations[key]) el.textContent = translations[key];
    });
    if (translations['app_name']) {
        document.getElementById('app-title').textContent = translations['app_name'] + ' - 管理控制台';
    }
}

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        item.classList.add('active');
        document.getElementById('page-' + item.dataset.page).classList.add('active');
        
        if (item.dataset.page === 'push') {
            loadPushTargets();
            updatePushTargetSelect();
            loadPushHistory();
        } else if (item.dataset.page === 'dashboard') {
            loadDashboard();
            loadLocalIPs();
        } else if (item.dataset.page === 'storage') {
            loadVolumes();
        } else if (item.dataset.page === 'users') {
            loadUsers();
        } else if (item.dataset.page === 'shares') {
            loadShares();
        }
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
    } catch (e) {
        console.error(e);
    }
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
                div.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;width:100%;">' +
                    '<div><div class="ip" style="font-size:16px;">' + ip.ip + '</div>' +
                    '<div style="font-size:12px;color:#666;margin-top:2px;">' + (ip.name || ip.adapter) + ' | ' + (ip.network || '') + '</div></div>' +
                    '<div style="display:flex;align-items:center;gap:8px;">' +
                    '<span style="background:' + typeColor + ';color:white;padding:2px 8px;border-radius:10px;font-size:11px;">' + typeLabel + '</span>' +
                    '<span style="font-size:11px;color:#999;">ID:' + (ip.device_id || 'N/A') + '</span></div></div>';
                container.appendChild(div);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

async function scanLAN() {
    const resultDiv = document.getElementById('scan-result');
    resultDiv.innerHTML = '<span style="color:#667eea;">正在扫描局域网设备...</span>';
    
    try {
        const res = await fetch('/api/ip/scan?port=8080');
        const data = await res.json();
        
        if (data.devices && data.devices.length) {
            let html = '<div style="margin-bottom:10px;font-weight:600;">发现 ' + data.devices.length + ' 台设备:</div>';
            data.devices.forEach(d => {
                html += '<div class="ip-item" style="margin-bottom:8px;display:inline-flex;align-items:center;gap:10px;">' +
                    '<div><div class="ip">' + d.ip + ':' + d.port + '</div>' +
                    '<div class="type">' + (translations['online'] || '在线') + '</div></div>' +
                    '<button class="btn btn-primary btn-sm" onclick="quickAddTarget(\'' + d.ip + '\', ' + d.port + ')">' + (translations['add_target'] || '添加') + '</button></div>';
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
        data.targets.map(t => '<tr><td>' + t.name + '</td><td>' + t.ip + ':' + t.port + '</td><td><button class="btn btn-success btn-sm" onclick="checkTarget(\'' + t.id + '\')">检测</button> <button class="btn btn-danger btn-sm" onclick="deleteTarget(\'' + t.id + '\')">' + (translations['delete'] || '删除') + '</button></td></tr>').join('') :
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
    const res = await fetch('/api/push/targets/check', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({id})
    });
    const data = await res.json();
    alert(data.status);
}

async function addTarget() {
    const name = document.getElementById('target-name').value;
    const ip = document.getElementById('target-ip').value;
    const port = parseInt(document.getElementById('target-port').value);
    
    if (!name || !ip) {
        alert('请填写名称和IP');
        return;
    }
    
    await fetch('/api/push/targets', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, ip, port})
    });
    
    closeModal('target');
    loadPushTargets();
    updatePushTargetSelect();
}

async function deleteTarget(id) {
    if (confirm('确认删除此目标?')) {
        await fetch('/api/push/targets/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id})
        });
        loadPushTargets();
        updatePushTargetSelect();
    }
}

async function startPush() {
    const targetId = document.getElementById('push-target-select').value;
    const folderPath = document.getElementById('push-folder-path').value;
    
    if (!targetId) {
        alert('请选择目标设备');
        return;
    }
    if (!folderPath) {
        alert('请输入文件夹路径');
        return;
    }
    
    const btn = document.getElementById('push-btn');
    btn.disabled = true;
    btn.textContent = translations['pushing'] || '推送中...';
    
    document.getElementById('push-progress').style.width = '5%';
    document.getElementById('push-status-text').textContent = '准备推送...';
    
    try {
        await fetch('/api/push/folder', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({target_id: targetId, folder_path: folderPath})
        });
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
                document.getElementById('push-status-text').textContent =
                    data.active.sent_files + ' / ' + data.active.total_files + ' 个文件';
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
        tb.innerHTML = data.history.map(h => '<tr><td>' + (h.start_time || '') + '</td><td>' + h.target + '</td><td>' + h.folder + '</td><td>' + h.sent_files + ' / ' + h.total_files + '</td><td><span class="badge ' + (h.status === 'success' ? 'badge-success' : 'badge-danger') + '">' + (h.status === 'success' ? (t['success'] || '成功') : (t['failed'] || '失败')) + '</span></td></tr>').join('');
    } else {
        tb.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">' + (t['no_data'] || '暂无数据') + '</td></tr>';
    }
}

function showModal(type) {
    document.getElementById('modal-' + type).classList.add('show');
}

function closeModal(type) {
    document.getElementById('modal-' + type).classList.remove('show');
}

async function createVolume() {
    const name = document.getElementById('storage-name').value;
    const path = document.getElementById('storage-path').value;
    const quota = parseInt(document.getElementById('storage-quota').value);
    
    await fetch('/api/storage/volumes', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, path, quota_gb: quota})
    });
    
    closeModal('storage');
    loadVolumes();
    loadDashboard();
}

async function createUser() {
    const name = document.getElementById('user-name').value;
    const password = document.getElementById('user-password').value;
    
    await fetch('/api/users', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: name, password})
    });
    
    closeModal('user');
    loadUsers();
    loadDashboard();
}

async function createShare() {
    const name = document.getElementById('share-name').value;
    const path = document.getElementById('share-path').value;
    
    await fetch('/api/smb/shares', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, path})
    });
    
    closeModal('share');
    loadShares();
    loadDashboard();
}

async function deleteVolume(name) {
    if (confirm('确认删除 ' + name + '?')) {
        await fetch('/api/storage/volumes/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        loadVolumes();
        loadDashboard();
    }
}

async function deleteUser(username) {
    if (confirm('确认删除 ' + username + '?')) {
        await fetch('/api/users/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username})
        });
        loadUsers();
        loadDashboard();
    }
}

async function deleteShare(name) {
    if (confirm('确认删除 ' + name + '?')) {
        await fetch('/api/smb/shares/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        loadShares();
        loadDashboard();
    }
}

initLangSelect();
loadTranslations('zh_CN');
loadDashboard();
loadLocalIPs();
</script>
</body>
</html>"""


# ==========================================
# 服务器启动
# ==========================================
def run_server(port: int = 8080):
    """启动NAS服务器"""
    # 初始化管理器
    config = Config()
    storage_mgr = StorageManager(config)
    user_mgr = UserManager(config)
    smb_mgr = SMBManager(config)
    push_mgr = PushManager(config)
    
    # 设置HTTP处理器类属性
    NASHandler.config = config
    NASHandler.storage_mgr = storage_mgr
    NASHandler.user_mgr = user_mgr
    NASHandler.smb_mgr = smb_mgr
    NASHandler.push_mgr = push_mgr
    
    # 创建服务器
    server = HTTPServer(("0.0.0.0", port), NASHandler)
    local_ips = IPManager.get_local_ips()
    
    # 打印启动信息
    print("=" * 60)
    print("  小思超级NAS服务 (第二代) - Python实现")
    print("=" * 60)
    print(f"  版本: 第二代")
    print(f"  特性: 零依赖 · 仅使用Python标准库")
    print(f"  语言支持: 28种语言")
    print("=" * 60)
    print(f"  本地访问: http://localhost:{port}")
    
    for ip_info in local_ips:
        if ip_info["type"] != "loopback":
            print(f"  网络访问: http://{ip_info['ip']}:{port}")
    
    print(f"  接收目录: {os.path.abspath(config.receive_dir)}")
    print("=" * 60)
    print("  按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[服务] 正在停止...")
        server.shutdown()
        print("[服务] 已停止")


if __name__ == "__main__":
    # 从命令行参数获取端口（可选）
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"[错误] 无效的端口参数: {sys.argv[1]}")
            sys.exit(1)
    
    run_server(port)