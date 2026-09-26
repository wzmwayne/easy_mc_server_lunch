#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置加载功能
"""

import sys
from pathlib import Path

# 添加项目目录到路径
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from mc_server_manager import MCServerManager

def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试配置加载功能")
    print("=" * 60)
    
    # 创建管理器实例
    data_dir = project_dir / 'data'
    print(f"\n数据目录: {data_dir}")
    print(f"数据目录存在: {data_dir.exists()}")
    
    manager = MCServerManager(str(data_dir))
    
    print(f"\n配置文件: {manager.config_file}")
    print(f"配置文件存在: {manager.config_file.exists()}")
    
    print(f"\n当前配置: {manager.properties}")
    print(f"配置项数量: {len(manager.properties)}")
    
    # 测试默认配置
    default_configs = {
        'server-name': 'Minecraft Server',
        'motd': 'A Minecraft Server',
        'max-players': '20',
        'server-port': '25565',
        'gamemode': 'survival',
        'difficulty': 'easy',
        'pvp': 'true',
        'online-mode': 'true',
        'pause-when-empty-seconds': '60'
    }
    
    print("\n默认配置检查:")
    for key, default_value in default_configs.items():
        if key in manager.properties:
            print(f"  ✓ {key}: {manager.properties[key]}")
        else:
            print(f"  ✗ {key}: 缺失 (默认值: {default_value})")
    
    # 测试 API 响应格式
    print("\n模拟 API 响应:")
    config = manager.properties.copy()
    for key, default_value in default_configs.items():
        if key not in config:
            config[key] = default_value
    
    print(f"返回的配置: {config}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    test_config_loading()