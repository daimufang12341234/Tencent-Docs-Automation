# Selenium浏览器自动化核心引擎
# 作者：dmf
# 时间：2026/4/16
"""
浏览器管理模块，负责Chrome浏览器的初始化和配置
"""

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
)


class BrowserManager:
    """浏览器管理器，负责Chrome的启动、配置和状态管理"""

    def __init__(self, user_data_dir, headless=True, timeout=30, logger=None):
        """
        初始化浏览器管理器

        参数:
            user_data_dir: Chrome用户数据目录（保存登录状态）
            headless: 是否后台静默运行
            timeout: 页面加载超时时间（秒）
            logger: 日志记录器
        """
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.timeout = timeout
        self.logger = logger
        self.driver = None
        self.wait = None

        # 创建用户数据目录
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

    def _cleanup_lock_files(self):
        """清理Chrome锁定文件，防止启动冲突"""
        lock_files = [
            'SingletonLock',
            'SingletonCookie',
            'SingletonSocket',
            'lockfile',
        ]
        for lock_file in lock_files:
            lock_path = os.path.join(self.user_data_dir, lock_file)
            if os.path.exists(lock_path):
                try:
                    os.remove(lock_path)
                    if self.logger:
                        self.logger.debug(f"清理锁定文件: {lock_path}")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"无法清理锁定文件 {lock_path}: {e}")

    def start(self, force_visible=False):
        """
        启动浏览器

        参数:
            force_visible: 强制使用可视化模式（用于首次登录或调试）

        返回:
            bool: 启动是否成功
        """
        # 先清理锁定文件
        self._cleanup_lock_files()

        try:
            # 配置Chrome选项
            options = Options()

            # 设置用户数据目录（保存登录状态）
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

            # 防止Chrome崩溃的关键参数
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--metrics-recording-only")
            options.add_argument("--disable-default-apps")
            options.add_argument("--mute-audio")
            options.add_argument("--hide-scrollbars")
            options.add_argument("--safebrowsing-disable-auto-update")
            options.add_argument("--disable-component-update")

            # 避免检测自动化
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            # 禁用一些不必要的功能
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")

            # 设置窗口大小
            options.add_argument("--window-size=1920,1080")

            # Windows锁屏兼容性参数 - 确保在锁屏状态下也能运行
            options.add_argument("--disable-gpu-compositing")
            options.add_argument("--use-gl=swiftshader")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-3d-apis")

            # 后台运行模式（除非强制可视化）
            if self.headless and not force_visible:
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                # 锁屏状态下必须的参数
                options.add_argument("--in-process-gpu")

            # 关键：设置远程调试端口，解决DevToolsActivePort问题
            import random
            debug_port = random.randint(9222, 9322)
            options.add_argument(f"--remote-debugging-port={debug_port}")

            # 启动浏览器
            if self.logger:
                self.logger.info(f"正在启动Chrome浏览器...")

            try:
                # 尝试使用 webdriver-manager 自动管理驱动
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except ImportError:
                # 如果没有 webdriver_manager，使用系统已安装的 chromedriver
                self.driver = webdriver.Chrome(options=options)
            except Exception as e:
                # 如果失败，尝试不带user-data-dir启动
                if self.logger:
                    self.logger.warning(f"首次启动失败: {str(e)}, 尝试备用方案...")
                options2 = Options()
                options2.add_argument("--no-first-run")
                options2.add_argument("--no-default-browser-check")
                options2.add_argument("--no-sandbox")
                options2.add_argument("--disable-dev-shm-usage")
                options2.add_argument("--window-size=1920,1080")
                if self.headless and not force_visible:
                    options2.add_argument("--headless=new")
                    options2.add_argument("--disable-gpu")
                debug_port2 = random.randint(9332, 9422)
                options2.add_argument(f"--remote-debugging-port={debug_port2}")
                options2.add_argument("--disable-blink-features=AutomationControlled")
                options2.add_experimental_option("excludeSwitches", ["enable-automation"])

                from webdriver_manager.chrome import ChromeDriverManager
                service2 = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service2, options=options2)

            # 设置超时时间
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(5)

            # 创建等待器
            self.wait = WebDriverWait(self.driver, self.timeout)

            # 设置执行脚本超时
            self.driver.set_script_timeout(self.timeout)

            if self.logger:
                self.logger.info("浏览器启动成功")

            return True

        except WebDriverException as e:
            if self.logger:
                self.logger.error(f"浏览器启动失败: {str(e)}")
            return False

    def stop(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                if self.logger:
                    self.logger.info("浏览器已关闭")
            except Exception as e:
                # 浏览器可能已被用户手动关闭，忽略错误
                pass
            finally:
                self.driver = None
                self.wait = None

    def visit_url(self, url):
        """
        访问指定URL

        参数:
            url: 要访问的URL

        返回:
            bool: 是否成功
        """
        if not self.driver:
            if self.logger:
                self.logger.error("浏览器未启动")
            return False

        try:
            if self.logger:
                self.logger.info(f"正在访问: {url}")

            self.driver.get(url)

            # 等待页面加载
            time.sleep(2)  # 给页面一些时间加载

            if self.logger:
                self.logger.info("页面加载完成")

            return True

        except TimeoutException:
            if self.logger:
                self.logger.warning(f"页面加载超时: {url}")
            return False

        except WebDriverException as e:
            if self.logger:
                self.logger.error(f"访问URL失败: {str(e)}")
            return False

    def wait_for_element(self, locator, timeout=None):
        """
        等待元素出现

        参数:
            locator: 元素定位器 (By.XPATH, "xpath表达式") 等
            timeout: 超时时间，默认使用全局timeout

        返回:
            WebElement 或 None
        """
        if not self.driver:
            return None

        timeout = timeout or self.timeout

        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located(locator))
            return element
        except TimeoutException:
            return None

    def wait_for_clickable(self, locator, timeout=None):
        """
        等待元素可点击

        参数:
            locator: 元素定位器
            timeout: 超时时间

        返回:
            WebElement 或 None
        """
        if not self.driver:
            return None

        timeout = timeout or self.timeout

        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable(locator))
            return element
        except TimeoutException:
            return None

    def find_element(self, locator):
        """
        查找元素（不等待）

        参数:
            locator: 元素定位器

        返回:
            WebElement 或 None
        """
        if not self.driver:
            return None

        try:
            return self.driver.find_element(*locator)
        except NoSuchElementException:
            return None

    def find_elements(self, locator):
        """
        查找多个元素

        参数:
            locator: 元素定位器

        返回:
            list of WebElement
        """
        if not self.driver:
            return []

        try:
            return self.driver.find_elements(*locator)
        except NoSuchElementException:
            return []

    def click_element(self, locator, wait_clickable=True):
        """
        点击元素

        参数:
            locator: 元素定位器
            wait_clickable: 是否等待元素可点击

        返回:
            bool: 是否成功
        """
        try:
            if wait_clickable:
                element = self.wait_for_clickable(locator)
            else:
                element = self.find_element(locator)

            if element:
                element.click()
                return True
            return False

        except Exception as e:
            if self.logger:
                self.logger.warning(f"点击元素失败: {str(e)}")
            return False

    def input_text(self, locator, text, clear_first=True):
        """
        输入文本

        参数:
            locator: 元素定位器
            text: 要输入的文本
            clear_first: 是否先清空

        返回:
            bool: 是否成功
        """
        try:
            element = self.wait_for_element(locator)
            if element:
                if clear_first:
                    element.clear()
                element.send_keys(text)
                return True
            return False

        except Exception as e:
            if self.logger:
                self.logger.warning(f"输入文本失败: {str(e)}")
            return False

    def execute_script(self, script, *args):
        """
        执行JavaScript脚本

        参数:
            script: JavaScript脚本
            args: 脚本参数

        返回:
            脚本执行结果
        """
        if not self.driver:
            return None

        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"执行脚本失败: {str(e)}")
            return None

    def get_page_source(self):
        """获取页面源码"""
        if self.driver:
            return self.driver.page_source
        return None

    def get_current_url(self):
        """获取当前URL"""
        if self.driver:
            return self.driver.current_url
        return None

    def get_title(self):
        """获取页面标题"""
        if self.driver:
            return self.driver.title
        return None

    def take_screenshot(self, filepath):
        """
        截取屏幕截图

        参数:
            filepath: 截图保存路径

        返回:
            bool: 是否成功
        """
        if self.driver:
            try:
                self.driver.save_screenshot(filepath)
                return True
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"截图失败: {str(e)}")
                return False
        return False

    def refresh(self):
        """刷新页面"""
        if self.driver:
            self.driver.refresh()

    def check_login_status(self):
        """
        检查登录状态（通过检查页面元素判断）

        返回:
            bool: 是否已登录
        """
        # 检查页面是否显示登录相关元素
        # 如果能看到"登录"按钮或扫码界面，说明未登录
        # 这里需要根据实际页面结构调整

        try:
            # 检查是否存在登录按钮
            login_buttons = self.find_elements(('xpath', "//button[contains(text(), '登录')]"))
            if login_buttons:
                return False

            # 检查是否存在扫码区域
            qr_elements = self.find_elements(('xpath', "//div[contains(@class, 'qr')]"))
            if qr_elements:
                return False

            return True

        except Exception:
            return True  # 默认认为已登录

    def is_running(self):
        """检查浏览器是否正在运行"""
        return self.driver is not None