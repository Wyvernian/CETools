import os

import maya.cmds as cmds
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtCore, QtWidgets

from CETools.windows.customWidgets import FlowLayout, GroupBox, ToolkitButton, scale_buttons, \
    toggle_visibility
import CETools.windows.animation.antools as ant
from CETools.windows.animation.anConstants import *
from CETools.functions.commonFunctions import refresh_dir


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class MainWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)

        self.cbox = None
        self.fileName = os.path.basename(__file__)
        self.filePath = os.path.dirname(__file__)
        self.build_win()

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        width = self.frameGeometry().width()
        if width < 1155:
            self.cbox.setFixedWidth(width - 20)
        else:
            self.cbox.setFixedWidth(1135)

    def build_win(self):
        self.setWindowTitle("CE Animation Toolkit")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setMinimumWidth(100)
        self.setMinimumHeight(110)
        self.resize(300, 700)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_container = QtWidgets.QWidget(self)
        scroll = QtWidgets.QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget

        page_layout = FlowLayout(main_container)
        page_layout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        page_layout.setContentsMargins(0, 0, 0, 0)

        scene_file = cmds.file(q=1, loc=1, un=0)
        if '/tasks' in scene_file:
            scene_directory = scene_file.split('/tasks')[0] + '/tasks'
        else:
            scene_directory = '/'.join(scene_file.split('/')[:-1])

        text_fields = []

        # CHANGE BTN SIZE

        scale_up_btn = QtWidgets.QAction("+", self)
        scale_up_btn.triggered.connect(lambda x: scale_buttons(tool_layout, factor=5))

        scale_down_btn = QtWidgets.QAction("-", self)
        scale_down_btn.triggered.connect(lambda x: scale_buttons(tool_layout, factor=-5))

        # MENU STUFF

        menu_bar = QtWidgets.QMenuBar()

        menu_bar.addAction(scale_up_btn)
        menu_bar.addAction(scale_down_btn)

        workspace_menu = QtWidgets.QMenu(self)
        workspace_menu.setTitle("Workspace")
        menu_bar.addMenu(workspace_menu)

        refresh_dir_menu = QtWidgets.QAction("Refresh working directory", self)
        refresh_dir_menu.triggered.connect(lambda x: refresh_dir(text_fields))

        workspace_menu.addAction(refresh_dir_menu)

        main_layout.addWidget(menu_bar)

        scroll.setWidget(main_container)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)

        main_layout.addWidget(scroll)

        common_box = QtWidgets.QWidget()
        common_box.setContentsMargins(0, 0, 0, 0)
        common_layout = QtWidgets.QGridLayout(common_box)

        self.cbox = QtWidgets.QFrame(self)
        common_layout.addWidget(self.cbox, 0, 0)
        common_layout.setContentsMargins(0, 0, 0, 0)

        common_layout.addWidget(self.cbox)

        vc_box = QtWidgets.QVBoxLayout(self.cbox)
        common_layout.setSpacing(0)

        # SHELVES
        copy_anim_box = GroupBox(name="Copy Anim".upper(), is_open=True)
        copy_anim_layout = QtWidgets.QGridLayout()
        copy_anim_box.vbox.addLayout(copy_anim_layout)
        copy_anim_widget = ant.CopyAnimWidget(parent=self, tool_layout=copy_anim_layout,
                                              dir_path=scene_directory)
        copy_anim_widget.hide()

        bookmark_box = GroupBox(name="Bookmark Tools".upper(), is_open=True)
        bookmark_layout = QtWidgets.QGridLayout()
        bookmark_box.vbox.addLayout(bookmark_layout)
        bookmark_widget = ant.BookmarkToolsWidget(parent=self, tool_layout=bookmark_layout,
                                              dir_path=scene_directory)
        bookmark_widget.hide()

        page_layout.addWidget(common_box)

        # COMMON BUTTONS

        tool_layout = FlowLayout()
        tool_layout.setSpacing(0)
        vc_box.addLayout(tool_layout)

        copy_anim_shelf_btn = ToolkitButton(icon_path=COPYANIM_ICON_CONST.format(self.filePath),
                                            tool_tip=COPYANIM_DESC_CONST)
        copy_anim_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=copy_anim_shelf_btn, widget=copy_anim_box))
        copy_anim_shelf_btn.double_clicked.connect(
            lambda: ant.ToolWindow(tool="CopyAnim", parent=self, window=True, width=COPYANIM_WIDTH_CONST,
                                   height=COPYANIM_HEIGHT_CONST))
        tool_layout.addWidget(copy_anim_shelf_btn)
        copy_anim_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        bookmark_shelf_btn = ToolkitButton(icon_path=BOOKMARK_ICON_CONST.format(self.filePath),
                                           tool_tip=BOOKMARK_DESC_CONST)
        bookmark_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=bookmark_shelf_btn, widget=bookmark_box))
        bookmark_shelf_btn.double_clicked.connect(
            lambda: ant.ToolWindow(tool="BookmarkTools", parent=self, window=True, width=BOOKMARK_WIDTH_CONST,
                                   height=BOOKMARK_HEIGHT_CONST))
        tool_layout.addWidget(bookmark_shelf_btn)
        bookmark_shelf_btn.setStyleSheet("""           
                        QPushButton:hover {{
                            image: url("{}/icons/open.png")
                        }}
                """.format(self.filePath))

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
            
            IconButton, AdvIconButton {
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
            
            QPushButton:hover {
                background-color: rgb(70,70,70)
            }

                
            QFrame { 
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
