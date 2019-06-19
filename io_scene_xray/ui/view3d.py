import bpy

from .base import XRayPanel, build_label
from ..skls_browser import UI_SklsList_item, OpBrowseSklsFile, OpCloseSklsFile
from .. import registry
from .. import plugin


@registry.requires(UI_SklsList_item, OpBrowseSklsFile, OpCloseSklsFile)
@registry.module_thing
class VIEW3D_PT_skls_animations(XRayPanel):
    'Contains open .skls file operator, animations list'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = build_label('Skls File Browser')

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.operator(operator=OpBrowseSklsFile.bl_idname, text='Open skls file...')
        if hasattr(context.object.xray, 'skls_browser'):
            if len(context.object.xray.skls_browser.animations):
                layout.operator(OpCloseSklsFile.bl_idname)
            layout.template_list(listtype_name='UI_SklsList_item', list_id='compact',
                dataptr=context.object.xray.skls_browser, propname='animations',
                active_dataptr=context.object.xray.skls_browser, active_propname='animations_index', rows=5)


class XRayColorizeMaterials(bpy.types.Operator):
    bl_idname = 'io_scene_xray.colorize_materials'
    bl_label = 'Colorize Materials'
    bl_description = 'Set a pseudo-random diffuse color for each surface (material)'

    seed = bpy.props.IntProperty(min=0, max=255)
    power = bpy.props.FloatProperty(default=0.5, min=0.0, max=1.0)

    def execute(self, context):
        from zlib import crc32

        objects = context.selected_objects
        if not objects:
            self.report({'ERROR'}, 'No objects selected')
            return {'CANCELLED'}

        seed = self.seed
        power = self.power
        materials = set()
        for obj in objects:
            for slot in obj.material_slots:
                materials.add(slot.material)

        for mat in materials:
            data = bytearray(mat.name, 'utf8')
            data.append(seed)
            hsh = crc32(data)
            mat.diffuse_color.hsv = (
                (hsh & 0xFF) / 0xFF,
                (((hsh >> 8) & 3) / 3 * 0.5 + 0.5) * power,
                ((hsh >> 2) & 1) * (0.5 * power) + 0.5
            )
        return {'FINISHED'}


@registry.requires(XRayColorizeMaterials)
@registry.module_thing
class XRayMaterialToolsPanel(bpy.types.Panel):
    bl_label = 'XRay Material'
    bl_category = 'XRay'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw_header(self, _context):
        icon = plugin.get_stalker_icon()
        self.layout.label(icon_value=icon)

    def draw(self, context):
        data = context.scene.xray
        layout = self.layout
        column = layout.column(align=True)
        operator = column.operator(XRayColorizeMaterials.bl_idname, icon='COLOR')
        operator.seed = data.materials_colorize_random_seed
        operator.power = data.materials_colorize_color_power
        column.prop(data, 'materials_colorize_random_seed', text='Seed')
        column.prop(data, 'materials_colorize_color_power', text='Power', slider=True)
