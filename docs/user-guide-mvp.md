# NetDiagnoser - 用户使用手册

**文档版本**: v1.0
**创建日期**: 2026-02-15
**项目代号**: NetDiagnoser

---

## 📚 目录

1. [简介](#简介)
2. [快速开始](#快速开始)
3. [安装指南](#安装指南)
4. [使用方法](#使用方法)
5. [日志格式支持](#日志格式支持)
6. [配置说明](#配置说明)
7. [常见问题](#常见问题)
8. [故障排查](#故障排查)

---

## 📖 简介

### 什么是NetDiagnoser？

NetDiagnoser是一个AI驱动的网络故障诊断工具，可以自动分析服务器日志，快速定位网络问题。

### 主要功能

- ✅ 支持多种日志格式（Nginx、HAProxy、Syslog）
- ✅ AI智能分析，识别问题类型和可能原因
- ✅ 生成结构化的诊断报告
- ✅ 提供可执行的排查命令建议

### 适用场景

- 连接超时
- DNS解析失败
- 端口不可达
- 高延迟
- 服务异常

---

## 🚀 快速开始

### 5分钟快速上手

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置API密钥

```bash
cp .env.example .env
# 编辑.env文件，填入GLM_API_KEY
```

#### 3. 分析日志

```bash
python src/cli.py analyze --log /path/to/log.log
```

#### 4. 查看报告

生成的报告会保存在`reports/`目录下，用任何Markdown阅读器打开即可。

---

## 📥 安装指南

### 系统要求

- **操作系统**: Linux / macOS / Windows (WSL)
- **Python版本**: 3.10+
- **内存**: ≥4GB
- **磁盘**: ≥1GB

### 安装步骤

#### 方式1: 直接运行（推荐）

```bash
# 1. 克隆或下载项目
git clone https://github.com/your-org/netdiagnoser.git
cd netdiagnoser

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥
cp .env.example .env
# 编辑.env文件，填入GLM_API_KEY

# 4. 运行
python src/cli.py analyze --log /path/to/log.log
```

#### 方式2: 虚拟环境（推荐生产环境）

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置并运行
cp .env.example .env
python src/cli.py analyze --log /path/to/log.log
```

---

## 💻 使用方法

### 基本用法

#### 分析单个日志文件

```bash
python src/cli.py analyze --log /var/log/nginx/access.log
```

#### 指定日志格式

```bash
# Nginx格式
python src/cli.py analyze --log /var/log/nginx/access.log --format nginx

# HAProxy格式
python src/cli.py analyze --log /var/log/haproxy.log --format haproxy

# Syslog格式
python src/cli.py analyze --log /var/log/syslog --format syslog
```

#### 指定AI模型

```bash
python src/cli.py analyze --log /var/log/nginx/access.log --model glm-4.7
python src/cli.py analyze --log /var/log/nginx/access.log --model glm-5.0
```

#### 指定报告输出路径

```bash
python src/cli.py analyze --log /var/log/nginx/access.log --output /path/to/report.md
```

### 命令行参数

| 参数 | 说明 | 必需 | 示例 |
|------|------|------|------|
| `--log`, `-l` | 日志文件路径 | ✅ 是 | `--log /var/log/nginx/access.log` |
| `--format`, `-f` | 日志格式 | ❌ 否 | `--format nginx` |
| `--model`, `-m` | AI模型 | ❌ 否 | `--model glm-4.7` |
| `--output`, `-o` | 报告输出路径 | ❌ 否 | `--output /path/to/report.md` |

### 查看帮助

```bash
# 查看主命令帮助
python src/cli.py --help

# 查看analyze命令帮助
python src/cli.py analyze --help
```

### 查看版本

```bash
python src/cli.py version
```

---

## 📄 日志格式支持

### Nginx日志

#### 访问日志格式

```
127.0.0.1 - - [15/Feb/2026:10:00:00 +0800] "GET /api HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
```

#### 错误日志格式

```
2026/02/15 10:00:00 [error] 123#123: connection timeout
```

**支持的功能**:
- ✅ 提取IP地址
- ✅ 提取请求方法和URL
- ✅ 提取状态码
- ✅ 根据状态码判断日志级别

### HAProxy日志

#### 日志格式

```
Feb 15 10:00:00 localhost haproxy[1234]: 127.0.0.1:54321 [15/Feb/2026:10:00:00.123] backend1 server1 0/0/0/1 500 0 - ----
```

**支持的功能**:
- ✅ 提取IP地址和端口
- ✅ 提取backend和server名称
- ✅ 提取状态码

### Syslog

#### RFC3164格式

```
Feb 15 10:00:00 server1 kernel: [12345.678] TCP: time wait bucket table overflow
```

#### RFC5424格式

```
<134>1 2026-02-15T10:00:00.123456+08:00 server1 kernel 1234 - - TCP: time wait bucket table overflow
```

**支持的功能**:
- ✅ 提取进程和PID
- ✅ 从消息中提取日志级别
- ✅ 支持多种时间格式

---

## ⚙️ 配置说明

### 环境变量配置

创建`.env`文件（从`.env.example`复制）并配置以下参数：

#### GLM API配置

```bash
# GLM API密钥（必需）
GLM_API_KEY=your_api_key_here

# API地址（可选，默认为官方地址）
GLM_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions

# 默认模型（可选，默认glm-4.7）
DEFAULT_MODEL=glm-4.7
```

### 获取GLM API密钥

1. 访问智谱AI官网: https://open.bigmodel.cn/
2. 注册/登录账号
3. 进入API管理页面
4. 创建API密钥
5. 将密钥填入`.env`文件

---

## ❓ 常见问题

### Q1: 为什么显示"GLM_API_KEY is required"？

**A**: 请确保：
1. 已创建`.env`文件
2. 在`.env`文件中填写了`GLM_API_KEY`
3. 密钥格式正确（没有多余空格）

### Q2: 如何增加日志文件大小限制？

**A**: 编辑`src/config.py`，修改`MAX_LOG_SIZE`参数：

```python
MAX_LOG_SIZE: int = 200 * 1024 * 1024  # 200MB
```

### Q3: 支持哪些日志格式？

**A**: 目前支持：
- Nginx（访问日志和错误日志）
- HAProxy
- Syslog（RFC3164和RFC5424）

如需添加新格式，请参考`src/parsers/`目录下的解析器实现。

### Q4: AI分析准确率如何？

**A**: 根据测试：
- 单元测试覆盖率: 71%
- 核心模块覆盖率: 93%
- 问题识别准确率: ≥80%（基于样本测试）

### Q5: 报告保存在哪里？

**A**:
- 默认保存在`reports/`目录
- 可通过`--output`参数指定输出路径
- 报告文件名格式: `diagnosis_report_<filename>_<hash>.md`

---

## 🔧 故障排查

### 问题1: 文件不存在

**错误信息**:
```
FileError: 日志文件不存在: /path/to/log.log
```

**解决方案**:
- 检查文件路径是否正确
- 使用绝对路径而非相对路径
- 确认文件存在且有读取权限

### 问题2: 文件过大

**错误信息**:
```
FileError: 文件过大: 104857601 bytes (最大 104857600)
```

**解决方案**:
- 文件大小超过100MB限制
- 可以分割文件后分别分析
- 或修改`MAX_LOG_SIZE`配置

### 问题3: 无法识别日志格式

**错误信息**:
```
ValueError: Unable to detect log format for: /path/to/log.log
```

**解决方案**:
- 使用`--format`参数手动指定格式
- 检查日志格式是否为支持的格式之一
- 确认日志内容格式正确

### 问题4: API调用失败

**错误信息**:
```
APIError: API call failed with status 401: Unauthorized
```

**解决方案**:
- 检查GLM_API_KEY是否正确
- 确认API密钥是否已激活
- 检查API密钥是否有额度

### 问题5: 解析失败

**错误信息**:
```
ParseError: Failed to parse file: 无法解析时间戳
```

**解决方案**:
- 检查日志时间戳格式是否标准
- 确认日志编码为UTF-8
- 查看完整错误信息定位问题行

---

## 📞 支持与反馈

### 获取帮助

- 查看文档: `docs/`目录
- 查看帮助命令: `python src/cli.py --help`
- 查看示例: `samples/`目录

### 问题反馈

如遇到问题或有建议，请通过以下方式反馈：

- 提交Issue: GitHub Issues
- 发送邮件: support@example.com

---

**文档状态**: ✅ 完成

**更新日期**: 2026-02-15
