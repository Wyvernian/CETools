import os

import maya.cmds as cmds
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtCore, QtWidgets

from CETools.windows.customWidgets import FlowLayout, GroupBox, ToolkitButton, scale_buttons, \
    toggle_visibility
import CETools.windows.rigging.rgtools as rgt
from CETools.windows.rigging.rgConstants import *
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
        self.setWindowTitle("CE Rigging Toolkit")
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
        ai_color_box = GroupBox(name="AiColor Control".upper(), is_open=True)
        ai_color_layout = QtWidgets.QGridLayout()
        ai_color_box.vbox.addLayout(ai_color_layout)
        ai_color_widget = rgt.AiColorAttribute(parent=self, tool_layout=ai_color_layout,
                                               dir_path=scene_directory)
        ai_color_widget.hide()

        palette_box = GroupBox(name="Color Palette".upper(), is_open=True)
        palette_layout = QtWidgets.QGridLayout()
        palette_box.vbox.addLayout(palette_layout)
        palette_widget = rgt.PaletteWidget(parent=self, tool_layout=palette_layout,
                                           dir_path=scene_directory)
        palette_widget.hide()

        joint_tools_box = GroupBox(name="Joint Tools".upper(), is_open=True)
        joint_tools_layout = QtWidgets.QGridLayout()
        joint_tools_box.vbox.addLayout(joint_tools_layout)
        joint_tools_widget = rgt.JointToolsWidget(parent=self, tool_layout=joint_tools_layout,
                                                  dir_path=scene_directory)
        joint_tools_widget.hide()

        cluster_tools_box = GroupBox(name="Cluster Tools".upper(), is_open=True)
        cluster_tools_layout = QtWidgets.QGridLayout()
        cluster_tools_box.vbox.addLayout(cluster_tools_layout)
        cluster_tools_widget = rgt.ClusterToolsWidget(parent=self, tool_layout=cluster_tools_layout,
                                                  dir_path=scene_directory)
        cluster_tools_widget.hide()


        curve_creator_box = GroupBox(name="Curve Creator".upper(), is_open=True)
        curve_creator_layout = QtWidgets.QGridLayout()
        curve_creator_box.vbox.addLayout(curve_creator_layout)
        curve_creator_widget = rgt.CurveCreatorWidget(parent=self, tool_layout=curve_creator_layout,
                                                      dir_path=scene_directory)
        curve_creator_widget.hide()

        rig_preset_box = GroupBox(name="Vehicle Rig".upper(), is_open=True)
        rig_preset_layout = QtWidgets.QGridLayout()
        rig_preset_box.vbox.addLayout(rig_preset_layout)
        vehicle_rig_widget = rgt.RigPresetWidget(parent=self, tool_layout=rig_preset_layout,
                                                  dir_path=scene_directory)
        vehicle_rig_widget.hide()

        optimise_box = GroupBox(name="Optimise Rig".upper(), is_open=True)
        optimise_layout = QtWidgets.QGridLayout()
        optimise_box.vbox.addLayout(optimise_layout)
        optimise_widget = rgt.OptimiseWidget(parent=self, tool_layout=optimise_layout,
                                             dir_path=scene_directory)
        optimise_widget.hide()

        matrix_box = GroupBox(name="Matrix Tools".upper(), is_open=True)
        matrix_layout = QtWidgets.QGridLayout()
        matrix_box.vbox.addLayout(matrix_layout)
        matrix_widget = rgt.MatrixRiggingWidget(parent=self, tool_layout=matrix_layout,
                                                dir_path=scene_directory)
        matrix_widget.hide()

        page_layout.addWidget(common_box)

        # COMMON BUTTONS

        tool_layout = FlowLayout()
        tool_layout.setSpacing(0)
        vc_box.addLayout(tool_layout)

        ai_color_shelf_btn = ToolkitButton(icon_path=AICOLOR_ICON_CONST.format(self.filePath),
                                           tool_tip=AICOLOR_DESC_CONST)
        ai_color_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=ai_color_shelf_btn, widget=ai_color_box))
        ai_color_shelf_btn.double_clicked.connect(
            lambda: rgt.ToolWindow(tool="AiColorAttribute", parent=self, window=True, width=AICOLOR_WIDTH_CONST,
                                   height=AICOLOR_HEIGHT_CONST))
        tool_layout.addWidget(ai_color_shelf_btn)
        ai_color_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        palette_shelf_btn = ToolkitButton(icon_path=PALETTE_ICON_CONST.format(self.filePath),
                                          tool_tip=PALETTE_DESC_CONST)
        palette_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=palette_shelf_btn, widget=palette_box))
        palette_shelf_btn.double_clicked.connect(
            lambda: rgt.ToolWindow(tool="Palette", parent=self, window=True, width=PALETTE_WIDTH_CONST,
                                   height=PALETTE_HEIGHT_CONST))
        tool_layout.addWidget(palette_shelf_btn)
        palette_shelf_btn.setStyleSheet("""           
                        QPushButton:hover {{
                            image: url("{}/icons/open.png")
                        }}
                """.format(self.filePath))

        joint_tools_shelf_btn = ToolkitButton(icon_path=JOINTTOOLS_ICON_CONST.format(self.filePath),
                                              tool_tip=JOINTTOOLS_DESC_CONST)
        joint_tools_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=joint_tools_shelf_btn, widget=joint_tools_box))
        joint_tools_shelf_btn.double_clicked.connect(
            lambda: rgt.ToolWindow(tool="JointTools", parent=self, window=True, width=JOINTTOOLS_WIDTH_CONST,
                                   height=JOINTTOOLS_HEIGHT_CONST))
        tool_layout.addWidget(joint_tools_shelf_btn)
        joint_tools_shelf_btn.setStyleSheet("""           
                        QPushButton:hover {{
                            image: url("{}/icons/open.png")
                        }}
                """.format(self.filePath))

        cluster_tools_shelf_btn = ToolkitButton(icon_path=CLUSTERTOOLS_ICON_CONST.format(self.filePath),
                                                tool_tip=CLUSTERTOOLS_DESC_CONST)
        cluster_tools_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=cluster_tools_shelf_btn, widget=cluster_tools_box))
        cluster_tools_shelf_btn.double_clicked.connect(
            lambda: rgt.ToolWindow(tool="ClusterTools", parent=self, window=True, width=CLUSTERTOOLS_WIDTH_CONST,
                                   height=CLUSTERTOOLS_HEIGHT_CONST))
        tool_layout.addWidget(cluster_tools_shelf_btn)
        cluster_tools_shelf_btn.setStyleSheet("""           
                                QPushButton:hover {{
                                    image: url("{}/icons/open.png")
                                }}
                        """.format(self.filePath))

        curve_creator_shelf_btn = ToolkitButton(icon_path=CURVECREATOR_ICON_CONST.format(self.filePath),
                                                tool_tip=CURVECREATOR_DESC_CONST)
        curve_creator_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=curve_creator_shelf_btn, widget=curve_creator_box))
        curve_creator_shelf_btn.double_clicked.connect(
            lambda: rgt.ToolWindow(tool="CurveCreator", parent=self, window=True, width=CURVECREATOR_WIDTH_CONST,
                                   height=CURVECREATOR_HEIGHT_CONST))
        tool_layout.addWidget(curve_creator_shelf_btn)
        curve_creator_shelf_btn.setStyleSheet("""           
                                QPushButton:hover {{
                                    image: url("{}/icons/open.png")
                                }}
                        """.format(self.filePath))

        rig_preset_shelf_btn = ToolkitButton(icon_path=VEHICLERIG_ICON_CONST.format(self.filePath),
                                             tool_tip=VEHICLERIG_DESC_CONST)
        rig_preset_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=rig_preset_shelf_btn, widget=rig_preset_box))
        rig_preset_shelf_btn.double_clicked.connect(
            lambda: rgt.ToolWindow(tool="RigPreset", parent=self, window=True, width=VEHICLERIG_WIDTH_CONST,
                                   height=VEHICLERIG_HEIGHT_CONST))
        tool_layout.addWidget(rig_preset_shelf_btn)
        rig_preset_shelf_btn.setStyleSheet("""           
                                        QPushButton:hover {{
                                            image: url("{}/icons/open.png")
                                        }}
                                """.format(self.filePath))

        optimise_shelf_btn = ToolkitButton(icon_path=OPTIMISE_ICON_CONST.format(self.filePath),
                                           tool_tip=OPTIMISE_DESC_CONST)
        optimise_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=optimise_shelf_btn, widget=optimise_box))
        optimise_shelf_btn.double_clicked.connect(
            lambda: rgt.ToolWindow(tool="Optimise", parent=self, window=True, width=OPTIMISE_WIDTH_CONST,
                                   height=OPTIMISE_HEIGHT_CONST))
        tool_layout.addWidget(optimise_shelf_btn)
        optimise_shelf_btn.setStyleSheet("""           
                                                QPushButton:hover {{
                                                    image: url("{}/icons/open.png")
                                                }}
                                        """.format(self.filePath))

        matrix_shelf_btn = ToolkitButton(icon_path=MATRIX_ICON_CONST.format(self.filePath), tool_tip=MATRIX_DESC_CONST)
        matrix_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=matrix_shelf_btn, widget=matrix_box))
        matrix_shelf_btn.double_clicked.connect(
            lambda: rgt.ToolWindow(tool="Matrix", parent=self, window=True, width=MATRIX_WIDTH_CONST,
                                   height=MATRIX_HEIGHT_CONST))
        tool_layout.addWidget(matrix_shelf_btn)
        matrix_shelf_btn.setStyleSheet("""           
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
