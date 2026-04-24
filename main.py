#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 腾讯文档值班打卡自动化工具 - 主程序
# 作者：dmf
# 时间：2026/4/16

"""
腾讯文档值班打卡自动化工具

功能:
1. 定时自动打卡（签到/签退）
2. 手动触发打卡
3. 登录状态持久化
4. 后台静默运行/可视化调试模式
5. 完整日志记录

使用:
    python main.py              # 启动定时打卡服务
    python main.py --sign-in    # 手动执行签到
    python main.py --sign-out   # 手动执行签退
    python main.py --login      # 首次登录（可视化）
    python main.py --debug      # 调试模式（可视化）
    python main.py --config     # 显示当前配置
"""

import os
import sys
import time
import argparse
import signal

# 添加项目根目录到路径
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from daka_tool import (
    ConfigLoader,
    setup_logger,
    BrowserManager,
    FormOperator,
    DakaScheduler,
)
from daka_tool.logger import DakaLogger


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description='腾讯文档值班打卡自动化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s              启动定时打卡服务
  %(prog)s --sign-in    手动执行签到
  %(prog)s --sign-out   手动执行签退
  %(prog)s --login      首次登录（可视化模式）
  %(prog)s --debug      调试模式（可视化）
  %(prog)s --config     显示当前配置
  %(prog)s --stop       停止正在运行的服务
        """
    )

    parser.add_argument('--sign-in', action='store_true',
                        help='手动执行签到打卡')
    parser.add_argument('--sign-out', action='store_true',
                        help='手动执行签退打卡')
    parser.add_argument('--login', action='store_true',
                        help='首次登录QQ账号（可视化模式）')
    parser.add_argument('--debug', action='store_true',
                        help='调试模式，可视化浏览器')
    parser.add_argument('--config', action='store_true',
                        help='显示当前配置信息')
    parser.add_argument('--stop', action='store_true',
                        help='停止正在运行的定时服务')
    parser.add_argument('--config-file', type=str, default=None,
                        help='指定配置文件路径')

    args = parser.parse_args()

    # 加载配置
    try:
        config = ConfigLoader(args.config_file)
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请确保 config.ini 文件存在")
        sys.exit(1)

    # 创建日志记录器
    logger = DakaLogger(config.log_dir)

    # 显示配置
    if args.config:
        print(str(config))
        return

    # 创建浏览器管理器
    browser = BrowserManager(
        user_data_dir=config.user_data_dir,
        headless=config.headless,
        timeout=config.timeout,
        logger=logger.logger
    )

    # 创建表单操作器
    form_operator = FormOperator(browser, config, logger)

    # 创建定时调度器
    scheduler = DakaScheduler(config, browser, form_operator, logger)

    # 首次登录
    if args.login:
        logger.info("首次登录流程...")
        logger.info("将启动可视化浏览器，请在浏览器中登录QQ账号")

        # 强制可视化模式
        browser.headless = False

        if not form_operator.do_first_login():
            logger.error("首次登录失败")
            sys.exit(1)

        # 登录流程完成，浏览器已被用户手动关闭
        logger.info("首次登录流程完成，登录状态已保存")
        logger.info("后续打卡将自动使用已保存的登录状态")
        return

    # 手动签到
    if args.sign_in:
        logger.info("手动执行签到打卡...")
        # 使用配置中的headless设置，但可以通过--debug覆盖
        if args.debug:
            browser.headless = False

        if not browser.start(force_visible=args.debug):
            logger.error("启动浏览器失败")
            sys.exit(1)

        success = form_operator.do_daka("签到")
        browser.stop()

        if success:
            logger.info("签到打卡成功")
        else:
            logger.error("签到打卡失败")
            sys.exit(1)
        return

    # 手动签退
    if args.sign_out:
        logger.info("手动执行签退打卡...")
        if args.debug:
            browser.headless = False

        if not browser.start(force_visible=args.debug):
            logger.error("启动浏览器失败")
            sys.exit(1)

        success = form_operator.do_daka("签退")
        browser.stop()

        if success:
            logger.info("签退打卡成功")
        else:
            logger.error("签退打卡失败")
            sys.exit(1)
        return

    # 调试模式
    if args.debug:
        logger.info("调试模式启动...")
        logger.info("将执行一次完整的打卡流程（可视化模式）")

        browser.headless = False

        if not browser.start(force_visible=True):
            logger.error("启动浏览器失败")
            sys.exit(1)

        # 根据当前时间判断执行签到还是签退
        now = time.localtime()
        current_hour = now.tm_hour

        if current_hour < 12:
            action_type = "签到"
        else:
            action_type = "签退"

        logger.info(f"当前时间 {current_hour}点，将执行 {action_type}")

        success = form_operator.do_daka(action_type)
        browser.stop()

        if success:
            logger.info("调试打卡成功")
        else:
            logger.error("调试打卡失败")

        return

    # 启动定时服务
    logger.info("=" * 50)
    logger.info("腾讯文档值班打卡自动化工具")
    logger.info("=" * 50)
    logger.info(str(config))

    # 设置信号处理
    def signal_handler(sig, frame):
        logger.info("收到停止信号，正在停止服务...")
        scheduler.stop()
        browser.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 启动定时调度
    scheduler.start()

    logger.info("定时打卡服务已启动")
    logger.info("按 Ctrl+C 停止服务")

    # 显示下次执行时间
    next_times = scheduler.get_next_run_times()
    if next_times:
        logger.info("下次执行时间:")
        for name, time_str in next_times.items():
            logger.info(f"  - {name}: {time_str}")

    # 保持运行
    try:
        check_interval = 60  # 每60秒检查一次

        while True:
            time.sleep(check_interval)

            # 每分钟检查一下调度器状态
            if not scheduler.is_running():
                logger.warning("调度器意外停止，尝试重新启动...")
                scheduler.start()

            # 每分钟检查配置文件是否有变化
            scheduler.check_and_update_schedule()

    except KeyboardInterrupt:
        logger.info("用户中断，正在停止服务...")
        scheduler.stop()
        browser.stop()
        logger.info("服务已停止")


if __name__ == '__main__':
    main()