# NetDiagnoser
AI驱动的网络故障诊断工具

## 功能特性

### 核心功能
- 日志分析：支持 Nginx、HAProxy、Syslog、dmesg 格式
- AI 诊断：使用 GLM AI 智能识别问题
- 报告生成：结构化 Markdown 诊断报告
- 命令白名单：安全的命令验证机制
- 审计日志：完整的操作记录

### 高级功能
- SSH 远程执行：在远程主机上执行诊断命令
- 工具执行器：带审批流程的命令执行
- Agent 诊断：AI 自主多轮诊断
- 自定义解析器：支持用户定义的日志格式

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
GLM_API_KEY=your_api_key_here
DEFAULT_MODEL=glm-4-flash
```

## 命令使用

### analyze - 分析日志文件

```bash
# 基本用法
python -m src.cli analyze --log /path/to/log.log

# 指定格式
python -m src.cli analyze --log /path/to/log.log --format nginx
python -m src.cli analyze --log /path/to/log.log --format dmesg

# 指定模型
python -m src.cli analyze --log /path/to/log.log --model glm-4.7

# 指定输出路径
python -m src.cli analyze --log /path/to/log.log --output report.md
```

### execute - 执行诊断命令

```bash
# 分析日志并预览执行计划
python -m src.cli execute --log samples/nginx_sample.log --dry-run

# 执行诊断命令（自动批准）
python -m src.cli execute --log samples/nginx_sample.log --auto-approve

# 在指定主机上执行
python -m src.cli execute --log samples/nginx_sample.log --host server1 --host server2
```

### agent - AI 自主诊断

```bash
# 运行 AI 代理诊断
python -m src.cli agent --log samples/nginx_sample.log

# 指定最大轮次
python -m src.cli agent --log samples/nginx_sample.log --max-rounds 3

# 使用模拟模式测试
python -m src.cli agent --log samples/nginx_sample.log --mock
```

### audit - 审计日志

```bash
# 查询审计日志
python -m src.cli audit --query

# 导出审计日志
python -m src.cli audit --export audit.json --format json
python -m src.cli audit --export audit.csv --format csv

# 过滤特定操作
python -m src.cli audit --action command_execute

# 查询最近 N 小时
python -m src.cli audit --hours 48
```

### whitelist - 命令白名单

```bash
# 列出所有白名单命令
python -m src.cli whitelist --list

# 按分类过滤
python -m src.cli whitelist --category network

# 检查命令是否允许
python -m src.cli whitelist --check "ping localhost"
```

### version - 查看版本

```bash
python -m src.cli version
```

## 支持的日志格式

| 格式 | 描述 |
|------|------|
| nginx | Nginx 访问日志和错误日志 |
| haproxy | HAProxy 负载均衡日志 |
| syslog | Syslog RFC3164 和 RFC5424 |
| dmesg | Linux 内核环形缓冲区日志 |
| custom | 用户自定义格式（通过 YAML 配置） |

## 项目结构

```
NetDiagnoser/
├── src/
│   ├── cli.py                  # CLI 入口
│   ├── config.py               # 配置管理
│   ├── core/
│   │   ├── log_parser.py       # 日志解析器
│   │   ├── ai_analyzer.py      # AI 分析器
│   │   ├── report_generator.py # 报告生成器
│   │   ├── command_whitelist.py# 命令白名单
│   │   ├── audit_logger.py     # 审计日志
│   │   ├── ssh_executor.py     # SSH 执行器
│   │   └── tool_executor.py    # 工具执行器
│   ├── parsers/
│   │   ├── base.py             # 解析器基类
│   │   ├── nginx_parser.py     # Nginx 解析器
│   │   ├── haproxy_parser.py   # HAProxy 解析器
│   │   ├── syslog_parser.py    # Syslog 解析器
│   │   ├── dmesg_parser.py     # dmesg 解析器
│   │   └── custom_parser.py    # 自定义解析器
│   ├── agent/
│   │   ├── base.py             # Agent 基类
│   │   ├── diagnostic_agent.py # 诊断 Agent
│   │   ├── tools.py            # Agent 工具
│   │   ├── memory.py           # Agent 记忆
│   │   └── prompts.py          # AI 提示词
│   └── utils/
│       ├── exceptions.py       # 自定义异常
│       ├── logger.py           # 日志工具
│       └── file_handler.py     # 文件处理
├── tests/
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── mocks/                  # Mock 工具
├── docs/                       # 文档
├── reports/                    # 生成的报告
├── samples/                    # 示例日志
└── logs/audit/                 # 审计日志
```

## 开发

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 带覆盖率
pytest --cov=src --cov-report=html
```

### 代码格式化

```bash
black src/ tests/
```

### 代码检查

```bash
ruff check src/ tests/
mypy src/
```

## 安全性

### 命令白名单

所有执行的命令都必须在白名单中。白名单包含以下安全命令分类：

- **网络**: ping, traceroute, curl, wget, nc, ip, ifconfig, arp, route, ethtool
- **端口**: netstat, ss, lsof
- **DNS**: dig, nslookup, host
- **服务**: systemctl, service
- **防火墙**: iptables, ip6tables, ufw, firewall-cmd
- **系统**: dmesg, journalctl, top, ps, free, vmstat, iostat, df, du, uptime

危险命令（如 rm、shutdown、dd）被明确阻止。

### 审计日志

所有操作都会被记录，包括：
- SSH 连接和断开
- 命令执行
- 日志分析
- Agent 操作

## 错误处理

工具提供详细的错误信息和异常类型：

| 错误类型 | 代码范围 | 描述 |
|----------|----------|------|
| FileError | 1000 | 文件操作错误 |
| ParseError | 2000 | 解析错误 |
| APIError | 3000 | API 调用错误 |
| ConfigError | 4000 | 配置错误 |
| ValidationError | 5000 | 验证错误 |
| SSHError | 6000 | SSH 相关错误 |
| ExecutionError | 7000 | 执行错误 |
| AgentError | 8000 | Agent 错误 |

## 许可证

Copyright © 2026
