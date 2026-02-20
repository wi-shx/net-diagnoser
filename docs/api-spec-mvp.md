# NetDiagnoser MVP - API接口规范

**文档版本**: v1.0
**创建日期**: 2026-02-15
**项目代号**: NetDiagnoser

---

## 📋 文档概述

### 文档目的
本文档定义NetDiagnoser MVP版本的API接口规范，包括内部模块间接口和外部GLM API调用规范。

### 适用范围
本文档适用于：
- 开发工程师（DE）：根据接口规范实现功能
- 测试工程师（QE）：根据接口规范编写测试用例

---

## 📦 目录

1. [内部API](#内部api)
   - [LogParser](#1-logparser-api)
   - [AIAnalyzer](#2-aianalyzer-api)
   - [ReportGenerator](#3-reportgenerator-api)
   - [Config](#4-config-api)
2. [外部API](#外部api)
   - [GLM API](#glm-api)
3. [数据模型](#数据模型)
4. [错误处理](#错误处理)

---

## 🔌 内部API

### 1. LogParser API

#### 类定义

```python
from typing import List, Optional
from datetime import datetime

class LogParser:
    """日志解析器"""

    def __init__(self, format: Optional[str] = None) -> None:
        """
        初始化日志解析器

        Args:
            format: 日志格式（nginx/haproxy/syslog），None表示自动检测

        Raises:
            ValueError: 格式参数无效
        """
        pass

    def parse_file(self, file_path: str) -> List[LogEntry]:
        """
        解析日志文件

        Args:
            file_path: 日志文件路径

        Returns:
            日志条目列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持
            IOError: 文件读取失败
        """
        pass

    def detect_format(self, file_path: str) -> str:
        """
        自动检测日志格式

        Args:
            file_path: 日志文件路径

        Returns:
            日志格式（nginx/haproxy/syslog/unknown）

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件为空或无法识别
        """
        pass

    def get_statistics(self, entries: List[LogEntry]) -> LogStatistics:
        """
        获取日志统计信息

        Args:
            entries: 日志条目列表

        Returns:
            统计信息对象

        Raises:
            ValueError: entries为空列表
        """
        pass
```

#### 使用示例

```python
from netdiagnoser.core.log_parser import LogParser

# 自动检测格式
parser = LogParser()
entries = parser.parse_file("/var/log/nginx/access.log")
format = parser.detect_format("/var/log/nginx/access.log")

# 指定格式
parser = LogParser(format="nginx")
entries = parser.parse_file("/var/log/nginx/access.log")

# 获取统计信息
stats = parser.get_statistics(entries)
print(f"Total lines: {stats.total_lines}")
print(f"Error rate: {stats.error_rate}%")
```

---

### 2. AIAnalyzer API

#### 类定义

```python
from typing import List

class AIAnalyzer:
    """AI分析器"""

    def __init__(self, api_key: str, model: str = "glm-4.7") -> None:
        """
        初始化AI分析器

        Args:
            api_key: GLM API密钥
            model: 模型名称（glm-4.7/glm-5.0）

        Raises:
            ValueError: api_key为空或model不支持
        """
        pass

    def analyze(self, entries: List[LogEntry], statistics: LogStatistics) -> AnalysisResult:
        """
        分析日志

        Args:
            entries: 日志条目列表
            statistics: 统计信息

        Returns:
            分析结果对象

        Raises:
            APIError: API调用失败
            ValueError: entries或statistics无效
        """
        pass

    def build_prompt(self, entries: List[LogEntry], statistics: LogStatistics) -> str:
        """
        构建AI prompt

        Args:
            entries: 日志条目列表
            statistics: 统计信息

        Returns:
            AI prompt字符串

        Raises:
            ValueError: entries为空列表
        """
        pass
```

#### 使用示例

```python
from netdiagnoser.core.ai_analyzer import AIAnalyzer
from netdiagnoser.config import get_api_key

# 初始化
analyzer = AIAnalyzer(api_key=get_api_key(), model="glm-4.7")

# 分析日志
result = analyzer.analyze(entries, statistics)

# 查看结果
print(f"Problem type: {result.problem_type}")
print(f"Risk level: {result.risk_level}")
print(f"Possible causes: {result.possible_causes}")

# 查看命令建议
for cmd in result.suggested_commands:
    print(f"\n{cmd.category}:")
    print(f"  {cmd.description}")
    print(f"  {cmd.command}")
```

---

### 3. ReportGenerator API

#### 类定义

```python
from typing import Optional

class ReportGenerator:
    """报告生成器"""

    def __init__(self, template_path: Optional[str] = None) -> None:
        """
        初始化报告生成器

        Args:
            template_path: 报告模板路径（可选），None使用默认模板

        Raises:
            FileNotFoundError: 模板文件不存在
        """
        pass

    def generate(self, log_file: str, entries: List[LogEntry],
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

        Raises:
            ValueError: 参数无效
        """
        pass

    def save(self, content: str, output_path: str) -> None:
        """
        保存报告

        Args:
            content: 报告内容
            output_path: 输出路径

        Raises:
            IOError: 文件写入失败
        """
        pass
```

#### 使用示例

```python
from netdiagnoser.core.report_generator import ReportGenerator
from datetime import datetime

# 初始化
generator = ReportGenerator()

# 生成报告
report = generator.generate(
    log_file="/var/log/nginx/access.log",
    entries=entries,
    statistics=statistics,
    analysis=result
)

# 保存报告
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"reports/diagnosis_report_{timestamp}.md"
generator.save(report, output_path)

print(f"Report saved to: {output_path}")
```

---

### 4. Config API

#### 函数定义

```python
import os
from typing import Optional

class Config:
    """配置类"""

    # GLM API配置
    GLM_API_KEY: str
    GLM_API_URL: str = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    DEFAULT_MODEL: str = "glm-4.7"

    # 文件配置
    MAX_LOG_SIZE: int = 100 * 1024 * 1024  # 100MB

    # 输出配置
    REPORTS_DIR: str = "reports"

    @classmethod
    def load(cls, env_file: str = ".env") -> None:
        """
        加载配置

        Args:
            env_file: 环境变量文件路径

        Raises:
            FileNotFoundError: .env文件不存在
            ValueError: 必需配置项缺失
        """
        pass

    @classmethod
    def get(cls, key: str, default: Optional[Any] = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值

        Raises:
            KeyError: 配置项不存在且未提供默认值
        """
        pass
```

#### 使用示例

```python
from netdiagnoser.config import Config

# 加载配置
Config.load()

# 获取配置
api_key = Config.get("GLM_API_KEY")
model = Config.get("DEFAULT_MODEL")
max_size = Config.get("MAX_LOG_SIZE")

# 直接访问属性
api_key = Config.GLM_API_KEY
model = Config.DEFAULT_MODEL
```

---

## 🌐 外部API

### GLM API

#### 基本信息

| 属性 | 值 |
|------|-----|
| API URL | https://open.bigmodel.cn/api/paas/v4/chat/completions |
| 认证方式 | Bearer Token（API Key） |
| 请求方法 | POST |
| 内容类型 | application/json |

#### 请求格式

```http
POST https://open.bigmodel.cn/api/paas/v4/chat/completions
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "model": "glm-4.7",
  "messages": [
    {
      "role": "user",
      "content": "AI prompt here..."
    }
  ],
  "temperature": 0.3,
  "top_p": 0.9
}
```

#### 响应格式

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "AI分析结果（JSON格式）"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1000,
    "completion_tokens": 500,
    "total_tokens": 1500
  }
}
```

#### Prompt格式

```
你是一个网络诊断专家，请分析以下日志：

## 日志摘要
- 总行数: 10000
- 错误行数: 500
- 错误率: 5%
- 时间范围: 2026-02-15 10:00:00 - 2026-02-15 11:00:00

## 错误日志（最近100条）
[错误日志内容...]

## 分析要求
请分析上述日志，找出网络问题的原因。

请输出JSON格式：
{
  "problem_type": "问题类型",
  "possible_causes": ["原因1", "原因2", "原因3"],
  "risk_level": "P0/P1/P2",
  "suggested_commands": [
    {
      "category": "命令分类",
      "description": "命令说明",
      "command": "命令本身"
    }
  ],
  "confidence": 0.95
}

问题类型包括：连接超时、DNS解析失败、端口不可达、高延迟、服务异常、无问题
风险等级：P0（服务完全不可用）、P1（部分功能受影响）、P2（偶发问题）
```

#### 错误处理

| HTTP状态码 | 错误类型 | 处理方式 |
|-----------|---------|---------|
| 401 | 认证失败 | 检查API Key是否正确 |
| 429 | 请求超限 | 等待后重试 |
| 500 | 服务器错误 | 重试或联系技术支持 |
| 503 | 服务不可用 | 等待后重试 |

---

## 📊 数据模型

### LogEntry（日志条目）

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime      # 时间戳
    level: str             # 日志级别（INFO/WARN/ERROR/FATAL）
    message: str            # 日志消息
    raw: str               # 原始日志行
    fields: Dict[str, Any] = None  # 提取的字段

    # Nginx特有字段
    ip_address: Optional[str] = None
    request_method: Optional[str] = None
    request_url: Optional[str] = None
    status_code: Optional[int] = None

    # HAProxy特有字段
    backend_name: Optional[str] = None
    server_name: Optional[str] = None

    # Syslog特有字段
    process: Optional[str] = None
    pid: Optional[int] = None
```

### LogStatistics（日志统计）

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

@dataclass
class LogStatistics:
    """日志统计信息"""
    total_lines: int                      # 总行数
    error_lines: int                      # 错误行数
    warning_lines: int                    # 警告行数
    error_rate: float                     # 错误率（百分比）
    level_counts: Dict[str, int]           # 按级别统计
    error_types: Dict[str, int]           # 按错误类型统计
    time_range: tuple[datetime, datetime]  # 时间范围（开始、结束）
```

### AnalysisResult（分析结果）

```python
from dataclasses import dataclass
from typing import List

@dataclass
class AnalysisResult:
    """AI分析结果"""
    problem_type: str                        # 问题类型
    possible_causes: List[str]               # 可能原因（Top 3）
    risk_level: str                          # 风险等级（P0/P1/P2）
    suggested_commands: List['SuggestedCommand']  # 建议的排查命令
    confidence: float                        # 置信度（0.0-1.0）

@dataclass
class SuggestedCommand:
    """建议命令"""
    category: str       # 命令分类（网络/端口/DNS/服务/防火墙）
    description: str    # 命令说明
    command: str        # 命令本身
```

---

## ❌ 错误处理

### 异常定义

```python
class NetDiagnoserError(Exception):
    """基础异常类"""
    pass

class FileError(NetDiagnoserError):
    """文件操作异常"""
    pass

class ParseError(NetDiagnoserError):
    """解析异常"""
    pass

class APIError(NetDiagnoserError):
    """API调用异常"""
    pass

class ConfigError(NetDiagnoserError):
    """配置异常"""
    pass

class ValidationError(NetDiagnoserError):
    """验证异常"""
    pass
```

### 错误码定义

| 错误码 | 错误类型 | 描述 | HTTP状态码 |
|--------|---------|------|-----------|
| 1001 | FileError | 文件不存在 | 404 |
| 1002 | FileError | 文件过大 | 413 |
| 1003 | FileError | 文件格式不支持 | 400 |
| 2001 | ParseError | 解析失败 | 400 |
| 2002 | ParseError | 日志格式无法识别 | 400 |
| 3001 | APIError | API调用失败 | 500 |
| 3002 | APIError | API认证失败 | 401 |
| 3003 | APIError | API超时 | 504 |
| 4001 | ConfigError | 配置文件不存在 | 404 |
| 4002 | ConfigError | 配置项缺失 | 400 |
| 5001 | ValidationError | 参数验证失败 | 400 |

---

**文档状态**: ✅ 完成

**下一步**: 提交评审通过后，开始MVP开发实现
