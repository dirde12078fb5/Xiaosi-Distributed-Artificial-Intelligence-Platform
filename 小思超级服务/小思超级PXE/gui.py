#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小思超级PXE - GUI启动入口
"""

import sys
import os

# 确保可以找到模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import main

if __name__ == '__main__':
    main()
