import logging
import os
import json

import maya.cmds as cmds
import maya.mel as mel

from CETools.functions.commonFunctions import UndoStack


def transfer_animation(input_objects, target_objects, copy=False):
    with UndoStack('transfer_anim'):
        for input_obj, target_obj in zip(input_objects, target_objects):
            attrs = cmds.listAnimatable(input_obj)
            stripped_attrs = [".".join(s.split(".")[1:]) for s in attrs]

            for attr in stripped_attrs:
                input_anim = cmds.listConnections(f'{input_obj}.{attr}', type='animCurve')
                if input_anim:
                    input_plug = cmds.listConnections(f'{input_obj}.{attr}', type='animCurve', p=1)
                else:
                    continue

                if not copy:
                    if cmds.getAttr(f'{input_obj}.{attr}', l=1):
                        logging.warning(f'{input_obj}.{attr} is locked and will not transfer animation.')
                        continue
                    cmds.connectAttr(f"{input_plug[0]}", f"{target_obj}.{attr}", f=1)
                    cmds.disconnectAttr(f"{input_plug[0]}", f"{input_obj}.{attr}")

                if copy:
                    new_anim_input = cmds.duplicate(input_anim)[0]
                    cmds.connectAttr(f"{new_anim_input}.{input_plug[0].split('.')[-1]}", f"{target_obj}.{attr}")


def generate_expression():
    cmds.expression()


def get_bookmarks():
    bookmarks = cmds.ls(type='timeSliderBookmark')
    if not bookmarks:
        logging.warning('No time slider bookmarks found.')
        return
    bookmark_dict = {}
    for bookmark in bookmarks:
        bookmark_dict[bookmark] = {}
        bookmark_dict[bookmark]['name'] = cmds.getAttr(f'{bookmark}.name')
        bookmark_dict[bookmark]['frame_range'] = cmds.getAttr(f'{bookmark}.timeRange')[0]
    sorted_keys = sorted(bookmark_dict, key=lambda k: bookmark_dict[k]['frame_range'][0])
    sorted_bookmarks = {key: bookmark_dict[key] for key in sorted_keys}
    return sorted_bookmarks


def print_bookmarks():
    bookmarks_dict = get_bookmarks()
    for key in bookmarks_dict.keys():
        print(f"{bookmarks_dict[key]['name']}: {bookmarks_dict[key]['frame_range']}")


def offset_bookmarks(offset=1):
    bookmarks = cmds.ls(type='timeSliderBookmark')
    if not bookmarks:
        logging.warning('No time slider bookmarks found.')
        return
    for i, bookmark in enumerate(bookmarks):
        new_frame_start = cmds.getAttr(f'{bookmark}.timeRange')[0][0] + i + offset
        new_frame_end = cmds.getAttr(f'{bookmark}.timeRange')[0][1] + i + offset
        cmds.setAttr(f'{bookmark}.timeRangeStart', new_frame_start)
        cmds.setAttr(f'{bookmark}.timeRangeEnd', new_frame_end)


def snap_bookmarks():
    bookmarks_dict = get_bookmarks()
    if not bookmarks_dict:
        logging.warning('No time slider bookmarks found.')
        return


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


def bake_manip_to_locator():
    # Because USD is ass in 2022, I have to get the xform of the manip at every frame, save to a list (so that I
    # don't lose manip pos), and then convert that list to an animation. Fun.
    # THIS ALSO DOESN'T FUCKING WORK FOR SOME REASON, WHY DOES IT ONLY TAKE FIRST FRAME OF ROTATION???
    start = int(cmds.playbackOptions(q=1, min=1))
    end = int(cmds.playbackOptions(q=1, max=1))
    cmds.currentTime(start, e=1)
    manip = get_current_manip()
    manip_anim = {}
    attributes = ('translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ')
    for i in range(start, end+1):
        pos, rot = get_manip_xform(manip)
        print(rot)
        #pos.extend(rot)
        manip_anim[i] = [pos, rot]
        print(manip_anim[i])
        time = cmds.currentTime(q=1)
        cmds.currentTime(start + i, e=1)

    locator = cmds.spaceLocator()
    for i in range(start, end+1):
        cmds.xform(locator, t=manip_anim[i][0], ro=manip_anim[i][1], ws=1)
        #for j, at in enumerate(attributes):
        cmds.setKeyframe(locator, at=attributes, t=(i,))
