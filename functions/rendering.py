import logging
import os

import maya.cmds as cmds
from math import floor
import mtoa.utils as mutils

from CETools.functions.commonFunctions import get_object_type, UndoStack


def smart_light_portals():
    pass


def ibl_presets():
    pass


def build_cyc():
    cyc = cmds.polyPlane(w=20, h=10, sx=1, sy=5)
    cmds.polyExtrudeEdge(f'{cyc[0]}.e[15]', kft=1, ltz=8)
    cmds.setAttr(f'{cyc[0]}.displaySmoothMesh', 2)

    return cyc


def light_setup(preset):
    light_presets = {
        "standard_1": {
            "key": {
                "intensity": 18.0,
                "color": (1.0, 1.0, 1.0),
                "exposure": 0.0,
                "translate": (0.0, 0.0, 0.0),
                "rotation": (0.0, 0.0, 0.0),
                "scale": (1.0, 1.0, 1.0),
            },
            "fill": {
                "intensity": 1.0,
                "color": (1.0, 1.0, 1.0),
                "exposure": 0.0,
            },
            "back": {
                "intensity": 1.0,
                "color": (1.0, 1.0, 1.0),
                "exposure": 0.0,
            },
        },
        "warm_1": {
            "key": {
                "intensity": 1.0,
                "aiColorTemperature": 4000,
                "exposure": 15.0,
                "translate": (-4.0, 3.0, 4.0),
                "rotate": (-10.0, -45.0, 0.0),
                "scale": (1.0, 1.0, 1.0),
            },
            "fill": {
                "intensity": 0.5,
                "aiColorTemperature": 5000,
                "aiSpread": 0.2,
                "exposure": 15.0,
                "translate": (4.0, 1.0, 4.0),
                "rotate": (10.0, 45.0, 0.0),
                "scale": (1.0, 0.2, 1.0),
            },
            "back": {
                "intensity": 0.2,
                "aiColorTemperature": 6000,
                "aiSpread": 0.2,
                "exposure": 15.0,
                "translate": (-4.0, 3.0, -4.0),
                "rotate": (-20.0, -135.0, 0.0),
                "scale": (1.0, 0.2, 1.0),
            },
        },
        "cool_1": {
            "key": {
                "intensity": 1.0,
                "color": (1.0, 1.0, 1.0),
                "exposure": 0.0,
            },
            "fill": {
                "intensity": 1.0,
                "color": (1.0, 1.0, 1.0),
                "exposure": 0.0,
            },
            "back": {
                "intensity": 1.0,
                "color": (1.0, 1.0, 1.0),
                "exposure": 0.0,
            },
        },
    }

    lights = []

    for light in light_presets[preset]:

        light_obj = mutils.createLocator('aiAreaLight', asLight=True)  # n=

        light_attributes = light_presets[preset][light]

        for attr in light_attributes:
            if isinstance(light_attributes[attr], tuple):
                for i, axis in enumerate(('X', 'Y', 'Z')):
                    cmds.setAttr(f'{light_obj[1]}.{attr}{axis}', light_attributes[attr][i])
            else:
                cmds.setAttr(f'{light_obj[0]}.{attr}', light_attributes[attr])

        if light_attributes['aiColorTemperature']:
            cmds.setAttr(f'{light_obj[0]}.aiUseColorTemperature', 1)

        light_name = cmds.rename(light_obj[1], f'tt_{light}_light_01')

        lights.append(light_name)

        # grp = cmds.group(light,n=f'{light_values[i]}_offset')
        # cmds.xform(rp=(0, 0, 0), t=5, ro=(0, 30, 0))
    return lights


def set_renderer(renderer):
    try:
        cmds.setAttr("defaultRenderGlobals.currentRenderer", renderer, type="string")
    except:
        cmds.error("{} renderer not found.".format(renderer))
        return


def set_overscan(overscan_value, is_percent, is_pixels):
    def overscan_operation(value, is_screen):
        if is_percent:
            return value * overscan_value / 100
        elif is_pixels:
            return overscan_value
        else:
            cmds.error("Well, you fucking broke it. Good one. Don't know how you managed that.")

    with UndoStack('overscan'):

        selected = cmds.ls(sl=1, l=1)
        if get_object_type(selected[0]) == 'camera':
            camera = selected[0]
            cam_shape = cmds.listRelatives(camera)
            image_plane = cmds.listRelatives(cam_shape)

            try:
                image_shape = cmds.listRelatives(image_plane)[0]
            except TypeError:
                logging.warning('Current camera needs an image plane.')
                return

            width = cmds.getAttr(f'{image_shape}.coverageX')
            height = cmds.getAttr(f'{image_shape}.coverageY')

            screen_width = cmds.getAttr(f'{cam_shape[0]}.horizontalFilmAperture')
            screen_height = cmds.getAttr(f'{cam_shape[0]}.verticalFilmAperture')

            width += overscan_operation(width, is_screen=False)
            height += overscan_operation(height, is_screen=False)

            # screen_width = overscan_operation(screen_width, is_screen=True)
            # screen_height = overscan_operation(screen_height, is_screen=True)

            cmds.setAttr("defaultResolution.width", width)
            cmds.setAttr("defaultResolution.height", height)
            # cmds.setAttr(f'{image_shape}.sizeX', screen_width)
            # cmds.setAttr(f'{image_shape}.sizeY', screen_height)
            cmds.setAttr(f'{cam_shape[0]}.cameraScale', 1 + overscan_value / 100)
