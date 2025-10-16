import os

import maya.cmds as cmds
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtCore, QtWidgets

import CETools.functions.lookdev as ldf
from CETools.windows.customWidgets import FlowLayout, GroupBox, ToolButton, ToolkitButton, scale_buttons, \
    toggle_visibility
import CETools.windows.lookdev.ldtools as ldt
from CETools.windows.lookdev.ldConstants import *
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
        self.setWindowTitle("CE Look Dev Toolkit")
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
        texture_link_box = GroupBox(name="Texture Link".upper(), is_open=True)
        texture_link_layout = QtWidgets.QGridLayout()
        texture_link_box.vbox.addLayout(texture_link_layout)
        texture_link_widget = ldt.TextureLinkWidget(parent=self, tool_layout=texture_link_layout,
                                                    dir_path=scene_directory)
        texture_link_widget.hide()

        assign_by_name_box = GroupBox(name="Assign By Name".upper(), is_open=True)
        assign_by_name_layout = QtWidgets.QGridLayout()
        assign_by_name_box.vbox.addLayout(assign_by_name_layout)
        assign_by_name_widget = ldt.AssignByNameWidget(parent=self, tool_layout=assign_by_name_layout,
                                                       dir_path=scene_directory)
        assign_by_name_widget.hide()

        hdri_creator_box = GroupBox(name="HDRI Creator".upper(), is_open=True)
        hdri_creator_layout = QtWidgets.QGridLayout()
        hdri_creator_box.vbox.addLayout(hdri_creator_layout)
        hdri_creator_widget = ldt.HDRICreatorWidget(parent=self, tool_layout=hdri_creator_layout,
                                                    dir_path=scene_directory)
        hdri_creator_widget.hide()

        turntable_box = GroupBox(name="Turntable".upper(), is_open=True)
        turntable_layout = QtWidgets.QGridLayout()
        turntable_box.vbox.addLayout(turntable_layout)
        turntable_widget = ldt.TurntableWidget(parent=self, tool_layout=turntable_layout,
                                               dir_path=scene_directory)
        turntable_widget.hide()

        text_fields = texture_link_widget.dir_input

        page_layout.addWidget(common_box)

        # COMMON BUTTONS

        tool_layout = FlowLayout()
        tool_layout.setSpacing(0)
        vc_box.addLayout(tool_layout)

        mat_link_export_btn = ToolButton(icon_path=MATLINKEXPORT_ICON_CONST.format(self.filePath),
                                         tool_tip=MATLINKEXPORT_DESC_CONST)
        mat_link_export_btn.clicked.connect(lambda: ldf.write_shader_connections())
        tool_layout.addWidget(mat_link_export_btn)

        render_balls_btn = ToolButton(icon_path=RENDERBALLS_ICON_CONST.format(self.filePath),
                                      tool_tip=RENDERBALLS_DESC_CONST)
        render_balls_btn.clicked.connect(lambda: ldf.create_render_balls(self.filePath))
        tool_layout.addWidget(render_balls_btn)
        '''
        quick_turntable_btn = IconButton(icon_path=QTURNTABLE_ICON_CONST.format(self.filePath),
                                         tool_tip=QTURNTABLE_DESC_CONST)
        quick_turntable_btn.clicked.connect(lambda: ldf.quick_turntable())
        tool_layout.addWidget(quick_turntable_btn)
        '''
        texture_link_shelf_btn = ToolkitButton(icon_path=TEXTURELINK_ICON_CONST.format(self.filePath),
                                               tool_tip=TEXTURELINK_DESC_CONST)
        texture_link_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=texture_link_shelf_btn, widget=texture_link_box))
        texture_link_shelf_btn.double_clicked.connect(
            lambda: ldt.ToolWindow(tool="TextureLink", parent=self, window=True, width=TEXTURELINK_WIDTH_CONST,
                                   height=TEXTURELINK_HEIGHT_CONST))
        tool_layout.addWidget(texture_link_shelf_btn)
        texture_link_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        assign_by_name_shelf_btn = ToolkitButton(icon_path=ASSIGNBYNAME_ICON_CONST.format(self.filePath),
                                                 tool_tip=ASSIGNBYNAME_DESC_CONST)
        assign_by_name_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=assign_by_name_shelf_btn, widget=assign_by_name_box))
        assign_by_name_shelf_btn.double_clicked.connect(
            lambda: ldt.ToolWindow(tool="AssignByName", parent=self, window=True, width=ASSIGNBYNAME_WIDTH_CONST,
                                   height=ASSIGNBYNAME_HEIGHT_CONST))
        tool_layout.addWidget(assign_by_name_shelf_btn)
        assign_by_name_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        hdri_creator_shelf_btn = ToolkitButton(icon_path=HDRICREATOR_ICON_CONST.format(self.filePath),
                                               tool_tip=HDRICREATOR_DESC_CONST)
        hdri_creator_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=hdri_creator_shelf_btn, widget=hdri_creator_box))
        hdri_creator_shelf_btn.double_clicked.connect(
            lambda: ldt.ToolWindow(tool="HDRICreator", parent=self, window=True, width=HDRICREATOR_WIDTH_CONST,
                                   height=HDRICREATOR_HEIGHT_CONST))
        tool_layout.addWidget(hdri_creator_shelf_btn)
        hdri_creator_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        turntable_shelf_btn = ToolkitButton(icon_path=TURNTABLE_ICON_CONST.format(self.filePath),
                                            tool_tip=TURNTABLE_DESC_CONST)
        turntable_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=turntable_shelf_btn, widget=turntable_box))
        turntable_shelf_btn.double_clicked.connect(
            lambda: ldt.ToolWindow(tool="Turntable", parent=self, window=True, width=TURNTABLE_WIDTH_CONST,
                                   height=TURNTABLE_HEIGHT_CONST))
        tool_layout.addWidget(turntable_shelf_btn)
        turntable_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

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
