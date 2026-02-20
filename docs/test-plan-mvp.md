# NetDiagnoser MVP - 测试计划

**文档版本**: v1.0
**创建日期**: 2026-02-15
**项目代号**: NetDiagnoser

---

## 📋 测试概述

### 测试目标
验证NetDiagnoser MVP版本的功能完整性、稳定性和可用性，确保满足PRD中定义的所有需求。

### 测试范围
- **功能测试**: 验证所有核心功能是否正常工作
- **集成测试**: 验证模块间协作是否正常
- **性能测试**: 验证性能指标是否达标
- **用户场景测试**: 验证5个常见网络问题场景

### 不包含的范围
- 工具调用功能（阶段二）
- Agent自主排查（阶段三）
- Web界面（阶段二）
- 多服务器管理（阶段二）

---

## 🧪 测试策略

### 1. 单元测试（已完成）
- **覆盖率**: 71%
- **测试用例数**: 30个
- **状态**: ✅ 全部通过

### 2. 功能测试（待执行）
验证PRD中定义的6个核心功能

#### 2.1 日志上传功能
- 支持上传.log和.txt格式文件
- 单个文件最大支持100MB
- 文件不存在时给出友好提示
- 上传成功显示文件基本信息

#### 2.2 日志解析功能
- 支持解析nginx、haproxy、syslog三种格式
- 无法识别的格式给出提示
- 解析失败行单独记录
- 提取关键信息准确率≥95%

#### 2.3 AI分析功能
- 调用GLM API成功
- 分析结果结构化（JSON格式）
- 问题识别准确率≥80%（人工抽样评估）
- API调用超时重试机制

#### 2.4 诊断报告功能
- 报告结构清晰，易读
- 包含文件信息、日志概览、分析结果、建议命令
- Markdown格式正确
- 报告自动保存到reports/目录

#### 2.5 命令建议功能
- 至少提供3类命令（网络、端口、DNS）
- 命令格式包含说明和示例
- 命令适用于Linux系统
- 避免危险命令（如rm、重启服务）

#### 2.6 CLI界面功能
- 核心命令可用
- 参数验证完善
- 帮助文档清晰
- 错误提示友好

### 3. 用户场景测试（待执行）
验证5个常见网络问题场景

#### 场景1: 连接超时
- 日志文件: `samples/connection-timeout.log`
- 预期结果: AI识别为"连接超时"
- 风险等级: P0

#### 场景2: DNS解析失败
- 日志文件: `samples/dns-failure.log`
- 预期结果: AI识别为"DNS解析失败"
- 风险等级: P0

#### 场景3: 端口不可达
- 日志文件: `samples/port-unreachable.log`
- 预期报告: AI识别为"端口不可达"
- 风险等级: P0

#### 场景4: 高延迟
- 日志文件: `samples/high-latency.log`
- 预期结果: AI识别为"高延迟"
- 风险等级: P1

#### 场景5: 服务异常
- 日志文件: `samples/service-error.log`
- 预期结果: AI识别为"服务异常"
- 风险等级: P1

---

## 📊 测试环境

### 硬件环境
- CPU: 标准配置
- 内存: ≥4GB
- 磁盘: ≥1GB

### 软件环境
- 操作系统: Linux (WSL2)
- Python版本: 3.14.3
- 依赖包: requirements.txt

### 测试数据
- Nginx日志样本: `samples/nginx_sample.log`
- HAProxy日志样本: `samples/haproxy_sample.log`
- Syslog日志样本: `samples/syslog_sample.log`
- 场景日志: 5个场景日志文件（待创建）

---

## 🔍 测试用例

### 功能测试用例

#### TC-001: 上传有效的.log文件
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/nginx_sample.log`
- **预期结果**: 成功上传，显示文件信息
- **实际结果**: 待测试

#### TC-002: 上传不存在的文件
- **步骤**:
  1. 运行`python src/cli.py analyze --log nonexistent.log`
- **预期结果**: 提示"文件不存在"
- **实际结果**: 待测试

#### TC-003: 解析Nginx日志
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/nginx_sample.log --format nginx`
- **预期结果**: 成功解析，显示统计信息
- **实际结果**: 待测试

#### TC-004: 解析HAProxy日志
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/haproxy_sample.log --format haproxy`
- **预期结果**: 成功解析，显示统计信息
- **实际结果**: 待测试

#### TC-005: 解析Syslog
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/syslog_sample.log --format syslog`
- **预期结果**: 成功解析，显示统计信息
- **实际结果**: 待测试

#### TC-006: 自动检测日志格式
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/nginx_sample.log`
- **预期结果**: 自动识别为nginx格式
- **实际结果**: 待测试

#### TC-007: AI分析功能
- **步骤**:
  1. 配置GLM_API_KEY
  2. 运行`python src/cli.py analyze --log samples/nginx_sample.log`
- **预期结果**: AI分析完成，显示问题类型和可能原因
- **实际结果**: 待测试

#### TC-008: 生成诊断报告
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/nginx_sample.log`
  2. 检查reports/目录
- **预期结果**: 报告文件存在，Markdown格式正确
- **实际结果**: 待测试

#### TC-009: 命令建议
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/nginx_sample.log`
  2. 查看报告中的命令建议
- **预期结果**: 至少提供3类命令
- **实际结果**: 待测试

#### TC-010: CLI帮助文档
- **步骤**:
  1. 运行`python src/cli.py --help`
  2. 运行`python src/cli.py analyze --help`
- **预期结果**: 帮助文档清晰
- **实际结果**: 待测试

### 用户场景测试用例

#### TC-101: 连接超时场景
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/connection-timeout.log`
- **预期结果**: AI识别为"连接超时"，风险等级P0
- **实际结果**: 待测试

#### TC-102: DNS解析失败场景
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/dns-failure.log`
- **预期结果**: AI识别为"DNS解析失败"，风险等级P0
- **实际结果**: 待测试

#### TC-103: 端口不可达场景
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/port-unreachable.log`
- **预期结果**: AI识别为"端口不可达"，风险等级P0
- **实际结果**: 待测试

#### TC-104: 高延迟场景
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/high-latency.log`
- **预期结果**: AI识别为"高延迟"，风险等级P1
- **实际结果**: 待测试

#### TC-105: 服务异常场景
- **步骤**:
  1. 运行`python src/cli.py analyze --log samples/service-error.log`
- **预期结果**: AI识别为"服务异常"，风险等级P1
- **实际结果**: 待测试

---

## 📊 缺陷管理

### 缺陷等级定义

| 等级 | 描述 | 示例 |
|------|------|------|
| P0 | 致命缺陷，功能完全不可用 | 程序崩溃、数据丢失 |
| P1 | 严重缺陷，主要功能受影响 | 核心功能失败、数据错误 |
| P2 | 一般缺陷，部分功能受影响 | 界面错误、文档错误 |
| P3 | 轻微缺陷，不影响功能 | 拼写错误、建议优化 |

### 缺陷跟踪

| ID | 标题 | 等级 | 状态 | 发现日期 | 负责人 |
|----|------|------|------|----------|--------|
| DEF-001 | 待填充 | - | - | - | - |

---

## ✅ 验收标准

### 功能验收
- [ ] 所有P0功能100%实现
- [ ] 所有测试用例通过率≥95%
- [ ] P0/P1缺陷数为0
- [ ] 文档完整

### 质量验收
- [ ] 单元测试覆盖率≥80%
- [ ] 代码符合PEP 8规范
- [ ] 代码审查通过
- [ ] 性能指标达标

### 性能验收
- [ ] 日志解析速度≥1000行/秒
- [ ] AI分析响应时间≤30秒（10000行日志）
- [ ] 内存占用≤500MB
- [ ] 支持日志文件大小≤100MB

---

## 📅 测试进度

| 阶段 | 状态 | 开始日期 | 完成日期 |
|------|------|----------|----------|
| 单元测试 | ✅ 完成 | 2026-02-15 | 2026-02-15 |
| 功能测试 | 🔄 进行中 | 2026-02-15 | 待完成 |
| 用户场景测试 | ⏸️ 待开始 | 待开始 | 待完成 |
| 缺陷修复 | ⏸️ 待开始 | 待开始 | 待完成 |
| 测试报告 | ⏸️ 待开始 | 待完成 | 待完成 |

---

**文档状态**: ✅ 完成

**下一步**: 执行功能测试和用户场景测试
