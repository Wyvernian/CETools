import os
from maya import OpenMayaUI as omui
from PySide2 import QtCore, QtGui, QtWidgets, __version__
from shiboken2 import wrapInstance
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from CETools.windows.customWidgets import FlowLayout
import CETools.windows.toolkitWindow as tool_win
import CETools.windows.lookdev.ldtools as ldt
import CETools.windows.rigging.rgtools as rgt
import CETools.windows.modelling.mdtools as mdt
import CETools.windows.matchmove.mmtools as mmt
import CETools.windows.rendering.rdtools as rdt


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class MainWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super().__init__(parent)

        self.scroll = None
        self.winLayout = None
        self.fileName = os.path.basename(__file__)
        self.filePath = os.path.dirname(__file__)
        self.imageDir = os.path.join(self.filePath, 'images', 'icons')
        self.bannerDir = os.path.join(self.filePath, 'images')
        self.build_win()

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        height = self.frameGeometry().height()
        if height > 375:
            self.winLayout.setContentsMargins(10, 200, 5, 5)
        else:
            self.winLayout.setContentsMargins(10, height - 175, 5, 5)
            self.scroll.setMinimumHeight(height - 210)

    def build_win(self):
        self.setWindowTitle("CE Tools")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.setMinimumWidth(105)
        self.setMinimumHeight(90)
        self.resize(190, 450)

        win_con = QtWidgets.QWidget(self)
        self.winLayout = QtWidgets.QVBoxLayout(self)

        container = QtWidgets.QWidget(win_con)
        self.scroll = QtWidgets.QScrollArea()  # Scroll Area which contains the widgets, set as the centralWidget

        page_layout = FlowLayout(container)

        self.scroll.setWidget(container)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)

        self.winLayout.addWidget(self.scroll)
        self.winLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.winLayout.setContentsMargins(10, 5, 5, 5)

        tools_mapping = {
            "Matchmove": {
                "Pointblast": mmt.Pointblast,
                "Fresh Cam": mmt.FreshCam,
                "Holdout": mmt.Holdout,
                "Fast Bake": mmt.FastBake,
                "Smart Bake": mmt.SmartBake,
                "Kuper Export": mmt.KuperExport,
                "Cone Generator": mmt.ConeGenerator,
                "Smooth Anim": mmt.SmoothAnim,
                "Retime": mmt.Retime,
                "Filmback Correct": mmt.FilmBackCorrect,
                "ZClean": mmt.ZClean,
                "Swap Anim": mmt.SwapAnim,
            },
            "Modelling": {
                "Move To Pivot": mdt.MoveToPivot,
                "Select Holes": mdt.BorderEdges,
                "Copy UV": mdt.CopyUV,
                "Rotate": mdt.Rotate,
                "Quick Mirror": mdt.QuickMirror,
                "Stamp": mdt.StampModel,
                "Mesh Clean": mdt.MeshClean,
            },
            "Rigging": {
                "Curve Creator": rgt.CurveCreator,
                "Color Palette": rgt.Palette,
                "Joint Tools": rgt.JointTools,
                "Ai Color Attribute": rgt.AiColorAttribute,
                "Cluster Tools": rgt.ClusterTools,
                "Optimise Rig": rgt.OptimiseRig,
                "Matrix Rigging": rgt.MatrixRigging,
                "Rig Presets": rgt.RigPreset,
                "Smart Rename": mmt.SmartRename,
            },
            "Look Dev": {
                "Write Shader Connections": ldt.WriteShaderConnections,
                "Create Standard Material": ldt.CreateStandardMaterial,
                "Create Render Balls": ldt.CreateRenderBalls,
                "Assign By Name": ldt.AssignByName,
                "HDRI Creator": ldt.HDRICreator,
                "Turntable": ldt.Turntable,
                "Texture Link": ldt.TextureLink,
            },
            "Rendering": {
                "Overscan": rdt.Overscan,
            },
        }

        buttons = {
            "matchmove": {
                "click_command": lambda x: tool_win.load_window(name='CE Matchmove Toolkit',
                                                                default_tools=tools_mapping['Matchmove'].keys(),
                                                                image_path=self.imageDir,
                                                                tools_mapping=tools_mapping),
            },
            "modelling": {
                "click_command": lambda x: tool_win.load_window(name='CE Modelling Toolkit',
                                                                default_tools=tools_mapping['Modelling'].keys(),
                                                                image_path=self.imageDir,
                                                                tools_mapping=tools_mapping),
            },
            "rigging": {
                "click_command": lambda x: tool_win.load_window(name='CE Rigging Toolkit',
                                                                default_tools=tools_mapping['Rigging'].keys(),
                                                                image_path=self.imageDir,
                                                                tools_mapping=tools_mapping),
            },
            "animation": {
                "click_command": lambda x: tool_win.load_window(name='CE Animation Toolkit',
                                                                default_tools=tools_mapping['Animation'].keys(),
                                                                image_path=self.imageDir,
                                                                tools_mapping=tools_mapping),
            },
            "look dev": {
                "click_command": lambda x: tool_win.load_window(name='CE Look Dev Toolkit',
                                                                default_tools=tools_mapping['Look Dev'].keys(),
                                                                image_path=self.imageDir,
                                                                tools_mapping=tools_mapping),
            },
            "rendering": {
                "click_command": lambda x: tool_win.load_window(name='CE Rendering Toolkit',
                                                                default_tools=tools_mapping['Rendering'].keys(),
                                                                image_path=self.imageDir,
                                                                tools_mapping=tools_mapping),
            },
            "custom": {
                "click_command": (lambda x: tool_win.load_window(name='CE Custom Toolkit', image_path=self.imageDir, tools_mapping=tools_mapping))
            },
        }

        for button_name in buttons.keys():
            btn = QtWidgets.QPushButton(button_name.upper())
            btn.clicked.connect(buttons[button_name]['click_command'])
            btn.setFixedSize(75, 75)
            btn.setEnabled(True)
            page_layout.addWidget(btn)

        import CETools.windows.main_ss as ss
        ss.setStylesheet(self, self.bannerDir)
