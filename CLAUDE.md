# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NetDiagnoser is an AI-powered network fault diagnosis tool. It analyzes network logs (Nginx, HAProxy, Syslog, dmesg) and uses the GLM AI API to identify problems and suggest troubleshooting commands.

## Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and set GLM_API_KEY
```

### Running
```bash
# Analyze a log file
python -m src.cli analyze --log /path/to/log.log

# Specify format explicitly
python -m src.cli analyze --log /path/to/log.log --format nginx
python -m src.cli analyze --log /path/to/log.log --format dmesg

# Specify AI model
python -m src.cli analyze --log /path/to/log.log --model glm-5.0

# Specify output path
python -m src.cli analyze --log /path/to/log.log --output /path/to/report.md

# Execute diagnostic commands (dry-run)
python -m src.cli execute --log samples/nginx_sample.log --dry-run

# Execute with auto-approve
python -m src.cli execute --log samples/nginx_sample.log --auto-approve

# Run AI agent diagnosis
python -m src.cli agent --log samples/nginx_sample.log --mock

# Query audit logs
python -m src.cli audit --query

# List command whitelist
python -m src.cli whitelist --list

# Show version
python -m src.cli version
```

### Testing
```bash
# Run all tests
pytest tests/

# Run unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_log_parser.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Architecture

### Three-Layer Architecture

1. **CLI Layer** (`src/cli.py`) - Entry point using Typer/Rich for command parsing and output
2. **Core Layer** (`src/core/`) - Business logic:
   - `log_parser.py` - Parses logs using format-specific parsers
   - `ai_analyzer.py` - Calls GLM API for log analysis
   - `report_generator.py` - Generates Markdown diagnostic reports
   - `command_whitelist.py` - Validates commands for security
   - `audit_logger.py` - Records all operations for auditing
   - `ssh_executor.py` - Executes commands via SSH
   - `tool_executor.py` - Manages command execution workflow
3. **Parser Layer** (`src/parsers/`) - Format-specific log parsers:
   - `base.py` - Abstract `BaseParser` class and `LogEntry` dataclass
   - `nginx_parser.py`, `haproxy_parser.py`, `syslog_parser.py`, `dmesg_parser.py` - Concrete parsers
   - `custom_parser.py` - User-defined parser support
4. **Agent Layer** (`src/agent/`) - AI agent for autonomous diagnosis:
   - `base.py` - Agent base classes
   - `diagnostic_agent.py` - Main diagnostic agent
   - `tools.py` - Agent tools
   - `memory.py` - Context memory
   - `prompts.py` - AI prompts

### Data Flow
```
CLI (cli.py)
  -> LogParser detects format and parses file
  -> AIAnalyzer builds prompt and calls GLM API
  -> ReportGenerator creates Markdown report
  -> ToolExecutor/SSHExecutor executes commands (optional)
  -> AuditLogger records all operations
```

### Key Data Classes
- `LogEntry` - Parsed log line with timestamp, level, message, and format-specific fields
- `LogStatistics` - Aggregated stats (total/error lines, level counts, time range)
- `AnalysisResult` - AI analysis with problem_type, causes, risk_level, suggested_commands
- `ReportData` - Combined data for report generation
- `WhitelistedCommand` - Command definition for whitelist
- `AuditEntry` - Audit log entry
- `CommandResult` - Command execution result
- `AgentResult` - Agent diagnosis result

### Adding a New Log Format Parser

1. Create a new parser in `src/parsers/` extending `BaseParser`
2. Implement `parse_line()` and `detect()` classmethod
3. Register in `LogParser.PARSER_MAP` in `src/core/log_parser.py`

## Configuration

Configuration is loaded from `.env` file via `src/config.py`:
- `GLM_API_KEY` - Required API key for Zhipu AI
- `DEFAULT_MODEL` - Default AI model (glm-4-flash)
- `GLM_API_URL` - API endpoint

## Security

### Command Whitelist

All executed commands must be in the whitelist defined in `src/core/command_whitelist.py`. The whitelist includes:
- Network: ping, traceroute, curl, wget, nc, ip, ifconfig, arp, route
- Ports: netstat, ss, lsof
- DNS: dig, nslookup, host
- Services: systemctl, service
- Firewall: iptables, ufw, firewall-cmd
- System: dmesg, journalctl, top, ps, free, df

Dangerous commands (rm, shutdown, dd, etc.) are blocked.

### Audit Logging

All operations are logged via `src/core/audit_logger.py`:
- SSH connections
- Command executions
- Log analysis
- Agent actions

## Testing Notes

- Tests use mock API responses when `GLM_API_KEY=test_key_for_demo`
- Sample log files are in `samples/`
- Network error simulation available in `tests/mocks/network_simulator.py`
- Mock SSH executor available in `src/core/ssh_executor.py` (MockSSHExecutor)

## Error Codes

| Error Type | Code Range |
|------------|------------|
| FileError | 1000 |
| ParseError | 2000 |
| APIError | 3000 |
| ConfigError | 4000 |
| ValidationError | 5000 |
| SSHError | 6000 |
| ExecutionError | 7000 |
| AgentError | 8000 |
