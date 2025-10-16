import logging
import os
from math import floor, ceil

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as om

from CETools.functions.commonFunctions import UndoStack, get_node_details, get_manip_xform, get_current_manip, \
    get_object_type
from CETools.functions.rigging import set_index_color

from itertools import groupby


def get_connected_edges():
    pass


def distribute_on_geometry(stamp, count, density, clamp, smooth_scale, use_fixed, offset, is_instance):
    selected = (cmds.ls(os=True, fl=True))

    if not cmds.objExists(stamp):
        logging.warning(f"Can't find object: {stamp}")
        return

    with UndoStack('stamp'):

        curve = mel.eval("polyToCurve -form 2 -degree 1 -conformToSmoothMeshPreview 1;")
        arc_length = cmds.arclen(curve[0], ch=0)
        if use_fixed is False:
            count = floor(arc_length / density)
        count = count * smooth_scale
        new_crv = cmds.rebuildCurve(curve, s=count, d=1, ch=0)[0]

        new_group = cmds.group(n="stamp_container_01", em=True)

        for x in range(0 + clamp, count - clamp, smooth_scale):
            pos = cmds.pointPosition(f'{new_crv}.cv[{x}]', w=True)
            if is_instance:
                new_item = cmds.instance(stamp)[0]
            else:
                new_item = cmds.duplicate(stamp)
            cmds.xform(new_item, t=pos)
            constraint = cmds.normalConstraint(selected, new_item, w=1, u=(1, 0, 0), aim=(0, 1, 0))
            cmds.delete(constraint)
            cmds.parent(new_item, new_group)
        cmds.delete(new_crv)
        all_stamps = cmds.ls(new_group, dag=1)
        cmds.select(all_stamps, r=1)


def drop_to_floor(nodes=None, offset=0):
    # no object is selected, return error
    if not nodes:
        nodes = cmds.ls(sl=True)

    if not nodes:
        cmds.error("No objects are selected")

    for node in nodes:
        bbox = cmds.exactWorldBoundingBox(node)

        pos = cmds.xform(node, q=True, t=True, ws=True)

        distance = pos[1] - bbox[1] + float(offset)
        pos[1] = distance

        cmds.xform(node, translation=pos, ws=True)


def instances_to_objects():
    # modified from https://forums.autodesk.com/t5/maya-forum/convert-multiple-instances-to-object/td-p/8104570
    def getInstances():
        instances = []
        iterDag = om.MItDag(om.MItDag.kBreadthFirst)
        while not iterDag.isDone():
            instanced = om.MItDag.isInstanced(iterDag)
            if instanced:
                instances.append(iterDag.fullPathName())
            iterDag.next()
        return instances

    def uninstance():
        instances = getInstances()
        while len(instances):
            parent = cmds.listRelatives(instances[0], parent=True, pa=1)[0]
            shading_group = cmds.listConnections(instances[0], type='shadingEngine')
            cmds.duplicate(parent, renameChildren=True)
            cmds.delete(parent)
            if shading_group:
                new_shading_group = cmds.listConnections(instances[0], type='shadingEngine')
                if shading_group != new_shading_group:
                    cmds.select(instances[0], r=1)
                    cmds.hypershade(assign=(cmds.ls(cmds.listConnections(shading_group), materials=1)))

            instances = getInstances()

    uninstance()


def combine_curves(*args):
    # use selected, or if nothing selected use input args
    crvs = cmds.ls(selection=True) or args
    crv_shapes = cmds.listRelatives(crvs, s=True)

    # freeze transforms of selected curves
    cmds.makeIdentity(crvs, apply=True, t=True, r=True, s=True)

    # create null transform to parent shapes to
    combine = cmds.group(em=True, name="newCombinedCtl")

    # parent shapes to null
    cmds.parent(crv_shapes, combine, s=True, r=True)

    # remove old transforms
    cmds.delete(crvs)
    return combine


def advanced_mirror(axis, direction, cut_mesh, instance, mirror_axis, interactive):
    selected = cmds.ls(sl=1, l=1)

    # Check if selected are a group or a mesh. If group - take all descendants. If mesh - run as normal.
    targets = []
    nodes_dict = get_node_details(selected)
    for node in nodes_dict.keys():
        if nodes_dict[node]['type'] == 'transform':
            children = cmds.listRelatives(cmds.ls(node), ad=1, pa=1, type='transform')
            child_nodes_dict = get_node_details(children)
            for child_node in child_nodes_dict.keys():
                if child_nodes_dict[child_node]['type'] == 'mesh':
                    targets.extend(child_node.split())
        else:
            targets.extend(node.split())

    # Reverse values if direction is 1 (0 == positive, 1 == negative)
    ws_direction = -1
    piv_index = 3
    if direction == 1:
        piv_index = 0

    axes = ('X', 'Y', 'Z')

    bbox = cmds.exactWorldBoundingBox(cmds.ls(targets), ii=0)
    with UndoStack('simple_mirror'):
        if interactive:
            plane_axes = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
            max_size = max(
                [bbox[3] - bbox[0], bbox[4] - bbox[1], bbox[5] - bbox[2]])

            center_x = (bbox[0] + bbox[3]) / 2.0
            center_y = (bbox[1] + bbox[4]) / 2.0
            center_z = (bbox[2] + bbox[5]) / 2.0

            center_point = [center_x, center_y, center_z]

            if mirror_axis == 2:
                center_point[axis] = 0
            elif mirror_axis == 0:
                center_point[axis] = center_x

            nurbs_plane = cmds.nurbsSquare(nr=plane_axes[axis], d=1, sl1=max_size, sl2=max_size)[0]
            curve_shapes = cmds.listRelatives(nurbs_plane, pa=1)
            cmds.select(curve_shapes, r=1)
            mirror_plane = combine_curves()
            cmds.delete(nurbs_plane)

            cmds.select(mirror_plane, r=1)
            set_index_color(13 + axis)

            cmds.xform(mirror_plane, t=center_point, ws=1)
            cmds.addAttr(ln='mergeThreshold', at='double', dv=0.001, min=0, max=1, k=1)
            cmds.addAttr(ln='cutMesh', at='bool', dv=cut_mesh, k=1)

            # Advanced controls
            center_node = cmds.createNode('colorConstant')
            cmds.setAttr(f'{center_node}.inColorR', center_point[0])
            cmds.setAttr(f'{center_node}.inColorG', center_point[1])
            cmds.setAttr(f'{center_node}.inColorB', center_point[2])

            bbox_min = cmds.createNode('colorConstant', n='bbox_min1')
            cmds.setAttr(f'{bbox_min}.inColorR', bbox[0])
            cmds.setAttr(f'{bbox_min}.inColorG', bbox[1])
            cmds.setAttr(f'{bbox_min}.inColorB', bbox[2])

            bbox_max = cmds.createNode('colorConstant', n='bbox_max1')
            cmds.setAttr(f'{bbox_max}.inColorR', bbox[3])
            cmds.setAttr(f'{bbox_max}.inColorG', bbox[4])
            cmds.setAttr(f'{bbox_max}.inColorB', bbox[5])

            colors = ('R', 'G', 'B')
            ax = ('X', 'Y', 'Z')

            center_con_nodes = []

            for i in range(3):
                center_con_nodes.append(cmds.createNode('condition'))
                cmds.connectAttr(f'{center_node}.outColor{colors[i]}', f'{center_con_nodes[i]}.secondTerm')
                cmds.connectAttr(f'{mirror_plane}.translate{ax[i]}', f'{center_con_nodes[i]}.firstTerm')
                cmds.setAttr(f'{center_con_nodes[i]}.operation', 2)

            for sel in cmds.ls(targets):
                mirror_node = cmds.polyMirrorFace(sel, axis=axis, mirrorAxis=mirror_axis, axisDirection=direction,
                                                  mirrorPosition=0, cutMesh=cut_mesh, mergeMode=cut_mesh,
                                                  mergeThresholdType=cut_mesh)[0]
                cmds.connectAttr(f'{mirror_plane}.translate', f'{mirror_node}.mirrorPlaneCenter')
                cmds.connectAttr(f'{mirror_plane}.rotate', f'{mirror_node}.mirrorPlaneRotate')
                cmds.connectAttr(f'{mirror_plane}.mergeThreshold', f'{mirror_node}.mergeThreshold')
                cmds.connectAttr(f'{mirror_plane}.cutMesh', f'{mirror_node}.cutMesh')
                cmds.connectAttr(f'{center_con_nodes[0]}.outColorR', f'{mirror_node}.axisDirection')

            cmds.rename(mirror_plane, f'{ax[axis]}_mirror_01')

        else:
            for sel in cmds.ls(targets):
                if instance:
                    sel = cmds.instance(sel)[0]
                    rotate_pivot = cmds.xform(sel, q=1, rp=1)
                    scale_pivot = cmds.xform(sel, q=1, sp=1)
                    cmds.xform(sel, piv=(bbox[piv_index], bbox[piv_index + 1], bbox[piv_index + 2]))
                    scale = cmds.getAttr(f'{sel}.scale{axes[axis]}')
                    cmds.setAttr(f'{sel}.scale{axes[axis]}', ws_direction * scale)
                    cmds.xform(sel, rp=rotate_pivot, sp=scale_pivot)
                else:
                    mirror = cmds.polyMirrorFace(sel, axis=axis, mirrorAxis=mirror_axis, axisDirection=direction,
                                                 mirrorPosition=0, cutMesh=cut_mesh, mergeMode=cut_mesh,
                                                 mergeThresholdType=cut_mesh)[0]

                    if not cut_mesh:
                        parent = cmds.listRelatives(sel, p=1)
                        poly_separate = cmds.polySeparate(sel, uss=1, inp=1)
                        new_meshes = poly_separate[0:-1]
                        separate = poly_separate[-1]
                        cmds.connectAttr(f'{mirror}.firstNewFace', f'{separate}.startFace')
                        cmds.connectAttr(f'{mirror}.lastNewFace', f'{separate}.endFace')
                        cmds.delete(new_meshes, ch=1)

                        if parent:
                            cmds.parent(new_meshes[0], parent)
                        else:
                            cmds.parent(new_meshes[0], w=1)
                        cmds.delete(sel)
                        cmds.select(new_meshes[-1], r=1)
                    else:
                        cmds.delete(sel, ch=1)


def interactive_mirror(axis, axis_direction, direction, mirror_axis):
    selected = cmds.ls(sl=1)
    bbox = cmds.exactWorldBoundingBox(selected)
    axes = ((1, 0, 0), (0, 1, 0), (0, 0, 1))

    max_size = max(
        [bbox[3] - bbox[0], bbox[4] - bbox[1], bbox[5] - bbox[2]])

    center_x = (bbox[0] + bbox[3]) / 2.0
    center_y = (bbox[1] + bbox[4]) / 2.0
    center_z = (bbox[2] + bbox[5]) / 2.0

    center_point = [center_x, center_y, center_z]

    if mirror_axis == 2:
        center_point[axis] = 0
    elif mirror_axis == 0:
        center_point[axis] = center_x

    mirror_plane = cmds.nurbsSquare(nr=axes[axis], d=1, sl1=max_size, sl2=max_size)[0]
    cmds.xform(mirror_plane, t=center_point, ws=1)
    cmds.addAttr(ln='mergeThreshold', at='double', dv=0.001, min=0, max=1, k=1)
    cmds.addAttr(ln='cutMesh', at='bool', dv=1, k=1)

    # Advanced controls
    center_node = cmds.createNode('colorConstant')
    cmds.setAttr(f'{center_node}.inColorR', center_point[0])
    cmds.setAttr(f'{center_node}.inColorG', center_point[1])
    cmds.setAttr(f'{center_node}.inColorB', center_point[2])

    bbox_min = cmds.createNode('colorConstant', n='bbox_min1')
    cmds.setAttr(f'{bbox_min}.inColorR', bbox[0])
    cmds.setAttr(f'{bbox_min}.inColorG', bbox[1])
    cmds.setAttr(f'{bbox_min}.inColorB', bbox[2])

    bbox_max = cmds.createNode('colorConstant', n='bbox_max1')
    cmds.setAttr(f'{bbox_max}.inColorR', bbox[3])
    cmds.setAttr(f'{bbox_max}.inColorG', bbox[4])
    cmds.setAttr(f'{bbox_max}.inColorB', bbox[5])

    colors = ('R', 'G', 'B')
    ax = ('X', 'Y', 'Z')

    center_con_nodes = []

    for i in range(3):
        center_con_nodes.append(cmds.createNode('condition'))
        cmds.connectAttr(f'{center_node}.outColor{colors[i]}', f'{center_con_nodes[i]}.secondTerm')
        cmds.connectAttr(f'{mirror_plane}.translate{ax[i]}', f'{center_con_nodes[i]}.firstTerm')
        cmds.setAttr(f'{center_con_nodes[i]}.operation', 2)

    for sel in selected:
        mirror_node = \
            cmds.polyMirrorFace(sel, axis=axis, axisDirection=axis_direction, direction=direction, ma=mirror_axis)[0]
        cmds.connectAttr(f'{mirror_plane}.translate', f'{mirror_node}.mirrorPlaneCenter')
        cmds.connectAttr(f'{mirror_plane}.rotate', f'{mirror_node}.mirrorPlaneRotate')
        cmds.connectAttr(f'{mirror_plane}.mergeThreshold', f'{mirror_node}.mergeThreshold')
        cmds.connectAttr(f'{mirror_plane}.cutMesh', f'{mirror_node}.cutMesh')
        cmds.connectAttr(f'{center_con_nodes[0]}.outColorR', f'{mirror_node}.axisDirection')
        '''
        for i in range(3)
            cmds.connectAttr(f'{center_con_nodes[i]}.outColor{colors[i]}',f'{mirror_node}.axisDirection')
        '''


def copy_uvs():
    selected = cmds.ls(sl=True)
    if not selected:
        logging.warning("Select a source and target mesh(es)")
    if len(selected) < 2:
        logging.warning("Select a source and target mesh(es)")

    for i, item in enumerate(selected):
        if i > 0:
            cmds.transferAttributes(selected[0], item, sampleSpace=4, transferUVs=2)


def build_custom_mesh(dir_path, mesh_name, replace=False, to_bbox_scale=True):
    curve_path = os.path.join(dir_path, mesh_name + '.crv')
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

        combine = combine_curves(curves, name=mesh_name)

        if replace:
            for sel in selected:
                if not get_object_type(sel) == "nurbsCurve":
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

        if selected and not replace:
            if cmds.objectType(selected) == "joint":
                duplicate_hierarchy(selected[0], '', 0, combine)
            # cl.attachCtrl(combine, selected)
            # elif cmds.objectType(cmds.listRelatives(selected[0],s=1,pa=1)[0],isType='nurbsCurve'):
            #    cl.replaceCurve(combine, selected)


def clean_double_faces(distance=0.0):
    selected = cmds.ls(sl=1)
    if not selected:
        cmds.error('Select at least one mesh.')
        return

    with UndoStack('clean_double_faces'):
        nodes_dict = get_node_details(selected)

        for node in nodes_dict.keys():
            if nodes_dict[node]['type'] == 'mesh':
                mesh = nodes_dict[node]['name']
                vtx = cmds.ls(f'{mesh}.vtx[*]', fl=True)
                cmds.select(vtx, r=1)
                cmds.polyMergeVertex(d=distance)
                cmds.select(mesh, r=1)
                lamina_faces = cmds.polyInfo(lf=1)
                if lamina_faces:
                    cmds.delete(lamina_faces)
                else:
                    logging.warning('No lamina faces found.')
            else:
                logging.warning(f"{nodes_dict[node]['name']} is not a mesh, skipping.")


def move_to_pivot():
    selected = cmds.ls(sl=1, l=1)
    current_manip = get_current_manip()
    if len(selected) > 1:
        targets = selected[0:-1]
    else:
        targets = selected

    if current_manip:
        manip_pos, manip_rot = get_manip_xform(ctx=current_manip)
        for target in targets:
            cmds.xform(target, t=manip_pos, ro=manip_rot, ws=1)


def rotate_to_component(rot_x: bool, rot_y: bool, rot_z: bool):
    selected = cmds.ls(sl=1, f=1)
    # Get edge closest axis and snap rotate object to match
    current_manip = get_current_manip()
    targets = selected[0:-1]

    if current_manip:
        manip_pos, manip_rot = get_manip_xform(ctx=current_manip)
        for target in targets:
            pos = cmds.xform(target, q=1, t=1, ws=1)
            rot = cmds.xform(target, q=1, ro=1, ws=1)

            cmds.xform(target, t=manip_pos, ro=manip_rot, ws=1)


def select_border_edges(invert=False):
    # https://forum.highend3d.com/t/python-store-all-border-edges/159952/4 thanks for head start
    mesh = cmds.ls(sl=1, l=1)
    info = cmds.polyEvaluate(mesh, e=True)
    new_edge_selection = []
    for i in range(info):
        if invert is True:
            border_edges = cmds.polySelect(mesh, eb=i, ns=True, ass=True)
            if border_edges is None and border_edges not in new_edge_selection:
                new_edge_selection.extend(border_edges)
        else:
            border_edges = cmds.polySelect(mesh, eb=i, ns=True, ass=True)
            if border_edges is not None and border_edges not in new_edge_selection:
                new_edge_selection.extend(border_edges)
    cmds.select(new_edge_selection, r=1)


def list_to_ranges(iterable):
    # https://discourse.techart.online/t/invert-selection-of-polygons/15230/9
    for key, group in groupby(enumerate(iterable), lambda x: x[1] - x[0]):
        group = list(group)
        yield (group[0][1], group[-1][1])

def generate_components(object, comp, indices):
    # https://discourse.techart.online/t/invert-selection-of-polygons/15230/9
    for pair in list_to_ranges(indices):
        if pair[1] == pair[0]:
            yield '{0}.{1}[{2}]'.format(object, comp, pair[0])
        else:
            yield '{0}.{1}[{2}:{3}]'.format(object, comp, pair[0], pair[1])
    '''
    indices = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 41]
    recap = generate_components("pCylinder", "v", indices)
    print(list(recap))
    '''
