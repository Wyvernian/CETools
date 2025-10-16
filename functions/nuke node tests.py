import nuke


def traverse_group():
    btn_knob = nuke.thisKnob()
    channel_name = btn_knob.name().split('_dyn_')[0]

    node = nuke.thisNode()
    nuke.showDag(node)
    node.begin()
    for node in nuke.allNodes('BackdropNode'):
        if channel_name == node.knob('label').value():
            x_centre = node.xpos() + node.screenWidth() / 2
            y_centre = node.ypos() + node.screenHeight() / 2
            nuke.zoom(1, [x_centre, y_centre])


traverse_group_str = """
btn_knob = nuke.thisKnob()
channel_name = btn_knob.name().split('_dyn_')[0]

node = nuke.thisNode()
nuke.showDag(node)
node.begin()
for node in nuke.allNodes('BackdropNode'):
    if channel_name == node.knob('label').value():
        x_centre = node.xpos() + node.screenWidth() / 2
        y_centre = node.ypos() + node.screenHeight() / 2
        nuke.zoom(1, [x_centre, y_centre])
"""


def delete_all():
    # Give to the Clear All button
    for knob in nuke.thisNode().knobs():
        if '_dyn_' in knob:
            nuke.thisNode().removeKnob(nuke.thisNode().knob(knob))

    nuke.thisNode().begin()
    for node in nuke.allNodes():
        if node.knob('name').value() == 'input':
            continue
        elif node.knob('name').value() == 'Output1':
            continue
        else:
            nuke.delete(node)


def delete_channel():
    # Give this command to each delete button
    btn_knob = nuke.thisKnob()
    channel_name = btn_knob.name().split('_dyn_')[0]

    for knob in nuke.thisNode().knobs():
        if channel_name == knob.split('_dyn_')[0]:
            nuke.thisNode().removeKnob(nuke.thisNode().knob(knob))

    nuke.thisNode().begin()
    for node in nuke.allNodes('BackdropNode'):
        if channel_name == node.knob('name').value().split('_dyn_')[0]:
            node.selectNodes(True)
            children = nuke.selectedNodes()
            for n in children:
                nuke.delete(n)
            nuke.delete(node)


delete_channel_str = """
btn_knob = nuke.thisKnob()
channel_name = btn_knob.name().split('_dyn_')[0]

for knob in nuke.thisNode().knobs():
    if channel_name == knob.split('_dyn_')[0]:
        nuke.thisNode().removeKnob(nuke.thisNode().knob(knob))

nuke.thisNode().begin()
for node in nuke.allNodes('BackdropNode'):
    if channel_name == node.knob('name').value().split('_dyn_')[0]:
        node.selectNodes(True)
        children = nuke.selectedNodes()
        for n in children:
            nuke.delete(n)
        nuke.delete(node)
"""


def connect_viewer():
    # Give this command to each view button
    btn_knob = nuke.thisKnob()
    knob_name = btn_knob.name().split('_dyn_')[0]

    nuke.thisNode().begin()
    for node in nuke.allNodes('Switch'):
        if knob_name == node.knob('name').value().split('_dyn_')[0]:
            nuke.connectViewer(0, node)


connect_viewer_str = """
btn_knob = nuke.thisKnob()
knob_name = btn_knob.name().split('_dyn_')[0]

nuke.thisNode().begin()
for node in nuke.allNodes('Switch'):
    if knob_name == node.knob('name').value().split('_dyn_')[0]:
        nuke.connectViewer(0, node)
"""


def mute_channel():
    # Give this command to each mute button
    btn_knob = nuke.thisKnob()
    knob_name = btn_knob.name().split('_dyn_')[0]

    nuke.thisNode().begin()
    for node in nuke.allNodes('Merge'):
        if knob_name == node.knob('label').value() and '_merge_plus' in node.knob('name').value():
            state = node['disable'].getValue()
            if state:
                btn_knob.setLabel("Light: On")
            else:
                btn_knob.setLabel("Light: Off")
            node['disable'].setValue(not state)


mute_channel_str = """
btn_knob = nuke.thisKnob()
knob_name = btn_knob.name().split('_dyn_')[0]

nuke.thisNode().begin()
for node in nuke.allNodes('Merge'):
    if knob_name == node.knob('label').value() and '_merge_plus' in node.knob('name').value():
        state = node['disable'].getValue()
        if state:
            btn_knob.setLabel("Light: On")
        else:
            btn_knob.setLabel("Light: Off")
        node['disable'].setValue(not state)
"""


def mute_edits():
    # Give this command to each mute button
    btn_knob = nuke.thisKnob()
    knob_name = btn_knob.name().split('_dyn_')[0]

    nuke.thisNode().begin()
    for node in nuke.allNodes('Switch'):
        if knob_name == node.knob('name').value().split('_dyn_')[0]:
            state = node['which'].getValue()
            if state:
                btn_knob.setLabel("Show Default: Off")
            else:
                btn_knob.setLabel("Show Default: On")
            node['which'].setValue(not state)


mute_grade_str = """
btn_knob = nuke.thisKnob()
knob_name = btn_knob.name().split('_dyn_')[0]

nuke.thisNode().begin()
for node in nuke.allNodes('Switch'):
    if knob_name == node.knob('name').value().split('_dyn_')[0]:
        state = node['which'].getValue()
        if state:
            btn_knob.setLabel("Show Default: Off")
        else:
            btn_knob.setLabel("Show Default: On")
        node['which'].setValue(not state)

"""


def move_backdrop_nodes(node, x_pos: int, y_pos: int):
    # Old position of Backdrop#
    position_x = node.xpos()
    position_y = node.ypos()

    # Select nodes in Backdrop#
    node.selectNodes(True)

    # Move Backdrop to new position#
    node.setXYpos(x_pos, y_pos)

    # Calculate offset between new and old Backdrop position#
    offset_x = position_x - node.xpos()
    offset_y = position_y - node.ypos()

    # Set new position for nodes in Backdrop
    for n in nuke.selectedNodes():
        cur_xpos = n.xpos()
        cur_ypos = n.ypos()
        n.setXYpos(cur_xpos - offset_x, cur_ypos - offset_y)
        n.setSelected(False)


def sort_backdrops():
    # Get y pos of all backdrops, sort them from lowest to highest, then condense so all backdrops positions start 30
    # pixels after the previous (should retain an expanded size backdrop)
    parent_node = nuke.thisNode()
    parent_node.begin()
    input_dot_01 = parent_node.node('input_dot_dyn_01')

    backdrops = [n for n in nuke.allNodes('BackdropNode') if '_dyn_' in n.knob('name').value()]
    backdrops.sort(key=lambda n: n.ypos())

    for i in range(len(backdrops)):
        if i == 0:
            move_backdrop_nodes(backdrops[i], input_dot_01.xpos() - 15, input_dot_01.ypos() + 35)

        else:
            move_backdrop_nodes(backdrops[i], input_dot_01.xpos() - 15,
                                round(backdrops[i - 1].ypos() + backdrops[i - 1]['bdheight'].value()) + 35)


def update_inputs():
    # For Subrat: Add color, intensity, exposure (don't know that the S M D stuff means)

    parent_node = nuke.thisNode()
    output_node = parent_node.node('Output1')

    # Create input node if it doesn't exist
    input_node = parent_node.node('input') or nuke.nodes.Input(name='input')

    # Input channel dots
    input_dot_01 = parent_node.node('input_dot_dyn_01')
    if not input_dot_01:
        input_dot_01 = nuke.nodes.Dot(name='input_dot_dyn_01')
        input_dot_01.setInput(0, input_node)
        output_node.setInput(0, input_dot_01)

    input_dot_02 = parent_node.node('input_dot_dyn_02') or nuke.nodes.Dot(name='input_dot_dyn_02',
                                                                          label='input_stream_begin')
    input_dot_02.setInput(0, input_dot_01)

    input_dot_01.setXYpos(input_node.xpos() + 34, input_node.ypos() + 50)
    input_dot_02.setXYpos(input_node.xpos() + 34 + 420, input_node.ypos() + 50)

    # Set lowest dot to continue the input chain from
    end_dot = parent_node.node('end_dot_dyn_')
    input_dots = [end_dot or input_dot_02]

    channels = input_node.channels()
    if channels:
        layers = list(set([channel.split('.')[0] for channel in channels if
                           'direct' in channel or 'rgb' in channel.lower()]))

        # Only add layers that don't currently exist
        knob_list = [x for x in parent_node.knobs() if '_dyn_' in x]
        if knob_list:
            layers = [x for x in layers if x not in [y.split('_dyn_')[0] for y in knob_list]]

        layers.sort()

        # Set node to insert layers after the Input1 or the latest node plugged into the Output1
        merge_nodes = [output_node.input(0)]

        if layers:
            if 'mix_slider' not in parent_node.knobs():
                mix_knob = nuke.Double_Knob('mix_slider', 'mix')
                mix_knob.setRange(0.0, 1.0)
                mix_knob.setValue(1.0)
                parent_node.addKnob(mix_knob)
                nuke.knobDefault('mix_slider', "1")

            for layer in layers:

                # Dots for organisation
                dot_01 = nuke.nodes.Dot(name=f'{layer}_dyn_dot_01', inputs=[merge_nodes[-1]])

                dot_02 = nuke.nodes.Dot(name=f'{layer}_dyn_dot_01', inputs=[dot_01])

                input_dot_03 = nuke.nodes.Dot(name=f'{layer}_dyn_input_dot_03', inputs=[input_dots[-1]])
                input_dot_04 = nuke.nodes.Dot(name=f'{layer}_dyn_input_dot_04', inputs=[input_dot_03])
                input_dots.append(input_dot_04)

                # Shuffle Node
                shuffle_node = nuke.nodes.Shuffle(name=f'{layer}_dyn_shuffle', label=layer, inputs=[dot_02])
                shuffle_node['in'].setValue(layer)

                # Merge From
                merge_from = nuke.nodes.Merge(name=f'{layer}_dyn_merge_from', label=layer,
                                              inputs=[dot_01, shuffle_node],
                                              operation='from')

                # Group
                layer_group_begin = nuke.Tab_Knob(f'{layer}_dyn_group_begin', layer, nuke.TABBEGINGROUP)
                layer_group_begin.setValue(False)
                parent_node.addKnob(layer_group_begin)

                # View Channel
                view_channel_button = nuke.PyScript_Knob(f'{layer}_dyn_view_btn', 'View Light',
                                                         f"{connect_viewer_str}")
                view_channel_button.setFlag(nuke.STARTLINE)
                parent_node.addKnob(view_channel_button)

                # Mute Channel
                mute_channel_button = nuke.PyScript_Knob(f'{layer}_dyn_channel_mute_btn', 'Light: On',
                                                         f"{mute_channel_str}")
                parent_node.addKnob(mute_channel_button)

                # Mute Channel
                mute_grade_button = nuke.PyScript_Knob(f'{layer}_dyn_grade_mute_btn', 'Show Default: Off',
                                                       f"{mute_grade_str}")
                parent_node.addKnob(mute_grade_button)

                # Traverse Group
                traverse_button = nuke.PyScript_Knob(f'{layer}_dyn_jump', 'Jump To Nodes', f"{traverse_group_str}")
                parent_node.addKnob(traverse_button)

                # Delete Channel
                delete_channel_button = nuke.PyScript_Knob(f'{layer}_dyn_delete_btn', 'X', f"{delete_channel_str}")
                parent_node.addKnob(delete_channel_button)

                # Grade, Link to sliders
                grade_node = nuke.nodes.Grade(name=f'{layer}_dyn_grade', label=layer, inputs=[shuffle_node])

                # I like dots
                dot_03 = nuke.nodes.Dot(name=f'{layer}_dyn_dot_03', inputs=[shuffle_node])
                dot_04 = nuke.nodes.Dot(name=f'{layer}_dyn_dot_04', inputs=[dot_03])

                # Switch Node
                switch_node = nuke.nodes.Switch(name=f'{layer}_dyn_switch', label=layer, inputs=[grade_node, dot_04])

                # Sticky note warning !!!1!
                sticky_note = nuke.nodes.StickyNote(name=f'{layer}_dyn_sticky', label="<font color='white'><b><center"
                                                                                      ">SHOW DEFAULT\nKEEP PIPE "
                                                                                      "CLEAR</center></b></font>")
                sticky_note['tile_color'].setValue(int("FF0000FF", 16))

                # Merge Plus
                merge_plus = nuke.nodes.Merge(name=f'{layer}_dyn_merge_plus', label=layer,
                                              inputs=[merge_from, switch_node],
                                              operation='plus')

                # Set mix for both merge nodes
                merge_from['mix'].setExpression('mix_slider')
                merge_plus['mix'].setExpression('mix_slider')

                # Multiply
                mult_slider = nuke.Color_Knob(f'{layer}_dyn_multiply', 'color')
                mult_slider.setValue(1)
                mult_slider.setRange(0, 4)
                parent_node.addKnob(mult_slider)
                grade_node['multiply'].setValue([1, 1, 1, 1])
                grade_node['multiply'].setExpression(f'{layer}_dyn_multiply')
                nuke.knobDefault(f'{layer}_dyn_multiply', "1")

                # Intensity = Gain * 2^Exposure
                # Gain
                gain_slider = nuke.Double_Knob(f'{layer}_dyn_intensity', 'intensity')
                gain_slider.setValue(1.0)
                gain_slider.setRange(0.0, 10.0)
                parent_node.addKnob(gain_slider)
                nuke.knobDefault(f'{layer}_dyn_intensity', "1")

                # Exposure
                gain_slider = nuke.Double_Knob(f'{layer}_dyn_exposure', 'exposure')
                gain_slider.setValue(0.0)
                gain_slider.setRange(-5.0, 5.0)
                parent_node.addKnob(gain_slider)
                grade_node['white'].setValue([1, 1, 1, 1])
                grade_node['white'].setExpression(f'max(pow(2, {layer}_dyn_exposure) * {layer}_dyn_intensity, 0)')
                nuke.knobDefault(f'{layer}_dyn_exposure', "0")

                # Offset
                offset_slider = nuke.Color_Knob(f'{layer}_dyn_add', 'offset')
                offset_slider.setValue(0)
                offset_slider.setRange(-1, 1)
                parent_node.addKnob(offset_slider)
                grade_node['add'].setValue([1, 1, 1, 1])
                grade_node['add'].setExpression(f'{layer}_dyn_add')
                nuke.knobDefault(f'{layer}_dyn_offset', "0")

                # Gamma
                gamma_slider = nuke.Color_Knob(f'{layer}_dyn_gamma', 'gamma')
                gamma_slider.setValue(1)
                gamma_slider.setRange(0.2, 5)
                parent_node.addKnob(gamma_slider)
                grade_node['gamma'].setValue([1, 1, 1, 1])
                grade_node['gamma'].setExpression(f'{layer}_dyn_gamma')
                nuke.knobDefault(f'{layer}_dyn_gamma', "1")

                # Close group
                layer_group_end = nuke.Tab_Knob(f'{layer}_dyn_group_end', None, nuke.TABENDGROUP)
                parent_node.addKnob(layer_group_end)

                # Set all node positions, standard node center is 34 for some reason (even though most are 80 px wide)
                node_centre = 34
                origin_x = round(merge_nodes[-1].xpos() + node_centre)

                # Create backdrop
                backdrop = nuke.nodes.BackdropNode(name=f'{layer}_dyn_backdrop', label=layer)
                backdrop.setXYpos(merge_nodes[-1].xpos() - 10, merge_nodes[-1].ypos() + 75)
                backdrop['bdwidth'].setValue(525)
                backdrop['bdheight'].setValue(670)

                # Set node positions
                dot_01.setXYpos(origin_x, merge_nodes[-1].ypos() + 100)
                dot_02.setXYpos(origin_x + 200, merge_nodes[-1].ypos() + 100)
                shuffle_node.setXYpos(origin_x + 200 - node_centre, merge_nodes[-1].ypos() + 155)
                merge_from.setXYpos(origin_x - 34, merge_nodes[-1].ypos() + 153)
                grade_node.setXYpos(origin_x + 200 - node_centre, merge_nodes[-1].ypos() + 210)
                input_dot_03.setXYpos(input_node.xpos() + 450 + node_centre, merge_nodes[-1].ypos() + 100)
                input_dot_04.setXYpos(input_node.xpos() + 450 + node_centre, merge_nodes[-1].ypos() + 720)
                dot_03.setXYpos(origin_x + 70, merge_nodes[-1].ypos() + 210)
                sticky_note.setXYpos(origin_x + 20, merge_nodes[-1].ypos() + 400)
                dot_04.setXYpos(origin_x + 70, merge_nodes[-1].ypos() + 680)
                switch_node.setXYpos(origin_x + 200 - node_centre, merge_nodes[-1].ypos() + 700)
                merge_plus.setXYpos(origin_x - 34, merge_nodes[-1].ypos() + 700)

                merge_nodes.append(merge_plus)

                # Set last merge node to be output at 0 (this works just go with it)
                output_node.setInput(0, merge_plus)

            # Organise everything
            sort_backdrops()

            # Push output to below the last merge node
            output_node.setXYpos(merge_nodes[-1].xpos(), merge_nodes[-1].ypos() + 100)

            # Get and set a new End Dot, so when the script adds more nodes it knows where to start the input chain from
            if end_dot:
                nuke.delete(end_dot)
            end_dot = nuke.nodes.Dot(name='end_dot_dyn_', label='input_stream_end', inputs=[input_dots[-1]])
            end_dot.setXYpos(input_node.xpos() + 400 + node_centre, output_node.ypos())


update_inputs()
