import os

import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtCore, QtWidgets

import CETools.functions.matchmove as mmf
from CETools.windows.customWidgets import FlowLayout, GroupBox, ToolButton, ToolkitButton
import CETools.windows.matchmove.mmtools as mmt
from CETools.windows.matchmove.mmConstants import *
from CETools.functions.commonFunctions import refresh_dir


def add_shelf(self, shelf='CE Shelf'):
    def find_shelf(target_shelf):
        g_shelf = mel.eval("$temp = $gShelfTopLevel")
        shelves = cmds.tabLayout(g_shelf, q=1, childArray=1)  # similar method to finding viewport cam
        for i in shelves:
            if target_shelf in shelves:
                target_shelf = i
                return target_shelf
            else:
                return

    def add_shelf_buttons(maya_shelf, mode='add'):

        if mode == 'overwrite':
            buttons = cmds.shelfLayout(maya_shelf, q=1, childArray=1)
            for btn in buttons:
                cmds.deleteUI(btn, control=True)

        cmds.shelfButton('pointblast', parent=maya_shelf, label="Pointblast",
                         image=POINTBLAST_ICON_CONST.format(self.filePath),
                         annotation=POINTBLAST_DESC_CONST,
                         command="import CETools.functions.matchmove as mmf\nmmf.cam_focus_2d()")
        cmds.shelfButton('fastbake', parent=maya_shelf, label="Fast Bake",
                         image=FASTBAKE_ICON_CONST.format(self.filePath), annotation=FASTBAKE_DESC_CONST,
                         command="import CETools.functions.matchmove as mmf\nmmf.bake_selected(state='fast')")
        cmds.shelfButton('smartbake', parent=maya_shelf, label="Smart Bake",
                         image=SMARTBAKE_ICON_CONST.format(self.filePath),
                         annotation=SMARTBAKE_DESC_CONST,
                         command="import CETools.functions.matchmove as mmf\nmmf.bake_selected(state='smart')")
        cmds.shelfButton('snap', parent=maya_shelf, label="Snappy Snap",
                         image=SNAP_ICON_CONST.format(self.filePath), annotation=SNAP_DESC_CONST,
                         command="import CETools.functions.matchmove as mmf\nmmf.snap()")
        cmds.shelfButton('holdout', parent=maya_shelf, label="Holdout",
                         image=HOLDOUT_ICON_CONST.format(self.filePath), annotation=HOLDOUT_DESC_CONST,
                         command="import CETools.functions.matchmove as mmf\nmmf.holdout()")
        cmds.shelfButton('freshcam', parent=maya_shelf, label="Fresh Cam",
                         image=FRESHCAM_ICON_CONST.format(self.filePath), annotation=FRESHCAM_DESC_CONST,
                         command="import CETools.functions.matchmove as mmf\nmmf.duplicate_camera()")
        cmds.shelfButton('kuper', parent=maya_shelf, label="Kuper Export",
                         image=KUPER_ICON_CONST.format(self.filePath), annotation=KUPER_DESC_CONST,
                         command="import CETools.functions.matchmove as mmf\nmmf.kuper_main()")

        # BOILERPLATE CODE FOR EACH BUTTON, SUBSTITUTE WITH .FORMAT()
        tool_cmd = ("import CETools.windows.matchmove.tools.mmtools as mmt\n"
                    "from maya.OpenMayaUI import MQtUtil\n"
                    "from shiboken2 import wrapInstance\n"
                    "from PySide2.QtWidgets import QWidget\n"
                    "\n"
                    "\n"
                    "def maya_main_window():\n"
                    "    main_window_ptr = MQtUtil.mainWindow()\n"
                    "    return wrapInstance(int(main_window_ptr), QWidget)\n"
                    "\n"
                    "mmt.ToolWindow(tool=\"{}\",parent=maya_main_window(),window=True,width={},height={})\n")
        cmds.shelfButton('retime', parent=maya_shelf, label="Retime",
                         image=RETIME_ICON_CONST.format(self.filePath), annotation=RETIME_DESC_CONST,
                         command=tool_cmd.format("Retime", RETIME_WIDTH_CONST, RETIME_HEIGHT_CONST))
        cmds.shelfButton('zclean', parent=maya_shelf, label="zClean",
                         image=ZCLEAN_ICON_CONST.format(self.filePath), annotation=ZCLEAN_DESC_CONST,
                         command=tool_cmd.format("ZClean", ZCLEAN_WIDTH_CONST, ZCLEAN_HEIGHT_CONST))
        cmds.shelfButton('swapanim', parent=maya_shelf, label="Swap Anim",
                         image=SWAPANIM_ICON_CONST.format(self.filePath), annotation=SWAPANIM_DESC_CONST,
                         command=tool_cmd.format("SwapAnim", SWAPANIM_WIDTH_CONST, SWAPANIM_HEIGHT_CONST))
        cmds.shelfButton('conegenerator', parent=maya_shelf, label="Cone Generator",
                         image=CONES_ICON_CONST.format(self.filePath), annotation=CONES_DESC_CONST,
                         command=tool_cmd.format("ConeGenerator", CONES_WIDTH_CONST, CONES_HEIGHT_CONST))
        cmds.shelfButton('filmback', parent=maya_shelf, label="Film Back Correct",
                         image=FILMBACK_ICON_CONST.format(self.filePath), annotation=FILMBACK_DESC_CONST,
                         command=tool_cmd.format("FilmBack", FILMBACK_WIDTH_CONST, FILMBACK_HEIGHT_CONST))
        cmds.shelfButton('smoothanim', parent=maya_shelf, label="Smooth Anim",
                         image=SMOOTHANIM_ICON_CONST.format(self.filePath),
                         annotation=SMOOTHANIM_DESC_CONST,
                         command=tool_cmd.format("SmoothAnim", SMOOTHANIM_WIDTH_CONST,
                                                 SMOOTHANIM_HEIGHT_CONST))
        cmds.shelfButton('smartrename', parent=maya_shelf, label="Smart Rename",
                         image=RENAME_ICON_CONST.format(self.filePath), annotation=RENAME_DESC_CONST,
                         command=tool_cmd.format("Rename", RENAME_WIDTH_CONST, RENAME_HEIGHT_CONST))

    targetShelf = find_shelf(shelf)

    if targetShelf:
        add_shelf_buttons(shelf, mode='overwrite')

    if not targetShelf:
        shelfCommand = 'addNewShelfTab "{}";'.format(shelf)
        mel.eval(shelfCommand)
        targetShelf = find_shelf(shelf)
        if not targetShelf:
            cmds.warning("The shelves are fucked, I dunno what to tell you.")
            return
        add_shelf_buttons(shelf, mode='add')


def necessary_scripts(category='CE Matchmove'):
    if "CE_Hotkeys" not in cmds.hotkeySet(q=1, hotkeySetArray=1):
        print("CE Hotkeys does not exist, creating.")
        cmds.hotkeySet("CE_Hotkeys")
    cmds.hotkeySet(q=1, current=1)
    cmds.hotkeySet("CE_Hotkeys", e=1, current=1)

    add_script(name="CE_pointblast", function="import CETools.functions.matchmove as mmf; mmf.cam_focus_2d()",
               category=category)
    add_script(name="CE_snap", function="import CETools.functions.matchmove as mmf; mmf.snap()", category=category)
    add_script(name="CE_freshCam", function="import CETools.functions.matchmove as mmf; mmf.duplicate_camera()",
               category=category)
    add_script(name="CE_polyOnOff", function=("""import maya.cmds as cmds
def poly_toggle():
    viewPanels = cmds.getPanel(type='modelPanel')
    focus = cmds.getPanel(withFocus=True)
    for i in viewPanels:
        if i in focus:
            focus_panel = i
    result = cmds.modelEditor(focus_panel, q=True, pm=True)
    cmds.modelEditor(focus_panel, e=True, pm=not result)
poly_toggle()"""), category=category, hotkey='`')

    add_script(name="CE_curveOnOff", function=("""import maya.cmds as cmds
def curve_toggle():
    viewPanels = cmds.getPanel(type='modelPanel')
    focus = cmds.getPanel(withFocus=True)
    for i in viewPanels:
        if i in focus:
            focus_panel = i
    result = cmds.modelEditor(focus_panel, q=True, nc=True)
    cmds.modelEditor(focus_panel, e=True, nc=not result)
curve_toggle()"""), category=category, hotkey='c')

    add_script(name="CE_createLocator", function=("""import maya.cmds as cmds
import math

def get_current_manip():
    current_ctx = cmds.currentCtx(q=1)
    if cmds.superCtx(current_ctx, ex=1):
        ctx = cmds.superCtx(current_ctx, q=1)
        try:
            cmds.manipMoveContext(ctx, q=1, m=1)
        except RuntimeError:
            return None
        return ctx

def get_manip_xform(ctx):
    mode = cmds.manipMoveContext(ctx, q=1, m=1)
    pos = cmds.manipMoveContext(ctx, q=1, p=1)

    if mode == 10:
        rot = []
        radians = cmds.manipMoveContext(ctx, q=1, oa=1)
        for rad in radians:
            rot.append(math.degrees(rad))

    elif mode == 2:
        rot = (0.0, 0.0, 0.0)

    elif mode == 0:
        selected = cmds.ls(sl=1, o=1)
        if selected:
            sel = cmds.listRelatives(selected[0], p=1)
            rot = cmds.xform(sel, q=1, ro=1, ws=1)
        else:
            # If nothing selected, default to origin
            return (0, 0, 0), (0, 0, 0)

    return pos, rot
    
current_manip = get_current_manip()
if current_manip:
    t, ro = get_manip_xform(current_manip)
else:
    t, ro = (0,0,0), (0,0,0)
    
loc = cmds.spaceLocator()
cmds.xform(loc,t=t,ro=ro,ws=1)
    """), category=category, hotkey='l')
    add_script(name="CE_zDepth", function="""import maya.cmds as cmds
def screenManip(fromWhere=0):
    currentMode = cmds.manipMoveContext('Move', q=True ,mode=True)
    if currentMode==6 or fromWhere==1:
        currentPanel = cmds.getPanel(wf=True)
        type = cmds.getPanel(typeOf=currentPanel)
        if type=="modelPanel":
            camera = cmds.modelPanel(currentPanel,q=True, camera=True)
            loc=cmds.xform(camera,ws=True, q=True ,t=True)
            cmds.manipMoveContext('Move',e=True,mode=6,ah=0,ot=loc)
    if currentMode==6 and fromWhere==1:
        cmds.manipMoveContext('Move', e=True ,mode=2)
screenManip(1)""", category=category, hotkey='1', ctrl=True)

    cmds.savePrefs(hotkeys=True)
    print(
        "All necessary scripts have been added! Assign a hotkey in Maya's Hotkey Editor under Custom Scripts > CE "
        "Matchmove")


def add_script(name='', function='', category='', hotkey=None, ctrl=False, alt=False, shift=False):
    if not cmds.runTimeCommand(name, q=1, exists=1):
        cmds.runTimeCommand(name, category=category, annotation=name, command=function, commandLanguage='python')
        cmds.nameCommand(name, annotation=name, command=name)
        print("{} has been added as a named command under Custom Scripts > CE Matchmove".format(name))

    if hotkey:

        button_text = "("

        if ctrl:
            button_text += "Ctrl+"
        if alt:
            button_text += "Alt+"
        if shift:
            button_text += "Shift+"

        button_text += hotkey.upper() + ")"

        if cmds.hotkey(hotkey, q=1, alt=alt, ctl=ctrl, sht=shift):
            cmds.hotkey(k=hotkey, alt=alt, ctl=ctrl, sht=shift, name=name)
            print("{} {}: Hotkey has been assigned.".format(name, button_text))

        else:

            print("{} {}: Hotkey is already in use, will need to be manually assigned.".format(name, button_text))


def scale_buttons(layout, factor=0):
    for i in range(layout.count()):
        widget = layout.itemAt(i).widget()
        if isinstance(widget, QtWidgets.QPushButton):
            size = str(widget.iconSize())
            size = size.split("(")[-1]
            size = int(size.split(",")[0])
            newSize = size + factor * 2
            if 50 <= newSize <= 100:
                widget.setIconSize(QtCore.QSize(newSize, newSize))


def toggle_visibility(layout, button, widget):
    if button.isChecked():
        layout.removeWidget(widget)
        button.setEnabled(False)
        widget.hide()

    else:
        layout.addWidget(widget)
        button.setEnabled(True)
        widget.show()


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
        self.setWindowTitle("CE Matchmove Toolkit")
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

        add_scripts_menu = QtWidgets.QAction("Add necessary scripts", self)
        add_scripts_menu.triggered.connect(lambda x: necessary_scripts(category="CE Matchmove"))

        add_shelf_menu = QtWidgets.QAction("Create CE Matchmove shelf", self)
        add_shelf_menu.triggered.connect(lambda x: add_shelf(self, shelf="CE_Matchmove"))

        workspace_menu.addAction(refresh_dir_menu)
        workspace_menu.addAction(add_scripts_menu)
        workspace_menu.addAction(add_shelf_menu)

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

        retime_box = GroupBox(name="Retime".upper(), is_open=True)
        retime_layout = QtWidgets.QGridLayout()
        retime_box.vbox.addLayout(retime_layout)
        retime_widget = mmt.RetimeWidget(parent=self, tool_layout=retime_layout, dir_path=scene_directory)
        retime_widget.hide()
        text_fields = retime_widget.dir_input

        reverse_box = GroupBox(name="Swap Anim".upper(), is_open=True)
        reverse_layout = QtWidgets.QGridLayout()
        reverse_box.vbox.addLayout(reverse_layout)
        swap_anim_widget = mmt.SwapAnimWidget(parent=self, tool_layout=reverse_layout, dir_path=scene_directory)
        swap_anim_widget.hide()

        cone_box = GroupBox(name="Cone Generator".upper(), is_open=True)
        cone_layout = QtWidgets.QGridLayout()
        cone_box.vbox.addLayout(cone_layout)
        cone_generator_widget = mmt.ConeGeneratorWidget(parent=self, tool_layout=cone_layout, dir_path=scene_directory)
        cone_generator_widget.hide()

        filmback_box = GroupBox(name="Film Back Correct".upper(), is_open=True)
        filmback_layout = QtWidgets.QGridLayout()
        filmback_box.vbox.addLayout(filmback_layout)
        film_back_widget = mmt.FilmBackWidget(parent=self, tool_layout=filmback_layout, dir_path=scene_directory)
        film_back_widget.hide()
        text_fields.append(film_back_widget.dir_input)

        z_clean_box = GroupBox(name="zClean".upper(), is_open=True)
        z_clean_layout = QtWidgets.QGridLayout()
        z_clean_box.vbox.addLayout(z_clean_layout)
        z_clean_widget = mmt.ZCleanWidget(parent=self, tool_layout=z_clean_layout, dir_path=scene_directory)
        z_clean_widget.hide()

        smooth_anim_box = GroupBox(name="Smooth Anim".upper(), is_open=True)
        smooth_anim_layout = QtWidgets.QGridLayout()
        smooth_anim_box.vbox.addLayout(smooth_anim_layout)
        smooth_anim_widget = mmt.SmoothAnimWidget(parent=self, tool_layout=smooth_anim_layout, dir_path=scene_directory)
        smooth_anim_widget.hide()

        rename_box = GroupBox(name="Smart Rename".upper(), is_open=True)
        rename_layout = QtWidgets.QGridLayout()
        rename_box.vbox.addLayout(rename_layout)
        rename_widget = mmt.RenameWidget(parent=self, tool_layout=rename_layout, dir=scene_directory)
        rename_widget.hide()

        page_layout.addWidget(common_box)

        # COMMON BUTTONS

        tool_layout = FlowLayout()
        tool_layout.setSpacing(0)
        vc_box.addLayout(tool_layout)

        cam_focus_btn = ToolButton(icon_path=POINTBLAST_ICON_CONST.format(self.filePath),
                                   tool_tip=POINTBLAST_DESC_CONST)
        cam_focus_btn.clicked.connect(lambda: mmf.cam_focus_2d())
        tool_layout.addWidget(cam_focus_btn)

        fast_bake_btn = ToolButton(icon_path=FASTBAKE_ICON_CONST.format(self.filePath), tool_tip=FASTBAKE_DESC_CONST)
        fast_bake_btn.clicked.connect(lambda: mmf.bake_selected(state='fast'))
        tool_layout.addWidget(fast_bake_btn)

        smart_bake_btn = ToolButton(icon_path=SMARTBAKE_ICON_CONST.format(self.filePath),
                                    tool_tip=SMARTBAKE_DESC_CONST)
        smart_bake_btn.clicked.connect(lambda: mmf.bake_selected(state='smart'))
        tool_layout.addWidget(smart_bake_btn)

        snap_btn = ToolButton(icon_path=SNAP_ICON_CONST.format(self.filePath), tool_tip=SNAP_DESC_CONST)
        snap_btn.clicked.connect(lambda: mmf.snap())
        tool_layout.addWidget(snap_btn)

        holdout_btn = ToolButton(icon_path=HOLDOUT_ICON_CONST.format(self.filePath), tool_tip=HOLDOUT_DESC_CONST)
        holdout_btn.clicked.connect(lambda: mmf.holdout())
        tool_layout.addWidget(holdout_btn)

        fresh_cam_btn = ToolButton(icon_path=FRESHCAM_ICON_CONST.format(self.filePath), tool_tip=FRESHCAM_DESC_CONST)
        fresh_cam_btn.clicked.connect(lambda: mmf.duplicate_camera())
        tool_layout.addWidget(fresh_cam_btn)

        kuper_btn = ToolButton(icon_path=KUPER_ICON_CONST.format(self.filePath), tool_tip=KUPER_DESC_CONST)
        kuper_btn.clicked.connect(lambda: mmf.kuper_main())
        tool_layout.addWidget(kuper_btn)

        retime_shelf_btn = ToolkitButton(icon_path=RETIME_ICON_CONST.format(self.filePath), tool_tip=RETIME_DESC_CONST)
        retime_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=retime_shelf_btn, widget=retime_box))
        retime_shelf_btn.double_clicked.connect(
            lambda: mmt.ToolWindow(tool="Retime", parent=self, window=True, width=RETIME_WIDTH_CONST,
                                   height=RETIME_HEIGHT_CONST))

        tool_layout.addWidget(retime_shelf_btn)
        retime_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))
        z_clean_btn = ToolkitButton(icon_path=ZCLEAN_ICON_CONST.format(self.filePath), tool_tip=ZCLEAN_DESC_CONST)
        z_clean_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=z_clean_btn, widget=z_clean_box))
        z_clean_btn.double_clicked.connect(
            lambda: mmt.ToolWindow(tool="ZClean", parent=self, window=True, width=ZCLEAN_WIDTH_CONST,
                                   height=ZCLEAN_HEIGHT_CONST))

        tool_layout.addWidget(z_clean_btn)
        z_clean_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        reverse_shelf_btn = ToolkitButton(icon_path=SWAPANIM_ICON_CONST.format(self.filePath),
                                          tool_tip=SWAPANIM_DESC_CONST)
        reverse_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=reverse_shelf_btn, widget=reverse_box))
        reverse_shelf_btn.double_clicked.connect(
            lambda: mmt.ToolWindow(tool="SwapAnim", parent=self, window=True, width=SWAPANIM_WIDTH_CONST,
                                   height=SWAPANIM_HEIGHT_CONST))

        tool_layout.addWidget(reverse_shelf_btn)
        reverse_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        cones_shelf_btn = ToolkitButton(icon_path=CONES_ICON_CONST.format(self.filePath), tool_tip=CONES_DESC_CONST)
        cones_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=cones_shelf_btn, widget=cone_box))
        cones_shelf_btn.double_clicked.connect(
            lambda: mmt.ToolWindow(tool="ConeGenerator", parent=self, window=True, width=CONES_WIDTH_CONST,
                                   height=CONES_HEIGHT_CONST))

        tool_layout.addWidget(cones_shelf_btn)
        cones_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        filmback_shelf_btn = ToolkitButton(icon_path=FILMBACK_ICON_CONST.format(self.filePath),
                                           tool_tip=FILMBACK_DESC_CONST)
        filmback_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=filmback_shelf_btn,
                                      widget=filmback_box))
        filmback_shelf_btn.double_clicked.connect(
            lambda: mmt.ToolWindow(tool="FilmBack", parent=self, window=True, width=FILMBACK_WIDTH_CONST,
                                   height=FILMBACK_HEIGHT_CONST))

        tool_layout.addWidget(filmback_shelf_btn)
        filmback_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        smooth_anim_shelf_btn = ToolkitButton(icon_path=SMOOTHANIM_ICON_CONST.format(self.filePath),
                                              tool_tip=SMOOTHANIM_DESC_CONST)
        smooth_anim_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=smooth_anim_shelf_btn,
                                      widget=smooth_anim_box))
        smooth_anim_shelf_btn.double_clicked.connect(
            lambda: mmt.ToolWindow(tool="SmoothAnim", parent=self, window=True, width=SMOOTHANIM_WIDTH_CONST,
                                   height=SMOOTHANIM_HEIGHT_CONST))

        tool_layout.addWidget(smooth_anim_shelf_btn)
        smooth_anim_shelf_btn.setStyleSheet("""           
                QPushButton:hover {{
                    image: url("{}/icons/open.png")
                }}
        """.format(self.filePath))

        rename_shelf_btn = ToolkitButton(icon_path=RENAME_ICON_CONST.format(self.filePath), tool_tip=RENAME_DESC_CONST)
        rename_shelf_btn.left_clicked.connect(
            lambda: toggle_visibility(layout=page_layout, button=rename_shelf_btn, widget=rename_box))
        rename_shelf_btn.double_clicked.connect(
            lambda: mmt.ToolWindow(tool="Rename", parent=self, window=True, width=RENAME_WIDTH_CONST,
                                   height=RENAME_HEIGHT_CONST))

        tool_layout.addWidget(rename_shelf_btn)
        rename_shelf_btn.setStyleSheet("""           
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
