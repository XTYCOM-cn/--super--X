#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
浮动文字桌宠增强版 - 主程序 (集成2.0超级词库)
高级交互版：添加音量式存在感控制、消息数量控制和弹窗位置记忆功能
包含所有功能：文本风格切换、存在感调节、位置吸附、鼠标跟随、右键菜单等
已集成2.0超级增强版词库，提供更丰富的文本内容
"""

import sys
import os
import random
import time
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu, 
                            QAction, QWidget, QVBoxLayout, QLabel, QDesktopWidget,
                            QSlider, QDialog, QHBoxLayout, QPushButton, QGroupBox,
                            QFormLayout, QComboBox, QCheckBox, QWidgetAction)
from PyQt5.QtCore import (Qt, QTimer, QPoint, QRect, QSize, QPropertyAnimation, 
                         QEasingCurve, QRectF, pyqtSignal, QObject)
from PyQt5.QtGui import (QIcon, QFont, QColor, QPainter, QPainterPath, 
                        QPixmap, QPen, QBrush, QLinearGradient, QCursor)

# 导入2.0词库适配器
try:
    from text_styles import TextStyles
except ImportError:
    # 如果找不到适配器，尝试导入原始版本
    try:
        from text_styles_adapter import TextStyles
    except ImportError:
        # 如果都找不到，创建一个简单的内部类
        class TextStyles:
            def __init__(self):
                self.current_style = "funny"
                self.current_tone = "normal"
                
            def get_text(self, category="general"):
                return "我是一个浮动文字桌宠"
                
            def set_style(self, style):
                self.current_style = style
                return True
                
            def set_tone(self, tone):
                self.current_tone = tone
                return True
                
            def get_random_texts(self, count=1, category="general"):
                return ["我是一个浮动文字桌宠"] * count

# 设置日志
logging.basicConfig(
    filename='error_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 全局变量
CATEGORIES = ["general", "coding", "browsing", "video", "office", 
             "gaming", "system", "chat", "music", "reading"]

STYLES = {
    "funny": "搞笑",
    "provocative": "挑衅",
    "self_mockery": "自嘲",
    "clever": "机灵"
}

TONES = {
    "normal": "普通",
    "sarcastic": "吐槽",
    "encouraging": "鼓励",
    "reminder": "提醒",
    "questioning": "疑问",
    "whispering": "悄悄话"
}

# 设置管理器
class SettingsManager(QObject):
    settingsChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.presence_value = 70       # 默认70%存在感（0-100）
        self.message_count = 2         # 默认每次显示2条消息
        self.edge_adsorption = True    # 默认启用边缘吸附
        self.mouse_following = False   # 默认不启用鼠标跟随
        self.autostart = False         # 默认不自动启动
        self.text_style = "funny"      # 默认搞笑风格
        self.tone = "normal"           # 默认普通语气
        self.fixed_position = False    # 默认不使用固定位置
        self.position = QPoint(100, 100)  # 默认固定位置
        
    def set_presence_value(self, value):
        """设置存在感值（0-100）"""
        if 0 <= value <= 100:
            self.presence_value = value
            self.settingsChanged.emit()
            return True
        return False
        
    def set_message_count(self, count):
        """设置每次显示的消息数量（1-5）"""
        if 1 <= count <= 5:
            self.message_count = count
            self.settingsChanged.emit()
            return True
        return False
        
    def set_edge_adsorption(self, enabled):
        self.edge_adsorption = enabled
        self.settingsChanged.emit()
        
    def set_mouse_following(self, enabled):
        self.mouse_following = enabled
        self.settingsChanged.emit()
        
    def set_autostart(self, enabled):
        self.autostart = enabled
        self.settingsChanged.emit()
        
    def set_text_style(self, style):
        if style in STYLES:
            self.text_style = style
            self.settingsChanged.emit()
            return True
        return False
        
    def set_tone(self, tone):
        if tone in TONES:
            self.tone = tone
            self.settingsChanged.emit()
            return True
        return False
        
    def set_fixed_position(self, enabled):
        """设置是否使用固定位置"""
        self.fixed_position = enabled
        self.settingsChanged.emit()
        
    def set_position(self, position):
        """设置固定位置"""
        self.position = position
        self.settingsChanged.emit()
        
    def get_interval(self):
        """根据存在感值计算显示间隔（秒）"""
        # 存在感值越高，间隔越短
        # 0% -> 120秒, 50% -> 30秒, 100% -> 5秒
        max_interval = 120
        min_interval = 5
        interval = max_interval - (self.presence_value / 100) * (max_interval - min_interval)
        
        # 添加一些随机性
        variation = interval * 0.2  # 20%的变化范围
        return random.uniform(interval - variation, interval + variation)
        
    def get_message_count(self):
        """获取每次显示的消息数量"""
        return self.message_count

# 浮动窗口类
class FloatingTextWindow(QWidget):
    rightClicked = pyqtSignal(QPoint)
    positionChanged = pyqtSignal(QPoint)
    
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text = text
        self.dragging = False
        self.drag_position = None
        self.init_ui()
        self.setup_animation()
        
    def init_ui(self):
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 创建标签显示文本
        self.label = QLabel(self.text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        
        # 设置字体
        font = QFont("微软雅黑", 12)
        font.setBold(True)
        self.label.setFont(font)
        
        # 设置布局
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # 设置大小
        self.adjustSize()
        self.setMinimumWidth(200)
        self.setMinimumHeight(80)
        
        # 随机背景样式
        self.bg_style = random.randint(0, 3)
        self.bg_color = random.choice([
            QColor(255, 200, 200, 220),  # 粉红
            QColor(200, 255, 200, 220),  # 淡绿
            QColor(200, 200, 255, 220),  # 淡蓝
            QColor(255, 255, 200, 220),  # 淡黄
            QColor(255, 200, 255, 220),  # 淡紫
            QColor(200, 255, 255, 220)   # 淡青
        ])
        
        # 设置显示时间 (3-6秒)
        self.display_time = random.randint(3000, 6000)
        
    def setup_animation(self):
        # 创建淡入动画
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(300)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 创建淡出动画
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out.finished.connect(self.close)
        
    def set_text(self, text):
        self.text = text
        self.label.setText(text)
        self.adjustSize()
        
    def set_random_position(self, edge_adsorption=True):
        """设置随机位置，可选是否启用边缘吸附"""
        screen = QDesktopWidget().availableGeometry()
        
        # 计算可用区域
        max_x = screen.width() - self.width()
        max_y = screen.height() - self.height()
        
        # 生成随机位置
        x = random.randint(0, max_x)
        y = random.randint(0, max_y)
        
        # 如果启用边缘吸附，有30%概率吸附到屏幕边缘
        if edge_adsorption and random.random() < 0.3:
            edge = random.choice(["left", "right", "top", "bottom"])
            if edge == "left":
                x = 0
            elif edge == "right":
                x = max_x
            elif edge == "top":
                y = 0
            elif edge == "bottom":
                y = max_y
                
        self.move(x, y)
        
    def set_fixed_position(self, position):
        """设置固定位置"""
        self.move(position)
        
    def follow_mouse(self, offset=30):
        """跟随鼠标位置，保持一定距离"""
        cursor_pos = QCursor.pos()
        
        # 随机选择方向 (上下左右)
        direction = random.choice(["up", "down", "left", "right"])
        
        if direction == "up":
            self.move(cursor_pos.x() - self.width() // 2, cursor_pos.y() - self.height() - offset)
        elif direction == "down":
            self.move(cursor_pos.x() - self.width() // 2, cursor_pos.y() + offset)
        elif direction == "left":
            self.move(cursor_pos.x() - self.width() - offset, cursor_pos.y() - self.height() // 2)
        elif direction == "right":
            self.move(cursor_pos.x() + offset, cursor_pos.y() - self.height() // 2)
            
    def show_with_animation(self):
        """带动画效果显示窗口"""
        self.show()
        self.fade_in.start()
        
        # 设置定时器在显示一段时间后关闭
        QTimer.singleShot(self.display_time, self.start_fade_out)
        
    def start_fade_out(self):
        """开始淡出动画"""
        self.fade_out.start()
        
    def paintEvent(self, event):
        """自定义绘制背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建圆角矩形路径
        path = QPainterPath()
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        
        try:
            # 使用QRectF避免类型错误
            path.addRoundedRect(rect, 15, 15)
            
            # 根据不同样式绘制背景
            if self.bg_style == 0:
                # 纯色背景
                painter.fillPath(path, self.bg_color)
                
            elif self.bg_style == 1:
                # 渐变背景
                gradient = QLinearGradient(0, 0, self.width(), self.height())
                gradient.setColorAt(0, self.bg_color)
                gradient.setColorAt(1, self.bg_color.lighter(130))
                painter.fillPath(path, gradient)
                
            elif self.bg_style == 2:
                # 带边框的背景
                painter.fillPath(path, self.bg_color)
                pen = QPen(self.bg_color.darker(120), 2)
                painter.setPen(pen)
                painter.drawPath(path)
                
            else:
                # 双色背景
                painter.fillPath(path, self.bg_color)
                
                # 绘制顶部装饰条
                top_rect = QRectF(rect.x(), rect.y(), rect.width(), 20)
                top_path = QPainterPath()
                top_path.addRoundedRect(top_rect, 15, 15)
                
                # 创建一个与顶部矩形相交的路径
                intersect_path = QPainterPath()
                intersect_path.addRect(QRectF(rect.x(), rect.y() + 10, rect.width(), 10))
                top_path = top_path.united(intersect_path)
                
                painter.fillPath(top_path, self.bg_color.darker(120))
                
        except Exception as e:
            logging.error(f"绘制错误: {e}")
            
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            self.rightClicked.emit(event.globalPos())
            event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.dragging:
            new_position = event.globalPos() - self.drag_position
            self.move(new_position)
            self.positionChanged.emit(new_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

# 设置对话框
class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("浮动文字桌宠设置")
        self.setMinimumWidth(400)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 存在感设置组
        presence_group = QGroupBox("存在感设置")
        presence_layout = QVBoxLayout()
        
        # 存在感滑块
        presence_slider_layout = QHBoxLayout()
        presence_slider_layout.addWidget(QLabel("低"))
        
        self.presence_slider = QSlider(Qt.Horizontal)
        self.presence_slider.setMinimum(0)
        self.presence_slider.setMaximum(100)
        self.presence_slider.setValue(self.settings_manager.presence_value)
        self.presence_slider.setTickPosition(QSlider.TicksBelow)
        self.presence_slider.setTickInterval(10)
        presence_slider_layout.addWidget(self.presence_slider)
        
        presence_slider_layout.addWidget(QLabel("高"))
        presence_layout.addLayout(presence_slider_layout)
        
        # 显示当前值
        self.presence_value_label = QLabel(f"当前值: {self.settings_manager.presence_value}%")
        presence_layout.addWidget(self.presence_value_label)
        
        # 消息数量滑块
        message_count_layout = QHBoxLayout()
        message_count_layout.addWidget(QLabel("每次显示消息数量:"))
        
        self.message_count_slider = QSlider(Qt.Horizontal)
        self.message_count_slider.setMinimum(1)
        self.message_count_slider.setMaximum(5)
        self.message_count_slider.setValue(self.settings_manager.message_count)
        self.message_count_slider.setTickPosition(QSlider.TicksBelow)
        self.message_count_slider.setTickInterval(1)
        message_count_layout.addWidget(self.message_count_slider)
        
        # 显示当前值
        self.message_count_label = QLabel(f"当前值: {self.settings_manager.message_count}条")
        message_count_layout.addWidget(self.message_count_label)
        
        presence_layout.addLayout(message_count_layout)
        presence_group.setLayout(presence_layout)
        main_layout.addWidget(presence_group)
        
        # 位置设置组
        position_group = QGroupBox("位置设置")
        position_layout = QVBoxLayout()
        
        # 边缘吸附
        self.edge_adsorption_checkbox = QCheckBox("启用边缘吸附")
        self.edge_adsorption_checkbox.setChecked(self.settings_manager.edge_adsorption)
        position_layout.addWidget(self.edge_adsorption_checkbox)
        
        # 鼠标跟随
        self.mouse_following_checkbox = QCheckBox("启用鼠标跟随")
        self.mouse_following_checkbox.setChecked(self.settings_manager.mouse_following)
        position_layout.addWidget(self.mouse_following_checkbox)
        
        # 固定位置
        self.fixed_position_checkbox = QCheckBox("使用固定位置")
        self.fixed_position_checkbox.setChecked(self.settings_manager.fixed_position)
        position_layout.addWidget(self.fixed_position_checkbox)
        
        position_group.setLayout(position_layout)
        main_layout.addWidget(position_group)
        
        # 文本风格设置组
        style_group = QGroupBox("文本风格设置")
        style_layout = QFormLayout()
        
        # 风格选择
        self.style_combo = QComboBox()
        for style, display_name in STYLES.items():
            self.style_combo.addItem(display_name, style)
        
        # 设置当前选中项
        for i in range(self.style_combo.count()):
            if self.style_combo.itemData(i) == self.settings_manager.text_style:
                self.style_combo.setCurrentIndex(i)
                break
                
        style_layout.addRow("文本风格:", self.style_combo)
        
        # 语气选择
        self.tone_combo = QComboBox()
        for tone, display_name in TONES.items():
            self.tone_combo.addItem(display_name, tone)
        
        # 设置当前选中项
        for i in range(self.tone_combo.count()):
            if self.tone_combo.itemData(i) == self.settings_manager.tone:
                self.tone_combo.setCurrentIndex(i)
                break
                
        style_layout.addRow("文本语气:", self.tone_combo)
        
        style_group.setLayout(style_layout)
        main_layout.addWidget(style_group)
        
        # 其他设置组
        other_group = QGroupBox("其他设置")
        other_layout = QVBoxLayout()
        
        # 自动启动
        self.autostart_checkbox = QCheckBox("开机自动启动")
        self.autostart_checkbox.setChecked(self.settings_manager.autostart)
        other_layout.addWidget(self.autostart_checkbox)
        
        other_group.setLayout(other_layout)
        main_layout.addWidget(other_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 连接信号
        self.presence_slider.valueChanged.connect(self.update_presence_value_label)
        self.message_count_slider.valueChanged.connect(self.update_message_count_label)
        
    def update_presence_value_label(self, value):
        self.presence_value_label.setText(f"当前值: {value}%")
        
    def update_message_count_label(self, value):
        self.message_count_label.setText(f"当前值: {value}条")
        
    def accept(self):
        # 保存设置
        self.settings_manager.set_presence_value(self.presence_slider.value())
        self.settings_manager.set_message_count(self.message_count_slider.value())
        self.settings_manager.set_edge_adsorption(self.edge_adsorption_checkbox.isChecked())
        self.settings_manager.set_mouse_following(self.mouse_following_checkbox.isChecked())
        self.settings_manager.set_fixed_position(self.fixed_position_checkbox.isChecked())
        self.settings_manager.set_autostart(self.autostart_checkbox.isChecked())
        
        # 设置文本风格
        style_index = self.style_combo.currentIndex()
        if style_index >= 0:
            style = self.style_combo.itemData(style_index)
            self.settings_manager.set_text_style(style)
            
        # 设置文本语气
        tone_index = self.tone_combo.currentIndex()
        if tone_index >= 0:
            tone = self.tone_combo.itemData(tone_index)
            self.settings_manager.set_tone(tone)
            
        super().accept()

# 关于对话框
class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("关于浮动文字桌宠")
        self.setMinimumWidth(400)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("浮动文字桌宠 - 超级增强版")
        title_font = QFont("微软雅黑", 16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 版本
        version_label = QLabel("版本: 2.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(version_label)
        
        # 描述
        description_label = QLabel(
            "浮动文字桌宠是一个可爱的桌面伴侣，它会在你的屏幕上显示各种有趣的文字。\n"
            "超级增强版添加了更丰富的文本内容、更多的场景检测和更强大的交互功能。"
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description_label)
        
        # 功能列表
        features_label = QLabel(
            "主要功能:\n"
            "- 音量式存在感控制\n"
            "- 消息数量精确调节\n"
            "- 弹窗位置记忆功能\n"
            "- 文本风格和语气切换\n"
            "- 边缘吸附和鼠标跟随\n"
            "- 丰富的场景检测和文本内容"
        )
        features_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(features_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def show_about(self):
        """显示关于对话框"""
        # 移动到鼠标位置
        self.move(QCursor.pos())
        self.exec_()

# 主应用类
class FloatingTextApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.text_styles = TextStyles()
        self.windows = []
        self.current_category = "general"
        self.init_ui()
        self.setup_tray_icon()
        self.setup_timers()
        self.detect_activity()
        
    def init_ui(self):
        self.setWindowTitle("浮动文字桌宠")
        self.setGeometry(100, 100, 1, 1)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 应用文本风格和语气
        self.text_styles.set_style(self.settings_manager.text_style)
        self.text_styles.set_tone(self.settings_manager.tone)
        
        # 连接设置变更信号
        self.settings_manager.settingsChanged.connect(self.on_settings_changed)
        
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        # 创建临时XPM图标数据
        xpm_data = [
            "32 32 3 1",
            "  c None",
            ". c #000000",
            "X c #FFFFFF",
            "                                ",
            "                                ",
            "       ................        ",
            "      ..XXXXXXXXXXXXXX..       ",
            "     ..XXXXXXXXXXXXXXXX..      ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "    ..XXXXXXXXXXXXXXXXXX..     ",
            "     ..XXXXXXXXXXXXXXXX..      ",
            "      ..XXXXXXXXXXXXXX..       ",
            "       ................        ",
            "                                ",
            "                                ",
            "                                ",
            "                                ",
            "                                "
        ]
        
        # 创建临时XPM文件
        xpm_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_icon.xpm")
        try:
            with open(xpm_file, "w") as f:
                f.write("/* XPM */\n")
                f.write("static char *icon[] = {\n")
                for line in xpm_data:
                    f.write(f'"{line}",\n')
                f.write("};\n")
                
            # 创建QIcon
            icon = QIcon(xpm_file)
            
            # 如果图标创建失败，尝试使用系统图标
            if icon.isNull():
                icon = QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon)
                
        except Exception as e:
            logging.error(f"创建图标失败: {e}")
            # 使用系统图标作为备选
            icon = QApplication.style().standardIcon(QApplication.style().SP_ComputerIcon)
            
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("浮动文字桌宠")
        
        # 创建托盘菜单
        self.tray_menu = QMenu()
        
        # 存在感子菜单
        self.presence_menu = QMenu("存在感")
        
        # 存在感滑块
        presence_widget = QWidget()
        presence_layout = QHBoxLayout(presence_widget)
        presence_layout.setContentsMargins(5, 5, 5, 5)
        
        presence_layout.addWidget(QLabel("低"))
        
        self.presence_slider = QSlider(Qt.Horizontal)
        self.presence_slider.setMinimum(0)
        self.presence_slider.setMaximum(100)
        self.presence_slider.setValue(self.settings_manager.presence_value)
        self.presence_slider.setFixedWidth(100)
        self.presence_slider.valueChanged.connect(self.on_presence_slider_changed)
        presence_layout.addWidget(self.presence_slider)
        
        presence_layout.addWidget(QLabel("高"))
        
        # 将小部件添加到QWidgetAction
        presence_action = QWidgetAction(self.presence_menu)
        presence_action.setDefaultWidget(presence_widget)
        self.presence_menu.addAction(presence_action)
        
        self.tray_menu.addMenu(self.presence_menu)
        
        # 消息数量子菜单
        self.message_count_menu = QMenu("消息数量")
        
        # 消息数量滑块
        message_count_widget = QWidget()
        message_count_layout = QHBoxLayout(message_count_widget)
        message_count_layout.setContentsMargins(5, 5, 5, 5)
        
        message_count_layout.addWidget(QLabel("1"))
        
        self.message_count_slider = QSlider(Qt.Horizontal)
        self.message_count_slider.setMinimum(1)
        self.message_count_slider.setMaximum(5)
        self.message_count_slider.setValue(self.settings_manager.message_count)
        self.message_count_slider.setFixedWidth(100)
        self.message_count_slider.valueChanged.connect(self.on_message_count_slider_changed)
        message_count_layout.addWidget(self.message_count_slider)
        
        message_count_layout.addWidget(QLabel("5"))
        
        # 将小部件添加到QWidgetAction
        message_count_action = QWidgetAction(self.message_count_menu)
        message_count_action.setDefaultWidget(message_count_widget)
        self.message_count_menu.addAction(message_count_action)
        
        self.tray_menu.addMenu(self.message_count_menu)
        
        # 文本风格子菜单
        self.style_menu = QMenu("文本风格")
        for style, display_name in STYLES.items():
            action = QAction(display_name, self)
            action.setData(style)
            action.triggered.connect(self.on_style_action_triggered)
            action.setCheckable(True)
            action.setChecked(style == self.settings_manager.text_style)
            self.style_menu.addAction(action)
            
        self.tray_menu.addMenu(self.style_menu)
        
        # 文本语气子菜单
        self.tone_menu = QMenu("文本语气")
        for tone, display_name in TONES.items():
            action = QAction(display_name, self)
            action.setData(tone)
            action.triggered.connect(self.on_tone_action_triggered)
            action.setCheckable(True)
            action.setChecked(tone == self.settings_manager.tone)
            self.tone_menu.addAction(action)
            
        self.tray_menu.addMenu(self.tone_menu)
        
        # 位置设置子菜单
        self.position_menu = QMenu("位置设置")
        
        self.edge_adsorption_action = QAction("边缘吸附", self)
        self.edge_adsorption_action.setCheckable(True)
        self.edge_adsorption_action.setChecked(self.settings_manager.edge_adsorption)
        self.edge_adsorption_action.triggered.connect(self.on_edge_adsorption_action_triggered)
        self.position_menu.addAction(self.edge_adsorption_action)
        
        self.mouse_following_action = QAction("鼠标跟随", self)
        self.mouse_following_action.setCheckable(True)
        self.mouse_following_action.setChecked(self.settings_manager.mouse_following)
        self.mouse_following_action.triggered.connect(self.on_mouse_following_action_triggered)
        self.position_menu.addAction(self.mouse_following_action)
        
        self.fixed_position_action = QAction("使用固定位置", self)
        self.fixed_position_action.setCheckable(True)
        self.fixed_position_action.setChecked(self.settings_manager.fixed_position)
        self.fixed_position_action.triggered.connect(self.on_fixed_position_action_triggered)
        self.position_menu.addAction(self.fixed_position_action)
        
        self.reset_position_action = QAction("重置位置", self)
        self.reset_position_action.triggered.connect(self.on_reset_position_action_triggered)
        self.position_menu.addAction(self.reset_position_action)
        
        self.tray_menu.addMenu(self.position_menu)
        
        # 其他菜单项
        self.tray_menu.addSeparator()
        
        self.settings_action = QAction("设置", self)
        self.settings_action.triggered.connect(self.show_settings)
        self.tray_menu.addAction(self.settings_action)
        
        self.about_action = QAction("关于", self)
        self.about_action.triggered.connect(self.show_about)
        self.tray_menu.addAction(self.about_action)
        
        self.tray_menu.addSeparator()
        
        self.exit_action = QAction("退出", self)
        self.exit_action.triggered.connect(self.close)
        self.tray_menu.addAction(self.exit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
        
    def setup_timers(self):
        """设置定时器"""
        # 显示文本的定时器
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.display_random_text)
        
        # 启动定时器
        interval = int(self.settings_manager.get_interval() * 1000)  # 转换为毫秒
        self.display_timer.start(interval)
        
        # 活动检测定时器
        self.activity_timer = QTimer(self)
        self.activity_timer.timeout.connect(self.detect_activity)
        self.activity_timer.start(2000)  # 每2秒检测一次
        
    def on_settings_changed(self):
        """设置变更时的处理"""
        # 更新文本风格和语气
        self.text_styles.set_style(self.settings_manager.text_style)
        self.text_styles.set_tone(self.settings_manager.tone)
        
        # 更新定时器间隔
        interval = int(self.settings_manager.get_interval() * 1000)  # 转换为毫秒
        self.display_timer.setInterval(interval)
        
        # 更新托盘菜单选中状态
        self.update_tray_menu_checked_state()
        
    def update_tray_menu_checked_state(self):
        """更新托盘菜单选中状态"""
        # 更新文本风格菜单
        for action in self.style_menu.actions():
            action.setChecked(action.data() == self.settings_manager.text_style)
            
        # 更新文本语气菜单
        for action in self.tone_menu.actions():
            action.setChecked(action.data() == self.settings_manager.tone)
            
        # 更新位置设置菜单
        self.edge_adsorption_action.setChecked(self.settings_manager.edge_adsorption)
        self.mouse_following_action.setChecked(self.settings_manager.mouse_following)
        self.fixed_position_action.setChecked(self.settings_manager.fixed_position)
        
        # 更新存在感滑块
        self.presence_slider.setValue(self.settings_manager.presence_value)
        
        # 更新消息数量滑块
        self.message_count_slider.setValue(self.settings_manager.message_count)
        
    def on_presence_slider_changed(self, value):
        """存在感滑块值变化时的处理"""
        self.settings_manager.set_presence_value(value)
        
    def on_message_count_slider_changed(self, value):
        """消息数量滑块值变化时的处理"""
        self.settings_manager.set_message_count(value)
        
    def on_style_action_triggered(self):
        """文本风格菜单项触发时的处理"""
        action = self.sender()
        if action:
            style = action.data()
            self.settings_manager.set_text_style(style)
            
    def on_tone_action_triggered(self):
        """文本语气菜单项触发时的处理"""
        action = self.sender()
        if action:
            tone = action.data()
            self.settings_manager.set_tone(tone)
            
    def on_edge_adsorption_action_triggered(self, checked):
        """边缘吸附菜单项触发时的处理"""
        self.settings_manager.set_edge_adsorption(checked)
        
    def on_mouse_following_action_triggered(self, checked):
        """鼠标跟随菜单项触发时的处理"""
        self.settings_manager.set_mouse_following(checked)
        
    def on_fixed_position_action_triggered(self, checked):
        """固定位置菜单项触发时的处理"""
        self.settings_manager.set_fixed_position(checked)
        
    def on_reset_position_action_triggered(self):
        """重置位置菜单项触发时的处理"""
        # 重置为默认位置
        self.settings_manager.set_position(QPoint(100, 100))
        
    def on_tray_icon_activated(self, reason):
        """托盘图标激活时的处理"""
        if reason == QSystemTrayIcon.Trigger:
            # 单击托盘图标时显示一条随机文本
            self.display_random_text()
            
    def detect_activity(self):
        """检测当前活动"""
        try:
            # 获取当前活跃窗口标题
            active_window_title = self.get_active_window_title()
            
            if active_window_title:
                # 根据窗口标题判断活动类别
                category = self.determine_category(active_window_title)
                
                # 如果类别变化，记录新类别
                if category != self.current_category:
                    logging.info(f"当前活动类别: {category}")
                    self.current_category = category
        except Exception as e:
            logging.error(f"活动检测错误: {e}")
            
    def get_active_window_title(self):
        """获取当前活跃窗口标题"""
        try:
            if sys.platform == "win32":
                import win32gui
                window = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(window)
            else:
                # 其他平台可以添加相应的实现
                return "未知窗口"
        except Exception as e:
            logging.error(f"获取窗口标题错误: {e}")
            return "未知窗口"
            
    def determine_category(self, window_title):
        """根据窗口标题判断活动类别"""
        window_title = window_title.lower()
        
        # 编程相关
        if any(keyword in window_title for keyword in ["vscode", "visual studio", "pycharm", "intellij", "eclipse", "sublime", "notepad++", "vim", "emacs", "atom", "code", "编辑器", "editor", "ide"]):
            return "coding"
            
        # 浏览器相关
        if any(keyword in window_title for keyword in ["chrome", "firefox", "edge", "safari", "opera", "浏览器", "browser", "internet explorer", "百度", "google", "bing", "搜索", "search"]):
            return "browsing"
            
        # 视频相关
        if any(keyword in window_title for keyword in ["video", "youtube", "bilibili", "哔哩哔哩", "优酷", "腾讯视频", "爱奇艺", "netflix", "播放器", "player", "movie", "电影", "视频"]):
            return "video"
            
        # 办公相关
        if any(keyword in window_title for keyword in ["word", "excel", "powerpoint", "office", "文档", "表格", "演示", "document", "spreadsheet", "presentation", "wps", "金山", "pdf"]):
            return "office"
            
        # 游戏相关
        if any(keyword in window_title for keyword in ["game", "steam", "epic", "origin", "uplay", "battle.net", "游戏", "lol", "dota", "cs", "minecraft", "我的世界"]):
            return "gaming"
            
        # 系统相关
        if any(keyword in window_title for keyword in ["设置", "控制面板", "任务管理器", "资源管理器", "settings", "control panel", "task manager", "explorer", "system", "系统"]):
            return "system"
            
        # 聊天相关
        if any(keyword in window_title for keyword in ["微信", "qq", "wechat", "telegram", "whatsapp", "discord", "slack", "teams", "聊天", "chat", "消息", "message"]):
            return "chat"
            
        # 音乐相关
        if any(keyword in window_title for keyword in ["music", "spotify", "网易云音乐", "qq音乐", "酷狗", "酷我", "apple music", "itunes", "音乐", "播放器", "player"]):
            return "music"
            
        # 阅读相关
        if any(keyword in window_title for keyword in ["reader", "pdf", "book", "阅读器", "电子书", "kindle", "小说", "novel", "article", "文章"]):
            return "reading"
            
        # 默认类别
        return "general"
        
    def display_random_text(self):
        """显示随机文本"""
        try:
            # 获取消息数量
            count = self.settings_manager.get_message_count()
            
            # 获取随机文本
            texts = self.text_styles.get_random_texts(count, self.current_category)
            
            # 显示文本
            for text in texts:
                window = FloatingTextWindow(text)
                
                # 设置位置
                if self.settings_manager.fixed_position:
                    window.set_fixed_position(self.settings_manager.position)
                elif self.settings_manager.mouse_following:
                    window.follow_mouse()
                else:
                    window.set_random_position(self.settings_manager.edge_adsorption)
                    
                # 连接信号
                window.rightClicked.connect(self.show_context_menu)
                window.positionChanged.connect(self.on_window_position_changed)
                
                # 显示窗口
                window.show_with_animation()
                
                # 保存窗口引用
                self.windows.append(window)
                
            # 清理已关闭的窗口
            self.windows = [w for w in self.windows if w.isVisible()]
            
            # 更新定时器间隔
            interval = int(self.settings_manager.get_interval() * 1000)  # 转换为毫秒
            self.display_timer.setInterval(interval)
            
        except Exception as e:
            logging.error(f"显示文本错误: {e}")
            
    def on_window_position_changed(self, position):
        """窗口位置变化时的处理"""
        # 如果启用了固定位置，保存新位置
        if self.settings_manager.fixed_position:
            self.settings_manager.set_position(position)
            
    def show_context_menu(self, pos):
        """显示右键菜单"""
        self.tray_menu.popup(pos)
        
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.settings_manager)
        if dialog.exec_() == QDialog.Accepted:
            # 设置已在对话框中保存
            pass
            
    def show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog()
        dialog.show_about()
        
    def closeEvent(self, event):
        """关闭事件处理"""
        # 关闭所有窗口
        for window in self.windows:
            window.close()
            
        # 关闭托盘图标
        self.tray_icon.hide()
        
        # 删除临时图标文件
        try:
            xpm_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_icon.xpm")
            if os.path.exists(xpm_file):
                os.remove(xpm_file)
        except:
            pass
            
        event.accept()

# 主函数
def main():
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        
        # 创建并显示应用
        floating_text_app = FloatingTextApp()
        
        # 进入事件循环
        sys.exit(app.exec_())
        
    except Exception as e:
        logging.error(f"程序启动错误: {e}")

if __name__ == "__main__":
    main()
