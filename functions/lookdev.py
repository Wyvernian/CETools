import logging

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from os import path
from glob import iglob
from re import findall
from json import dump
from colorsys import hsv_to_rgb
from math import floor
import json

from CETools.functions.commonFunctions import UndoStack


def setup_turntable(anim_steps):
    with UndoStack('setup_turntable'):
        offset_groups = ('CE_TURNTABLE_OFFSET', 'CE_CAMERA_OFFSET', 'CE_SKYDOME_OFFSET')
        for grp in offset_groups:
            if not cmds.objExists(grp):
                logging.warning('You must click Setup Turntable Groups first.')
                return

        # Set time to 0, otherwise bugs happen
        cmds.currentTime(0)
        cmds.cutKey(offset_groups, clear=1)

        frame_start = cmds.playbackOptions(q=1, minTime=1)
        frame_end = cmds.playbackOptions(q=1, maxTime=1)

        step = (frame_end - frame_start) / (len(anim_steps))

        frames = [floor(frame_start + step * i) for i in range(len(anim_steps) + 1)]

        for i, anim_step in enumerate(anim_steps):
            step_data = json.loads(anim_step)
            target = offset_groups[step_data[0]]
            axis = f'rotate{step_data[1]}'
            direction = step_data[2]
            tangent = 'linear'
            current_value = cmds.keyframe(f'{target}.{axis}', t=(frames[i],), q=True, ev=True) or [0]

            cmds.setKeyframe(target, at=axis, t=(frames[i],), v=current_value[0], itt=tangent,
                             ott=tangent)
            cmds.setKeyframe(target, at=axis, t=(frames[i + 1],),
                             v=((current_value[0] + 360) if direction == 0 else (current_value[0] - 360)), itt=tangent,
                             ott=tangent)


def find_object_type(item):
    if cmds.listRelatives(item, shapes=True, f=True):
        item_type = cmds.objectType(cmds.listRelatives(item, shapes=True, f=True)[0])
    else:
        item_type = cmds.objectType(item)
    return item_type


def hsv2rgb(h, s, v):
    # add stuff in case the conversion is fucked here
    return hsv_to_rgb(h, s, v)


def create_render_balls(file_path):
    # We have a shitty jpeg Macbeth Chart yippee, look at me
    macbeth_chart_path = path.join(file_path, "images", "macbeth_chart.png")
    if not path.exists(macbeth_chart_path):
        logging.warning('Could not locate macbeth_chart.png')
        return
    selected = cmds.ls(sl=1)
    if not selected:
        logging.warning('Select a camera.')
        return

    if len(selected) == 1:
        if find_object_type(selected[0]) == 'camera':
            camera = selected[0]
        else:
            logging.warning('Selected object is not a camera.')
            return

    with UndoStack('render_balls'):

        # Chrome Ball
        chrome_ball = cmds.polySphere(n='chrome_ball', r=0.3)[0]
        chrome_ball_shp = cmds.listRelatives(chrome_ball, s=1, f=1)[0]
        if not cmds.objExists('ai_chrome_ball'):
            chrome_shader, _ = create_ai_standard_surface(name='ai_chrome_ball')
            cmds.setAttr(f'{chrome_shader}.metalness', 1)
            r, g, b = hsv2rgb(0.0, 0.0, 0.6)
            cmds.setAttr(f'{chrome_shader}.baseColor', r, g, b, type='double3')
            cmds.setAttr(f'{chrome_shader}.specularColor', r, g, b, type='double3')
            cmds.setAttr(f'{chrome_shader}.specularRoughness', 0.06)
        cmds.select(chrome_ball, r=1)
        cmds.hyperShade(assign='ai_chrome_ball')

        # Matte Ball
        matte_ball = cmds.polySphere(n='matte_ball', r=0.3)[0]
        matte_ball_shp = cmds.listRelatives(matte_ball, s=1, f=1)[0]
        if not cmds.objExists('ai_matte_ball'):
            matte_shader, _ = create_ai_standard_surface(name='ai_matte_ball')
            r, g, b = hsv2rgb(0.0, 0.0, 0.18)
            cmds.setAttr(f'{matte_shader}.baseColor', r, g, b, type='double3')
            cmds.setAttr(f'{matte_shader}.specularColor', 0.4, 0.4, 0.4, type='double3')
            cmds.setAttr(f'{matte_shader}.specularRoughness', 0.6)
        cmds.select(matte_ball, r=1)
        cmds.hyperShade(assign='ai_matte_ball')

        # Macbeth Chart
        macbeth_chart = cmds.polyPlane(h=1, w=1.5, sh=1, sw=1, ax=(0, 0, 1), ch=0)[0]
        macbeth_chart_shp = cmds.listRelatives(macbeth_chart, s=1, f=1)[0]
        if not cmds.objExists('ai_macbeth_chart'):
            macbeth_shader, macbeth_shading_group = create_ai_standard_surface(name='ai_macbeth_chart')
            file_node = link_file_node(macbeth_shader, 'baseColor')
            cmds.setAttr(f'{file_node}.fileTextureName', macbeth_chart_path, type='string')
            cmds.setAttr(f'{macbeth_shader}.specularRoughness', 0.2)
        cmds.select(macbeth_chart, r=1)
        cmds.hyperShade(assign='ai_macbeth_chart')

        attributes = ['castsShadows', 'aiVisibleInDiffuseReflection', 'aiVisibleInSpecularReflection']
        for at in attributes:
            cmds.setAttr(f'{chrome_ball_shp}.{at}', 0)
            cmds.setAttr(f'{matte_ball_shp}.{at}', 0)
            cmds.setAttr(f'{macbeth_chart_shp}.{at}', 0)

        group = cmds.group([chrome_ball, matte_ball, macbeth_chart], n='render_balls_grp')

        cmds.xform(chrome_ball, t=(-4, -1, -10), r=1)
        cmds.xform(matte_ball, t=(-3, -1, -10), r=1)
        cmds.xform(macbeth_chart, t=(-3.5, -2, -10), r=1)
        cmds.parentConstraint(camera, group)


def fill_node_array(node_plug, input_plugs):
    items = cmds.listConnections(node_plug, c=1)
    indices = []
    for item in items:
        indices.append(int(findall(r'\d+', item)[-1]))

    i = 0
    while input_plugs:
        if i not in indices:
            cmds.connectAttr(input_plugs[0], f'{node_plug}[{i - 1}]')
            input_plugs.pop(0)
        i += 1


def assign_material_by_name(matching_string, new_shader, all_terms, match_path, use_material):
    shapes = cmds.ls(geometry=True, sl=1, dag=1, l=1)
    selected = cmds.listRelatives(shapes, p=True, f=True)

    if not shapes or not selected:
        logging.warning('No objects have been selected.')

    with UndoStack('assign_mat_by_name'):

        selection_dict = {}
        for s in selected:
            if use_material:
                shapes_in_sel = cmds.listRelatives(s, s=1, f=1)
                shading_groups = cmds.listConnections(shapes_in_sel, type='shadingEngine')
                shaders = cmds.ls(cmds.listConnections(shading_groups), materials=1, l=1)
                if not shaders:
                    continue
                for shader in shaders:
                    if match_path:
                        selection_dict[shader] = shader.lower()
                    else:
                        selection_dict[shader] = shader.lower().split(':')[-1]

            elif match_path is True:
                selection_dict[s] = s.lower()
            else:
                selection_dict[s] = cmds.ls(s)[0].lower()

        matching_strings = matching_string.lower().split()

        if all_terms:
            matching_objects = [sel for sel in selection_dict.keys() if
                                all(match in selection_dict[sel] for match in matching_strings)]
        else:
            matching_objects = [sel for sel in selection_dict.keys() if
                                any(match in selection_dict[sel] for match in matching_strings)]

        if use_material:
            set_members = []
            for matching_shader in matching_objects:
                old_sgs = cmds.listConnections(f'{matching_shader}.outColor')
                if old_sgs:
                    for sg in old_sgs:
                        members = cmds.ls(cmds.sets(sg, q=1), l=1)
                        # Verify and take only objects that are in selection
                        matching_members = [x for x in members if
                                            x.split(".")[0] in selected or x.split(".")[0] in shapes]
                        set_members.extend(matching_members)

            new_members = list(set(set_members))

            new_sg = cmds.listConnections(f'{new_shader}.outColor')[0]
            if new_sg:
                cmds.sets(new_members, e=1, fe=new_sg)

        else:
            cmds.select(matching_objects, r=1)
            cmds.hyperShade(assign=new_shader)


def write_shader_connections():
    file_path = cmds.fileDialog2(fileFilter="*.json", dialogStyle=2)

    if not file_path:
        logging.warning('Save process aborted.')
        return

    selected = cmds.ls(sl=1, l=1)
    shapes_in_sel = cmds.listRelatives(selected, s=1, f=1)
    shading_groups = cmds.listConnections(shapes_in_sel, type='shadingEngine')
    shaders = cmds.ls(cmds.listConnections(shading_groups), materials=1)

    shader_data = {}

    for shader in shaders:
        shader_data[shader] = []

    for sel in selected:
        shape = cmds.listRelatives(sel, s=1, f=1)
        shader_group = cmds.listConnections(shape, type='shadingEngine')
        shader = cmds.ls(cmds.listConnections(shader_group), materials=1)[0]
        shader_data[shader].append(sel)

    with open(file_path[0], 'w') as json_file:
        dump(shader_data, json_file, indent=4)


def assign_shader_to_curves(width, shader):
    selected = cmds.ls(sl=1, l=1)
    for sel in selected:
        shapes = cmds.listRelatives(sel, s=1)
        for shape in shapes:
            cmds.setAttr(f'{shape}.aiRenderCurve', 1)
            cmds.setAttr(f'{shape}.aiCurveWidth', width)
            cmds.connectAttr(f'{shape}.aiCurveShader', shader)


def texture_to_raw(file_node):
    cmds.setAttr(f'{file_node}.colorSpace', 'Utility - Raw', type='string')
    cmds.setAttr(f'{file_node}.alphaIsLuminance', 1)


def create_shading_group(shader):
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=f'{shader}_SG')
    cmds.connectAttr(f'{shader}.outColor', f'{shading_group}.surfaceShader')
    return shading_group


def create_ai_standard_surface(name='aiStandardSurface'):
    shader = cmds.shadingNode("aiStandardSurface", asShader=True, name=name)
    shading_group = create_shading_group(shader)
    return shader, shading_group


def connect_textures(folder_path, diffuse, specular, metalness, normals, displacement):
    texture_types = {
        'BaseColor': ['outColor', 'baseColor', diffuse],
        'Roughness': ['outAlpha', 'specular', specular],
        'Metalness': ['outAlpha', 'metalness', metalness],
        'Normal': ['outAlpha', 'normal', normals],
        'Height': ['outAlpha', 'height', displacement],
    }
    # 'Emissive': ['outAlpha', 'emission']
    attributes = (
        "coverage", "translateFrame", "rotateFrame", "mirrorU", "mirrorV", "stagger", "wrapU", "wrapV", "repeatUV",
        "vertexUvOne", "vertexUvTwo", "vertexUvThree", "vertexCameraOne", "noiseUV", "offset", "rotateUV")

    shading_group = ''

    if not path.exists(folder_path):
        cmds.error("Invalid file path")
        return

    image_files = [f for f in iglob(f'{folder_path}/*') if f.endswith((".png", ".jpg", ".tiff"))]
    image_files.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

    image_files = [f for f in iglob(f'{folder_path}/*') if f.endswith((".png", ".jpg", ".tiff"))]
    material_groups = {}
    for file in image_files:
        for texture_type in texture_types.keys():
            if texture_type in file:
                file_name = path.basename(file)
                shader_name = file_name.split(texture_type)[0]
                highest_tile_id = findall(r"\d{4}", file_name)[-1]
                if shader_name not in material_groups.keys():
                    material_groups[shader_name] = {}
                if texture_type not in material_groups[shader_name].keys():
                    material_groups[shader_name][texture_type] = {}
                material_groups[shader_name][texture_type][highest_tile_id] = file

    scene_materials = cmds.ls(mat=1)

    for shader_key in material_groups.keys():

        similar_material = None
        # Check if similar material already exists in the scene.
        for material in scene_materials:
            if material in shader_key:
                similar_material = material

        if similar_material:
            shader = similar_material
            shading_group = cmds.listConnections(similar_material, type='shadingEngine')[0]
        else:
            shader, shading_group = create_ai_standard_surface(name=f'{shader_key.strip("_")}')

        for texture in material_groups[shader_key].keys():

            if texture_types[texture][2] is False:
                continue

            highest_tile_id = max(material_groups[shader_key][texture].keys())

            file_node = cmds.shadingNode('file', name=f'{shader}{texture}', asTexture=True,
                                         isColorManaged=True)

            if len(material_groups[shader_key][texture].keys()) > 1:
                cmds.setAttr(f'{file_node}.uvTilingMode', 3)

            place_2d_texture = cmds.shadingNode("place2dTexture", asUtility=True)
            cmds.connectAttr("%s.outUV" % place_2d_texture, "%s.uvCoord" % file_node, f=True)
            cmds.connectAttr("%s.outUvFilterSize" % place_2d_texture, "%s.uvFilterSize" % file_node, f=True)
            for attribute in attributes:
                cmds.connectAttr(f'{place_2d_texture}.{attribute}', f'{file_node}.{attribute}', f=True)

            cmds.setAttr(f'{file_node}.fileTextureName', material_groups[shader_key][texture][highest_tile_id],
                         type='string')
            cmds.setAttr(f'{file_node}.ignoreColorSpaceFileRules', 1)

            if texture_types[texture][0] == 'outAlpha':
                texture_to_raw(file_node)
            else:
                cmds.setAttr(f'{file_node}.colorSpace', 'Utility - sRGB - Texture', type='string')

            if texture_types[texture][1] == 'normal':
                texture_to_raw(file_node)
                bump2d = cmds.shadingNode('bump2d', asUtility=1)
                cmds.setAttr(f'{bump2d}.bumpInterp', 1)
                cmds.connectAttr(f'{file_node}.outAlpha', f'{bump2d}.bumpValue')
                cmds.connectAttr(f'{bump2d}.outNormal', f'{shader}.normalCamera', f=1)

            elif texture_types[texture][1] == 'height':
                texture_to_raw(file_node)
                displacement_map = cmds.shadingNode('displacementShader', asUtility=1)
                cmds.connectAttr(f'{file_node}.outAlpha', f'{displacement_map}.displacement')
                cmds.connectAttr(f'{displacement_map}.displacement', f'{shading_group}.displacementShader', f=1)

            else:
                cmds.connectAttr(f'{file_node}.{texture_types[texture][0]}',
                                 f'{shader}.{texture_types[texture][1]}',
                                 f=1)


def link_file_node(dest_node, dest_attribute='color'):
    attributes = (
        "coverage", "translateFrame", "rotateFrame", "mirrorU", "mirrorV", "stagger", "wrapU", "wrapV", "repeatUV",
        "vertexUvOne", "vertexUvTwo", "vertexUvThree", "vertexCameraOne", "noiseUV", "offset", "rotateUV")

    file_node = cmds.shadingNode('file', name=f'file1', asTexture=True,
                                 isColorManaged=True)

    place_2d_texture = cmds.shadingNode("place2dTexture", asUtility=True)
    cmds.connectAttr("%s.outUV" % place_2d_texture, "%s.uvCoord" % file_node, f=True)
    cmds.connectAttr("%s.outUvFilterSize" % place_2d_texture, "%s.uvFilterSize" % file_node, f=True)

    for attribute in attributes:
        cmds.connectAttr(f'{place_2d_texture}.{attribute}', f'{file_node}.{attribute}', f=True)

    cmds.connectAttr(f'{file_node}.outColor', f'{dest_node}.{dest_attribute}', f=1)
    return file_node


def build_hdri(hdri_path, name):
    selected = cmds.ls(sl=1)
    if len(selected) == 1 and find_object_type(cmds.listRelatives(selected[0], f=1, s=1)) == 'aiSkyDomeLight':
        skydome = cmds.listRelatives(selected[0], s=1, f=1)[0]
        file_node = cmds.listConnections(f'{skydome}.color', type='file')
        if file_node:
            file_node = file_node[0]
        else:
            file_node = link_file_node(skydome)

    else:
        skydome = cmds.shadingNode('aiSkyDomeLight', name=f'{name}Shape', asLight=1)
        cmds.setAttr(f'{skydome}.aiAov', 'hdr', type='string')

        file_node = link_file_node(skydome)

        cmds.rename(cmds.listRelatives(skydome, p=1, f=1), name)

    cmds.setAttr(f'{file_node}.fileTextureName', hdri_path, type='string')
    cmds.select(cmds.listRelatives(skydome, p=1, f=1), r=1)


# https://gist.github.com/Kif11/247f6b05e8d3a6c3ffb193b8c6f4dec7#file-obj_in_frust-py-L1
# Find if object located within camera frustum
# Usage:
#   from obj_in_frust import in_frustum
#   in_frustum('camera1', 'pCube1')

class Plane(object):
    def __init__(self, normalisedVector):
        # OpenMaya.MVector.__init__()
        self.vector = normalisedVector
        self.distance = 0.0

    def relativeToPlane(self, point):
        # Converting the point as a vector from the origin to its position
        pointVec = OpenMaya.MVector(point.x, point.y, point.z)
        val = (self.vector * pointVec) + self.distance

        if (val > 0.0):
            return 1  # In front
        elif (val < 0.0):
            return -1  # Behind

        return 0  # On the plane


class Frustum(object):
    def __init__(self, cameraName):
        # Initialising selected transforms into its associated dagPaths
        selectionList = OpenMaya.MSelectionList()
        objDagPath = OpenMaya.MDagPath()
        selectionList.add(cameraName)
        selectionList.getDagPath(0, objDagPath)
        self.camera = OpenMaya.MFnCamera(objDagPath)

        self.nearClip = self.camera.nearClippingPlane()
        self.farClip = self.camera.farClippingPlane()
        self.aspectRatio = self.camera.aspectRatio()

        left_util = OpenMaya.MScriptUtil()
        left_util.createFromDouble(0.0)
        ptr0 = left_util.asDoublePtr()

        right_util = OpenMaya.MScriptUtil()
        right_util.createFromDouble(0.0)
        ptr1 = right_util.asDoublePtr()

        bot_util = OpenMaya.MScriptUtil()
        bot_util.createFromDouble(0.0)
        ptr2 = bot_util.asDoublePtr()

        top_util = OpenMaya.MScriptUtil()
        top_util.createFromDouble(0.0)
        ptr3 = top_util.asDoublePtr()

        stat = self.camera.getViewingFrustum(self.aspectRatio, ptr0, ptr1, ptr2, ptr3, False, True)

        planes = []

        left = left_util.getDoubleArrayItem(ptr0, 0)
        right = right_util.getDoubleArrayItem(ptr1, 0)
        bottom = bot_util.getDoubleArrayItem(ptr2, 0)
        top = top_util.getDoubleArrayItem(ptr3, 0)

        ## planeA = right plane
        a = OpenMaya.MVector(right, top, -self.nearClip)
        b = OpenMaya.MVector(right, bottom, -self.nearClip)
        c = (a ^ b).normal()  ## normal of plane = cross product of vectors a and b
        planeA = Plane(c)
        planes.append(planeA)

        ## planeB = left plane
        a = OpenMaya.MVector(left, bottom, -self.nearClip)
        b = OpenMaya.MVector(left, top, -self.nearClip)
        c = (a ^ b).normal()
        planeB = Plane(c)
        planes.append(planeB)

        ##planeC = bottom plane
        a = OpenMaya.MVector(right, bottom, -self.nearClip)
        b = OpenMaya.MVector(left, bottom, -self.nearClip)
        c = (a ^ b).normal()
        planeC = Plane(c)
        planes.append(planeC)

        ##planeD = top plane
        a = OpenMaya.MVector(left, top, -self.nearClip)
        b = OpenMaya.MVector(right, top, -self.nearClip)
        c = (a ^ b).normal()
        planeD = Plane(c)
        planes.append(planeD)

        # planeE = far plane
        c = OpenMaya.MVector(0, 0, 1)
        planeE = Plane(c)
        planeE.distance = self.farClip
        planes.append(planeE)

        # planeF = near plane
        c = OpenMaya.MVector(0, 0, -1)
        planeF = Plane(c)
        planeF.distance = self.nearClip
        planes.append(planeF)

        self.planes = planes
        self.numPlanes = 6

    def relativeToFrustum(self, pointsArray):
        numInside = 0
        numPoints = len(pointsArray)

        for j in range(0, 6):
            numBehindThisPlane = 0

            for i in range(0, numPoints):
                if (self.planes[j].relativeToPlane(pointsArray[i]) == -1):  # Behind
                    numBehindThisPlane += 1
                if numBehindThisPlane == numPoints:
                    ##all points were behind the same plane
                    return False
                elif (numBehindThisPlane == 0):
                    numInside += 1

        if (numInside == self.numPlanes):
            return True  # Inside
        return True  # Intersect


def in_frustum(cameraName, objectName):
    """
    returns: True if withing the frustum of False if not
    """
    selectionList = OpenMaya.MSelectionList()
    camDagPath = OpenMaya.MDagPath()
    selectionList.add(cameraName)
    selectionList.getDagPath(0, camDagPath)

    cameraDagPath = OpenMaya.MFnCamera(camDagPath)

    camInvWorldMtx = camDagPath.inclusiveMatrixInverse()

    fnCam = Frustum(cameraName)
    points = []

    # For node inobjectList
    selectionList = OpenMaya.MSelectionList()
    objDagPath = OpenMaya.MDagPath()
    selectionList.add(objectName)
    selectionList.getDagPath(0, objDagPath)

    fnDag = OpenMaya.MFnDagNode(objDagPath)
    obj = objDagPath.node()

    dWorldMtx = objDagPath.exclusiveMatrix()
    bbox = fnDag.boundingBox()

    minx = bbox.min().x
    miny = bbox.min().y
    minz = bbox.min().z
    maxx = bbox.max().x
    maxy = bbox.max().y
    maxz = bbox.max().z

    # Getting points relative to the cameras transmformation matrix
    points.append(bbox.min() * dWorldMtx * camInvWorldMtx)
    points.append(OpenMaya.MPoint(maxx, miny, minz) * dWorldMtx * camInvWorldMtx)
    points.append(OpenMaya.MPoint(maxx, miny, maxz) * dWorldMtx * camInvWorldMtx)
    points.append(OpenMaya.MPoint(minx, miny, maxz) * dWorldMtx * camInvWorldMtx)
    points.append(OpenMaya.MPoint(minx, maxy, minz) * dWorldMtx * camInvWorldMtx)
    points.append(OpenMaya.MPoint(maxx, maxy, minz) * dWorldMtx * camInvWorldMtx)
    points.append(bbox.max() * dWorldMtx * camInvWorldMtx)
    points.append(OpenMaya.MPoint(minx, maxy, maxz) * dWorldMtx * camInvWorldMtx)

    return fnCam.relativeToFrustum(points)
