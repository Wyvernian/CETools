import os
import subprocess

from PySide2 import QtCore, QtGui, QtWidgets
import maya.cmds as cmds

import CETools.functions.matchmove as mmf
from CETools.windows.toolkitWindow import Toolkit, SimpleTool


def set_dir(self, filepath="/home", text_field=None, text='', file_type="EXR files (*.exr)"):
    file_directory = QtWidgets.QFileDialog.getOpenFileName(self, text,
                                                           filepath,
                                                           file_type)[0]

    if file_directory:
        text_field.setText(file_directory)
        print(file_directory)


def set_text_field(target):
    sel = cmds.ls(sl=1, l=1) or ['']
    target.setText(sel[0])


def flip_text_field(target_a, target_b):
    target_a_text = target_a.text()
    target_b_text = target_b.text()
    target_b.setText(target_a_text)
    target_a.setText(target_b_text)


def move_ui(self):
    pos = QtGui.QCursor.pos()
    self.move(pos.x() + 20, pos.y() + 15)


class Pointblast(SimpleTool):
    def __init__(self):
        super().__init__(name='Pointblast', icon_path='pointblast.png',
                         tool_tip="Select an object to focus on in 2D\nthrough the current viewport "
                                  "camera.\nLeft-Click to toggle on/off in the camera.",
                         on_click_function=lambda: mmf.cam_focus_2d())


class FastBake(SimpleTool):
    def __init__(self):
        super().__init__(name='Fast Bake', icon_path='fastbake.png',
                         tool_tip="Bake Animation Faster",
                         on_click_function=lambda: mmf.bake_selected(state='fast'))


class SmartBake(SimpleTool):
    def __init__(self):
        super().__init__(name='Fast Bake', icon_path='smartbake.png',
                         tool_tip="Bake Animation Smarter",
                         on_click_function=lambda: mmf.bake_selected(state='smart'))


class Holdout(SimpleTool):
    def __init__(self):
        super().__init__(name='Holdout', icon_path='holdout.png',
                         tool_tip="Toggle useBackground visibility on selected objects",
                         on_click_function=lambda: mmf.holdout())


class FreshCam(SimpleTool):
    def __init__(self):
        super().__init__(name='Fresh Cam', icon_path='freshcam.png',
                         tool_tip="Select a camera and duplicate\nit with all_objects data, minty fresh.",
                         on_click_function=lambda: mmf.duplicate_camera())


class KuperExport(SimpleTool):
    def __init__(self):
        super().__init__(name='Kuper Export', icon_path='kuper.png',
                         tool_tip="Exports a selected camera as a kuper file. If this tool was\nmade by a certain 'Kuper', your code sucks and I had to rewrite it.",
                         on_click_function=lambda: mmf.kuper_main())


class Retime(Toolkit):

    def __init__(self):
        super().__init__(name='Retime', icon_path='retime.png',
                         tool_tip="Open Retime Toolbox: \nRetime tracking and camera data\nwith a valid ASCII retime file\nand retimed image sequence.",
                         toolbox_function=self.RetimeWidget)

    class RetimeWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.dir_input = []
            self.build_ui()

        def build_ui(self):
            #######
            top_layout = QtWidgets.QGridLayout()

            retime_dir = QtWidgets.QLineEdit(self.dir_path)
            self.dir_input.append(retime_dir)
            retime_dir.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Retime File:"), 0, 0)
            top_layout.addWidget(retime_dir, 0, 1)

            sequence_dir = QtWidgets.QLineEdit(self.dir_path)
            self.dir_input.append(sequence_dir)
            sequence_dir.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Retimed Sequence:"), 1, 0)
            top_layout.addWidget(sequence_dir, 1, 1)

            sel = cmds.ls(sl=1, l=1) or ['persp']
            camera = QtWidgets.QLineEdit(sel[0])
            camera.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Camera:"), 2, 0)
            top_layout.addWidget(camera, 2, 1)

            options_layout = QtWidgets.QVBoxLayout()

            overwrite_btn = QtWidgets.QRadioButton("Overwrite frame range from Retime File")
            options_layout.addWidget(overwrite_btn)
            overwrite_btn.setChecked(True)

            insert_btn = QtWidgets.QRadioButton("Insert into Maya playback range")
            options_layout.addWidget(insert_btn)
            insert_btn.setChecked(False)

            reverse_btn = QtWidgets.QCheckBox("Reverse ASCII read order")
            options_layout.addWidget(reverse_btn)
            reverse_btn.setChecked(False)

            retime_btn = QtWidgets.QPushButton("Retime Camera")
            retime_btn.clicked.connect(
                lambda x: mmf.run_retime(retime_path=retime_dir.text(), camera=camera.text(),
                                         sequence_path=sequence_dir.text(),
                                         overwrite=overwrite_btn.isChecked(), insert=insert_btn.isChecked(),
                                         reverse_order=reverse_btn.isChecked()))
            retime_btn.setFixedHeight(25)
            options_layout.addWidget(retime_btn)

            retime_folder = QtWidgets.QPushButton()
            retime_folder.clicked.connect(lambda x: subprocess.Popen(['xdg-open', retime_dir.text()]))
            retime_folder.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
            retime_folder.setFixedSize(20, 20)
            retime_folder.setToolTip("View Retime File/Directory")
            top_layout.addWidget(retime_folder, 3, 2)

            cam_select = QtWidgets.QPushButton()
            cam_select.clicked.connect(lambda x: set_text_field(target=camera))
            cam_select.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
            cam_select.setFixedSize(20, 20)
            cam_select.setToolTip("Update camera selection")
            top_layout.addWidget(cam_select, 2, 2)

            retime_select = QtWidgets.QPushButton()
            retime_select.setFixedSize(20, 20)
            retime_select.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirLinkIcon))
            retime_select.clicked.connect(
                lambda x: set_dir(self, retime_dir.text() or self.dir_path or '', retime_dir, 'Select Retime File',
                                  "ASCII files (*.ascii);; All Files (*.*)"))
            retime_select.setToolTip("Select File")
            top_layout.addWidget(retime_select, 0, 2)

            sequence_select = QtWidgets.QPushButton()
            sequence_select.setFixedSize(20, 20)
            sequence_select.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirLinkIcon))
            sequence_select.clicked.connect(
                lambda x: set_dir(self, sequence_dir.text() or self.dir_path or '', sequence_dir,
                                  'Select Retimed Sequence',
                                  "EXR files (*.exr);; All Files (*.*)"))
            sequence_select.setToolTip("Select File")
            top_layout.addWidget(sequence_select, 1, 2)

            # Add to tool box layout
            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)


class ZClean(Toolkit):

    def __init__(self):
        super().__init__(name='ZClean', icon_path='zclean.png',
                         tool_tip="Open zClean Toolbox:\nCreates a distance locator on the target object to allow\nadjustments to its zdepth in a camera's XY space.",
                         toolbox_function=self.ZCleanWidget)

    class ZCleanWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir = dir_path
            self.build_ui()

        def build_ui(self):
            top_layout = QtWidgets.QGridLayout()
            z_host = QtWidgets.QLineEdit()
            z_host.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Camera: "), 0, 0)
            top_layout.addWidget(z_host, 0, 1)

            z_target = QtWidgets.QLineEdit()
            z_target.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Target Object: "), 1, 0)
            top_layout.addWidget(z_target, 1, 1)

            optionsLayout = QtWidgets.QGridLayout()

            clean_btn = QtWidgets.QPushButton("zClean")
            clean_btn.clicked.connect(lambda x: mmf.z_constrain(src_obj=z_host.text(), dest_obj=z_target.text()))
            clean_btn.setFixedHeight(25)
            optionsLayout.addWidget(clean_btn, 0, 0)

            z_bake_btn = QtWidgets.QPushButton("Bake")
            z_bake_btn.clicked.connect(lambda x: mmf.z_bake(dest_obj=z_target.text()))
            z_bake_btn.setFixedHeight(25)
            optionsLayout.addWidget(z_bake_btn, 0, 1)

            update_cam_btn = QtWidgets.QPushButton()
            update_cam_btn.clicked.connect(lambda x: set_text_field(target=z_host))
            update_cam_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
            update_cam_btn.setFixedSize(20, 20)
            update_cam_btn.setToolTip("Update camera selection")
            top_layout.addWidget(update_cam_btn, 0, 2)

            update_object_btn = QtWidgets.QPushButton()
            update_object_btn.clicked.connect(lambda x: set_text_field(target=z_target))
            update_object_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
            update_object_btn.setFixedSize(20, 20)
            update_object_btn.setToolTip("Update target selection")
            top_layout.addWidget(update_object_btn, 1, 2)

            # Add to tool box layout
            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(optionsLayout, 1, 0)


class SwapAnim(Toolkit):

    def __init__(self):
        super().__init__(name='Swap Animation', icon_path='swapanim.png',
                         tool_tip="Open Swap Anim Toolbox:\nCopies and inverts all_objects animation from\nthe animated object to the target object.",
                         toolbox_function=self.SwapAnimWidget)

    class SwapAnimWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir = dir_path
            self.build_ui()

        def run_invert(self, host, target):
            mmf.invert_anim(host=host.text(), target=target.text())
            flip_text_field(target_a=host, target_b=target)

        def build_ui(self):
            top_layout = QtWidgets.QGridLayout()
            host = QtWidgets.QLineEdit()
            host.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Animated Object: "), 0, 0)
            top_layout.addWidget(host, 0, 1)

            target = QtWidgets.QLineEdit()
            target.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Target Object: "), 1, 0)
            top_layout.addWidget(target, 1, 1)

            options_layout = QtWidgets.QVBoxLayout()

            reverse_btn = QtWidgets.QPushButton("Reverse Animation")
            reverse_btn.clicked.connect(lambda x: run_invert(self, target=target, host=host))
            reverse_btn.setFixedHeight(25)
            options_layout.addWidget(reverse_btn)

            update_anim_object_btn = QtWidgets.QPushButton()
            update_anim_object_btn.clicked.connect(lambda x: set_text_field(target=host))
            update_anim_object_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
            update_anim_object_btn.setFixedSize(20, 20)
            update_anim_object_btn.setToolTip("Update animated object selection")
            top_layout.addWidget(update_anim_object_btn, 0, 2)

            update_target_btn = QtWidgets.QPushButton()
            update_target_btn.clicked.connect(lambda x: set_text_field(target=target))
            update_target_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowLeft))
            update_target_btn.setFixedSize(20, 20)
            update_target_btn.setToolTip("Update target selection")
            top_layout.addWidget(update_target_btn, 1, 2)

            swap_btn = QtWidgets.QPushButton()
            swap_btn.clicked.connect(lambda x: flip_text_field(target_a=host, target_b=target))
            swap_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
            swap_btn.setFixedSize(20, 20)
            swap_btn.setToolTip("Reverse Selections")
            top_layout.addWidget(swap_btn, 2, 2)

            # Add to tool box layout

            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)


class ConeGenerator(Toolkit):

    def __init__(self):
        super().__init__(name='Cone Generator', icon_path='cones.png',
                         tool_tip="Open Cone Generator Toolbox:\nCreates cones at selected objects and stores\nthem in 'Track Cones' group. Cones can be\nscaled linearly or by distance from the camera.",
                         toolbox_function=self.ConeGeneratorWidget)

    class ConeGeneratorWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir = dir_path
            self.build_ui()

        def build_ui(self):
            cone_top_layout = QtWidgets.QGridLayout()
            cone_scale_layout = QtWidgets.QGridLayout()
            cone_scale_layout.setSpacing(3)

            create_cone_btn = QtWidgets.QPushButton("Create Cones")
            create_cone_btn.clicked.connect(lambda x: mmf.create_cones_at_pivots())
            create_cone_btn.setFixedHeight(25)
            cone_top_layout.addWidget(create_cone_btn, 0, 0)

            select_cone_btn = QtWidgets.QPushButton("Select Cones")
            select_cone_btn.clicked.connect(lambda x: mmf.select_cones())
            select_cone_btn.setFixedHeight(25)
            cone_top_layout.addWidget(select_cone_btn, 0, 1)

            subtract_cone_a = QtWidgets.QPushButton("-0.5")
            subtract_cone_a.clicked.connect(lambda x: mmf.scale_cones(factor=-0.5))
            subtract_cone_a.setFixedSize(25, 25)
            cone_scale_layout.addWidget(subtract_cone_a, 0, 0)

            subtract_cone_b = QtWidgets.QPushButton("-1")
            subtract_cone_b.clicked.connect(lambda x: mmf.scale_cones(factor=-1))
            subtract_cone_b.setFixedSize(25, 25)
            cone_scale_layout.addWidget(subtract_cone_b, 0, 1)

            add_cone_a = QtWidgets.QPushButton("+0.5")
            add_cone_a.clicked.connect(lambda x: mmf.scale_cones(factor=0.5))
            add_cone_a.setFixedSize(25, 25)
            cone_scale_layout.addWidget(add_cone_a, 0, 2)

            add_cone_b = QtWidgets.QPushButton("+1")
            add_cone_b.clicked.connect(lambda x: mmf.scale_cones(factor=1))
            add_cone_b.setFixedSize(25, 25)
            cone_scale_layout.addWidget(add_cone_b, 0, 3)

            label = QtWidgets.QLabel("SCALE:")
            cam_cone_scale = QtWidgets.QDoubleSpinBox()
            cam_cone_scale.setSingleStep(0.1)
            cam_cone_scale.setValue(0.2)
            cone_scale_layout.addWidget(label, 0, 4)
            cone_scale_layout.addWidget(cam_cone_scale, 0, 5)

            cone_scale = QtWidgets.QPushButton("CAM")
            cone_scale.clicked.connect(lambda x: mmf.cam_depth(size=cam_cone_scale.value()))
            cone_scale.setFixedSize(40, 25)
            cone_scale_layout.addWidget(cone_scale, 0, 6)

            # Add to tool box layout
            self.tool_layout.addLayout(cone_top_layout, 0, 0)
            self.tool_layout.addLayout(cone_scale_layout, 1, 0)


class FilmBackCorrect(Toolkit):

    def __init__(self):
        super().__init__(name='Filmback Correct', icon_path='filmback.png',
                         tool_tip="Open Film Back Correct Toolbox:\nReplace distorted image sequence in viewport\ncamera with an undistorted sequence.",
                         toolbox_function=self.FilmBackWidget)

    class FilmBackWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.tool_layout = tool_layout
            self.dir_path = dir_path
            self.build_ui()

        def build_ui(self):
            top_layout = QtWidgets.QGridLayout()
            options_layout = QtWidgets.QGridLayout()

            film_back_dir = QtWidgets.QLineEdit(self.dir_path)
            film_back_dir.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            top_layout.addWidget(QtWidgets.QLabel("Undistorted Seq. :"), 0, 0)
            top_layout.addWidget(film_back_dir, 0, 1)

            file_select = QtWidgets.QPushButton()
            file_select.setFixedSize(20, 20)
            file_select.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirLinkIcon))
            file_select.clicked.connect(
                lambda x: set_dir(
                    self, film_back_dir.text() or self.dir_path or '', film_back_dir, 'Select Undistorted Sequence')
            )
            file_select.setToolTip("Select File")
            top_layout.addWidget(file_select, 0, 2)

            film_back_btn = QtWidgets.QPushButton("Adjust Film Back in Viewport Camera")
            film_back_btn.clicked.connect(lambda x: mmf.filmback_correct(file=film_back_dir.text(), pixel_aspect=1))
            film_back_btn.setFixedHeight(25)
            options_layout.addWidget(film_back_btn)

            # Add to tool box layout

            self.tool_layout.addLayout(top_layout, 0, 0)
            self.tool_layout.addLayout(options_layout, 1, 0)


class SmoothAnim(Toolkit):

    def __init__(self):
        super().__init__(name='Smooth Anim', icon_path='smoothanim.png',
                         tool_tip="Open Retime Toolbox: \nRetime tracking and camera data\nwith a valid ASCII retime file\nand retimed image sequence.",
                         toolbox_function=self.SmoothAnimWidget)

    class SmoothAnimWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.toolLayout = tool_layout
            self.dir = dir_path
            self.build_ui()

        def build_ui(self):
            self.smoothTopLayout = QtWidgets.QGridLayout()
            self.smoothOptionLayout = QtWidgets.QGridLayout()
            self.smoothOptionLayout.setSpacing(5)

            self.smoothZBtn = QtWidgets.QPushButton("Smooth")
            self.smoothZBtn.clicked.connect(
                lambda x: mmf.z_smooth(samples=smoothSamples.value(), rate=smoothRate.value(),
                                       iterations=smoothIterations.value()))
            self.smoothZBtn.setFixedHeight(25)
            self.smoothTopLayout.addWidget(self.smoothZBtn, 0, 3)

            label = QtWidgets.QLabel("Samples:")
            label.setToolTip("Amount of values to sample on either side of each key.")
            smoothSamples = QtWidgets.QSpinBox()
            smoothSamples.setValue(2)
            self.smoothOptionLayout.addWidget(label, 0, 0)
            self.smoothOptionLayout.addWidget(smoothSamples, 0, 1)

            label = QtWidgets.QLabel("Sampling Rate:")
            label.setToolTip("Distance between each sampled value in the timeline.")
            smoothRate = QtWidgets.QDoubleSpinBox()
            smoothRate.setValue(1)
            smoothRate.setSingleStep(0.1)
            self.smoothOptionLayout.addWidget(label, 1, 0)
            self.smoothOptionLayout.addWidget(smoothRate, 1, 1)

            label = QtWidgets.QLabel("Iterations:")
            label.setToolTip("Amount of smoothing operations to perform.")
            smoothIterations = QtWidgets.QSpinBox()
            smoothIterations.setValue(5)
            self.smoothOptionLayout.addWidget(label, 2, 0)
            self.smoothOptionLayout.addWidget(smoothIterations, 2, 1)

            ## Add to tool box layout
            self.toolLayout.addLayout(self.smoothTopLayout, 1, 0)
            self.toolLayout.addLayout(self.smoothOptionLayout, 0, 0)


class SmartRename(Toolkit):

    def __init__(self):
        super().__init__(name='Smart Rename', icon_path='rename.png',
                         tool_tip="Open Smart Rename Toolbox:\nRename selected objects or\nhierarchies in the outliner.",
                         toolbox_function=self.RenameWidget)

    class RenameWidget(QtWidgets.QWidget):
        def __init__(self, parent, tool_layout=None, dir_path=''):
            super().__init__(parent)

            self.toolLayout = tool_layout
            self.dir_path = dir_path
            self.buildUI()

        def update_preview(self):

            '''
            prefix_field=self.prefix
            name_field=self.name
            suffix_field=self.suffix
            pad_index_field=self.pad_index
            padding_field=self.padding
            smartSuffixTogle = self.smart_suffix
            letterSuffixToggle = self.letter_suffix
            '''
            self.name.setText(self.name.text().replace(' ', '_'))

            ## SUFFIX CODE
            if not self.prefix.isEnabled():
                prefix = "(objPrefix)_"
            else:
                prefix = self.prefix.text() + '_'

            if self.prefix.text() == '':
                prefix = ''

            name = (self.name.text()) if self.name.isEnabled() else '(objName)'

            ## SUFFIX CODE
            if not self.suffix.isEnabled():
                suffix = "_(objSuffix)"
            elif self.smartSuffix.isChecked():
                suffix = "_(objType)"
            else:
                suffix = '_' + (self.suffix.text())

            if self.suffix.text() == '':
                suffix = ''

            letter = 'a' if self.letterSuffix.isChecked() else ''
            padding = str(f'{self.padIndex.value() :{0}<{self.padding.value() + 1}}')
            padding = padding[:-1] + '1'
            padding = '_' + letter + padding
            if not self.padding.isEnabled():
                padding = '_(objPadding)'

            finalName = "{prefix}{name}{suffix}{padding}".format(prefix=prefix, name=name, suffix=suffix, letter=letter,
                                                                 padding=padding)

            self.preview.setText(finalName)

        def buildUI(self):
            mainLayout = QtWidgets.QGridLayout()
            mainLayout.setSpacing(3)

            self.prefix = QtWidgets.QLineEdit("track")
            self.prefix.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.prefix.textChanged.connect(lambda: self.update_preview())
            mainLayout.addWidget(QtWidgets.QLabel("Prefix:"), 0, 0)
            mainLayout.addWidget(self.prefix, 0, 1)

            self.name = QtWidgets.QLineEdit("cone")
            self.name.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.name.textChanged.connect(lambda: self.update_preview())
            mainLayout.addWidget(QtWidgets.QLabel("Name:"), 1, 0)
            mainLayout.addWidget(self.name, 1, 1)

            self.suffix = QtWidgets.QLineEdit("geo")
            self.suffix.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.suffix.textChanged.connect(lambda: self.update_preview())
            mainLayout.addWidget(QtWidgets.QLabel("Suffix:"), 2, 0)
            mainLayout.addWidget(self.suffix, 2, 1)

            self.padIndex = QtWidgets.QSpinBox()
            self.padIndex.setValue(1)
            self.padIndex.setSingleStep(1)
            self.padIndex.setRange(0, 9)
            self.padIndex.setFixedWidth(35)
            self.padIndex.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.padIndex.valueChanged.connect(lambda: self.update_preview())
            mainLayout.addWidget(QtWidgets.QLabel("Start #:"), 3, 0)
            mainLayout.addWidget(self.padIndex, 3, 1)

            self.padding = QtWidgets.QSpinBox()
            self.padding.setValue(3)
            self.padding.setSingleStep(1)
            self.padding.setRange(0, 9)
            self.padding.setFixedWidth(35)
            self.padding.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.padding.valueChanged.connect(lambda: self.update_preview())
            mainLayout.addWidget(QtWidgets.QLabel("Padding:"), 4, 0)
            mainLayout.addWidget(self.padding, 4, 1)

            self.extractName = QtWidgets.QPushButton("Extract")
            self.extractName.clicked.connect(lambda: mmf.extract_name(prefix_field=self.prefix,
                                                                      name_field=self.name,
                                                                      suffix_field=self.suffix,
                                                                      pad_index_field=self.padIndex,
                                                                      padding_field=self.padding,
                                                                      letter_check=self.letterSuffix
                                                                      ))

            self.extractName.setFixedHeight(25)
            self.extractName.setToolTip("Extract name from selected")
            mainLayout.addWidget(self.extractName, 7, 0)

            self.lockPrefix = QtWidgets.QPushButton()
            self.lockPrefix.setCheckable(True)
            self.lockPrefix.setChecked(False)
            self.lockPrefix.clicked.connect(lambda: remote_enable(origin=self.lockPrefix, targets=[self.prefix]))
            self.lockPrefix.clicked.connect(lambda: self.update_preview())
            self.lockPrefix.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.lockPrefix.setFixedSize(20, 20)
            self.lockPrefix.setToolTip("Lock existing prefix")
            mainLayout.addWidget(self.lockPrefix, 0, 2)

            self.lockName = QtWidgets.QPushButton()
            self.lockName.setCheckable(True)
            self.lockName.setChecked(False)
            self.lockName.clicked.connect(lambda: remote_enable(origin=self.lockName, targets=[self.name]))
            self.lockName.clicked.connect(lambda: self.update_preview())
            self.lockName.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.lockName.setFixedSize(20, 20)
            self.lockName.setToolTip("Lock existing name")
            mainLayout.addWidget(self.lockName, 1, 2)

            self.lockSuffix = QtWidgets.QPushButton()
            self.lockSuffix.setCheckable(True)
            self.lockSuffix.setChecked(False)
            self.lockSuffix.clicked.connect(lambda: remote_enable(origin=self.lockSuffix, targets=[self.suffix]))
            self.lockSuffix.clicked.connect(lambda: self.update_preview())
            self.lockSuffix.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.lockSuffix.setFixedSize(20, 20)
            self.lockSuffix.setToolTip("Lock existing suffix")
            mainLayout.addWidget(self.lockSuffix, 2, 2)

            self.lockPadding = QtWidgets.QPushButton()
            self.lockPadding.setCheckable(True)
            self.lockPadding.setChecked(False)
            self.lockPadding.clicked.connect(
                lambda: remote_enable(origin=self.lockPadding, targets=[self.padding, self.padIndex]))
            self.lockPadding.clicked.connect(lambda: self.update_preview())
            self.lockPadding.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.lockPadding.setFixedSize(20, 20)
            self.lockPadding.setToolTip("Lock existing padding")
            mainLayout.addWidget(self.lockPadding, 3, 2)

            self.smartSuffix = QtWidgets.QCheckBox("Smart Suffix")
            self.smartSuffix.setChecked(False)
            self.smartSuffix.clicked.connect(lambda: self.update_preview())
            mainLayout.addWidget(self.smartSuffix, 5, 0)

            self.letterSuffix = QtWidgets.QCheckBox("Append Letter to Padding")
            self.letterSuffix.setChecked(False)
            self.letterSuffix.clicked.connect(lambda: self.update_preview())
            mainLayout.addWidget(self.letterSuffix, 5, 1)

            radioLayout = QtWidgets.QHBoxLayout()

            self.rSelect = QtWidgets.QRadioButton("Selection")
            self.rHierarchy = QtWidgets.QRadioButton("Hierarchy")
            self.rAll = QtWidgets.QRadioButton("All")

            radioLayout.addWidget(self.rSelect)
            radioLayout.addWidget(self.rHierarchy)
            radioLayout.addWidget(self.rAll)
            self.rSelect.setChecked(True)

            previewLayout = QtWidgets.QVBoxLayout()

            self.preview = QtWidgets.QLineEdit()
            self.preview.setReadOnly(True)
            self.preview.setFixedWidth(250)
            self.preview.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            previewLayout.addWidget(QtWidgets.QLabel("Preview:"))
            previewLayout.addWidget(self.preview)

            self.renameBtn = QtWidgets.QPushButton("Rename")
            self.renameBtn.clicked.connect(lambda: mmf.smart_rename(prefix=self.prefix.text(),
                                                                    name=self.name.text(),
                                                                    suffix=self.suffix.text(),
                                                                    pad_index=self.padIndex.value(),
                                                                    padding=self.padding.value(),
                                                                    lock_prefix=self.lockPrefix.isChecked(),
                                                                    lock_name=self.lockName.isChecked(),
                                                                    lock_suffix=self.lockSuffix.isChecked(),
                                                                    lock_padding=self.lockPadding.isChecked(),
                                                                    smart_suffix=self.smartSuffix.isChecked(),
                                                                    letter_suffix=self.letterSuffix.isChecked(),
                                                                    selected=self.rSelect.isChecked(),
                                                                    hierarchy=self.rHierarchy.isChecked(),
                                                                    all_objects=self.rAll.isChecked(),
                                                                    ))

            self.renameBtn.setFixedHeight(25)
            mainLayout.addWidget(self.renameBtn, 7, 1)

            # SET VALID VALUES FOR PREFIX/SUFFIX
            regex_a = QtCore.QRegExp("[a-z-A-Z]+")
            validator = QtGui.QRegExpValidator(regex_a)

            self.prefix.setValidator(validator)
            self.suffix.setValidator(validator)

            regex_b = QtCore.QRegExp("[a-z-A-Z_ ]+")
            validator = QtGui.QRegExpValidator(regex_b)
            self.name.setValidator(validator)

            # Add to tool box layout
            self.toolLayout.addLayout(mainLayout, 0, 0)
            self.toolLayout.addLayout(radioLayout, 1, 0)
            self.toolLayout.addLayout(previewLayout, 2, 0)

            self.update_preview()


def remote_enable(origin, targets):
    state = origin.isChecked()
    for t in targets:
        t.setEnabled(not state)
