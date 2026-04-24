# 配置读取模块
# 作者：dmf
# 时间：2026/4/16
"""
使用 ini_config 模块读取配置文件
"""

import os
import sys

# 添加项目根目录到路径，以便导入 ini_config
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from ini_config import IniConfig


class ConfigLoader:
    """配置加载器，使用 ini_config 读取 INI 配置文件"""

    def __init__(self, config_path=None):
        """
        初始化配置加载器

        参数:
            config_path: 配置文件路径，默认为程序目录下的 config.ini
        """
        if config_path is None:
            # 获取程序所在目录
            if getattr(sys, 'frozen', False):
                # 打包后的exe运行
                base_dir = os.path.dirname(sys.executable)
            else:
                # Python脚本运行
                base_dir = _project_root
            config_path = os.path.join(base_dir, 'config.ini')

        self._config_path = config_path
        self._config = None
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self._config_path):
            raise FileNotFoundError(f"配置文件不存在: {self._config_path}")

        # 使用 ini_config 读取配置，支持热重载
        self._config = IniConfig(self._config_path, encoding='utf-8', auto_reload=True)

    def reload(self):
        """重新加载配置"""
        self._config.reload()

    @property
    def document_url(self):
        """腾讯文档表单链接"""
        return self._config.DOCUMENT.url

    @property
    def user_group(self):
        """用户组别"""
        return self._config.USER.group

    @property
    def user_nickname(self):
        """用户昵称"""
        return self._config.USER.nickname

    @property
    def display_name(self):
        """组别+昵称组合"""
        return self._config.USER.display_name

    @property
    def selected_slot(self):
        """选择的值班时间段"""
        return self._config.SCHEDULE.selected_slot

    @property
    def sign_in_time(self):
        """签到执行时间"""
        return self._config.SCHEDULE.sign_in_time

    @property
    def sign_out_time(self):
        """签退执行时间"""
        return self._config.SCHEDULE.sign_out_time

    @property
    def headless(self):
        """是否后台静默运行"""
        value = self._config.BROWSER.headless
        if isinstance(value, str):
            return value.lower() == 'true'
        return bool(value)

    @property
    def user_data_dir(self):
        """登录数据保存目录"""
        # 相对路径转换为绝对路径
        dir_name = self._config.BROWSER.user_data_dir
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = _project_root
        return os.path.join(base_dir, dir_name)

    @property
    def timeout(self):
        """页面加载超时时间"""
        return self._config.BROWSER.get_int('timeout', default=30)

    @property
    def max_attempts(self):
        """最大重试次数"""
        return self._config.RETRY.get_int('max_attempts', default=3)

    @property
    def retry_interval(self):
        """重试间隔"""
        return self._config.RETRY.get_int('retry_interval', default=5)

    @property
    def log_dir(self):
        """日志保存目录"""
        dir_name = self._config.LOG.log_dir
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = _project_root
        return os.path.join(base_dir, dir_name)

    @property
    def log_level(self):
        """日志级别"""
        return self._config.LOG.log_level

    def get_all_config(self):
        """获取所有配置的字典形式"""
        return {
            'document': {
                'url': self.document_url,
            },
            'user': {
                'group': self.user_group,
                'nickname': self.user_nickname,
                'display_name': self.display_name,
            },
            'schedule': {
                'selected_slot': self.selected_slot,
                'sign_in_time': self.sign_in_time,
                'sign_out_time': self.sign_out_time,
            },
            'browser': {
                'headless': self.headless,
                'user_data_dir': self.user_data_dir,
                'timeout': self.timeout,
            },
            'retry': {
                'max_attempts': self.max_attempts,
                'retry_interval': self.retry_interval,
            },
            'log': {
                'log_dir': self.log_dir,
                'log_level': self.log_level,
            },
        }

    def __str__(self):
        """配置信息字符串表示"""
        config_dict = self.get_all_config()
        lines = ["=" * 50, "当前配置信息", "=" * 50]
        for section, values in config_dict.items():
            lines.append(f"\n[{section.upper()}]")
            for key, value in values.items():
                lines.append(f"  {key}: {value}")
        lines.append("=" * 50)
        return "\n".join(lines)