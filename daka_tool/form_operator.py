# 表单操作模块
# 作者：dmf
# 时间：2026/4/16
"""
腾讯文档表单操作自动化，实现打卡流程
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)


class FormOperator:
    """表单操作器，执行腾讯文档打卡流程"""

    # 时间段选项映射
    TIME_SLOTS = ['09-12', '12-15', '15-18', '18-21', '21-24']

    def __init__(self, browser_manager, config, logger):
        """
        初始化表单操作器

        参数:
            browser_manager: 浏览器管理器实例
            config: 配置加载器实例
            logger: 日志记录器实例
        """
        self.browser = browser_manager
        self.config = config
        self.logger = logger

    def do_daka(self, action_type):
        """
        执行打卡流程

        参数:
            action_type: 打卡类型（"签到" 或 "签退")

        返回:
            bool: 是否成功
        """
        self.logger.log_start(action_type)

        max_attempts = self.config.max_attempts
        retry_interval = self.config.retry_interval

        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"第 {attempt}/{max_attempts} 次尝试")

            try:
                # 1. 打开表单
                if not self._open_form():
                    if attempt < max_attempts:
                        self.logger.warning(f"打开表单失败，{retry_interval}秒后重试...")
                        time.sleep(retry_interval)
                        continue
                    else:
                        self.logger.log_fail(action_type, "打开表单失败")
                        return False

                # 2. 点击「再填一份」
                if not self._click_new_form():
                    if attempt < max_attempts:
                        self.logger.warning(f"点击再填一份失败，{retry_interval}秒后重试...")
                        time.sleep(retry_interval)
                        continue
                    else:
                        self.logger.log_fail(action_type, "点击再填一份失败")
                        return False

                # 3. 选择打卡类型
                if not self._select_daka_type(action_type):
                    if attempt < max_attempts:
                        self.logger.warning(f"选择打卡类型失败，{retry_interval}秒后重试...")
                        time.sleep(retry_interval)
                        continue
                    else:
                        self.logger.log_fail(action_type, "选择打卡类型失败")
                        return False

                # 4. 填入组别昵称
                if not self._fill_display_name():
                    if attempt < max_attempts:
                        self.logger.warning(f"填入组别昵称失败，{retry_interval}秒后重试...")
                        time.sleep(retry_interval)
                        continue
                    else:
                        self.logger.log_fail(action_type, "填入组别昵称失败")
                        return False

                # 5. 勾选时间段
                if not self._select_time_slot():
                    if attempt < max_attempts:
                        self.logger.warning(f"勾选时间段失败，{retry_interval}秒后重试...")
                        time.sleep(retry_interval)
                        continue
                    else:
                        self.logger.log_fail(action_type, "勾选时间段失败")
                        return False

                # 6. 点击提交
                if not self._click_submit():
                    if attempt < max_attempts:
                        self.logger.warning(f"点击提交失败，{retry_interval}秒后重试...")
                        time.sleep(retry_interval)
                        continue
                    else:
                        self.logger.log_fail(action_type, "点击提交失败")
                        return False

                # 7. 处理提交后弹窗
                if not self._handle_popup():
                    # 弹窗处理失败不影响打卡成功，只是记录
                    self.logger.warning("处理提交弹窗失败，但打卡可能已成功")

                # 打卡成功
                self.logger.log_success(action_type, self.config.display_name, self.config.selected_slot)
                return True

            except Exception as e:
                self.logger.log_error(f"打卡过程中发生异常: {str(e)}", e)
                if attempt < max_attempts:
                    self.logger.warning(f"{retry_interval}秒后重试...")
                    time.sleep(retry_interval)
                    # 重试前重新启动浏览器
                    self.browser.stop()
                    time.sleep(2)
                    self.browser.start()
                else:
                    self.logger.log_fail(action_type, f"异常: {str(e)}")
                    return False

        return False

    def _open_form(self):
        """打开腾讯文档表单"""
        self.logger.log_step("打开表单", False, "开始...")

        url = self.config.document_url
        if not url:
            self.logger.log_step("打开表单", False, "配置文件中没有表单URL")
            return False

        # 访问表单URL
        if not self.browser.visit_url(url):
            self.logger.log_step("打开表单", False, "页面加载失败")
            return False

        # 等待页面加载完成
        time.sleep(3)

        # 检查是否需要登录
        if not self.browser.check_login_status():
            self.logger.log_step("打开表单", False, "需要登录")
            return False

        self.logger.log_step("打开表单", True, url)
        return True

    def _click_new_form(self):
        """点击「再填一份」按钮"""
        self.logger.log_step("点击再填一份", False, "开始查找按钮...")

        # 多策略定位「再填一份」按钮
        locators = [
            # 腾讯文档实际按钮结构
            (By.CSS_SELECTOR, ".dui-m-actionbar-item-text"),
            (By.XPATH, "//div[contains(@class, 'dui-m-actionbar-item-text')]"),
            (By.XPATH, "//div[contains(@class, 'dui-m-actionbar-item') and contains(text(), '再填一份')]"),
            # 通用定位策略
            (By.XPATH, "//div[contains(text(), '再填一份')]"),
            (By.XPATH, "//*[contains(text(), '再填一份')]"),
            (By.XPATH, "//button[contains(text(), '再填一份')]"),
            (By.XPATH, "//span[contains(text(), '再填一份')]"),
            (By.XPATH, "//a[contains(text(), '再填一份')]"),
        ]

        for locator in locators:
            try:
                elements = self.browser.find_elements(locator)
                for element in elements:
                    text = element.text if element.text else ""
                    if "再填一份" in text:
                        # 使用JavaScript点击，更稳定
                        self.browser.execute_script("arguments[0].click();", element)
                        self.logger.log_step("点击再填一份", True, f"定位策略: {locator}, 元素文本: {text}")
                        time.sleep(2)  # 等待页面跳转
                        return True
            except (TimeoutException, NoSuchElementException):
                continue

        # 尝试通过JavaScript查找并点击
        js_click = """
        // 精确匹配 dui-m-actionbar-item-text
        var btn = document.querySelector('.dui-m-actionbar-item-text');
        if (btn && btn.textContent.includes('再填一份')) {
            btn.click();
            return 'found by class: ' + btn.className;
        }

        // 查找包含"再填一份"的所有div
        var divs = document.querySelectorAll('div');
        for (var div of divs) {
            if ((div.textContent || div.innerText || '').includes('再填一份')) {
                div.click();
                return 'found by text: ' + div.className;
            }
        }

        return null;
        """
        result = self.browser.execute_script(js_click)
        if result:
            self.logger.log_step("点击再填一份", True, f"通过JavaScript点击成功: {result}")
            time.sleep(2)
            return True

        self.logger.log_step("点击再填一份", False, "未找到按钮")
        return False

    def _select_daka_type(self, action_type):
        """选择打卡类型（签到/签退）"""
        self.logger.log_step("选择打卡类型", False, f"类型: {action_type}")

        # 等待表单页面加载
        time.sleep(2)

        # 腾讯文档使用 React 等框架，需要触发完整事件链
        js_select = """
        var radioOptions = document.querySelectorAll('.form-choice-radio-option[role="radio"]');
        for (var option of radioOptions) {
            var textEl = option.querySelector('.form-choice-option-text-content');
            if (textEl && textEl.textContent.trim() === '%s') {
                // 先聚焦
                option.focus();

                // 触发完整的 React 事件链
                // 1. mousedown
                option.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window, button: 0}));

                // 2. mouseup
                option.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window, button: 0}));

                // 3. click
                option.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window, button: 0}));

                // 4. 触发 input 和 change 事件（React 需要）
                option.dispatchEvent(new Event('input', {bubbles: true}));
                option.dispatchEvent(new Event('change', {bubbles: true}));

                // 5. 触发 keydown/keyup 模拟键盘选择
                option.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, key: 'Enter', code: 'Enter'}));
                option.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, key: 'Enter', code: 'Enter'}));

                // 6. 设置 aria-checked 属性（手动确保状态）
                option.setAttribute('aria-checked', 'true');

                // 7. 模拟指针事件
                option.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, cancelable: true, pointerType: 'mouse'}));
                option.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, cancelable: true, pointerType: 'mouse'}));

                return 'clicked with full events';
            }
        }
        return null;
        """ % action_type

        result = self.browser.execute_script(js_select)
        if result:
            self.logger.info(f"选择打卡类型: {result}")
            time.sleep(1)

        # 验证是否成功（检查是否还有错误提示）
        js_verify = """
        var questions = document.querySelectorAll('.question');
        for (var q of questions) {
            var titleEl = q.querySelector('.question-title span');
            if (titleEl && titleEl.textContent.includes('值班打卡选项')) {
                var content = q.querySelector('.question-content');
                // 检查是否有 error class
                var hasError = content && content.classList.contains('error');
                // 检查选中状态
                var radioOptions = q.querySelectorAll('.form-choice-radio-option[role="radio"]');
                var selected = false;
                var selectedText = '';
                for (var option of radioOptions) {
                    if (option.getAttribute('aria-checked') === 'true') {
                        selected = true;
                        var textEl = option.querySelector('.form-choice-option-text-content');
                        selectedText = textEl ? textEl.textContent : '';
                    }
                }
                return {selected: selected, selectedText: selectedText, hasError: hasError};
            }
        }
        return null;
        """

        verify_result = self.browser.execute_script(js_verify)
        if verify_result:
            self.logger.info(f"验证结果: {verify_result}")
            if verify_result.get('selected') and verify_result.get('selectedText') == action_type and not verify_result.get('hasError'):
                self.logger.log_step("选择打卡类型", True, f"已选中且无错误: {action_type}")
                return True
            elif verify_result.get('selected') and verify_result.get('selectedText') == action_type:
                self.logger.warning("选中但仍有错误提示，可能需要额外操作")
                # 尝试点击其他选项再点击回来
                self.browser.execute_script("""
                var radioOptions = document.querySelectorAll('.form-choice-radio-option[role="radio"]');
                // 先点击一个其他选项
                for (var option of radioOptions) {
                    var textEl = option.querySelector('.form-choice-option-text-content');
                    if (textEl && textEl.textContent.trim() !== '%s') {
                        option.click();
                        break;
                    }
                }
                """ % action_type)
                time.sleep(0.5)
                # 再点击目标选项
                self.browser.execute_script(js_select)
                time.sleep(1)

        self.logger.log_step("选择打卡类型", True, f"完成: {action_type}")
        return True

    def _fill_display_name(self):
        """填入组别+昵称"""
        self.logger.log_step("填入组别昵称", False, f"内容: {self.config.display_name}")

        display_name = self.config.display_name

        # 腾讯文档使用 React 等框架，需要触发完整事件链
        js_fill = """
        // 查找所有 textarea
        var textareas = document.querySelectorAll('textarea');
        for (var ta of textareas) {
            // 获取焦点
            ta.focus();

            // 清空原有内容
            ta.value = '';

            // 触发各种事件
            ta.dispatchEvent(new Event('input', {bubbles: true}));
            ta.dispatchEvent(new Event('change', {bubbles: true}));

            // 使用原生 setter 设置值（React 会拦截）
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            nativeInputValueSetter.call(ta, '%s');

            // 触发 React 事件
            ta.dispatchEvent(new Event('input', {bubbles: true}));
            ta.dispatchEvent(new Event('change', {bubbles: true}));

            // 模拟键盘输入
            ta.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, key: 'a'}));
            ta.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, key: 'a'}));

            // 触发 blur 事件让 React 处理
            ta.blur();
            ta.focus();

            return 'filled textarea with native setter, value=' + ta.value;
        }
        return null;
        """ % display_name

        result = self.browser.execute_script(js_fill)
        if result:
            self.logger.info(f"填入组别昵称: {result}")
            time.sleep(1)

        # 验证是否成功（检查是否有错误提示）
        js_verify = """
        var questions = document.querySelectorAll('.question');
        for (var q of questions) {
            var titleEl = q.querySelector('.question-title span');
            if (titleEl && titleEl.textContent.includes('组别')) {
                var content = q.querySelector('.question-content');
                var hasError = content && content.classList.contains('error');
                var ta = q.querySelector('textarea');
                var value = ta ? ta.value : '';
                return {value: value, hasError: hasError};
            }
        }
        return null;
        """

        verify_result = self.browser.execute_script(js_verify)
        if verify_result:
            self.logger.info(f"组别昵称验证结果: {verify_result}")
            if verify_result.get('value') == display_name and not verify_result.get('hasError'):
                self.logger.log_step("填入组别昵称", True, f"已填入且无错误: {display_name}")
                return True
            elif verify_result.get('value') == display_name and verify_result.get('hasError'):
                # 尝试另一种方式：模拟真实输入
                self.logger.warning("填入成功但仍有错误，尝试模拟真实输入")
                js_simulate_input = """
                var ta = document.querySelectorAll('textarea')[0];
                if (ta) {
                    ta.focus();
                    ta.select();

                    // 模拟逐字符输入
                    var text = '%s';
                    ta.value = '';

                    // 触发 focusin
                    ta.dispatchEvent(new FocusEvent('focusin', {bubbles: true}));

                    // 逐字符模拟（简化版）
                    for (var i = 0; i < text.length; i++) {
                        ta.value += text[i];
                        ta.dispatchEvent(new InputEvent('input', {
                            bubbles: true,
                            cancelable: true,
                            inputType: 'insertText',
                            data: text[i]
                        }));
                    }

                    // 触发 blur
                    ta.dispatchEvent(new FocusEvent('focusout', {bubbles: true}));

                    return 'simulated input: ' + ta.value;
                }
                return null;
                """ % display_name

                result2 = self.browser.execute_script(js_simulate_input)
                if result2:
                    self.logger.info(f"模拟输入结果: {result2}")
                    time.sleep(1)

        self.logger.log_step("填入组别昵称", True, f"完成: {display_name}")
        return True

    def _select_time_slot(self):
        """勾选值班时间段"""
        self.logger.log_step("勾选时间段", False, f"时间段: {self.config.selected_slot}")

        time_slot = self.config.selected_slot

        # 腾讯文档使用 React 等框架，需要触发完整事件链
        js_select = """
        var questions = document.querySelectorAll('.question');
        for (var q of questions) {
            var titleEl = q.querySelector('.question-title span');
            if (titleEl && titleEl.textContent.includes('值班时间')) {
                var radioOptions = q.querySelectorAll('.form-choice-radio-option[role="radio"]');
                for (var option of radioOptions) {
                    var textEl = option.querySelector('.form-choice-option-text-content');
                    if (textEl && textEl.textContent.trim() === '%s') {
                        // 触发完整事件链
                        option.focus();
                        option.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window, button: 0}));
                        option.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window, button: 0}));
                        option.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window, button: 0}));
                        option.dispatchEvent(new Event('input', {bubbles: true}));
                        option.dispatchEvent(new Event('change', {bubbles: true}));
                        option.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, key: 'Enter', code: 'Enter'}));
                        option.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, key: 'Enter', code: 'Enter'}));
                        option.setAttribute('aria-checked', 'true');
                        option.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, cancelable: true, pointerType: 'mouse'}));
                        option.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, cancelable: true, pointerType: 'mouse'}));
                        return 'clicked with full events';
                    }
                }
            }
        }
        return null;
        """ % time_slot

        result = self.browser.execute_script(js_select)
        if result:
            self.logger.info(f"选择时间段: {result}")
            time.sleep(1)

        # 验证是否成功
        js_verify = """
        var questions = document.querySelectorAll('.question');
        for (var q of questions) {
            var titleEl = q.querySelector('.question-title span');
            if (titleEl && titleEl.textContent.includes('值班时间')) {
                var content = q.querySelector('.question-content');
                var hasError = content && content.classList.contains('error');
                var radioOptions = q.querySelectorAll('.form-choice-radio-option[role="radio"]');
                var selected = false;
                var selectedText = '';
                for (var option of radioOptions) {
                    if (option.getAttribute('aria-checked') === 'true') {
                        selected = true;
                        var textEl = option.querySelector('.form-choice-option-text-content');
                        selectedText = textEl ? textEl.textContent : '';
                    }
                }
                return {selected: selected, selectedText: selectedText, hasError: hasError};
            }
        }
        return null;
        """

        verify_result = self.browser.execute_script(js_verify)
        if verify_result:
            self.logger.info(f"时间段验证结果: {verify_result}")
            if verify_result.get('selected') and verify_result.get('selectedText') == time_slot and not verify_result.get('hasError'):
                self.logger.log_step("勾选时间段", True, f"已选中且无错误: {time_slot}")
                return True
            elif verify_result.get('selected') and verify_result.get('selectedText') == time_slot:
                # 尝试切换选项再选回来
                self.browser.execute_script("""
                var questions = document.querySelectorAll('.question');
                for (var q of questions) {
                    var titleEl = q.querySelector('.question-title span');
                    if (titleEl && titleEl.textContent.includes('值班时间')) {
                        var radioOptions = q.querySelectorAll('.form-choice-radio-option[role="radio"]');
                        for (var option of radioOptions) {
                            var textEl = option.querySelector('.form-choice-option-text-content');
                            if (textEl && textEl.textContent.trim() !== '%s') {
                                option.click();
                                break;
                            }
                        }
                    }
                }
                """ % time_slot)
                time.sleep(0.5)
                self.browser.execute_script(js_select)
                time.sleep(1)

        self.logger.log_step("勾选时间段", True, f"完成: {time_slot}")
        return True

    def _click_submit(self):
        """点击提交按钮"""
        self.logger.log_step("点击提交", False, "开始查找提交按钮...")

        # 腾讯文档提交按钮结构：<div class="question-commit"><button type="button">提交</button></div>

        # 方法1：找到按钮后模拟完整点击事件
        js_submit = """
        // 精确匹配提交按钮
        var commitDiv = document.querySelector('.question-commit');
        if (commitDiv) {
            var btn = commitDiv.querySelector('button');
            if (btn) {
                // 模拟鼠标事件序列
                var mouseDownEvent = new MouseEvent('mousedown', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                btn.dispatchEvent(mouseDownEvent);

                var mouseUpEvent = new MouseEvent('mouseup', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                btn.dispatchEvent(mouseUpEvent);

                var clickEvent = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                btn.dispatchEvent(clickEvent);

                // 也尝试直接调用 click 方法
                btn.click();

                return 'clicked with events: ' + btn.textContent;
            }
        }
        return null;
        """
        result = self.browser.execute_script(js_submit)
        if result:
            self.logger.log_step("点击提交", True, f"通过JavaScript点击成功: {result}")
            time.sleep(3)  # 等待提交响应
            return True

        # 方法2：直接找到元素并使用 Selenium 点击
        locators = [
            (By.CSS_SELECTOR, ".question-commit button"),
            (By.XPATH, "//div[contains(@class, 'question-commit')]//button"),
        ]

        for locator in locators:
            try:
                elements = self.browser.find_elements(locator)
                for element in elements:
                    text = element.text or ""
                    if "提交" in text:
                        # 先滚动到元素
                        self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)

                        # 尝试多种点击方式
                        try:
                            # 方式1：直接点击
                            element.click()
                            self.logger.log_step("点击提交", True, f"直接点击成功")
                            time.sleep(3)
                            return True
                        except:
                            # 方式2：JavaScript点击
                            self.browser.execute_script("arguments[0].click();", element)
                            self.logger.log_step("点击提交", True, f"JS点击成功")
                            time.sleep(3)
                            return True
            except (TimeoutException, NoSuchElementException):
                continue

        self.logger.log_step("点击提交", False, "未找到提交按钮")
        return False

    def _handle_popup(self):
        """处理提交后的弹窗"""
        self.logger.log_step("处理弹窗", False, "开始检查弹窗...")

        time.sleep(1)  # 等待弹窗出现

        # 第一个弹窗：确认提交弹窗 - 点击"确认"
        js_confirm = """
        // 确认弹窗
        var confirmBtn = document.querySelector('.dui-modal-footer-ok');
        if (confirmBtn) {
            confirmBtn.click();
            return 'clicked confirm button';
        }
        // 查找包含"确认"的按钮
        var buttons = document.querySelectorAll('.dui-modal-footer button');
        for (var btn of buttons) {
            var text = btn.textContent || btn.innerText || '';
            if (text.includes('确认')) {
                btn.click();
                return 'clicked: ' + text;
            }
        }
        return null;
        """
        result = self.browser.execute_script(js_confirm)
        if result:
            self.logger.info(f"点击确认弹窗: {result}")
            time.sleep(2)  # 等待提交完成

        # 第二个弹窗：提交成功弹窗 - 显示"已提交"
        # 检查是否出现成功提示
        js_check_success = """
        var successEl = document.querySelector('.form-submit-result-success-title');
        if (successEl && successEl.textContent.includes('已提交')) {
            return '提交成功';
        }
        return null;
        """
        result = self.browser.execute_script(js_check_success)
        if result:
            self.logger.log_step("处理弹窗", True, "提交成功！显示'已提交'")
            # 不需要点击任何按钮，打卡已完成
            return True

        # 检查是否还有其他弹窗需要关闭
        js_close_modal = """
        // 关闭可能存在的弹窗
        var closeBtn = document.querySelector('.dui-modal-close');
        if (closeBtn) {
            closeBtn.click();
            return 'closed modal';
        }
        return null;
        """
        result = self.browser.execute_script(js_close_modal)
        if result:
            self.logger.info(f"关闭弹窗: {result}")

        self.logger.log_step("处理弹窗", True, "弹窗处理完成")
        return True

    def do_first_login(self):
        """
        执行首次登录流程（可视化模式）

        返回:
            bool: 是否成功
        """
        self.logger.info("首次登录流程开始...")

        # 使用可视化模式启动浏览器
        if not self.browser.start(force_visible=True):
            self.logger.error("启动浏览器失败")
            return False

        # 打开表单页面
        url = self.config.document_url
        if not self.browser.visit_url(url):
            self.logger.error("打开表单页面失败")
            return False

        self.logger.info("=" * 50)
        self.logger.info("请在浏览器中手动登录QQ账号...")
        self.logger.info("登录成功后，登录状态将自动保存到 chrome_data 目录")
        self.logger.info("完成登录后，请直接关闭浏览器窗口")
        self.logger.info("=" * 50)

        # 等待用户手动关闭浏览器
        import time
        try:
            while True:
                # 检查浏览器是否还在运行
                try:
                    if self.browser.driver:
                        # 尝试获取页面标题，如果成功说明浏览器还在
                        self.browser.driver.title  # 这会抛出异常如果浏览器已关闭
                        time.sleep(1)
                    else:
                        break
                except:
                    # 浏览器被用户手动关闭了
                    self.logger.info("检测到浏览器已关闭")
                    # 清理 driver 引用，避免程序退出时再次尝试关闭
                    self.browser.driver = None
                    break
        except KeyboardInterrupt:
            self.logger.info("用户中断登录流程")
            # 用户按 Ctrl+C，也需要清理
            self.browser.driver = None

        self.logger.info("登录状态已保存，后续打卡将自动使用该登录状态")
        return True