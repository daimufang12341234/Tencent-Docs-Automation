# 日志记录模块
# 作者：dmf
# 时间：2026/4/16
"""
打卡自动化工具日志记录
"""

import os
import sys
import logging
from datetime import datetime


def setup_logger(log_dir=None, log_level='INFO', name='DakaTool'):
    """
    设置日志记录器

    参数:
        log_dir: 日志保存目录
        log_level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        name: 日志器名称

    返回:
        logging.Logger 实例
    """
    # 获取日志目录
    if log_dir is None:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(base_dir, 'logs')

    # 创建日志目录
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建日志器
    logger = logging.getLogger(name)

    # 清除已有的处理器
    logger.handlers.clear()

    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器 - 按日期命名
    log_file = os.path.join(log_dir, f'daka_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 单次打卡详细日志文件
    detail_log_file = os.path.join(log_dir, f'daka_detail_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

    return logger


class DakaLogger:
    """打卡日志记录器，提供更详细的打卡结果记录"""

    def __init__(self, log_dir=None):
        """
        初始化打卡日志记录器

        参数:
            log_dir: 日志保存目录
        """
        if log_dir is None:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, 'logs')

        self.log_dir = log_dir

        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 创建标准日志器
        self.logger = setup_logger(log_dir)

    def log_start(self, action_type):
        """记录打卡开始"""
        self.logger.info(f"========== 开始{action_type}打卡 ==========")

    def log_step(self, step_name, success=True, detail=''):
        """记录打卡步骤"""
        status = "成功" if success else "失败"
        msg = f"[{step_name}] {status}"
        if detail:
            msg += f" - {detail}"
        if success:
            self.logger.info(msg)
        else:
            self.logger.warning(msg)

    def log_error(self, error_msg, exception=None):
        """记录错误"""
        self.logger.error(error_msg)
        if exception:
            self.logger.error(f"异常详情: {str(exception)}")

    def log_success(self, action_type, display_name, time_slot):
        """记录打卡成功"""
        self.logger.info(f"✓ {action_type}打卡成功！用户: {display_name}, 时间段: {time_slot}")
        # 写入成功记录文件
        self._write_success_record(action_type, display_name, time_slot)

    def log_fail(self, action_type, reason):
        """记录打卡失败"""
        self.logger.error(f"✗ {action_type}打卡失败！原因: {reason}")
        # 写入失败记录文件
        self._write_fail_record(action_type, reason)

    def _write_success_record(self, action_type, display_name, time_slot):
        """写入成功记录"""
        record_file = os.path.join(self.log_dir, 'daka_records.txt')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(record_file, 'a', encoding='utf-8') as f:
            f.write(f"[SUCCESS] {timestamp} | {action_type} | {display_name} | {time_slot}\n")

    def _write_fail_record(self, action_type, reason):
        """写入失败记录"""
        record_file = os.path.join(self.log_dir, 'daka_records.txt')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(record_file, 'a', encoding='utf-8') as f:
            f.write(f"[FAIL] {timestamp} | {action_type} | 原因: {reason}\n")

    def info(self, msg):
        """记录信息级别日志"""
        self.logger.info(msg)

    def warning(self, msg):
        """记录警告级别日志"""
        self.logger.warning(msg)

    def error(self, msg):
        """记录错误级别日志"""
        self.logger.error(msg)

    def debug(self, msg):
        """记录调试级别日志"""
        self.logger.debug(msg)