# 腾讯文档值班打卡自动化工具

> 基于 Selenium + APScheduler 的自动化打卡解决方案，支持定时执行、登录状态持久化、后台静默运行。

---

## 功能特性

- **定时打卡**：支持自定义签到/签退时间，基于 Cron 表达式调度
- **手动触发**：支持命令行手动执行签到/签退操作
- **登录持久化**：Chrome 用户数据目录保存登录状态，无需重复登录
- **双模式运行**：控制台版（调试）+ 后台版（静默运行）
- **完整日志**：每日日志文件 + 打卡记录汇总
- **配置热更新**：运行中修改配置自动生效

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                     main.py (入口)                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ DakaScheduler│  │FormOperator │  │BrowserManager│   │
│  │  (定时调度)   │──│  (表单操作)  │──│  (浏览器管理) │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ ConfigLoader │  │   DakaLogger│                     │
│  │  (配置管理)   │  │   (日志记录) │                     │
│  └──────────────┘  └──────────────┘                     │
├─────────────────────────────────────────────────────────┤
│              ini_config (INI 配置解析模块)               │
└─────────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 入口 | `main.py` | 命令行参数解析、流程控制 |
| 定时调度 | `daka_tool/scheduler.py` | APScheduler Cron 任务调度 |
| 表单操作 | `daka_tool/form_operator.py` | 腾讯文档表单自动填写提交 |
| 浏览器管理 | `daka_tool/browser.py` | Chrome 启动/关闭、登录状态管理 |
| 配置管理 | `daka_tool/config_loader.py` | 配置文件读取、参数验证 |
| 日志记录 | `daka_tool/logger.py` | 分级日志、文件持久化 |
| INI解析 | `ini_config/` | 支持 interpolator 扩展的配置解析 |

### 技术栈

- **Python 3.8+** - 运行环境
- **Selenium 4.x** - 浏览器自动化
- **webdriver-manager** - Chrome 驱动自动管理
- **APScheduler 3.x** - 定时任务调度
- **PyInstaller** - 打包为 Windows 可执行文件

---

## 安装部署

### 方式一：源码运行

```bash
# 克隆仓库
git clone https://github.com/daimufang12341234/Tencent-Docs-Automation.git
cd Tencent-Docs-Automation

# 安装依赖
pip install -r requirements.txt

# 首次登录（可视化模式）
python main.py --login

# 启动定时服务
python main.py
```

### 方式二：打包部署

```bash
# 执行打包脚本
python build.py

# 发布目录
release/
├── DakaTool.exe      # 控制台版（调试用）
├── DakaToolBg.exe    # 后台版（静默运行）
├── config.ini        # 配置文件
```

---

## 配置说明

编辑 `config.ini` 文件：

```ini
[DOCUMENT]
# 腾讯文档表单链接
url = https://docs.qq.com/form/page/xxx

[USER]
# 组别
group = 3组
# 昵称
nickname = your_name
# 显示名称（组别+昵称）
display_name = 3组your_name

[SCHEDULE]
# 值班时间段
selected_slot = 09-12
# 签到时间（HH:MM）
sign_in_time = 08:55
# 签退时间（HH:MM）
sign_out_time = 12:05

[BROWSER]
# 后台静默运行
headless = true
# 登录数据目录
user_data_dir = chrome_data
# 超时时间（秒）
timeout = 30

[LOG]
log_dir = logs
log_level = INFO
```

---

## 使用指南

### 常用命令

| 命令 | 说明 |
|------|------|
| `python main.py` | 启动定时打卡服务 |
| `python main.py --login` | 首次登录（可视化） |
| `python main.py --sign-in` | 手动签到 |
| `python main.py --sign-out` | 手动签退 |
| `python main.py --debug` | 调试模式（可视化） |
| `python main.py --config` | 显示当前配置 |

### 打包版本使用

```bash
# 调试版（显示窗口）
DakaTool.exe --login     # 首次登录
DakaTool.exe --debug     # 调试打卡

# 后台版（无窗口）
DakaToolBg.exe           # 启动定时服务
DakaToolBg.exe --login   # 首次登录
```

### 日志查看

```
logs/
├── daka_20260424.log    # 每日运行日志
└── daka_records.txt     # 打卡记录汇总
```

---

## 项目结构

```
Tencent-Docs-Automation/
├── main.py                 # 主程序入口
├── config.ini              # 配置文件
├── requirements.txt        # Python 依赖
├── build.py                # 打包脚本
├── README.md               # 项目说明
│
├── daka_tool/              # 核心功能模块
│   ├── __init__.py
│   ├── scheduler.py        # 定时调度
│   ├── form_operator.py    # 表单操作
│   ├── browser.py          # 浏览器管理
│   ├── config_loader.py    # 配置加载
│   └── logger.py           # 日志记录
│
└── ini_config/             # INI 配置解析模块
    ├── __init__.py
    ├── core.py             # 核心解析逻辑
    ├── env_interpolator.py # 环境变量插值
    ├── section_proxy.py    # Section 代理
    └── exceptions.py       # 异常定义
```

---

## License

MIT License

## Author

dmf - 2026/04

---

---

# Tencent Docs Auto Clock-in Tool

> An automated clock-in solution based on Selenium + APScheduler, supporting scheduled execution, login state persistence, and silent background operation.

---

## Features

- **Scheduled Clock-in**: Custom sign-in/sign-out times with Cron-based scheduling
- **Manual Trigger**: Command-line sign-in/sign-out execution
- **Login Persistence**: Chrome user data directory saves login state, no repeated login needed
- **Dual Mode**: Console version (debug) + Background version (silent operation)
- **Full Logging**: Daily log files + clock-in record summary
- **Hot Config Update**: Auto-apply config changes during runtime

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     main.py (Entry)                      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ DakaScheduler│  │FormOperator │  │BrowserManager│   │
│  │ (Scheduling) │──│ (Form Ops)  │──│ (Browser Mgr)│   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ ConfigLoader │  │   DakaLogger│                     │
│  │ (Config Mgr) │  │    (Logger) │                     │
│  └──────────────┘  └──────────────┘                     │
├─────────────────────────────────────────────────────────┤
│              ini_config (INI Config Parser Module)       │
└─────────────────────────────────────────────────────────┘
```

### Core Modules

| Module | File | Function |
|--------|------|----------|
| Entry | `main.py` | CLI parsing, flow control |
| Scheduling | `daka_tool/scheduler.py` | APScheduler Cron task scheduling |
| Form Operations | `daka_tool/form_operator.py` | Auto-fill and submit Tencent Docs forms |
| Browser Manager | `daka_tool/browser.py` | Chrome start/stop, login state management |
| Config Manager | `daka_tool/config_loader.py` | Config reading, parameter validation |
| Logger | `daka_tool/logger.py` | Graded logging, file persistence |
| INI Parser | `ini_config/` | Extended INI parsing with interpolator |

### Tech Stack

- **Python 3.8+** - Runtime environment
- **Selenium 4.x** - Browser automation
- **webdriver-manager** - Auto Chrome driver management
- **APScheduler 3.x** - Scheduled task management
- **PyInstaller** - Package to Windows executable

---

## Installation & Deployment

### Method 1: Run from Source

```bash
# Clone repository
git clone https://github.com/daimufang12341234/Tencent-Docs-Automation.git
cd Tencent-Docs-Automation

# Install dependencies
pip install -r requirements.txt

# First login (visual mode)
python main.py --login

# Start scheduled service
python main.py
```

### Method 2: Package Deployment

```bash
# Run build script
python build.py

# Release directory
release/
├── DakaTool.exe      # Console version (debug)
├── DakaToolBg.exe    # Background version (silent)
├── config.ini        # Config file
```

---

## Configuration

Edit `config.ini`:

```ini
[DOCUMENT]
# Tencent Docs form URL
url = https://docs.qq.com/form/page/xxx

[USER]
# Group
group = Group3
# Nickname
nickname = your_name
# Display name (group + nickname)
display_name = Group3your_name

[SCHEDULE]
# Shift time slot
selected_slot = 09-12
# Sign-in time (HH:MM)
sign_in_time = 08:55
# Sign-out time (HH:MM)
sign_out_time = 12:05

[BROWSER]
# Silent background mode
headless = true
# Login data directory
user_data_dir = chrome_data
# Timeout (seconds)
timeout = 30

[LOG]
log_dir = logs
log_level = INFO
```

---

## Usage Guide

### Common Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Start scheduled clock-in service |
| `python main.py --login` | First login (visual mode) |
| `python main.py --sign-in` | Manual sign-in |
| `python main.py --sign-out` | Manual sign-out |
| `python main.py --debug` | Debug mode (visual) |
| `python main.py --config` | Show current config |

### Packaged Version Usage

```bash
# Debug version (visible window)
DakaTool.exe --login     # First login
DakaTool.exe --debug     # Debug clock-in

# Background version (no window)
DakaToolBg.exe           # Start scheduled service
DakaToolBg.exe --login   # First login
```

### View Logs

```
logs/
├── daka_20260424.log    # Daily runtime log
└── daka_records.txt     # Clock-in record summary
```

---

## Project Structure

```
Tencent-Docs-Automation/
├── main.py                 # Main entry
├── config.ini              # Config file
├── requirements.txt        # Python dependencies
├── build.py                # Build script
├── README.md               # Project readme
│
├── daka_tool/              # Core module
│   ├── __init__.py
│   ├── scheduler.py        # Scheduling
│   ├── form_operator.py    # Form operations
│   ├── browser.py          # Browser management
│   ├── config_loader.py    # Config loading
│   └── logger.py           # Logging
│
└── ini_config/             # INI parser module
    ├── __init__.py
    ├── core.py             # Core parsing logic
    ├── env_interpolator.py # Environment interpolation
    ├── section_proxy.py    # Section proxy
    └── exceptions.py       # Exceptions
```

---

## License

MIT License

## Author

dmf - 2026/04