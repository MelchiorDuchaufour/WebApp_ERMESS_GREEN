"""
serre_rigerie_detail.py — ajoute la structure fine manquante à la maquette Rigerie.

Rouvre `plan_rigerie/serre_rigerie.blend` (qui n'a que chéneaux, faîtages et
poteaux d'angle) et lui ajoute ce que montrent les photos de la serre :

  - barres de vitrage : le vitrage n'est pas une nappe unique, il est découpé en
    petites vitres. Chevrons montant du chéneau au faîtage (IMG_5709) + barres
    horizontales de recouvrement, et meneaux verticaux sur les quatre faces
    avec une traverse horizontale (IMG_5710) ;
  - fermes à treillis en y-z, une par travée, avec entrait, arbalétriers et
    diagonales — le motif en zigzag visible sous le vitrage (IMG_5709) ;
  - ouvrants de faîtage : un châssis de part et d'autre de chacun des faîtages,
    rendu entrouvert pour qu'il se lise en image.

HYPOTHÈSES (tout est en tête de fichier, une ligne à changer après mesure) :
  le pas des vitres est compté sur IMG_5710 — environ 7 vitres entre deux poteaux
  de façade — et rapporté au PAS_POTEAUX_MUR de plan_rigerie.py, lui-même une
  hypothèse. Les photos ne permettent pas mieux : aucune référence métrique ne se
  trouve dans le plan du vitrage (les tubes verts, seuls repères cotés, sont au
  premier plan). Idem pour la géométrie exacte des ouvrants.

N'écrit PAS sur serre_rigerie.blend : sortie dans serre_rigerie_detail.blend.

    blender -b plan_rigerie/serre_rigerie.blend --python serre_rigerie_detail.py
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import plan_rigerie as pr  # noqa: E402

OUT = ICI                    # serre_rigerie_detail.blend à côté de ce script

# --- repris de serre_rigerie_blender.py (mêmes valeurs) -------------------------
H_CHENEAU = 4.00
PENTE_DEG = 23.0
N_NEFS, FAITAGE_AXE = pr.N_NEFS, pr.FAITAGE_AXE          # nefs (plan_rigerie.py), faîtages // x

# --- HYPOTHÈSES de la structure fine --------------------------------------------
N_VITRES_TRAVEE = 7          # vitres comptées entre 2 poteaux de façade (IMG_5710)
PAS_FERME = pr.PAS_POTEAUX_MUR                  # ≈ 3,28 m : 1 ferme par travée
PAS_VITRE = PAS_FERME / N_VITRES_TRAVEE         # ≈ 0,457 m
PAS_RECOUV = 0.80            # pas des recouvrements horizontaux sur les pans
Z_TRAVERSE = 2.20            # traverse horizontale des façades
R_BARRE = 0.018              # demi-section des barres de vitrage
R_FERME = 0.035              # membrures de ferme
R_DIAG = 0.022               # diagonales de treillis
PAS_DIAG = 1.20              # pas des diagonales le long de l'entrait

OUV_LARG = 0.90              # longueur de l'ouvrant dans la pente
OUV_LONG = 2.40              # longueur le long du faîtage
OUV_JEU = 0.35               # intervalle entre deux ouvrants consécutifs
OUV_ANGLE = 18.0             # angle d'ouverture rendu (degrés)
OUV_EP = 0.04
OUV_DEUX_COTES = True        # un châssis de chaque côté du faîtage

L = pr.H_DROIT if FAITAGE_AXE == "x" else pr.LARGEUR
W_NEF = L / N_NEFS
TAN_P = math.tan(math.radians(PENTE_DEG))
H_FAITE = H_CHENEAU + (W_NEF / 2) * TAN_P


def z_toit(u):
    """Altitude du pan au droit de la coordonnée transverse u (0 <= u <= L)."""
    u = min(max(u, 0.0), L)
    i = min(int(u // W_NEF), N_NEFS - 1)
    u0, um = i * W_NEF, i * W_NEF + W_NEF / 2
    return H_CHENEAU + (u - u0) * TAN_P if u <= um else H_FAITE - (u - um) * TAN_P


def pt(u, a, z):
    """(u transverse, a le long des faîtages) -> (x, y, z) selon FAITAGE_AXE."""
    return (a, u, z) if FAITAGE_AXE == "x" else (u, a, z)


def barres(nom, chemins, rayon, coll, mat):
    cu = bpy.data.curves.new(nom, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = rayon
    cu.bevel_resolution = 0                      # section carrée : c'est un profilé
    for ch in chemins:
        sp = cu.splines.new("POLY")
        sp.points.add(len(ch) - 1)
        for i, p in enumerate(ch):
            sp.points[i].co = (p[0], p[1], p[2], 1.0)
    ob = bpy.data.objects.new(nom, cu)
    coll.objects.link(ob)
    if mat:
        cu.materials.append(mat)
    return ob


def dalle(bm, coins, ep):
    """Panneau plan d'épaisseur ep à partir de 4 coins (normale ~ verticale)."""
    import mathutils
    v = [mathutils.Vector(c) for c in coins]
    n = (v[1] - v[0]).cross(v[3] - v[0])
    n.normalize()
    bas = [bm.verts.new(tuple(p - n * ep / 2)) for p in v]
    haut = [bm.verts.new(tuple(p + n * ep / 2)) for p in v]
    bm.faces.new(bas[::-1])
    bm.faces.new(haut)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((bas[i], bas[j], haut[j], haut[i]))


def pans_a(poly, u):
    """Étendue [a0, a1] du bâtiment le long des faîtages, à la transverse u."""
    return pr.portee(poly, u, FAITAGE_AXE)


def pans_u(poly, a):
    """Étendue [u0, u1] transverse, à la coordonnée a le long des faîtages."""
    return pr.portee(poly, a, "y" if FAITAGE_AXE == "x" else "x")


# ───────────────────────────── pièces ──────────────────────────────────────────
def vitrage_toit(poly, coll, mat):
    """Chevrons dans la pente + recouvrements horizontaux, sur les 2N pans."""
    a_min = min(p[0] if FAITAGE_AXE == "x" else p[1] for p in poly)
    a_max = max(p[0] if FAITAGE_AXE == "x" else p[1] for p in poly)
    chemins = []
    # chevrons : a = cste, du chéneau au faîtage
    a = a_min + PAS_VITRE / 2
    while a < a_max:
        u0, u1 = pans_u(poly, a)
        for i in range(N_NEFS):
            for s0, s1 in ((i * W_NEF, i * W_NEF + W_NEF / 2),
                           (i * W_NEF + W_NEF / 2, (i + 1) * W_NEF)):
                b0, b1 = max(s0, u0), min(s1, u1)
                if b1 - b0 > 0.05:
                    chemins.append([pt(b0, a, z_toit(b0)), pt(b1, a, z_toit(b1))])
        a += PAS_VITRE
    # recouvrements : u = cste, sur toute la portée
    u = PAS_RECOUV
    while u < L:
        if min(abs(u - k * W_NEF) for k in range(N_NEFS + 1)) > 0.25:
            a0, a1 = pans_a(poly, u)
            if a1 - a0 > 0.2:
                chemins.append([pt(u, a0, z_toit(u)), pt(u, a1, z_toit(u))])
        u += PAS_RECOUV
    return barres("vitrage_toit", chemins, R_BARRE, coll, mat)


def vitrage_murs(poly, coll, mat):
    """Meneaux verticaux + traverse horizontale, le long de chaque côté."""
    chemins = []
    for (xa, ya), (xb, yb) in zip(poly, poly[1:] + poly[:1]):
        dx, dy = xb - xa, yb - ya
        lg = math.hypot(dx, dy)
        if lg < 0.3:
            continue
        n = max(1, int(round(lg / PAS_VITRE)))
        for k in range(1, n):
            t = k / n
            x, y = xa + t * dx, ya + t * dy
            u = y if FAITAGE_AXE == "x" else x
            ztop = z_toit(u)
            if ztop > 0.3:
                chemins.append([(x, y, 0.0), (x, y, ztop)])
        if Z_TRAVERSE < min(z_toit(ya if FAITAGE_AXE == "x" else xa),
                            z_toit(yb if FAITAGE_AXE == "x" else xb)):
            chemins.append([(xa, ya, Z_TRAVERSE), (xb, yb, Z_TRAVERSE)])
    return barres("vitrage_murs", chemins, R_BARRE, coll, mat)


def fermes(poly, coll, mat_m, mat_d):
    """Une ferme à treillis par travée et par nef : entrait + arbalétriers + diagonales."""
    a_min = min(p[0] if FAITAGE_AXE == "x" else p[1] for p in poly)
    a_max = max(p[0] if FAITAGE_AXE == "x" else p[1] for p in poly)
    membrures, diagonales = [], []
    a = a_min + PAS_FERME
    while a < a_max - 0.3:
        u0, u1 = pans_u(poly, a)
        for i in range(N_NEFS):
            s0, sm, s1 = i * W_NEF, i * W_NEF + W_NEF / 2, (i + 1) * W_NEF
            b0, b1 = max(s0, u0), min(s1, u1)
            if b1 - b0 < 1.0:
                continue
            membrures.append([pt(b0, a, H_CHENEAU), pt(b1, a, H_CHENEAU)])      # entrait
            som = [pt(b0, a, z_toit(b0))]
            if b0 < sm < b1:
                som.append(pt(sm, a, H_FAITE))
            som.append(pt(b1, a, z_toit(b1)))
            membrures.append(som)                                                # arbalétriers
            u, haut = b0, True                                                   # zigzag
            while u + PAS_DIAG < b1:
                v = u + PAS_DIAG
                p_a = pt(u, a, z_toit(u) if haut else H_CHENEAU)
                p_b = pt(v, a, H_CHENEAU if haut else z_toit(v))
                diagonales.append([p_a, p_b])
                u, haut = v, not haut
        a += PAS_FERME
    ob = barres("fermes_membrures", membrures, R_FERME, coll, mat_m)
    barres("fermes_diagonales", diagonales, R_DIAG, coll, mat_d)
    return ob


def ouvrants(poly, coll, mat):
    """Châssis d'aération le long des faîtages, rendus entrouverts."""
    th = math.radians(OUV_ANGLE)
    a_pente = math.radians(PENTE_DEG)
    # direction du plan de l'ouvrant une fois ouvert, dans le plan (u, z)
    du, dz = math.cos(a_pente - th), -math.sin(a_pente - th)
    bm = bmesh.new()
    cadres = []
    n = 0
    for i in range(N_NEFS):
        um = i * W_NEF + W_NEF / 2
        a0, a1 = pans_a(poly, um)
        cotes = (1, -1) if OUV_DEUX_COTES else (1,)
        for sg in cotes:
            a = a0 + OUV_JEU
            while a + OUV_LONG < a1:
                u_l = um + sg * OUV_LARG * du
                z_l = H_FAITE + OUV_LARG * dz
                coins = [pt(um, a, H_FAITE), pt(um, a + OUV_LONG, H_FAITE),
                         pt(u_l, a + OUV_LONG, z_l), pt(u_l, a, z_l)]
                dalle(bm, coins, OUV_EP)
                cadres.append(coins + [coins[0]])     # dormant visible du châssis
                n += 1
                a += OUV_LONG + OUV_JEU
    me = bpy.data.meshes.new("ouvrants_faitage")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("ouvrants_faitage", me)
    coll.objects.link(ob)
    if mat:
        me.materials.append(mat)
    barres("ouvrants_cadres", cadres, R_BARRE * 1.6, coll,
           bpy.data.materials.get("acier_galva") or bpy.data.materials.get("structure"))
    print(f"[detail] {n} ouvrants")
    return ob


def main():
    poly = pr.enveloppe()
    c = bpy.data.collections.new("Structure_fine")
    bpy.context.scene.collection.children.link(c)

    m_struct = bpy.data.materials.get("structure")
    m_galva = bpy.data.materials.get("acier_galva") or m_struct
    m_verre = bpy.data.materials.get("verre")

    vitrage_toit(poly, c, m_galva)
    vitrage_murs(poly, c, m_galva)
    fermes(poly, c, m_struct, m_galva)
    ouvrants(poly, c, m_verre)

    f = OUT / "serre_rigerie_detail.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(f))
    print(f"[detail] pas des vitres {PAS_VITRE:.3f} m · fermes tous les {PAS_FERME} m "
          f"· faîtage {H_FAITE:.2f} m -> {f}")


main()
