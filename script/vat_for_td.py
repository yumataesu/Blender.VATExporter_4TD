import bpy
from bpy.props import *        
import bmesh

bl_info = {
    "name": "VAT for TouchDesigner",
    "author": "YumaTaesu",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "",
    "description": "Export VAT for TouchDesigner",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"
}


def create_mesh_sequence(context, data, object):
    """Return a list of combined mesh data per frame"""
    meshes = []
    for i in range(context.scene.frame_start, context.scene.frame_end):
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
        meshes.append(me)
        
    return meshes

def create_vertex_sequences(data, mesh_seq):
    """Return lists of vertex offsets and normals from a list of mesh data"""
    original = mesh_seq[0].vertices
    offsets = []
    normals = []
    
    for mesh in mesh_seq:
        for v in mesh.vertices:
            offset = v.co - original[v.index].co
            x, y, z = offset
            offsets.extend((x, y, z, 1.0))
            x, y, z = v.normal
            normals.extend(((x + 1.0) * 0.5, (y + 1.0) * 0.5, (z + 1.0) * 0.5, 1.0))

    return offsets, normals

def bake(context, data, offsets, normals, size):
    """Stores vertex offsets and normals in seperate image textures"""
    width, height = size
    offset_texture = data.images.new(
        name="offsets",
        width=width,
        height=height,
        alpha=True,
        float_buffer=True
    )
    normal_texture = data.images.new(
        name="normals",
        width=width,
        height=height,
        alpha=True
    )
    offset_texture.pixels = offsets
    normal_texture.pixels = normals
    
    
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
        start = context.scene.frame_start
        end = context.scene.frame_end
        time_range = end - start + 1
        
        origin_obj = context.selected_objects[0]
        
        mesh_seq = create_mesh_sequence(context, bpy.data, origin_obj)
        
        offsets, normals = create_vertex_sequences(bpy.data, mesh_seq)
        
        texture_size = len(origin_obj.data.vertices), time_range
        bake(context, bpy.data, offsets, normals, texture_size)
        
        origin = mesh_seq[0].copy()
        create_export_mesh_object(context, bpy.data, origin)
        
        context.scene.frame_set(1)
        return {'FINISHED'}


class VIEW3D_PT_VertexAnimationTexture(bpy.types.Panel):
    bl_label = "Vertex Animation"
    bl_idname = "VIEW3D_PT_Vertex_Animation_Texture"
    bl_category = "Touch Designer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Export Vertex & Normal VAT")
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        s = context.scene
        col = layout.column(align=True)
        col.prop(s, "frame_start", text="Frame Start")
        col.prop(s, "frame_end", text="Frame End")
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
  for c in classs:
    bpy.utils.register_class(c)

#
# unregister
#        
def unregister():
  for c in classs:
    bpy.utils.register_class(c)

#
# script entry
#        
if __name__ == "__main__":
  register()

