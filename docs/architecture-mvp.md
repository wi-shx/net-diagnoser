# NetDiagnoser MVP - 架构设计文档

**文档版本**: v1.0
**创建日期**: 2026-02-15
**项目代号**: NetDiagnoser
**当前阶段**: MVP架构设计

---

## 📋 文档概述

### 文档目的
本文档定义NetDiagnoser MVP版本的技术架构，包括系统架构图、技术选型、模块划分、API规范和数据模型，为开发实现提供明确的指导。

### 适用范围
本文档适用于：
- 开发工程师（DE）：根据架构实现功能
- 测试工程师（QE）：根据架构编写测试用例
- 项目经理（PjM）：根据架构验收交付物

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  analyze     │  │   --log      │  │   --model    │        │
│  │  command     │  │   parameter  │  │   parameter  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Log Parser   │  │ AI Analyzer  │  │Report Generator│      │
│  │   Module     │  │   Module     │  │    Module     │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   GLM API    │  │  File System │  │  Config File │        │
│  │  (Zhipu AI)  │  │  (logs/reports)│  │  (.env/.yaml) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 架构分层说明

#### 1. CLI Layer（命令行层）
- **职责**: 提供用户交互界面
- **技术**: Python + Typer/Rich
- **组件**: 命令解析、参数验证、输出格式化

#### 2. Core Layer（核心层）
- **职责**: 实现核心业务逻辑
- **技术**: Python 3.10+
- **组件**:
  - Log Parser: 日志解析模块
  - AI Analyzer: AI分析模块
  - Report Generator: 报告生成模块

#### 3. External Services（外部服务层）
- **职责**: 与外部系统交互
- **组件**:
  - GLM API: 智谱AI大语言模型
  - File System: 文件读写
  - Config File: 配置管理

---

## 🔧 技术选型

### 核心技术栈

| 技术 | 选型 | 版本 | 用途 | 选择理由 |
|------|------|------|------|---------|
| **语言** | Python | 3.10+ | 主要开发语言 | 生态成熟，AI库丰富 |
| **CLI框架** | Typer | 0.9+ | 命令行界面 | 简单易用，自动生成帮助 |
| **输出美化** | Rich | 13.0+ | 终端美化 | 支持彩色输出、进度条 |
| **HTTP客户端** | httpx | 0.24+ | 调用GLM API | 支持async，性能好 |
| **配置管理** | python-dotenv | 1.0+ | 环境变量管理 | 简单易用，标准做法 |
| **日志处理** | PyYAML | 6.0+ | 配置文件（可选） | 支持复杂配置 |
| **测试框架** | pytest | 7.0+ | 单元测试 | 生态成熟，功能强大 |
| **代码规范** | black/ruff/mypy | 最新 | 代码质量 | 标准工具链 |

### AI模型选型

| 模型 | API | Token限制 | 成本 | 适用场景 |
|------|-----|-----------|------|---------|
| **GLM-4.7** | Zhipu AI | 128K | ¥0.05/1K tokens | 日志分析，文本生成 |
| **GLM-5.0** | Zhipu AI | 128K+ | ¥0.10/1K tokens | 复杂问题分析（可选） |

**默认模型**: GLM-4.7（性价比高，MVP够用）

---

## 📦 模块划分

### 项目结构

```
NetDiagnoser/
├── src/
│   ├── __init__.py
│   ├── cli.py                  # CLI入口
│   ├── config.py               # 配置管理
│   ├── core/
│   │   ├── __init__.py
│   │   ├── log_parser.py        # 日志解析器
│   │   ├── ai_analyzer.py       # AI分析器
│   │   └── report_generator.py  # 报告生成器
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py             # 解析器基类
│   │   ├── nginx_parser.py     # Nginx解析器
│   │   ├── haproxy_parser.py   # HAProxy解析器
│   │   └── syslog_parser.py    # Syslog解析器
│   └── utils/
│       ├── __init__.py
│       ├── file_handler.py     # 文件处理
│       ├── logger.py           # 日志工具
│       └── validator.py        # 参数验证
├── tests/
│   ├── unit/
│   │   ├── test_log_parser.py
│   │   ├── test_ai_analyzer.py
│   │   ├── test_report_generator.py
│   │   ├── test_nginx_parser.py
│   │   ├── test_haproxy_parser.py
│   │   └── test_syslog_parser.py
│   ├── integration/
│   │   └── test_analyze_workflow.py
│   └── fixtures/
│       ├── nginx_sample.log
│       ├── haproxy_sample.log
│       └── syslog_sample.log
├── docs/
│   ├── PRD-MVP.md
│   ├── user-stories.md
│   ├── README.md
│   └── architecture-mvp.md
├── reports/
│   └── .gitkeep
├── samples/
│   ├── connection-timeout.log
│   ├── dns-failure.log
│   ├── port-unreachable.log
│   ├── high-latency.log
│   └── service-error.log
├── .env.example
├── .env
├── requirements.txt
├── setup.py
├── README.md
└── pyproject.toml
```

### 模块职责

#### 1. CLI模块 (`cli.py`)
- **职责**: 命令行入口
- **主要函数**:
  - `analyze()`: 分析日志命令
  - `version()`: 显示版本号
- **依赖**: Typer, Rich

#### 2. 配置模块 (`config.py`)
- **职责**: 配置管理
- **主要类**:
  - `Config`: 配置类，加载.env文件
- **配置项**:
  - `GLM_API_KEY`: GLM API密钥
  - `GLM_API_URL`: GLM API地址
  - `DEFAULT_MODEL`: 默认模型（glm-4.7）
  - `MAX_LOG_SIZE`: 最大日志大小（100MB）

#### 3. 日志解析器 (`core/log_parser.py`)
- **职责**: 日志解析入口
- **主要类**:
  - `LogParser`: 日志解析器
  - `LogEntry`: 日志条目数据类
- **方法**:
  - `parse_file()`: 解析文件
  - `detect_format()`: 自动检测格式
  - `get_statistics()`: 获取统计信息
- **依赖**: parsers模块

#### 4. AI分析器 (`core/ai_analyzer.py`)
- **职责**: AI日志分析
- **主要类**:
  - `AIAnalyzer`: AI分析器
- **方法**:
  - `analyze()`: 分析日志
  - `build_prompt()`: 构建AI prompt
- **依赖**: httpx, GLM API

#### 5. 报告生成器 (`core/report_generator.py`)
- **职责**: 生成诊断报告
- **主要类**:
  - `ReportGenerator`: 报告生成器
- **方法**:
  - `generate()`: 生成报告
  - `save()`: 保存报告

#### 6. 解析器模块 (`parsers/`)
- **职责**: 实现各种日志格式解析
- **主要类**:
  - `BaseParser`: 解析器基类（抽象类）
  - `NginxParser`: Nginx解析器
  - `HAProxyParser`: HAProxy解析器
  - `SyslogParser`: Syslog解析器
- **方法**:
  - `parse()`: 解析单行日志
  - `extract_fields()`: 提取字段

#### 7. 工具模块 (`utils/`)
- **职责**: 工具函数
- **主要模块**:
  - `file_handler.py`: 文件处理（读取、写入）
  - `logger.py`: 日志工具
  - `validator.py`: 参数验证

---

## 🔌 API接口规范

### 内部API（模块间调用）

#### 1. LogParser API

```python
class LogParser:
    def __init__(self, format: str = None):
        """
        初始化日志解析器
        Args:
            format: 日志格式（nginx/haproxy/syslog），None表示自动检测
        """
        pass

    def parse_file(self, file_path: str) -> list[LogEntry]:
        """
        解析日志文件
        Args:
            file_path: 日志文件路径
        Returns:
            日志条目列表
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
        """
        pass

    def detect_format(self, file_path: str) -> str:
        """
        自动检测日志格式
        Args:
            file_path: 日志文件路径
        Returns:
            日志格式（nginx/haproxy/syslog/unknown）
        """
        pass

    def get_statistics(self, entries: list[LogEntry]) -> LogStatistics:
        """
        获取日志统计信息
        Args:
            entries: 日志条目列表
        Returns:
            统计信息（总行数、错误行数、错误率等）
        """
        pass
```

#### 2. AIAnalyzer API

```python
class AIAnalyzer:
    def __init__(self, api_key: str, model: str = "glm-4.7"):
        """
        初始化AI分析器
        Args:
            api_key: GLM API密钥
            model: 模型名称（glm-4.7/glm-5.0）
        """
        pass

    def analyze(self, entries: list[LogEntry], statistics: LogStatistics) -> AnalysisResult:
        """
        分析日志
        Args:
            entries: 日志条目列表
            statistics: 统计信息
        Returns:
            分析结果（问题类型、可能原因、风险等级）
        Raises:
            APIError: API调用失败
        """
        pass

    def build_prompt(self, entries: list[LogEntry], statistics: LogStatistics) -> str:
        """
        构建AI prompt
        Args:
            entries: 日志条目列表
            statistics: 统计信息
        Returns:
            AI prompt字符串
        """
        pass
```

#### 3. ReportGenerator API

```python
class ReportGenerator:
    def __init__(self, template_path: str = None):
        """
        初始化报告生成器
        Args:
            template_path: 报告模板路径（可选）
        """
        pass

    def generate(self, log_file: str, entries: list[LogEntry],
                 statistics: LogStatistics, analysis: AnalysisResult) -> str:
        """
        生成报告
        Args:
            log_file: 日志文件路径
            entries: 日志条目列表
            statistics: 统计信息
            analysis: 分析结果
        Returns:
            Markdown格式报告字符串
        """
        pass

    def save(self, content: str, output_path: str) -> None:
        """
        保存报告
        Args:
            content: 报告内容
            output_path: 输出路径
        """
        pass
```

### 外部API（GLM API）

#### 调用示例

```python
import httpx

async def call_glm_api(api_key: str, prompt: str, model: str = "glm-4.7") -> dict:
    """
    调用GLM API
    Args:
        api_key: API密钥
        prompt: AI prompt
        model: 模型名称
    Returns:
        API响应
    """
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "top_p": 0.9
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
```

#### 响应格式

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "AI分析结果（JSON格式）"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 1000,
    "completion_tokens": 500,
    "total_tokens": 1500
  }
}
```

---

## 📊 数据模型

### 1. LogEntry（日志条目）

```python
@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime      # 时间戳
    level: str             # 日志级别（INFO/WARN/ERROR/FATAL）
    message: str            # 日志消息
    raw: str               # 原始日志行
    fields: dict           # 提取的字段（IP、端口、状态码等）

    # Nginx特有字段
    ip_address: str = None
    request_method: str = None
    request_url: str = None
    status_code: int = None

    # HAProxy特有字段
    backend_name: str = None
    server_name: str = None

    # Syslog特有字段
    process: str = None
    pid: int = None
```

### 2. LogStatistics（日志统计）

```python
@dataclass
class LogStatistics:
    """日志统计信息"""
    total_lines: int          # 总行数
    error_lines: int          # 错误行数
    warning_lines: int        # 警告行数
    error_rate: float         # 错误率（百分比）
    level_counts: dict        # 按级别统计
    error_types: dict         # 按错误类型统计
    time_range: tuple         # 时间范围（开始、结束）
```

### 3. AnalysisResult（分析结果）

```python
@dataclass
class AnalysisResult:
    """AI分析结果"""
    problem_type: str        # 问题类型（连接超时/DNS解析失败/端口不可达/高延迟/服务异常/无问题）
    possible_causes: list    # 可能原因（Top 3）
    risk_level: str          # 风险等级（P0/P1/P2）
    suggested_commands: list # 建议的排查命令
    confidence: float        # 置信度（0.0-1.0）

    # 命令建议格式
    @dataclass
    class Command:
        category: str       # 命令分类（网络/端口/DNS/服务/防火墙）
        description: str    # 命令说明
        command: str        # 命令本身
```

### 4. ReportData（报告数据）

```python
@dataclass
class ReportData:
    """报告数据"""
    # 文件信息
    file_name: str
    file_size: int
    file_format: str
    analysis_time: datetime

    # 日志统计
    statistics: LogStatistics

    # 分析结果
    analysis: AnalysisResult
```

---

## 🔄 数据流

### 1. 分析流程

```
用户输入命令（CLI）
    ↓
参数验证（cli.py）
    ↓
加载日志文件（file_handler.py）
    ↓
解析日志（log_parser.py）
    ├── 检测格式
    ├── 调用对应解析器
    └── 提取字段
    ↓
生成统计信息（log_parser.py）
    ↓
构建AI prompt（ai_analyzer.py）
    ↓
调用GLM API（ai_analyzer.py）
    ↓
解析AI响应（ai_analyzer.py）
    ↓
生成报告（report_generator.py）
    ↓
保存报告（report_generator.py）
    ↓
输出到终端（cli.py）
```

### 2. 日志解析流程

```
日志文件
    ↓
读取文件（file_handler.py）
    ↓
逐行解析（base_parser.py）
    ├── 正则匹配
    ├── 提取字段
    └── 转换类型
    ↓
生成LogEntry对象
    ↓
添加到列表
    ↓
统计信息计算
    ↓
返回LogStatistics对象
```

### 3. AI分析流程

```
LogEntry列表 + LogStatistics
    ↓
构建prompt（ai_analyzer.py）
    ├── 添加日志摘要
    ├── 添加统计信息
    └── 添加分析要求
    ↓
调用GLM API
    ↓
获取AI响应
    ↓
解析JSON响应
    ↓
生成AnalysisResult对象
```

---

## 🎯 性能优化

### 1. 日志解析优化

**策略**：
- 使用生成器逐行读取，避免内存溢出
- 编译正则表达式（re.compile）
- 使用多进程解析大文件（可选）

**示例**：
```python
import re
from typing import Generator

def parse_large_file(file_path: str) -> Generator[LogEntry, None, None]:
    """逐行解析大文件"""
    pattern = re.compile(r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+)" (\d+) (\d+)$')
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line)
            if match:
                yield LogEntry.from_match(match)
```

### 2. AI调用优化

**策略**：
- 批量分析（一次API调用处理多条日志）
- 缓存分析结果
- 超时重试机制

**示例**：
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_analyze(log_hash: str) -> AnalysisResult:
    """缓存分析结果"""
    return ai_analyzer.analyze(...)
```

---

## 🔒 安全设计

### 1. API密钥管理

**策略**：
- 使用.env文件存储密钥
- 不提交.env到Git
- 运行时检查密钥是否存在

**示例**：
```python
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GLM_API_KEY")
if not api_key:
    raise ValueError("GLM_API_KEY not found in .env file")
```

### 2. 文件大小限制

**策略**：
- 限制单个文件最大100MB
- 文件过大时给出提示

**示例**：
```python
MAX_LOG_SIZE = 100 * 1024 * 1024  # 100MB

file_size = os.path.getsize(file_path)
if file_size > MAX_LOG_SIZE:
    raise ValueError(f"File too large: {file_size} bytes (max {MAX_LOG_SIZE})")
```

### 3. 敏感信息过滤

**策略**：
- 不显示完整的API密钥
- 过滤日志中的密码、token

**示例**：
```python
import re

def mask_sensitive_info(text: str) -> str:
    """过滤敏感信息"""
    text = re.sub(r'password=[^\s&]+', 'password=***', text)
    text = re.sub(r'token=[^\s&]+', 'token=***', text)
    return text
```

---

## 📋 部署架构

### 本地部署

```
NetDiagnoser（本地CLI）
    │
    ├── 日志文件（本地）
    ├── 配置文件（.env）
    └── GLM API（远程调用）
```

### 安装方式

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/netdiagnoser.git
cd netdiagnoser

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env，填入GLM_API_KEY

# 4. 安装CLI
pip install -e .

# 5. 运行
netdiagnoser analyze --log /path/to/log.log
```

---

## ✅ 架构评审检查清单

- [ ] 系统架构图清晰完整
- [ ] 技术选型有理有据
- [ ] 模块划分合理
- [ ] API接口规范完整
- [ ] 数据模型定义清晰
- [ ] 数据流程合理
- [ ] 性能优化策略可行
- [ ] 安全设计完善
- [ ] 部署方案明确

---

**文档状态**: ✅ 完成

**下一步**: 提交评审通过后，进入DE（开发工程师）角色，开始MVP开发实现
