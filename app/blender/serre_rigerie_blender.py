"""
serre_rigerie_blender.py — Maquette 3D de départ de la Serre Rigerie (Blender).

Reprend EXACTEMENT la géométrie au sol de plan_rigerie.py (enveloppe du plan
2012, 41 tablettes) et ajoute la troisième dimension :
  - tablettes : plateau à 0,80 m (donné 22/09/2026), pieds 5 × 5 cm ;
  - toiture à TRIPLE FAÎTAGE (donné) : 3 nefs égales, faîtages parallèles au
    mur haut (29,50 m), nefs de 11,83 m. Nombre et sens : dans plan_rigerie.py ;
  - hauteur de chéneau et pente : HYPOTHÈSES reprises de la config « Rigerie »
    grande-feuille de GreenhousesJL (chéneau 4 m, pente 23°) ;
  - réseau eau chaude / froide (photos bocage/rigerie_circu_eau/) : tubes verts
    à 1,50 m (chaud) et 1,35 m (froid), une paire le long du mur haut (rang 1) et
    deux paires entre les rangs 2 et 3 ; par tablette, un circuit en flexible noir :
    départ sur le tube chaud, 12 longueurs (6 allers-retours) sous le plateau sur
    toute la largeur, retour dans le tube froid (pr.CIRCUIT, retours du 22/09) ; tubes
    accrochés par chaînes aux poteaux de façade (IMG_5710) et à des poteaux
    centraux (IMG_5711). Tracé des flexibles et pas des poteaux : schématiques.

Crée un .blend NEUF (plan_rigerie/serre_rigerie.blend) et deux rendus de contrôle.
Ne modifie aucun autre fichier Blender.

    blender -b --factory-startup --python serre_rigerie_blender.py            # .blend seul
    blender -b --factory-startup --python serre_rigerie_blender.py -- --render
    blender -b --factory-startup --python serre_rigerie_blender.py -- --render dessus   # une seule vue

Repère identique au plan : x le long du mur haut, y vers le haut du plan, z vertical.
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import plan_rigerie as pr  # noqa: E402  (géométrie au sol, sans matplotlib)

# --- 3D : donné -------------------------------------------------------------------
Z_TABLETTE = 0.80            # dessus du plateau
N_NEFS, FAITAGE_AXE = pr.N_NEFS, pr.FAITAGE_AXE   # toiture, définie avec le plan 2D
portee = pr.portee

# --- 3D : HYPOTHÈSES (à mesurer : chéneau, faîtage) ----------------------------------
H_CHENEAU = 4.00             # m
PENTE_DEG = 23.0             # pente de toiture
EP_PLATEAU = 0.04
PIED = 0.05                  # section des pieds
PAS_PIEDS = 2.5              # espacement max des pieds le long d'une tablette
R_TUBE = 0.028               # tubes verts, Ø ≈ 55 mm (photos)
R_FLEX = 0.010               # flexibles caoutchouc noirs, Ø ≈ 20 mm
Z_FLEX_CHAUD, Z_FLEX_FROID = 0.71, 0.68   # sous le plateau (0,76 m) ; 2 niveaux : pas de croisement
N_PASSES = 12                # longueurs de flexible sous une tablette = 6 allers-retours
                             # (compté par l'user sur place, 22/09) ; si impair, +1 retour
# versions précédentes : 1 aller-retour par flexible (Z_FLEX = 0.70), puis 3 passes

OUT = ICI / "plan_rigerie"


# --- utilitaires maillage ------------------------------------------------------------
def boite(bm, x0, x1, y0, y1, z0, z1):
    v = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        bm.faces.new([v[i] for i in f])


def prisme(bm, profil, axe, a0, a1):
    """Extrude un profil fermé (u, z) le long de l'axe `axe` entre a0 et a1."""
    def p3(u, z, a):
        return (u, a, z) if axe == "y" else (a, u, z)
    n = len(profil)
    v0 = [bm.verts.new(p3(u, z, a0)) for u, z in profil]
    v1 = [bm.verts.new(p3(u, z, a1)) for u, z in profil]
    bm.faces.new(v0[::-1])
    bm.faces.new(v1)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((v0[i], v0[j], v1[j], v1[i]))


def objet(nom, bm, coll, mat=None):
    me = bpy.data.meshes.new(nom)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(nom, me)
    coll.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


def collection(nom):
    c = bpy.data.collections.new(nom)
    bpy.context.scene.collection.children.link(c)
    return c


def materiau(nom, rgb, rough=0.6, metal=0.0, alpha=1.0):
    m = bpy.data.materials.new(nom)
    m.diffuse_color = (*rgb, alpha)                     # couleur en vue Solide
    nt = m.node_tree if m.node_tree else None
    if nt is None:
        m.use_nodes = True
        nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m


def materiau_verre():
    """Verre mince : transparent + reflet, sans réfraction (volume fermé de 30 m)."""
    m = bpy.data.materials.new("verre")
    m.diffuse_color = (0.80, 0.90, 1.00, 0.15)
    if m.node_tree is None:
        m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.05
    tr.inputs["Color"].default_value = (0.90, 0.95, 0.97, 1.0)
    mix.inputs["Fac"].default_value = 0.2
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(m, attr, val)
        except (AttributeError, TypeError):
            pass
    return m


def tube(nom, chemins, rayon, coll, mat):
    """Un objet courbe (section ronde) regroupant plusieurs polylignes 3D."""
    cu = bpy.data.curves.new(nom, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = rayon
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    for pts in chemins:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for pt, (x, y, z) in zip(sp.points, pts):
            pt.co = (x, y, z, 1.0)
    ob = bpy.data.objects.new(nom, cu)
    coll.objects.link(ob)
    cu.materials.append(mat)
    return ob


# --- géométrie 3D ----------------------------------------------------------------------
def profil_toit():
    """Profil (u, z) des N nefs, u = coordonnée transverse aux faîtages."""
    L = pr.LARGEUR if FAITAGE_AXE == "y" else pr.H_DROIT
    w = L / N_NEFS
    h_f = H_CHENEAU + (w / 2) * math.tan(math.radians(PENTE_DEG))
    # les deux pans extérieurs sont prolongés de 0,5 m au-delà des murs pour que
    # la coupe booléenne tombe pile à H_CHENEAU sur le mur
    z_ext = H_CHENEAU - 0.5 * math.tan(math.radians(PENTE_DEG))
    pts = [(-0.5, -1.0), (-0.5, z_ext)]
    for i in range(N_NEFS):
        pts.append((i * w + w / 2, h_f))
        if i < N_NEFS - 1:
            pts.append(((i + 1) * w, H_CHENEAU))
    pts += [(L + 0.5, z_ext), (L + 0.5, -1.0)]
    return pts, w, h_f


def enveloppe_verre(poly, coll, mat):
    """Volume = (emprise extrudée) ∩ (prisme de toiture), sans face au sol."""
    bm = bmesh.new()
    vb = [bm.verts.new((x, y, 0.0)) for x, y in poly]
    vh = [bm.verts.new((x, y, 12.0)) for x, y in poly]
    bm.faces.new(vb[::-1])
    bm.faces.new(vh)
    for i in range(len(poly)):
        j = (i + 1) % len(poly)
        bm.faces.new((vb[i], vb[j], vh[j], vh[i]))
    env = objet("enveloppe_verre", bm, coll, mat)

    prof, _, _ = profil_toit()
    a1 = pr.H_DROIT + 1 if FAITAGE_AXE == "y" else pr.LARGEUR + 1
    bm = bmesh.new()
    prisme(bm, prof, FAITAGE_AXE, -1.0, a1)
    toit = objet("_prisme_toit", bm, coll)

    mod = env.modifiers.new("coupe_toit", "BOOLEAN")
    mod.operation = "INTERSECT"
    mod.object = toit
    try:
        mod.solver = "EXACT"
    except TypeError:
        pass
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(env.evaluated_get(dg))
    env.modifiers.remove(mod)
    ancien = env.data
    env.data = me
    me.name = "enveloppe_verre"
    bpy.data.meshes.remove(ancien)
    bpy.data.objects.remove(toit)
    if not me.materials:
        me.materials.append(mat)

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.normal_update()
    sol = [f for f in bm.faces if f.normal.z < -0.99 and f.calc_center_median().z < 0.01]
    bmesh.ops.delete(bm, geom=sol, context="FACES_ONLY")
    bm.to_mesh(me)
    bm.free()
    return env


def aretes(env, coll, mat):
    """Arêtes réelles de l'enveloppe (murs, pignons, pans) en profilés de 5 cm."""
    ob = bpy.data.objects.new("aretes_enveloppe", env.data.copy())
    coll.objects.link(ob)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    wf = ob.modifiers.new("profiles", "WIREFRAME")
    wf.thickness = 0.05
    wf.use_boundary = True
    return ob


def structure(poly, coll, mat):
    _, w, h_f = profil_toit()
    bm = bmesh.new()
    L = pr.LARGEUR if FAITAGE_AXE == "y" else pr.H_DROIT

    def barre(u, z0, z1, demi):
        a0, a1 = portee(poly, min(max(u, 1e-3), L - 1e-3), FAITAGE_AXE)
        if FAITAGE_AXE == "y":
            boite(bm, u - demi, u + demi, a0, a1, z0, z1)
        else:
            boite(bm, a0, a1, u - demi, u + demi, z0, z1)

    for i in range(1, N_NEFS):                        # chéneaux intérieurs
        barre(i * w, H_CHENEAU - 0.20, H_CHENEAU, 0.15)
    # sablières : déjà dessinées par aretes_enveloppe (le mur bas n'est pas parallèle
    # au mur haut, une barre droite à u = 0 ne le suivrait pas)
    for i in range(N_NEFS):                           # faîtages
        barre(i * w + w / 2, h_f - 0.12, h_f, 0.06)
    # poteaux : angles de l'emprise + pieds des chéneaux sur les pignons
    pieds = list(poly)
    for i in range(1, N_NEFS):
        a0, a1 = portee(poly, i * w, FAITAGE_AXE)
        pieds += [(i * w, a0), (i * w, a1)] if FAITAGE_AXE == "y" else [(a0, i * w), (a1, i * w)]
    for x, y in pieds:
        boite(bm, x - 0.05, x + 0.05, y - 0.05, y + 0.05, 0.0, H_CHENEAU)
    return objet("structure", bm, coll, mat)


def tablette_3d(t, coll, mat):
    bm = bmesh.new()
    boite(bm, t["x0"], t["x1"], t["y0"], t["y1"], Z_TABLETTE - EP_PLATEAU, Z_TABLETTE)
    long_x = (t["x1"] - t["x0"]) >= (t["y1"] - t["y0"])
    a0, a1 = (t["x0"], t["x1"]) if long_x else (t["y0"], t["y1"])
    b0, b1 = (t["y0"], t["y1"]) if long_x else (t["x0"], t["x1"])
    n = max(2, math.ceil((a1 - a0 - 0.2) / PAS_PIEDS) + 1)
    for k in range(n):
        a = a0 + 0.1 + k * (a1 - a0 - 0.2) / (n - 1)
        for b in (b0 + 0.1, b1 - 0.1):
            x, y = (a, b) if long_x else (b, a)
            boite(bm, x - PIED / 2, x + PIED / 2, y - PIED / 2, y + PIED / 2,
                  0.0, Z_TABLETTE - EP_PLATEAU)
    ob = objet(f"R{t['rang']}-{t['num']:02d}", bm, coll, mat)
    ob["rang"], ob["numero"] = t["rang"], t["num"]
    ob["statut"] = "hypothese" if t["hyp"] else "donne"
    return ob


def demi_cercle(xa, xb, y0, sens, n=8):
    """Boucle en demi-cercle de (xa, y0) à (xb, y0), bombée vers sens (±1 en y)."""
    r = abs(xb - xa) / 2
    return [((xa + xb) / 2 - (xb - xa) / 2 * math.cos(math.pi * k / n),
             y0 + sens * r * math.sin(math.pi * k / n)) for k in range(n + 1)]


def serpentin(t, s, x_passes, y_tube, y_desc, zp, zh):
    """Flexible : descente depuis le tube, puis N passes dans la longueur de la tablette,
    reliées par des boucles. s = sens (±1 en y) du tube vers la tablette."""
    proche, loin = (t["y1"], t["y0"]) if s < 0 else (t["y0"], t["y1"])
    r = abs(x_passes[1] - x_passes[0]) / 2 if len(x_passes) > 1 else 0.0
    y_n, y_f = proche + s * (0.05 + r), loin - s * (0.05 + r)   # boucles dans la tablette
    xa = x_passes[0]
    pts = [(xa, y_tube, zp), (xa, y_desc, zp), (xa, y_desc, zh)]
    y_cour = y_f
    pts.append((xa, y_f, zh))
    for i in range(1, len(x_passes)):
        xp, xn = x_passes[i - 1], x_passes[i]
        bombe = s if y_cour == y_f else -s
        pts += [(x, yy, zh) for x, yy in demi_cercle(xp, xn, y_cour, bombe)[1:]]
        y_cour = y_n if y_cour == y_f else y_f
        pts.append((xn, y_cour, zh))
    return pts


def reseau_3d(tabs, coll, m_vert, m_noir, m_galva, m_laiton):
    lignes, pot_mur, pot_centre = pr.reseau(tabs)
    zc, zf = pr.Z_TUBE_CHAUD, pr.Z_TUBE_FROID
    chauds, froids, flex_c, flex_f, chaines = [], [], [], [], []
    bm_vannes = bmesh.new()
    for li in lignes:
        y, x0, x1, s = li["y"], li["x0"], li["x1"], li["cote"]
        # colonne montante + tube horizontal ; le froid démarre 15 cm plus loin
        xc, xf, xb = pr.colonnes(li)                 # colonnes côte à côte : retour direct
        chauds.append([(xc, y, 0.0), (xc, y, zc), (xb, y, zc)])
        froids.append([(xf, y, 0.0), (xf, y, zf), (xb, y, zf)])
        y_desc = y + s * 0.07                        # les flexibles descendent devant le tube
        for t in (t for t in tabs if t["rang"] == li["rang"]):
            larg = t["x1"] - t["x0"]
            if pr.CIRCUIT == "chaud_vers_froid":
                # N_PASSES longueurs régulières sur la largeur ; nombre pair -> le flexible
                # part du tube chaud et revient côté tubes, dans le tube froid
                n = N_PASSES + N_PASSES % 2
                xs = [t["x0"] + 0.15 + k * (larg - 0.30) / (n - 1) for k in range(n)]
                pts = serpentin(t, s, xs, y, y_desc, zc, Z_FLEX_CHAUD)
                pts += [(xs[-1], y_desc, Z_FLEX_CHAUD), (xs[-1], y_desc, zf), (xs[-1], y, zf)]
                flex_c.append(pts)
                vannes = ((xs[0], zc), (xs[-1], zf))  # départ (chaud) et retour (froid)
            else:
                # 1re version : flexibles chaud et froid indépendants, longueurs alternées
                n = N_PASSES + N_PASSES % 2
                xs = [t["x0"] + 0.15 + k * (larg - 0.30) / (n - 1) for k in range(n)]
                vannes = []
                for x_passes, zp, zh, dest in ((xs[0::2], zc, Z_FLEX_CHAUD, flex_c),
                                               (xs[1::2], zf, Z_FLEX_FROID, flex_f)):
                    dest.append(serpentin(t, s, x_passes, y, y_desc, zp, zh))
                    vannes.append((x_passes[0], zp))
            for xa, zp in vannes:
                boite(bm_vannes, xa - 0.025, xa + 0.025, y_desc - 0.025, y_desc + 0.025,
                      zp - 0.12, zp - 0.04)
    tube("tubes_verts_chauds", chauds, R_TUBE, coll, m_vert)
    tube("tubes_verts_froids", froids, R_TUBE, coll, m_vert)
    if pr.CIRCUIT == "chaud_vers_froid":
        tube("flexibles_circuits", flex_c, R_FLEX, coll, m_noir)
    else:
        tube("flexibles_chauds", flex_c, R_FLEX, coll, m_noir)
        tube("flexibles_froids", flex_f, R_FLEX, coll, m_noir)
    objet("vannes", bm_vannes, coll, m_laiton)

    # supports : poteaux (jusqu'au chéneau) + chaînes qui portent les tubes
    bm = bmesh.new()
    ligne_mur = next(li for li in lignes if li["nom"] == "mur")
    for px, py in pot_mur:                           # façade du mur haut (IMG_5710)
        boite(bm, px - 0.05, px + 0.05, py - 0.05, py + 0.05, 0.0, H_CHENEAU)
        yt = ligne_mur["y"]
        chaines += [[(px, py - 0.05, zc + 0.14), (px, yt, zc + R_TUBE)],
                    [(px, yt, zc - R_TUBE), (px, yt, zf + R_TUBE)]]
    for px, py in pot_centre:                        # poteaux centraux (IMG_5711)
        boite(bm, px - 0.05, px + 0.05, py - 0.05, py + 0.05, 0.0, H_CHENEAU)
        for li in lignes:
            if li["nom"] == "mur":
                continue
            side = 1 if li["y"] > py else -1
            chaines += [[(px, py + side * 0.05, zc + 0.35), (px, li["y"], zc + R_TUBE)],
                        [(px, li["y"], zc - R_TUBE), (px, li["y"], zf + R_TUBE)]]
    objet("poteaux_supports_tubes", bm, coll, m_galva)
    tube("chaines", chaines, 0.006, coll, m_galva)


# --- scène -------------------------------------------------------------------------------
def camera(nom, loc, cible, lens):
    cam = bpy.data.objects.new(nom, bpy.data.cameras.new(nom))
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    d = [c - l for c, l in zip(cible, loc)]
    cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0.0,
                          math.atan2(d[1], d[0]) - math.pi / 2)
    cam.data.lens = lens
    cam.data.clip_end = 500
    return cam


def construire():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.length_unit = "METERS"

    poly = pr.enveloppe()
    tabs = pr.tablettes()
    pr.verifier(tabs, poly)

    c_serre, c_tab, c_ctx = collection("Serre"), collection("Tablettes"), collection("Contexte")
    c_res = collection("Reseau_eau")
    m_verre = materiau_verre()
    m_struct = materiau("structure", (0.55, 0.57, 0.60), rough=0.4, metal=0.8)
    m_tab = materiau("tablette", (0.45, 0.62, 0.38), rough=0.7)
    m_tab_h = materiau("tablette_hypothese", (0.85, 0.55, 0.30), rough=0.7)
    m_sol = materiau("sol_serre", (0.62, 0.61, 0.58), rough=0.9)
    m_ext = materiau("sol_exterieur", (0.42, 0.47, 0.38), rough=1.0)
    m_vert = materiau("tube_vert", (0.09, 0.24, 0.14), rough=0.45, metal=0.3)
    m_noir = materiau("caoutchouc_noir", (0.015, 0.015, 0.015), rough=0.55)
    m_galva = materiau("acier_galva", (0.62, 0.64, 0.66), rough=0.35, metal=0.9)
    m_laiton = materiau("laiton_vanne", (0.72, 0.55, 0.25), rough=0.3, metal=1.0)

    env = enveloppe_verre(poly, c_serre, m_verre)
    aretes(env, c_serre, m_struct)
    structure(poly, c_serre, m_struct)

    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, y, 0.001)) for x, y in poly])
    objet("sol_serre", bm, c_serre, m_sol)
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in ((-60, -60, -0.01), (90, -60, -0.01),
                                            (90, 95, -0.01), (-60, 95, -0.01))])
    objet("sol_exterieur", bm, c_ctx, m_ext)

    for t in tabs:
        tablette_3d(t, c_tab, m_tab_h if t["hyp"] else m_tab)
    reseau_3d(tabs, c_res, m_vert, m_noir, m_galva, m_laiton)

    sun = bpy.data.objects.new("soleil", bpy.data.lights.new("soleil", "SUN"))
    sun.data.energy = 4.0
    sun.data.angle = math.radians(1.5)
    sun.rotation_euler = (math.radians(40), 0, math.radians(35))
    c_ctx.objects.link(sun)

    world = bpy.data.worlds.new("ciel")
    sc.world = world
    if world.node_tree is None:
        world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.62, 0.74, 0.92, 1.0)
    bg.inputs["Strength"].default_value = 0.35
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            pass

    cx, cy = pr.LARGEUR / 2, pr.H_DROIT / 2
    cam_ext = camera("cam_exterieur", (cx + 30, cy - 38, 17), (cx - 1, cy + 1, 1.0), 30)
    camera("cam_interieur", (6.5, 4.0, 1.65), (18.0, 30.0, 2.0), 20)
    yr = pr.niveaux()["reseau"]
    camera("cam_reseau_centre", (pr.LARGEUR - 5.5, yr + 1.4, 1.9),   # vers les colonnes
           (pr.LARGEUR - 0.2, yr - 0.1, 0.9), 24)                      # côté galerie (IMG_5715)
    camera("cam_reseau_mur", (1.2, pr.H_DROIT - 3.2, 2.1), (9.0, pr.H_DROIT - 0.3, 0.9), 22)
    t6 = next(t for t in tabs if t["rang"] == 2 and t["num"] == 6)
    xm = (t6["x0"] + t6["x1"]) / 2
    camera("cam_sous_tablette", (xm, yr + 0.02, 0.22), (xm, yr + 4.5, 0.74), 16)
    dessus = camera("cam_dessus", (cx, cy, 40.0), (cx, cy, 0.0), 50)
    dessus.rotation_euler = (0.0, 0.0, 0.0)          # vue en plan, +y vers le haut
    dessus.data.type = "ORTHO"
    dessus.data.ortho_scale = 39.0                   # rendu portrait : couvre les 35,5 m en y
    sc.camera = cam_ext

    # vue 3D du fichier sauvegardé : aperçu matériaux (verre transparent)
    for scr in bpy.data.screens:
        for area in scr.areas:
            if area.type == "VIEW_3D":
                for sp in area.spaces:
                    if sp.type == "VIEW_3D":
                        sp.shading.type = "MATERIAL"
                        sp.region_3d.view_perspective = "CAMERA"
    return poly, tabs


def rendre(seules=None):
    """Rend les caméras (toutes, ou seulement celles de `seules`, noms sans « cam_ »)."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
    sc.render.film_transparent = False
    toit = [bpy.data.objects[n] for n in ("enveloppe_verre", "aretes_enveloppe", "structure")]
    for cam in ("cam_exterieur", "cam_interieur", "cam_reseau_centre", "cam_reseau_mur",
                "cam_sous_tablette", "cam_dessus"):
        if seules and cam[4:] not in seules:
            continue
        vue_plan = cam == "cam_dessus"               # portrait, sans verre ni charpente
        sc.render.resolution_x, sc.render.resolution_y = (1000, 1200) if vue_plan else (1600, 1000)
        for ob in toit:
            ob.hide_render = vue_plan
        sc.camera = bpy.data.objects[cam]
        sc.render.filepath = str(OUT / f"rendu_{cam[4:]}.png")
        bpy.ops.render.render(write_still=True)
    for ob in toit:
        ob.hide_render = False
    sc.camera = bpy.data.objects["cam_exterieur"]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    OUT.mkdir(exist_ok=True)
    poly, tabs = construire()
    _, w, h_f = profil_toit()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "serre_rigerie.blend"))
    print(f"[rigerie] {len(tabs)} tablettes à z = {Z_TABLETTE} m · {N_NEFS} nefs de "
          f"{w:.2f} m (faîtages // {FAITAGE_AXE}) · chéneau {H_CHENEAU} m · faîtage {h_f:.2f} m")
    if "--render" in argv:
        rendre([a for a in argv if not a.startswith("--")] or None)
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "serre_rigerie.blend"))
    print(f"[rigerie] -> {OUT / 'serre_rigerie.blend'}")


main()
