#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块
"""

from .platform import (
    get_platform_info,
    is_windows,
    is_linux,
    is_macos,
    get_network_interfaces,
    check_admin_privileges,
    elevate_privileges,
    open_firewall_port,
    get_local_ip
)

__all__ = [
    'get_platform_info',
    'is_windows',
    'is_linux',
    'is_macos',
    'get_network_interfaces',
    'check_admin_privileges',
    'elevate_privileges',
    'open_firewall_port',
    'get_local_ip'
]
