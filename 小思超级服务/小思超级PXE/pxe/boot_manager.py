#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PXE启动配置管理器
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger('SuperPXE.BootManager')

class BootManager:
    def __init__(self, tftp_root='./tftpboot', http_root='./httpboot'):
        self.tftp_root = Path(tftp_root)
        self.http_root = Path(http_root)
        self.config_file = self.http_root / 'boot_config.json'
        self.config = self._load_config()
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.tftp_root,
            self.http_root,
            self.tftp_root / 'pxelinux.cfg',
            self.http_root / 'iso',
            self.http_root / 'images'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"确保目录存在: {directory}")
    
    def _load_config(self):
        """加载启动配置"""
        default_config = {
            'default_menu': 'default',
            'menus': {
                'default': {
                    'title': '小思超级PXE启动菜单',
                    'timeout': 30,
                    'entries': []
                }
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                logger.info("已加载启动配置")
            except Exception as e:
                logger.error(f"加载启动配置失败: {e}")
        
        return default_config
    
    def _save_config(self):
        """保存启动配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info("已保存启动配置")
            return True
        except Exception as e:
            logger.error(f"保存启动配置失败: {e}")
            return False
    
    def add_menu(self, menu_name, title, timeout=30):
        """添加启动菜单"""
        if menu_name in self.config['menus']:
            logger.warning(f"菜单已存在: {menu_name}")
            return False
        
        self.config['menus'][menu_name] = {
            'title': title,
            'timeout': timeout,
            'entries': []
        }
        
        return self._save_config()
    
    def remove_menu(self, menu_name):
        """删除启动菜单"""
        if menu_name not in self.config['menus']:
            logger.warning(f"菜单不存在: {menu_name}")
            return False
        
        if menu_name == self.config['default_menu']:
            logger.warning("不能删除默认菜单")
            return False
        
        del self.config['menus'][menu_name]
        return self._save_config()
    
    def add_boot_entry(self, menu_name, entry_name, entry_type, **kwargs):
        """添加启动项"""
        if menu_name not in self.config['menus']:
            logger.warning(f"菜单不存在: {menu_name}")
            return False
        
        entry = {
            'name': entry_name,
            'type': entry_type
        }
        entry.update(kwargs)
        
        self.config['menus'][menu_name]['entries'].append(entry)
        logger.info(f"已添加启动项: {entry_name}")
        
        self._generate_pxelinux_config()
        return self._save_config()
    
    def remove_boot_entry(self, menu_name, entry_name):
        """删除启动项"""
        if menu_name not in self.config['menus']:
            logger.warning(f"菜单不存在: {menu_name}")
            return False
        
        menu = self.config['menus'][menu_name]
        for i, entry in enumerate(menu['entries']):
            if entry['name'] == entry_name:
                del menu['entries'][i]
                logger.info(f"已删除启动项: {entry_name}")
                self._generate_pxelinux_config()
                return self._save_config()
        
        logger.warning(f"启动项不存在: {entry_name}")
        return False
    
    def set_default_menu(self, menu_name):
        """设置默认菜单"""
        if menu_name not in self.config['menus']:
            logger.warning(f"菜单不存在: {menu_name}")
            return False
        
        self.config['default_menu'] = menu_name
        self._generate_pxelinux_config()
        return self._save_config()
    
    def _generate_pxelinux_config(self):
        """生成PXELINUX配置文件"""
        default_menu = self.config['menus'][self.config['default_menu']]
        
        config_lines = [
            'DEFAULT menu.c32',
            'PROMPT 0',
            f'NOESCAPE 0',
            f'ALLOWOPTIONS 0',
            f'TIMEOUT {default_menu["timeout"] * 10}',
            f'MENU TITLE {default_menu["title"]}',
            ''
        ]
        
        for entry in default_menu['entries']:
            config_lines.extend(self._generate_entry_config(entry))
            config_lines.append('')
        
        config_content = '\n'.join(config_lines)
        
        config_path = self.tftp_root / 'pxelinux.cfg' / 'default'
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            logger.info(f"已生成PXELINUX配置: {config_path}")
        except Exception as e:
            logger.error(f"生成PXELINUX配置失败: {e}")
    
    def _generate_entry_config(self, entry):
        """生成单个启动项的配置"""
        lines = []
        
        if entry['type'] == 'linux':
            lines.append(f'LABEL {entry["name"].replace(" ", "_")}')
            lines.append(f'  MENU LABEL {entry["name"]}')
            lines.append(f'  KERNEL {entry.get("kernel", "vmlinuz")}')
            if 'initrd' in entry:
                lines.append(f'  INITRD {entry["initrd"]}')
            if 'append' in entry:
                lines.append(f'  APPEND {entry["append"]}')
        
        elif entry['type'] == 'iso':
            lines.append(f'LABEL {entry["name"].replace(" ", "_")}')
            lines.append(f'  MENU LABEL {entry["name"]}')
            lines.append(f'  KERNEL memdisk')
            lines.append(f'  INITRD {entry["iso_path"]}')
            lines.append(f'  APPEND iso')
        
        elif entry['type'] == 'local':
            lines.append(f'LABEL {entry["name"].replace(" ", "_")}')
            lines.append(f'  MENU LABEL {entry["name"]}')
            lines.append(f'  LOCALBOOT 0')
        
        return lines
    
    def list_menus(self):
        """列出所有菜单"""
        return list(self.config['menus'].keys())
    
    def list_entries(self, menu_name):
        """列出菜单中的所有启动项"""
        if menu_name not in self.config['menus']:
            return []
        return self.config['menus'][menu_name]['entries']
    
    def get_config(self):
        """获取当前配置"""
        return self.config.copy()
