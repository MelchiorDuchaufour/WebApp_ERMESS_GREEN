#!/usr/bin/env python3
"""
placer_selon_plan.py — Positions 3D des capteurs du central 15353 d'après le
schéma « Plan Sigrow.png » (~/doctorat/webapp/), dans le repère de plan_rigerie.py.

1. Détecte les symboles par couleur et forme :
     carré magenta = Pixel+, triangle magenta = AirPro+,
     rond violet = SoilPro+, triangle violet = Air+   (la légende est ignorée).
2. Détecte les tablettes (fonds gris) et cale l'image sur plan_rigerie.py :
   x par une droite par rang (bords des tablettes), y par morceaux entre les
   bords des rangs. Le schéma n'est pas à l'échelle en y : seule la position
   relative aux tablettes compte.
3. Hauteurs : SoilPro+ dans le substrat sur tablette, Pixel+ au niveau des
   feuilles, Air+ puis AirPro+ au-dessus. Deux capteurs très proches sur le plan
   (< 55 px, soit moins de 2 symboles) sont supposés superposés : même (x, y),
   au moins 0,4 m d'écart en z.
4. Les identifiants sont attribués par type, dans l'ordre de lecture du plan
   (haut-gauche -> bas-droite) et par numéro croissant : le schéma ne les donne
   pas, l'attribution est donc À VALIDER sur place.

Écrit/complète capteurs_positions.json (les capteurs Bocage déjà placés sont gardés).

    python3 placer_selon_plan.py [--plan "~/doctorat/webapp/Plan Sigrow.png"] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import requests
from PIL import Image
from scipy import ndimage

ICI = Path(__file__).resolve().parent
TABLETTES = ICI.parent / "plan_rigerie" / "tablettes_rigerie.csv"
POSITIONS = ICI / "capteurs_positions.json"
Z_TABLETTE = 0.80
Z_TYPE = {"soilpro": 0.90, "pixel": 1.10, "air": 1.60, "airpro": 2.20}
NOM_TYPE = {"soilpro": "SoilPro+", "pixel": "Pixel+", "air": "Air+", "airpro": "AirPro+"}
PROCHES_PX, ECART_Z = 55, 0.4      # px sur le schéma (symbole ≈ 30 px) ; m


def detecter(chemin):
    im = np.asarray(Image.open(chemin).convert("RGB")).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    H, W = r.shape
    mag = (r > 170) & (g < 80) & (b > 170)
    vio = (r > 80) & (r < 150) & (g < 90) & (b > 120) & (b < 200)
    symb = []
    for couleur, m in (("magenta", mag), ("violet", vio)):
        lab, n = ndimage.label(m)
        for i in range(1, n + 1):
            ys, xs = np.where(lab == i)
            if len(xs) < 150:
                continue
            w, h = np.ptp(xs) + 1, np.ptp(ys) + 1
            fill = len(xs) / (w * h)
            forme = "carre" if fill > 0.9 else "triangle" if fill < 0.6 else "rond"
            typ = {("magenta", "carre"): "pixel", ("magenta", "triangle"): "airpro",
                   ("violet", "rond"): "soilpro", ("violet", "triangle"): "air"}.get((couleur, forme))
            cx, cy = xs.mean(), ys.mean()
            if typ is None or cy > 0.88 * H and 0.38 * W < cx < 0.68 * W:   # légende
                continue
            symb.append({"type": typ, "px": float(cx), "py": float(cy)})
    grey = (abs(r - g) < 8) & (abs(g - b) < 8) & (r > 205) & (r < 240)
    lab, _ = ndimage.label(grey)
    tabs = []
    for sl in ndimage.find_objects(lab):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        if x1 - x0 > 50 and y1 - y0 > 40:
            tabs.append((x0, x1, y0, y1))
    return symb, tabs


def caler(tabs_img):
    """Associe chaque rangée de tablettes de l'image à un rang réel."""
    reel = {}
    for t in csv.DictReader(TABLETTES.open()):
        reel.setdefault(int(t["rang"]), []).append(
            (float(t["x_min"]), float(t["x_max"]), float(t["y_min"]), float(t["y_max"])))
    # rangées de l'image, de haut en bas (rang 1 en haut, comme sur le plan)
    bandes = []
    for t in sorted(tabs_img, key=lambda t: t[2]):
        if bandes and abs(t[2] - bandes[-1][0][2]) < 20:
            bandes[-1].append(t)
        else:
            bandes.append([t])
    if len(bandes) != 5:
        sys.exit(f"{len(bandes)} rangées détectées au lieu de 5 : vérifier le plan")
    rangs = []
    for k, bande in enumerate(bandes, start=1):
        img = sorted(bande)                         # gauche -> droite
        vrai = sorted(reel[k])
        if len(img) != len(vrai):
            sys.exit(f"rang {k} : {len(img)} tablettes sur l'image, {len(vrai)} dans le CSV")
        xi = [v for t in img for v in (t[0], t[1])]
        xr = [v for t in vrai for v in (t[0], t[1])]
        a, b0 = np.polyfit(xi, xr, 1)
        yi0, yi1 = np.median([t[2] for t in img]), np.median([t[3] for t in img])
        rangs.append({"rang": k, "ax": a, "bx": b0, "yi": (yi0, yi1),
                      "yr": (max(t[3] for t in vrai), min(t[2] for t in vrai))})
    return rangs


def vers_plan(px, py, rangs):
    # y : par morceaux entre bords de rangs (image vers le bas = y réel décroissant)
    pts_i, pts_r = [], []
    for r in rangs:
        pts_i += list(r["yi"]); pts_r += list(r["yr"])
    y = float(np.interp(py, pts_i, pts_r))
    # x : droite du rang le plus proche verticalement
    r = min(rangs, key=lambda r: 0 if r["yi"][0] <= py <= r["yi"][1]
            else min(abs(py - r["yi"][0]), abs(py - r["yi"][1])))
    dedans = [q["rang"] for q in rangs if q["yi"][0] - 4 <= py <= q["yi"][1] + 4]
    if dedans:
        lieu = f"R{dedans[0]}"
    else:
        haut = max((q for q in rangs if q["yi"][1] < py), key=lambda q: q["yi"][1], default=None)
        bas = min((q for q in rangs if q["yi"][0] > py), key=lambda q: q["yi"][0], default=None)
        lieu = f"entre R{haut['rang']} et R{bas['rang']}" if haut and bas else f"bord R{r['rang']}"
    return r["ax"] * px + r["bx"], y, lieu


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=str(Path.home() / "doctorat/webapp/Plan Sigrow.png"))
    ap.add_argument("--central", type=int, default=15353)
    ap.add_argument("--cle", default="SIGROW_API_KEY_15353")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    symb, tabs = detecter(args.plan)
    rangs = caler(tabs)
    for s in symb:
        s["x"], s["y"], s["rang"] = vers_plan(s["px"], s["py"], rangs)
        s["z"] = Z_TYPE[s["type"]]

    # capteurs proches SUR L'IMAGE -> superposés. Le schéma n'est pas à l'échelle
    # en y (un rang de 3,2 m et un de 8,8 m y ont la même hauteur) : la proximité
    # se juge donc en pixels. Un groupe prend le (x, y) de son capteur le plus bas
    # (SoilPro+ ou Pixel+, posé sur la tablette) et ses membres sont empilés en z.
    parent = list(range(len(symb)))
    def racine(i):
        while parent[i] != i:
            i = parent[i]
        return i
    for i, s in enumerate(symb):
        for j, t in enumerate(symb[:i]):
            if np.hypot(s["px"] - t["px"], s["py"] - t["py"]) < PROCHES_PX:
                parent[racine(i)] = racine(j)
    groupes = {}
    for i, s in enumerate(symb):
        groupes.setdefault(racine(i), []).append(s)
    for membres in groupes.values():
        membres.sort(key=lambda s: Z_TYPE[s["type"]])
        base = membres[0]
        for k, s in enumerate(membres):
            s["groupe"] = len(membres) - 1
            s["x"], s["y"], s["rang"] = base["x"], base["y"], base["rang"]
            if k:
                s["z"] = round(max(s["z"], membres[k - 1]["z"] + ECART_Z), 2)

    # identifiants : par type, ordre de lecture du plan
    sys.path.insert(0, str(ICI))
    from serveur_3d import lire_cles  # noqa: E402
    import os
    cle = os.environ.get(args.cle) or lire_cles().get(args.cle)
    devs = requests.get(f"https://api3.sigrow.com/v3/partners/central/{args.central}/data/latest/",
                        headers={"X-API-Key": cle}, timeout=30).json()
    ids = {}
    for d in devs:
        ids.setdefault(d["device_type"], []).append(d["id"])
    caps = {}
    for typ in Z_TYPE:
        sur_plan = sorted((s for s in symb if s["type"] == typ), key=lambda s: (round(s["py"] / 40), s["px"]))
        dispo = sorted(ids.get(typ, []))
        if len(sur_plan) != len(dispo):
            print(f"! {typ} : {len(sur_plan)} sur le plan, {len(dispo)} sur le central")
        for s, rid in zip(sur_plan, dispo):
            caps[str(rid)] = {"x": round(s["x"], 2), "y": round(s["y"], 2), "z": s["z"],
                              "label": f"{NOM_TYPE[typ]} {rid} · {s['rang']}",
                              "a_valider": True, "source": args.central}
            print(f"{NOM_TYPE[typ]:9s} {rid:>6}  image ({s['px']:4.0f},{s['py']:4.0f})  ->  "
                  f"x {s['x']:5.2f}  y {s['y']:5.2f}  z {s['z']:.2f}  {s['rang']}"
                  + ("  (superposé)" if s["groupe"] else ""))
    if args.dry_run:
        return
    cur = json.loads(POSITIONS.read_text(encoding="utf-8"))
    cur["capteurs"].update(caps)
    cur["note_15353"] = ("Capteurs du central 15353 placés par placer_selon_plan.py d'après « Plan Sigrow.png ». "
                         "Attribution des identifiants à un symbole arbitraire (par type, ordre de lecture) : à valider.")
    POSITIONS.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"-> {len(caps)} capteurs écrits dans {POSITIONS.name}")


if __name__ == "__main__":
    main()
