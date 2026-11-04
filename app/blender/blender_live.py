"""
blender_live.py — Serre Rigerie en direct dans Blender (première version, locale).

Anime dans la maquette :
  * les écrans thermiques (un par nef, déploiement 0 = replié, 1 = fermé),
  * les ouvrants de faîtage (angle d'ouverture, charnière sur le faîtage),
  * le chauffage (couleur des tubes verts chauds, 0 = arrêt, 1 = plein),
  * les capteurs Sigrow (sphères colorées par la variable choisie).

Sources :
  * capteurs   : serveur local de la webapp  GET /api/latest et /api/capteurs
  * actionneurs: GET /api/actionneurs (fichier actionneurs_bocage.json, réglé
                 depuis l'onglet « Contrôle » de la webapp, ou à la main ici)
  Mode « Manuel » : les curseurs du panneau pilotent directement la scène.

Lancer (serveur de la webapp démarré sur le port 8766) :
    blender blender/serre_rigerie_detail.blend --python blender/blender_live.py
Panneau : vue 3D > barre latérale (N) > onglet « Serre live ».
"""
from __future__ import annotations

import json
import math
import sys
import urllib.request
from pathlib import Path

import bmesh
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_rigerie as pr  # noqa: E402

N_NEFS = 3
L_NEFS = pr.H_DROIT / N_NEFS          # faîtages parallèles à x : nefs empilées en y
Z_ECRAN = 3.92                        # juste sous le chéneau (4,00 m)
Y_FAITAGES = [(i + 0.5) * L_NEFS for i in range(N_NEFS)]
Z_FAITAGE = 4.0 + (L_NEFS / 2) * math.tan(math.radians(23.0))
ANGLE_MAX = 45.0                      # ouverture maximale des ouvrants (°)
VIRIDIS = ["#440154", "#46327e", "#365c8d", "#277f8e", "#1fa187", "#4ac16d", "#a0da39", "#fde725"]


# ------------------------------------------------------------------ outils
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lin(c):  # sRGB -> linéaire
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


def couleur(t):
    t = min(1.0, max(0.0, t))
    s = t * (len(VIRIDIS) - 1)
    i = min(len(VIRIDIS) - 2, int(s))
    a, b = hex_rgb(VIRIDIS[i]), hex_rgb(VIRIDIS[i + 1])
    return lin(tuple(a[k] + (b[k] - a[k]) * (s - i) for k in range(3))) + (1.0,)


def collection(nom):
    c = bpy.data.collections.get(nom)
    if c is None:
        c = bpy.data.collections.new(nom)
        bpy.context.scene.collection.children.link(c)
    return c


def materiau(nom, rgba, alpha=1.0, emission=0.0):
    m = bpy.data.materials.get(nom) or bpy.data.materials.new(nom)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Alpha"].default_value = alpha
    for k in ("Emission Color", "Emission"):
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = rgba
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission
    if alpha < 1:
        m.blend_method = "BLEND" if hasattr(m, "blend_method") else m.blend_method
    m.diffuse_color = rgba[:3] + (alpha,)        # affichage en mode « Solid »
    return m


def get_json(url, timeout=8):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def clip_poly(poly, x0, x1, y0, y1):
    """Sutherland–Hodgman : polygone (éventuellement concave) ∩ rectangle."""
    def clip(pts, dedans, inter):
        out = []
        for i, p in enumerate(pts):
            q = pts[i - 1]
            if dedans(p):
                if not dedans(q):
                    out.append(inter(q, p))
                out.append(p)
            elif dedans(q):
                out.append(inter(q, p))
        return out

    def ix(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))

    def iy(yc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / (b[1] - a[1]), yc)
    pts = list(poly)
    for dedans, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                          (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if not pts:
            break
        pts = clip(pts, dedans, inter)
    return pts


# ------------------------------------------------------------------ construction
def construire():
    live = collection("Live")
    poly = pr.enveloppe()
    xs = [p[0] for p in poly]
    # écrans : un objet par nef, maillage refait à chaque mise à jour
    m_ecran = materiau("ecran_thermique", (0.93, 0.90, 0.80, 1.0), alpha=0.85)
    for i in range(N_NEFS):
        nom = f"ecran_nef{i + 1}"
        if nom not in bpy.data.objects:
            me = bpy.data.meshes.new(nom)
            ob = bpy.data.objects.new(nom, me)
            ob.data.materials.append(m_ecran)
            live.objects.link(ob)
        bpy.data.objects[nom]["xlim"] = (min(xs), max(xs))
    # ouvrants : une pièce par ouvrant, charnière sur le faîtage
    src = bpy.data.objects.get("ouvrants_faitage")
    if src and "ouvrant_000" not in bpy.data.objects:
        bm = bmesh.new()
        bm.from_mesh(src.data)
        bm.verts.ensure_lookup_table()
        vu, parts = set(), []
        for v in bm.verts:
            if v.index in vu:
                continue
            pile, comp = [v], []
            while pile:
                a = pile.pop()
                if a.index in vu:
                    continue
                vu.add(a.index)
                comp.append(a.index)
                pile += [e.other_vert(a) for e in a.link_edges]
            parts.append(comp)
        m_ouv = src.active_material
        for k, comp in enumerate(parts):
            cos = [src.matrix_world @ bm.verts[i].co for i in comp]
            ymin, ymax = min(c.y for c in cos), max(c.y for c in cos)
            yf = min(Y_FAITAGES, key=lambda y: abs(y - (ymin + ymax) / 2))
            cote = 1 if (ymin + ymax) / 2 > yf else -1      # pan côté +y ou -y
            charniere = (sum(c.x for c in cos) / len(cos), yf, Z_FAITAGE)
            nb = bmesh.new()
            idx = {}
            for i in comp:
                c = src.matrix_world @ bm.verts[i].co
                idx[i] = nb.verts.new((c.x - charniere[0], c.y - charniere[1], c.z - charniere[2]))
            for f in bm.faces:
                if all(v.index in idx for v in f.verts):
                    try:
                        nb.faces.new([idx[v.index] for v in f.verts])
                    except ValueError:
                        pass
            me = bpy.data.meshes.new(f"ouvrant_{k:03d}")
            nb.to_mesh(me)
            ob = bpy.data.objects.new(f"ouvrant_{k:03d}", me)
            ob.location = charniere
            ob["cote"] = cote
            if m_ouv:
                ob.data.materials.append(m_ouv)
            live.objects.link(ob)
        src.hide_viewport = src.hide_render = True
    # chauffage : matériau dédié sur les tubes chauds
    tubes = bpy.data.objects.get("tubes_verts_chauds")
    if tubes:
        m = materiau("chauffage_live", (0.09, 0.24, 0.14, 1.0))
        if tubes.data.materials:
            tubes.data.materials[0] = m
        else:
            tubes.data.materials.append(m)


def maj_ecran(i, f):
    ob = bpy.data.objects.get(f"ecran_nef{i + 1}")
    if not ob:
        return
    f = min(1.0, max(0.0, f))
    x0, x1 = ob["xlim"]
    y0 = i * L_NEFS
    # écran tiré depuis le chéneau bas de la nef ; replié = bande de 0,15 m
    larg = max(0.15, f * L_NEFS)
    pts = clip_poly(pr.enveloppe(), x0, x1, y0, y0 + larg)
    bm = bmesh.new()
    if len(pts) >= 3:
        bm.faces.new([bm.verts.new((x, y, Z_ECRAN)) for x, y in pts])
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def maj_ouvrants(angle_deg):
    a = math.radians(min(ANGLE_MAX, max(0.0, angle_deg)))
    for ob in bpy.data.objects:
        if ob.name.startswith("ouvrant_"):
            ob.rotation_euler = (ob["cote"] * a, 0.0, 0.0)


def maj_chauffage(p):
    m = bpy.data.materials.get("chauffage_live")
    if not m:
        return
    p = min(1.0, max(0.0, p))
    froid, chaud = (0.09, 0.24, 0.14), (0.85, 0.12, 0.05)
    c = tuple(froid[k] + (chaud[k] - froid[k]) * p for k in range(3)) + (1.0,)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = c
    for k in ("Emission Color", "Emission"):
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = c
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 2.0 * p
    m.diffuse_color = c


def maj_capteurs(positions, latest, var):
    live = collection("Live_capteurs")
    vals = {}
    for rid, r in latest.get("remotes", {}).items():
        v = (r.get("values") or {}).get(var)
        if v is not None:
            vals[rid] = v
    lo, hi = (min(vals.values()), max(vals.values())) if vals else (0, 1)
    if hi - lo < 1e-6:
        hi = lo + 1
    for rid, p in positions.get("capteurs", {}).items():
        nom = f"capteur_{rid}"
        ob = bpy.data.objects.get(nom)
        if ob is None:
            me = bpy.data.meshes.new(nom)
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.25)
            bm.to_mesh(me)
            ob = bpy.data.objects.new(nom, me)
            ob.data.materials.append(materiau(f"mat_{nom}", (0.6, 0.6, 0.6, 1)))
            live.objects.link(ob)
        ob.location = (p["x"], p["y"], p["z"])
        v = vals.get(rid)
        c = couleur((v - lo) / (hi - lo)) if v is not None else (0.5, 0.5, 0.5, 1.0)
        m = ob.active_material
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = c
        m.diffuse_color = c
        ob["valeur"] = -999.0 if v is None else v
        ob["nom_sigrow"] = latest.get("remotes", {}).get(rid, {}).get("name", "")
    return lo, hi, len(vals)


# ------------------------------------------------------------------ état et minuterie
def _maj(self, ctx):
    if self.mode == "MANUEL":
        appliquer(self)


class EtatLive(bpy.types.PropertyGroup):
    serveur: bpy.props.StringProperty(name="Serveur", default="http://localhost:8766")
    site: bpy.props.StringProperty(name="Site", default="bocage")
    mode: bpy.props.EnumProperty(name="Actionneurs", items=[
        ("SERVEUR", "Serveur", "Lit /api/actionneurs (onglet Contrôle de la webapp)"),
        ("MANUEL", "Manuel", "Les curseurs ci-dessous pilotent la scène")], default="SERVEUR")
    variable: bpy.props.EnumProperty(name="Capteurs", items=[
        ("temp", "T° air", ""), ("humid", "HR", ""), ("vpd", "VPD", ""), ("par", "PAR", ""),
        ("pixel_object1_temp", "T° feuille", ""), ("soil_temp", "T° sol", ""), ("co2", "CO₂", "")], default="temp")
    periode: bpy.props.IntProperty(name="Rafraîchir (s)", default=30, min=5, max=600)
    ecran1: bpy.props.FloatProperty(update=_maj, name="Écran nef 1", min=0, max=1, default=0, subtype="FACTOR")
    ecran2: bpy.props.FloatProperty(update=_maj, name="Écran nef 2", min=0, max=1, default=0, subtype="FACTOR")
    ecran3: bpy.props.FloatProperty(update=_maj, name="Écran nef 3", min=0, max=1, default=0, subtype="FACTOR")
    ouvrants: bpy.props.FloatProperty(update=_maj, name="Ouvrants (°)", min=0, max=ANGLE_MAX, default=0)
    chauffage: bpy.props.FloatProperty(update=_maj, name="Chauffage", min=0, max=1, default=0, subtype="FACTOR")
    statut: bpy.props.StringProperty(default="")
    actif: bpy.props.BoolProperty(default=False)


def appliquer(e):
    for i, f in enumerate((e.ecran1, e.ecran2, e.ecran3)):
        maj_ecran(i, f)
    maj_ouvrants(e.ouvrants)
    maj_chauffage(e.chauffage)


def rafraichir():
    e = bpy.context.scene.serre_live
    base = e.serveur.rstrip("/")
    msgs = []
    try:
        lat = get_json(f"{base}/api/latest?site={e.site}")
        pos = get_json(f"{base}/api/capteurs?site={e.site}")
        lo, hi, n = maj_capteurs(pos, lat, e.variable)
        msgs.append(f"{n} capteurs · {e.variable} {lo:.1f}–{hi:.1f} · {lat.get('updated', '')[11:16]}")
    except Exception as err:
        msgs.append(f"capteurs : {err}")
    if e.mode == "SERVEUR":
        try:
            act = get_json(f"{base}/api/actionneurs?site={e.site}")
            ec = act.get("ecrans", [0] * N_NEFS)
            e.ecran1, e.ecran2, e.ecran3 = (list(ec) + [0, 0, 0])[:3]
            e.ouvrants = act.get("ouvrants_deg", 0)
            e.chauffage = act.get("chauffage", 0)
            msgs.append(f"actionneurs ({act.get('source', '?')}, {act.get('maj', '?')})")
        except Exception as err:
            msgs.append(f"actionneurs : {err}")
    appliquer(e)
    e.statut = " · ".join(msgs)
    return e.periode if e.actif else None


class SERRE_OT_demarrer(bpy.types.Operator):
    bl_idname = "serre.demarrer"
    bl_label = "Démarrer le direct"

    def execute(self, ctx):
        e = ctx.scene.serre_live
        construire()
        e.actif = True
        if not bpy.app.timers.is_registered(rafraichir):
            bpy.app.timers.register(rafraichir, first_interval=0.1)
        return {"FINISHED"}


class SERRE_OT_arreter(bpy.types.Operator):
    bl_idname = "serre.arreter"
    bl_label = "Arrêter"

    def execute(self, ctx):
        ctx.scene.serre_live.actif = False
        return {"FINISHED"}


class SERRE_OT_appliquer(bpy.types.Operator):
    bl_idname = "serre.appliquer"
    bl_label = "Appliquer les curseurs"

    def execute(self, ctx):
        construire()
        appliquer(ctx.scene.serre_live)
        return {"FINISHED"}


class SERRE_PT_live(bpy.types.Panel):
    bl_label = "Serre Rigerie · direct"
    bl_space_type, bl_region_type, bl_category = "VIEW_3D", "UI", "Serre live"

    def draw(self, ctx):
        e, l = ctx.scene.serre_live, self.layout
        l.prop(e, "serveur"); l.prop(e, "site"); l.prop(e, "variable"); l.prop(e, "periode")
        l.prop(e, "mode", expand=True)
        col = l.column(align=True)
        col.enabled = e.mode == "MANUEL"
        for k in ("ecran1", "ecran2", "ecran3", "ouvrants", "chauffage"):
            col.prop(e, k)
        if e.mode == "MANUEL":
            l.operator("serre.appliquer")
        row = l.row()
        row.operator("serre.demarrer", icon="PLAY")
        row.operator("serre.arreter", icon="PAUSE")
        for ligne in (e.statut or "arrêté").split(" · "):
            l.label(text=ligne)


CLASSES = (EtatLive, SERRE_OT_demarrer, SERRE_OT_arreter, SERRE_OT_appliquer, SERRE_PT_live)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.serre_live = bpy.props.PointerProperty(type=EtatLive)


if __name__ == "__main__":
    register()
    construire()
    if bpy.app.background:              # test sans interface : un passage puis rendu
        e = bpy.context.scene.serre_live
        e.actif = False
        rafraichir()
