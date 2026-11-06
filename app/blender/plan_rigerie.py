#!/usr/bin/env python3
"""
plan_rigerie.py — Plan d'implantation des tablettes de la Serre Rigerie
(= « Grande serre » du Bocage), vue de dessus à l'échelle 1:250 sur A4 paysage.

Sources
  - Enveloppe : plan de site manuscrit « vérifié par Cédric le 12/12/2012 »
    (~/doctorat/rapport/plan serre.pdf). Coin bas-gauche : le mur gauche fait
    25,50 m jusqu'au magasin, puis le mur mitoyen du magasin descend de 9,50 m
    (pointillé tracé PARALLÈLE au mur gauche, donc une cote verticale) avec un
    décalage perpendiculaire de 5 m (« 5 ⊥ »). Le 35,5 du mur droit part du
    mur haut, sous la bande hachurée : la bande est hors des 1020 m².
    Aire calculée 1015 m² pour 1020 m² annoncés.
  - Tablettes des rangs 1-3 et faîtages parallèles au mur haut : communiqués le
    22/09/2026. Jeu entre tablettes : supposé, plus large que sur le schéma p.7
    (retour du 22/09), rang 1 centré.
  - Correction du 06/11/2026 (retour de terrain) : 4 nefs et non 3, double rangée
    (rangs 2-3) de 8 m, une rangée de poteaux au nord et une au sud de cette double
    rangée, plus de place entre celle-ci et les rangs 4-5.
  - Réseau eau chaude / froide : photos bocage/rigerie_circu_eau/ (22/09/2026).
    Une paire chaud/froid le long du mur haut pour le rang 1 (IMG_5705, 5710),
    deux paires entre les rangs 2 et 3, une par rangée (IMG_5711, 5715, et les
    deux paires rouge/bleu du schéma p.7). Tubes verts à ~1,5 m, accrochés par
    chaînes aux poteaux de façade (mur haut) et à des poteaux centraux.
  - Rangs 4-5, recul, couloir, allées : schéma « Grande serre : vue de haut »
    (Analyse-Bocage_VF Mars.docx p.7, même figure dans le pptx Sigrow). Son axe
    horizontal est à l'échelle (une tablette y fait 1,87 m pour un cadre de
    29,50 m), pas son axe vertical.

Tout ce qui est dans le bloc HYPOTHÈSES est à remplacer par un relevé. Le script
refuse de tracer si une tablette sort de la serre.

Repère : x le long du mur haut (0 = mur gauche), y vers le haut
(0 = pied du mur droit, mitoyen de la galerie Cuenol). Mètres.

Sorties (dossier plan_rigerie/) : .pdf et .svg vectoriels à l'échelle,
.png 300 dpi, .dxf R12 (QCAD, LibreCAD, FreeCAD), .csv des tablettes.

    python3 plan_rigerie.py
"""
from __future__ import annotations

import csv
from pathlib import Path

# matplotlib est importé dans les fonctions de rendu seulement : la géométrie
# (enveloppe, niveaux, tablettes) reste importable depuis le Python de Blender.

# --- Enveloppe (plan 2012) -----------------------------------------------------
LARGEUR = 29.50              # mur haut
H_DROIT = 35.50              # mur droit, mitoyen galerie Cuenol
H_GAUCHE = 25.50             # mur gauche, jusqu'au magasin
PAN_DX, PAN_DY = 5.00, 9.50  # mur mitoyen du magasin (pan coupé bas-gauche)
# bande hachurée au-dessus du mur haut : cotes ESTIMÉES sur le scan
BANDE_X0, BANDE_H, BANDE_X_HACH = 3.30, 2.70, 26.00

# --- Tablettes (données 22/09/2026) ----------------------------------------------
T_LARG = 1.80
R1_N, R1_LONG = 13, 3.20     # rang 1, contre le mur haut
R23_N, R23_LONG = 12, 8.00   # rangs 2 et 3, sous les 12 positions de droite (06/11 ; avant 8,80)

# --- Toiture (donnée 22/09/2026) -------------------------------------------------
N_NEFS = 4                   # 4 nefs égales (06/11/2026 ; avant : 3)
FAITAGE_AXE = "x"            # faîtages parallèles au mur haut -> nefs de 35,50/4 = 8,875 m
                             # rangées de poteaux sous les chéneaux : y = 8,875 / 17,75 / 26,625 m
                             # ("y" = parallèles au mur droit, nefs de 9,83 m : 1re version)

# --- HYPOTHÈSES (schéma p.7 ou valeur courante) --------------------------------
JEU_X = 0.40                 # entre deux tablettes voisines ; rang 1 centré, marges déduites
                             # (max 0,508 m : les marges tombent alors à 0)
# 1re version calée sur le schéma p.7 : MARGE_G = 1.30, MARGE_D = 2.10 -> jeu 0,225 m
RECUL_HAUT = 0.80            # mur haut -> rang 1
# couloir rang 1 / rang 2 : déduit (double rangée centrée sur le chéneau du milieu, cf. niveaux())
JEU_R2_R3 = 0.60             # passage du réseau central entre les rangs 2 et 3 (existe : 22/09)
R45_REPARTITION = "fixe"     # "fixe" (06/11) : valeurs ci-dessous, rangs 4-5 regroupés au sud.
                             # "egale" = 3 espaces égaux R3->R4 = R4->R5 = R5->mur bas (22/09)
ALLEE_R3_R4 = 4.05           # hyp. : contient la rangée de poteaux ; laisse R5 à 1 m du point haut du mur bas
R45_POS = 11                 # rangs 4-5 larges de ~11 positions (22/09), alignés côté galerie
R45_N = 2                    # tablettes par rang 4 et 5, posées en long (p.7)
R45_LARG = 1.80
R45_JEU_X = 0.30             # entre les deux tablettes d'un même rang
R4_R5_JEU = 0.80             # (mode "fixe") hyp., avant 0.20

# --- Réseau eau chaude / froide (photos 22/09/2026) ------------------------------
Z_TUBE_CHAUD, Z_TUBE_FROID = 1.50, 1.35   # tubes verts superposés, « à 1,5 m » (donné)
RECUL_TUBES_MUR = 0.18       # hyp. axe des tubes du mur haut -> mur
DEMI_ECART_PAIRES = 0.14     # hyp. écart des 2 paires centrales de part et d'autre des poteaux
PAS_POTEAUX_MUR = 3.20       # hyp. poteaux de façade portant les tubes (IMG_5710)
PAS_POTEAUX_CENTRE = 4.00    # hyp. poteaux du réseau central (IMG_5711)
CIRCUIT = "chaud_vers_froid" # 1 circuit par tablette : départ sur le tube chaud, 3 passes
                             # sous la tablette, retour dans le tube froid (22/09, « je crois »)
# 1re version : CIRCUIT = "deux_departs" -> un flexible chaud + un froid indépendants

ECHELLE = 250                # 1:250 -> 1 m = 4 mm
PAGE_MM = (297, 210)         # A4 paysage
OUT = Path(__file__).resolve().parent / "plan_rigerie"

# --- styles par calque (matplotlib ; le DXF reprend les noms de calques) ---------
C_DONNEE, C_HYP = "#222222", "#c05a00"
STYLE = {
    "MURS":          dict(color="#111111", lw=2.0, ls="-"),
    "LIMITE":        dict(color="#555555", lw=0.8, ls="-"),
    "BANDE_2012":    dict(color="#8a8a8a", lw=0.7, ls="--"),
    "TABLETTES":     dict(color="#3d7a2b", lw=0.6, ls="-"),
    "TABLETTES_HYP": dict(color="#3d7a2b", lw=0.6, ls=(0, (3, 2))),
    "COTES":         dict(color=C_DONNEE, lw=0.4, ls="-"),
    "COTES_HYP":     dict(color=C_HYP, lw=0.4, ls="-"),
    "TEXTE":         dict(color="#222222", lw=0.4, ls="-"),
    "ANNOT":         dict(color="#6b6b6b", lw=0.6, ls="-"),
    "TOITURE":       dict(color="#6b6b6b", lw=0.55, ls="-."),
    "RESEAU_CHAUD":  dict(color="#d6453d", lw=0.7, ls="-"),
    "RESEAU_FROID":  dict(color="#2f6fc0", lw=0.7, ls="-"),
    "POTEAUX":       dict(color="#555555", lw=0.4, ls="-"),
}
DXF_LAYERS = {  # nom: (couleur ACI, type de ligne)
    "MURS": (7, "CONTINUOUS"), "LIMITE": (8, "CONTINUOUS"),
    "BANDE_2012": (8, "DASHED"), "TABLETTES": (3, "CONTINUOUS"),
    "TABLETTES_HYP": (3, "DASHED"), "COTES": (4, "CONTINUOUS"),
    "COTES_HYP": (30, "CONTINUOUS"), "TEXTE": (7, "CONTINUOUS"),
    "ANNOT": (8, "CONTINUOUS"), "TOITURE": (8, "DASHDOT"),
    "RESEAU_CHAUD": (1, "CONTINUOUS"), "RESEAU_FROID": (5, "CONTINUOUS"),
    "POTEAUX": (8, "CONTINUOUS"),
}
FILL = {"TABLETTES": "#cfe6bf", "TABLETTES_HYP": "#edf5e6", "POTEAUX": "#555555"}


def fr(v: float, nd: int = 2) -> str:
    return f"{v:.{nd}f}".replace(".", ",")


# --- géométrie -----------------------------------------------------------------
def enveloppe():
    y_pan = H_DROIT - H_GAUCHE
    return [(0, H_DROIT), (LARGEUR, H_DROIT), (LARGEUR, 0),
            (PAN_DX, y_pan - PAN_DY), (0, y_pan)]


def aire(pts):
    n = len(pts)
    return abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
                   for i in range(n))) / 2


def niveaux():
    """Bords haut/bas (y) de chaque rang, et du couloir."""
    y = {}
    y["r1"] = (H_DROIT - RECUL_HAUT, H_DROIT - RECUL_HAUT - R1_LONG)
    # double rangée centrée sur la rangée de poteaux du milieu (chéneau central, réseau)
    y["reseau"] = H_DROIT / 2
    y["r2"] = (y["reseau"] + JEU_R2_R3 / 2 + R23_LONG, y["reseau"] + JEU_R2_R3 / 2)
    y["r3"] = (y["reseau"] - JEU_R2_R3 / 2, y["reseau"] - JEU_R2_R3 / 2 - R23_LONG)
    y["couloir"] = (y["r1"][1], y["r2"][0])
    if R45_REPARTITION == "egale":
        y_bas = H_DROIT - H_GAUCHE - PAN_DY          # point le plus haut du mur bas (0,5 m)
        a = b = (y["r3"][1] - y_bas - 2 * R45_LARG) / 3
    else:
        a, b = ALLEE_R3_R4, R4_R5_JEU
    y["r4"] = (y["r3"][1] - a, y["r3"][1] - a - R45_LARG)
    y["r5"] = (y["r4"][1] - b, y["r4"][1] - b - R45_LARG)
    return y


def marge_x():
    """Marge entre le mur et la tablette extrême du rang 1, identique des deux côtés."""
    return (LARGEUR - R1_N * T_LARG - (R1_N - 1) * JEU_X) / 2


def pas_x():
    if marge_x() < 0:
        raise ValueError(f"{R1_N} tablettes de {T_LARG} m avec un jeu de {JEU_X} m "
                         f"dépassent les {LARGEUR} m du mur haut")
    return T_LARG + JEU_X, JEU_X


def portee(poly, u, axe):
    """Intervalle [a_min, a_max] de la droite u = cste à l'intérieur du polygone convexe.
    axe = "y" : droite x = u, parcourue en y ; axe = "x" : droite y = u, parcourue en x."""
    ts = []
    for (xa, ya), (xb, yb) in zip(poly, poly[1:] + poly[:1]):
        ua, ub = (xa, xb) if axe == "y" else (ya, yb)
        aa, ab = (ya, yb) if axe == "y" else (xa, xb)
        if (ua - u) * (ub - u) <= 0 and ua != ub:
            ts.append(aa + (u - ua) * (ab - aa) / (ub - ua))
    return min(ts), max(ts)


def lignes_toit():
    """[(u, 'faîtage' | 'chéneau')] ; u = coordonnée transverse aux faîtages."""
    L = LARGEUR if FAITAGE_AXE == "y" else H_DROIT
    w = L / N_NEFS
    return [(i * w / 2, "faîtage" if i % 2 else "chéneau") for i in range(1, 2 * N_NEFS)]


def tablettes():
    """Liste de dicts : rang, numéro (1 = côté galerie, comme le rapport), rectangle."""
    pas, _ = pas_x()
    y = niveaux()
    x_d = lambda k: LARGEUR - marge_x() - (k - 1) * pas   # bord droit de la position k
    tabs = []
    for rang, n, hyp in (("r1", R1_N, False), ("r2", R23_N, False), ("r3", R23_N, False)):
        for k in range(1, n + 1):
            tabs.append(dict(rang=int(rang[1]), num=k, x0=x_d(k) - T_LARG, x1=x_d(k),
                             y0=y[rang][1], y1=y[rang][0], hyp=hyp))
    x0_45, x1_45 = x_d(R45_POS) - T_LARG, x_d(1)
    long45 = (x1_45 - x0_45 - (R45_N - 1) * R45_JEU_X) / R45_N
    for rang in ("r4", "r5"):
        for k in range(1, R45_N + 1):               # 1 = côté galerie
            xr = x1_45 - (k - 1) * (long45 + R45_JEU_X)
            tabs.append(dict(rang=int(rang[1]), num=k, x0=xr - long45, x1=xr,
                             y0=y[rang][1], y1=y[rang][0], hyp=True))
    return tabs


def reseau(tabs):
    """Lignes de distribution (tubes verts) et poteaux qui les portent.

    Chaque ligne = une paire chaud/froid superposée (Z_TUBE_CHAUD au-dessus de
    Z_TUBE_FROID), qui alimente les tablettes du rang `rang`. Les deux colonnes
    montantes (aller et retour) sont côte à côte au MÊME bout : retour direct, pas
    de Tichelmann. Côté d'arrivée confirmé sur place le 23/09 :
      - ligne du mur haut : coin haut gauche (IMG_5705, 2 colonnes) ;
      - réseau central : côté galerie Cuenol, à droite (IMG_5715, 4 colonnes),
        cohérent avec les flèches du schéma p.15 et l'aller plus chaud à
        l'« extrémité » (61 °C contre 51 °C au milieu).
    """
    y = niveaux()
    x_fin = max(t["x1"] for t in tabs if t["rang"] <= 3) + 0.15
    x_r23 = min(t["x0"] for t in tabs if t["rang"] == 2)
    x_bout_c = x_r23 - 0.15                  # bouchon du réseau central, côté gauche
    x_arr_c = LARGEUR - 0.25                 # colonnes du réseau central, côté galerie
    # 1re version : réseau central alimenté à gauche, x0 = x_r23 - 0.60 (cercles du schéma p.7)
    lignes = [
        dict(nom="mur", rang=1, y=H_DROIT - RECUL_TUBES_MUR, x0=0.30, x1=x_fin, cote=-1,
             depart="gauche"),
        dict(nom="centre_r2", rang=2, y=y["reseau"] + DEMI_ECART_PAIRES, x0=x_bout_c,
             x1=x_arr_c, cote=+1, depart="droite"),
        dict(nom="centre_r3", rang=3, y=y["reseau"] - DEMI_ECART_PAIRES, x0=x_bout_c,
             x1=x_arr_c, cote=-1, depart="droite"),
    ]   # cote : côté (en y) où descendent les flexibles, vers les tablettes servies
    n_mur = int(LARGEUR / PAS_POTEAUX_MUR)
    poteaux_mur = [(k * PAS_POTEAUX_MUR, H_DROIT - 0.05) for k in range(1, n_mur + 1)
                   if k * PAS_POTEAUX_MUR < LARGEUR - 0.3]
    poteaux_centre = []
    x = x_bout_c + 0.75
    while x < x_fin:
        poteaux_centre.append((x, y["reseau"]))
        x += PAS_POTEAUX_CENTRE
    return lignes, poteaux_mur, poteaux_centre


def poteaux_nefs(tabs=None):
    """Rangées de poteaux sous les chéneaux, hors rangée centrale (déjà dans reseau()).
    Même pas et mêmes x que les poteaux centraux. Lève une erreur si un poteau tombe
    sur une tablette."""
    tabs = tabs or tablettes()
    _, _, centre = reseau(tabs)
    x_ref, poly, y_c = centre[0][0], enveloppe(), niveaux()["reseau"]
    w, out = H_DROIT / N_NEFS, []
    for i in range(1, N_NEFS):
        yp = i * w
        if abs(yp - y_c) < 1e-6:
            continue
        a0, a1 = portee(poly, yp, "x")
        k0 = int((x_ref - a0) // PAS_POTEAUX_CENTRE)
        x = x_ref - k0 * PAS_POTEAUX_CENTRE
        while x < a1 - 0.3:
            if x > a0 + 0.3:
                for t in tabs:
                    if t["x0"] <= x <= t["x1"] and t["y0"] <= yp <= t["y1"]:
                        raise ValueError(f"poteau ({x:.2f}, {yp:.2f}) sur la tablette R{t['rang']}-{t['num']}")
                out.append((x, yp))
            x += PAS_POTEAUX_CENTRE
    return out


def colonnes(li):
    """(x colonne chaude, x colonne froide, x du bout opposé) d'une ligne du réseau.
    La colonne froide est 15 cm en retrait vers l'intérieur de la ligne."""
    if li["depart"] == "gauche":
        return li["x0"], li["x0"] + 0.15, li["x1"]
    return li["x1"], li["x1"] - 0.15, li["x0"]


def dedans(p, poly):
    """Point strictement dans le polygone (lancer de rayon)."""
    x, y = p
    res = False
    for (xa, ya), (xb, yb) in zip(poly, poly[1:] + poly[:1]):
        if (ya > y) != (yb > y) and x < xa + (y - ya) * (xb - xa) / (yb - ya):
            res = not res
    return res


def verifier(tabs, poly):
    for t in tabs:
        coins = [(t["x0"], t["y0"]), (t["x1"], t["y0"]), (t["x0"], t["y1"]), (t["x1"], t["y1"])]
        if not all(dedans(c, poly) for c in coins):
            raise ValueError(f"tablette rang {t['rang']} n°{t['num']} hors de la serre : "
                             "revoir les paramètres HYPOTHÈSES")


# --- scène : primitives communes au rendu matplotlib et au DXF ---------------------
class Scene:
    def __init__(self):
        self.items = []

    def poly(self, pts, layer, closed=True, fill=None, hatch=None):
        self.items.append(("poly", dict(pts=list(pts), layer=layer, closed=closed,
                                        fill=fill, hatch=hatch)))

    def line(self, p, q, layer):
        self.items.append(("poly", dict(pts=[p, q], layer=layer, closed=False,
                                        fill=None, hatch=None)))

    def text(self, x, y, s, pt, layer="TEXTE", rot=0, ha="center", va="center",
             style="normal", weight="normal", color=None, bg=False, dxf=True):
        self.items.append(("text", dict(x=x, y=y, s=s, pt=pt, layer=layer, rot=rot,
                                        ha=ha, va=va, style=style, weight=weight,
                                        color=color, bg=bg, dxf=dxf)))

    def arrow(self, p, q, layer="ANNOT"):
        self.items.append(("arrow", dict(p=p, q=q, layer=layer)))


def _tick(sc, x, y, layer, d=0.22):
    sc.line((x - d, y - d), (x + d, y + d), layer)


def cote_h(sc, x1, x2, y, txt, hyp=False, refs=None, pt=5.5):
    """Cote horizontale ; refs = (y_ref1, y_ref2) pour les lignes d'attache."""
    lay = "COTES_HYP" if hyp else "COTES"
    sc.line((x1, y), (x2, y), lay)
    for x, yr in zip((x1, x2), refs or (None, None)):
        _tick(sc, x, y, lay)
        if yr is not None:
            s = 1 if y > yr else -1
            sc.line((x, yr + s * 0.25), (x, y + s * 0.35), lay)
    sc.text((x1 + x2) / 2, y + 0.15, txt, pt, lay, ha="center", va="bottom",
            style="italic" if hyp else "normal", color=C_HYP if hyp else C_DONNEE)


def cote_v(sc, y1, y2, x, txt, hyp=False, refs=None, pt=5.5, label_right=False):
    lay = "COTES_HYP" if hyp else "COTES"
    sc.line((x, y1), (x, y2), lay)
    for y, xr in zip((y1, y2), refs or (None, None)):
        _tick(sc, x, y, lay)
        if xr is not None:
            s = 1 if x > xr else -1
            sc.line((xr + s * 0.25, y), (x + s * 0.35, y), lay)
    col, sty = (C_HYP, "italic") if hyp else (C_DONNEE, "normal")
    if label_right:
        sc.text(x + 0.4, (y1 + y2) / 2, txt, pt, lay, ha="left", va="center", style=sty, color=col)
    else:
        sc.text(x - 0.15, (y1 + y2) / 2, txt, pt, lay, rot=90, ha="center", va="bottom",
                style=sty, color=col)


def construire(tabs, poly):
    sc = Scene()
    y = niveaux()
    pas, jeu = pas_x()
    top = H_DROIT

    # bande hachurée (hors 1020 m²)
    bande = [(BANDE_X0, top), (LARGEUR, top), (LARGEUR, top + BANDE_H), (BANDE_X0, top + BANDE_H)]
    sc.poly([(BANDE_X0, top), (BANDE_X_HACH, top), (BANDE_X_HACH, top + BANDE_H),
             (BANDE_X0, top + BANDE_H)], "BANDE_2012", hatch="////")
    sc.poly(bande, "BANDE_2012")
    sc.text((BANDE_X0 + LARGEUR) / 2, top + BANDE_H / 2,
            "bande hachurée du plan 2012 (hors 1020 m², cotes estimées)", 5.5,
            "ANNOT", style="italic", color="#6b6b6b", bg=True)

    # couloir
    sc.poly([(0, y["couloir"][0]), (LARGEUR, y["couloir"][0]), (LARGEUR, y["couloir"][1]),
             (0, y["couloir"][1])], "LIMITE", fill="#f4eedd", hatch=None)
    sc.items[-1][1]["layer_mpl_only"] = True
    sc.text(LARGEUR * 0.52, (y["couloir"][0] + y["couloir"][1]) / 2 + 0.05,
            f"couloir de passage  ({fr(y['couloir'][0] - y['couloir'][1])} m)", 6.5, style="italic", color=C_HYP)

    # tablettes
    for t in tabs:
        lay = "TABLETTES_HYP" if t["hyp"] else "TABLETTES"
        sc.poly([(t["x0"], t["y0"]), (t["x1"], t["y0"]), (t["x1"], t["y1"]),
                 (t["x0"], t["y1"])], lay, fill=FILL[lay])
        if t["rang"] <= 3:
            sc.text((t["x0"] + t["x1"]) / 2, (t["y0"] + t["y1"]) / 2, str(t["num"]), 5.5,
                    color="#2b5c1e")

    # réseau eau chaude / froide : en plan, la paire superposée est dédoublée
    # (chaud au-dessus, froid en dessous, ±6 cm) pour rester lisible
    lignes, pot_mur, pot_centre = reseau(tabs)
    for li in lignes:
        xc, xf, xb = colonnes(li)
        for lay, dy, xr in (("RESEAU_CHAUD", 0.06, xc), ("RESEAU_FROID", -0.06, xf)):
            yy = li["y"] + dy
            sc.line((xr, yy), (xb, yy), lay)
            c = (xr, yy)                                  # colonne montante
            sc.poly([(c[0] - 0.09, c[1] - 0.09), (c[0] + 0.09, c[1] - 0.09),
                     (c[0] + 0.09, c[1] + 0.09), (c[0] - 0.09, c[1] + 0.09)], lay,
                    fill=STYLE[lay]["color"])
    for px, py in pot_mur + pot_centre + poteaux_nefs(tabs):
        sc.poly([(px - 0.06, py - 0.06), (px + 0.06, py - 0.06), (px + 0.06, py + 0.06),
                 (px - 0.06, py + 0.06)], "POTEAUX", fill=FILL["POTEAUX"])

    # toiture : faîtages et chéneaux (trait mixte), étiquetés côté gauche
    for u, nom in lignes_toit():
        a0, a1 = portee(poly, u, FAITAGE_AXE)
        p, q = ((u, a0), (u, a1)) if FAITAGE_AXE == "y" else ((a0, u), (a1, u))
        sc.line(p, q, "TOITURE")
        if FAITAGE_AXE == "x":
            sc.text(a0 + 0.35, u - 0.12, nom, 5, "TOITURE", ha="left", va="top",
                    style="italic", color="#6b6b6b")
        else:
            sc.text(u - 0.12, a1 - 0.3, nom, 5, "TOITURE", rot=90, ha="right", va="bottom",
                    style="italic", color="#6b6b6b")

    # murs
    sc.poly(poly, "MURS")

    # --- cotes de l'enveloppe (noir = plan 2012) ---
    cote_h(sc, 0, LARGEUR, top + BANDE_H + 1.1, fr(LARGEUR), refs=(top, top + BANDE_H))
    y_pan = H_DROIT - H_GAUCHE
    cote_v(sc, top, y_pan, -2.3, fr(H_GAUCHE), refs=(0, 0))
    cote_v(sc, y_pan, y_pan - PAN_DY, -2.3, fr(PAN_DY), refs=(None, PAN_DX))
    cote_h(sc, 0, PAN_DX, -1.9, fr(PAN_DX), refs=(y_pan, y_pan - PAN_DY))
    cote_h(sc, PAN_DX, LARGEUR, -1.9, fr(LARGEUR - PAN_DX), refs=(None, 0))
    cote_v(sc, top, 0, 37.0, fr(H_DROIT), refs=(LARGEUR, LARGEUR))

    # --- chaîne verticale côté droit (rangs) ---
    xc = 33.0
    bornes = [top, y["r1"][0], y["r1"][1], y["couloir"][1], y["r2"][1], y["r3"][0],
              y["r3"][1], y["r4"][0], y["r4"][1], y["r5"][0], y["r5"][1], 0]
    hyps = [True, False, True, False, True, False, True, True, True, True, True]
    for (a, b), h in zip(zip(bornes[:-1], bornes[1:]), hyps):
        cote_v(sc, a, b, xc, fr(a - b), hyp=h, label_right=True)
    for yb in bornes:
        sc.line((LARGEUR + 0.3, yb), (xc - 0.35, yb), "ANNOT")
    for r in range(1, 6):
        yy = sum(y[f"r{r}"]) / 2
        sc.text(LARGEUR + 0.45, yy, f"Rang {r}", 6.5, ha="left", weight="bold")

    # --- cotes horizontales du rang 1 (dans le couloir) ---
    yc = y["couloir"][1] + 0.3
    x13 = marge_x()
    cote_h(sc, 0, x13, yc, fr(x13), hyp=True, pt=5)
    cote_h(sc, x13, x13 + T_LARG, yc, fr(T_LARG), pt=5)
    cote_h(sc, x13 + T_LARG, x13 + pas, yc, "", hyp=True)       # jeu : texte déporté
    sc.text(x13 + pas + 0.3, yc + 0.15, f"jeu entre tablettes {fr(jeu)}", 5,
            "COTES_HYP", ha="left", va="bottom", style="italic", color=C_HYP)
    cote_h(sc, LARGEUR - x13, LARGEUR, yc, fr(x13), hyp=True, pt=5)

    # --- passage à gauche des rangs 2-3 ---
    x_r23 = min(t["x0"] for t in tabs if t["rang"] == 2)
    cote_h(sc, 0, x_r23, sum(y["r2"]) / 2, fr(x_r23), hyp=True)

    # --- rangs 4-5 : chaîne dans l'allée au-dessus du rang 4 (mêmes x pour le rang 5) ---
    r45 = sorted((t for t in tabs if t["rang"] == 4), key=lambda t: t["x0"])
    yb = y["r4"][0] + 0.5
    xs = [portee(poly, yb, "x")[0]] + [v for t in r45 for v in (t["x0"], t["x1"])] + [LARGEUR]
    for a, b in zip(xs[:-1], xs[1:]):
        cote_h(sc, a, b, yb, fr(b - a), hyp=True)

    # --- annotations de contexte ---
    sc.text(-3.6, y_pan - PAN_DY / 2, "magasin\nRigerie", 6, "ANNOT", ha="right",
            style="italic", color="#6b6b6b")
    sc.text(38.6, top / 2, "galerie Cuenol (mitoyenne)", 6, "ANNOT", rot=90,
            style="italic", color="#6b6b6b")
    t_e = 0.90                                    # position le long du mur magasin
    pe = (PAN_DX * t_e, y_pan - PAN_DY * t_e)
    nx, ny = PAN_DY, PAN_DX                       # normale entrante (non normée)
    nn = (nx ** 2 + ny ** 2) ** 0.5
    nx, ny = nx / nn, ny / nn
    sc.arrow((pe[0] - 2.4 * nx, pe[1] - 2.4 * ny), (pe[0] + 1.2 * nx, pe[1] + 1.2 * ny))
    sc.text(pe[0] - 2.4 * nx - 0.2, pe[1] - 2.4 * ny, "entrée\n(magasin)", 6, "ANNOT",
            ha="right", va="center", style="italic", color="#6b6b6b")   # confirmé 22/09
    return sc


# --- rendu matplotlib ------------------------------------------------------------
def rendre_mpl(sc, ax):
    from matplotlib.patches import Polygon
    for kind, d in sc.items:
        if kind == "poly":
            st = STYLE[d["layer"]]
            if d.get("layer_mpl_only"):           # fond du couloir : pas de contour
                ax.add_patch(Polygon(d["pts"], closed=True, fc=d["fill"], ec="none", zorder=1))
                continue
            if d["hatch"]:
                ax.add_patch(Polygon(d["pts"], closed=True, fill=False, hatch=d["hatch"],
                                     ec="#b5b5b5", lw=0, zorder=1))
                continue
            z = {"MURS": 4, "TOITURE": 5}.get(d["layer"], 3)
            ax.add_patch(Polygon(d["pts"], closed=d["closed"], fc=d["fill"] or "none",
                                 ec=st["color"], lw=st["lw"], ls=st["ls"], zorder=z,
                                 joinstyle="miter"))
        elif kind == "text":
            bbox = dict(boxstyle="square,pad=0.15", fc="white", ec="none") if d["bg"] else None
            ax.text(d["x"], d["y"], d["s"], fontsize=d["pt"], rotation=d["rot"],
                    rotation_mode="anchor", ha=d["ha"], va=d["va"], fontstyle=d["style"],
                    fontweight=d["weight"], color=d["color"] or STYLE[d["layer"]]["color"],
                    bbox=bbox, zorder=6, linespacing=1.1)
        elif kind == "arrow":
            ax.annotate("", xy=d["q"], xytext=d["p"], zorder=6,
                        arrowprops=dict(arrowstyle="-|>", color="#6b6b6b", lw=0.9,
                                        mutation_scale=7))


def cartouche(ax, tabs, poly, x0, ytop):
    """Titre, échelle, tableau, légende, hypothèses (page PDF seulement)."""
    from matplotlib.patches import Rectangle
    y = ytop
    ax.text(x0, y, "Serre Rigerie", fontsize=15, fontweight="bold", va="top")
    y -= 2.3
    ax.text(x0, y, "Grande serre du Bocage · implantation des tablettes", fontsize=7.5, va="top")
    y -= 1.35
    ax.text(x0, y, f"vue de dessus · échelle 1:{ECHELLE} (A4 paysage) · cotes en m",
            fontsize=6.5, va="top", color="#555")

    # barre d'échelle 0-10 m
    y -= 2.6
    for i in range(5):
        ax.add_patch(Rectangle((x0 + 2 * i, y), 2, 0.45, fc="#222" if i % 2 == 0 else "white",
                               ec="#222", lw=0.5))
    for v in (0, 5, 10):
        ax.text(x0 + v, y - 0.25, f"{v}", fontsize=5.5, ha="center", va="top")
    ax.text(x0 + 10.6, y + 0.22, "m", fontsize=5.5, va="center")

    # tableau des rangs
    y -= 2.5
    cols = [x0, x0 + 3.3, x0 + 5.6, x0 + 11.8, x0 + 16.2]
    heads = ["Rang", "Nb", "Tablette (m)", "Surface", "Source"]
    for c, h in zip(cols, heads):
        ax.text(c, y, h, fontsize=6.3, fontweight="bold", va="top")
    y -= 1.0
    ax.plot([x0, x0 + 23.2], [y, y], color="#222", lw=0.5)
    y -= 0.35
    tot_n, tot_s = 0, 0.0
    for r in range(1, 6):
        tr = [t for t in tabs if t["rang"] == r]
        dx, dy = tr[0]["x1"] - tr[0]["x0"], tr[0]["y1"] - tr[0]["y0"]
        s = sum((t["x1"] - t["x0"]) * (t["y1"] - t["y0"]) for t in tr)
        tot_n += len(tr)
        tot_s += s
        hyp = tr[0]["hyp"]
        col = C_HYP if hyp else C_DONNEE
        vals = [f"{r}", f"{len(tr)}", f"{fr(dx)} × {fr(dy)}", f"{fr(s, 1)} m²",
                "hyp. (rapport p.7)" if hyp else ("donné 06/11/2026" if r in (2, 3) else "donné 22/09/2026")]
        for c, v in zip(cols, vals):
            ax.text(c, y, v, fontsize=6.3, va="top", color=col,
                    fontstyle="italic" if hyp and c == cols[-1] else "normal")
        y -= 1.05
    ax.plot([x0, x0 + 23.2], [y + 0.15, y + 0.15], color="#222", lw=0.5)
    y -= 0.3
    for c, v in zip(cols, ["Total", f"{tot_n}", "", f"{fr(tot_s, 1)} m²", ""]):
        ax.text(c, y, v, fontsize=6.3, va="top", fontweight="bold")
    y -= 1.5
    a = aire(poly)
    L = LARGEUR if FAITAGE_AXE == "y" else H_DROIT
    mur = "droit" if FAITAGE_AXE == "y" else "haut"
    ax.text(x0, y, f"Sol de la serre : {fr(a, 0)} m² calculés ({fr(1020, 0)} m² au plan 2012)\n"
                   f"Tablettes : {fr(100 * tot_s / a, 0)} % du sol\n"
                   f"Toiture : {N_NEFS} nefs de {fr(L / N_NEFS)} m, faîtages parallèles au mur {mur}",
            fontsize=6.3, va="top", linespacing=1.5)

    # légende
    y -= 4.3
    ax.text(x0, y, "Légende", fontsize=6.8, fontweight="bold", va="top")
    y -= 1.35
    items = [
        (lambda yy: ax.add_patch(Rectangle((x0, yy - 0.55), 1.6, 0.55, fc=FILL["TABLETTES"],
                                           ec="#3d7a2b", lw=0.6)), "tablette, dimensions données"),
        (lambda yy: ax.add_patch(Rectangle((x0, yy - 0.55), 1.6, 0.55, fc=FILL["TABLETTES_HYP"],
                                           ec="#3d7a2b", lw=0.6, ls=(0, (3, 2)))),
         "tablette, dimensions supposées"),
        (lambda yy: ax.add_patch(Rectangle((x0, yy - 0.55), 1.6, 0.55, fc="#f4eedd", ec="none")),
         "couloir de passage"),
        (lambda yy: ax.plot([x0, x0 + 1.6], [yy - 0.28] * 2, color="#6b6b6b", lw=0.55,
                            ls="-."), "faîtage / chéneau"),
        (lambda yy: ax.plot([x0, x0 + 1.6], [yy - 0.28] * 2, color=STYLE["RESEAU_CHAUD"]["color"],
                            lw=0.9), f"tube chaud (départ), vert à {fr(Z_TUBE_CHAUD)} m"),
        (lambda yy: ax.plot([x0, x0 + 1.6], [yy - 0.28] * 2, color=STYLE["RESEAU_FROID"]["color"],
                            lw=0.9), (f"tube froid (reçoit le retour), vert à {fr(Z_TUBE_FROID)} m"
                                      if CIRCUIT == "chaud_vers_froid"
                                      else f"départ froid, tube vert à {fr(Z_TUBE_FROID)} m")),
        (lambda yy: ax.add_patch(Rectangle((x0 + 0.65, yy - 0.43), 0.3, 0.3, fc="#555555",
                                           ec="none")), "poteau portant les tubes (chaînes)"),
        (lambda yy: ax.plot([x0, x0 + 1.6], [yy - 0.28] * 2, color=C_DONNEE, lw=0.6),
         "cote donnée (plan 2012, relevé du 22/09/2026)"),
        (lambda yy: ax.plot([x0, x0 + 1.6], [yy - 0.28] * 2, color=C_HYP, lw=0.6),
         "cote supposée, à mesurer sur place"),
    ]
    for draw, lab in items:
        draw(y)
        ax.text(x0 + 2.2, y - 0.28, lab, fontsize=6.2, va="center")
        y -= 1.15

    # sources
    y -= 0.9
    src = ("Enveloppe : plan de site du 12/12/2012 (29,50 · 25,50 · 35,5 ; mur du magasin\n"
           "5,00 × 9,50). Tablettes des rangs 1 à 3 : données du 22/09/2026, longueur des rangs 2-3 et 4 nefs : 06/11/2026.\n"
           f"Jeu entre tablettes supposé ({fr(JEU_X)} m), rang 1 centré. Rangs 4-5, recul,\n"
           "couloir, allées : schéma p.7 du rapport Analyse Bocage ou valeurs courantes.\n"
           "Réseau chaud/froid : photos du 22/09/2026 (rigerie_circu_eau/), une paire par\n"
           + ("rangée ; par tablette (rangs 1 à 3), départ chaud, retour au froid. En plan, chaque\n"
              if CIRCUIT == "chaud_vers_froid" else
              "rangée, un départ chaud et un froid par tablette (rangs 1 à 3). En plan, chaque\n") +
           "paire superposée est dédoublée pour la lisibilité.\n"
           "Nord non indiqué sur le plan 2012. Géométrie : bocage/plan_rigerie.py (+ DXF, CSV).")
    ax.text(x0, y, src, fontsize=5.6, va="top", color="#555", linespacing=1.45)


def ecrire_mpl(sc, tabs, poly):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pw, ph = PAGE_MM
    m_par_mm = ECHELLE / 1000
    W, H = pw * m_par_mm, ph * m_par_mm          # page en mètres réels
    x_min, y_min = -9.0, -6.5
    fig = plt.figure(figsize=(pw / 25.4, ph / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(x_min, x_min + W)
    ax.set_ylim(y_min, y_min + H)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.rcParams["hatch.linewidth"] = 0.5
    rendre_mpl(sc, ax)
    cartouche(ax, tabs, poly, x0=41.2, ytop=y_min + H - 2.2)
    OUT.mkdir(exist_ok=True)
    for ext, kw in (("pdf", {}), ("svg", {}), ("png", dict(dpi=300))):
        fig.savefig(OUT / f"plan_rigerie.{ext}", **kw)
    plt.close(fig)


# --- DXF R12 (sans dépendance) -----------------------------------------------------
def ecrire_dxf(sc, path):
    rows = []
    add = lambda code, val: rows.extend((str(code), str(val)))
    add(0, "SECTION"); add(2, "HEADER")
    add(9, "$ACADVER"); add(1, "AC1009")
    add(9, "$DWGCODEPAGE"); add(3, "ANSI_1252")
    add(9, "$INSUNITS"); add(70, 6)                       # mètres
    add(0, "ENDSEC")
    add(0, "SECTION"); add(2, "TABLES")
    add(0, "TABLE"); add(2, "LTYPE"); add(70, 3)
    add(0, "LTYPE"); add(2, "CONTINUOUS"); add(70, 0); add(3, "Solid line")
    add(72, 65); add(73, 0); add(40, 0.0)
    add(0, "LTYPE"); add(2, "DASHED"); add(70, 0); add(3, "__ __ __")
    add(72, 65); add(73, 2); add(40, 0.6); add(49, 0.4); add(49, -0.2)
    add(0, "LTYPE"); add(2, "DASHDOT"); add(70, 0); add(3, "__ . __ . __")
    add(72, 65); add(73, 4); add(40, 1.4)
    add(49, 0.8); add(49, -0.3); add(49, 0.0); add(49, -0.3)
    add(0, "ENDTAB")
    add(0, "TABLE"); add(2, "LAYER"); add(70, len(DXF_LAYERS))
    for name, (col, lt) in DXF_LAYERS.items():
        add(0, "LAYER"); add(2, name); add(70, 0); add(62, col); add(6, lt)
    add(0, "ENDTAB")
    add(0, "ENDSEC")
    add(0, "SECTION"); add(2, "ENTITIES")
    halign = {"left": 0, "center": 1, "right": 2}
    valign = {"baseline": 0, "bottom": 1, "center": 2, "top": 3}
    for kind, d in sc.items:
        if kind == "poly":
            if d["hatch"] or d.get("layer_mpl_only"):
                continue
            add(0, "POLYLINE"); add(8, d["layer"]); add(66, 1)
            add(10, 0.0); add(20, 0.0); add(30, 0.0); add(70, 1 if d["closed"] else 0)
            for x, y in d["pts"]:
                add(0, "VERTEX"); add(8, d["layer"])
                add(10, f"{x:.4f}"); add(20, f"{y:.4f}"); add(30, 0.0)
            add(0, "SEQEND"); add(8, d["layer"])
        elif kind == "arrow":
            (px, py), (qx, qy) = d["p"], d["q"]
            add(0, "LINE"); add(8, d["layer"])
            add(10, f"{px:.4f}"); add(20, f"{py:.4f}"); add(30, 0.0)
            add(11, f"{qx:.4f}"); add(21, f"{qy:.4f}"); add(31, 0.0)
        elif kind == "text" and d["dxf"]:
            h = d["pt"] * 0.3528 * 0.72 * ECHELLE / 1000   # hauteur de capitale, m réels
            lines = d["s"].split("\n")
            for i, s in enumerate(lines):
                yy = d["y"] - (i - (len(lines) - 1) / 2) * h * 1.6
                ha, va = halign[d["ha"]], valign[d["va"]]
                add(0, "TEXT"); add(8, d["layer"])
                add(10, f"{d['x']:.4f}"); add(20, f"{yy:.4f}"); add(30, 0.0)
                add(40, f"{h:.3f}")
                add(1, s.replace("≈", "~"))
                add(50, d["rot"])
                if ha or va:
                    add(72, ha); add(73, va)
                    add(11, f"{d['x']:.4f}"); add(21, f"{yy:.4f}"); add(31, 0.0)
    add(0, "ENDSEC"); add(0, "EOF")
    path.write_text("\n".join(rows) + "\n", encoding="cp1252", errors="replace")


def ecrire_csv(tabs, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "rang", "numero", "x_min", "x_max", "y_min", "y_max",
                    "dim_x", "dim_y", "surface_m2", "statut"])
        for t in tabs:
            dx, dy = t["x1"] - t["x0"], t["y1"] - t["y0"]
            w.writerow([f"R{t['rang']}-{t['num']:02d}", t["rang"], t["num"],
                        *(f"{v:.3f}" for v in (t["x0"], t["x1"], t["y0"], t["y1"], dx, dy)),
                        f"{dx * dy:.2f}", "hypothese" if t["hyp"] else "donne"])


def main():
    poly = enveloppe()
    tabs = tablettes()
    verifier(tabs, poly)
    sc = construire(tabs, poly)
    ecrire_mpl(sc, tabs, poly)
    ecrire_dxf(sc, OUT / "plan_rigerie.dxf")
    ecrire_csv(tabs, OUT / "tablettes_rigerie.csv")
    pas, jeu = pas_x()
    y = niveaux()
    print(f"aire serre {aire(poly):.1f} m² · {len(tabs)} tablettes · jeu entre tablettes "
          f"{jeu:.3f} m · bas du rang 5 à y = {y['r5'][1]:.2f} m")
    print(f"-> {OUT}/plan_rigerie.{{pdf,svg,png,dxf}}, tablettes_rigerie.csv")


if __name__ == "__main__":
    main()
