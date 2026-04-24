# 定时任务模块
# 作者：dmf
# 时间：2026/4/16
"""
定时打卡任务调度
"""

import time
import threading
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class DakaScheduler:
    """打卡定时任务调度器"""

    def __init__(self, config, browser_manager, form_operator, logger):
        """
        初始化调度器

        参数:
            config: 配置加载器实例
            browser_manager: 浏览器管理器实例
            form_operator: 表单操作器实例
            logger: 日志记录器实例
        """
        self.config = config
        self.browser = browser_manager
        self.form_operator = form_operator
        self.logger = logger

        self.scheduler = None
        self.running = False

        # 记录当前配置的时间，用于检测变化
        self._current_sign_in_time = None
        self._current_sign_out_time = None

    def start(self):
        """启动定时任务调度"""
        if self.running:
            self.logger.warning("定时任务已运行")
            return

        self.logger.info("启动定时任务调度...")

        # 创建后台调度器
        self.scheduler = BackgroundScheduler()

        # 获取当前配置的时间
        sign_in_time = self.config.sign_in_time
        sign_out_time = self.config.sign_out_time

        # 记录当前配置
        self._current_sign_in_time = sign_in_time
        self._current_sign_out_time = sign_out_time

        # 解析签到时间
        sign_in_hour, sign_in_minute = self._parse_time(sign_in_time)

        # 解析签退时间
        sign_out_hour, sign_out_minute = self._parse_time(sign_out_time)

        # 添加签到任务
        self.scheduler.add_job(
            self._do_sign_in,
            CronTrigger(hour=sign_in_hour, minute=sign_in_minute),
            id='sign_in',
            name='签到打卡',
            misfire_grace_time=300  # 允许5分钟内的延迟执行
        )

        # 添加签退任务
        self.scheduler.add_job(
            self._do_sign_out,
            CronTrigger(hour=sign_out_hour, minute=sign_out_minute),
            id='sign_out',
            name='签退打卡',
            misfire_grace_time=300
        )

        # 启动调度器
        self.scheduler.start()
        self.running = True

        self.logger.info(f"定时任务已启动:")
        self.logger.info(f"  - 签到时间: {sign_in_time}")
        self.logger.info(f"  - 签退时间: {sign_out_time}")

    def check_and_update_schedule(self):
        """
        检查配置文件是否有变化，如有则更新任务时间

        返回:
            bool: 是否有变化
        """
        if not self.scheduler or not self.running:
            return False

        # 重新加载配置
        try:
            self.config.reload()
        except Exception as e:
            self.logger.warning(f"重新加载配置失败: {e}")
            return False

        # 获取新的时间配置
        new_sign_in_time = self.config.sign_in_time
        new_sign_out_time = self.config.sign_out_time

        # 检查是否有变化
        changed = False

        if new_sign_in_time != self._current_sign_in_time:
            self.logger.info(f"签到时间已修改: {self._current_sign_in_time} -> {new_sign_in_time}")
            sign_in_hour, sign_in_minute = self._parse_time(new_sign_in_time)

            # 删除旧任务，添加新任务（更可靠）
            self.scheduler.remove_job('sign_in')
            self.scheduler.add_job(
                self._do_sign_in,
                CronTrigger(hour=sign_in_hour, minute=sign_in_minute),
                id='sign_in',
                name='签到打卡',
                misfire_grace_time=300
            )
            self._current_sign_in_time = new_sign_in_time
            changed = True

        if new_sign_out_time != self._current_sign_out_time:
            self.logger.info(f"签退时间已修改: {self._current_sign_out_time} -> {new_sign_out_time}")
            sign_out_hour, sign_out_minute = self._parse_time(new_sign_out_time)

            # 删除旧任务，添加新任务（更可靠）
            self.scheduler.remove_job('sign_out')
            self.scheduler.add_job(
                self._do_sign_out,
                CronTrigger(hour=sign_out_hour, minute=sign_out_minute),
                id='sign_out',
                name='签退打卡',
                misfire_grace_time=300
            )
            self._current_sign_out_time = new_sign_out_time
            changed = True

        if changed:
            self.logger.info("定时任务已更新")
            # 输出新的下次执行时间
            next_times = self.get_next_run_times()
            if next_times:
                self.logger.info("新的下次执行时间:")
                for name, time_str in next_times.items():
                    self.logger.info(f"  - {name}: {time_str}")

        return changed

    def stop(self):
        """停止定时任务调度"""
        if self.scheduler:
            self.scheduler.shutdown()
            self.scheduler = None
        self.running = False
        self.logger.info("定时任务已停止")

    def _parse_time(self, time_str):
        """
        解析时间字符串

        参数:
            time_str: 时间字符串（格式：HH:MM）

        返回:
            tuple: (hour, minute)
        """
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return hour, minute

    def _do_sign_in(self):
        """执行签到打卡"""
        self.logger.info("触发签到任务...")
        self._execute_daka("签到")

    def _do_sign_out(self):
        """执行签退打卡"""
        self.logger.info("触发签退任务...")
        self._execute_daka("签退")

    def _execute_daka(self, action_type):
        """
        执行打卡操作

        参数:
            action_type: 打卡类型（"签到" 或 "签退")
        """
        try:
            # 启动浏览器
            if not self.browser.start():
                self.logger.error(f"启动浏览器失败，{action_type}打卡无法执行")
                return

            # 执行打卡
            success = self.form_operator.do_daka(action_type)

            # 关闭浏览器
            self.browser.stop()

            if success:
                self.logger.info(f"{action_type}打卡完成")
            else:
                self.logger.error(f"{action_type}打卡失败")

            # 输出下次执行时间（确认任务会继续执行）
            next_times = self.get_next_run_times()
            if next_times:
                self.logger.info("下次执行时间:")
                for name, time_str in next_times.items():
                    self.logger.info(f"  - {name}: {time_str}")

        except Exception as e:
            self.logger.error(f"{action_type}打卡过程中发生异常: {str(e)}")
            self.browser.stop()

    def run_once(self, action_type):
        """
        手动执行一次打卡

        参数:
            action_type: 打卡类型（"签到" 或 "签退"）

        返回:
            bool: 是否成功
        """
        self.logger.info(f"手动执行{action_type}打卡...")
        self._execute_daka(action_type)

    def get_next_run_times(self):
        """
        获取下次执行时间

        返回:
            dict: 各任务的下次执行时间
        """
        if not self.scheduler:
            return {}

        next_times = {}
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            if next_run:
                next_times[job.name] = next_run.strftime('%Y-%m-%d %H:%M:%S')

        return next_times

    def is_running(self):
        """检查调度器是否运行"""
        return self.running and self.scheduler is not None


class SimpleScheduler:
    """
    简单的定时调度器（不使用APScheduler）
    使用简单的循环检查方式
    """

    def __init__(self, config, browser_manager, form_operator, logger):
        self.config = config
        self.browser = browser_manager
        self.form_operator = form_operator
        self.logger = logger

        self.running = False
        self.thread = None

    def start(self):
        """启动定时任务"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self.thread.start()

        self.logger.info("简单定时调度器已启动")

    def stop(self):
        """停止定时任务"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("简单定时调度器已停止")

    def _schedule_loop(self):
        """调度循环"""
        sign_in_time = self.config.sign_in_time
        sign_out_time = self.config.sign_out_time

        self.logger.info(f"签到时间: {sign_in_time}")
        self.logger.info(f"签退时间: {sign_out_time}")

        while self.running:
            now = datetime.now()
            current_time = now.strftime('%H:%M')

            # 检查是否到达签到时间
            if current_time == sign_in_time:
                self.logger.info("到达签到时间")
                self._execute_daka("签到")
                # 等待一分钟，避免重复执行
                time.sleep(60)

            # 检查是否到达签退时间
            if current_time == sign_out_time:
                self.logger.info("到达签退时间")
                self._execute_daka("签退")
                time.sleep(60)

            # 每秒检查一次
            time.sleep(1)

    def _execute_daka(self, action_type):
        """执行打卡"""
        try:
            if not self.browser.start():
                self.logger.error(f"启动浏览器失败")
                return

            success = self.form_operator.do_daka(action_type)
            self.browser.stop()

            if success:
                self.logger.info(f"{action_type}打卡完成")
            else:
                self.logger.error(f"{action_type}打卡失败")

        except Exception as e:
            self.logger.error(f"{action_type}打卡异常: {str(e)}")
            self.browser.stop()

    def run_once(self, action_type):
        """手动执行一次"""
        self._execute_daka(action_type)

    def is_running(self):
        return self.running