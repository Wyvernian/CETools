import hou
import os
import glob
import re
import json
from difflib import SequenceMatcher


def alternate_names(name):
    def camel_case(st):
        output = ''.join(x for x in st.title() if x.isalnum())
        return output[0].lower() + output[1:]

    camel_case = camel_case(name)
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    return name, camel_case, snake_case


def read_shader_connections(node, file_path, ignore, try_alternate_names):
    ignore = ignore.split()
    clean_shader_data = {}
    print(try_alternate_names)

    material_library = node.node('auto_materials')
    with open(file_path, 'r') as f:
        shader_data = json.load(f)

    if ignore:
        for shader_reference in shader_data.keys():
            new_key = shader_reference
            for s in ignore:
                new_key = new_key.replace(s, '')
            clean_shader_data[new_key] = shader_data[shader_reference]
        shader_data = clean_shader_data

    for shader_reference in shader_data.keys():
        for i in range(1, int(material_library.parm('materials').rawValue()) + 1):
            material = material_library.parm(f'matnode{i}').rawValue()

            name = shader_reference
            camel_case = 'nhmgo9wrtfu3k'
            snake_case = 'g3qw9fucoj9qkue'

            if try_alternate_names == 'on':
                name, camel_case, snake_case = alternate_names(shader_reference)
            print(name, camel_case, snake_case)

            if shader_reference:
                key = ''

                if name in material:
                    key = name
                if camel_case in material:
                    key = name
                if snake_case in material:
                    key = name

                if key:
                    maya_geo_path = ' '.join(shader_data[key])
                    hou_geo_path = maya_geo_path.replace("|", "/")
                    material_library.parm(f'geopath{i}').set(hou_geo_path)


def closest(seq, args):
    # Cache information about `seq`.
    # We only really need to change one sequence.
    sm = SequenceMatcher(b=seq)

    def _ratio(x):
        sm.set_seq1(x)
        return sm.ratio()

    return max(args, key=_ratio)


def organise_materials(node, prim_path):
    material_library = node.node('auto_materials')
    prims = node.stage().GetPrimAtPath(prim_path).GetAllChildren()
    prim_names = {}
    for prim in prims:
        prim_name = (str(prim).split('/')[-1])
        prim_path = str(prim).split('<')[-1]
        prim_path = str(prim_path).split('>')[0]
        prim_names[prim_name.strip(">)")] = prim_path

    # print(prim_names)
    for i in range(1, int(material_library.parm('materials').rawValue()) + 1):
        material_path = material_library.parm(f'matnode{i}').rawValue()
        best_match = closest(material_path.split('_')[-1], tuple(prim_names.keys()))
        material_library.parm(f'geopath{i}').set(prim_names[best_match])


def texture_to_raw(file_node, shading_group, shader_key):
    file_node.parm('color_family').set('Utility')
    file_node.parm('color_space').set('Utility - Raw')
    color_correct = shading_group.createNode("arnold::color_correct", run_init_scripts=False,
                                             node_name=f'{file_node.name()}_cc')
    color_correct.parm('alpha_is_luminance').set(1)
    color_correct.setNamedInput('input', file_node, 'rgba')
    return color_correct


def create_ai_standard_surface(node, name='aiStandardSurface'):
    material = node.createNode('arnold_materialbuilder', node_name=name)
    shader = material.createNode("arnold::standard_surface", run_init_scripts=False, node_name=f'{name}_ss')
    shading_group = material.node("OUT_material")
    shading_group.setNamedInput('surface', shader, 'shader')

    return shader, material, shading_group


def connect_textures(node, folder_path, udim=False, use_latest=True, shader_from_file=True):
    texture_types = {
        'BaseColor': ['rgba', 'base_color'],
        'Roughness': ['a', 'specular'],
        'Metalness': ['a', 'metalness'],
        'Normal': ['a', 'normal'],
    }
    # 'Emissive': ['outAlpha', 'emission']
    #         'Height': ['a', 'height'],

    material = ''

    material_library = hou.pwd().node('auto_materials')

    if not os.path.exists(folder_path):
        hou.ui.displayMessage(f"Invalid file path at:   {folder_path}")
        return

    image_files = [f for f in glob.iglob(f'{folder_path}/*') if f.endswith((".png", ".jpg", ".tiff"))]

    if use_latest is True:
        image_files.sort(key=lambda f: int(''.join(filter(str.isdigit, f))))

    if shader_from_file is True:
        image_files = [f for f in glob.iglob(f'{folder_path}/*') if f.endswith((".png", ".jpg", ".tiff"))]
        material_groups = {}
        for file in image_files:
            for texture_type in texture_types.keys():
                if texture_type in file:
                    file_name = os.path.basename(file)
                    shader_name = file_name.split(texture_type)[0]
                    tile_id = re.findall(r"\d+", file_name)[-1]
                    if shader_name not in material_groups.keys():
                        material_groups[shader_name] = {}
                    if texture_type not in material_groups[shader_name].keys():
                        material_groups[shader_name][texture_type] = {}
                    material_groups[shader_name][texture_type][tile_id] = file

    for shader_key in material_groups.keys():

        shader, material, shading_group = create_ai_standard_surface(node=material_library,
                                                                     name=f'{shader_key.strip("_")}')

        for texture in material_groups[shader_key].keys():

            highest_tile_id = max(material_groups[shader_key][texture].keys())
            file_name = material_groups[shader_key][texture][highest_tile_id]

            file_node = material.createNode("arnold::image", node_name=f'{shader_key}{texture}')

            if len(material_groups[shader_key][texture].keys()) == 1:
                file_node.parm('filename').set(file_name)
            else:
                udim_name = re.sub('(\d{4})', "<UDIM>", file_name)
                file_node.parm('filename').set(udim_name)

            if texture_types[texture][0] == 'a':
                file_node = texture_to_raw(file_node, material, shader_key)
            else:
                file_node.parm('color_family').set('Utility')
                file_node.parm('color_space').set('Utility - sRGB - Texture')

            if texture_types[texture][1] == 'normal':
                bump2d = material.createNode('bump2d', run_init_scripts=False, node_name=f'{shader_key}bump')
                bump2d.setNamedInput('bump_map', file_node, 'a')
                shader.setNamedInput('normal', bump2d, 'vector')
            else:
                shader.setNamedInput(f'{texture_types[texture][1]}', file_node, f'{texture_types[texture][0]}')

            material.layoutChildren(vertical_spacing=2)

    material_library.layoutChildren()
