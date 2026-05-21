#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级PXE - 命令行界面
"""

import argparse
import sys
import logging
import os
import json
from pathlib import Path
from pxe_server import SuperPXE
from pxe import BootManager
from utils import check_admin_privileges, elevate_privileges

def setup_logging(log_level='INFO'):
    """设置日志"""
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    
    logging.basicConfig(
        level=level_map.get(log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )

def run_diagnose():
    """运行诊断工具"""
    print("\n" + "="*70)
    print("  🔧 小思超级PXE - 高级诊断工具")
    print("="*70)
    print()
    
    # 导入高级诊断模块
    import diagnose_advanced
    
    # 运行诊断
    diagnose_advanced.main()

def init_config():
    """初始化配置文件"""
    if Path('config.json').exists():
        print("配置文件 config.json 已存在！")
        return
    
    if not Path('config.example.json').exists():
        print("错误：找不到 config.example.json")
        return
    
    import shutil
    shutil.copy('config.example.json', 'config.json')
    print("✅ 已创建配置文件 config.json")
    print()
    print("请编辑 config.json 以匹配您的网络环境！")

def main():
    parser = argparse.ArgumentParser(
        description='小思超级PXE - Python跨平台网络安装系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s diagnose            # 运行诊断工具
  %(prog)s init                # 初始化配置文件
  %(prog)s gui                 # 启动图形用户界面
  %(prog)s server              # 启动PXE服务器
  %(prog)s menu list           # 列出所有启动菜单
  %(prog)s entry add "Ubuntu" linux --kernel vmlinuz --initrd initrd.img --append "root=/dev/nfs"
'''
    )
    
    subparsers = parser.add_subparsers(title='命令', dest='command', help='可用命令')
    
    # diagnose command
    diagnose_parser = subparsers.add_parser('diagnose', help='运行诊断工具')
    
    # init command
    init_parser = subparsers.add_parser('init', help='初始化配置文件')
    
    # gui command
    gui_parser = subparsers.add_parser('gui', help='启动图形用户界面')
    
    # server command
    server_parser = subparsers.add_parser('server', help='启动PXE服务器')
    server_parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='配置文件路径 (默认: config.json)'
    )
    server_parser.add_argument(
        '--no-elevate',
        action='store_true',
        help='不尝试提升权限'
    )
    
    # menu命令
    menu_parser = subparsers.add_parser('menu', help='启动菜单管理')
    menu_subparsers = menu_parser.add_subparsers(title='菜单操作', dest='menu_action')
    
    # menu list
    menu_list_parser = menu_subparsers.add_parser('list', help='列出所有菜单')
    
    # menu add
    menu_add_parser = menu_subparsers.add_parser('add', help='添加菜单')
    menu_add_parser.add_argument('name', help='菜单名称')
    menu_add_parser.add_argument('title', help='菜单标题')
    menu_add_parser.add_argument('--timeout', type=int, default=30, help='超时时间(秒)')
    
    # menu remove
    menu_remove_parser = menu_subparsers.add_parser('remove', help='删除菜单')
    menu_remove_parser.add_argument('name', help='菜单名称')
    
    # menu default
    menu_default_parser = menu_subparsers.add_parser('default', help='设置默认菜单')
    menu_default_parser.add_argument('name', help='菜单名称')
    
    # entry命令
    entry_parser = subparsers.add_parser('entry', help='启动项管理')
    entry_subparsers = entry_parser.add_subparsers(title='启动项操作', dest='entry_action')
    
    # entry list
    entry_list_parser = entry_subparsers.add_parser('list', help='列出菜单中的启动项')
    entry_list_parser.add_argument('--menu', default='default', help='菜单名称')
    
    # entry add
    entry_add_parser = entry_subparsers.add_parser('add', help='添加启动项')
    entry_add_parser.add_argument('name', help='启动项名称')
    entry_add_parser.add_argument(
        'type',
        choices=['linux', 'iso', 'local'],
        help='启动项类型'
    )
    entry_add_parser.add_argument('--menu', default='default', help='菜单名称')
    entry_add_parser.add_argument('--kernel', help='Linux内核文件')
    entry_add_parser.add_argument('--initrd', help='initrd文件')
    entry_add_parser.add_argument('--append', help='内核参数')
    entry_add_parser.add_argument('--iso-path', help='ISO文件路径')
    
    # entry remove
    entry_remove_parser = entry_subparsers.add_parser('remove', help='删除启动项')
    entry_remove_parser.add_argument('name', help='启动项名称')
    entry_remove_parser.add_argument('--menu', default='default', help='菜单名称')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger('SuperPXE')
    
    if args.command == 'diagnose':
        run_diagnose()
    
    elif args.command == 'init':
        init_config()
    
    elif args.command == 'gui':
        # 启动GUI
        from gui.main_window import main as gui_main
        gui_main()
    
    elif args.command == 'server':
        # 检查权限
        if not args.no_elevate and not check_admin_privileges():
            logger.info('需要管理员/root权限，尝试提升权限...')
            if not elevate_privileges():
                logger.error('提升权限失败，请以管理员/root身份运行')
                return 1
        
        # 启动服务器
        logger.info('=' * 50)
        logger.info('小思超级PXE - Python跨平台网络安装系统')
        logger.info('=' * 50)
        
        pxe = SuperPXE(args.config)
        try:
            pxe.start()
        except KeyboardInterrupt:
            logger.info('收到停止信号')
            pxe.stop()
        except Exception as e:
            logger.error(f'服务器运行出错: {e}')
            return 1
    
    elif args.command == 'menu':
        boot_manager = BootManager()
        
        if args.menu_action == 'list':
            menus = boot_manager.list_menus()
            print('启动菜单列表:')
            for menu in menus:
                default_mark = ' (默认)' if menu == boot_manager.config['default_menu'] else ''
                print(f'  - {menu}{default_mark}')
        
        elif args.menu_action == 'add':
            if boot_manager.add_menu(args.name, args.title, args.timeout):
                print(f'成功添加菜单: {args.name}')
            else:
                print(f'添加菜单失败: {args.name}')
        
        elif args.menu_action == 'remove':
            if boot_manager.remove_menu(args.name):
                print(f'成功删除菜单: {args.name}')
            else:
                print(f'删除菜单失败: {args.name}')
        
        elif args.menu_action == 'default':
            if boot_manager.set_default_menu(args.name):
                print(f'成功设置默认菜单: {args.name}')
            else:
                print(f'设置默认菜单失败: {args.name}')
    
    elif args.command == 'entry':
        boot_manager = BootManager()
        
        if args.entry_action == 'list':
            entries = boot_manager.list_entries(args.menu)
            print(f'菜单 "{args.menu}" 中的启动项:')
            if not entries:
                print('  (无)')
            else:
                for entry in entries:
                    print(f'  - {entry["name"]} ({entry["type"]})')
        
        elif args.entry_action == 'add':
            kwargs = {}
            if args.type == 'linux':
                if args.kernel:
                    kwargs['kernel'] = args.kernel
                if args.initrd:
                    kwargs['initrd'] = args.initrd
                if args.append:
                    kwargs['append'] = args.append
            elif args.type == 'iso':
                if args.iso_path:
                    kwargs['iso_path'] = args.iso_path
            
            if boot_manager.add_boot_entry(args.menu, args.name, args.type, **kwargs):
                print(f'成功添加启动项: {args.name}')
            else:
                print(f'添加启动项失败: {args.name}')
        
        elif args.entry_action == 'remove':
            if boot_manager.remove_boot_entry(args.menu, args.name):
                print(f'成功删除启动项: {args.name}')
            else:
                print(f'删除启动项失败: {args.name}')
    
    else:
        parser.print_help()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
