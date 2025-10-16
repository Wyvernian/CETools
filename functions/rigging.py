import logging
import os
import maya.cmds as cmds
import maya.api.OpenMaya as om2

from decimal import Decimal
from ast import literal_eval

from CETools.functions.commonFunctions import UndoStack, get_current_manip, get_manip_xform, get_node_details


def align_end_joint(joint=None):
    if joint is None:
        joint = cmds.ls(sl=1)[0]
    children = cmds.listRelatives(joint, ad=1, pa=1)
    for item in children:
        children = cmds.listRelatives(item, ad=1, pa=1)
        if children:
            pass
        else:
            cmds.joint(item, edit=1, oj="none", zso=1)


def deselect_ends():
    selected = cmds.ls(sl=1)
    for item in selected:
        children = cmds.listRelatives(item, ad=1, pa=1)
        if children:
            pass
        else:
            cmds.select(item, d=True)


def curve_on_selected(curve_degree=3):
    cmds.curve(d=curve_degree, p=[cmds.xform(x, q=True, ws=True, translation=True) for x in cmds.ls(sl=True)])


def toggle_local_rot_axes(state):
    selected = cmds.ls(sl=1)
    children = cmds.listRelatives(selected, ad=1, pa=1)
    for child in selected + children:
        cmds.setAttr(f"{child}.displayLocalAxis", state)


def set_rotate_order(ro):
    selected = cmds.ls(sl=1)
    for sel in selected:
        cmds.setAttr(f'{sel}.rotateOrder', ro)


def joint_positions(joints):
    pos = []
    for j in joints:
        pos.append(cmds.xform(j, q=True, t=True, ws=True))
    return pos


def create_clusters(crv):
    curve_cvs = cmds.ls('{0}.cv[:]'.format(crv), fl=1)
    for cv in curve_cvs:
        cmds.cluster(cv, rel=1)


def remove_recursion():
    selected = cmds.ls(sl=1)
    connections = cmds.listConnections()
    if selected in connections:
        pass


def spline_ik(div=3):
    sel = cmds.ls(sl=1)

    with UndoStack("splineIK"):
        joints = segment_selected(sel, div)

        joint_pos = joint_positions(joints)
        spline_crv = cmds.curve(d=3, p=joint_pos)
        cmds.ikHandle(sj=joints[0], ee=joints[-1], solver='ikSplineSolver', c=spline_crv, ccv=False)
        create_clusters(spline_crv)

        #cmds.joint()


def create_rope_rig(div=40, bezier=True, sub_controls=1):
    selected_joints = cmds.ls(sl=1, type='joint')

    if len(selected_joints) != 1:
        logging.warning('Select only the root joint')
        return
    root_grp = cmds.group(em=1, w=1, name='rope_rig_01')

    root_joint = selected_joints[0]
    align_end_joint(root_joint)
    cmds.select(root_joint, hi=True, r=1)
    original_joints = cmds.ls(sl=1)
    bound_joints = cmds.duplicate(rc=1)

    joints = segment_selected(original_joints, div)
    joints_pos = joint_positions(joints)

    if bezier:

        bound_joints = segment_selected(bound_joints, sub_controls + 1, parent_joints=False)

        bound_joints_pos = joint_positions(bound_joints)

        knots = list(range(len(bound_joints_pos)))
        curve_knots = [knot for knot in knots for _ in range(3)]

        curve_points = []
        curve_dict = {}
        for j, joint in enumerate(bound_joints_pos):
            in_point = []
            if 0 < j < len(bound_joints_pos):
                for i in range(3):
                    in_point.append(
                        bound_joints_pos[j][i] + (bound_joints_pos[j - 1][i] - bound_joints_pos[j][i]) * 1 / 2)

                curve_points.append(in_point)
                curve_points.append(in_point)

            curve_points.append(joint)

        spline_crv = cmds.curve(d=3, p=curve_points, k=curve_knots, bez=True)

    else:
        knots = list(range(len(joints_pos)))
        curve_knots = knots[:1] + knots[:1] + knots + knots[-1:] + knots[-1:]

        in_point, out_point = [], []
        for i in range(3):
            in_point.append(joints_pos[0][i] + (joints_pos[1][i] - joints_pos[0][i]) * 1 / 3)
            out_point.append(joints_pos[-1][i] + (joints_pos[-2][i] - joints_pos[-1][i]) * 1 / 3)

        curve_points = joints_pos[:]
        curve_points[1:1] = [in_point]
        curve_points[-1:-1] = [out_point]
        spline_crv = cmds.curve(d=3, p=curve_points, k=curve_knots)

    for joint in bound_joints:
        radius = cmds.getAttr(f'{joint}.radius')
        cmds.setAttr(f'{joint}.radius', radius * 3)

    ik_handle = cmds.ikHandle(sj=joints[0], ee=joints[-1], solver='ikSplineSolver', c=spline_crv, ccv=False)[0]

    bound_grp = cmds.group(bound_joints, w=1)
    bound_joints = cmds.listRelatives(bound_grp, c=1)
    radius = cmds.getAttr(f'{bound_joints[0]}.radius')

    ctrl_chain = []
    if bezier:
        for i, joint in enumerate(bound_joints):
            if i == 0:
                cvs = [f'{spline_crv}.cv[0]', f'{spline_crv}.cv[1]']

            elif i == len(bound_joints):
                cvs = [f'{spline_crv}.cv[-2]', f'{spline_crv}.cv[-1]']

            else:
                cvs = [f'{spline_crv}.cv[{i * 3 - 1}]', f'{spline_crv}.cv[{i * 3}]', f'{spline_crv}.cv[{i * 3 + 1}]']

            cluster = cmds.cluster(cvs, rel=1)
            pos = cmds.xform(joint, q=1, t=1, ws=1)
            rot = cmds.xform(joint, q=1, ro=1, ws=1)
            ctrl = cmds.circle(r=radius)
            ctrl_offset = cmds.group(ctrl, w=1)
            cmds.xform(ctrl_offset, t=pos, ro=rot)
            ctrl_chain.append(ctrl)
            ctrl_pos = cmds.xform(ctrl, q=1, t=1, ws=1)
            cmds.xform(cluster, rp=ctrl_pos, sp=ctrl_pos)
            cmds.parentConstraint(ctrl, cluster, mo=True)
            cmds.scaleConstraint(ctrl, cluster, mo=False)

    else:
        for i, joint in enumerate(bound_joints):
            pos = cmds.xform(joint, q=1, t=1, ws=1)
            rot = cmds.xform(joint, q=1, ro=1, ws=1)
            ctrl = cmds.circle(r=radius)
            ctrl_offset = cmds.group(ctrl, w=1)
            cmds.xform(ctrl_offset, t=pos, ro=rot)
            ctrl_chain.append(ctrl)
            cmds.parentConstraint(ctrl, joint, mo=False)
            '''
        if i > 0:
            cmds.parent(ctrl_offset, ctrl_chain[i - 1])
            '''
    cmds.setAttr(f'{ik_handle}.dTwistControlEnable', 1)
    cmds.setAttr(f'{ik_handle}.dForwardAxis', 4)
    cmds.setAttr(f'{ik_handle}.dWorldUpAxis', 0)
    cmds.setAttr(f'{ik_handle}.dWorldUpType', 4)
    cmds.connectAttr(f'{ctrl_chain[0]}.xformMatrix', f'{ik_handle}.dWorldUpMatrix')
    cmds.connectAttr(f'{ctrl_chain[-1]}.xformMatrix', f'{ik_handle}.dWorldUpMatrixEnd')

    # cmds.skinCluster(bound_joints, spline_crv, omi=1, mi=div)

    arclen = cmds.arclen(spline_crv, ch=1)
    stretch_mult = cmds.createNode('multiplyDivide', name='stretch_mult')
    cmds.connectAttr(f'{arclen}.arcLength', f'{stretch_mult}.input1X')
    cmds.setAttr(f'{stretch_mult}.operation', 2)
    cmds.setAttr(f'{stretch_mult}.input2X', cmds.getAttr(f'{arclen}.arcLength'))
    for joint in joints:
        cmds.connectAttr(f'{stretch_mult}.outputX', f'{joint}.scaleZ')

    plane_pos = [[0.5, 0, 0.5], [-0.5, 0, 0.5], [0.5, 0, -0.5], [-0.5, 0, -0.5]]
    planes = []
    for pos in plane_pos:
        plane = cmds.polyPlane(h=1, sx=1, sy=1)[0]
        planes.append(plane)
        cmds.xform(plane, t=pos)
    new_plane = cmds.polyUnite(planes, ch=0)[0]
    curve_length = cmds.arclen(spline_crv, ch=0)
    cmds.polyExtrudeFacet(f'{new_plane}.f[0:3]', inputCurve=spline_crv, d=curve_length, twist=curve_length * 30, ch=0)
    cmds.skinCluster(joints, new_plane)


def segment_selected(joints=None, val=3, parent_joints=True):
    if joints is None:
        joints = cmds.ls(sl=1, type='joint')
        if joints is None:
            logging.warning('Please select at least two joints')
            return

    joint_chain = [joints[0]]
    jnt = None
    cmds.select(joints[0], r=True)

    with UndoStack('segement_joints'):

        if len(joints) > 1:
            for j in range(len(joints) - 1):

                next_joint = cmds.listRelatives(joints[j], c=True)[0]
                tx = cmds.getAttr(next_joint + '.tx')
                ty = cmds.getAttr(next_joint + '.ty')
                tz = cmds.getAttr(next_joint + '.tz')
                rad = cmds.getAttr(next_joint + '.radius')

                for i in range(val - 1):
                    jnt = cmds.joint(rad=rad)
                    joint_chain.append(jnt)
                    cmds.xform(jnt, t=(tx / val, ty / val, tz / val), os=True)

                joint_chain.append(next_joint)
                if parent_joints is True:
                    cmds.parent(next_joint, jnt)

            if parent_joints is False:
                for i in range(1, len(joint_chain) - 1):
                    cmds.parent(joint_chain[i], w=1)

            return joint_chain

        else:
            logging.warning('Please select at least two joints')

def motion_path_velocity(target, motion_path, frame_start, frame_rate):
    exp = f"{motion_path}.uValue = ((time - {frame_start}/{frame_rate}) * {target}.forwardVelocity/{target}.distance * 100 / 3.6)%1;"


def add_signature(items, signatures):
    """
    This is used for detecting and removing matrix constraints,
    since its a litle more complicated to do that with nodes.
    """
    for s in signatures:
        for i, item in enumerate(items):
            cmds.addAttr(item, ln=s, at='message')
            if i > 0:
                cmds.connectAttr('{}.{}'.format(items[i - 1], s), '{}.{}'.format(item, s))


def find_object_type(item):
    if cmds.listRelatives(item, shapes=True, f=True):
        item_type = cmds.objectType(cmds.listRelatives(item, shapes=True, f=True)[0])
    else:
        item_type = cmds.objectType(item)
    return item_type


def constrain(translation=False, rotation=False, scale=False, maintain_offset=False):
    selection = cmds.ls(os=1)[0]
    parent = cmds.ls(os=1)[0]
    children = cmds.ls(os=1)[1:]

    with UndoStack("constrain"):

        for sel in children:

            parent = cmds.listRelatives(sel, p=1, pa=1)[0]
            object_type = find_object_type(sel)

            if object_type == 'joint':
                jnt_cm = cmds.createNode('composeMatrix', n=sel + '_joint_orient_cmtx')
                jnt_mm_a = cmds.createNode('multMatrix', n=sel + '_driven_jnt_mmtx')
                jnt_im = cmds.createNode('inverseMatrix', n=sel + 'jnt_dmtx')
                jnt_mm_b = cmds.createNode('multMatrix', n=sel + '_driver_jnt_mmtx')
                jnt_dm = cmds.createNode('decomposeMatrix', n=sel + 'jnt_dmtx')

                add_signature([jnt_cm, jnt_mm_a, jnt_im, jnt_mm_b, jnt_dm, sel], ['mtxJointOrient'])

                cmds.connectAttr('%s.jointOrient' % sel, '%s.inputRotate' % jnt_cm)

                cmds.connectAttr('%s.outputMatrix' % jnt_cm, '%s.matrixIn[0]' % jnt_mm_a)
                cmds.connectAttr('%s.worldMatrix[0]' % parent, '%s.matrixIn[1]' % jnt_mm_a)

                cmds.connectAttr('%s.matrixSum' % jnt_mm_a, '%s.inputMatrix' % jnt_im)

                cmds.connectAttr('%s.outputMatrix' % jnt_im, '%s.matrixIn[1]' % jnt_mm_b)
                cmds.connectAttr('%s.worldMatrix[0]' % parent, '%s.matrixIn[0]' % jnt_mm_b)

                cmds.connectAttr('%s.matrixSum' % jnt_mm_b, '%s.inputMatrix' % jnt_dm)

                cmds.connectAttr('%s.outputRotate' % jnt_dm, '%s.rotate' % sel)
                cmds.disconnectAttr('%s.jointOrient' % sel, '%s.inputRotate' % jnt_cm)

            mm = cmds.createNode('multMatrix', n=sel + '_mmtx')
            dm = cmds.createNode('decomposeMatrix', n=sel + '_dmtx')

            if maintain_offset:

                # do it in node form, cant be fucked with transformMatrix math in python
                mm_temp = cmds.createNode('multMatrix')
                try:
                    cmds.addAttr(parent, ln='offsetMatrix', at='matrix')
                except:
                    pass
                cmds.connectAttr('%s.worldMatrix[0]' % sel, '%s.matrixIn[0]' % mm_temp)
                cmds.connectAttr('%s.worldInverseMatrix[0]' % parent, '%s.matrixIn[1]' % mm_temp)
                cmds.connectAttr('%s.matrixSum' % mm_temp, '%s.offsetMatrix' % parent)

                cmds.connectAttr('%s.offsetMatrix' % parent, '%s.matrixIn[0]' % mm)
                cmds.connectAttr('%s.worldMatrix[0]' % parent, '%s.matrixIn[1]' % mm)
                cmds.connectAttr('%s.worldInverseMatrix[0]' % parent, '%s.matrixIn[2]' % mm)

                cmds.delete('%s.offsetMatrix' % parent, icn=True)
            else:
                cmds.connectAttr('%s.worldMatrix[0]' % parent, '%s.matrixIn[0]' % mm)
                cmds.connectAttr('%s.worldInverseMatrix[0]' % parent, '%s.matrixIn[1]' % mm)

            cmds.connectAttr('%s.matrixSum' % mm, '%s.inputMatrix' % dm)

            if translation:
                cmds.connectAttr('%s.outputTranslate' % dm, '%s.translate' % sel)
                add_signature([mm, dm, sel], ['mtxTranslate'])

            if rotation and object_type != 'joint':
                cmds.connectAttr('%s.outputRotate' % dm, '%s.rotate' % sel)
                add_signature([mm, dm, sel], ['mtxRotate'])

            if scale:
                cmds.connectAttr('%s.outputScale' % dm, '%s.scale' % sel)
                cmds.connectAttr('%s.outputShear' % dm, '%s.shear' % sel)
                add_signature([mm, dm, sel], ['mtxScale'])

            if maintain_offset:
                print('mo')
                mParent = cmds.xform(parent, q=1, m=1)
                mChild = cmds.xform(sel, q=1, m=1)
                print(mParent)
                print(mChild)


def ik_fk_blend():
    """
    Select three hierarchies, blend between the first two into the last.
    """
    selected = cmds.ls(os=1, l=1)
    drivers = selected[0:1]
    driven = selected[2]
    '''
    try:
        cmds.addAttr(driver_a, shortName="Blend Ik / FK", longName='blendIkFk', defaultValue=0.0, minValue=0.0, maxValue=1.0)
    except:
        pass
    '''
    hierarchies = {}
    for i in range(0, len(selected)):
        hierarchies[i] = [selected[i]]
        hierarchies[i] += list(reversed(cmds.listRelatives(selected[i], ad=1, pa=1, f=1, type='transform')))
    print(hierarchies)

    # blend = cmds.createNode('blendColors',n=driven+'_ik_fk_blend')
    # for drv, drvn in zip(hierarchies())


def parallel_parent():
    """
    An experimental workflow that keeps all objects on the same level of the hierarchy
    even if they are parented to one another. Might work better with parallel evaluation
    and GPUs, will need further testing. Also its cool.
    """

    sel = cmds.ls(os=1)
    root = cmds.listRelatives(sel, p=1, pa=1)[0]
    parent = sel[0]
    child = sel[1]

    with UndoStack("parallel"):

        for i in range(1, len(sel)):
            print(sel[i - 1], sel[i])
            mmTemp = cmds.createNode('multMatrix', n=sel[i] + '_temp_mmtx')
            invTemp = cmds.createNode('inverseMatrix', n=sel[i] + '_temp_imtx')
            mm = cmds.createNode('multMatrix', n=sel[i] + '_mmtx')

            try:
                cmds.addAttr(sel[i - 1], ln='offsetMatrix', at='matrix')
            except:
                pass

            cmds.connectAttr('%s.offsetParentMatrix' % sel[i - 1], '%s.inputMatrix' % invTemp)
            cmds.connectAttr('%s.outputMatrix' % invTemp, '%s.matrixIn[0]' % mmTemp)
            cmds.connectAttr('%s.offsetParentMatrix' % sel[i], '%s.matrixIn[1]' % mmTemp)

            cmds.connectAttr('%s.matrixSum' % mmTemp, '%s.offsetMatrix' % sel[i - 1])

            cmds.connectAttr('%s.offsetMatrix' % sel[i - 1], '%s.matrixIn[0]' % mm)
            cmds.connectAttr('%s.worldMatrix[0]' % sel[i - 1], '%s.matrixIn[1]' % mm)
            cmds.connectAttr('%s.worldInverseMatrix[0]' % root, '%s.matrixIn[2]' % mm)

            # cmds.delete('%s.offsetMatrix' % sel[i-1],icn=True)

            # cmds.connectAttr('%s.matrixSum' % mm, '%s.offsetParentMatrix' % sel[i])

            # cmds.delete(invTemp)


def negate_transforms(translation=False, rotation=False, scale=False, maintain_offset=False):
    selected = cmds.ls(sl=1)

    with UndoStack("negateTransforms"):

        for sel in selected:
            parent = sel
            rotation_order = cmds.xform(sel, q=1, roo=1)

            if scale is True:
                grp = cmds.group(em=1, n=sel + '_negate_s')
                divide = cmds.createNode('multiplyDivide', n=grp + '_md')
                cmds.setAttr('%s.operation' % divide, 2)
                cmds.setAttr('%s.input1X' % divide, 1)
                cmds.setAttr('%s.input1Y' % divide, 1)
                cmds.setAttr('%s.input1Z' % divide, 1)
                cmds.xform(grp, roo=rotation_order[::-1])
                cmds.connectAttr('%s.scale' % sel, '%s.input2' % divide)
                cmds.connectAttr('%s.output' % divide, '%s.scale' % grp)
                cmds.parent(grp, sel)
                parent = grp

            if rotation is True:
                grp = cmds.group(em=1, n=sel + '_negate_r')
                inverse = cmds.createNode('unitConversion', n=grp + '_uc')
                cmds.setAttr('%s.conversionFactor' % inverse, -1)
                cmds.xform(grp, roo=rotation_order[::-1])
                cmds.connectAttr('%s.rotate' % sel, '%s.input' % inverse)
                cmds.connectAttr('%s.output' % inverse, '%s.rotate' % grp)
                cmds.parent(grp, parent)
                parent = grp

            if translation is True:
                grp = cmds.group(em=1, n=sel + '_negate_t')
                inverse = cmds.createNode('unitConversion', n=grp + '_uc')
                cmds.setAttr('%s.conversionFactor' % inverse, -1)
                cmds.xform(grp, roo=rotation_order[::-1])
                cmds.connectAttr('%s.translate' % sel, '%s.input' % inverse)
                cmds.connectAttr('%s.output' % inverse, '%s.translate' % grp)
                cmds.parent(grp, parent)
                cmds.select(grp, r=1)


def space_switch():
    selected = cmds.ls(os=1)

    target = selected[-1]
    attr_location = selected[0]
    spaces = selected[1:-1]

    with UndoStack("spaceSwitch"):
        parent = cmds.listRelatives(target, p=1, pa=1)[0]

        offset_choice = cmds.createNode('choice', n=target + '_if_space_offset_choice')
        world_choice = cmds.createNode('choice', n=target + '_if_space_choice')
        space_mmtx = cmds.createNode('multMatrix', n=target + '_if_space_mmtx')
        space_dmtx = cmds.createNode('decomposeMatrix', n=target + '_dmtx')

        print('SPACE SWITCHER LOOP TEST BELOW')
        space_enum = ''.join("{}:".format(x) for x in spaces)[
                     :-1]  ## generate a string of "a:b:c:" and remove the last ""

        print(space_enum)
        cmds.addAttr(target, ln='space', at='enum', en=space_enum, k=1)

        for i, s in enumerate(spaces):
            cmds.connectAttr('%s.worldMatrix[0]' % s, '%s.input[%i]' % (world_choice, i))

            # i'll figure out what this means eventually
            offset_node_wm = om2.MMatrix(cmds.xform(target, q=True, m=True, ws=True))
            target_node_wm = om2.MMatrix(cmds.xform(s, q=True, m=True, ws=True))
            offset_matrix = offset_node_wm * target_node_wm.inverse()
            ass = ''.join('{},'.format(x) for x in offset_matrix)[:-1]
            mt = om2.MTransformationMatrix(offset_matrix)
            print(offset_matrix)
            print(ass)

            # add an attribute for each because maya is a bitch baby and doesnt like setting inputs as matrix directly
            cmds.addAttr(attr_location, ln=s.split('|')[-1] + '_offset', at='matrix')
            cmds.setAttr('{}.{}_offset'.format(attr_location, s.split('|')[-1]), *offset_matrix, type='matrix')
            cmds.connectAttr('{}.{}_offset'.format(attr_location, s.split('|')[-1]),
                             '{}.input[{}]'.format(offset_choice, i))

        cmds.connectAttr('%s.space' % target, '%s.selector' % offset_choice)
        cmds.connectAttr('%s.space' % target, '%s.selector' % world_choice)

        cmds.connectAttr('%s.output' % offset_choice, '%s.matrixIn[0]' % space_mmtx)
        cmds.connectAttr('%s.output' % world_choice, '%s.matrixIn[1]' % space_mmtx)
        cmds.connectAttr('%s.worldInverseMatrix' % attr_location, '%s.matrixIn[2]' % space_mmtx)

        cmds.connectAttr('%s.matrixSum' % space_mmtx, '%s.inputMatrix' % space_dmtx)

        cmds.connectAttr('%s.outputTranslate' % space_dmtx, '%s.translate' % parent)
        cmds.connectAttr('%s.outputRotate' % space_dmtx, '%s.rotate' % parent)


def align_pole_vector():
    selected = cmds.ls(os=1)
    if len(selected) != 4:
        logging.warning(
            "Select the root ik joint, mid ik joint, ik handle and pole vector control to create the pole vector.")
        return
    root = selected[0]
    mid = selected[1]
    ik = selected[2]
    pv = selected[3]

    root = cmds.listConnections(f'{pv}.startJoint')[0]
    effector = cmds.listConnections(f'{pv}.endEffector')[0]
    end = cmds.listConnections(f'{effector}.translate')[0]

    root_pos = om2.MVector(cmds.xform(root, q=1, rp=1, ws=1))
    mid_pos = om2.MVector(cmds.xform(mid, q=1, rp=1, ws=1))
    ik_pos = om2.MVector(cmds.xform(ik, q=1, rp=1, ws=1))

    root_to_ik = ik_pos - root_pos
    root_to_ik_scaled = root_to_ik / 2
    mid_point = root_pos + root_to_ik_scaled
    mid_point_to_mid_vec = (mid_pos - mid_point) * 2
    point = mid_point + mid_point_to_mid_vec
    cmds.xform(pv, t=point)


def offset_matrix(lock=True):
    """
    Freeze transforms using matrices. Not sure if this breaks anything I kinda developed this myself.
    Checks the current offsetParentMatrix and multiplies that with the transformMatrix, so that you can
    infinitely freeze the transform and it updates the matrix. It's like Freeze Transforms with
    no (current) drawbacks :) and it removes the need for offset groups in most cases.
    """
    selection = cmds.ls(sl=1)

    with UndoStack("offsetMatrix"):
        for s in selection:
            print(lock)
            xform_mtx = om2.MMatrix(cmds.xform(s, q=True, m=True, os=True))
            current_mtx = om2.MMatrix(cmds.getAttr('%s.offsetParentMatrix' % s))
            new_offset_mtx = xform_mtx * current_mtx

            if not lock:
                cmds.setAttr('%s.offsetParentMatrix' % s, lock=lock)
            cmds.setAttr('%s.offsetParentMatrix' % s, new_offset_mtx, type='matrix')
            if lock:
                cmds.setAttr('%s.offsetParentMatrix' % s, lock=lock)
            cmds.setAttr('%s.translate' % s, 0, 0, 0)
            cmds.setAttr('%s.rotate' % s, 0, 0, 0)
            cmds.setAttr('%s.scale' % s, 1, 1, 1)


'''
deleting these nodes needs a bit of work, but its good enough for now
'''


def traverse_nodes(node, attribute, node_list):
    connections = cmds.listConnections(node, d=False, s=True, p=True)
    if connections:
        for c in connections:
            if attribute in c:
                node_list.append(c)
                traverse_nodes(c, attribute, node_list)


def delete_constraint():
    selection = cmds.ls(sl=1) or []
    node_list = []
    for s in selection:
        traverse_nodes(s, 'mtx', node_list)
        cmds.deleteAttr('%s.mtxJointOrient' % s)
        cmds.deleteAttr('%s.mtxTranslate' % s)
        cmds.deleteAttr('%s.mtxRotate' % s)
        cmds.deleteAttr('%s.mtxScale' % s)

    for n in node_list:
        node = n.split('.')[0]
        try:
            cmds.delete(node)
        except ValueError:  ## when it stops working, delete attributes on selected
            pass


def set_index_color(index, selection=None, in_outliner=False):
    if selection is None:
        selection = cmds.ls(sl=1)

    with UndoStack("set_index_color"):

        for sel in selection:
            if not in_outliner:
                if (cmds.listRelatives(sel, s=1, pa=1)) is None:
                    cmds.setAttr(sel + ".overrideEnabled", 1)
                    cmds.setAttr(sel + ".overrideRGBColors", 0)
                    cmds.setAttr(sel + ".overrideColor", index)

                else:
                    for sh in cmds.listRelatives(sel, s=1, pa=1):
                        cmds.setAttr(sh + ".overrideEnabled", 1)
                        cmds.setAttr(sh + ".overrideRGBColors", 0)
                        cmds.setAttr(sh + ".overrideColor", index)
            else:
                color = cmds.colorIndex(index, q=1)
                cmds.setAttr(sel + ".useOutlinerColor", 1)
                cmds.setAttr(sel + ".outlinerColor", *color, type='double3')
    return index


def save_custom_curve(dir_path):
    selected = cmds.ls(sl=1)

    if not selected:
        logging.warning("Select a NURBS curve.")
        return

    for sel in selected:
        if cmds.objectType(cmds.listRelatives(sel, s=1)[0]) != 'nurbsCurve':
            logging.warning("This function only supports NURBS curves.")
            return

    selected = combine_curves(selected)

    # RETRIEVE ALL CURVE DATA
    shapes = cmds.listRelatives(selected, s=1)
    out = ''

    for shp in shapes:

        try:
            cvs = cmds.getAttr(shp + '.cv[*]')
            curve_cvs = cmds.ls('{0}.cv[:]'.format(shp), fl=True)
            new_cv = []
            for cv in curve_cvs:
                cv_extended = [cmds.pointPosition(cv, l=True)]
                for c in cv_extended:
                    new_cv.append([float(Decimal("%.3f" % c[0])), float(Decimal("%.3f" % c[1])),
                                   float(Decimal("%.3f" % c[2]))])

            cvs_simple = []
            for c in cvs:
                cvs_simple.append(
                    [float(Decimal("%.3f" % c[0])), float(Decimal("%.3f" % c[1])), float(Decimal("%.3f" % c[2]))])

            degree = cmds.getAttr(shp + '.degree')
            spans = cmds.getAttr(shp + '.spans')
            form = cmds.getAttr(shp + '.form')
            cv_count = len(curve_cvs)

            knot_count = cv_count + degree - 1
            knots_array = [0] * knot_count
            for i in range(0, len(knots_array) - degree + 1):
                knots_array[i + degree - 1] = i

            out += '%s' % ', '.join(map(str, new_cv))
            out += ':' + '%s' % ', '.join(map(str, knots_array))
            out += ':' + str(degree)
            out += ':' + str(form) + "\n"

        except ValueError:
            logging.warning("Invalid curve values, skipping {}".format(shp))
            continue

    return out


def duplicate_hierarchy(node, node_parent, number, crv):
    children = cmds.listRelatives(node, children=True, type='joint', f=True)

    if children or number == 0:

        path = node
        objects = path.split('|')
        new_name = objects[-1]
        position = cmds.xform(node, ws=True, t=True, q=True)

        # duplicate the base control

        ctrl = cmds.duplicate(crv, rc=True)
        group = cmds.group(ctrl, n=new_name + '_grp')
        cmds.xform(group, piv=(0, 0, 0))

        cmds.select(group, replace=True)

        cmds.parentConstraint(node, group, mo=0)
        cmds.delete(cmds.parentConstraint(node, group))
        cmds.parentConstraint(ctrl, node, mo=0)

        parent_to = ctrl
        node_locator = group  # cmds.rename(new_name)
        cmds.move(position[0], position[1], position[2], a=True)
        if node_parent:
            cmds.parent(node_locator, node_parent)

        number += 1
        if children:
            for child in children:
                if not cmds.listRelatives(child):
                    cmds.delete(crv)
                else:
                    number = duplicate_hierarchy(child, parent_to, number, crv)  # parent_to is normally node_locator
        else:
            cmds.delete(crv)
    else:
        cmds.delete(crv)

    return number


def select_same_type_below(object_type, parents=None):
    if parents is None:
        parents = cmds.ls(sl=1)

    children = cmds.listRelatives(parents, ad=1, f=1)
    for child in children:
        child_type = find_object_type(child)
        if child_type == object_type:
            cmds.select(child, add=1)


def build_custom_curve(dir_path, curve_name, replace=False, to_bbox_scale=True):
    current_manip = get_current_manip()
    if current_manip:
        pos, rot = get_manip_xform(ctx=current_manip)

    curve_path = os.path.join(dir_path, curve_name + '.crv')
    curve_inputs = []

    if os.path.exists(curve_path):
        with open(curve_path, "r") as f:
            lines = f.readlines()
            for i in range(0, len(lines)):
                curve_inputs.append(str(lines[i]).strip("\n"))
    else:
        return

    with UndoStack("buildCustom"):

        selected = cmds.ls(sl=1)
        curves = []
        for i, curve_input in enumerate(curve_inputs):
            points_list, knots_list, degrees, period = curve_input.split(":")

            # OPEN CURVES DONT HAVE KNOTS, P == 0
            if int(period) == 0:
                curves.append(cmds.curve(p=literal_eval(points_list), d=int(degrees), ws=True))
            else:
                curves.append(
                    cmds.curve(p=literal_eval(points_list), d=int(degrees), k=literal_eval(knots_list), ws=True))
            # IF CLOSED/PERIODIC CURVE, CLOSE
            if int(period) == 2:
                cmds.closeCurve(curves[i], ch=False, rpo=True, ps=False)

        combine = combine_curves(curves, name=curve_name)

        if replace:
            for sel in selected:
                if not find_object_type(sel) == "nurbsCurve":
                    continue
                sel_curve_shapes = cmds.listRelatives(sel, s=1, f=1)
                color_index = cmds.getAttr(f'{sel_curve_shapes[0]}.overrideColor')
                override_enabled = cmds.getAttr(f'{sel_curve_shapes[0]}.overrideEnabled')

                new_curve = cmds.duplicate(combine, rc=1, f=1)
                new_curve_shapes = cmds.listRelatives(new_curve, s=1, f=1)
                if to_bbox_scale:
                    # cmds.makeIdentity(sel, s=1)
                    sel_bbox = cmds.exactWorldBoundingBox(sel_curve_shapes)
                    new_bbox = cmds.exactWorldBoundingBox(new_curve_shapes)
                    curve_cvs = cmds.ls('{0}.cv[:]'.format(new_curve[0]), fl=1)
                    sel_curve_radius = max(
                        [sel_bbox[3] - sel_bbox[0], sel_bbox[4] - sel_bbox[1], sel_bbox[5] - sel_bbox[2]])
                    new_curve_radius = max(
                        [new_bbox[3] - new_bbox[0], new_bbox[4] - new_bbox[1], new_bbox[5] - new_bbox[2]])
                    radius = sel_curve_radius / new_curve_radius
                    print(sel_bbox, sel_curve_radius)
                    print(new_bbox, new_curve_radius)
                    cmds.scale(radius, radius, radius, curve_cvs, ocp=1, r=1)

                if override_enabled:
                    for shape in new_curve_shapes:
                        cmds.setAttr(f'{shape}.overrideColor', color_index)
                        cmds.setAttr(f'{shape}.overrideEnabled', 1)

                cmds.delete(sel_curve_shapes)
                cmds.parent(new_curve_shapes, sel, r=1, s=1)
                cmds.delete(new_curve)
            cmds.delete(combine)
            cmds.select(selected, r=1)

        elif selected:
            if current_manip:
                cmds.xform(combine, t=pos, ro=rot)

            elif cmds.objectType(selected) == "joint":
                duplicate_hierarchy(selected[0], '', 0, combine)
            else:
                cmds.group()

            # cl.attachCtrl(combine, selected)
            # elif cmds.objectType(cmds.listRelatives(selected[0],s=1,pa=1)[0],isType='nurbsCurve'):
            #    cl.replaceCurve(combine, selected)


def attach_control_curve(curve, item):
    group = cmds.group(curve, w=True)
    cmds.xform(group, piv=(0, 0, 0))
    cmds.delete(cmds.parentConstraint(item, group, mo=0))
    cmds.parentConstraint(curve, item, mo=0)
    cmds.select(curve)


def combine_curves(curves, name='newCombinedCtl'):
    curve_shapes = cmds.listRelatives(curves, s=True)

    # freeze transforms of selected curves
    cmds.makeIdentity(curves, apply=True, t=True, r=True, s=True)

    # create null transform to parent shapes to
    combine_curve = cmds.group(em=True, name=name)
    # parent shapes to null
    parent = cmds.parent(curve_shapes, combine_curve, s=True, r=True)
    # remove old transforms
    cmds.delete(curves)
    cmds.select(combine_curve)

    return combine_curve


def parent_stack(*args):
    for i in range(len(args)):
        if i > 0:
            cmds.parent(args[i - 1], args[i])


def clusters_on_selected():
    selected = cmds.ls(sl=1, fl=1)
    with UndoStack('clusters_on_selected'):
        for sel in selected:
            # WOW, crazy stuff!
            cmds.cluster(sel)


def lock_attributes(objects, attributes):
    for obj in objects:
        for at in attributes:
            cmds.setAttr(f'{obj}.{at}', lock=1, channelBox=0, keyable=0)


def create_tyre_rig(root_ctrl, wheel_ctrl_parent, wheel_geo_parent, is_steerable, steer_ctrl=None):
    wheels = cmds.ls(sl=1, l=1)

    with UndoStack('tyre_rig'):

        for i, wheel in enumerate(wheels):

            cmds.select(clear=1)
            wheel_pos = cmds.xform(wheel, q=1, ws=1, t=1)
            wheel_radius = (cmds.exactWorldBoundingBox(wheel)[4] - cmds.exactWorldBoundingBox(wheel)[1]) / 2

            wheel_rotate = cmds.joint(n=f'{wheel}_rotate')
            cmds.xform(wheel_rotate, t=wheel_pos)

            wheel_oldpos = cmds.spaceLocator(n=f'{wheel}_oldpos')[0]
            cmds.xform(wheel_oldpos, t=wheel_pos)

            wheel_dir = cmds.spaceLocator(n=f'{wheel}_dir')[0]
            cmds.xform(wheel_dir, ws=1, t=wheel_pos)
            cmds.xform(wheel_dir, r=1, t=(0, 0, 5))

            wheel_ctrl = cmds.circle(n=f'{wheel}_ctrl', r=wheel_radius * 1.05, nr=(1, 0, 0))[0]
            wheel_ctrl_offset = cmds.group(n=f'{wheel}_ctrl_offset')
            cmds.xform(wheel_ctrl_offset, ws=1, t=wheel_pos)

            wheel_grp = cmds.group(em=1, n=f'{wheel}_grp')
            cmds.xform(wheel_grp, ws=1, t=wheel_pos)
            cmds.xform(wheel_ctrl, t=(0, 0, 0))

            children = cmds.listRelatives(wheel, ad=1, f=1, type='transform')
            for child in children:
                if 'tyre' in child:
                    target = child
                else:
                    target = wheel

            lattice = cmds.lattice(target, dv=(5, 10, 10), oc=1)
            cmds.select(clear=1)
            for j in range(1, 9):
                cmds.select(f'{lattice[1]}.pt[0:4][0][{j}]', add=1)
            cluster = cmds.cluster(rel=1)

            wheel_squash_ctrl = cmds.circle(n=f'{wheel}_squash_ctrl', r=wheel_radius * 0.8, nr=(0, 1, 0))[0]
            lock_attributes([wheel_squash_ctrl], ['tx', 'tz', 'sx', 'sy', 'sz', 'visibility'])
            cmds.setAttr(f'{wheel_squash_ctrl}.rotateOrder', 1)
            cmds.addAttr(ln='tyrePressureMulti', nn='Tyre Pressure Multi', at='float', dv=0.15, min=0.01,
                         max=10,
                         k=1)

            squash_multi = cmds.createNode('floatMath', n=f'{wheel}_squash_multi')
            squash_con = cmds.createNode('condition', n=f'{wheel}_squash_con')
            squash_add = cmds.createNode('floatMath', n=f'{wheel}_squash_add')

            squash_rot_con = cmds.createNode('condition', n=f'{wheel}_squash_rot_con')

            cmds.connectAttr(f'{wheel_squash_ctrl}.translateY', f'{squash_rot_con}.firstTerm')
            cmds.connectAttr(f'{wheel_squash_ctrl}.rotate', f'{squash_rot_con}.colorIfFalse')
            cmds.setAttr(f'{squash_rot_con}.operation', 4)

            cmds.connectAttr(f'{wheel_squash_ctrl}.translateY', f'{squash_con}.firstTerm')
            cmds.connectAttr(f'{wheel_squash_ctrl}.translateY', f'{squash_con}.colorIfTrueG')
            cmds.setAttr(f'{squash_con}.operation', 2)
            cmds.setAttr(f'{squash_con}.colorIfFalseG', 0)

            cmds.connectAttr(f'{wheel_squash_ctrl}.translateY', f'{squash_multi}.floatA')
            cmds.connectAttr(f'{wheel_squash_ctrl}.tyrePressureMulti', f'{squash_multi}.floatB')
            cmds.setAttr(f'{squash_multi}.operation', 2)

            cmds.connectAttr(f'{squash_multi}.outFloat', f'{squash_add}.floatB')

            cmds.connectAttr(f'{squash_add}.outFloat', f'{squash_con}.colorIfTrueR')

            cmds.connectAttr(f'{squash_con}.outColorR', f'{cluster[1]}.scaleX')
            cmds.connectAttr(f'{squash_con}.outColorG', f'{cluster[1]}.translateY')
            cmds.connectAttr(f'{squash_rot_con}.outColorR', f'{cluster[1]}.rotateX')
            cmds.connectAttr(f'{squash_rot_con}.outColorB', f'{cluster[1]}.rotateZ')

            cmds.transformLimits(wheel_squash_ctrl, tx=(0, 0), etx=(1, 1), tz=(0, 0), etz=(1, 1))
            cmds.transformLimits(cluster[1], ty=(0, 10), ety=(1, 1))

            cmds.normalConstraint('pPlane1', wheel_squash_ctrl, aim=(0, 1, 0), u=(1, 0, 1))
            cmds.geometryConstraint('pPlane1', wheel_squash_ctrl)

            cluster_offset_grp = cmds.group(cluster)

            wheel_squash_ctrl_offset = cmds.group(wheel_squash_ctrl, n=f'{wheel}_squash_ctrl_offset')

            parent_constraint = cmds.parentConstraint(cluster_offset_grp, wheel_squash_ctrl_offset)
            cmds.delete(parent_constraint)

            cmds.parent(lattice[1:3], cluster_offset_grp, wheel_grp)
            cmds.parent(wheel_squash_ctrl_offset, wheel_ctrl)

            if not wheel_squash_ctrl:
                wheel_squash_ctrl = cmds.spaceLocator(n=f'{wheel}_floor_loc')[0]
                cmds.parent(wheel_squash_ctrl, wheel_ctrl)
                cmds.geometryConstraint('pPlane1', wheel_squash_ctrl)
                wheel_squash_ctrl_offset = cmds.group(wheel_squash_ctrl, n=f'{wheel}_squash_ctrl_offset')

                cmds.xform(wheel_squash_ctrl_offset, t=(wheel_pos[0], 0, wheel_pos[2]))

            cmds.parentConstraint(wheel_rotate, wheel)

            cmds.select(wheel_ctrl)
            cmds.addAttr(ln='rotateMulti', nn='Rotate Multi', at='float', k=1, min=0.01, max=100, dv=1)
            cmds.addAttr(ln='manualRotate', nn='Manual Rotate', at='float', k=1)
            cmds.addAttr(ln='rotateType', nn='Rotate Type', at='enum', enumName="Auto:Manual", k=1)

            lock_attributes([wheel_ctrl], ['tx', 'tz', 'rx', 'sx', 'sy', 'sz', 'visibility'])

            # Parent things

            cmds.parent(wheel_dir, wheel_rotate, wheel_grp)
            cmds.parent(wheel_grp, wheel_ctrl)

            if is_steerable and steer_ctrl:
                cmds.connectAttr(f'{steer_ctrl}.rotate', f'{wheel_grp}.rotate')

            cmds.parent(wheel_ctrl_offset, wheel_ctrl_parent)

            cmds.parent(wheel_oldpos, wheel_geo_parent)

            wheel_name = wheel.split(':')[-1]

            height_calc_exp = f"\nfloat ${wheel_name}_radius = {wheel_radius} * {root_ctrl}.rigScale;\n"
            store_position_exp = f"\nvector ${wheel_name}_oldpos = `xform -q -ws -t \"{wheel_oldpos}\"`;\nvector ${wheel_name}_newpos = `xform -q -ws -t \"{wheel_grp}\"`;\nvector ${wheel_name}_dirpos = `xform -q -ws -t \"{wheel_dir}\"`;\n"
            wheel_dir_exp = f"\nvector ${wheel_name}_dir = (${wheel_name}_dirpos - ${wheel_name}_newpos);\nvector ${wheel_name}_movement = (${wheel_name}_newpos - ${wheel_name}_oldpos);\n"
            wheel_mag_exp = f"\nfloat ${wheel_name}_distance = mag(${wheel_name}_movement);\n${wheel_name}_dot = dotProduct(${wheel_name}_movement, ${wheel_name}_dir, 1);\n"
            wheel_if = f"\nif ({wheel_ctrl}.rotateType)\n\t{wheel_rotate}.rotateX = {wheel_ctrl}.manualRotate;\n\nelse if ({wheel_squash_ctrl}.translateY < 0)\n\t{wheel_rotate}.rotateX = {wheel_rotate}.rotateX;\n\nelse\n\t"
            joint_rotation_exp = f"{wheel_rotate}.rotateX = {wheel_rotate}.rotateX + 360/(6.283*${wheel_name}_radius) * (${wheel_name}_dot * ${wheel_name}_distance) * {wheel_ctrl}.rotateMulti;\n"
            move_old_pos_loc_exp = f"\nmatchTransform {wheel_oldpos} {wheel_grp};\n"
            reset_rot = f"\nif (time == 0)\n\t{wheel_rotate}.rotateX = 0;"
            force_update_exp = f"\n$temp = {root_ctrl}.translateZ;\n"

            cmds.expression(ae=1, an=1, n=f'wheel_rotation_{i + 1}',
                            s=f'{height_calc_exp}{store_position_exp}{wheel_dir_exp}{wheel_mag_exp}{wheel_if}'
                              f'{joint_rotation_exp}{move_old_pos_loc_exp}{reset_rot}{force_update_exp}')

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
            """


def create_vehicle_rig(name='vehicle'):
    selected = cmds.ls(sl=1)
    car_root = selected[0]
    wheels = selected[1:-1]
    body = selected[-1]

    with UndoStack('vehicle_rig'):

        wheels_bbox = cmds.exactWorldBoundingBox(wheels)
        wheels_center = (wheels_bbox[5] - wheels_bbox[2]) / 2

        vehicle_bbox = cmds.exactWorldBoundingBox(body)
        vehicle_scale = max([vehicle_bbox[3] - vehicle_bbox[0], vehicle_bbox[5] - vehicle_bbox[2]])

        if len(wheels) > 3:
            steered_wheels = wheels[0:2]
        else:
            steered_wheels = wheels[0]
        steer_pivot = cmds.xform(wheels[0], q=1, ws=1, t=1)

        # Create Base Rig
        rig_grp = cmds.group(em=1, n=f'{name}_rig_grp')
        controls_grp = cmds.group(em=1, n='controls_grp')
        geo_grp = cmds.group(em=1, n='geometry_grp')
        steer_grp = cmds.group(em=1, n='steer_grp')

        cmds.xform(steer_grp, t=(0, steer_pivot[1], steer_pivot[2]), ws=1)

        # root ctrl
        root_ctrl = cmds.circle(n='root_ctrl', r=vehicle_scale / 1.5, nr=(0, 1, 0))[0]
        # cmds.xform(root_ctrl, t=(0, steer_pivot[1], 0), ws=1)
        # set_index_color(17, root_ctrl)
        lock_attributes([root_ctrl], ['sx', 'sy', 'sz', 'visibility'])
        cmds.addAttr(ln='rigScale', nn='Rig Scale', at='float', dv=1, min=0.01, max=100)
        root_grp = cmds.group(root_ctrl, n='root_grp', r=1)

        # root ctrl
        main_ctrl = cmds.circle(n='main_ctrl', r=vehicle_scale / 2, nr=(0, 1, 0))[0]
        # cmds.xform(root_ctrl, t=(0, steer_pivot[1], 0), ws=1)
        # set_index_color(17, root_ctrl)
        lock_attributes([main_ctrl], ['sx', 'sy', 'sz', 'visibility'])
        cmds.addAttr(ln='rigScale', nn='Rig Scale', at='float', dv=1, min=0.01, max=100)
        main_grp = cmds.group(main_ctrl, n='main_grp', r=1)

        # steer ctrl
        steer_ctrl = cmds.circle(n='steer_ctrl', r=vehicle_scale / 4, nr=(0, 1, 0))[0]
        # set_index_color(14, steer_ctrl)
        lock_attributes([steer_ctrl], ['tx', 'ty', 'tz', 'rx', 'rz', 'sx', 'sy', 'sz', 'visibility'])
        cmds.transformLimits(steer_ctrl, ry=(-45, 45), ery=(1, 1))

        # Parent things

        cmds.parent(steer_ctrl, steer_grp)
        cmds.parent(steer_grp, main_ctrl)
        cmds.parent(main_grp, root_ctrl)
        cmds.parent(root_grp, controls_grp)
        cmds.parent(controls_grp, geo_grp, rig_grp)

        # bad way of fixing paths
        steer_ctrl = f'|{rig_grp}|{controls_grp}|{root_grp}|{root_ctrl}|{main_grp}|{main_ctrl}|{steer_grp}|{steer_ctrl}'

        for i, wheel in enumerate(wheels):

            cmds.select(clear=1)
            wheel_pos = cmds.xform(wheel, q=1, ws=1, t=1)
            wheel_radius = (cmds.exactWorldBoundingBox(wheel)[4] - cmds.exactWorldBoundingBox(wheel)[1]) / 2

            wheel_rotate = cmds.joint(n=f'{wheel}_rotate')
            cmds.xform(wheel_rotate, t=wheel_pos)

            wheel_oldpos = cmds.spaceLocator(n=f'{wheel}_oldpos')[0]
            cmds.xform(wheel_oldpos, t=wheel_pos)

            wheel_dir = cmds.spaceLocator(n=f'{wheel}_dir')[0]
            cmds.xform(wheel_dir, ws=1, t=wheel_pos)
            cmds.xform(wheel_dir, r=1, t=(0, 0, 5))

            wheel_ctrl = cmds.circle(n=f'{wheel}_ctrl', r=wheel_radius * 1.05, nr=(1, 0, 0))[0]
            wheel_ctrl_offset = cmds.group(n=f'{wheel}_ctrl_offset')
            cmds.xform(wheel_ctrl_offset, ws=1, t=wheel_pos)

            wheel_grp = cmds.group(em=1, n=f'{wheel}_grp')
            cmds.xform(wheel_grp, ws=1, t=wheel_pos)
            cmds.xform(wheel_ctrl, t=(0, 0, 0))

            wheel_squash_ctrl = None

            children = cmds.listRelatives(wheel, ad=1, f=1, type='transform')
            for child in children:
                if 'tyre' in child:
                    target = child
                else:
                    target = wheel

            lattice = cmds.lattice(target, dv=(5, 10, 10), oc=1)
            cmds.select(clear=1)
            for j in range(1, 9):
                cmds.select(f'{lattice[1]}.pt[0:4][0][{j}]', add=1)
            cluster = cmds.cluster(rel=1)

            wheel_squash_ctrl = cmds.circle(n=f'{wheel}_squash_ctrl', r=wheel_radius * 0.8, nr=(0, 1, 0))[0]
            lock_attributes([wheel_squash_ctrl], ['tx', 'tz', 'sx', 'sy', 'sz', 'visibility'])
            cmds.setAttr(f'{wheel_squash_ctrl}.rotateOrder', 1)
            cmds.addAttr(ln='tyrePressureMulti', nn='Tyre Pressure Multi', at='float', dv=0.15, min=0.01,
                         max=10,
                         k=1)

            squash_multi = cmds.createNode('floatMath', n=f'{wheel}_squash_multi')
            squash_con = cmds.createNode('condition', n=f'{wheel}_squash_con')
            squash_add = cmds.createNode('floatMath', n=f'{wheel}_squash_add')

            squash_rot_con = cmds.createNode('condition', n=f'{wheel}_squash_rot_con')

            cmds.connectAttr(f'{wheel_squash_ctrl}.translateY', f'{squash_rot_con}.firstTerm')
            cmds.connectAttr(f'{wheel_squash_ctrl}.rotate', f'{squash_rot_con}.colorIfFalse')
            cmds.setAttr(f'{squash_rot_con}.operation', 4)

            cmds.connectAttr(f'{wheel_squash_ctrl}.translateY', f'{squash_con}.firstTerm')
            cmds.connectAttr(f'{wheel_squash_ctrl}.translateY', f'{squash_con}.colorIfTrueG')
            cmds.setAttr(f'{squash_con}.operation', 2)
            cmds.setAttr(f'{squash_con}.colorIfFalseG', 0)

            cmds.connectAttr(f'{wheel_squash_ctrl}.translateY', f'{squash_multi}.floatA')
            cmds.connectAttr(f'{wheel_squash_ctrl}.tyrePressureMulti', f'{squash_multi}.floatB')
            cmds.setAttr(f'{squash_multi}.operation', 2)

            cmds.connectAttr(f'{squash_multi}.outFloat', f'{squash_add}.floatB')

            cmds.connectAttr(f'{squash_add}.outFloat', f'{squash_con}.colorIfTrueR')

            cmds.connectAttr(f'{squash_con}.outColorR', f'{cluster[1]}.scaleX')
            cmds.connectAttr(f'{squash_con}.outColorG', f'{cluster[1]}.translateY')
            cmds.connectAttr(f'{squash_rot_con}.outColorR', f'{cluster[1]}.rotateX')
            cmds.connectAttr(f'{squash_rot_con}.outColorB', f'{cluster[1]}.rotateZ')

            cmds.transformLimits(wheel_squash_ctrl, tx=(0, 0), etx=(1, 1), tz=(0, 0), etz=(1, 1))
            cmds.transformLimits(cluster[1], ty=(0, 10), ety=(1, 1))

            cmds.normalConstraint('pPlane1', wheel_squash_ctrl, aim=(0, 1, 0), u=(1, 0, 1))
            cmds.geometryConstraint('pPlane1', wheel_squash_ctrl)

            cluster_offset_grp = cmds.group(cluster)

            wheel_squash_ctrl_offset = cmds.group(wheel_squash_ctrl, n=f'{wheel}_squash_ctrl_offset')

            parent_constraint = cmds.parentConstraint(cluster_offset_grp, wheel_squash_ctrl_offset)
            cmds.delete(parent_constraint)

            cmds.parent(lattice[1:3], cluster_offset_grp, wheel_grp)
            cmds.parent(wheel_squash_ctrl_offset, wheel_ctrl)

            if not wheel_squash_ctrl:
                wheel_squash_ctrl = cmds.spaceLocator(n=f'{wheel}_floor_loc')[0]
                cmds.parent(wheel_squash_ctrl, wheel_ctrl)
                cmds.geometryConstraint('pPlane1', wheel_squash_ctrl)
                wheel_squash_ctrl_offset = cmds.group(wheel_squash_ctrl, n=f'{wheel}_squash_ctrl_offset')

                cmds.xform(wheel_squash_ctrl_offset, t=(wheel_pos[0], 0, wheel_pos[2]))

            cmds.parentConstraint(wheel_rotate, wheel)

            cmds.select(wheel_ctrl)
            cmds.addAttr(ln='rotateMulti', nn='Rotate Multi', at='float', k=1, min=0.01, max=100, dv=1)
            cmds.addAttr(ln='manualRotate', nn='Manual Rotate', at='float', k=1)
            cmds.addAttr(ln='rotateType', nn='Rotate Type', at='enum', enumName="Auto:Manual", k=1)

            lock_attributes([wheel_ctrl], ['tx', 'tz', 'rx', 'sx', 'sy', 'sz', 'visibility'])

            # Parent things

            cmds.parent(wheel_dir, wheel_rotate, wheel_grp)
            cmds.parent(wheel_grp, wheel_ctrl)

            if wheel in steered_wheels:
                cmds.connectAttr(f'{steer_ctrl}.rotate', f'{wheel_grp}.rotate')

            cmds.parent(wheel_ctrl_offset, f'|{rig_grp}|{controls_grp}|{root_grp}|{root_ctrl}|{main_grp}|{main_ctrl}')

            cmds.parent(wheel_oldpos, f'|{rig_grp}|{geo_grp}')

            wheel_name = wheel.split(':')[-1]

            height_calc_exp = f"\nfloat ${wheel_name}_radius = {wheel_radius} * {root_ctrl}.rigScale;\n"
            store_position_exp = f"\nvector ${wheel_name}_oldpos = `xform -q -ws -t \"{wheel_oldpos}\"`;\nvector ${wheel_name}_newpos = `xform -q -ws -t \"{wheel_grp}\"`;\nvector ${wheel_name}_dirpos = `xform -q -ws -t \"{wheel_dir}\"`;\n"
            wheel_dir_exp = f"\nvector ${wheel_name}_dir = (${wheel_name}_dirpos - ${wheel_name}_newpos);\nvector ${wheel_name}_movement = (${wheel_name}_newpos - ${wheel_name}_oldpos);\n"
            wheel_mag_exp = f"\nfloat ${wheel_name}_distance = mag(${wheel_name}_movement);\n${wheel_name}_dot = dotProduct(${wheel_name}_movement, ${wheel_name}_dir, 1);\n"
            wheel_if = f"\nif ({wheel_ctrl}.rotateType)\n\t{wheel_rotate}.rotateX = {wheel_ctrl}.manualRotate;\n\nelse if ({wheel_squash_ctrl}.translateY < 0)\n\t{wheel_rotate}.rotateX = {wheel_rotate}.rotateX;\n\nelse\n\t"
            joint_rotation_exp = f"{wheel_rotate}.rotateX = {wheel_rotate}.rotateX + 360/(6.283*${wheel_name}_radius) * (${wheel_name}_dot * ${wheel_name}_distance) * {wheel_ctrl}.rotateMulti;\n"
            move_old_pos_loc_exp = f"\nmatchTransform {wheel_oldpos} {wheel_grp};\n"
            reset_rot = f"\nif (time == 0)\n\t{wheel_rotate}.rotateX = 0;"
            force_update_exp = f"\n$temp = {root_ctrl}.translateZ;\n"

            cmds.expression(ae=1, an=1, n=f'wheel_rotation_{i + 1}',
                            s=f'{height_calc_exp}{store_position_exp}{wheel_dir_exp}{wheel_mag_exp}{wheel_if}'
                              f'{joint_rotation_exp}{move_old_pos_loc_exp}{reset_rot}{force_update_exp}')

        tilt_ctrl = cmds.circle(n='tilt_ctrl', r=vehicle_scale / 4, nr=(0, 1, 0))[0]
        cmds.xform(tilt_ctrl, t=(0, steer_pivot[1], 0), ws=1)
        cmds.transformLimits(tilt_ctrl, rx=(-5, 5), erx=(1, 1), rz=(-5, 5), erz=(1, 1))
        lock_attributes([tilt_ctrl], ['tx', 'ty', 'tz', 'ry', 'sx', 'sy', 'sz', 'visibility'])
        cmds.parentConstraint(tilt_ctrl, body, mo=1)
        tilt_ctrl_offset = cmds.group(tilt_ctrl, n='tilt_ctrl_offset', r=1)

        cmds.select(tilt_ctrl, r=1)
        cmds.addAttr(ln='shakeFrequency', nn='Shake Frequency', at='float', k=1, dv=10, min=1, max=100)
        cmds.addAttr(ln='shakeMulti', nn='Shake Multiplier', at='float', k=1, dv=0.1, min=0, max=10)
        shake_expression = f"{tilt_ctrl_offset}.rotateX = noise(seed(1), time * {tilt_ctrl}.shakeFrequency) * {tilt_ctrl}.shakeMulti;\n{tilt_ctrl_offset}.rotateZ = noise(seed(2), time * {tilt_ctrl}.shakeFrequency) * {tilt_ctrl}.shakeMulti;"
        cmds.expression(ae=1, an=1, n=f'{name}_body_shake', s=shake_expression)

        cmds.parent(tilt_ctrl_offset, f'|{rig_grp}|{controls_grp}|{root_grp}|{root_ctrl}|{main_grp}|{main_ctrl}')
        cmds.parent(car_root, f'|{rig_grp}|{geo_grp}')

        # root rotation pivot
        rot_piv = cmds.spaceLocator(n=f'{name}_rot_piv_ctrl')[0]
        cmds.connectAttr(f'{rot_piv}.translate', f'{root_ctrl}.rotatePivot')
        cmds.parent(rot_piv, f'|{rig_grp}|{controls_grp}|{root_grp}|{root_ctrl}|{main_grp}|{main_ctrl}')
        lock_attributes([rot_piv], ['rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'visibility'])


def arnold_color_attribute(shader, ctrl, connect_node=True):
    objects = cmds.ls(sl=1)

    cmds.select(objects, r=1)
    cmds.hyperShade(assign=shader)

    cmds.select(ctrl, r=1)
    ctrl_attributes = cmds.listAttr(ctrl)

    if 'ai_color' in ctrl_attributes:
        pass
    else:
        cmds.addAttr(ln='ai_color', at='double3')
        cmds.addAttr(ln='ai_colorX', nn='R', at='double', p='ai_color', k=1, min=0, max=1, dv=1)
        cmds.addAttr(ln='ai_colorY', nn='G', at='double', p='ai_color', k=1, min=0, max=1, dv=1)
        cmds.addAttr(ln='ai_colorZ', nn='B', at='double', p='ai_color', k=1, min=0, max=1, dv=1)

    if shader and connect_node is True:
        ai_color = cmds.createNode('aiUserDataColor')
        cmds.setAttr(f'{ai_color}.attribute', 'color', type='string')
        cmds.connectAttr(f'{ai_color}.outColor', f'{shader}.baseColor', f=1)

    target_shapes = []

    shading_grp = cmds.listConnections(f'{shader}.outColor')

    target_shapes.extend(cmds.listRelatives(objects, s=1, f=1))
    shapes = list(set(target_shapes))

    for shape in shapes:
        cmds.select(shape, r=1)
        shape_attr = cmds.listAttr(shape)
        if 'mtoa_constant_color' in shape_attr:
            pass
        else:
            cmds.addAttr(ln='mtoa_constant_color', at='double3')
            cmds.addAttr(ln='mtoa_constant_colorX', at='double', p='mtoa_constant_color')
            cmds.addAttr(ln='mtoa_constant_colorY', at='double', p='mtoa_constant_color')
            cmds.addAttr(ln='mtoa_constant_colorZ', at='double', p='mtoa_constant_color')

        cmds.connectAttr(f'{ctrl}.ai_colorX', f'{shape}.mtoa_constant_colorX', f=1)
        cmds.connectAttr(f'{ctrl}.ai_colorY', f'{shape}.mtoa_constant_colorY', f=1)
        cmds.connectAttr(f'{ctrl}.ai_colorZ', f'{shape}.mtoa_constant_colorZ', f=1)


def change_geometry_target():
    selected = cmds.ls(sl=1)

    geometry = selected[0]
    targets = selected[1:]

    shape = cmds.listRelatives(geometry, s=1)[0]

    for target in targets:
        constraints = []

        constraints.extend = cmds.listRelatives(target, ad=1, type='geometryConstraint')
        constraints.extend(cmds.listRelatives(target, ad=1, type='normalConstraint'))

        if constraints:
            for constraint in constraints:
                cmds.connectAttr(f'{shape}.worldMesh[0]', f'{constraint}.target[0].targetGeometry', f=1)


def retarget_constraints():
    selected = cmds.ls(sl=1)

    geometry = selected[0]
    targets = selected[1:]

    shape = cmds.listRelatives(geometry, s=1)[0]

    for target in targets:

        constraints = cmds.listRelatives(target, ad=1, type='geometryConstraint')
        constraints.extend(cmds.listRelatives(target, ad=1, type='normalConstraint'))

        if constraints:
            for constraint in constraints:
                cmds.connectAttr(f'{shape}.worldMesh[0]', f'{constraint}.target[0].targetGeometry', f=1)


def create_aircraft_rig():
    node_dict = {}

    def create_propeller(geo):

        cmds.select(ctrl, r=1)
        cmds.addAttr(ln='rpm', nn='RPM', at='float', k=1, dv=0)
        rpm_expression = f"if(frame==1001):\n\t{ctrl}.rotateX=0;\nelse:\n\t{ctrl}.rotateX += (({ctrl}.rpm*frame*360)/(30*60))/frame;"
        cmds.expression(ae=1, an=1, n=f'{ctrl}_rpm_expression', s=rpm_expression)
        cmds.orientConstraint(ctrl, geo, mo=0)

    def create_rudder():
        pass

    def create_aileron():
        pass

    def create_elevator():
        pass

    def create_root_ctrl():
        pass

    def create_body_ctrl():
        pass

    selected = cmds.ls(sl=1)
    node_dict = get_node_details(selected)
    for node_uuid in node_dict:
        if 'propeller' in node_dict[node_uuid]['name']:
            create_propeller(geo)
