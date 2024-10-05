from PyQt6.QtCore import QMimeData, QPoint
from PyQt6.QtGui import QPixmap, QRegion, QAction
from PyQt6.QtWidgets import QTabWidget, QMenu, QWidget
from PyQt6.QtWidgets import QTabWidget, QStylePainter, QStyleOptionTab, QStyle, QTabBar
from PyQt6.QtCore import QRect, Qt, QPoint
from PyQt6.QtGui import QColor, QPainter, QPen, QWheelEvent
from PyQt6.QtWidgets import QToolButton, QCalendarWidget, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QDate
import os
from PyQt6.QtGui import QColor, QPainter, QPen, QWheelEvent
class CircularTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setUsesScrollButtons(True)
        self.setDocumentMode(True)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.setCurrentIndex((self.currentIndex() - 1) % self.count())
        else:
            self.setCurrentIndex((self.currentIndex() + 1) % self.count())

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(min(200, size.width()))  # Limit max width to 200 pixels
        return size

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            if opt.text:
                text_rect = self.style().subElementRect(QStyle.SubElement.SE_TabBarTabText, opt, self)
                painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextShowMnemonic, opt.text)
            else:
                painter.drawControl(QStyle.ControlElement.CE_TabBarTab, opt)

class ImprovedTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(CircularTabBar(self))
        self.setTabPosition(QTabWidget.TabPosition.North)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.filesets = {}  # Dictionary to store filesets

    def add_to_fileset(self, fileset_name, file_path):
        if fileset_name not in self.filesets:
            self.filesets[fileset_name] = []
        if file_path not in self.filesets[fileset_name]:
            self.filesets[fileset_name].append(file_path)
        self.update_fileset_tabs()

    def update_fileset_tabs(self):
        self.clear()
        for fileset_name, files in self.filesets.items():
            for file_path in files:
                self.add_new_tab(file_path), os.path.basename(file_path)
        self.addTab(QWidget(), "+")  # Add tab for creating new filesets


class ImprovedTabBar(QTabBar):
    def __init__(self):
        super().__init__()
        self.setDrawBase(False)
        self.setExpanding(False)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionTab()

        for index in range(self.count()):
            self.initStyleOption(option, index)
            if index == self.currentIndex():
                option.state |= QStyle.StateFlag.State_Selected
            painter.drawControl(QStyle.ControlElement.CE_TabBarTab, option)

        # Draw a line at the bottom of the tab bar
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawLine(self.rect().bottomLeft(), self.rect().bottomRight())

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setHeight(size.height() - 2)  # Reduce tab height slightly
        return size
class TabWidget(QTabWidget):
    def __init__(self, parent=None, new=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.tabBar().setMouseTracking(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        if new:
            TabWidget.setup(self)

    def __setstate__(self, data):
        self.__init__(new=False)
        self.setParent(data["parent"])
        for widget, tabname in data["tabs"]:
            self.addTab(widget, tabname)
        TabWidget.setup(self)

    def __getstate__(self):
        data = {
            "parent": self.parent(),
            "tabs": [],
        }
        tab_list = data["tabs"]
        for k in range(self.count()):
            tab_name = self.tabText(k)
            widget = self.widget(k)
            tab_list.append((widget, tab_name))
        return data

    def setup(self):
        pass

    def mouseMoveEvent(self, e):
        globalPos = self.mapToGlobal(e.pos())
        tabBar = self.tabBar()
        posInTab = tabBar.mapFromGlobal(globalPos)
        index = tabBar.tabAt(e.pos())
        tabRect = tabBar.tabRect(index)

        pixmap = QPixmap(tabRect.size())
        tabBar.render(pixmap, QPoint(), QRegion(tabRect))
        mimeData = QMimeData()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        close_alltabs = QAction("Close All Tabs", self)
        close_alltabs.triggered.connect(self.close_all_tabs)
        menu.addAction(close_alltabs)
        menu.exec(event.globalPos())

    def close_all_tabs(self):
        self.clear()

    def addTab(self, widget, label):
        index = super().addTab(widget, label)
        if self.is_daily_note(label):
            self.add_daily_note_buttons(index)
        return index

    def is_daily_note(self, label):
        # Implement your logic to determine if it's a daily note
        # For example, check if the label matches a date format
        try:
            QDate.fromString(label, "yyyy-MM-dd")
            return True
        except:
            return False

    def add_daily_note_buttons(self, index):
        tab_bar = self.tabBar()
        
        # Create buttons
        back_button = QToolButton(self)
        back_button.setIcon(QIcon.fromTheme("go-previous"))
        back_button.clicked.connect(lambda: self.navigate_daily_note(index, -1))

        forward_button = QToolButton(self)
        forward_button.setIcon(QIcon.fromTheme("go-next"))
        forward_button.clicked.connect(lambda: self.navigate_daily_note(index, 1))

        calendar_button = QToolButton(self)
        calendar_button.setIcon(QIcon.fromTheme("x-office-calendar"))
        calendar_button.clicked.connect(lambda: self.show_calendar(index))

        # Add buttons to tab
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.LeftSide, back_button)
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, forward_button)
        
        # For the calendar button, we need to create a custom widget
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(calendar_button)
        layout.setContentsMargins(0, 0, 0, 0)
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, widget)

    def navigate_daily_note(self, index, direction):
        current_date = QDate.fromString(self.tabText(index), "yyyy-MM-dd")
        new_date = current_date.addDays(direction)
        new_label = new_date.toString("yyyy-MM-dd")
        # Here you would implement the logic to open the new daily note
        print(f"Navigating to {new_label}")

    def show_calendar(self, index):
        calendar = QCalendarWidget(self)
        calendar.clicked.connect(lambda date: self.navigate_to_date(index, date))
        calendar.show()

    def navigate_to_date(self, index, date):
        new_label = date.toString("yyyy-MM-dd")
        # Here you would implement the logic to open the daily note for the selected date
        print(f"Navigating to {new_label}")
