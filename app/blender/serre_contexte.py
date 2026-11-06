"""
serre_contexte.py — ESSAI : volumes simplifiés autour de la serre Rigerie.

Serres et bâtiments voisins, sol, arbres. Emplacements relevés à la main sur une vue
aérienne (capture du 06/11/2026), calée sur le plan par trois coins de la serre : précision
de l'ordre du mètre. Hauteurs, pentes et nombres de nefs des voisins : estimés, non mesurés.
L'image elle-même n'est pas reprise dans la maquette.

Tous les objets commencent par « voisin_ » : la page 3D les affiche et les masque ensemble.

    blender -b serre_rigerie_detail.blend --python serre_contexte.py
"""
import math
from pathlib import Path

import bmesh
import bpy

ICI = Path(__file__).resolve().parent

# --- calage image -> plan : coins NO, NE, SE de la serre Rigerie ------------------------
NO, NE, SE = (525.0, 205.0), (985.0, 270.0), (895.0, 845.0)
LARGEUR, HAUTEUR = 29.5, 35.5
UX = ((NE[0] - NO[0]) / LARGEUR, (NE[1] - NO[1]) / LARGEUR)      # px par m selon x
DY = ((SE[0] - NE[0]) / HAUTEUR, (SE[1] - NE[1]) / HAUTEUR)      # px par m selon -y
DET = UX[0] * DY[1] - UX[1] * DY[0]
ECHELLE = math.hypot(*UX)


def plan(px):
    """Pixel de la vue aérienne -> (x, y) du plan de la serre."""
    a, b = px[0] - NO[0], px[1] - NO[1]
    x = (a * DY[1] - b * DY[0]) / DET
    h = (UX[0] * b - UX[1] * a) / DET
    return (x, HAUTEUR - h)


def materiau(nom, couleur, rugosite=0.8):
    m = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
    m.use_nodes = True
    h = couleur.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    rgb = [((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92 for c in srgb]
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rugosite
    m.diffuse_color = (*rgb, 1.0)
    return m


COLL = bpy.data.collections.get("Voisins") or bpy.data.collections.new("Voisins")
if COLL.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(COLL)
for ob in list(COLL.objects):
    bpy.data.objects.remove(ob)


def objet(nom, bm, mat):
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new(nom)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(nom, me)
    COLL.objects.link(ob)
    return ob


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def serre(nom, coins_px, nefs, z_chenau, pente_deg, couleur, lignes="#3c464d"):
    """Quadrilatère a, b, c, d : faîtages parallèles à a->b, nefs réparties de a vers d."""
    a, b, c, d = [plan(p) for p in coins_px]
    larg = math.hypot(d[0] - a[0], d[1] - a[1]) / nefs
    dz = (larg / 2) * math.tan(math.radians(pente_deg))
    n = 2 * nefs
    z = [z_chenau + (dz if j % 2 else 0.0) for j in range(n + 1)]
    bm = bmesh.new()
    p0 = [lerp(a, d, j / n) for j in range(n + 1)]       # pignon côté a-d
    p1 = [lerp(b, c, j / n) for j in range(n + 1)]       # pignon côté b-c
    v0 = [bm.verts.new((*p, h)) for p, h in zip(p0, z)]
    v1 = [bm.verts.new((*p, h)) for p, h in zip(p1, z)]
    for j in range(n):
        bm.faces.new((v0[j], v1[j], v1[j + 1], v0[j + 1]))
    b0 = [bm.verts.new((*p0[j], 0.0)) for j in (0, n)]
    b1 = [bm.verts.new((*p1[j], 0.0)) for j in (0, n)]
    bm.faces.new((b0[0], b0[1], *reversed(v0)))          # pignons
    bm.faces.new((b1[0], b1[1], *reversed(v1)))
    bm.faces.new((b0[0], b1[0], v1[0], v0[0]))           # longs pans
    bm.faces.new((b0[1], b1[1], v1[n], v0[n]))
    objet(f"voisin_{nom}", bm, materiau(f"voisin_{nom}", couleur, 0.45))
    # faîtages et chéneaux : bandes sombres, pour que les nefs se lisent
    bm = bmesh.new()
    ux, uy = p1[0][0] - p0[0][0], p1[0][1] - p0[0][1]
    lg = math.hypot(ux, uy)
    nx, ny = -uy / lg * 0.09, ux / lg * 0.09
    for j in range(n + 1):
        h = z[j] + 0.03
        q = [(p0[j][0] - nx, p0[j][1] - ny), (p1[j][0] - nx, p1[j][1] - ny),
             (p1[j][0] + nx, p1[j][1] + ny), (p0[j][0] + nx, p0[j][1] + ny)]
        bm.faces.new([bm.verts.new((*p, h)) for p in q])
    objet(f"voisin_{nom}_lignes", bm, materiau("voisin_lignes", lignes))


def sol(nom, pts_px, couleur):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((*plan(p), 0.02)) for p in pts_px])
    objet(f"voisin_sol_{nom}", bm, materiau(f"voisin_sol_{nom}", couleur, 1.0))


def arbres(liste):
    bm = bmesh.new()
    for cx, cy, r_px in liste:
        x, y = plan((cx, cy))
        r = r_px / ECHELLE
        m = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        bmesh.ops.scale(bm, vec=(r, r, r * 1.25), verts=m["verts"])
        bmesh.ops.translate(bm, vec=(x, y, r * 1.25 + 1.5), verts=m["verts"])
    objet("voisin_arbres", bm, materiau("voisin_arbres", "#3f6b3a", 1.0))


# --- sol ---------------------------------------------------------------------------------
sol("cour", [(0, 250), (360, 290), (440, 300), (440, 390), (190, 480), (180, 625), (240, 880), (60, 400), (0, 300)], "#c9bda3")
sol("route", [(0, 300), (60, 400), (240, 880), (280, 1081), (0, 1081)], "#8d8d8a")
sol("parking", [(895, 850), (1345, 940), (1500, 760), (1500, 1081), (880, 1081)], "#77797a")
sol("herbe_nord", [(560, 40), (1500, 190), (1460, 280), (1118, 215), (1003, 190), (600, 148)], "#7f8f58")
sol("herbe_est", [(1460, 280), (1500, 190), (1500, 760), (1385, 830)], "#7f8f58")
sol("massifs", [(510, 795), (895, 850), (880, 1081), (280, 1081), (280, 875), (420, 815)], "#55683f")

# --- bâtiments et serres (coins a, b, c, d) ---------------------------------------------
serre("serre_est", [(1010, 870), (1345, 930), (1460, 278), (1118, 222)], 7, 3.0, 23, "#7f94a8")   # chéneau 1 m sous celui de Rigerie (4,00 m)
serre("galerie", [(895, 842), (1003, 197), (1118, 210), (1005, 862)], 2, 6.1, 10, "#e4e7e8")   # un peu plus haute que Rigerie (faîtage 5,88 m)
serre("serre_nord_ouest", [(0, 225), (30, 0), (400, 0), (360, 285)], 4, 3.2, 23, "#9db2c4")
serre("petite_serre", [(182, 625), (420, 540), (510, 780), (280, 870)], 3, 3.0, 23, "#ccd6dc")
serre("batiment_nord", [(600, 150), (980, 208), (973, 272), (595, 205)], 1, 5.5, 35, "#4c4f54", "#2c2e31")
serre("batiment_magasin", [(190, 480), (440, 390), (465, 480), (245, 595)], 1, 3.5, 30, "#a8553f", "#6d3627")

# --- végétation --------------------------------------------------------------------------
arbres([(45, 740, 42), (95, 880, 48), (25, 810, 30), (190, 700, 28), (1400, 870, 48),
        (560, 980, 38), (700, 1020, 50), (640, 900, 26), (760, 890, 28), (830, 960, 24),
        (480, 870, 22), (340, 550, 22)])

bpy.ops.wm.save_as_mainfile(filepath=str(ICI / "serre_rigerie_detail.blend"))
print(f"[contexte] {len(COLL.objects)} objets · échelle {ECHELLE:.1f} px/m · "
      f"contrôle pan coupé (453,610) -> {plan((453, 610))}, (510,785) -> {plan((510, 785))}")
