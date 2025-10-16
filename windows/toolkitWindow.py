import functools
import os
from abc import abstractmethod

import maya.cmds as cmds
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtCore, QtGui, QtWidgets

from CETools.windows.customWidgets import FlowLayout, GroupBox, ToolButton, ToolkitButton, scale_buttons
from CETools.functions.commonFunctions import refresh_dir


class Tool(object):
    # Generic class that handles base actions for tools
    # This includes creating buttons, toggleable shelves, etc.
    # Subclasses should only need to take a few input layouts to function, and tool properties should be hard-coded.
    # Abstracted methods are ones that are always called for creation of any subclasses
    def __init__(self, name, tool_tip, icon_path=''):
        self.name = name
        self.tool_tip = tool_tip
        self.icon_path = icon_path
        self.button = None

    @abstractmethod
    def create_button(self, toolbox_parent_layout, parent_window):
        pass

    @abstractmethod
    def delete_button(self):
        pass

    def get_name(self):
        return self.name

    def get_tooltip(self):
        return self.tool_tip

    def get_button(self):
        return self.button

    def get_toolbox(self):
        return None

    def get_directory_dependents(self):
        pass


class SimpleTool(Tool):
    # Subclass of Tool intended for simple buttons that run a command on click.

    def __init__(self, name, tool_tip, on_click_function, icon_path=''):
        super().__init__(name, tool_tip, icon_path)
        self.on_click_function = on_click_function

    def create_button(self, toolbox_parent_layout=None, parent_window=None, image_path=''):
        # Create the ToolkitButton (a subclass of QPushButton) and assign an icon, or if not found,
        # a name to the button. Link the clicked command to the button afterward.
        icon_file_path = os.path.join(image_path, self.icon_path) if image_path and self.icon_path else None
        self.button = ToolButton(tool_tip=self.tool_tip, icon_path=icon_file_path, name=self.name)
        self.button.clicked.connect(self.on_click_function)

    def delete_button(self):
        self.button.deleteLater()


class Toolkit(Tool):
    # Subclass of Tool, that uses the QPushButton as a toggle for the toolbox. Needs to handle more data
    # than Simple Tool, including creating a generic shell ToolWidget to hold the custom tool data.
    # Each toolbox is unique and stored in their respective tools python file (e.g. rdtools is rendering tools)
    # If the button is double-clicked, the toolbox will pop out a copy into a new window.

    def __init__(self, name, tool_tip, toolbox_function, icon_path=''):
        super().__init__(name, tool_tip, icon_path)
        self.tool_widget = None
        self.tool_groupbox = None
        self.tool_layout = None
        self.toolbox_function = toolbox_function

    def create_button(self, toolbox_parent_layout, parent_window, image_path=''):
        # Create the ToolkitButton (a subclass of QPushButton) and assign an icon, or if not found,
        # a name to the button. Then run the toolbox shell creation function.
        icon_file_path = os.path.join(image_path, self.icon_path) if image_path and self.icon_path else None
        self.button = ToolkitButton(tool_tip=self.tool_tip, icon_path=icon_file_path, name=self.name)
        self.create_toolbox_shell(toolbox_parent_layout, parent_window)

    def create_toolbox_shell(self, toolbox_parent_layout, parent_window):
        self.tool_groupbox = GroupBox(name=self.name.upper(), is_open=True)
        self.tool_layout = QtWidgets.QGridLayout()

        # Instantiate the ToolWidget and connect it to the layouts inside the tool_groupbox and the parent window
        self.tool_widget = ToolWidget(tool=self.toolbox_function, parent=parent_window,
                                      window=False, layout=self.tool_layout)

        # Access the vbox component of the tool_groupbox and add the custom tool layouts into it.
        self.tool_groupbox.vbox.addLayout(self.tool_layout)
        self.tool_widget.hide()
        self.button.left_clicked.connect(
            lambda: self.toggle_toolbox_visibility(parent_layout=toolbox_parent_layout))
        self.button.double_clicked.connect(
            lambda: ToolWidget(tool=self.toolbox_function, parent=parent_window, window=True))

    def toggle_toolbox_visibility(self, parent_layout):
        # Toggle visibility and remove widget from parent Tool FlowLayout, but DO NOT delete the tool instance so
        # the current tool config is preserved
        if self.button.isChecked():
            parent_layout.removeWidget(self.tool_groupbox)
            self.button.setEnabled(False)
            self.tool_groupbox.hide()
        else:
            parent_layout.addWidget(self.tool_groupbox)
            self.button.setEnabled(True)
            self.tool_groupbox.show()

    def get_directory_dependents(self):
        # Return a list of the widgets that require a connection to the refresh_dir function of the main toolkit window.
        #self.directory_dependents = self.tool_widget.dir_input
        pass

    def set_working_directory(self):
        pass

    def delete_button(self):
        # Delete the QPushButton and the toolbox/groupbox.
        self.button.deleteLater()
        self.tool_groupbox.deleteLater()

    def get_toolbox(self):
        return self.tool_groupbox


def load_window(name, image_path, tools_mapping, default_tools=None):
    try:
        custom_win.close()
        custom_win.deleteLater()
    except:
        pass
    custom_win = ToolkitWindow(name=name, image_path=image_path, tools_mapping=tools_mapping,
                               default_tools=default_tools)
    try:
        custom_win.create()
        custom_win.show(dockable=True)

    except:
        custom_win.close()
        custom_win.deleteLater()


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class ToolWidget(QtWidgets.QWidget):

    def __init__(self, parent, tool=None, window=False, layout=None, height=200, width=250):
        super().__init__(parent)

        self.fileName = os.path.basename(__file__)
        self.filePath = os.path.dirname(__file__)
        self.layout = layout
        self.parent = parent
        self.window = window
        self.height = height
        self.width = width
        self.tool = tool
        self.build_win()

    def move_ui(self):
        pos = QtGui.QCursor.pos()
        self.move(pos.x() - self.width / 2, pos.y() - 15)

    def build_win(self):
        if self.window:
            self.setWindowFlags(QtCore.Qt.Tool)
            self.setFixedSize(self.width, self.height)
            container = QtWidgets.QWidget(self)
            tool_layout = QtWidgets.QGridLayout(container)
        else:
            tool_layout = self.layout

        scene_file = cmds.file(q=1, loc=1, un=0)
        if '/tasks' in scene_file:
            dir_path = scene_file.split('/tasks')[0] + '/tasks'
        else:
            dir_path = '/'.join(scene_file.split('/')[:-1])

        self.tool(parent=self, tool_layout=tool_layout, dir_path=dir_path)

        if self.window:
            self.move_ui()

        self.show()


class ToolkitWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window(), name='CE Custom Toolkit', image_path='', tools_mapping=None,
                 default_tools=None):
        super().__init__(parent)

        self.directory_pointers = []
        self.page_layout = None
        self.image_path = image_path
        self.main_tool_layout = FlowLayout()
        self.common_frame = QtWidgets.QFrame(self)
        self.tools_mapping = tools_mapping
        self.default_tools = default_tools
        self.toolkit_name = name
        self.fileName = os.path.basename(__file__)
        self.filePath = os.path.dirname(__file__)
        self.build_win()

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        width = self.frameGeometry().width()
        if width < 1155:
            self.common_frame.setFixedWidth(width - 20)
        else:
            self.common_frame.setFixedWidth(1135)

    def toggle_tool(self, tool_instance, tool_action):
        checked = tool_action.isChecked()
        if checked:
            tool_instance.create_button(toolbox_parent_layout=self.page_layout, parent_window=self,
                                        image_path=self.image_path)
            self.main_tool_layout.addWidget(tool_instance.get_button())
            # Retrieve pointers to widgets that the refresh_dir button will influence
            #dir_dependents = tool_instance.get_directory_dependents()
            #if dir_dependents:
            #    self.directory_pointers.append(dir_dependents)
        else:
            self.main_tool_layout.removeWidget(tool_instance.get_button())
            toolbox = tool_instance.get_toolbox()
            if toolbox:
                self.page_layout.removeWidget(toolbox)
            tool_instance.delete_button()

    def scale_buttons(self, factor=0):
        for i in range(self.main_tool_layout.count()):
            widget = self.main_tool_layout.itemAt(i).widget()
            if isinstance(widget, QtWidgets.QPushButton):
                size = str(widget.iconSize())
                size = size.split("(")[-1]
                size = int(size.split(",")[0])
                new_size = size + factor * 2
                if 50 <= new_size <= 100:
                    widget.setIconSize(QtCore.QSize(new_size, new_size))

    def toggle_all(self, menu, ignore, state):
        for action in menu.actions():
            if action not in ignore:
                if action.isChecked() != state:
                    action.trigger()

    def build_win(self):
        self.setWindowTitle(self.toolkit_name)
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setMinimumWidth(100)
        self.setMinimumHeight(110)
        self.resize(300, 700)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_container = QtWidgets.QWidget(self)
        scroll = QtWidgets.QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget

        self.page_layout = FlowLayout(main_container)
        self.page_layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.page_layout.setContentsMargins(0, 0, 0, 0)

        scene_file = cmds.file(q=1, loc=1, un=0)
        if '/tasks' in scene_file:
            scene_directory = scene_file.split('/tasks')[0] + '/tasks'
        else:
            scene_directory = '/'.join(scene_file.split('/')[:-1])

        text_fields = []

        # CHANGE BTN SIZE

        scale_up_btn = QtWidgets.QAction("+", self)
        scale_up_btn.triggered.connect(lambda: scale_buttons(self.main_tool_layout, factor=5))

        scale_down_btn = QtWidgets.QAction("-", self)
        scale_down_btn.triggered.connect(lambda: scale_buttons(self.main_tool_layout, factor=-5))

        # MENU STUFF

        menu_bar = QtWidgets.QMenuBar()

        menu_bar.addAction(scale_up_btn)
        menu_bar.addAction(scale_down_btn)

        # Workspace Menu
        workspace_menu = QtWidgets.QMenu("Workspace", self)
        menu_bar.addMenu(workspace_menu)

        refresh_dir_menu = QtWidgets.QAction("Refresh working directory", self)
        refresh_dir_menu.triggered.connect(lambda x: refresh_dir(text_fields))
        workspace_menu.addAction(refresh_dir_menu)

        # Add Tools Menu
        tools_menu = QtWidgets.QMenu("Enable Tools", self)
        menu_bar.addMenu(tools_menu)

        main_layout.addWidget(menu_bar)

        # Adding layouts

        scroll.setWidget(main_container)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)

        main_layout.addWidget(scroll)

        common_box = QtWidgets.QWidget()
        common_box.setContentsMargins(0, 0, 0, 0)
        common_layout = QtWidgets.QGridLayout(common_box)

        common_layout.addWidget(self.common_frame, 0, 0)
        common_layout.setContentsMargins(0, 0, 0, 0)

        common_layout.addWidget(self.common_frame)

        vertical_content_box = QtWidgets.QVBoxLayout(self.common_frame)
        common_layout.setSpacing(0)

        # Layout for flowing open toolboxes
        self.main_tool_layout.setSpacing(0)
        # search_layout = self.build_search_box()
        # vertical_content_box.addLayout(search_layout)
        vertical_content_box.addLayout(self.main_tool_layout)

        # Add a QMenu, with categories and tool checkboxes that match the tool_mapping dict.
        for tool_category in self.tools_mapping.keys():
            toolbox_menu = QtWidgets.QMenu(tool_category, self)
            tools_menu.addMenu(toolbox_menu)
            show_all_action = QtWidgets.QAction('All', self)
            show_none_action = QtWidgets.QAction('None', self)
            toolbox_menu.addAction(show_all_action)
            toolbox_menu.addAction(show_none_action)
            toolbox_menu.addSeparator()

            for tool in self.tools_mapping[tool_category].keys():
                # Create menu button for class toggle
                tool_action = QtWidgets.QAction(tool, self)
                tool_action.setCheckable(True)
                # Get and create class from tool mapping
                tool_class = self.tools_mapping[tool_category][tool]
                tool_instance = tool_class()
                # Connect switching buttons on/off to tool_action
                tool_action.triggered.connect(
                    functools.partial(self.toggle_tool, tool_instance=tool_instance, tool_action=tool_action))
                toolbox_menu.addAction(tool_action)
                if self.default_tools:
                    if tool in self.default_tools:
                        tool_action.setChecked(True)
                        self.toggle_tool(tool_instance=tool_instance, tool_action=tool_action)

            # Check all boxes on/off in category
            show_all_action.triggered.connect(
                functools.partial(self.toggle_all, toolbox_menu, [show_all_action, show_none_action], state=True))
            show_none_action.triggered.connect(
                functools.partial(self.toggle_all, toolbox_menu, [show_all_action, show_none_action], state=False))

        self.page_layout.addWidget(common_box)

        # Example code for windows that I'm aiming towards. Simple and Toolbox tools should be called the same way.

        '''
        for tool_name in tool_names:
            if tool_name in self.tools_mapping.keys():
                tool_class = self.tools_mapping[tool_name]
                tool_instance = tool_class()
                tool_instance.create_button(toolbox_parent_layout=self.page_layout, parent_window=self)
                self.main_tool_layout.addWidget(tool_instance.get_button())
            else:
                logging.warning(f'{tool_name} was not found in tool_mapping dict')
        '''
        # Set stylesheet weirdly

        self.setStyleSheet("""
            MainWindow {            
                background-color: #161616;
            }

            QRadioButton {
                background-color: rgb(27,27,27);
            }

            QRadioButton::indicator::unchecked {
                background-color: black;
                border: 1px solid; 
                border-radius: 5px; 
            }
            
            ToolkitButton {
                border-radius: 5px;
                font-weight: bold;
                font-family: verdana;
                font-size: 10px;
                color: rgb(150,150,150);
                background-color: none;
            }

            ToolButton {
                border-radius: 5px;
                font-weight: bold;
                font-family: verdana;
                font-size: 10px;
                color: rgb(150,150,150);
                background-color: none;
            }


            QPushButton {
                background-color: rgb(50,50,50);
                font-weight: bold;
                font-family: verdana;
                font-size: 10px;
                color: rgb(150,150,150);

            }


            QFrame { 
                background-color: rgb(27,27,27); 
            }
            
            QMenuBar { 
                background-color: rgb(27,27,27); 
            }
            
            Tool { 
                background-color: rgb(27,27,27); 
            }
            
            
            QScrollArea { 
                background-color: rgb(27,27,27); 
            }

            QLineEdit {
                background-color: rgb(10,10,10);
            }

            QSpinBox {
                background-color: rgb(10,10,10);
            }

            QDoubleSpinBox {
                background-color: rgb(10,10,10);
            }


            QGroupBox {
                border-radius: 3px;
                background-color: rgb(35,35,35);
                font-weight: bold;
                font-size: 12px;
                font-family: verdana;
            }


            QGroupBox::title {
                subcontrol-origin: margin;
                left: 6px;
                top: 4px;
            }
            QGroupBox::indicator:checked {
                image: url(:/arrowDown.png);
            }
            QGroupBox::indicator:unchecked {
                image: url(:/arrowRight.png);
            }

            }


            QWidget {
                background-color: #161616;
                border: 0px;

            }

            QScrollBar {
                background-color: #161616;
                border-radius: 5px;
            }

            QScrollBar::handle {
                background-color: rgb(100,100,100);
                border-radius: 2px;   
            }

             QScrollBar:horizontal {
                height: 5px;
            }

            QScrollBar:vertical {
                width: 5px;
            }

            """)
