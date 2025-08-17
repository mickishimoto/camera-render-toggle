"""
Camera Render Tools (Toggle + Batch Render)

This Blender add-on provides two tools for managing camera rendering:

1. Camera Render Toggle:
   - Disables rendering for all cameras **except** the currently active one.
   - Press again to re-enable all cameras.
   - Also toggles visibility in collections (safe for rendering control).

2. Batch Render Cameras:
   - Renders animation for all cameras that are currently enabled for rendering.
   - Output folder and auto-shutdown options are configurable from the UI.
   - Uses current Render Properties (engine and output format).
   - Saves log file and filenames with camera names and timestamps.

Location: 3D View > N Panel > C-gy tab

Author: C-gy
Compatible with Blender 4.0+
"""



bl_info = {
    "name": "Camera Render Tools (Toggle + Batch Render)",
    "author": "C-gy",
    "version": (1, 2, 0),
    "blender": (4, 0, 0),
    "location": "3D View > N Panel > C-gy",
    "description": "Toggle camera render visibility and batch render active cameras",
    "category": "Render",
}

import bpy
import os
import time
import datetime
import platform
from bpy.props import StringProperty, BoolProperty, EnumProperty, PointerProperty
from bpy.types import PropertyGroup, Operator, Panel
from collections import deque

# --------------------------
# Utility
# --------------------------

def is_renderable(obj):
    if obj.hide_render:
        return False
    for collection in obj.users_collection:
        if collection.hide_render:
            return False
    return True

def get_all_camera_objects():
    return [obj for obj in bpy.data.objects if obj.type == 'CAMERA']

def get_renderable_cameras():
    return [cam for cam in get_all_camera_objects() if is_renderable(cam)]

def collections_of_object(obj):
    name = obj.name
    return [col for col in bpy.data.collections if col.objects.get(name) is not None]

def iter_layer_collections(root):
    q = deque([root])
    while q:
        lc = q.popleft()
        yield lc
        q.extend(lc.children)

def layer_collections_for_collection(view_layer, collection):
    return [lc for lc in iter_layer_collections(view_layer.layer_collection) if lc.collection == collection]

def set_collection_render_enabled(context, collection, enabled):
    for lc in layer_collections_for_collection(context.view_layer, collection):
        lc.exclude = not enabled

# --------------------------
# State Property (Toggle)
# --------------------------

def _ensure_state_prop():
    if not hasattr(bpy.types.WindowManager, "cam_toggle_last_action"):
        bpy.types.WindowManager.cam_toggle_last_action = EnumProperty(
            name="Camera Toggle State",
            items=[
                ("enabled_all", "Enabled All", ""),
                ("disabled_others", "Disabled Others", "")
            ],
            default="enabled_all",
            options={'HIDDEN'}
        )

# --------------------------
# Batch Render Settings
# --------------------------

class CameraRenderSettings(PropertyGroup):
    output_dir: StringProperty(
        name="Output Folder",
        description="Folder to save rendered video files",
        default="//renders/",
        subtype='DIR_PATH'
    )
    shutdown_after: BoolProperty(
        name="Shutdown after rendering",
        description="Shutdown the computer after all renders complete",
        default=False
    )

# --------------------------
# Camera Render Toggle Operator
# --------------------------

class OBJECT_OT_toggle_camera_render(Operator):
    bl_idname = "object.toggle_camera_render"
    bl_label = "Toggle Camera Render"
    bl_description = "Disable non-active cameras / Re-enable all cameras"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        _ensure_state_prop()
        wm = context.window_manager
        scene = context.scene
        active_camera = scene.camera
        all_cameras = get_all_camera_objects()

        if not all_cameras:
            self.report({'WARNING'}, "No camera found in the scene.")
            return {'CANCELLED'}

        if active_camera is None:
            active_camera = all_cameras[0]

        if wm.cam_toggle_last_action != 'disabled_others':
            for cam in all_cameras:
                is_active = (cam == active_camera)
                cam.hide_render = not is_active
                for col in collections_of_object(cam):
                    set_collection_render_enabled(context, col, is_active)
            wm.cam_toggle_last_action = 'disabled_others'
            self.report({'INFO'}, f"📷 Non-active cameras disabled. Active camera: \"{active_camera.name}\"")
        else:
            for cam in all_cameras:
                cam.hide_render = False
                for col in collections_of_object(cam):
                    set_collection_render_enabled(context, col, True)
            wm.cam_toggle_last_action = 'enabled_all'
            self.report({'INFO'}, "✅ All cameras enabled for rendering.")
        return {'FINISHED'}

# --------------------------
# Batch Render Operator
# --------------------------

class OBJECT_OT_batch_render_active_cameras(Operator):
    bl_idname = "object.batch_render_active_cameras"
    bl_label = "Render Cameras (Active Only)"
    bl_description = "Renders only cameras that are enabled for render"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        settings = scene.camera_render_settings
        output_dir = bpy.path.abspath(settings.output_dir)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        render_engine = scene.render.engine
        # Get render engine prefix
        engine_map = {
            "CYCLES": "C",
            "BLENDER_EEVEE_NEXT": "E",
            "BLENDER_EEVEE": "E",
            "BLENDER_WORKBENCH": "W"
        }
        egn = engine_map.get(scene.render.engine, "X")  # 'X' = unknown

        all_cameras = get_all_camera_objects()
        renderable_cameras = get_renderable_cameras()
        skipped_cameras = [cam.name for cam in all_cameras if cam not in renderable_cameras]

        log_path = os.path.join(output_dir, "render_log.txt")
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write(f"Total cameras: {len(all_cameras)}\n")
            if skipped_cameras:
                log_file.write(f"Skipped cameras: {', '.join(skipped_cameras)}\n")
            else:
                log_file.write("No skipped cameras.\n")
            log_file.write(f"Renderable cameras: {len(renderable_cameras)}\n\n")

        for idx, cam in enumerate(renderable_cameras, start=1):
            scene.camera = cam
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            output_path = os.path.join(output_dir, f"{egn}_{cam.name}_{timestamp}")
            scene.render.filepath = output_path

            start_time = time.time()
            start_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.report({'INFO'}, f"[{idx}/{len(renderable_cameras)}] Rendering {cam.name}...")

            with open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"[{idx}/{len(renderable_cameras)}] Started rendering: {cam.name} at {start_str}\n")

            bpy.ops.render.render(animation=True)

            end_time = time.time()
            end_str = datetime.datetime.now().strftime("%H:%M:%S")
            mins, secs = divmod(end_time - start_time, 60)

            with open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"[{idx}/{len(renderable_cameras)}] Finished: {cam.name} at {end_str} ({int(mins)}m {int(secs)}s)\n\n")

        def draw(self, context):
            self.layout.label(text="✅ Rendering complete.")
        bpy.context.window_manager.popup_menu(draw, title="Done", icon='RENDER_RESULT')

        if settings.shutdown_after:
            system = platform.system()
            if system == "Windows":
                os.system("shutdown /s /t 60 /f")
            elif system == "Darwin":
                os.system("sudo shutdown -h +1")
            elif system == "Linux":
                os.system("shutdown -h +1")

        return {'FINISHED'}

# --------------------------
# Panel
# --------------------------

class CAMERA_RENDER_PT_tools_panel(Panel):
    bl_label = "Camera Render Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'C-gy'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.camera_render_settings
        wm = context.window_manager
        state = getattr(wm, "cam_toggle_last_action", "enabled_all")
        label = "Disable Others" if state != "disabled_others" else "Enable All"

        layout.operator("object.toggle_camera_render", icon='RESTRICT_RENDER_OFF', text=label)
        layout.separator()
        layout.prop(settings, "output_dir")
        layout.prop(settings, "shutdown_after")
        layout.operator("object.batch_render_active_cameras", icon='RENDER_ANIMATION')

# --------------------------
# Register
# --------------------------

classes = (
    CameraRenderSettings,
    OBJECT_OT_toggle_camera_render,
    OBJECT_OT_batch_render_active_cameras,
    CAMERA_RENDER_PT_tools_panel,
)

def register():
    _ensure_state_prop()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.camera_render_settings = PointerProperty(type=CameraRenderSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.WindowManager, "cam_toggle_last_action"):
        del bpy.types.WindowManager.cam_toggle_last_action
    del bpy.types.Scene.camera_render_settings

if __name__ == "__main__":
    register()
