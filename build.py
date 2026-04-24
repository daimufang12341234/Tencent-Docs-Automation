#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 腾讯文档值班打卡自动化工具 - 打包脚本
# 作者：dmf
# 时间：2026/4/16

"""
使用 PyInstaller 打包为 Windows 可执行文件
"""

import os
import sys
import shutil
import subprocess
import ctypes


def is_admin():
    """检查是否以管理员身份运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """以管理员身份重新运行"""
    if sys.platform == 'win32':
        script = os.path.abspath(__file__)
        params = ' '.join([script] + sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit(0)


def clean_build_files():
    """清理旧的打包文件"""
    print("[1/4] 清理旧的打包文件...")

    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  - 删除目录: {dir_name}")

    # 删除 spec 文件
    for f in os.listdir('.'):
        if f.endswith('.spec'):
            os.remove(f)
            print(f"  - 删除文件: {f}")


def install_dependencies():
    """检查并安装打包依赖"""
    print("[2/4] 检查并安装打包依赖...")

    # 安装 PyInstaller
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller', '-q'], check=True)
    print("  - PyInstaller 已安装")

    # 安装项目依赖
    if os.path.exists('requirements.txt'):
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '-q'], check=True)
        print("  - 项目依赖已安装")


def build_exe():
    """执行打包"""
    print("[3/4] 开始打包...")

    # PyInstaller 参数 - 控制台版本（用于调试）
    args_console = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--name', 'DakaTool',
        '--console',                      # 显示窗口
        '--clean',
        '--noconfirm',

        '--add-data', 'ini_config;ini_config',
        '--add-data', 'config.ini;.',
        '--add-data', '使用说明.md;.',

        '--hidden-import', 'selenium',
        '--hidden-import', 'selenium.webdriver',
        '--hidden-import', 'selenium.webdriver.chrome',
        '--hidden-import', 'selenium.webdriver.chrome.service',
        '--hidden-import', 'selenium.webdriver.chrome.options',
        '--hidden-import', 'webdriver_manager',
        '--hidden-import', 'webdriver_manager.chrome',
        '--hidden-import', 'apscheduler',
        '--hidden-import', 'apscheduler.schedulers',
        '--hidden-import', 'apscheduler.schedulers.background',
        '--hidden-import', 'apscheduler.triggers',
        '--hidden-import', 'apscheduler.triggers.cron',

        '--collect-all', 'webdriver_manager',

        'main.py',
    ]

    # PyInstaller 参数 - 无窗口版本（用于正式使用）
    args_windowless = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--name', 'DakaToolBg',           # 后台版本名称
        '--noconsole',                    # 无窗口模式
        '--uac-admin',                    # 请求管理员权限
        '--clean',
        '--noconfirm',

        '--add-data', 'ini_config;ini_config',
        '--add-data', 'config.ini;.',
        '--add-data', '使用说明.md;.',

        '--hidden-import', 'selenium',
        '--hidden-import', 'selenium.webdriver',
        '--hidden-import', 'selenium.webdriver.chrome',
        '--hidden-import', 'selenium.webdriver.chrome.service',
        '--hidden-import', 'selenium.webdriver.chrome.options',
        '--hidden-import', 'webdriver_manager',
        '--hidden-import', 'webdriver_manager.chrome',
        '--hidden-import', 'apscheduler',
        '--hidden-import', 'apscheduler.schedulers',
        '--hidden-import', 'apscheduler.schedulers.background',
        '--hidden-import', 'apscheduler.triggers',
        '--hidden-import', 'apscheduler.triggers.cron',

        '--collect-all', 'webdriver_manager',

        'main.py',
    ]

    print("  - 打包控制台版本（DakaTool.exe）...")
    result = subprocess.run(args_console, check=True)
    if result.returncode != 0:
        print("  - 控制台版本打包失败！")
        sys.exit(1)

    print("  - 打包无窗口版本（DakaToolBg.exe）...")
    result = subprocess.run(args_windowless, check=True)
    if result.returncode != 0:
        print("  - 无窗口版本打包失败！")
        sys.exit(1)

    print("  - 打包成功！")


def create_release():
    """创建发布目录"""
    print("[4/4] 创建发布目录...")

    release_dir = 'release'
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)

    os.makedirs(release_dir)

    # 复制文件
    files_to_copy = [
        ('dist/DakaTool.exe', 'DakaTool.exe'),       # 控制台版本
        ('dist/DakaToolBg.exe', 'DakaToolBg.exe'),   # 无窗口版本
        ('config.ini', 'config.ini'),
        ('使用说明.md', '使用说明.md'),
    ]

    for src, dst in files_to_copy:
        src_path = src
        dst_path = os.path.join(release_dir, dst)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            print(f"  - 复制: {src} -> {dst_path}")
        else:
            print(f"  - 警告: {src} 不存在，跳过")

    print()
    print("=" * 50)
    print("打包完成！")
    print(f"发布目录: {release_dir}/")
    print()
    print("发布文件:")
    for f in os.listdir(release_dir):
        size = os.path.getsize(os.path.join(release_dir, f))
        size_mb = size / (1024 * 1024)
        print(f"  - {f} ({size_mb:.2f} MB)")
    print()
    print("使用方法:")
    print("  【调试模式】")
    print("  - DakaTool.exe --login      首次登录（可视化）")
    print("  - DakaTool.exe --debug      调试打卡（可视化）")
    print("  - DakaTool.exe --sign-in    手动签到（显示窗口）")
    print()
    print("  【正式使用 - 后台运行】")
    print("  - DakaToolBg.exe            启动定时打卡（无窗口）")
    print("  - DakaToolBg.exe --login    首次登录")
    print()
    print("  【查看日志】")
    print("  - 打开 logs/ 目录查看打卡日志")
    print("  - logs/daka_YYYYMMDD.log    每日日志")
    print("  - logs/daka_records.txt     打卡记录汇总")
    print("=" * 50)


def main():
    """主函数"""
    print("=" * 50)
    print("腾讯文档值班打卡自动化工具 - 打包脚本")
    print("=" * 50)
    print()

    # Windows 下检查管理员权限
    if sys.platform == 'win32' and not is_admin():
        print("需要管理员权限，正在请求...")
        run_as_admin()
        return

    # 检查是否在项目目录
    if not os.path.exists('main.py'):
        print("错误: 请在项目根目录运行此脚本")
        sys.exit(1)

    # 检查 Python 版本
    python_version = sys.version_info
    print(f"Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print()

    try:
        clean_build_files()
        install_dependencies()
        build_exe()
        create_release()
    except subprocess.CalledProcessError as e:
        print(f"错误: 执行失败 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()