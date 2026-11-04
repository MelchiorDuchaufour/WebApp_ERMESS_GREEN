"""Exporte la maquette Blender de la serre Rigerie en .glb pour la webapp 3D.

    blender -b ../plan_rigerie/serre_rigerie_detail.blend --python export_glb.py

Sortie : serre.glb à côté de ce script. Le repère Blender (x le long du mur
haut, y vers le haut du plan, z vertical) est converti en Y-up par glTF ;
la page le reconvertit pour placer les capteurs dans le repère du plan.
"""
from pathlib import Path
import bpy

ICI = Path(__file__).resolve().parent
# ni caméras ni lumières : la page gère son propre éclairage
for ob in list(bpy.data.objects):
    if ob.type in {"CAMERA", "LIGHT"}:
        bpy.data.objects.remove(ob)
cols = {}
for ob in bpy.data.objects:
    c = ob.users_collection[0].name if ob.users_collection else "-"
    cols.setdefault(c, []).append(ob.name)
for c, obs in cols.items():
    print(f"[export] {c}: {len(obs)} objets, ex. {obs[:4]}")
bpy.ops.export_scene.gltf(filepath=str(ICI / "serre.glb"), export_format="GLB",
                          export_apply=True, export_cameras=False, export_lights=False,
                          export_extras=True)
print("[export] ok ->", ICI / "serre.glb")
