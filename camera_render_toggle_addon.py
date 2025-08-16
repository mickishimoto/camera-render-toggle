"""
Camera Render Toggle (Active vs Others) - Safe

This Blender add-on allows you to quickly toggle rendering visibility
of cameras in your scene:

- Press the toggle button (or run the operator) to *disable rendering*
  for all cameras **except** the active one.
- Press it again to *enable rendering* for **all** cameras.

This is useful for managing multiple cameras during production or export.
It also disables the collections containing those cameras to ensure render exclusion.

Compatible with Blender 4.0+
Author: C-gy
"""

bl_info = {
    "name": "Camera Render Toggle (Active vs Others) - Safe",
    "author": "C-gy",
    "version": (1, 0, 2),
    "blender": (4, 0, 0),
    "location": "3D View > N Panel > Custom",
    "description": "Disable rendering for non-active cameras / Toggle again to enable all (Safe version)",
    "category": "Render",
}

import bpy
from collections import deque

# Ensure persistent toggle state property on WindowManager
def _ensure_state_prop():
    if not hasattr(bpy.types.WindowManager, "cam_toggle_last_action"):
        bpy.types.WindowManager.cam_toggle_last_action = bpy.props.EnumProperty(
            name="Camera Toggle State",
            items=[
                ("enabled_all", "Enabled All", ""),
                ("disabled_others", "Disabled Others", "")
            ],
            default="enabled_all",
            options={'HIDDEN'}
        )

def get_all_camera_objects():
    return [obj for obj in bpy.data.objects if obj.type == 'CAMERA']

# --- FIX: In Blender 4.x, __contains__ on bpy_prop_collection expects string names ---
def collections_of_object(obj):
    cols = []
    name = obj.name
    for col in bpy.data.collections:
        # Use name instead of "obj in col.objects"
        if col.objects.get(name) is not None:
            cols.append(col)
    return cols

# --- Traverse LayerCollections to toggle 'exclude' ---
def iter_layer_collections(root):
    q = deque([root])
    while q:
        lc = q.popleft()
        yield lc
        for child in lc.children:
            q.append(child)

def layer_collections_for_collection(view_layer, collection):
    return [lc for lc in iter_layer_collections(view_layer.layer_collection) if lc.collection == collection]

def set_collection_render_enabled(context, collection, enabled):
    for lc in layer_collections_for_collection(context.view_layer, collection):
        lc.exclude = not enabled

def toggle_camera_collections_render(context):
    wm = context.window_manager
    scene = context.scene
    active_camera = scene.camera
    all_cameras = get_all_camera_objects()

    if not all_cameras:
        raise RuntimeError("No camera found in the scene.")

    if active_camera is None:
        active_camera = all_cameras[0]

    if wm.cam_toggle_last_action != 'disabled_others':
        for cam in all_cameras:
            is_active = (cam == active_camera)
            cam.hide_render = not is_active
            for col in collections_of_object(cam):
                set_collection_render_enabled(context, col, is_active)
        wm.cam_toggle_last_action = 'disabled_others'
        return f"📷 Non-active cameras disabled. Active camera: \"{active_camera.name}\""
    else:
        for cam in all_cameras:
            cam.hide_render = False
            for col in collections_of_object(cam):
                set_collection_render_enabled(context, col, True)
        wm.cam_toggle_last_action = 'enabled_all'
        return "✅ All cameras enabled for rendering."

class OBJECT_OT_toggle_camera_render(bpy.types.Operator):
    bl_idname = "object.toggle_camera_render"
    bl_label = "Toggle Camera Render"
    bl_description = "Disable non-active cameras / Re-enable all cameras"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            msg = toggle_camera_collections_render(context)
        except RuntimeError as e:
            self.report({'WARNING'}, str(e))
            return {'CANCELLED'}
        self.report({'INFO'}, msg)
        return {'FINISHED'}

class CAMERA_RENDER_PT_toggle_panel(bpy.types.Panel):
    bl_label = "Camera Render Toggle"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'C-gy'

    def draw(self, context):
        wm = context.window_manager
        state = getattr(wm, "cam_toggle_last_action", "enabled_all")
        label = "Disable Others" if state != "disabled_others" else "Enable All"
        self.layout.operator("object.toggle_camera_render", icon='RESTRICT_RENDER_OFF', text=label)

addon_keymaps = []

def register():
    _ensure_state_prop()
    bpy.utils.register_class(OBJECT_OT_toggle_camera_render)
    bpy.utils.register_class(CAMERA_RENDER_PT_toggle_panel)

def unregister():
    bpy.utils.unregister_class(CAMERA_RENDER_PT_toggle_panel)
    bpy.utils.unregister_class(OBJECT_OT_toggle_camera_render)
    # Cleanup dynamically added property
    if hasattr(bpy.types.WindowManager, "cam_toggle_last_action"):
        del bpy.types.WindowManager.cam_toggle_last_action

if __name__ == "__main__":
    register()
