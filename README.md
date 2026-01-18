# Minecraft Fabric 服务器管理端

基于Flask的现代化Web界面Minecraft Fabric服务器管理工具，提供完整的服务器安装、配置和管理功能。

## 功能特性

### 🎮 服务器管理
- **自动安装Fabric服务器**：从fabric-installer-1.1.1.jar开始，支持选择Minecraft版本和Loader版本
- **自动检测和安装JDK**：支持Termux和Debian/Ubuntu环境
- **服务器控制**：启动、停止、重启服务器
- **实时状态监控**：查看服务器运行状态、CPU和内存使用情况

### ⚙️ 配置管理
- **基本设置**：服务器名称、MOTD、最大玩家数、端口
- **游戏设置**：游戏模式、难度、PVP、硬核模式、飞行
- **世界设置**：世界名称、种子、类型、视距、出生点保护
- **安全设置**：在线模式、白名单、生物生成
- **性能设置**：空置暂停时间（0=禁用，60=60秒后暂停）

### 👥 玩家管理
- **白名单管理**：添加/移除白名单玩家
- **管理员管理**：添加/移除管理员，设置权限等级（1-4）
- **封禁玩家**：封禁/解封玩家，支持封禁原因
- **封禁IP**：封禁/解封IP地址

### 📦 Mod管理
- **查看已安装Mod**：列出所有已安装的Mod
- **添加Mod**：从本地路径添加Mod文件
- **删除Mod**：移除不需要的Mod

### 📋 日志查看
- **实时日志**：通过HTTP轮询实时查看服务器日志
- **日志格式化**：自动简化日志格式，移除冗余时间戳
- **中文显示**：日志级别使用中文（信息、警告、错误）
- **命令输出**：显示所有控制台命令的执行结果

### 💾 世界备份
- **创建备份**：一键备份世界数据
- **查看备份**：列出所有备份及其大小和创建时间
- **删除备份**：管理备份存储空间

### 💻 命令执行
- **Web端命令**：直接在网页上执行Minecraft服务器命令
- **实时反馈**：命令执行结果实时显示在日志中
- **快捷操作**：支持回车键快速发送命令

## 安装要求

### Python依赖
```bash
pip install flask flask-socketio psutil
```

### 系统要求
- Python 3.7+
- Java 17+ (会自动检测并安装)
- Termux (Android) 或 Linux系统

## 使用方法

### 启动管理端
```bash
python mc_server_manager.py
```

启动后，在浏览器中访问：
- **本地访问**: http://localhost:5000
- **局域网访问**: http://<你的IP>:5000

### 界面操作

#### 主界面
- **服务器控制**: 左侧面板提供启动、停止、重启按钮
- **服务器信息**: 显示服务器名称、MOTD、最大玩家数等基本信息
- **实时状态**: 显示内存使用、CPU使用率等性能指标

#### 功能标签页
- **日志**: 实时查看服务器日志输出
- **配置**: 修改服务器配置并保存
- **玩家管理**: 管理白名单、管理员和封禁列表
- **Mod管理**: 查看和管理已安装的Mod
- **备份**: 创建、查看和删除世界备份

## 配置文件说明

### server.properties
服务器主配置文件，包含所有游戏和服务器设置。

| 参数 | 说明 | 默认值 |
|------|------|--------|
| server-name | 服务器名称 | Minecraft Server |
| motd | 服务器描述信息 | A Minecraft Server |
| max-players | 最大玩家数 | 20 |
| server-port | 服务器端口 | 25565 |
| gamemode | 游戏模式 | survival |
| difficulty | 游戏难度 | easy |
| pvp | 是否允许PVP | true |
| hardcore | 硬核模式 | false |
| allow-flight | 允许飞行 | false |
| level-name | 世界名称 | world |
| level-seed | 世界种子 | (随机) |
| level-type | 世界类型 | minecraft:normal |
| view-distance | 视距 | 10 |
| spawn-protection | 出生点保护范围 | 16 |
| online-mode | 在线模式 | true |
| white-list | 启用白名单 | false |
| enforce-whitelist | 强制白名单 | false |
| spawn-monsters | 生成怪物 | true |
| spawn-animals | 生成动物 | true |
| pause-when-empty-seconds | 空置暂停时间（秒） | 60 |

### whitelist.json
白名单配置文件，存储允许加入服务器的玩家信息。

```json
[
  {
    "uuid": "玩家UUID",
    "name": "玩家名称"
  }
]
```

### ops.json
管理员配置文件，存储服务器管理员信息。

```json
[
  {
    "uuid": "玩家UUID",
    "name": "玩家名称",
    "level": 4
  }
]
```

权限等级：
- Level 1：绕过出生点保护
- Level 2：使用更多命令和命令方块
- Level 3：使用多人游戏管理相关命令
- Level 4：所有命令

### banned-players.json
封禁玩家配置文件。

```json
[
  {
    "uuid": "玩家UUID",
    "name": "玩家名称",
    "created": "封禁时间",
    "source": "封禁来源",
    "expires": "过期时间",
    "reason": "封禁原因"
  }
]
```

### banned-ips.json
封禁IP配置文件。

```json
[
  {
    "ip": "IP地址",
    "created": "封禁时间",
    "source": "封禁来源",
    "expires": "过期时间",
    "reason": "封禁原因"
  }
]
```

## API接口

### 服务器状态
- `GET /api/status` - 获取服务器状态

### 服务器控制
- `POST /api/server/start` - 启动服务器
- `POST /api/server/stop` - 停止服务器
- `POST /api/server/restart` - 重启服务器
- `POST /api/server/kill-java` - 强制结束所有Java进程
- `POST /api/server/command` - 向服务器发送命令

### 配置管理
- `GET /api/config` - 获取配置
- `POST /api/config` - 更新配置

### 玩家管理
- `GET /api/whitelist` - 获取白名单
- `POST /api/whitelist` - 添加白名单玩家
- `DELETE /api/whitelist` - 移除白名单玩家
- `GET /api/ops` - 获取管理员列表
- `POST /api/ops` - 添加管理员
- `DELETE /api/ops` - 移除管理员
- `GET /api/banned-players` - 获取封禁玩家列表
- `POST /api/banned-players` - 封禁玩家
- `DELETE /api/banned-players` - 解封玩家
- `GET /api/banned-ips` - 获取封禁IP列表
- `POST /api/banned-ips` - 封禁IP
- `DELETE /api/banned-ips` - 解封IP

### Mod管理
- `GET /api/mods` - 获取Mod列表
- `POST /api/mods` - 添加Mod
- `DELETE /api/mods` - 删除Mod

### 日志和备份
- `GET /api/logs` - 获取日志
- `GET /api/command-output` - 获取命令输出
- `GET /api/backups` - 获取备份列表
- `POST /api/backups` - 创建备份
- `DELETE /api/backups` - 删除备份

### 服务器安装
- `GET /api/server/check-installed` - 检查服务器是否已安装
- `POST /api/server/install` - 安装Fabric服务器

## 安装Fabric服务器

### 通过Web界面安装
1. 启动管理端
2. 在浏览器中访问Web界面
3. 使用API或命令行手动安装（当前版本）

### 手动安装
如果自动安装失败，可以手动执行：

```bash
# 下载Fabric安装器
wget https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.1.1/fabric-installer-1.1.1.jar

# 安装Fabric服务器
java -jar fabric-installer-1.1.1.jar server 1.21.5 0.18.4 /path/to/server --download-minecraft

# 接受EULA
echo "eula=true" > eula.txt

# 启动服务器
java -jar fabric-server-launch.jar nogui
```

## 常见问题

### Java未安装
程序会自动检测Java环境，如果未安装会提示是否自动安装。支持：
- Termux: `pkg install openjdk-17`
- Debian/Ubuntu: `sudo apt install openjdk-17-jdk`

### 服务器启动失败
1. 检查Java版本是否为17或更高
2. 检查端口25565是否被占用
3. 检查eula.txt是否已设置为true
4. 查看日志文件了解详细错误

### Mod不工作
1. 确保已安装Fabric API
2. 检查Mod版本是否与Minecraft版本匹配
3. 查看服务器日志了解具体错误

### Web界面无法访问
1. 检查Flask是否正确安装
2. 检查端口5000是否被占用
3. 检查防火墙设置
4. 确认服务端已成功启动

## 技术支持

如有问题或建议，请查看：
- [Fabric官方文档](https://fabricmc.net/wiki/start:introduction/)
- [Minecraft Wiki](https://minecraft.fandom.com/wiki/Server.properties)
- [Flask文档](https://flask.palletsprojects.com/)
- [Socket.IO文档](https://socket.io/)

## 许可证

本项目仅供学习和个人使用。Minecraft是Mojang Studios的商标。

## 更新日志

### v2.1.0 (2026-01-16)
- 添加Web端命令执行功能
- 添加空置暂停配置选项
- 优化日志显示格式（移除冗余时间戳，使用中文）
- 添加自动打开浏览器功能
- 改进日志格式化和显示
- 移除WebSocket，改用HTTP轮询

### v1.0.0 (2025-01-14)
- 初始版本发布
- 支持Fabric服务器安装
- 完整的配置管理功能
- 玩家管理功能
- Mod管理功能
- 日志查看功能