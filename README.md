# NetDiagnoser
AI驱动的网络故障诊断工具

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
DEFAULT_MODEL=glm-4.7
```

### 使用方法

#### 分析日志文件

```bash
python src/cli.py analyze --log /path/to/log.log
```

#### 指定日志格式

```bash
python src/cli.py analyze --log /path/to/log.log --format nginx
```

#### 指定AI模型

```bash
python src/cli.py analyze --log /path/to/log.log --model glm-5.0
```

#### 指定报告输出路径

```bash
python src/cli.py analyze --log /path/to/log.log --output /path/to/report.md
```

#### 查看帮助

```bash
python src/cli.py --help
python src/cli.py analyze --help
```

#### 查看版本

```bash
python src/cli.py version
```

## 支持的日志格式

- **Nginx**: 访问日志和错误日志
- **HAProxy**: 负载均衡日志
- **Syslog**: RFC3164和RFC5424格式

## 项目结构

```
NetDiagnoser/
├── src/
│   ├── cli.py                  # CLI入口
│   ├── config.py               # 配置管理
│   ├── core/
│   │   ├── log_parser.py        # 日志解析器
│   │   ├── ai_analyzer.py       # AI分析器
│   │   └── report_generator.py  # 报告生成器
│   ├── parsers/
│   │   ├── base.py             # 解析器基类
│   │   ├── nginx_parser.py     # Nginx解析器
│   │   ├── haproxy_parser.py   # HAProxy解析器
│   │   └── syslog_parser.py    # Syslog解析器
│   └── utils/
│       ├── exceptions.py       # 自定义异常
│       ├── logger.py           # 日志工具
│       └── file_handler.py     # 文件处理
├── tests/
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── fixtures/               # 测试数据
├── docs/                       # 文档
├── reports/                    # 生成的报告
└── samples/                    # 示例日志
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/ tests/
```

### 代码检查

```bash
ruff check src/ tests/
```

## 许可证

Copyright © 2026
