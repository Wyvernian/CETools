import os

import maya.cmds as cmds
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtCore, QtWidgets

import CETools.functions.modelling as mdf
from CETools.windows.customWidgets import FlowLayout, GroupBox, ToolButton, ToolkitButton, scale_buttons, \
    toggle_visibility
import CETools.windows.modelling.mdtools as mdt
from CETools.windows.modelling.mdConstants import *
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
        self.setWindowTitle("CE Modelling Toolkit")
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
        stamp_box = GroupBox(name="Stamp".upper(), is_open=True)
        stamp_layout = QtWidgets.QGridLayout()
        stamp_box.vbox.addLayout(stamp_layout)
        stamp_widget = mdt.StampWidget(parent=self, tool_layout=stamp_layout,
                                       dir_path=scene_directory)
        stamp_widget.hide()

        uv_layout_box = GroupBox(name="UV Layout".upper(), is_open=True)
        uv_layout_layout = QtWidgets.QGridLayout()
        uv_layout_box.vbox.addLayout(uv_layout_layout)
        uv_layout_widget = mdt.UVLayoutWidget(parent=self, tool_layout=uv_layout_layout,
                                              dir_path=scene_directory)
        uv_layout_widget.hide()

        mirror_box = GroupBox(name="Mirror Tools".upper(), is_open=True)
        mirror_layout = QtWidgets.QGridLayout()
        mirror_box.vbox.addLayout(mirror_layout)
        mirror_widget = mdt.MirrorWidget(parent=self, tool_layout=mirror_layout,
                                         dir_path=scene_directory)
        mirror_widget.hide()

        rotate_box = GroupBox(name="Rotation Tools".upper(), is_open=True)
        rotate_layout = QtWidgets.QGridLayout()
        rotate_box.vbox.addLayout(rotate_layout)
        rotate_widget = mdt.RotateWidget(parent=self, tool_layout=rotate_layout,
                                         dir_path=scene_directory)
        rotate_widget.hide()

        clean_box = GroupBox(name="Mesh Clean Tools".upper(), is_open=True)
        clean_layout = QtWidgets.QGridLayout()
        clean_box.vbox.addLayout(clean_layout)
        clean_widget = mdt.MeshCleanWidget(parent=self, tool_layout=clean_layout,
                                           dir_path=scene_directory)
        clean_widget.hide()

        page_layout.addWidget(common_box)

        # COMMON BUTTONS

        tool_layout = FlowLayout()
        tool_layout.setSpacing(0)
        vc_box.addLayout(tool_layout)

        copy_uvs_btn = ToolButton(icon_path=COPYUV_ICON_CONST.format(self.filePath),
                                  tool_tip=COPYUV_DESC_CONST)
        copy_uvs_btn.clicked.connect(lambda: mdf.copy_uvs())
        tool_layout.addWidget(copy_uvs_btn)

        move_to_pivot_btn = ToolButton(icon_path=MOVETOPIVOT_ICON_CONST.format(self.filePath),
                                       tool_tip=MOVETOPIVOT_DESC_CONST)
        move_to_pivot_btn.clicked.connect(lambda: mdf.move_to_pivot())
        tool_layout.addWidget(move_to_pivot_btn)

        stamp_shelf_btn = ToolkitButton(icon_path=STAMP_ICON_CONST.format(self.filePath), tool_tip=STAMP_DESC_CONST)
        stamp_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=stamp_shelf_btn, widget=stamp_box))
        stamp_shelf_btn.double_clicked.connect(
            lambda: mdt.ToolWindow(tool="Stamp", parent=self, window=True, width=STAMP_WIDTH_CONST,
                                   height=STAMP_HEIGHT_CONST))
        tool_layout.addWidget(stamp_shelf_btn)
        stamp_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        uv_layout_btn = ToolkitButton(icon_path=UVLAYOUT_ICON_CONST.format(self.filePath), tool_tip=UVLAYOUT_DESC_CONST)
        uv_layout_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=uv_layout_btn, widget=uv_layout_box))
        uv_layout_btn.double_clicked.connect(
            lambda: mdt.ToolWindow(tool="UVLayout", parent=self, window=True, width=UVLAYOUT_WIDTH_CONST,
                                   height=UVLAYOUT_HEIGHT_CONST))
        tool_layout.addWidget(uv_layout_btn)
        uv_layout_btn.setStyleSheet("""           
                        QPushButton:hover {{
                            image: url("{}/icons/open.png")
                        }}
                """.format(self.filePath))

        mirror_btn = ToolkitButton(icon_path=MIRROR_ICON_CONST.format(self.filePath), tool_tip=MIRROR_DESC_CONST)
        mirror_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=mirror_btn, widget=mirror_box))
        mirror_btn.double_clicked.connect(
            lambda: mdt.ToolWindow(tool="Mirror", parent=self, window=True, width=MIRROR_WIDTH_CONST,
                                   height=MIRROR_HEIGHT_CONST))
        tool_layout.addWidget(mirror_btn)
        mirror_btn.setStyleSheet("""           
                                QPushButton:hover {{
                                    image: url("{}/icons/open.png")
                                }}
                        """.format(self.filePath))

        rotate_btn = ToolkitButton(icon_path=ROTATE_ICON_CONST.format(self.filePath), tool_tip=ROTATE_DESC_CONST)
        rotate_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=rotate_btn, widget=rotate_box))
        rotate_btn.double_clicked.connect(
            lambda: mdt.ToolWindow(tool="Rotate", parent=self, window=True, width=ROTATE_WIDTH_CONST,
                                   height=ROTATE_HEIGHT_CONST))
        tool_layout.addWidget(rotate_btn)
        rotate_btn.setStyleSheet("""           
                                QPushButton:hover {{
                                    image: url("{}/icons/open.png")
                                }}
                        """.format(self.filePath))

        clean_btn = ToolkitButton(icon_path=CLEAN_ICON_CONST.format(self.filePath), tool_tip=CLEAN_DESC_CONST)
        clean_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=clean_btn, widget=clean_box))
        clean_btn.double_clicked.connect(
            lambda: mdt.ToolWindow(tool="Clean", parent=self, window=True, width=CLEAN_WIDTH_CONST,
                                   height=CLEAN_HEIGHT_CONST))
        tool_layout.addWidget(clean_btn)
        clean_btn.setStyleSheet("""           
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
