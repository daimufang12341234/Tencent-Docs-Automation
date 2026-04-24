# 腾讯文档值班打卡自动化工具 | Tencent Docs Auto Clock-in Tool

> 基于 Selenium + APScheduler 的自动化打卡解决方案 | Automated clock-in solution based on Selenium + APScheduler

---

## 功能特性 | Features

| 中文 | English |
|------|---------|
| 定时打卡：支持自定义签到/签退时间，基于 Cron 表达式调度 | Scheduled Clock-in: Custom sign-in/sign-out times with Cron-based scheduling |
| 手动触发：支持命令行手动执行签到/签退操作 | Manual Trigger: Command-line sign-in/sign-out execution |
| 登录持久化：Chrome 用户数据目录保存登录状态，无需重复登录 | Login Persistence: Chrome user data directory saves login state |
| 双模式运行：控制台版（调试）+ 后台版（静默运行） | Dual Mode: Console version (debug) + Background version (silent) |
| 完整日志：每日日志文件 + 打卡记录汇总 | Full Logging: Daily log files + clock-in record summary |
| 配置热更新：运行中修改配置自动生效 | Hot Config Update: Auto-apply config changes during runtime |

---

## 技术架构 | Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     main.py (入口 | Entry)              │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ DakaScheduler│  │FormOperator │  │BrowserManager│   │
│  │  (定时调度)   │──│  (表单操作)  │──│  (浏览器管理) │   │
│  │(Scheduling)  │  │(Form Ops)   │  │(Browser Mgr) │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ ConfigLoader │  │   DakaLogger│                     │
│  │  (配置管理)   │  │   (日志记录) │                     │
│  │(Config Mgr)  │  │  (Logger)   │                     │
│  └──────────────┘  └──────────────┘                     │
├─────────────────────────────────────────────────────────┤
│              ini_config (INI 配置解析模块 | INI Parser) │
└─────────────────────────────────────────────────────────┘
```

### 核心模块 | Core Modules

| 模块 | Module | 文件 | File | 功能 | Function |
|------|--------|------|------|------|----------|
| 入口 | Entry | `main.py` | 命令行参数解析、流程控制 | CLI parsing, flow control |
| 定时调度 | Scheduling | `daka_tool/scheduler.py` | APScheduler Cron 任务调度 | APScheduler Cron task scheduling |
| 表单操作 | Form Ops | `daka_tool/form_operator.py` | 腾讯文档表单自动填写提交 | Auto-fill and submit Tencent Docs forms |
| 浏览器管理 | Browser Mgr | `daka_tool/browser.py` | Chrome 启动/关闭、登录状态管理 | Chrome start/stop, login state management |
| 配置管理 | Config Mgr | `daka_tool/config_loader.py` | 配置文件读取、参数验证 | Config reading, parameter validation |
| 日志记录 | Logger | `daka_tool/logger.py` | 分级日志、文件持久化 | Graded logging, file persistence |
| INI解析 | INI Parser | `ini_config/` | 支持 interpolator 扩展的配置解析 | Extended INI parsing with interpolator |

### 技术栈 | Tech Stack

- **Python 3.8+** - 运行环境 | Runtime environment
- **Selenium 4.x** - 浏览器自动化 | Browser automation
- **webdriver-manager** - Chrome 驱动自动管理 | Auto Chrome driver management
- **APScheduler 3.x** - 定时任务调度 | Scheduled task management
- **PyInstaller** - 打包为 Windows 可执行文件 | Package to Windows executable

---

## 安装部署 | Installation & Deployment

### 方式一：源码运行 | Method 1: Run from Source

```bash
# 克隆仓库 | Clone repository
git clone https://github.com/daimufang12341234/Tencent-Docs-Automation.git
cd Tencent-Docs-Automation

# 安装依赖 | Install dependencies
pip install -r requirements.txt

# 首次登录（可视化模式）| First login (visual mode)
python main.py --login

# 启动定时服务 | Start scheduled service
python main.py
```

### 方式二：打包部署 | Method 2: Package Deployment

```bash
# 执行打包脚本 | Run build script
python build.py

# 发布目录 | Release directory
release/
├── DakaTool.exe      # 控制台版（调试用）| Console version (debug)
├── DakaToolBg.exe    # 后台版（静默运行）| Background version (silent)
├── config.ini        # 配置文件 | Config file
```

---

## 配置说明 | Configuration

编辑 `config.ini` 文件 | Edit `config.ini`:

```ini
[DOCUMENT]
# 腾讯文档表单链接 | Tencent Docs form URL
url = https://docs.qq.com/form/page/xxx

[USER]
# 组别 | Group
group = 3组
# 昵称 | Nickname
nickname = your_name
# 显示名称 | Display name
display_name = 3组your_name

[SCHEDULE]
# 值班时间段 | Shift time slot
selected_slot = 09-12
# 签到时间（HH:MM）| Sign-in time
sign_in_time = 08:55
# 签退时间（HH:MM）| Sign-out time
sign_out_time = 12:05

[BROWSER]
# 后台静默运行 | Silent background mode
headless = true
# 登录数据目录 | Login data directory
user_data_dir = chrome_data
# 超时时间（秒）| Timeout (seconds)
timeout = 30

[LOG]
log_dir = logs
log_level = INFO
```

---

## 使用指南 | Usage Guide

### 常用命令 | Common Commands

| 命令 | Command | 说明 | Description |
|------|---------|------|-------------|
| `python main.py` | 启动定时打卡服务 | Start scheduled clock-in service |
| `python main.py --login` | 首次登录（可视化） | First login (visual mode) |
| `python main.py --sign-in` | 手动签到 | Manual sign-in |
| `python main.py --sign-out` | 手动签退 | Manual sign-out |
| `python main.py --debug` | 调试模式（可视化） | Debug mode (visual) |
| `python main.py --config` | 显示当前配置 | Show current config |

### 打包版本使用 | Packaged Version Usage

```bash
# 调试版（显示窗口）| Debug version (visible window)
DakaTool.exe --login     # 首次登录 | First login
DakaTool.exe --debug     # 调试打卡 | Debug clock-in

# 后台版（无窗口）| Background version (no window)
DakaToolBg.exe           # 启动定时服务 | Start scheduled service
DakaToolBg.exe --login   # 首次登录 | First login
```

### 日志查看 | View Logs

```
logs/
├── daka_20260424.log    # 每日运行日志 | Daily runtime log
└── daka_records.txt     # 打卡记录汇总 | Clock-in record summary
```

---

## 项目结构 | Project Structure

```
Tencent-Docs-Automation/
├── main.py                 # 主程序入口 | Main entry
├── config.ini              # 配置文件 | Config file
├── requirements.txt        # Python 依赖 | Dependencies
├── build.py                # 打包脚本 | Build script
├── README.md               # 项目说明 | Project readme
│
├── daka_tool/              # 核心功能模块 | Core module
│   ├── __init__.py
│   ├── scheduler.py        # 定时调度 | Scheduling
│   ├── form_operator.py    # 表单操作 | Form operations
│   ├── browser.py          # 浏览器管理 | Browser management
│   ├── config_loader.py    # 配置加载 | Config loading
│   └── logger.py           # 日志记录 | Logging
│
└── ini_config/             # INI 配置解析模块 | INI parser module
    ├── __init__.py
    ├── core.py             # 核心解析逻辑 | Core parsing logic
    ├── env_interpolator.py # 环境变量插值 | Env interpolation
    ├── section_proxy.py    # Section 代理 | Section proxy
    └── exceptions.py       # 异常定义 | Exceptions
```

---

## License

MIT License

## Author

dmf - 2026/04