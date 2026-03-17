#!/usr/bin/env python3
"""MOTUS-VIGILUS — Frégate U-GAMMA : La Forge — Conversion .npz → .fbx via Blender headless"""

import bpy
import sys
import numpy as np
from mathutils import Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
if len(argv) < 2:
    print("[ERREUR] Usage: blender -b template.blend -P motus_forge.py -- input.npz output.fbx")
    sys.exit(1)

npz_path = argv[0]
fbx_path = argv[1]

print(f"[U-GAMMA] Chargement : {npz_path}")
data = np.load(npz_path, allow_pickle=True)
rotations = data["rotations"]
root_position = data["root_position"]
bone_names = data["bone_names"]
fps = int(data["fps"])
n_frames = len(rotations)
print(f"[U-GAMMA] {n_frames} frames @ {fps} FPS — {len(bone_names)} bones")


def find_bone(armature, name):
    """Find bone by exact name or common variations."""
    pose_bones = armature.pose.bones
    if name in pose_bones:
        return pose_bones[name]
    for pb in pose_bones:
        if pb.name.lower().replace(" ", "").replace("_", "") == name.lower().replace(" ", "").replace("_", ""):
            return pb
    return None


armature = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        armature = obj
        break

if not armature:
    print("[ERREUR] Aucune armature trouvée dans le template")
    sys.exit(1)

print(f"[U-GAMMA] Armature : {armature.name} ({len(armature.pose.bones)} bones)")

bone_map = {}
missing = []
for bname in bone_names:
    pb = find_bone(armature, str(bname))
    if pb:
        bone_map[str(bname)] = pb
    else:
        missing.append(str(bname))

if missing:
    available = [pb.name for pb in armature.pose.bones]
    print(f"[WARN] Bones manquants : {missing}")
    print(f"[WARN] Bones disponibles : {available}")

print(f"[U-GAMMA] {len(bone_map)}/{len(bone_names)} bones mappés")

bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = n_frames
bpy.context.scene.render.fps = fps

bpy.context.view_layer.objects.active = armature
armature.select_set(True)

for frame_idx in range(n_frames):
    bpy.context.scene.frame_set(frame_idx + 1)

    pos = root_position[frame_idx]
    armature.location = Vector((float(pos[0]), float(pos[1]), float(pos[2])))
    armature.keyframe_insert(data_path="location", frame=frame_idx + 1)

    for bone_idx, bone_name in enumerate(bone_names):
        pb = bone_map.get(str(bone_name))
        if pb is None:
            continue
        w, x, y, z = rotations[frame_idx, bone_idx]
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion((float(w), float(x), float(y), float(z)))
        pb.keyframe_insert(data_path="rotation_quaternion", frame=frame_idx + 1)

    if frame_idx % 100 == 0:
        print(f"[U-GAMMA] Frame {frame_idx + 1}/{n_frames}")

print(f"[U-GAMMA] Export FBX → {fbx_path}")
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=False,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False,
    bake_anim_simplify_factor=0.0,
    axis_forward='-Z',
    axis_up='Y',
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
)
print(f"[U-GAMMA] Forge terminée — {fbx_path}")
