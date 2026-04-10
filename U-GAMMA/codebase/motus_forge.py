#!/usr/bin/env python3
"""MOTUS-VIGILUS — Frégate U-GAMMA : La Forge — v4 FIX AXIS
Conversion .npz → .fbx via Blender headless

DIAGNOSTIC v4 — Bug racine identifié :
  U-ALPHA produit des rotations MONDE dans un espace où X = gauche du personnage
  (axis_map: [-mp_x, mp_y, -mp_z]).
  Le template Blender R15 a le squelette MIROIR : LeftUpperArm pointe vers +X
  (droite dans Blender) alors que U-ALPHA attend -X.

  → Toutes les rotations bras/jambes sont appliquées dans le mauvais sens X.
  → Résultat : atomes volants, bras inversés.

FIX v4 :
  1. Correction de l'axe X : flip_x_quat(Q) = (w, x, -y, -z)
     appliqué à toutes les world_q AVANT la conversion world→local.
  2. root_position.x negated (même flip).
  3. root_position = delta depuis frame 0 (centrage sur l'origine).
  4. Keyframe de repos à frame 0 (identity) pour éviter la T-pose fantôme dans Roblox.
"""

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

print(f"[U-GAMMA v4] Chargement : {npz_path}")
data = np.load(npz_path, allow_pickle=True)
rotations     = data["rotations"]
root_position = data["root_position"]
bone_names    = data["bone_names"]
fps           = int(data["fps"])
n_frames      = len(rotations)
print(f"[U-GAMMA v4] {n_frames} frames @ {fps} FPS — {len(bone_names)} bones")

# ── Hiérarchie parent .npz ───────────────────────────────────────────────────
NPZ_PARENT = {
    'LowerTorso':    None,
    'UpperTorso':    'LowerTorso',
    'Head':          'UpperTorso',
    'LeftUpperArm':  'UpperTorso',
    'LeftLowerArm':  'LeftUpperArm',
    'LeftHand':      'LeftLowerArm',
    'RightUpperArm': 'UpperTorso',
    'RightLowerArm': 'RightUpperArm',
    'RightHand':     'RightLowerArm',
    'LeftUpperLeg':  'LowerTorso',
    'LeftLowerLeg':  'LeftUpperLeg',
    'LeftFoot':      'LeftLowerLeg',
    'RightUpperLeg': 'LowerTorso',
    'RightLowerLeg': 'RightUpperLeg',
    'RightFoot':     'RightLowerLeg',
}


def flip_x_quat(q):
    """Transforme un quaternion de l'espace U-ALPHA (X=gauche) vers l'espace
    Blender template (X=droite) via flip_X : M=diag(-1,1,1).
    Formule : Q_blender = (w, x, -y, -z).
    """
    return Quaternion((q.w, q.x, -q.y, -q.z))


def find_bone(armature, name):
    pose_bones = armature.pose.bones
    if name in pose_bones:
        return pose_bones[name]
    norm = name.lower().replace(" ", "").replace("_", "")
    for pb in pose_bones:
        if pb.name.lower().replace(" ", "").replace("_", "") == norm:
            return pb
    return None


# ── Armature ─────────────────────────────────────────────────────────────────
armature = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        armature = obj
        break

if not armature:
    print("[ERREUR] Aucune armature trouvée dans le template")
    sys.exit(1)

print(f"[U-GAMMA v4] Armature : {armature.name} ({len(armature.pose.bones)} bones)")

armature.location = Vector((0.0, 0.0, 0.0))
armature.rotation_euler = (0.0, 0.0, 0.0)
armature.scale = (1.0, 1.0, 1.0)

# ── Mapping bones ─────────────────────────────────────────────────────────────
bone_map = {}
missing  = []
for bname in bone_names:
    pb = find_bone(armature, str(bname))
    if pb:
        bone_map[str(bname)] = pb
    else:
        missing.append(str(bname))

if missing:
    print(f"[WARN] Bones manquants : {missing}")
print(f"[U-GAMMA v4] {len(bone_map)}/{len(bone_names)} bones mappés")

# ── Root bone pour root_position ─────────────────────────────────────────────
ROOT_CANDIDATES = ["HumanoidRootNode", "Root", "root", "HumanoidRootPart",
                   "Hips", "hips", "Pelvis", "LowerTorso"]
root_bone = None
for c in ROOT_CANDIDATES:
    root_bone = find_bone(armature, c)
    if root_bone:
        print(f"[U-GAMMA v4] Root bone : {root_bone.name}")
        break

# ── Baseline position (frame 0) pour root delta ──────────────────────────────
# On soustrait la position initiale afin que le personnage parte de l'origine.
root_pos_baseline = root_position[0].copy()
print(f"[U-GAMMA v4] root_pos_baseline (frame 0) = {root_pos_baseline}")

# ── Paramètres de scène ───────────────────────────────────────────────────────
# On démarre à frame 0 (pose de repos) + frames 1..n
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end   = n_frames
bpy.context.scene.render.fps  = fps

bpy.context.view_layer.objects.active = armature
armature.select_set(True)

bone_name_list = [str(b) for b in bone_names]
bone_idx_map   = {n: i for i, n in enumerate(bone_name_list)}


def bake_rest_pose_frame(frame):
    """Insère des keyframes identity (pose de repos) à la frame donnée."""
    bpy.context.scene.frame_set(frame)
    if root_bone is not None:
        root_bone.location = Vector((0.0, 0.0, 0.0))
        root_bone.keyframe_insert(data_path="location", frame=frame)
    for bname in bone_name_list:
        pb = bone_map.get(bname)
        if pb is None:
            continue
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
        pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)


# ── Frame 0 : pose de repos (évite la T-pose fantôme dans Roblox) ─────────────
bake_rest_pose_frame(0)
print("[U-GAMMA v4] Frame 0 — pose de repos injectée")

# ── Boucle principale ──────────────────────────────────────────────────────────
for frame_idx in range(n_frames):
    blender_frame = frame_idx + 1          # frames Blender 1..n
    bpy.context.scene.frame_set(blender_frame)

    # root_position → root bone (delta, X négué pour corriger le flip)
    if root_bone is not None:
        pos   = root_position[frame_idx]
        delta = pos - root_pos_baseline
        # X flip : U-ALPHA X = gauche → Blender X = droite
        root_bone.location = Vector((-float(delta[0]),
                                      float(delta[1]),
                                      float(delta[2])))
        root_bone.keyframe_insert(data_path="location", frame=blender_frame)

    # ── Rotations monde (espace U-ALPHA) → corrigées → locales ────────────────
    # Étape 1 : charger les quaternions bruts depuis le .npz
    world_quats_raw = {}
    for bname in bone_name_list:
        idx = bone_idx_map[bname]
        w, x, y, z = rotations[frame_idx, idx]
        world_quats_raw[bname] = Quaternion((float(w), float(x), float(y), float(z)))

    # Étape 2 : corriger l'espace X (flip_X → Blender armature space)
    world_quats = {bname: flip_x_quat(q) for bname, q in world_quats_raw.items()}

    # Étape 3 : world → local  (local_i = inv(world_parent_i) @ world_i)
    for bname in bone_name_list:
        pb = bone_map.get(bname)
        if pb is None:
            continue

        world_q  = world_quats[bname]
        parent_n = NPZ_PARENT.get(bname)

        if parent_n and parent_n in world_quats:
            local_q = world_quats[parent_n].inverted() @ world_q
        else:
            local_q = world_q

        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = local_q
        pb.keyframe_insert(data_path="rotation_quaternion", frame=blender_frame)

    if frame_idx % 100 == 0:
        print(f"[U-GAMMA v4] Frame {blender_frame}/{n_frames}")

# ── Export FBX ────────────────────────────────────────────────────────────────
print(f"[U-GAMMA v4] Export FBX → {fbx_path}")
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=False,
    object_types={'ARMATURE', 'MESH'},
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
    bake_space_transform=False,
)
print(f"[U-GAMMA v4] Forge terminée — {fbx_path}")
