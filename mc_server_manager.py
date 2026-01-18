#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minecraft Fabric Server Manager
基于Flask的Web界面MC服务器管理端
"""

# ============================================================================
# =========================== 可修改配置区域 ===========================
# ============================================================================

# 调试模式
# True: 显示详细的调试信息（终端和浏览器控制台）
# False: 不显示调试信息
DEBUG_MODE = False

# Flask 配置
FLASK_HOST = '0.0.0.0'  # 监听地址（0.0.0.0 = 所有网络接口，127.0.0.1 = 仅本地）
FLASK_PORT = 5000       # 监听端口
FLASK_DEBUG = False     # Flask 调试模式（不建议在生产环境启用）

# 服务器配置
SERVER_DATA_DIR = './data'  # 服务器数据目录（相对路径）
SERVER_LOG_LINES = 100      # 日志显示行数
SERVER_POLL_INTERVAL = 1    # 日志轮询间隔（秒）
STATUS_POLL_INTERVAL = 5    # 状态轮询间隔（秒）

# 认证配置
# 已禁用鉴权码功能

# ============================================================================
# =========================== 配置区域结束 ===========================
# ============================================================================

import os
import sys
import json
import subprocess
import shutil
import urllib.request
import time
import signal
import threading
import hashlib
import secrets
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    from flask import Flask, render_template, jsonify, request, redirect
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class Colors:
    """终端颜色定义"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class MCServerManager:
    """Minecraft Fabric服务器管理器"""
    
    def __init__(self, server_dir: str = None):
        """初始化管理器"""
        self.server_dir = Path(server_dir) if server_dir else Path.cwd()
        self.server_process = None
        self.server_lock = threading.Lock()
        self.config_file = self.server_dir / "server.properties"
        self.whitelist_file = self.server_dir / "whitelist.json"
        self.ops_file = self.server_dir / "ops.json"
        self.banned_players_file = self.server_dir / "banned-players.json"
        self.banned_ips_file = self.server_dir / "banned-ips.json"
        self.mods_dir = self.server_dir / "mods"
        self.logs_dir = self.server_dir / "logs"
        self.backups_dir = self.server_dir / "backups"
        
        # 创建必要的目录
        self.mods_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self.properties = self._load_properties()
        self.whitelist = self._load_json(self.whitelist_file, [])
        self.ops = self._load_json(self.ops_file, [])
        self.banned_players = self._load_json(self.banned_players_file, [])
        self.banned_ips = self._load_json(self.banned_ips_file, [])
        
        # 日志监控
        self.log_watcher_active = False
        self.log_position = 0
        
        # 命令输出队列（持久化）
        self.command_output_queue = []
        self.command_output_lock = threading.Lock()
        
        # 加载持久化的输出
        self._load_persistent_output()
        
        # 时间同步
        self.time_sync_enabled = True
        self.time_sync_interval = 3600  # 每小时同步一次（秒）
        self.last_time_sync = 0
        
        # 启动时自动同步时间
        self.sync_system_time()
    
    def _load_properties(self) -> Dict[str, str]:
        """加载server.properties文件"""
        props = {}
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        props[key.strip()] = value.strip()
        return props
    
    def _save_properties(self):
        """保存server.properties文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            for key, value in self.properties.items():
                f.write(f"{key}={value}\n")
    
    def update_property(self, key: str, value: str) -> Dict:
        """更新服务器配置属性"""
        result = {"success": False, "message": ""}
        
        if key not in self.properties:
            result["message"] = f"配置项 {key} 不存在"
            return result
        
        self.properties[key] = value
        self._save_properties()
        
        result["success"] = True
        result["message"] = f"配置项 {key} 已更新为 {value}"
        return result
    
    def _load_json(self, file_path: Path, default):
        """加载JSON文件"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return default
        return default
    
    def _save_json(self, file_path: Path, data):
        """保存JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def _format_log_message(self, message: str) -> str:
        """格式化日志消息，保留所有原始输出"""
        import re
        
        # 不进行任何格式化，直接返回原始消息
        # 这样可以显示所有终端输出内容
        return message
    
    def _log_command_output(self, message: str, level: str = "output"):
        """记录命令输出到队列、控制台和日志文件"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 格式化消息（移除 Minecraft 服务器日志中的冗余信息）
        formatted_message = self._format_log_message(message)
        
        output = {
            "timestamp": timestamp,
            "message": formatted_message,
            "level": level
        }
        
        # 输出到控制台（带颜色）
        if level == "error":
            print(f"{Colors.FAIL}[{timestamp}] {formatted_message}{Colors.ENDC}")
        elif level == "success":
            print(f"{Colors.OKGREEN}[{timestamp}] {formatted_message}{Colors.ENDC}")
        elif level == "info":
            print(f"{Colors.OKCYAN}[{timestamp}] {formatted_message}{Colors.ENDC}")
        elif level == "command":
            print(f"{Colors.WARNING}[{timestamp}] 命令: {formatted_message}{Colors.ENDC}")
        else:
            print(f"[{timestamp}] {formatted_message}")
        
        # 添加到队列
        with self.command_output_lock:
            self.command_output_queue.append(output)
            # 限制队列大小，保留最近500条
            if len(self.command_output_queue) > 500:
                self.command_output_queue = self.command_output_queue[-500:]
        
        # 保存到持久化文件
        self._save_persistent_output()
        
        # 保存到统一日志文件（带颜色标记）
        self._save_to_unified_log(timestamp, formatted_message, level)
    
    def _save_to_unified_log(self, timestamp: str, message: str, level: str):
        """保存到统一日志文件（带自动创建目录和实时刷新）"""
        unified_log_file = self.logs_dir / "unified.log"
        
        # 自动创建日志目录
        if not self.logs_dir.exists():
            try:
                self.logs_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"{Colors.WARNING}创建日志目录失败: {e}{Colors.ENDC}")
                return
        
        try:
            # 追加模式写入，并立即刷新
            with open(unified_log_file, 'a', encoding='utf-8', buffering=1) as f:
                f.write(f"[{timestamp}] [{level.upper()}] {message}\n")
                f.flush()  # 立即刷新到磁盘
        except Exception as e:
            print(f"{Colors.WARNING}写入日志失败: {e}{Colors.ENDC}")
    
    def _load_persistent_output(self):
        """从文件加载持久化的输出"""
        output_file = self.server_dir / ".persistent_output.json"
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    self.command_output_queue = json.load(f)
                    # 限制加载的输出数量
                    if len(self.command_output_queue) > 500:
                        self.command_output_queue = self.command_output_queue[-500:]
            except Exception as e:
                print(f"{Colors.WARNING}加载持久化输出失败: {e}{Colors.ENDC}")
                self.command_output_queue = []
    
    def _save_persistent_output(self):
        """保存输出到持久化文件"""
        output_file = self.server_dir / ".persistent_output.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.command_output_queue, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"{Colors.WARNING}保存持久化输出失败: {e}{Colors.ENDC}")
    
    def sync_system_time(self) -> Dict:
        """同步系统时间"""
        result = {"success": False, "message": ""}
        
        if not self.time_sync_enabled:
            result["message"] = "时间同步功能已禁用"
            return result
        
        # 检查是否需要同步
        current_time = time.time()
        if current_time - self.last_time_sync < self.time_sync_interval:
            result["message"] = f"距离上次同步不足 {self.time_sync_interval} 秒，跳过"
            return result
        
        self._log_command_output("开始同步系统时间...", "info")
        
        try:
            # 方法1: 使用 ntpdate 命令（如果可用）
            ntp_servers = [
                "pool.ntp.org",
                "time.google.com",
                "time.cloudflare.com",
                "time.apple.com"
            ]
            
            for ntp_server in ntp_servers:
                try:
                    self._log_command_output(f"尝试从 {ntp_server} 同步时间...", "info")
                    return_code, output_lines = self._run_command_with_output(
                        ['ntpdate', '-u', ntp_server],
                        cwd=None
                    )
                    
                    if return_code == 0:
                        self.last_time_sync = time.time()
                        self._log_command_output(f"时间同步成功: {ntp_server}", "success")
                        result["success"] = True
                        result["message"] = f"时间同步成功: {ntp_server}"
                        return result
                except FileNotFoundError:
                    continue
                except Exception as e:
                    self._log_command_output(f"使用 {ntp_server} 同步失败: {e}", "warning")
                    continue
            
            # 方法2: 使用多个网络时间API
            time_apis = [
                'http://worldtimeapi.org/api/timezone/Etc/UTC',
                'http://worldtimeapi.org/api/ip',
                'https://timeapi.io/api/Time/current/zone?timeZone=UTC'
            ]
            
            for api_url in time_apis:
                try:
                    self._log_command_output(f"尝试使用网络时间API同步: {api_url}", "info")
                    
                    # 获取网络时间戳
                    response = urllib.request.urlopen(api_url, timeout=10)
                    data = json.loads(response.read().decode())
                    
                    # 根据不同的API响应格式提取时间戳
                    if 'unixtime' in data:
                        network_time = data['unixtime']
                    elif 'unixTime' in data:
                        network_time = data['unixTime']
                    elif 'datetime' in data:
                        # 解析ISO格式时间
                        from datetime import datetime
                        dt = datetime.fromisoformat(data['datetime'].replace('Z', '+00:00'))
                        network_time = int(dt.timestamp())
                    else:
                        self._log_command_output(f"无法解析时间API响应: {api_url}", "warning")
                        continue
                    
                    # 设置系统时间
                    import os
                    os.system(f'date -u @{network_time}')
                    
                    self.last_time_sync = time.time()
                    self._log_command_output(f"时间同步成功: {api_url}", "success")
                    result["success"] = True
                    result["message"] = f"时间同步成功: {api_url}"
                    return result
                    
                except Exception as e:
                    self._log_command_output(f"网络时间API同步失败 ({api_url}): {e}", "warning")
                    continue
            
            # 方法3: 使用 timedatectl（如果可用）
            try:
                return_code, output_lines = self._run_command_with_output(
                    ['timedatectl', 'set-ntp', 'true'],
                    cwd=None
                )
                
                if return_code == 0:
                    self.last_time_sync = time.time()
                    self._log_command_output("时间同步成功: timedatectl", "success")
                    result["success"] = True
                    result["message"] = "时间同步成功: timedatectl"
                    return result
            except FileNotFoundError:
                pass
            except Exception as e:
                self._log_command_output(f"timedatectl 同步失败: {e}", "warning")
            
            # 方法4: 使用 ntpdig（如果可用）
            try:
                self._log_command_output("尝试使用 ntpdig 同步时间...", "info")
                return_code, output_lines = self._run_command_with_output(
                    ['ntpdig', '-N', 'time.google.com'],
                    cwd=None
                )
                
                if return_code == 0 and output_lines:
                    # 解析ntpdig输出获取时间戳
                    for line in output_lines:
                        if line.strip():
                            try:
                                # ntpdig输出格式通常是: 1234567890.123
                                timestamp = float(line.strip().split()[0])
                                import os
                                os.system(f'date -u @{int(timestamp)}')
                                
                                self.last_time_sync = time.time()
                                self._log_command_output("时间同步成功: ntpdig", "success")
                                result["success"] = True
                                result["message"] = "时间同步成功: ntpdig"
                                return result
                            except (ValueError, IndexError):
                                continue
            except FileNotFoundError:
                pass
            except Exception as e:
                self._log_command_output(f"ntpdig 同步失败: {e}", "warning")
            
            # 方法5: 使用 sntp（如果可用）
            try:
                self._log_command_output("尝试使用 sntp 同步时间...", "info")
                return_code, output_lines = self._run_command_with_output(
                    ['sntp', '-Ss', 'time.google.com'],
                    cwd=None
                )
                
                if return_code == 0:
                    self.last_time_sync = time.time()
                    self._log_command_output("时间同步成功: sntp", "success")
                    result["success"] = True
                    result["message"] = "时间同步成功: sntp"
                    return result
            except FileNotFoundError:
                pass
            except Exception as e:
                self._log_command_output(f"sntp 同步失败: {e}", "warning")
            
            result["message"] = "所有时间同步方法都失败了（可能需要安装ntpdate或网络连接问题）"
            return result
            
        except Exception as e:
            self._log_command_output(f"时间同步出错: {e}", "error")
            result["message"] = f"时间同步出错: {e}"
            return result
    
    def get_time_sync_status(self) -> Dict:
        """获取时间同步状态"""
        status = {
            "enabled": self.time_sync_enabled,
            "last_sync": self.last_time_sync,
            "sync_interval": self.time_sync_interval,
            "current_time": time.time(),
            "time_until_next_sync": max(0, self.time_sync_interval - (time.time() - self.last_time_sync))
        }
        
        if self.last_time_sync > 0:
            from datetime import datetime
            last_sync_datetime = datetime.fromtimestamp(self.last_time_sync)
            status["last_sync_formatted"] = last_sync_datetime.strftime("%Y-%m-%d %H:%M:%S")
        else:
            status["last_sync_formatted"] = "从未同步"
        
        return status
    
    def enable_time_sync(self, interval: int = 3600) -> Dict:
        """启用时间同步"""
        result = {"success": False, "message": ""}
        
        if interval < 60:
            result["message"] = "同步间隔不能少于60秒"
            return result
        
        self.time_sync_enabled = True
        self.time_sync_interval = interval
        self._log_command_output(f"时间同步已启用，间隔: {interval} 秒", "success")
        
        result["success"] = True
        result["message"] = f"时间同步已启用，间隔: {interval} 秒"
        return result
    
    def disable_time_sync(self) -> Dict:
        """禁用时间同步"""
        self.time_sync_enabled = False
        self._log_command_output("时间同步已禁用", "info")
        
        return {
            "success": True,
            "message": "时间同步已禁用"
        }
    
    def _run_command_with_output(self, cmd: List[str], cwd: str = None) -> Tuple[int, List[str]]:
        """运行命令并实时捕获输出"""
        self._log_command_output(f"执行命令: {' '.join(cmd)}", "command")
        
        output_lines = []
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=cwd or str(self.server_dir)
            )
            
            # 实时读取输出
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    line = line.strip()
                    if line:  # 只记录非空行
                        output_lines.append(line)
                        self._log_command_output(line, "output")
            
            return_code = process.wait()
            self._log_command_output(f"命令完成，返回码: {return_code}", "success" if return_code == 0 else "error")
            return return_code, output_lines
            
        except Exception as e:
            error_msg = f"命令执行出错: {e}"
            self._log_command_output(error_msg, "error")
            return -1, [error_msg]
    
    def check_java(self) -> Tuple[bool, str]:
        """检查Java是否安装"""
        try:
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, 
                                  text=True)
            if result.returncode == 0:
                version_line = result.stderr.split('\n')[0]
                return True, version_line
            return False, "Java未安装"
        except FileNotFoundError:
            return False, "Java未安装"
    
    def install_java(self) -> bool:
        """安装Java JDK"""
        print(f"\n{Colors.WARNING}正在检查Java环境...{Colors.ENDC}")
        
        if shutil.which('pkg'):
            print(f"{Colors.OKCYAN}检测到Termux环境，使用pkg安装JDK...{Colors.ENDC}")
            try:
                subprocess.run(['pkg', 'install', '-y', 'openjdk-17'], check=True)
                print(f"{Colors.OKGREEN}✓ Java JDK 17安装成功！{Colors.ENDC}")
                return True
            except subprocess.CalledProcessError:
                print(f"{Colors.FAIL}✗ Java安装失败{Colors.ENDC}")
                return False
        elif shutil.which('apt'):
            print(f"{Colors.OKCYAN}检测到Debian/Ubuntu环境，使用apt安装JDK...{Colors.ENDC}")
            try:
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run(['sudo', 'apt', 'install', '-y', 'openjdk-17-jdk'], check=True)
                print(f"{Colors.OKGREEN}✓ Java JDK 17安装成功！{Colors.ENDC}")
                return True
            except subprocess.CalledProcessError:
                print(f"{Colors.FAIL}✗ Java安装失败{Colors.ENDC}")
                return False
        else:
            print(f"{Colors.FAIL}✗ 无法自动安装Java，请手动安装JDK 17{Colors.ENDC}")
            return False
    
    def download_fabric_installer(self, version: str = "1.1.1") -> Path:
        """下载Fabric安装器"""
        url = f"https://maven.fabricmc.net/net/fabricmc/fabric-installer/{version}/fabric-installer-{version}.jar"
        installer_path = self.server_dir / f"fabric-installer-{version}.jar"
        
        print(f"\n{Colors.OKCYAN}正在下载Fabric安装器 {version}...{Colors.ENDC}")
        
        try:
            def progress_hook(count, block_size, total_size):
                percent = int(count * block_size * 100 / total_size)
                sys.stdout.write(f"\r下载进度: {percent}%")
                sys.stdout.flush()
            
            urllib.request.urlretrieve(url, installer_path, reporthook=progress_hook)
            print(f"\n{Colors.OKGREEN}✓ Fabric安装器下载完成！{Colors.ENDC}")
            return installer_path
        except Exception as e:
            print(f"\n{Colors.FAIL}✗ 下载失败: {e}{Colors.ENDC}")
            raise
    
    def get_available_mc_versions(self) -> List[str]:
        """获取可用的Minecraft版本列表"""
        try:
            url = "https://meta.fabricmc.net/v2/game/version"
            response = urllib.request.urlopen(url, timeout=10)
            versions_data = json.loads(response.read().decode())
            
            versions = []
            for v in versions_data:
                if v.get('stable', True):
                    versions.append(v['version'])
            
            versions.sort(key=lambda x: [int(i) for i in x.split('.')], reverse=True)
            return versions[:20]
        except Exception as e:
            print(f"{Colors.WARNING}无法获取版本列表: {e}{Colors.ENDC}")
            return ["1.21.5", "1.21.4", "1.21.3", "1.21.1", "1.20.4", "1.20.1", "1.19.4", "1.19.3", "1.19.2", "1.18.2"]
    
    def install_fabric_server(self, mc_version: str = "1.21.5") -> Dict:
        """安装Fabric服务器"""
        result = {"success": False, "message": ""}
        
        self._log_command_output(f"{'='*50}", "info")
        self._log_command_output("开始安装Fabric服务器", "info")
        self._log_command_output(f"{'='*50}", "info")
        
        # 检查Java
        has_java, java_info = self.check_java()
        if not has_java:
            self._log_command_output(f"Java未安装: {java_info}", "error")
            result["message"] = f"Java未安装: {java_info}"
            return result
        
        self._log_command_output(f"Java环境: {java_info}", "success")
        
        # 下载安装器
        try:
            installer_path = self.download_fabric_installer()
        except Exception as e:
            self._log_command_output(f"下载安装器失败: {e}", "error")
            result["message"] = f"下载安装器失败: {e}"
            return result
        
        # 安装Fabric
        self._log_command_output("正在安装Fabric服务器...", "info")
        self._log_command_output(f"Minecraft版本: {mc_version}", "info")
        
        try:
            cmd = [
                'java', '-jar', str(installer_path),
                'server',
                '-dir', str(self.server_dir),
                '-mcversion', mc_version,
                '-downloadMinecraft'
            ]
            
            return_code, output_lines = self._run_command_with_output(cmd, str(self.server_dir))
            
            if return_code == 0:
                self._log_command_output("Fabric服务器安装成功！", "success")
                
                server_jar = self.server_dir / "server.jar"
                if not server_jar.exists():
                    self._log_command_output("Minecraft服务器jar文件未下载成功", "error")
                    result["message"] = "Minecraft服务器jar文件未下载成功"
                    return result
                
                # 同意EULA
                eula_file = self.server_dir / "eula.txt"
                with open(eula_file, 'w') as f:
                    f.write("eula=true\n")
                self._log_command_output("已接受EULA协议", "success")
                
                self.properties = self._load_properties()
                result["success"] = True
                result["message"] = "Fabric服务器安装成功"
                return result
            else:
                self._log_command_output(f"安装失败，返回码: {return_code}", "error")
                result["message"] = f"安装失败，返回码: {return_code}"
                return result
                
        except Exception as e:
            self._log_command_output(f"安装出错: {e}", "error")
            result["message"] = f"安装出错: {e}"
            return result
    
    def start_server(self) -> Dict:
        """启动服务器"""
        result = {"success": False, "message": ""}
        
        with self.server_lock:
            if self.server_process and self.server_process.poll() is None:
                result["message"] = "服务器已经在运行中"
                return result
            
            # 查找启动jar文件
            launch_jar = None
            for jar_file in self.server_dir.glob("fabric-server-launch*.jar"):
                launch_jar = jar_file
                break
            
            if not launch_jar:
                result["message"] = "未找到Fabric服务器启动文件"
                return result
            
            self._log_command_output(f"正在启动服务器: {launch_jar.name}", "info")
            
            try:
                # 计算内存分配（可用内存的70%）
                import psutil
                total_memory = psutil.virtual_memory().total
                heap_size = int(total_memory * 0.7 / 1024 / 1024)
                
                cmd = [
                    'java',
                    f'-Xms{heap_size}M',
                    f'-Xmx{heap_size}M',
                    '-jar',
                    str(launch_jar),
                    'nogui'
                ]
                
                self.server_process = subprocess.Popen(
                    cmd,
                    cwd=str(self.server_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                print(f"{Colors.OKGREEN}✓ 服务器启动进程已创建，PID: {self.server_process.pid}{Colors.ENDC}")
                self._log_command_output(f"服务器启动进程已创建，PID: {self.server_process.pid}", "success")
                
                # 启动后台线程读取服务器输出
                def read_server_output():
                    """读取服务器输出并保存到日志（捕获所有输出）"""
                    try:
                        # 读取stdout
                        for line in self.server_process.stdout:
                            line = line.rstrip('\n\r')
                            if line:
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                formatted_line = self._format_log_message(line)
                                self._save_to_unified_log(timestamp, formatted_line, "output")
                                # 同时输出到控制台
                                print(f"[SERVER] {formatted_line}")
                    except:
                        pass
                
                import threading
                output_thread = threading.Thread(target=read_server_output, daemon=True)
                output_thread.start()
                
                result["success"] = True
                result["message"] = f"服务器启动中，PID: {self.server_process.pid}"
                result["pid"] = self.server_process.pid
                return result
                
            except Exception as e:
                self._log_command_output(f"启动失败: {e}", "error")
                result["message"] = f"启动失败: {e}"
                return result

    def stop_server(self) -> Dict:
        """停止服务器"""
        result = {"success": False, "message": ""}
        
        with self.server_lock:
            if not self.server_process or self.server_process.poll() is not None:
                result["message"] = "服务器未运行"
                return result
            
            print(f"\n{Colors.WARNING}正在停止服务器...{Colors.ENDC}")
            
            try:
                self.server_process.stdin.write("stop\n")
                self.server_process.stdin.flush()
                
                try:
                    self.server_process.wait(timeout=30)
                    print(f"{Colors.OKGREEN}✓ 服务器已停止{Colors.ENDC}")
                    self.server_process = None
                    result["success"] = True
                    result["message"] = "服务器已停止"
                    return result
                except subprocess.TimeoutExpired:
                    print(f"{Colors.FAIL}✗ 服务器未响应，强制终止{Colors.ENDC}")
                    self.server_process.kill()
                    self.server_process = None
                    result["success"] = True
                    result["message"] = "服务器已强制停止"
                    return result
                    
            except Exception as e:
                result["message"] = f"停止失败: {e}"
                return result
    
    def restart_server(self) -> Dict:
        """重启服务器"""
        print(f"\n{Colors.WARNING}正在重启服务器...{Colors.ENDC}")
        
        if self.server_process and self.server_process.poll() is None:
            stop_result = self.stop_server()
            if not stop_result["success"]:
                return stop_result
            time.sleep(2)
        
        return self.start_server()
    
    def get_server_status(self) -> Dict:
        """获取服务器状态"""
        status = {
            "running": False,
            "pid": None,
            "uptime": 0,
            "memory_usage": 0,
            "cpu_usage": 0
        }
        
        if self.server_process and self.server_process.poll() is None:
            status["running"] = True
            status["pid"] = self.server_process.pid
            
            if PSUTIL_AVAILABLE:
                try:
                    process = psutil.Process(self.server_process.pid)
                    status["memory_usage"] = process.memory_info().rss / 1024 / 1024  # MB
                    status["cpu_usage"] = process.cpu_percent()
                except psutil.NoSuchProcess:
                    pass
        
        return status
    
    def get_latest_logs(self, lines: int = None) -> List[str]:
        """获取最新日志（从统一日志文件，返回所有原始输出）"""
        if lines is None:
            lines = SERVER_LOG_LINES
        
        unified_log_file = self.logs_dir / "unified.log"
        if not unified_log_file.exists():
            # 如果统一日志不存在，尝试从命令输出队列获取
            if self.command_output_queue:
                return [f"{item['level'].upper()} [{item['timestamp']}] {item['message']}" 
                       for item in self.command_output_queue[-lines:]]
            return ["暂无日志"]
        
        try:
            with open(unified_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                # 不进行格式化，直接返回原始日志行
                if len(all_lines) > lines:
                    return [line.rstrip('\n\r') for line in all_lines[-lines:]]
                else:
                    return [line.rstrip('\n\r') for line in all_lines]
        except Exception as e:
            return [f"读取日志失败: {e}"]
    
    def get_new_logs(self) -> List[str]:
        """获取新增的日志行（从统一日志文件）"""
        unified_log_file = self.logs_dir / "unified.log"
        if not unified_log_file.exists():
            return []
        
        try:
            with open(unified_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.log_position)
                new_lines = f.readlines()
                self.log_position = f.tell()
                # 格式化每行日志
                formatted_lines = []
                for line in new_lines:
                    formatted_lines.append(self._format_log_message(line.rstrip('\n\r')))
                return formatted_lines
        except Exception:
            return []
    
    def add_to_whitelist(self, player_name: str) -> Dict:
        """添加玩家到白名单"""
        result = {"success": False, "message": ""}
        
        # 检查是否已存在
        for player in self.whitelist:
            if player['name'].lower() == player_name.lower():
                result["message"] = f"玩家 {player_name} 已在白名单中"
                return result
        
        entry = {
            "uuid": "00000000-0000-0000-0000-000000000000",
            "name": player_name
        }
        self.whitelist.append(entry)
        self._save_json(self.whitelist_file, self.whitelist)
        self.properties['white-list'] = 'true'
        self._save_properties()
        
        result["success"] = True
        result["message"] = f"{player_name} 已添加到白名单"
        return result
    
    def remove_from_whitelist(self, player_name: str) -> Dict:
        """从白名单移除玩家"""
        result = {"success": False, "message": ""}
        
        original_count = len(self.whitelist)
        self.whitelist = [p for p in self.whitelist if p['name'].lower() != player_name.lower()]
        
        if len(self.whitelist) == original_count:
            result["message"] = f"玩家 {player_name} 不在白名单中"
            return result
        
        self._save_json(self.whitelist_file, self.whitelist)
        result["success"] = True
        result["message"] = f"{player_name} 已从白名单移除"
        return result
    
    def add_op(self, player_name: str, level: int = 4) -> Dict:
        """添加管理员"""
        result = {"success": False, "message": ""}
        
        # 检查是否已存在
        for op in self.ops:
            if op['name'].lower() == player_name.lower():
                result["message"] = f"玩家 {player_name} 已是管理员"
                return result
        
        entry = {
            "uuid": "00000000-0000-0000-0000-000000000000",
            "name": player_name,
            "level": level
        }
        self.ops.append(entry)
        self._save_json(self.ops_file, self.ops)
        
        result["success"] = True
        result["message"] = f"{player_name} 已设置为管理员 (Level {level})"
        return result
    
    def remove_op(self, player_name: str) -> Dict:
        """移除管理员"""
        result = {"success": False, "message": ""}
        
        original_count = len(self.ops)
        self.ops = [p for p in self.ops if p['name'].lower() != player_name.lower()]
        
        if len(self.ops) == original_count:
            result["message"] = f"玩家 {player_name} 不是管理员"
            return result
        
        self._save_json(self.ops_file, self.ops)
        result["success"] = True
        result["message"] = f"{player_name} 已移除管理员权限"
        return result
    
    def ban_player(self, player_name: str, reason: str = "") -> Dict:
        """封禁玩家"""
        result = {"success": False, "message": ""}
        
        # 检查是否已封禁
        for player in self.banned_players:
            if player['name'].lower() == player_name.lower():
                result["message"] = f"玩家 {player_name} 已被封禁"
                return result
        
        entry = {
            "uuid": "00000000-0000-0000-0000-000000000000",
            "name": player_name,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S +0800"),
            "source": "Server",
            "expires": "forever",
            "reason": reason or "Banned by an operator"
        }
        self.banned_players.append(entry)
        self._save_json(self.banned_players_file, self.banned_players)
        
        result["success"] = True
        result["message"] = f"{player_name} 已被封禁"
        return result
    
    def unban_player(self, player_name: str) -> Dict:
        """解封玩家"""
        result = {"success": False, "message": ""}
        
        original_count = len(self.banned_players)
        self.banned_players = [p for p in self.banned_players if p['name'].lower() != player_name.lower()]
        
        if len(self.banned_players) == original_count:
            result["message"] = f"玩家 {player_name} 未被封禁"
            return result
        
        self._save_json(self.banned_players_file, self.banned_players)
        result["success"] = True
        result["message"] = f"{player_name} 已解封"
        return result
    
    def ban_ip(self, ip_address: str, reason: str = "") -> Dict:
        """封禁IP"""
        result = {"success": False, "message": ""}
        
        # 检查是否已封禁
        for ip in self.banned_ips:
            if ip['ip'] == ip_address:
                result["message"] = f"IP {ip_address} 已被封禁"
                return result
        
        entry = {
            "ip": ip_address,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S +0800"),
            "source": "Server",
            "expires": "forever",
            "reason": reason or "Banned by an operator"
        }
        self.banned_ips.append(entry)
        self._save_json(self.banned_ips_file, self.banned_ips)
        
        result["success"] = True
        result["message"] = f"IP {ip_address} 已被封禁"
        return result
    
    def unban_ip(self, ip_address: str) -> Dict:
        """解封IP"""
        result = {"success": False, "message": ""}
        
        original_count = len(self.banned_ips)
        self.banned_ips = [ip for ip in self.banned_ips if ip['ip'] != ip_address]
        
        if len(self.banned_ips) == original_count:
            result["message"] = f"IP {ip_address} 未被封禁"
            return result
        
        self._save_json(self.banned_ips_file, self.banned_ips)
        result["success"] = True
        result["message"] = f"IP {ip_address} 已解封"
        return result
    
    def get_mods_list(self) -> List[str]:
        """获取已安装的mod列表"""
        if not self.mods_dir.exists():
            return []
        
        mods = []
        for mod_file in self.mods_dir.glob("*.jar"):
            mods.append(mod_file.name)
        return mods
    
    def add_mod(self, mod_path: str) -> Dict:
        """添加mod"""
        result = {"success": False, "message": ""}
        
        if not self.mods_dir.exists():
            self.mods_dir.mkdir()
        
        try:
            mod_file = Path(mod_path)
            if not mod_file.exists():
                result["message"] = "文件不存在"
                return result
            
            # 检查是否已存在
            dest_path = self.mods_dir / mod_file.name
            if dest_path.exists():
                result["message"] = f"Mod {mod_file.name} 已存在"
                return result
            
            shutil.copy(mod_path, self.mods_dir)
            result["success"] = True
            result["message"] = f"Mod {mod_file.name} 添加成功"
            return result
        except Exception as e:
            result["message"] = f"添加mod失败: {e}"
            return result
    
    def remove_mod(self, mod_name: str) -> Dict:
        """移除mod"""
        result = {"success": False, "message": ""}
        
        mod_file = self.mods_dir / mod_name
        if not mod_file.exists():
            result["message"] = f"Mod {mod_name} 不存在"
            return result
        
        try:
            mod_file.unlink()
            result["success"] = True
            result["message"] = f"Mod {mod_name} 已删除"
            return result
        except Exception as e:
            result["message"] = f"删除mod失败: {e}"
            return result
    
    def update_property(self, key: str, value: str) -> Dict:
        """更新服务器配置"""
        result = {"success": False, "message": ""}
        
        if key not in self.properties:
            result["message"] = f"配置项 {key} 不存在"
            return result
        
        self.properties[key] = value
        self._save_properties()
        
        result["success"] = True
        result["message"] = f"配置 {key} 已更新为 {value}"
        return result
    
    def backup_world(self) -> Dict:
        """备份世界"""
        result = {"success": False, "message": ""}
        
        world_dir = self.server_dir / "world"
        if not world_dir.exists():
            result["message"] = "世界目录不存在"
            return result
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"world_backup_{timestamp}.zip"
        backup_path = self.backups_dir / backup_name
        
        try:
            import zipfile
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(world_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.server_dir)
                        zipf.write(file_path, arcname)
            
            result["success"] = True
            result["message"] = f"世界已备份到 {backup_name}"
            result["backup_path"] = str(backup_path)
            return result
        except Exception as e:
            result["message"] = f"备份失败: {e}"
            return result
    
    def get_backups_list(self) -> List[Dict]:
        """获取备份列表"""
        backups = []
        if not self.backups_dir.exists():
            return backups
        
        for backup_file in self.backups_dir.glob("*.zip"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    
    def delete_backup(self, backup_name: str) -> Dict:
        """删除备份"""
        result = {"success": False, "message": ""}
        
        backup_path = self.backups_dir / backup_name
        if not backup_path.exists():
            result["message"] = f"备份 {backup_name} 不存在"
            return result
        
        try:
            backup_path.unlink()
            result["success"] = True
            result["message"] = f"备份 {backup_name} 已删除"
            return result
        except Exception as e:
            result["message"] = f"删除备份失败: {e}"
            return result
    
    def kill_all_java_processes(self) -> Dict:
        """强制结束所有 Java 进程"""
        result = {"success": False, "message": "", "killed_count": 0}
        
        try:
            import psutil
            killed_count = 0
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'java' in proc.info['name'].lower():
                        self._log_command_output(f"结束 Java 进程: PID {proc.info['pid']} - {proc.info['name']}", "info")
                        proc.terminate()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 等待进程结束
            time.sleep(2)
            
            result["success"] = True
            result["message"] = f"已结束 {killed_count} 个 Java 进程"
            result["killed_count"] = killed_count
            
            # 清除服务器进程引用
            if self.server_process:
                self.server_process = None
            
            return result
            
        except ImportError:
            # 如果没有 psutil，使用 pkill 命令
            try:
                subprocess.run(['pkill', '-9', 'java'], check=True)
                result["success"] = True
                result["message"] = "已使用 pkill 结束所有 Java 进程"
                result["killed_count"] = -1  # 未知数量
                
                # 清除服务器进程引用
                if self.server_process:
                    self.server_process = None
                
                return result
            except subprocess.CalledProcessError:
                result["message"] = "没有找到 Java 进程或结束失败"
                return result
        except Exception as e:
            result["message"] = f"结束进程失败: {e}"
            return result
    
    def send_command(self, command: str) -> Dict:
        """向服务器发送命令"""
        result = {"success": False, "message": "", "output": ""}
        
        if not self.server_process or self.server_process.poll() is not None:
            result["message"] = "服务器未运行，无法发送命令"
            return result
        
        try:
            self._log_command_output(f"发送命令: {command}", "command")
            
            # 发送命令到服务器 stdin
            self.server_process.stdin.write(f"{command}\n")
            self.server_process.stdin.flush()
            
            result["success"] = True
            result["message"] = f"命令 '{command}' 已发送"
            result["command"] = command
            return result
            
        except Exception as e:
            self._log_command_output(f"发送命令失败: {e}", "error")
            result["message"] = f"发送命令失败: {e}"
            return result


# Flask 应用和路由
if FLASK_AVAILABLE:
    import logging
    
    # 禁用 Flask 访问日志
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'minecraft-server-manager-secret-key'
    app.config['DEBUG'] = FLASK_DEBUG
    
    # 全局管理器实例
    manager = None
    
    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')
    
    @app.route('/auth')
    def auth():
        """认证页面（已禁用）"""
        return redirect('/')
    
    @app.route('/api/status')
    def api_status():
        """获取服务器状态"""
        status = manager.get_server_status()
        status.update({
            "server_name": manager.properties.get('server-name', 'Minecraft Server'),
            "motd": manager.properties.get('motd', 'A Minecraft Server'),
            "max_players": manager.properties.get('max-players', '20'),
            "server_port": manager.properties.get('server-port', '25565'),
            "gamemode": manager.properties.get('gamemode', 'survival'),
            "difficulty": manager.properties.get('difficulty', 'easy'),
            "level_name": manager.properties.get('level-name', 'world'),
        })
        return jsonify(status)
    
    @app.route('/api/server/start', methods=['POST'])
    def api_start_server():
        """启动服务器"""
        result = manager.start_server()
        return jsonify(result)
    
    @app.route('/api/server/stop', methods=['POST'])
    def api_stop_server():
        """停止服务器"""
        result = manager.stop_server()
        return jsonify(result)
    
    @app.route('/api/server/restart', methods=['POST'])
    def api_restart_server():
        """重启服务器"""
        result = manager.restart_server()
        return jsonify(result)
    
    @app.route('/api/server/install', methods=['POST'])
    def api_install_server():
        """安装Fabric服务器"""
        data = request.json
        mc_version = data.get('mc_version', '1.21.5')
        result = manager.install_fabric_server(mc_version)
        return jsonify(result)
    
    @app.route('/api/server/check-installed')
    def api_check_installed():
        """检查服务器是否已安装"""
        server_jar = manager.server_dir / "server.jar"
        launch_jar = None
        for jar_file in manager.server_dir.glob("fabric-server-launch*.jar"):
            launch_jar = jar_file
            break
        
        return jsonify({
            "installed": server_jar.exists() and launch_jar is not None,
            "server_jar": str(server_jar),
            "launch_jar": str(launch_jar) if launch_jar else None
        })
    
    @app.route('/api/command-output')
    def api_command_output():
        """获取命令输出"""
        with manager.command_output_lock:
            output = manager.command_output_queue.copy()
            manager.command_output_queue.clear()
        return jsonify(output)
    
    @app.route('/api/config', methods=['GET', 'POST'])
    def api_config():
        """获取或更新配置"""
        if request.method == 'GET':
            return jsonify(manager.properties)
        elif request.method == 'POST':
            data = request.json
            results = []
            for key, value in data.items():
                result = manager.update_property(key, value)
                results.append(result)
            return jsonify(results)
    
    @app.route('/api/whitelist', methods=['GET', 'POST', 'DELETE'])
    def api_whitelist():
        """白名单管理"""
        if request.method == 'GET':
            return jsonify(manager.whitelist)
        elif request.method == 'POST':
            data = request.json
            result = manager.add_to_whitelist(data.get('name', ''))
            return jsonify(result)
        elif request.method == 'DELETE':
            data = request.json
            result = manager.remove_from_whitelist(data.get('name', ''))
            return jsonify(result)
    
    @app.route('/api/ops', methods=['GET', 'POST', 'DELETE'])
    def api_ops():
        """管理员管理"""
        if request.method == 'GET':
            return jsonify(manager.ops)
        elif request.method == 'POST':
            data = request.json
            result = manager.add_op(data.get('name', ''), data.get('level', 4))
            return jsonify(result)
        elif request.method == 'DELETE':
            data = request.json
            result = manager.remove_op(data.get('name', ''))
            return jsonify(result)
    
    @app.route('/api/banned-players', methods=['GET', 'POST', 'DELETE'])
    def api_banned_players():
        """封禁玩家管理"""
        if request.method == 'GET':
            return jsonify(manager.banned_players)
        elif request.method == 'POST':
            data = request.json
            result = manager.ban_player(data.get('name', ''), data.get('reason', ''))
            return jsonify(result)
        elif request.method == 'DELETE':
            data = request.json
            result = manager.unban_player(data.get('name', ''))
            return jsonify(result)
    
    @app.route('/api/banned-ips', methods=['GET', 'POST', 'DELETE'])
    def api_banned_ips():
        """封禁IP管理"""
        if request.method == 'GET':
            return jsonify(manager.banned_ips)
        elif request.method == 'POST':
            data = request.json
            result = manager.ban_ip(data.get('ip', ''), data.get('reason', ''))
            return jsonify(result)
        elif request.method == 'DELETE':
            data = request.json
            result = manager.unban_ip(data.get('ip', ''))
            return jsonify(result)
    
    @app.route('/api/mods', methods=['GET', 'POST', 'DELETE'])
    def api_mods():
        """Mod管理"""
        if request.method == 'GET':
            return jsonify(manager.get_mods_list())
        elif request.method == 'POST':
            data = request.json
            result = manager.add_mod(data.get('path', ''))
            return jsonify(result)
        elif request.method == 'DELETE':
            data = request.json
            result = manager.remove_mod(data.get('name', ''))
            return jsonify(result)
    
    @app.route('/api/logs')
    def api_logs():
        """获取日志"""
        lines = request.args.get('lines', 50, type=int)
        
        if DEBUG_MODE:
            print(f"[DEBUG] API: /api/logs?lines={lines}")
            print(f"[DEBUG] 日志文件存在: {(manager.logs_dir / 'unified.log').exists()}")
        
        return jsonify(manager.get_latest_logs(lines))
    
    @app.route('/api/backups', methods=['GET', 'POST', 'DELETE'])
    def api_backups():
        """备份管理"""
        if request.method == 'GET':
            return jsonify(manager.get_backups_list())
        elif request.method == 'POST':
            result = manager.backup_world()
            return jsonify(result)
        elif request.method == 'DELETE':
            data = request.json
            result = manager.delete_backup(data.get('name', ''))
            return jsonify(result)
    
    @app.route('/api/server/kill-java', methods=['POST'])
    def api_kill_java():
        """强制结束所有 Java 进程"""
        result = manager.kill_all_java_processes()
        return jsonify(result)
    
    @app.route('/api/server/command', methods=['POST'])
    def api_send_command():
        """向服务器发送命令"""
        data = request.json
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({"success": False, "message": "命令不能为空"})
        
        result = manager.send_command(command)
        return jsonify(result)
    
    @app.route('/api/time-sync/status')
    def api_time_sync_status():
        """获取时间同步状态"""
        status = manager.get_time_sync_status()
        return jsonify(status)
    
    @app.route('/api/time-sync/sync', methods=['POST'])
    def api_time_sync():
        """手动同步时间"""
        result = manager.sync_system_time()
        return jsonify(result)
    
    @app.route('/api/time-sync/enable', methods=['POST'])
    def api_enable_time_sync():
        """启用时间同步"""
        data = request.json
        interval = data.get('interval', 3600)
        result = manager.enable_time_sync(interval)
        return jsonify(result)
    
    @app.route('/api/time-sync/disable', methods=['POST'])
    def api_disable_time_sync():
        """禁用时间同步"""
        result = manager.disable_time_sync()
        return jsonify(result)


def check_port_in_use(port: int) -> Tuple[bool, Optional[int]]:
    """检查端口是否被占用，返回 (是否占用, 占用进程PID)"""
    try:
        import psutil
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return True, conn.pid
        return False, None
    except (ImportError, PermissionError) as e:
        # 如果没有 psutil 或权限不足，使用备用方法
        return check_port_in_use_fallback(port)


def check_port_in_use_fallback(port: int) -> Tuple[bool, Optional[int]]:
    """备用方法：使用 netstat 或 ss 检查端口"""
    # 方法1: 尝试直接绑定端口
    try:
        import socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(1)
        result = test_socket.connect_ex(('127.0.0.1', port))
        test_socket.close()
        if result == 0:
            # 端口被占用，尝试获取PID
            return get_pid_by_port(port)
        return False, None
    except:
        pass
    
    # 方法2: 使用 ss 命令
    try:
        result = subprocess.run(
            ['ss', '-tuln'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if f':{port}' in result.stdout:
            return get_pid_by_port(port)
        return False, None
    except:
        pass
    
    # 方法3: 使用 netstat 命令
    try:
        result = subprocess.run(
            ['netstat', '-tuln'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if f':{port}' in result.stdout:
            return get_pid_by_port(port)
        return False, None
    except:
        # 如果所有方法都失败，假设端口可用
        return False, None


def get_pid_by_port(port: int) -> Tuple[bool, Optional[int]]:
    """尝试获取占用端口的进程PID"""
    # 方法1: 尝试使用 lsof
    try:
        result = subprocess.run(
            ['lsof', '-t', '-i', f':{port}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip() and result.stdout.strip().isdigit():
            return True, int(result.stdout.strip())
    except:
        pass
    
    # 方法2: 尝试使用 psutil 遍历进程（避免 net_connections 权限问题）
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # 尝试获取连接信息
                try:
                    connections = proc.net_connections()
                    for conn in connections:
                        if conn.laddr.port == port and conn.status == 'LISTEN':
                            return True, conn.pid
                except (psutil.AccessDenied, psutil.NoSuchProcess, PermissionError):
                    # 如果无法获取连接信息，尝试通过进程名判断
                    if 'python' in proc.info.get('name', '').lower() or 'flask' in proc.info.get('name', '').lower():
                        # 可能是我们的程序，返回这个PID
                        return True, proc.info['pid']
            except:
                continue
    except:
        pass
    
    # 方法3: 尝试使用 ss -tulnp
    try:
        result = subprocess.run(
            ['ss', '-tulnp'],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'pid=' in line:
                try:
                    pid_match = line.split('pid=')[1].split(',')[0]
                    if pid_match.strip().isdigit():
                        return True, int(pid_match.strip())
                except:
                    pass
    except:
        pass
    
    # 方法4: 使用 ps 命令查找 Python 进程
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if 'python' in line and 'mc_server_manager' in line:
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    return True, int(parts[1])
    except:
        pass
    
    # 无法获取PID，但端口被占用
    return True, None


def kill_process(pid: int) -> bool:
    """终止进程"""
    try:
        import psutil
        process = psutil.Process(pid)
        process.terminate()
        process.wait(timeout=5)
        return True
    except ImportError:
        try:
            subprocess.run(['kill', str(pid)], check=True)
            time.sleep(1)
            return True
        except:
            return False
    except:
        return False


def main():
    """主函数"""
    global manager
    
    # 获取脚本所在目录的绝对路径
    script_dir = Path(__file__).resolve().parent
    
    # 使用配置中的数据目录
    data_dir = script_dir / SERVER_DATA_DIR
    
    # 如果目录不存在，创建它
    if not data_dir.exists():
        print(f"{Colors.OKCYAN}创建数据目录: {data_dir}{Colors.ENDC}")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    manager = MCServerManager(str(data_dir))
    
    if not FLASK_AVAILABLE:
        print(f"{Colors.FAIL}Flask 未安装，请运行: pip install flask{Colors.ENDC}")
        sys.exit(1)
    
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}  Easy MC Server Lunch (Web版){Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"数据目录: {manager.server_dir}")
    
    # 调试模式警告
    if DEBUG_MODE:
        print(f"{Colors.WARNING}⚠️  警告：已开启调试模式{Colors.ENDC}")
    
    print(f"{Colors.OKGREEN}✓ Web界面启动中...{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    # 检查端口是否被占用（使用配置中的端口）
    port = FLASK_PORT
    is_in_use, pid = check_port_in_use(port)
    
    if is_in_use:
        print(f"\n{Colors.WARNING}警告: 端口 {port} 已被占用！{Colors.ENDC}")
        if pid:
            try:
                import psutil
                process = psutil.Process(pid)
                print(f"{Colors.WARNING}占用进程: PID {pid} - {process.name()}{Colors.ENDC}")
            except:
                print(f"{Colors.WARNING}占用进程: PID {pid}{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}占用进程: 未知{Colors.ENDC}")
        
        print(f"\n{Colors.OKCYAN}请选择操作:{Colors.ENDC}")
        print(f"  [y] 结束占用进程并继续启动")
        print(f"  [n] 取消启动")
        
        choice = input(f"\n{Colors.WARNING}是否结束占用进程? (y/n): {Colors.ENDC}").strip().lower()
        
        if choice == 'y':
            if pid:
                print(f"\n{Colors.OKCYAN}正在尝试结束进程 {pid}...{Colors.ENDC}")
                if kill_process(pid):
                    print(f"{Colors.OKGREEN}✓ 进程 {pid} 已结束{Colors.ENDC}")
                    time.sleep(2)  # 等待端口释放
                else:
                    print(f"{Colors.FAIL}✗ 无法结束进程 {pid}{Colors.ENDC}")
                    print(f"{Colors.WARNING}请手动结束该进程后重试{Colors.ENDC}")
                    sys.exit(1)
            else:
                print(f"{Colors.FAIL}✗ 无法自动结束进程，请手动结束后重试{Colors.ENDC}")
                sys.exit(1)
        else:
            print(f"{Colors.WARNING}已取消启动{Colors.ENDC}")
            sys.exit(0)
    
    # 启动Flask服务器
    try:
        import threading
        import webbrowser
        
        # 在新线程中打开浏览器
        def open_browser():
            time.sleep(2)  # 等待服务器启动
            webbrowser.open('http://localhost:5000')
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}正在关闭服务器...{Colors.ENDC}")
        if manager.server_process and manager.server_process.poll() is None:
            manager.stop_server()
        print(f"{Colors.OKGREEN}✓ 服务器管理端已关闭{Colors.ENDC}")


if __name__ == '__main__':
    main()