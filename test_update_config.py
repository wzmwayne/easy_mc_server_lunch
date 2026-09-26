#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置更新功能
"""

import sys
from pathlib import Path

# 添加项目目录到路径
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from mc_server_manager import MCServerManager

def test_update_property():
    """测试配置更新功能"""
    print("=" * 60)
    print("测试配置更新功能")
    print("=" * 60)
    
    # 创建管理器实例
    data_dir = project_dir / 'data'
    manager = MCServerManager(str(data_dir))
    
    print(f"\n初始配置: {manager.properties}")
    print(f"配置文件存在: {manager.config_file.exists()}")
    
    # 测试添加新配置项
    test_configs = {
        'server-name': 'My Test Server',
        'motd': 'Welcome to my server!',
        'max-players': '20',
        'server-port': '25565',
        'gamemode': 'survival',
        'difficulty': 'easy',
        'pvp': 'true',
        'online-mode': 'true',
        'pause-when-empty-seconds': '60'
    }
    
    print("\n测试添加配置项:")
    for key, value in test_configs.items():
        result = manager.update_property(key, value)
        status = "✓" if result["success"] else "✗"
        print(f"  {status} {key}: {result['message']}")
    
    print(f"\n更新后配置: {manager.properties}")
    print(f"配置文件存在: {manager.config_file.exists()}")
    
    # 读取配置文件内容
    if manager.config_file.exists():
        print("\n配置文件内容:")
        with open(manager.config_file, 'r', encoding='utf-8') as f:
            print(f.read())
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_update_property()