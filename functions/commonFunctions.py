import os
import math

import maya.cmds as cmds


class UndoStack(object):
    def __init__(self, name="actionName"):
        self.name = name

    def __enter__(self):
        cmds.undoInfo(openChunk=True, chunkName=self.name, infinity=True)

    def __exit__(self, typ, val, tb):
        cmds.undoInfo(closeChunk=True)


def refresh_dir(text_fields):
    scene_file = cmds.file(q=1, loc=1, un=0)
    if '/tasks' in scene_file:
        scene_directory = scene_file.split('/tasks')[0] + '/tasks'
    else:
        scene_directory = '/'.join(scene_file.split('/')[:-1])
    for textField in text_fields:
        textField.setText(scene_directory)
    return scene_directory


def get_node_details(args) -> dict:
    # Get node details for verification and scene-wide searching, intended to optimise CE rigging functions

    node_dict = {}
    for arg in args:
        uuid = cmds.ls(arg, uuid=1)[0]
        node_dict[uuid] = {}
        node_dict[uuid]['name'] = cmds.ls(arg)[0]
        node_dict[uuid]['long_name'] = cmds.ls(arg, l=1)[0]

        if cmds.listRelatives(arg, shapes=True, f=True):
            object_type = cmds.objectType(cmds.listRelatives(arg, shapes=True, f=True)[0])
        else:
            object_type = cmds.objectType(arg)
        node_dict[uuid]['type'] = object_type

    return node_dict


"""
float $fl_wheel_radius = 30.933398514986038 * root_ctrl.rigScale;

vector $fl_wheel_oldpos = `xform -q -ws -t "fl_wheel_oldpos"`;
vector $fl_wheel_newpos = `xform -q -ws -t "fl_wheel_grp"`;
vector $fl_wheel_dirpos = `xform -q -ws -t "fl_wheel_dir"`;

vector $fl_wheel_dir = ($fl_wheel_dirpos - $fl_wheel_newpos);
vector $fl_wheel_movement = ($fl_wheel_newpos - $fl_wheel_oldpos);

float $fl_wheel_distance = mag($fl_wheel_movement);
$fl_wheel_dot = dotProduct($fl_wheel_movement, $fl_wheel_dir, 1);

if (fl_wheel_ctrl.rotateType)
	fl_wheel_rotate.rotateX = fl_wheel_ctrl.manualRotate;

else if (fl_wheel_squash_ctrl.translateY < 0)
	fl_wheel_rotate.rotateX = fl_wheel_rotate.rotateX;

else
	fl_wheel_rotate.rotateX = fl_wheel_rotate.rotateX + 360/(6.283*$fl_wheel_radius) * ($fl_wheel_dot * $fl_wheel_distance) * fl_wheel_ctrl.rotateMulti;

matchTransform fl_wheel_oldpos fl_wheel_grp;

if (time == 0)
	fl_wheel_rotate.rotateX = 0;
$temp = root_ctrl.translateZ;




float $oldpos[] = `xform -q -ws -t "aircraft_oldpos"`;
float $newpos[] = `xform -q -ws -t "aircraft_currentpos"`;
vector $dirpos = `xform -q -ws -t "aircraft_dirpos"`;

vector $diff = $oldpos - $newpos;
float $diff_angle[] = `angleBetween -euler -v1 $oldpos -v2 $newpos`;


if (cog_ctrl.automationMasterSwitch == 1)

	rudder_choice.input[1] = $diff.y * cog_ctrl.rudderMulti;
	l_elevator_choice.input[1] = $diff.x * cog_ctrl.leftElevatorMulti;
	l_aileron_choice.input[1] = $diff.z * cog_ctrl.leftAileronMulti;
	r_aileron_choice.input[1] = $diff.z * cog_ctrl.rightAileronMulti;
	print $oldpos;
	print "\n";
	print $newpos;
	print "\n";
	print $diff_angle;
	print "\n\n";

	matchTransform aircraft_oldpos aircraft_currentpos;

geo_offset.translateY = noise(1+time*cog_ctrl.turbulenceFrequency)*cog_ctrl.turbulenceMulti*cog_ctrl.turbulenceTranslateMulti;
geo_offset.rotateX = noise(2+time*cog_ctrl.turbulenceFrequency)*cog_ctrl.turbulenceMulti*cog_ctrl.turbulenceRotationMulti;
geo_offset.rotateZ = noise(3+time*cog_ctrl.turbulenceFrequency)*cog_ctrl.turbulenceMulti*cog_ctrl.turbulenceRotationMulti;
"""


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


def lock_attributes(objects, attributes):
    for obj in objects:
        for at in attributes:
            cmds.setAttr(f'{obj}.{at}', lock=1, channelBox=0, keyable=0)


def get_object_type(item):
    if cmds.listRelatives(item, shapes=True, f=True):
        item_type = cmds.objectType(cmds.listRelatives(item, shapes=True, f=True)[0])
    else:
        item_type = cmds.objectType(item)
    return item_type


def get_subdirectory_from_directory(directory, subdirectory):
    new_path = os.path.abspath(os.path.join(os.path.dirname(directory), os.pardir, subdirectory))
    return new_path


def find_closest_folder(start_path, target):
    if os.path.exists(start_path):

        # Normalize the path first
        path = os.path.normpath(start_path)
        # Split the path into parts
        parts = path.split(os.sep)

        for i in range(len(parts), 0, -1):
            # Join the parts back to a path
            current_path = os.sep.join(parts[:i])
            # Check if the last part of the current path is the target folder
            if os.path.basename(current_path) == target:
                return current_path
    return None
