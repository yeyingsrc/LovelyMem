from PySide6.QtWidgets import QGroupBox, QGridLayout, QPushButton
from PySide6.QtCore import Qt
import sqlite3
import os

class FavoriteButtonGroup(QGroupBox):
    def __init__(self, favorite_manager):
        super().__init__("喜爱功能")
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(5, 5, 5, 5)
        self.layout().setSpacing(5)
        self.buttons = []
        self.favorite_manager = favorite_manager
        
        # 添加数据库版本检查
        self.check_db_version()
        
        self.load_favorites()

    def add_favorite(self, button, source_area):
        # 创建新按钮，并在前面加上来源区域的标签
        new_button_text = f"{source_area}-{button.text()}"
        new_button = QPushButton(new_button_text)
        new_button.clicked.connect(button.click)
        new_button.setContextMenuPolicy(Qt.CustomContextMenu)
        new_button.customContextMenuRequested.connect(lambda pos, btn=new_button: self.show_context_menu(pos, btn))
        
        # 使用收藏槽的特定样式
        new_button.setStyleSheet(self.favorite_button_style())
        
        row = len(self.buttons) // 2
        col = len(self.buttons) % 2
        self.layout().addWidget(new_button, row, col)
        self.buttons.append(new_button)
        self.save_favorite(new_button_text, self.favorite_button_style())

    def show_context_menu(self, pos, button):
        context_menu = self.favorite_manager.create_context_menu(button, is_favorite=True)
        context_menu.exec_(button.mapToGlobal(pos))

    def load_favorites(self):
        conn = sqlite3.connect('db/favorites.db')
        c = conn.cursor()
        
        # 检查表结构
        c.execute("PRAGMA table_info(favorites)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'style' not in columns:
            # 如果style列不存在,添加它
            c.execute("ALTER TABLE favorites ADD COLUMN style TEXT")
            conn.commit()
            print("已添加style列到favorites表")
        
        c.execute("SELECT name, style FROM favorites")
        for row in c.fetchall():
            name, style = row
            button = QPushButton(name)
            button.setStyleSheet(self.favorite_button_style())  # 使用新的样式
            self.add_favorite_from_db(button)
        conn.close()

    def add_favorite_from_db(self, button):
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(lambda pos, btn=button: self.show_context_menu(pos, btn))
        
        row = len(self.buttons) // 2
        col = len(self.buttons) % 2
        self.layout().addWidget(button, row, col)
        self.buttons.append(button)

    def save_favorite(self, name, style):
        conn = sqlite3.connect('db/favorites.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS favorites
                     (name TEXT PRIMARY KEY, style TEXT)''')
        c.execute("INSERT OR REPLACE INTO favorites (name, style) VALUES (?, ?)", (name, style))
        conn.commit()
        conn.close()

    def remove_favorite(self, button):
        self.layout().removeWidget(button)
        self.buttons.remove(button)
        button.deleteLater()
        self.delete_favorite(button.text())
        self.rearrange_buttons()

    def delete_favorite(self, name):
        conn = sqlite3.connect('db/favorites.db')
        c = conn.cursor()
        c.execute("DELETE FROM favorites WHERE name = ?", (name,))
        conn.commit()
        conn.close()

    def rearrange_buttons(self):
        for i, button in enumerate(self.buttons):
            row = i // 2
            col = i % 2
            self.layout().addWidget(button, row, col)

    def check_db_version(self):
        conn = sqlite3.connect('db/favorites.db')
        c = conn.cursor()
        
        # 创建版本表(如果不存在)
        c.execute('''CREATE TABLE IF NOT EXISTS db_version
                     (version INTEGER PRIMARY KEY)''')
        
        # 获取当前版本
        c.execute("SELECT version FROM db_version")
        result = c.fetchone()
        current_version = result[0] if result else 0
        
        # 执行必要的升级
        if current_version < 1:
            # 升级到版本1: 添加style列
            c.execute("ALTER TABLE favorites ADD COLUMN style TEXT")
            c.execute("INSERT OR REPLACE INTO db_version (version) VALUES (1)")
            conn.commit()
            print("数据库已升级到版本1")
        
        conn.close()

    def favorite_button_style(self):
        return """
            QPushButton {
                background-color: #fffacd;  /* 浅黄色 */
                color: #333333;
                padding: 5px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #fff68f;  /* 稍深的黄色，用于悬停效果 */
            }
        """