# 使用场景定义 - NetDiagnoser MVP

**文档版本**: v1.0
**创建日期**: 2026-02-14
**状态**: 已确认

---

## 场景总览

| ID | 场景名称 | 用户 | 优先级 | 涉及用户故事 |
|----|----------|------|--------|-------------|
| UC-001 | 生产服务器网络中断 | 运维工程师 | P0 | US-001, US-002 |
| UC-002 | 网卡驱动问题排查 | 运维工程师 | P0 | US-001, US-002 |
| UC-003 | 定制化软件日志异常 | 运维工程师 | P0 | US-001, US-002 |
| UC-004 | 开发环境连接问题 | 开发人员 | P1 | US-001 |
| UC-005 | 批量服务器健康检查 | 运维工程师 | P1 | US-002, US-004 |

---

## 场景详情

### UC-001: 生产服务器网络中断

**标题**: 生产服务器突然无法访问

**用户**: 运维工程师

**优先级**: P0

---

#### 前置条件

- 已配置SSH密钥到目标服务器
- 命令白名单已配置
- 有服务器日志文件

---

#### 操作步骤

**Step 1: 收集日志**
```
1. 登录到无法访问的服务器
2. 导出dmesg日志: `dmesg > dmesg.log`
3. 导出定制化软件日志（如果有）
```

**Step 2: 上传日志并分析**
```bash
# 使用NetDiagnoser CLI
netdiagnoser analyze --file dmesg.log
```

**预期输出**:
- 系统识别日志类型为dmesg
- AI分析日志中的网络相关错误
- 生成诊断报告

**Step 3: 查看诊断报告**

报告内容示例:
```markdown
# 网络诊断报告

## 问题摘要
- 问题类型: 网卡Link Down
- 严重程度: 高
- 时间范围: 2026-02-14 10:25:12 - 10:25:15

## 问题详情
### 日志分析
发现异常:
- [123456.789012] eth0: Link is Down
- [123457.123456] IPv6: ADDRCONF(NETDEV_UP): eth0: link is not ready

### 问题根因
网卡eth0物理连接断开或驱动异常

## 推荐命令
1. 检查网卡状态: `ip link show eth0`
2. 查看网卡驱动: `ethtool -i eth0`
3. 检查网络服务: `systemctl status network`

## 执行计划
- [ ] 命令1: 检查网卡状态
- [ ] 命令2: 检查网卡驱动
- [ ] 命令3: 检查网络服务
```

**Step 4: 批准并执行命令**
```bash
# 批准并执行推荐的命令
netdiagnoser execute --approve-all
```

**系统行为**:
- 显示每个命令，等待用户确认（单次/批量）
- 用户选择批量批准
- 通过SSH连接到服务器
- 按顺序执行命令
- 实时返回执行结果

**Step 5: 查看执行结果**

系统更新报告:
```markdown
## 执行结果

### 命令1: ip link show eth0
状态: ✅ 成功
输出:
2: eth0: <BROADCAST,MULTICAST,DOWN> mtu 1500 qdisc pfifo_fast state DOWN mode DEFAULT
    link/ether xx:xx:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff

### 命令2: ethtool -i eth0
状态: ✅ 成功
输出:
driver: e1000e
version: 3.2.6-k
firmware-version: 0.5-1

### 命令3: systemctl status network
状态: ✅ 成功
输出:
network.service - LSB: Bring up/down networking
   Loaded: loaded (/etc/rc.d/init.d/network)
   Active: active (exited)

## 诊断结论
网卡状态为DOWN，需要检查物理连接或重启网卡。
```

**Step 6: 根据结果修复**

根据诊断结果，用户执行:
```bash
# 重启网卡
netdiagnoser execute --command "ip link set eth0 up"
```

---

#### 期望结果

- 用户快速定位问题根因（< 1分钟）
- AI推荐的命令有效，帮助解决问题
- 执行过程安全可控，所有命令在白名单内

---

#### 异常处理

**异常1**: 命令不在白名单
- 系统拒绝执行
- 记录到审计日志
- 提示用户需要管理员配置

**异常2**: SSH连接失败
- 提示检查网络连接
- 提示检查SSH密钥配置
- 记录错误到日志

**异常3**: AI分析超时
- 提示网络问题或AI服务异常
- 提供基础诊断命令建议（不依赖AI）

---

### UC-002: 网卡驱动问题排查

**标题**: dmesg日志显示网卡驱动错误

**用户**: 运维工程师

**优先级**: P0

---

#### 前置条件

- 有dmesg日志文件
- 服务器正常运行

---

#### 操作步骤

**Step 1: 上传日志**
```bash
netdiagnoser analyze --file dmesg.log
```

**Step 2: AI分析**

日志示例:
```
[123456.789012] e1000e 0000:00:19.0 eth0: Reset adapter
[123457.234567] e1000e 0000:00:19.0 eth0: Hardware Error
```

AI识别:
- 问题类型: 硬件/驱动错误
- 严重程度: 高
- 可能原因: 网卡硬件故障或驱动不兼容

**Step 3: 推荐诊断命令**

```markdown
## 推荐命令
1. 查看驱动详细信息: `ethtool -i eth0`
2. 检查硬件状态: `ethtool eth0`
3. 查看内核日志: `dmesg | grep -i e1000e`
4. 更新驱动（如需要）: `modprobe -r e1000e && modprobe e1000e`
```

**Step 4: 执行并验证**

---

#### 期望结果

- AI准确识别驱动问题
- 推荐的命令有效，帮助定位问题
- 提供驱动更新或硬件更换建议

---

### UC-003: 定制化软件日志异常

**标题**: 定制化软件日志显示连接超时

**用户**: 运维工程师

**优先级**: P0

---

#### 前置条件

- 有定制化软件日志
- 已配置日志解析规则

---

#### 操作步骤

**Step 1: 配置日志解析规则**

配置文件示例（`config/log_patterns.yaml`）:
```yaml
custom_logs:
  app_x:
    pattern: '\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+): (.*)'
    fields:
      - timestamp
      - level
      - message
    error_keywords:
      - timeout
      - connection refused
      - network unreachable
```

**Step 2: 上传日志并分析**
```bash
netdiagnoser analyze --file app.log --pattern app_x
```

**Step 3: AI分析**

日志示例:
```
[2026-02-14 10:30:00] ERROR: Connection timeout to 192.168.1.100
[2026-02-14 10:30:05] ERROR: Connection timeout to 192.168.1.100
[2026-02-14 10:30:10] ERROR: Connection timeout to 192.168.1.100
```

AI识别:
- 问题类型: 网络连接超时
- 目标地址: 192.168.1.100
- 频率: 持续发生
- 可能原因: 目标不可达、网络拥堵、防火墙拦截

**Step 4: 推荐诊断命令**

```markdown
## 推荐命令
1. 测试连通性: `ping -c 4 192.168.1.100`
2. 检查路由: `traceroute 192.168.1.100`
3. 检查端口: `nc -zv 192.168.1.100 8080`
4. 检查防火墙: `iptables -L -n`
```

---

#### 期望结果

- 定制化日志成功解析
- AI准确识别连接超时问题
- 推荐的诊断命令有效

---

### UC-004: 开发环境连接问题

**标题**: 开发中遇到数据库连接问题

**用户**: 开发人员

**优先级**: P1

---

#### 前置条件

- 开发环境正常运行
- 有应用日志

---

#### 操作步骤

**Step 1: 上传应用日志**
```bash
netdiagnoser analyze --file app.log
```

**Step 2: AI分析并用自然语言解释**

AI输出:
```
问题原因: 应用无法连接到数据库
可能原因:
1. 数据库服务未启动
2. 网络不通
3. 连接配置错误

建议排查步骤:
1. 检查数据库服务: `systemctl status mysql`
2. 测试数据库连接: `telnet localhost 3306`
3. 查看网络配置: `ip addr show`
```

**Step 3: 执行检查命令**

---

#### 期望结果

- 用通俗易懂的语言解释问题
- 给出清晰的排查步骤
- 帮助开发人员理解问题并学习

---

### UC-005: 批量服务器健康检查

**标题**: 多台服务器定期网络健康检查

**用户**: 运维工程师

**优先级**: P1

---

#### 前置条件

- 已配置多台服务器信息
- 命令白名单已配置

---

#### 操作步骤

**Step 1: 配置服务器列表**

配置文件（`config/servers.yaml`）:
```yaml
servers:
  - name: server-1
    host: 192.168.1.10
    ssh_key: ~/.ssh/id_rsa
  - name: server-2
    host: 192.168.1.11
    ssh_key: ~/.ssh/id_rsa
  - name: server-3
    host: 192.168.1.12
    ssh_key: ~/.ssh/id_rsa
```

**Step 2: 执行批量健康检查**
```bash
netdiagnoser health-check --all-servers
```

**Step 3: 批准执行**

系统显示:
```
将对3台服务器执行以下命令:
- ping -c 4 8.8.8.8
- ip link show
- dmesg | grep -i error

是否继续? (y/n): y
```

**Step 4: 查看结果**

系统输出汇总:
```markdown
# 批量健康检查报告

## server-1 (192.168.1.10)
状态: ✅ 正常
网络延迟: 2ms
网卡状态: UP
内核错误: 0

## server-2 (192.168.1.11)
状态: ⚠️ 警告
网络延迟: 150ms
网卡状态: UP
内核错误: 3

## server-3 (192.168.1.12)
状态: ❌ 异常
网络延迟: 超时
网卡状态: DOWN
内核错误: 12
```

---

#### 期望结果

- 批量诊断多台服务器
- 快速定位有问题的服务器
- 提供汇总报告

---

## 场景映射到功能

| 场景 | 核心功能 | 依赖功能 |
|------|----------|----------|
| UC-001 | 日志解析、AI分析、SSH执行 | 命令白名单、批准机制 |
| UC-002 | dmesg解析、AI分析 | SSH执行 |
| UC-003 | 定制化日志解析、AI分析 | 日志模式配置 |
| UC-004 | 日志解析、AI分析 | 自然语言解释 |
| UC-005 | SSH执行、批量操作 | 服务器配置、审计日志 |

---

## 版本历史

| 版本 | 日期 | 修改内容 | 修改人 |
|------|------|----------|--------|
| v1.0 | 2026-02-14 | 初始版本 | PM（小王） |

---

**文档状态**: ✅ 已确认，进入架构设计阶段
