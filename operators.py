  
import bpy
from bpy.props import *        
import bmesh

def create_sequence(context, data, object):
    """Return a list of offsets normal data per frame & mesh of first frame """

    offsets = []
    normals = []
    first_frame_mesh = None
    
    s = context.scene.start_frame
    e = context.scene.end_frame
    
    for i in range(s, e+1):
        context.scene.frame_set(i)
        depsgraph = context.evaluated_depsgraph_get()
        bm = bmesh.new()
        eval_object = object.evaluated_get(depsgraph)
        me = data.meshes.new_from_object(eval_object)
        me.transform(object.matrix_world)
        bm.from_mesh(me)
        data.meshes.remove(me)
        
        me = data.meshes.new("mesh")
        bm.to_mesh(me)
        bm.free()
        me.calc_normals()

        if i == s:
            first_frame_mesh = me.copy()
        
        original = first_frame_mesh[0].vertices
        for v in me.vertices:
            offset = v.co - original[v.index].co
            x, y, z = offset
            offsets.extend((x, y, z, 1.0))
            x, y, z = v.normal
            normals.extend(((x + 1.0) * 0.5, (y + 1.0) * 0.5, (z + 1.0) * 0.5, 1.0))


    return offsets, normals, first_frame_mesh


def bake(context, data, offsets, normals, size):
    """Stores vertex offsets and normals in seperate image textures"""
    width, height = size
    offset_texture = data.images.new(
        name="offsets",
        width=width,
        height=height,
        alpha=False,
        float_buffer=True
    )
    normal_texture = data.images.new(
        name="normals",
        width=width,
        height=height,
        alpha=False
    )
    offset_texture.pixels = offsets
    normal_texture.pixels = normals

    return offset_texture, normal_texture

    
    
def create_export_mesh_object(context, data, me):
    """Create a mesh object with custom VAT UV attribute"""
    while len(me.uv_layers) < 2:
        me.uv_layers.new()
    uv_layer = me.uv_layers[1]
    uv_layer.name = "vertex_anim"
    for loop in me.loops:
        uv_layer.data[loop.index].uv = (
            (loop.vertex_index + 0.5)/len(me.vertices), 0
        )
    ob = data.objects.new("export_mesh", me)
    context.scene.collection.objects.link(ob)
    return ob


class OBJECT_OT_VertexAnimationTexture(bpy.types.Operator):
    bl_idname = "object.vertexanimationtexture"
    bl_label = "Vertex Animation Texture"
    bl_options = {'REGISTER', 'UNDO'}
    
    #--- execute ---#
    def execute(self, context):
        s = context.scene.start_frame
        e = context.scene.end_frame
        p = context.scene.export_path
        time_range = e - s + 1
        if not p:
            print('[error] : export path is empty.')
            return

        
        origin_obj = context.selected_objects[0]
        texture_size = len(origin_obj.data.vertices), time_range
        
        # create offsets & normal textures---------------------------------
        offsets, normals, origin = create_sequence(context, bpy.data, origin_obj) 
        offset_texture, normal_texture = bake(context, bpy.data, offsets, normals, texture_size)

        # create mesh object with custom attribute---------------------------------
        mobj = create_export_mesh_object(context, bpy.data, origin)

        # export assets---------------------------------
        origin_obj.select_set(False)
        mobj.select_set(True)
        bpy.ops.export_scene.fbx(filepath=p + "model.fbx", use_selection=True, global_scale=0.01)

        offset_texture.file_format = 'OPEN_EXR'
        offset_texture.filepath_raw = p + "offsets.exr"
        offset_texture.save()

        # todo : save 16bit or 10bit / RGB format for memory friendly.
        normal_texture.file_format = 'OPEN_EXR'
        normal_texture.filepath_raw = p + "normals.exr"
        normal_texture.save()


        context.scene.frame_set(1)
        return {'FINISHED'}


class VIEW3D_PT_VertexAnimationTexture(bpy.types.Panel):
    bl_label = "VAT Exporter"
    bl_idname = "VIEW3D_PT_Vertex_Animation_Texture"
    bl_category = "Touch Designer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        layout = self.layout
        # layout.label(text="Export Vertex & Normal VAT")
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        s = context.scene
        col = layout.column(align=True)
        col.prop(s, "start_frame")
        col.prop(s, "end_frame")
        col.prop(s, 'export_path')
        layout.operator(OBJECT_OT_VertexAnimationTexture.bl_idname, text = "Export")

#
# register classs
#
classs = [
  VIEW3D_PT_VertexAnimationTexture,
  OBJECT_OT_VertexAnimationTexture
]

#
# register
#
def register():
    bpy.types.Scene.start_frame = bpy.props.IntProperty(
        name = "Frame Start",
        default = 1,
        description = "Set start frame",
        min = 1,
        max = 4098
    )
    bpy.types.Scene.end_frame = bpy.props.IntProperty(
        name = "Frame End",
        default = 300,
        description = "Set end frame",
        min = 1,
        max = 4096
    )
    bpy.types.Scene.export_path = bpy.props.StringProperty(
        name = "Export Directory",
        default = "",
        description = "Set your export dir for fbx & vats",
        subtype = 'DIR_PATH'
    )
    
    # for c in classs:
    #     bpy.utils.register_class(c)

#
# unregister
#        
def unregister():
    del bpy.types.Scene.start_frame
    del bpy.types.Scene.end_frame
    del bpy.types.Scene.export_path

    # for c in classs:
    #     bpy.utils.register_class(c)

#
# script entry
#        
# if __name__ == "__main__":
#   register()


# comment out if you develop
# unregister()
# register()
