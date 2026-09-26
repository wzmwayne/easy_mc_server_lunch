# Minecraft Java Edition Server Properties 完整配置清单
## 版本 1.14 - 1.21.11

本文档详细列出了 Minecraft Java Edition 服务器配置文件 `server.properties` 中所有可用的配置项，包括其类型、默认值、有效范围和详细描述。

---

## 配置项分类

### 1. 服务器基本信息

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `server-name` | String | Minecraft Server | 任意字符串 | 服务器名称，显示在服务器列表中 |
| `motd` | String | A Minecraft Server | 任意字符串 | 服务器描述信息（Message of the Day），显示在服务器名称下方 |
| `server-ip` | String | (空) | 有效的IP地址 | 服务器监听的IP地址，留空则监听所有可用地址 |
| `server-port` | Integer | 25565 | 1-65535 | 服务器监听的TCP端口号 |

### 2. 玩家管理

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `max-players` | Integer | 20 | 0-(2^31-1) | 服务器同时支持的最大玩家数量 |
| `white-list` | Boolean | false | true/false | 是否启用白名单，启用后只有白名单玩家可以加入 |
| `enforce-whitelist` | Boolean | false | true/false | 是否强制执行白名单，启用后不在白名单的玩家会被踢出 |
| `player-idle-timeout` | Integer | 0 | 任意非负整数（分钟） | 玩家空闲超时时间，超过此时间玩家会被踢出（0=不踢出） |
| `op-permission-level` | Integer | 4 | 0-4 | 使用 `/op` 命令设置的管理员默认权限等级 |
| `function-permission-level` | Integer | 2 | 1-4 | 函数的默认权限等级 |
| `hide-online-players` | Boolean | false | true/false | 是否在状态请求中隐藏玩家列表 |
| `prevent-proxy-connections` | Boolean | false | true/false | 是否阻止代理连接（当ISP与Mojang认证服务器不同时踢出玩家） |

### 3. 游戏模式设置

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `gamemode` | String | survival | survival/creative/adventure/spectator | 默认游戏模式（1.14+接受字符串名称，旧版本支持数字0-3） |
| `force-gamemode` | Boolean | false | true/false | 是否强制玩家加入时使用默认游戏模式 |
| `difficulty` | String | easy | peaceful/easy/normal/hard | 服务器难度（1.14+接受字符串名称，旧版本支持数字0-3） |
| `hardcore` | Boolean | false | true/false | 是否启用硬核模式（难度强制为困难，死亡后变成旁观者） |
| `pvp` | Boolean | true | true/false | 是否允许PvP（玩家对战） |
| `allow-flight` | Boolean | false | true/false | 是否允许玩家在生存模式下飞行（需要模组支持） |

### 4. 世界生成设置

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `level-name` | String | world | 任意字符串 | 世界名称和目录名称 |
| `level-seed` | String | (空) | 任意字符串 | 世界种子，留空则使用随机种子 |
| `level-type` | String | minecraft:normal | minecraft:normal/flat/large_biomes/amplified/customized 等 | 世界类型预设 |
| `generate-structures` | Boolean | true | true/false | 是否生成结构（村庄、神殿等） |
| `generator-settings` | String | {} | JSON格式字符串 | 自定义世界生成设置 |
| `max-world-size` | Integer | 29999984 | 1-29999984 | 世界边界最大半径（方块数） |
| `spawn-protection` | Integer | 16 | 任意非负整数 | 出生点保护区域边长（2x+1），0=禁用 |

### 5. 性能和距离设置

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `view-distance` | Integer | 10 | 3-32 | 服务器视距（区块数，半径非直径） |
| `simulation-distance` | Integer | 10 | 3-32 | 模拟距离（生物更新的最大距离，区块数） |
| `network-compression-threshold` | Integer | 256 | 任意非负整数 | 网络数据包压缩阈值（字节数） |
| `entity-broadcast-range-percentage` | Integer | 100 | 10-1000 | 实体广播范围百分比（影响实体渲染距离） |
| `max-chained-neighbor-updates` | Integer | 1000000 | 任意整数（负数=无限制） | 连续方块更新最大数量限制 |
| `max-tick-time` | Integer | 60000 | -1或0-(2^63-1)（毫秒） | 单个tick最大允许时间，超时则服务器关闭 |
| `sync-chunk-writes` | Boolean | true | true/false | 是否启用同步区块写入（防止崩溃后数据丢失，但可能影响性能） |
| `use-native-transport` | Boolean | true | true/false | 是否使用原生传输（Linux性能优化） |

### 6. 网络和连接设置

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `online-mode` | Boolean | true | true/false | 是否启用在线模式（验证Minecraft账户） |
| `enforce-secure-profile` | Boolean | true | true/false | 是否只允许Mojang签名的公钥玩家加入 |
| `rate-limit` | Integer | 0 | 任意非负整数 | 玩家发送数据包的最大数量限制，0=禁用 |
| `pause-when-empty-seconds` | Integer | 60 | 任意非负整数（秒） | 服务器在无玩家时的暂停时间，0=禁用 |
| `log-ips` | Boolean | true | true/false | 是否在控制台和日志中记录玩家IP地址 |
| `snooper-enabled` | Boolean | true | true/false | 是否启用数据收集（已弃用，1.14+已移除） |

### 7. RCON 和查询设置

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `enable-rcon` | Boolean | false | true/false | 是否启用RCON（远程控制台） |
| `rcon.port` | Integer | 25575 | 1-65535 | RCON监听的TCP端口号 |
| `rcon.password` | String | (空) | 任意字符串 | RCON连接密码 |
| `broadcast-rcon-to-ops` | Boolean | true | true/false | 是否向在线管理员广播RCON命令输出 |
| `enable-query` | Boolean | false | true/false | 是否启用查询协议（GameSpy4） |
| `query.port` | Integer | 25565 | 1-65535 | 查询服务器监听的UDP端口号 |
| `broadcast-console-to-ops` | Boolean | true | true/false | 是否向在线管理员广播控制台命令输出 |

### 8. 资源包设置

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `resource-pack` | String | (空) | 有效的URL | 资源包下载地址 |
| `resource-pack-sha1` | String | (空) | SHA1哈希值（小写十六进制） | 资源包的SHA1校验和（推荐设置以验证完整性） |
| `resource-pack-prompt` | String | (空) | 聊天组件语法格式 | 资源包提示的自定义消息 |
| `resource-pack-id` | String | (空) | UUID格式 | 资源包的UUID标识符 |
| `require-resource-pack` | Boolean | false | true/false | 是否强制玩家使用资源包（拒绝则断开连接） |

### 9. 服务器功能开关

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `enable-status` | Boolean | true | true/false | 服务器是否显示为"在线"状态 |
| `enable-command-block` | Boolean | false | true/false | 是否启用命令方块 |
| `enable-jmx-monitoring` | Boolean | false | true/false | 是否启用JMX监控（需要额外JVM参数） |
| `enable-code-of-conduct` | Boolean | false | true/false | 是否启用行为准则文件检查 |

### 10. 管理服务器设置（1.20+）

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `management-server-enabled` | Boolean | false | true/false | 是否启用Minecraft服务器管理协议 |
| `management-server-host` | String | localhost | 有效的主机名或IP | 管理服务器监听的主机地址 |
| `management-server-port` | Integer | 0 | 任意端口号 | 管理服务器监听的端口号 |
| `management-server-secret` | String | (空) | 40个字母数字字符 | 管理服务器的授权密钥（留空则自动生成） |
| `management-server-tls-enabled` | Boolean | true | true/false | 管理服务器是否使用TLS加密 |
| `management-server-tls-keystore` | String | (空) | 密钥库文件路径 | TLS密钥库文件路径 |
| `management-server-tls-keystore-password` | String | (空) | 密钥库密码 | TLS密钥库密码 |

### 11. 数据包设置（1.20+）

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `initial-enabled-packs` | String | vanilla | 逗号分隔的数据包列表 | 世界创建时启用的数据包 |
| `initial-disabled-packs` | String | (空) | 逗号分隔的数据包列表 | 世界创建时禁用的数据包 |

### 12. 文本过滤设置（1.19+）

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `text-filtering-config` | String | (空) | 配置字符串 | 文本过滤机制配置（主要用于Realms） |
| `text-filtering-version` | Integer | 0 | 0或1 | 文本过滤配置的版本格式 |

### 13. 其他设置

| 配置项 | 类型 | 默认值 | 有效范围/选项 | 描述 |
|--------|------|--------|--------------|------|
| `region-file-compression` | String | deflate | deflate/gzip/zstd | 区域文件压缩算法（1.20+） |
| `status-heartbeat-interval` | Integer | 0 | 任意非负整数（毫秒） | 管理服务器发送心跳通知的间隔（1.20+） |
| `bug-report-link` | String | (空) | 有效的URL | 错误报告链接 |

---

## 已弃用或移除的配置项

以下配置项在新版本中已被移除或转换为游戏规则：

| 配置项 | 状态 | 替代方案 | 移除版本 |
|--------|------|----------|----------|
| `spawn-animals` | 已移除 | 游戏规则 `doMobSpawning` | 1.21 |
| `spawn-npcs` | 已移除 | 游戏规则 `doMobSpawning` | 1.21 |
| `spawn-monsters` | 已移除 | 游戏规则 `doMonsterSpawning` | 1.21 |
| `snooper-enabled` | 已移除 | 无 | 1.14 |
| `allow-nether` | 已移除 | 游戏规则 `allowNether` | 1.21 |

---

## 版本历史

### 1.14 (Village & Pillage 更新)
- `difficulty` 和 `gamemode` 现在接受字符串名称（不再仅支持数字）
- 移除了 `snooper-enabled`
- 优化了性能和光照系统

### 1.15 (Buzzy Bees 更新)
- 资源包大小限制从 50MB 增加到 100MB

### 1.16 (Nether Update 更新)
- 添加了 `enable-jmx-monitoring`
- 添加了 `prevent-proxy-connections`
- 添加了 `hide-online-players`

### 1.17 (Caves & Cliffs 第一部分)
- 添加了 `text-filtering-config`
- 添加了 `text-filtering-version`
- Java 要求从 8 升级到 16

### 1.18 (Caves & Cliffs 第二部分)
- 添加了 `simulation-distance`
- 资源包大小限制从 100MB 增加到 250MB
- 世界生成大幅改进

### 1.19 (The Wild Update 更新)
- 添加了 `enforce-secure-profile`
- 添加了 `previews-chat`（测试功能）

### 1.20 (Trails & Tales 更新)
- 添加了 `management-server-enabled` 及相关配置
- 添加了 `initial-enabled-packs` 和 `initial-disabled-packs`
- 添加了 `region-file-compression`
- 添加了 `status-heartbeat-interval`

### 1.21 (Tricky Trials 更新)
- 移除了 `spawn-animals`、`spawn-npcs`、`spawn-monsters`（转换为游戏规则）
- 移除了 `allow-nether`（转换为游戏规则）
- 添加了 `accepts-transfers`
- 添加了 `bug-report-link`

---

## 使用建议

1. **性能优化**：
   - 降低 `view-distance` 和 `simulation-distance` 可以显著提高性能
   - 设置 `max-players` 为实际需要的数量
   - 使用 `sync-chunk-writes=false` 可以提高性能，但会增加崩溃后数据丢失的风险

2. **安全建议**：
   - 生产环境应保持 `online-mode=true`
   - 启用 `enforce-secure-profile=true` 以增强安全性
   - 使用 `white-list` 和 `enforce-whitelist` 限制访问
   - 如果必须使用 `online-mode=false`，建议配合 `enforce-whitelist` 使用

3. **世界管理**：
   - 使用 `level-seed` 可以创建可重现的世界
   - `max-world-size` 可以限制世界边界大小
   - `spawn-protection` 可以保护出生点免受破坏

4. **网络优化**：
   - 调整 `network-compression-threshold` 可以优化网络带宽使用
   - `entity-broadcast-range-percentage` 可以控制实体渲染距离
   - `rate-limit` 可以防止数据包洪水攻击

---

## 注意事项

1. **文件编码**：`server.properties` 文件使用 UTF-8 编码
2. **修改生效**：修改配置后需要重启服务器才能生效，或使用 `/reload` 命令
3. **自动生成**：如果配置项不存在，服务器会在启动时自动添加并设置为默认值
4. **版本兼容性**：某些配置项在不同版本中可能有不同的行为或默认值
5. **数值范围**：超出指定范围的值可能会被服务器拒绝或重置为默认值

---

## 参考资源

- [Minecraft Wiki - Server.properties](https://minecraft.wiki/w/Server.properties)
- [Minecraft Wiki - Java Edition 版本历史](https://minecraft.wiki/w/Java_Edition)
- [Minecraft 官方服务器文档](https://www.minecraft.net/en-us/download/server)

---

*最后更新：2026年3月1日*
*适用于 Minecraft Java Edition 1.14 - 1.21.11*