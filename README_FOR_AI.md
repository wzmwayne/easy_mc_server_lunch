# Minecraft Fabric Server Manager - AI开发者文档

本文档为AI开发者提供详细的技术文档，用于理解、维护和扩展本项目。

## 项目概述

**项目名称**: Minecraft Fabric Server Manager (Web版)
**版本**: 2.1.0
**开发语言**: Python 3.7+
**Web框架**: Flask
**前端技术**: HTML5 + 原生CSS + JavaScript
**目标平台**: Termux (Android) / Linux

## 项目结构

```
/data/data/com.termux/files/home/mc/
├── mc_server_manager.py          # 主程序文件（包含后端和API）
├── templates/
│   └── index.html                # Web界面模板
├── server.properties             # Minecraft服务器配置
├── eula.txt                      # EULA协议
├── whitelist.json                # 白名单
├── ops.json                      # 管理员
├── banned-players.json           # 封禁玩家
├── banned-ips.json               # 封禁IP
├── mods/                         # Mod目录
├── logs/                         # 日志目录
├── world/                        # 世界数据
├── backups/                      # 备份目录
├── libraries/                    # 依赖库
└── .fabric/                      # Fabric相关文件
```

## 核心架构

### 1. 后端架构

#### MCServerManager类
核心管理类，负责所有服务器操作：

**初始化**:
```python
def __init__(self, server_dir: str = None)
```
- 设置服务器目录路径
- 初始化配置文件路径
- 加载配置数据（properties, whitelist, ops等）
- 创建必要的目录（mods, backups）

**配置管理**:
- `_load_properties()`: 加载server.properties文件
- `_save_properties()`: 保存server.properties文件
- `_load_json()`: 加载JSON配置文件
- `_save_json()`: 保存JSON配置文件

**Java环境**:
- `check_java()`: 检查Java是否安装
- `install_java()`: 自动安装Java 17（支持Termux和Debian/Ubuntu）

**Fabric安装**:
- `download_fabric_installer()`: 下载Fabric安装器
- `get_available_mc_versions()`: 获取可用的Minecraft版本列表
- `install_fabric_server()`: 安装Fabric服务器

**服务器控制**:
- `start_server()`: 启动服务器（使用线程锁保证线程安全）
- `stop_server()`: 停止服务器（发送stop命令，超时则强制终止）
- `restart_server()`: 重启服务器
- `get_server_status()`: 获取服务器状态（运行状态、PID、内存、CPU）

**玩家管理**:
- `add_to_whitelist()`: 添加白名单玩家
- `remove_from_whitelist()`: 移除白名单玩家
- `add_op()`: 添加管理员
- `remove_op()`: 移除管理员
- `ban_player()`: 封禁玩家
- `unban_player()`: 解封玩家
- `ban_ip()`: 封禁IP
- `unban_ip()`: 解封IP

**Mod管理**:
- `get_mods_list()`: 获取已安装Mod列表
- `add_mod()`: 添加Mod
- `remove_mod()`: 删除Mod

**备份管理**:
- `backup_world()`: 创建世界备份（ZIP格式）
- `get_backups_list()`: 获取备份列表
- `delete_backup()`: 删除备份

**日志管理**:
- `get_latest_logs()`: 获取最新日志
- `get_new_logs()`: 获取新增日志（用于实时监控）

**配置更新**:
- `update_property()`: 更新单个配置项

**命令执行**:
- `send_command()`: 向服务器发送命令（通过stdin）

**日志格式化**:
- `_format_log_message()`: 格式化日志消息，移除冗余时间戳，翻译日志级别

#### Flask应用

**路由定义**:

主页:
```python
@app.route('/')
def index():
    return render_template('index.html')
```

API接口:
- `GET /api/status` - 获取服务器状态
- `POST /api/server/start` - 启动服务器
- `POST /api/server/stop` - 停止服务器
- `POST /api/server/restart` - 重启服务器
- `POST /api/server/kill-java` - 强制结束所有Java进程
- `POST /api/server/command` - 向服务器发送命令
- `GET /api/server/check-installed` - 检查服务器是否已安装
- `POST /api/server/install` - 安装Fabric服务器
- `GET /api/config` - 获取配置
- `POST /api/config` - 更新配置
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
- `GET /api/mods` - 获取Mod列表
- `POST /api/mods` - 添加Mod
- `DELETE /api/mods` - 删除Mod
- `GET /api/logs` - 获取日志
- `GET /api/command-output` - 获取命令输出
- `GET /api/backups` - 获取备份列表
- `POST /api/backups` - 创建备份
- `DELETE /api/backups` - 删除备份

#### HTTP轮询机制

**实时日志**:
- 客户端每秒调用 `GET /api/logs?lines=100`
- 使用哈希值检测内容变化，避免不必要的DOM更新
- 新增日志行会自动滚动到底部

**实时状态**:
- 客户端每5秒调用 `GET /api/status`
- 更新服务器状态徽章和性能统计

### 2. 前端架构

#### HTML结构
- 使用原生CSS，无外部依赖
- 响应式设计，支持移动端
- 深色主题，符合游戏风格

#### 主要组件

**导航栏**:
- 服务器名称和图标

**左侧面板**:
- 服务器控制按钮（启动/停止/重启/强制结束）
- 服务器信息卡片（内存、CPU、配置信息）
- 安装提示（未安装时显示）

**右侧面板**（所有板块直接显示）:
- 实时输出：显示服务器日志
- 命令执行：输入框和发送按钮
- 服务器配置：配置表单
- 白名单管理：白名单列表和操作
- 管理员管理：管理员列表和操作
- 封禁玩家管理：封禁列表和操作
- 封禁IP管理：IP封禁列表和操作
- Mod管理：Mod列表和操作
- 备份管理：备份列表和操作

#### JavaScript功能

**API调用**:
```javascript
async function apiCall(url, method = 'GET', data = null)
```
统一封装的API调用函数，处理错误和响应

**状态管理**:
- `loadStatus()`: 加载服务器状态（每5秒轮询）
- `updateStatus(status)`: 更新UI显示

**服务器控制**:
- `startServer()`: 启动服务器
- `stopServer()`: 停止服务器
- `restartServer()`: 重启服务器
- `killJava()`: 强制结束所有Java进程

**命令执行**:
- `sendCommand()`: 向服务器发送命令（通过stdin）

**配置管理**:
- `loadConfig()`: 加载配置到表单
- 表单提交保存配置（包括空置暂停时间）

**玩家管理**:
- 白名单管理（加载/添加/删除）
- 管理员管理（加载/添加/删除）
- 封禁玩家管理（加载/添加/删除）
- 封禁IP管理（加载/添加/删除）

**Mod管理**:
- `loadMods()`: 加载Mod列表
- `addMod()`: 添加Mod（待实现文件上传）
- `removeMod()`: 删除Mod

**备份管理**:
- `loadBackups()`: 加载备份列表
- `createBackup()`: 创建备份
- `deleteBackup()`: 删除备份
- `downloadBackup()`: 下载备份（待实现）

**日志显示**:
- `loadLogs()`: 加载历史日志（每1秒轮询）
- `appendLog(log)`: 添加日志行到显示区域
- 哈希值检测：只在内容变化时更新DOM
- 日志颜色分类（信息/警告/错误/成功/命令）
- 自动滚动到底部

**通知系统**:
- `showToast(message, type)`: 显示Toast通知

## 数据流

### 1. 服务器启动流程
```
用户点击"启动"按钮
  → startServer() JavaScript函数
  → POST /api/server/start
  → MCServerManager.start_server()
  → 启动Java进程
  → 返回结果
  → 更新UI显示
```

### 2. 实时日志流程
```
服务器进程输出日志
  → 后台线程读取stdout
  → 格式化日志消息（移除冗余时间戳，翻译日志级别）
  → 保存到data/logs/unified.log
  → 客户端每秒轮询 GET /api/logs
  → 返回最新日志行
  → 哈希值检测变化
  → 更新日志显示区域
```

### 3. 实时状态流程
```
客户端每5秒轮询
  → GET /api/status
  → 调用get_server_status()
  → 检查进程状态、CPU、内存
  → 返回状态数据
  → 客户端接收并updateStatus()
  → 更新状态徽章和统计信息
```

## 关键技术点

### 1. 线程安全
使用`threading.Lock()`保护服务器进程操作：
```python
with self.server_lock:
    # 服务器操作
```

### 2. 进程管理
使用`subprocess.Popen`管理Java进程：
- `stdin`: 发送命令（如stop）
- `stdout/stderr`: 捕获输出
- `poll()`: 检查进程状态
- `wait(timeout)`: 等待进程结束

### 3. 进程管理
使用`subprocess.Popen`管理Java进程：
- `stdin`: 发送命令（如stop、自定义命令）
- `stdout/stderr`: 捕获输出（后台线程持续读取）
- `poll()`: 检查进程状态
- `wait(timeout)`: 等待进程结束

### 4. 实时通信
使用HTTP轮询实现：
- 日志：每秒轮询一次
- 状态：每5秒轮询一次
- 哈希值检测避免不必要的DOM更新

### 5. 日志格式化
- 移除Minecraft日志中的冗余时间戳 `[HH:MM:SS]`
- 翻译日志级别为中文（INFO → 信息，ERROR → 错误等）
- 统一时间格式为 `HH:MM:SS`

### 4. 错误处理
所有操作返回统一格式的字典：
```python
{
    "success": True/False,
    "message": "操作结果描述",
    # 可选的其他字段
}
```

### 5. 配置管理
- properties文件：键值对格式
- JSON文件：whitelist.json, ops.json等
- 自动加载和保存

## 依赖项

### Python依赖
```
flask>=2.0.0
psutil>=5.8.0
```

### 系统依赖
```
java-17-jdk (或更高版本)
```

## 配置文件格式

### server.properties示例
```
server-name=Minecraft Server
motd=A Minecraft Server
max-players=20
server-port=25565
gamemode=survival
difficulty=easy
pvp=true
hardcore=false
allow-flight=false
level-name=world
level-seed=
level-type=minecraft:normal
view-distance=10
spawn-protection=16
online-mode=false
white-list=false
enforce-whitelist=false
spawn-monsters=true
spawn-animals=true
pause-when-empty-seconds=60
```

### JSON配置示例
```json
[
  {
    "uuid": "00000000-0000-0000-0000-000000000000",
    "name": "player_name",
    "level": 4
  }
]
```

## 扩展开发指南

### 添加新的API端点
1. 在Flask应用中定义路由
2. 调用MCServerManager相应方法
3. 返回JSON响应

示例：
```python
@app.route('/api/new-feature', methods=['POST'])
def api_new_feature():
    data = request.json
    result = manager.new_feature(data)
    return jsonify(result)
```

### 添加新的前端功能
1. 在HTML中添加UI元素
2. 在JavaScript中添加处理函数
3. 使用apiCall()与后端通信

### 改进日志系统
当前使用HTTP轮询和文件位置跟踪，可以改进为：
- 使用文件系统监控（如watchdog）
- 实现日志过滤和搜索
- 添加日志导出功能

### 添加文件上传功能
当前Mod上传功能待实现，需要：
1. 添加Flask文件上传处理
2. 验证文件类型和大小
3. 保存到mods目录

## 已知限制

1. **UUID获取**: 当前白名单和管理员UUID为占位符，需要从Mojang API获取真实UUID
2. **Mod上传**: 文件上传功能尚未实现
3. **备份下载**: 备份下载功能尚未实现
4. **玩家在线状态**: 不显示在线玩家列表
5. **无认证机制**: 当前没有用户认证，建议添加登录功能

## 安全考虑

1. **端口暴露**: 默认监听0.0.0.0:5000，建议在生产环境使用反向代理（如Nginx）
2. **认证**: 当前没有认证机制，建议添加用户认证
3. **CSRF保护**: 建议启用Flask-WTF CSRF保护
4. **输入验证**: 加强用户输入验证
5. **文件权限**: 确保配置文件和备份目录权限正确

## 性能优化建议

1. **日志监控**: 使用文件系统监控代替轮询
2. **状态更新**: 根据服务器运行状态调整更新频率
3. **缓存**: 缓存不常变化的数据（如配置）
4. **压缩**: 启用WebSocket和HTTP压缩
5. **静态资源**: 使用CDN或本地缓存静态资源

## 测试建议

1. **单元测试**: 为MCServerManager类编写单元测试
2. **集成测试**: 测试API端点
3. **端到端测试**: 使用Selenium测试Web界面
4. **负载测试**: 测试并发连接和日志处理

## 故障排查

### 服务器无法启动
1. 检查Java版本（需要17+）
2. 检查端口占用
3. 检查eula.txt
4. 查看日志文件

### WebSocket连接失败
1. 不适用（已改为HTTP轮询）

### 日志不更新
1. 检查后台线程是否正常运行
2. 检查日志文件权限
3. 查看浏览器控制台错误

### 配置保存失败
1. 检查文件权限
2. 检查配置文件格式
3. 查看服务器日志

## 未来改进方向

1. **用户认证**: 添加登录和权限管理
2. **多服务器支持**: 支持管理多个服务器
3. **玩家在线状态**: 显示在线玩家列表
4. **性能图表**: 使用Chart.js显示历史性能数据
5. **插件系统**: 支持第三方插件扩展
6. **移动应用**: 开发原生移动应用
7. **Docker支持**: 提供Docker镜像
8. **日志增强**: 添加日志搜索、过滤和导出功能

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送Pull Request

## 许可证

本项目仅供学习和个人使用。Minecraft是Mojang Studios的商标。