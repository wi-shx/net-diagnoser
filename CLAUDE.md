# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NetDiagnoser is an AI-powered network fault diagnosis tool. It analyzes network logs (Nginx, HAProxy, Syslog) and uses the GLM AI API to identify problems and suggest troubleshooting commands.

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

# Specify AI model
python -m src.cli analyze --log /path/to/log.log --model glm-5.0

# Specify output path
python -m src.cli analyze --log /path/to/log.log --output /path/to/report.md

# Show version
python -m src.cli version
```

### Testing
```bash
# Run all tests
pytest tests/

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
3. **Parser Layer** (`src/parsers/`) - Format-specific log parsers:
   - `base.py` - Abstract `BaseParser` class and `LogEntry` dataclass
   - `nginx_parser.py`, `haproxy_parser.py`, `syslog_parser.py` - Concrete parsers

### Data Flow
```
CLI (cli.py)
  -> LogParser detects format and parses file
  -> AIAnalyzer builds prompt and calls GLM API
  -> ReportGenerator creates Markdown report
```

### Key Data Classes
- `LogEntry` - Parsed log line with timestamp, level, message, and format-specific fields
- `LogStatistics` - Aggregated stats (total/error lines, level counts, time range)
- `AnalysisResult` - AI analysis with problem_type, causes, risk_level, suggested_commands
- `ReportData` - Combined data for report generation

### Adding a New Log Format Parser

1. Create a new parser in `src/parsers/` extending `BaseParser`
2. Implement `parse_line()` and `detect()` classmethod
3. Register in `LogParser.PARSER_MAP` in `src/core/log_parser.py`

## Configuration

Configuration is loaded from `.env` file via `src/config.py`:
- `GLM_API_KEY` - Required API key for Zhipu AI
- `DEFAULT_MODEL` - Default AI model (glm-4.7)
- `GLM_API_URL` - API endpoint

## Testing Notes

- Tests use mock API responses when `GLM_API_KEY=test_key_for_demo`
- Sample log files are in `samples/`
- Integration tests test the full analyze workflow
