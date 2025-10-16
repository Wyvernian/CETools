import logging
from os import path
from math import ceil, floor
from maya.app.stereo import stereoCameraRig
import random

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from CETools.functions.commonFunctions import *
from CETools.functions.rigging import set_index_color


def unlock(objects):
    attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
    for obj in objects:
        for attr in attrs:
            cmds.setAttr(f"{obj}.{attr}", lock=0)


def snap():
    # Currently not working well and not a priority fix
    selected = cmds.ls(selection=True)

    if len(selected) < 2:
        logging.warning("Select at least two objects/components.")
        return

    with UndoStack('snap'):

        source = selected[:-1]
        target = selected[-1]
        print(source, target)

        t = cmds.xform(target, q=True, t=True, ws=True)
        ro = cmds.xform(target, q=True, ro=True, ws=True)
        s = cmds.xform(target, q=True, s=True, ws=True)

        for src in source:
            cmds.xform(src, t=t, ro=ro, s=s, ws=1)


def bake_selected(state='fast'):
    selected = cmds.ls(selection=True)
    if not selected:
        logging.warning("Select an object to bake")
        return
    with UndoStack("bake"):

        for sel in selected:
            if state == 'fast':
                cmds.bakeResults(sel, at=['tx', 'ty', 'tz', 'rx', 'ry', 'rz'], t=(
                    cmds.playbackOptions(q=True, minTime=True), cmds.playbackOptions(q=True, maxTime=True)))
            else:
                cmds.bakeResults(sel, at=['tx', 'ty', 'tz', 'rx', 'ry', 'rz'], t=(
                    cmds.playbackOptions(q=True, minTime=True), cmds.playbackOptions(q=True, maxTime=True)), smart=True)

            cmds.delete(cmds.listRelatives(sel, type='constraint'))


def get_active_camera():
    viewports = cmds.getPanel(type='modelPanel')
    focus = cmds.getPanel(withFocus=True)
    active_panel = ''

    for i in viewports:
        if i in focus:
            active_panel = i

    if active_panel == '':
        return
    viewport_cam = cmds.modelPanel(active_panel, q=True, camera=True)
    return viewport_cam


def get_avg_pos(selection):
    x = sum(cmds.xform(s, q=1, t=1, ws=1)[0] for s in selection) / len(selection)
    y = sum(cmds.xform(s, q=1, t=1, ws=1)[1] for s in selection) / len(selection)
    z = sum(cmds.xform(s, q=1, t=1, ws=1)[2] for s in selection) / len(selection)
    return x, y, z

def cam_focus_2d():
    viewport_cam = get_active_camera()
    if viewport_cam is None:
        logging.warning("No active viewport camera found. Make sure a viewport window is currently in focus.")
        return

    # Check if 2d pan/zoom is enabled
    state = cmds.getAttr('%s.panZoomEnabled' % viewport_cam)

    if state == 0:

        start_frame = int(cmds.playbackOptions(q=True, minTime=True))
        end_frame = int(cmds.playbackOptions(q=True, maxTime=True))

        selection = cmds.ls(sl=1)
        if selection:
            shape = cmds.ls(sl=1, o=1)[0] or []
        else:
            logging.warning("Select an object to focus on.")
            return

        focal_length = cmds.getAttr('%s.focalLength' % viewport_cam)

        with UndoStack("cam_focus_2d"):
            cmds.setAttr('%s.panZoomEnabled' % viewport_cam, 1)

            loc = cmds.spaceLocator()
            x, y, z = get_avg_pos(cmds.ls(sl=1, fl=1))
            cmds.xform(loc, t=(x, y, z), ws=1)

            cmds.parent(loc, shape)
            camera_scale = cmds.getAttr('%s.cameraScale' % viewport_cam)
            h_film_offset = cmds.getAttr('%s.horizontalFilmOffset' % viewport_cam)
            v_film_offset = cmds.getAttr('%s.verticalFilmOffset' % viewport_cam)
            for f in range(start_frame, end_frame + 1):
                cam_world = om2.MMatrix(cmds.getAttr('%s.worldMatrix' % viewport_cam, t=f))
                sel_pos = om2.MPoint(cmds.getAttr('%s.worldPosition[0]' % loc[0], t=f)[0])

                relative_pos = sel_pos * cam_world.inverse()

                x = -(focal_length * (relative_pos[0] / relative_pos[2])) / 25.4
                y = -(focal_length * (relative_pos[1] / relative_pos[2])) / 25.4

                horizontal_pan = (x / camera_scale) - h_film_offset
                vertical_pan = (y / camera_scale) - v_film_offset

                cmds.setAttr('%s.horizontalPan' % viewport_cam, horizontal_pan)
                cmds.setAttr('%s.verticalPan' % viewport_cam, vertical_pan)

                cmds.setKeyframe('%s.horizontalPan' % viewport_cam, time=f, v=horizontal_pan)
                cmds.setKeyframe('%s.verticalPan' % viewport_cam, time=f, v=vertical_pan)

            cmds.delete(loc)
    else:
        delete_track()


def delete_track():
    viewport_cam = get_active_camera()
    if viewport_cam is None:
        logging.warning("No active viewport camera found. Make sure a viewport window is currently in focus.")
        return
    cmds.setAttr('%s.panZoomEnabled' % viewport_cam, 0)
    cmds.cutKey('%s.horizontalPan' % viewport_cam, s=1)
    cmds.cutKey('%s.verticalPan' % viewport_cam, s=1)
    cmds.setAttr('%s.horizontalPan' % viewport_cam, 0)
    cmds.setAttr('%s.verticalPan' % viewport_cam, 0)
    cmds.setAttr('%s.zoom' % viewport_cam, 1)


def duplicate_camera(camera=None):
    if camera is None:
        camera = cmds.ls(sl=1)
        if not cmds.listRelatives(camera, type='camera'):
            logging.warning("Select a camera to create a fresh copy.")
            return

    with UndoStack('duplicateCam'):

        camera_shape = cmds.listRelatives(camera, s=1, f=1)[0]
        old_nodes = cmds.listRelatives(camera_shape, f=1)

        cam = cmds.duplicate(camera, un=1, rc=1)[0]
        if 'CamMain' not in cam:
            cam = cmds.rename(cam, 'CamMain')

        parent = cmds.listRelatives(cam, p=1)
        if parent:
            cam = cmds.parent(cam, w=1)[0]

        cam_shape = cmds.listRelatives(cam, s=1, f=1)[0]

        new_nodes = cmds.listRelatives(camera_shape, f=1)
        if new_nodes:
            for n in new_nodes:
                if n not in old_nodes:
                    cmds.imagePlane(cmds.listRelatives(n, s=1), e=1, c=cam_shape, sia=0)

        for attr in ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']:
            cmds.setAttr(f"{cam}.{attr}", lock=True)

        if not cmds.objExists('camTrack'):
            cmds.group(em=1, name='camTrack', w=1)

        cmds.parent(cam, '|camTrack')
        fresh_camera = '|camTrack|' + cam

        # Set up the stereo camera rig
        stereoCameraRig.rigRoot(cmds.listRelatives(fresh_camera, f=1)[0])
        cmds.select(fresh_camera, r=1)
        return fresh_camera


def run_retime(camera='camera1', retime_path=None, sequence_path=None, overwrite=False, insert=True,
               reverse_order=False):
    # assign default preferences

    if not retime_path or not path.isfile(retime_path) or not retime_path.endswith(
            '.ascii') or not retime_path.endswith('.txt'):
        logging.warning("Retime File is not a valid .ascii or .txt, aborting.")
        return

    if sequence_path is None or not path.isfile(sequence_path) or not sequence_path.endswith('.exr'):
        logging.warning("Sequence File is not a valid .exr, aborting.")
        return

    old_column = 0
    new_column = 1

    if reverse_order is True:
        old_column, new_column = 1, 0

    selected = cmds.ls(sl=1, l=1)

    with UndoStack("retime"):
        camera = duplicate_camera(camera)
        cam_shp = cmds.listRelatives(camera, f=1)

        targets = [camera]

        if selected:
            target_list = [camera]
            target_list.extend(selected)
            targets = list(set(target_list))

        old_time = []
        new_time = []
        with open(retime_path) as file:
            for item in file:
                try:
                    item = item.strip("\n")
                    line = item.split(" ")
                    old_time.append(line[old_column])
                    new_time.append(line[new_column])
                except IndexError:
                    pass

        # Remove empty spaces
        old_time = [float(i) for i in old_time if i]
        new_time = [float(i) for i in new_time if i]
        end_frame = 0.0

        for target in targets:
            for o, n in zip(old_time, new_time):
                for at in ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']:
                    cmds.setAttr(f"{target}.{at}", lock=False)
                    value = cmds.keyframe(target, q=1, at=at, eval=1, t=(o,))
                    if value:
                        cmds.setKeyframe(target, time=(n,), v=value[0], at=at)
                    if end_frame == 0.0:
                        if o > max(new_time):
                            end_frame = n

        # Get the lowest and highest keys from combined list, rounded, and set them as the bake animation range
        if overwrite is True:
            time_range = sorted(new_time)
            start = floor(float(time_range[0]))
            end = ceil(float(time_range[-1]))
            if max(old_time) > max(new_time):
                end_frame = end

            cmds.bakeResults(camera, time=(start, end_frame))
            cmds.playbackOptions(minTime=start, maxTime=end_frame)

        if insert is True:
            start_time = cmds.playbackOptions(query=True, minTime=True)
            end_time = cmds.playbackOptions(query=True, maxTime=True)
            cmds.bakeResults(camera, time=(start_time, end_time))

        for attr in ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']:
            cmds.setAttr(f"{camera}.{attr}", lock=True)

        # SET NEW IMAGE PLANE SETTINGS
        image_plane = cmds.listRelatives(cmds.listRelatives(cam_shp, f=1), f=1)[0]
        cmds.setAttr("%s.imageName" % image_plane, sequence_path, type='string')
        cmds.setAttr("%s.useFrameExtension" % image_plane)
        cmds.setAttr("%s.useFrameExtension" % image_plane)

        # GROUP CAMERA IN CAM RETIME
        if not cmds.objExists('camRetime'):
            cmds.group(em=1, name='camRetime', w=1)
        try:
            cmds.parent(camera, 'camRetime')
        except:
            pass


def invert_anim(host=None, target=None):
    if not cmds.objExists(host):
        logging.warning('Animated Object is not valid, aborting.')
        return

    if not cmds.objExists(target):
        logging.warning('Target is not valid, aborting.')
        return

    with UndoStack("invertAnim"):
        duplicate = cmds.duplicate(target, rc=1, po=1)[0]
        target_grp = cmds.listRelatives(target, p=1)
        grp = cmds.group(target)
        new_dest = cmds.parent(grp, host)[0]

        target = host + '|' + new_dest + '|' + target.split('|')[-1]
        con_pnt = cmds.pointConstraint(duplicate, target)
        con_ori = cmds.orientConstraint(duplicate, target)

        start_time = cmds.playbackOptions(query=True, minTime=True)
        end_time = cmds.playbackOptions(query=True, maxTime=True)
        cmds.bakeResults(target, time=(start_time, end_time))

        cmds.delete(con_pnt, con_ori)
        if target_grp:
            cmds.parent(target, target_grp)
        else:
            cmds.parent(target, w=1)

        cmds.cutKey(host, s=True)
        cmds.delete(duplicate, grp)


def create_cones_at_pivots():
    # Get the selection from the outliner
    selected = cmds.ls(sl=1)

    if not selected:
        logging.warning("No objects selected in the outliner.")
        return
    with UndoStack('createCones'):
        # Create a group for the cones in the outliner
        cone_group = cmds.group(empty=True, name="track_cones")

        # Loop through selected objects and create cones at their pivots
        for sel in selected:
            height = 2
            # Create a cone at the pivot position with default scaling
            cone = cmds.polyCone(radius=1, height=height, subdivisionsX=20, subdivisionsY=1)
            cmds.setAttr(cone[0] + ".scaleX", 5)
            cmds.setAttr(cone[0] + ".scaleY", 5)
            cmds.setAttr(cone[0] + ".scaleZ", 5)

            # Rotate the cone to 180 degrees
            cmds.setAttr(cone[0] + ".rotateX", 180)
            cmds.setAttr(cone[0] + ".rotateY", 0)
            cmds.setAttr(cone[0] + ".rotateZ", 0)

            # Translate the cone to match the initial scaling in Y
            initial_scaling_value = 5
            cmds.setAttr(cone[0] + ".translateY", initial_scaling_value)

            # Move the pivot of the cone to the bottom vertex
            cmds.makeIdentity(cone[0], apply=True, translate=True, rotate=True, scale=True)
            bbox = cmds.exactWorldBoundingBox(cone[0])
            bottom = [(bbox[0] + bbox[3]) / 2, bbox[1], (bbox[2] + bbox[5]) / 2]
            cmds.xform(cone[0], piv=bottom, ws=True)

            # Move the cone to the pivot position of the object
            pivot_position = cmds.xform(sel, q=True, t=True, ws=True)
            cmds.xform(cone[0], translation=pivot_position, r=True)

            # Create a red surface shader and assign it to the cone
            if not cmds.objExists('track_cones_MAT'):
                shader = cmds.shadingNode("surfaceShader", asShader=True, name='track_cones_MAT')
                cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name="track_cones_SG")
                cmds.setAttr(shader + ".outColor", 1, 0, 0, type="double3")
                cmds.select(cone[0])
                cmds.hyperShade(assign=shader)
            else:
                cmds.select(cone[0])
                cmds.hyperShade(assign='track_cones_MAT')

            cmds.parent(cone[0], cone_group)


def select_cones():
    if cmds.objExists("track_cones|*"):
        cmds.select("track_cones|*")
    else:
        logging.warning(
            "No Track Cones group available. What did you do to it? HUH? WHERE'S THE GROUP YOU SICK BASTARD?")


def scale_cones(factor=1.0):
    selected = cmds.ls(sl=1)
    for sel in selected:
        scale = cmds.xform(sel, q=True, scale=True, r=True)
        new_scale = (scale[0] + factor, scale[1] + factor, scale[2] + factor)
        cmds.xform(sel, scale=new_scale)


def cam_depth(size=1.0):
    selected = cmds.ls(sl=1)
    viewports = cmds.getPanel(type='modelPanel')
    visible = cmds.getPanel(vis=True)
    active_panel = ''

    with UndoStack(cam_depth):

        for i in viewports:
            if i in visible:
                active_panel = i

        viewport_cam = cmds.modelPanel(active_panel, q=True, camera=True)
        focal_length = cmds.getAttr('%s.focalLength' % viewport_cam)
        t1 = cmds.xform(viewport_cam, q=1, t=1)
        v1 = om2.MVector(t1)

        for sel in selected:
            t2 = cmds.xform(sel, q=1, t=1, ws=1)
            v2 = om2.MVector(t2)

            dist = om2.MVector(v2 - v1).length()

            scale = size * ((0.254 * dist) / focal_length)  # 0.254 for inches conversion
            new_scale = (scale, scale, scale)
            cmds.xform(sel, scale=new_scale)


def filmback_correct(file=None, pixel_aspect=1):
    if file is None or not path.isfile(file) or not file.endswith('.exr'):
        logging.warning("Undistorted Sequence File is not a valid .exr, aborting.")
        return

    sel = cmds.ls(sl=1)
    if sel:
        if cmds.listRelatives(sel[0], type='camera'):
            print('Using selected camera')
            viewport_cam = sel[0]
        else:
            print('No camera selected, using viewport camera')
            viewport_cam = get_active_camera()

    else:
        print('No camera selected, using viewport camera')
        viewport_cam = get_active_camera()

    if viewport_cam is None:
        logging.warning("No active viewport camera found. Make sure a viewport window is currently in focus.")
        return

    cam_shape = cmds.listRelatives(viewport_cam)
    image_plane = cmds.listRelatives(cam_shape)

    try:
        image_shape = cmds.listRelatives(image_plane)[0]
    except TypeError:
        logging.warning('Current camera needs an image plane.')
        return

    with UndoStack('filmback'):

        coverage_x = cmds.getAttr('%s.coverageX' % image_shape)
        coverage_y = cmds.getAttr('%s.coverageY' % image_shape)

        cmds.setAttr('%s.imageName' % image_shape, file, type='string')

        new_width = cmds.getAttr('%s.coverageX' % image_shape)
        new_height = cmds.getAttr('%s.coverageY' % image_shape)

        cov_origin_x = ((new_width * pixel_aspect) - (coverage_x * pixel_aspect)) / 2
        cov_origin_y = (new_height - coverage_y) / 2

        cmds.setAttr('%s.coverageOriginX' % image_shape, cov_origin_x)
        cmds.setAttr('%s.coverageOriginY' % image_shape, cov_origin_y)
        cmds.setAttr('%s.coverageX' % image_shape, coverage_x)
        cmds.setAttr('%s.coverageY' % image_shape, coverage_y)


def define_selection():
    selection_list = []
    sel = cmds.ls(sl=True)

    for each in sel:
        cams = cmds.listRelatives(each, s=True, c=True)
        if cams:  # not transform
            if cmds.objectType(cams[0]) == 'camera':
                camera = 'camera_%s' % each
                selection_list.append(camera)
        else:
            connections = cmds.listConnections(each, t='animCurve')
            if connections:
                obj_group = 'vobjgroup_%s' % each
                selection_list.append(obj_group)
            else:
                point_grp = 'pointgrp_%s' % each
                selection_list.append(point_grp)

    selection_list.sort()
    return selection_list


def choose_file():
    multiple_filters = "ASCII (*.asc);;All Files (*.*)"
    file_to_write_kuper = cmds.fileDialog2(fileFilter=multiple_filters, dialogStyle=2)

    if file_to_write_kuper:
        return file_to_write_kuper[0]
    else:
        return


def open_file(which_file, f_kuper):
    if which_file:
        try:
            if f_kuper.closed is True:
                f_kuper = open(which_file, 'w')
            else:
                f_kuper = open(which_file, 'a')
        except:
            f_kuper = open(which_file, 'w')
        return True, f_kuper
    else:
        return False, None


def close_file(f_kuper):
    try:
        f_kuper.close()
        print('closed file\n')
    except:
        print('')


def write_camera_anim(which_cam, f_kuper):
    frame_start = cmds.playbackOptions(q=True, minTime=True)
    frame_end = cmds.playbackOptions(q=True, maxTime=True)

    # ---------------- Header -----------------------------------
    # f.write('group_camera = %s' %whichCam)
    f_kuper.write('Axes = frame, VTrack, VEW, VNS, Vpan, VTilt, VRoll, focal\n')

    # frames
    for frame in range(int(frame_start), int(frame_end) + 1):
        cmds.currentTime(frame, edit=True)
        translates = cmds.xform(which_cam, q=True, ws=True, t=True)
        tx = translates[0]
        ty = translates[1]
        tz = translates[2]

        rotates = cmds.xform(which_cam, q=True, ws=True, ro=True)
        rx = rotates[0]
        ry = rotates[1]
        rz = rotates[2]
        focal = cmds.camera(which_cam, q=True, fl=True)
        f_kuper.write('%.6f %.9f %.9f %.9f %.9f %.9f %.9f %.9f\n' % (frame, tz, tx, ty, -ry, rx, -rz, focal))


def write_object_anim(which_obj, f_kuper):
    frame_start = cmds.playbackOptions(q=True, minTime=True)
    frame_end = cmds.playbackOptions(q=True, maxTime=True)

    f_kuper.write('Axes = frame, VTrack, VEW, VNS, Vpan, VTilt, VRoll\n')

    # frames
    for frame in range(int(frame_start), int(frame_end) + 1):
        cmds.currentTime(frame, edit=True)
        translates = cmds.xform(which_obj, q=True, ws=True, t=True)
        tx = translates[0]
        ty = translates[1]
        tz = translates[2]

        rotates = cmds.xform(which_obj, q=True, ws=True, ro=True)
        rx = rotates[0]
        ry = rotates[1]
        rz = rotates[2]
        # order is = Frame, Tz, Tx, Ty, -Ry, Rx, -Rz (with spaces)
        f_kuper.write('%.6f %.9f %.9f %.9f %.9f %.9f %.9f\n' % (frame, tz, tx, ty, -ry, rx, -rz))


def write_pts_info(which_type, which_grp, f_kuper):
    locator_list = []

    f_kuper.write('\npoints_%s = %s\n' % (which_type, which_grp))
    child_list = cmds.listRelatives(which_grp, type='transform', c=True)

    for eachSel in child_list:
        shape = cmds.listRelatives(eachSel, s=True, c=True)[0]

        if cmds.objectType(str(shape)) == 'locator':
            locator_list.append(str(eachSel))

    for transform in locator_list:
        t = cmds.xform(transform, q=1, ws=1, t=1)
        tokens = transform.split("|")

        f_kuper.write((tokens[- 1] + " point x: " + str(t[0]) + " y: " + str(t[1]) + " z: " + str(t[2]) + "\n"))


def kuper_main():
    file_to_write_kuper = ''
    f_kuper = None

    selection_list = define_selection()
    if len(selection_list) > 0:
        file_to_write_kuper = choose_file()
    else:
        logging.warning('please select a camera, point group, and or object group')

    for each in selection_list:
        group_type = str(each.split('_')[0])
        if group_type == 'camera':
            camera = each.split('camera_')[1]
            if file_to_write_kuper != '':
                is_file, f_kuper = open_file(file_to_write_kuper, f_kuper)
                if is_file:
                    write_camera_anim(camera, f_kuper)

        if group_type == 'vobjgroup':
            obj_group = each.split('vobjgroup_')[1]
            if file_to_write_kuper != '':
                is_file, f_kuper = open_file(file_to_write_kuper, f_kuper)
                if is_file:
                    write_object_anim(obj_group, f_kuper)

    if file_to_write_kuper != '':
        close_file(f_kuper)


def z_constrain(src_obj, dest_obj):
    # create a locator and parent to camera
    if not cmds.objExists(src_obj):
        logging.warning('Camera is not valid.')
        return

    if not cmds.objExists(dest_obj):
        logging.warning('Target Object is not valid.')
        return

    with UndoStack('z_constrain'):
        cmds.select(cl=1)

        world_grp = cmds.group(n="worldXYZ", em=1)
        world_grp = cmds.ls(world_grp, l=1)[0]
        cmds.parentConstraint(src_obj, world_grp, mo=0)
        cmds.select(world_grp, r=1)
        bake_selected(state="fast")

        new_group = cmds.group(n="screenXY", em=1)
        new_group = cmds.ls(new_group, l=1)[0]

        cmds.parent(new_group, world_grp, r=1)
        cmds.aimConstraint(dest_obj, world_grp + new_group, aim=(0, 0, 1))
        cmds.select(world_grp + new_group, r=1)
        bake_selected(state="fast")

        distance_locator = cmds.spaceLocator(n="distance")[0]
        distance_locator = cmds.ls(distance_locator, l=1)[0]

        cmds.parent(distance_locator, world_grp + new_group, r=1)

        cmds.setAttr(world_grp + new_group + distance_locator + ".translateZ", 10)
        print(world_grp + new_group + distance_locator)
        z_constraint = \
            cmds.pointConstraint(dest_obj, world_grp + new_group + distance_locator, offset=(0, 0, 0), skip=('x', 'y'),
                                 weight=1)[0]
        cmds.select(cl=1)

        start_time = cmds.playbackOptions(q=1, min=1)
        end_time = cmds.playbackOptions(q=1, max=1)
        cmds.bakeResults(world_grp + new_group + distance_locator, t=(start_time, end_time), sampleBy=1,
                         disableImplicitControl=True, preserveOutsideKeys=True, sparseAnimCurveBake=True,
                         controlPoints=True, shape=True, at="tz")

        cmds.delete(z_constraint)

        cmds.cutKey(dest_obj, at=['tx', 'ty', 'tz'], option='keys', cl=1)
        cmds.pointConstraint(world_grp + new_group + distance_locator, dest_obj, mo=0)

        cmds.select(world_grp + new_group + distance_locator, r=1)


def z_bake(dest_obj=''):
    if cmds.objExists(dest_obj):
        cmds.select(dest_obj)
        bake_selected(state='fast')
    else:
        logging.warning('Target object is not valid.')
        return


def z_constrain_selected():
    objs = cmds.ls(sl=1)
    if len(objs) == 2:
        z_constrain(objs[0], objs[1])
    else:
        logging.warning("zconstrain requires two selected objects")
        return


def z_smooth(samples, rate, iterations):
    selected = cmds.ls(sl=True)

    if not selected or not cmds.keyframe(selected, q=True, sl=True):
        logging.warning('Select keyframes to smooth.')
        return

    with UndoStack('z_smooth'):

        unlock(selected)

        for sel in selected:
            anim_curves = cmds.keyframe(sel, q=True, sl=True, n=True)
            for repeats in range(0, iterations):
                for crv in anim_curves:
                    sel_keys = cmds.keyframe(crv, q=True, sl=True)
                    for i in range(0, len(sel_keys) - 1):
                        value_list = []
                        key = int(sel_keys[i])
                        key_val = cmds.keyframe(crv, t=(key,), q=True, ev=True)[0]

                        for s in range(-samples, samples):
                            val = cmds.keyframe(crv, t=(key + rate * s,), q=True, ev=True)[0]
                            value_list.append(val)

                        total = sum(value_list) + key_val
                        average = total / (1 + samples * 2)
                        cmds.setKeyframe(crv, v=average, t=key)


def get_object_type(sel):
    try:
        object_type = cmds.objectType(sel)  # Get object type.
    except:
        object_type = "transform"  # If there is no shape node pass "transform".
    return object_type


def is_one_image_plane_selected(shape_list):
    shape_list_size = len(shape_list)
    if not 0 < shape_list_size < 2:
        return False

    object_type = get_object_type(shape_list[0])
    if object_type == "imagePlane":
        return True
    else:
        return False


def get_shape_list(transform_list):
    shape_list = []
    for transform in transform_list:
        shape = cmds.listRelatives(transform, shapes=True, fullPath=True)[0]
        if cmds.objectType(shape, isType='mesh'):
            shape_list.append(shape)
    return shape_list


def holdout():
    selected_geo = cmds.ls(selection=True, long=True)
    selected_shapes = get_shape_list(selected_geo)
    selected_shapes_len = len(selected_shapes)

    with UndoStack("holdout"):

        active_camera = get_active_camera()

        if selected_shapes_len == 0 or is_one_image_plane_selected(selected_shapes):  # If nothing is selected toggle
            # all_objects geometry in scene.
            holdout_geo_exists = False
            geo_list = cmds.ls(geometry=True, long=True)  # Get list of geometric Dag objects in scene.
            for geo in geo_list:
                try:
                    holdout_geo_exists = cmds.getAttr(geo + '.holdOut')
                except:
                    pass

            if holdout_geo_exists:  # If Holdout Geometry exists in scene...
                for geo in geo_list:
                    try:
                        cmds.setAttr(geo + '.holdOut', 0)  # Turn off holdout for all_objects geometry in scene
                        # cmds.modelEditor(activePanel, e=1, hos=0)

                    except:
                        pass
                return

            if not holdout_geo_exists:  # If there is no Holdout Geometry in scene...
                for geo in geo_list:
                    try:
                        cmds.setAttr(geo + '.holdOut', 1)  # Turn on holdout for all_objects geometry in scene
                        # cmds.modelEditor(activePanel, e=1, hos=1)

                    except:
                        pass
                return

        elif selected_shapes_len >= 0:
            for sel_geo_shape in selected_shapes:
                try:
                    toggle_state = cmds.getAttr(sel_geo_shape + '.holdOut')
                    cmds.setAttr(sel_geo_shape + '.holdOut', (not toggle_state))
                    # togglePanel = cmds.modelEditor(activePanel, q=1, hos=1)
                    # cmds.modelEditor(activePanel, e=1, hos=(not toggle_state))
                except:
                    pass


def find_object_type(item):
    if cmds.listRelatives(item, shapes=True, f=True):
        item_type = cmds.objectType(cmds.listRelatives(item, shapes=True, f=True)[0])
    else:
        item_type = cmds.objectType(item)
    return item_type


def legacy_rename(prefix='', name='', suffix='', pad_index=1, padding=3, lock_prefix=False, lock_name=False,
                  lock_suffix=False, lock_padding=False, smart_suffix=False, letter_suffix=False, selected=True,
                  hierarchy=False, all_objects=False, preserve_namespaces=True):
    suffix_dict = {
        "joint": "JNT",
        "jointEnd": "END",
        "mesh": "OBJ",
        "transform": "GRP",
        "camera": "CAM",
        "ikEffector": "EFF",
        "ikHandle": "IK",
        "nurbsSurface": "SRF",
        "nurbsCurve": "CRV",
        "locator": "LOC",
        "clusterHandle": "CLT",
        "aiLightPortal": "PTL",
        "imagePlane": "IMG",
        "parentConstraint": "PaCON",
        "pointConstraint": "PoCON",
        "orientConstraint": "OCON",
        "scaleConstraint": "SCON",
        "poleVectorConstraint": "PV",
        "aimConstraint": "AIM",
    }

    a = -1

    if hierarchy:
        items = cmds.ls(os=True, dag=True, tr=True, l=True)
    elif selected:
        items = cmds.ls(os=True, l=True)
    elif all_objects:
        logging.warning("This doesn't work! Thanks Maya! WOO")
        return
    else:
        return

    with UndoStack("smart_rename"):
        for i, item in enumerate(items):

            if hierarchy:
                items = cmds.ls(os=True, dag=True, tr=True, l=True)
            elif selected:
                items = cmds.ls(os=True, l=True)
            elif all_objects:
                logging.warning("This doesn't work! Thanks Maya!")
                return
            else:
                return

            item_name = extract_name(set_fields=False, target_object=(cmds.ls(items[i], sn=True)))
            item_type = get_object_type(items[i])

            # CHANGE LETTERING BASED ON CHILD OBJECTS
            parent_object = cmds.listRelatives(items[i], parent=True, f=True)
            previous_parent = cmds.listRelatives(items[i - 1], parent=True, f=True)
            children = cmds.listRelatives(items[i], children=True, f=True)
            p_children = None

            if parent_object:
                parent_name = extract_name(set_fields=False, target_object=(cmds.ls(parent_object, sn=True)))
                p_children = cmds.listRelatives(parent_object, children=True, f=True)

                if parent_name[2] != name:
                    a = 0

            if p_children:
                if len(p_children) > 1:
                    a += 1
                else:
                    a += 1
            else:
                a += 1

            if selected:
                a = i

            # TESTING FOR LIKE OBJECTS IN SAME LEVEL OF HIERARCHY, THIS COULD GET MESSY

            if parent_object:
                if item_type != get_object_type(parent_object):
                    if parent_object != previous_parent:
                        a = 0

            # SUFFIX MODIFIERS

            if smart_suffix and suffix != '':
                if item_type not in suffix_dict:  # IF TYPE IS NOT IN DICTIONARY
                    item_type = "mesh"
                    logging.warning("Some objects aren't registered in the suffix database. Will use _OBJ_ instead.")

                if children is None:
                    if item_type == "joint":
                        item_type = "jointEnd"

                suffix = (suffix_dict.get(item_type)).lower()

            padding_text = ''
            if letter_suffix:
                padding_text += str(chr(ord('@') + (a + 1))).lower()

            if lock_padding:
                padding_text = item_name[4]
            else:
                padding_text += str(f"{pad_index :{'0'}<{padding + 1}}")
                padding_text = padding_text[:-1]

                if not letter_suffix:
                    padding_text += str(a + 1)
                else:
                    padding_text += '1'

            final_name = ''

            '''
            STRING CONSTRUCTION LOGIC:
                if a field is blank, it is removed (or not added)
                if a field is not blank and not locked, it is added
                if a field is locked, it is ignored, and the original is used
            '''

            if not lock_prefix:
                if prefix != '':
                    final_name += prefix + '_'
            if lock_prefix and item_name[1] != '':
                final_name += item_name[1] + '_'

            if not lock_name:
                if name != '':
                    final_name += name
            if lock_name and item_name[2] != '':
                final_name += item_name[2]

            if not lock_suffix:
                if suffix != '':
                    final_name += '_' + suffix
            if lock_suffix and item_name[3] != '':
                final_name += '_' + item_name[3]

            if not lock_padding:
                if padding_text != '':
                    final_name += '_' + padding_text
            if lock_padding and item_name[4] != '':
                final_name += '_' + item_name[4]

            # CREATE FINAL NAME
            print(final_name)
            if final_name != '':
                cmds.rename(items[i], final_name)


def extract_name(set_fields=True, target_object=None, prefix_field=None, name_field=None, suffix_field=None,
                 pad_index_field=None,
                 padding_field=None, letter_check=None, preserve_namespaces=False):
    if target_object:
        input_object = target_object
    else:
        input_object = cmds.ls(sl=1)

    if len(input_object) == 1:

        prefix = ''
        name = ''
        suffix = ''
        pad_index = 0
        padding = 0
        letter = ''
        number = ''
        padding_text = ''

        if '|' in input_object:
            input_object = input_object.split('|')[-1]
        if ':' in input_object:
            if preserve_namespaces:
                namespace = ':'.join(x for x in input_object.split(':')[0:-1])
            input_object = input_object.split(':')[-1]

        # OBJECT NAME ANALYSIS

        components = input_object[0].split('_')

        if len(components) > 1 and (any(char.isdigit() for char in components[-1])):
            pad_value = components[-1]
            letter = ''.join(x for x in pad_value if x.isalpha())
            number = ''.join(x for x in pad_value if x.isdigit())
            components.pop()

        if len(components) == 1:
            name = ''.join(x for x in components[0] if not x.isdigit())
            number = ''.join(x for x in components[0] if x.isdigit())

        if len(components) == 2:
            name = components[0]
            suffix = components[1]

        if len(components) >= 3:
            prefix = components[0]
            name = '_'.join(components[1:(len(components) - 1)])
            suffix = components[-1]

        if set_fields:

            if letter == '':
                letter_check.setChecked(False)
            else:
                letter_check.setChecked(True)

            if not number == '':
                pad_index = int(number[0])
                padding = int(len(number) - 1)

            # REPLACE TEXT/VALUES IN FIELDS

            if prefix_field.isEnabled():
                prefix_field.setText(prefix)

            if name_field.isEnabled():
                name_field.setText(name)

            if suffix_field.isEnabled():
                suffix_field.setText(suffix)

            pad_index_field.setValue(pad_index)
            padding_field.setValue(padding)


        else:
            clean_name = ''
            if preserve_namespaces:
                clean_name = namespace + ':' + clean_name
            if prefix:
                clean_name += prefix + '_'
            if name:
                clean_name += name
            if suffix:
                clean_name += '_' + suffix
            if letter:
                padding_text = letter
            if number:
                padding_text += str(number)

            return [clean_name, prefix, name, suffix, padding_text]

    else:
        logging.warning("Select one object to extract the name from.")
        return


def screen_anim_visualiser(interval, frame_range):
    selected = cmds.ls(sl=1, type='transform')
    camera = selected[0]
    targets = selected[1:]

    if not selected:
        logging.warning('Select a camera and an animated object')
        return

    if len(selected) < 2:
        logging.warning('Select a camera and an animated object')
        return

    for target in targets:

        if frame_range == 'playback':
            start_time = cmds.playbackOptions(q=True, min=True)
            end_time = cmds.playbackOptions(q=True, max=True)
        else:
            all_keys = sorted(cmds.keyframe(target, q=True) or [])
            if all_keys:
                start_time = all_keys[0]
                end_time = all_keys[1]
            else:
                return

        snapshot = cmds.snapshot(target, motionTrail=1, increment=1, startTime=start_time, endTime=end_time,
                                 anchorTransform=camera)
        motion_trail = cmds.listRelatives(snapshot[0], c=1)[0]
        points = cmds.getAttr(f'{motion_trail}.points')
        keyframes = cmds.getAttr(f'{motion_trail}.keyframeTimes')

        curve_points = []
        for i, point in enumerate(points):
            if interval == 'key':
                if (i + start_time) in keyframes:
                    stripped_point = point[:-1]
                    curve_points.append(stripped_point)
            else:
                stripped_point = point[:-1]
                curve_points.append(stripped_point)

        curve = cmds.curve(p=curve_points, n=f'{target}_screen_path_crv')

        set_index_color(random.randint(3, 31), [curve])
        cmds.parentConstraint(camera, curve)
        cmds.scaleConstraint(camera, curve)
        cmds.delete(snapshot)


def smart_rename(prefix='', name='', suffix='', pad_index=1, padding=3, lock_prefix=False, lock_name=False,
                 lock_suffix=False, lock_padding=False, smart_suffix=False, letter_suffix=False, selected=True,
                 hierarchy=False, all_objects=False, preserve_namespaces=True):
    suffix_dict = {
        "joint": "JNT",
        "jointEnd": "END",
        "mesh": "OBJ",
        "transform": "GRP",
        "camera": "CAM",
        "ikEffector": "EFF",
        "ikHandle": "IK",
        "nurbsSurface": "SRF",
        "nurbsCurve": "CRV",
        "locator": "LOC",
        "clusterHandle": "CLT",
        "aiLightPortal": "PTL",
        "imagePlane": "IMG",
        "parentConstraint": "PaCON",
        "pointConstraint": "PoCON",
        "orientConstraint": "OCON",
        "scaleConstraint": "SCON",
        "poleVectorConstraint": "PV",
        "aimConstraint": "AIM",
    }

    '''
        def build_hierarchy_dict(node):
        """
        Recursively build a dictionary representing the hierarchy starting from the given node.
        """
        # Initialize the dictionary for this node
        outliner_hierarchy = {node: {}}

        # List children of the current node, excluding intermediate objects
        node_children = cmds.listRelatives(node, children=True, type='transform', path=True) or []

        # Recursively build the hierarchy for each child
        for child in node_children:
            outliner_hierarchy[node].update(build_hierarchy_dict(child))
        print(outliner_hierarchy)
        return outliner_hierarchy

    def get_scene_hierarchy(root_nodes):
        """
        Builds the hierarchy dictionary for all top-level nodes in the scene.
        """
        # List all top-level transform nodes in the scene

        top_level_nodes = cmds.ls(root_nodes)

        # Build the hierarchy starting from each top-level node
        scene_hierarchy = {}
        for node in top_level_nodes:
            scene_hierarchy.update(build_hierarchy_dict(node))

        return scene_hierarchy
    '''

    def get_all_keys(d):
        for key, value in d.items():
            yield key
            if isinstance(value, dict):
                yield from get_all_keys(value)

    def count(d):
        return sum([count(v) if isinstance(v, dict) else 1 for v in d.values()])

    def build_hierarchy_dict(node_name, node_uuid):
        """
        Recursively build a dictionary representing the hierarchy starting from the given node.
        """

        # Initialize the dictionary for this node
        outliner_hierarchy = {node_uuid: {}}

        # List children of the current node, excluding intermediate objects
        node_children = cmds.listRelatives(node_name, children=True, type='transform', path=True) or []

        # Recursively build the hierarchy for each child
        for child in node_children:
            outliner_hierarchy[node_uuid].update(build_hierarchy_dict(child, cmds.ls(child, uuid=1)[0]))

        return outliner_hierarchy

    def get_scene_hierarchy(root_nodes):
        """
        Builds the hierarchy dictionary for all top-level nodes in the scene.
        """
        # List all top-level transform nodes in the scene

        top_level_nodes = cmds.ls(root_nodes)

        # Build the hierarchy starting from each top-level node
        scene_hierarchy = {}
        for node in top_level_nodes:
            node_uuid = cmds.ls(node, uuid=1)[0]
            scene_hierarchy.update(build_hierarchy_dict(node, node_uuid))

        return scene_hierarchy

    with UndoStack("smart_rename"):

        if hierarchy:
            roots = cmds.ls(os=True, dag=True, tr=True, l=1)
        elif selected:
            roots = cmds.ls(os=True, l=1)
        elif all_objects:
            roots = cmds.ls(assemblies=True, l=1)
        else:
            return

        scene_hierarchy = get_scene_hierarchy(root_nodes=roots)

        i = 0
        a = -1

        for node in get_all_keys(scene_hierarchy):
            node_longname = cmds.ls(node, l=1)[0]
            item_name = extract_name(set_fields=False, target_object=cmds.ls(node, sn=1))

            try:
                cmds.rename(node_longname, f'node_temp_name_{i}')
            except RuntimeError:
                continue

            node_longname = cmds.ls(node, l=1)[0]

            item_type = get_object_type(node_longname)

            # Operate on name

            if smart_suffix and suffix != '':
                if item_type not in suffix_dict:  # IF TYPE IS NOT IN DICTIONARY
                    item_type = "mesh"
                    logging.warning("Some objects aren't registered in the suffix database. Will use _OBJ_ instead.")

                '''
                if children is None:
                    if item_type == "joint":
                        item_type = "jointEnd"

                '''
                suffix = (suffix_dict.get(item_type)).lower()

            padding_text = ''
            if letter_suffix:
                padding_text += str(chr(ord('@') + (a + 1))).lower()

            if lock_padding:
                padding_text = item_name[4]
            else:
                padding_text += str(f"{pad_index :{'0'}<{padding + 1}}")
                padding_text = padding_text[:-1]

                if not letter_suffix:
                    padding_text += str(a + 1)
                else:
                    padding_text += '1'

            final_name = ''

            '''
            STRING CONSTRUCTION LOGIC:
                if a field is blank, it is removed (or not added)
                if a field is not blank and not locked, it is added
                if a field is locked, it is ignored, and the original is used
            '''

            if not lock_prefix:
                if prefix != '':
                    final_name += prefix + '_'
            if lock_prefix and item_name[1] != '':
                final_name += item_name[1] + '_'

            if not lock_name:
                if name != '':
                    final_name += name
            if lock_name and item_name[2] != '':
                final_name += item_name[2]

            if not lock_suffix:
                if suffix != '':
                    final_name += '_' + suffix
            if lock_suffix and item_name[3] != '':
                final_name += '_' + item_name[3]

            if not lock_padding:
                if padding_text != '':
                    final_name += '_' + padding_text
            if lock_padding and item_name[4] != '':
                final_name += '_' + item_name[4]

            # CREATE FINAL NAME
            if final_name != '':
                cmds.rename(node_longname, final_name)

            i += 1

        return

        a = -1

        for i, item in enumerate(items):

            # CHANGE LETTERING BASED ON CHILD OBJECTS
            parent_object = cmds.listRelatives(items[i], parent=True, f=True)
            previous_parent = cmds.listRelatives(items[i - 1], parent=True, f=True)
            children = cmds.listRelatives(items[i], children=True, f=True)
            p_children = None

            if parent_object:
                parent_name = extract_name(set_fields=False, target_object=(cmds.ls(parent_object, sn=True)))
                p_children = cmds.listRelatives(parent_object, children=True, f=True)

                if parent_name[2] != name:
                    a = 0

            if p_children:
                if len(p_children) > 1:
                    a += 1
                else:
                    a += 1
            else:
                a += 1

            if selected:
                a = i

            # TESTING FOR LIKE OBJECTS IN SAME LEVEL OF HIERARCHY, THIS COULD GET MESSY

            if parent_object:
                if item_type != get_object_type(parent_object):
                    if parent_object != previous_parent:
                        a = 0

            # SUFFIX MODIFIERS

            if smart_suffix and suffix != '':
                if item_type not in suffix_dict:  # IF TYPE IS NOT IN DICTIONARY
                    item_type = "mesh"
                    logging.warning("Some objects aren't registered in the suffix database. Will use _OBJ_ instead.")

                if children is None:
                    if item_type == "joint":
                        item_type = "jointEnd"

                suffix = (suffix_dict.get(item_type)).lower()

            padding_text = ''
            if letter_suffix:
                padding_text += str(chr(ord('@') + (a + 1))).lower()

            if lock_padding:
                padding_text = item_name[4]
            else:
                padding_text += str(f"{pad_index :{'0'}<{padding + 1}}")
                padding_text = padding_text[:-1]

                if not letter_suffix:
                    padding_text += str(a + 1)
                else:
                    padding_text += '1'

            final_name = ''

            '''
            STRING CONSTRUCTION LOGIC:
                if a field is blank, it is removed (or not added)
                if a field is not blank and not locked, it is added
                if a field is locked, it is ignored, and the original is used
            '''

            if not lock_prefix:
                if prefix != '':
                    final_name += prefix + '_'
            if lock_prefix and item_name[1] != '':
                final_name += item_name[1] + '_'

            if not lock_name:
                if name != '':
                    final_name += name
            if lock_name and item_name[2] != '':
                final_name += item_name[2]

            if not lock_suffix:
                if suffix != '':
                    final_name += '_' + suffix
            if lock_suffix and item_name[3] != '':
                final_name += '_' + item_name[3]

            if not lock_padding:
                if padding_text != '':
                    final_name += '_' + padding_text
            if lock_padding and item_name[4] != '':
                final_name += '_' + item_name[4]

            # CREATE FINAL NAME
            print(final_name)
            if final_name != '':
                cmds.rename(items[i], final_name)
