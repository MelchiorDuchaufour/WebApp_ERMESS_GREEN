#!/usr/bin/env python3
"""
construire.py : fabrique la version statique de la webapp pour GitHub Pages.

  python3 statique/construire.py _site        (depuis le dossier app/)

1. copie les pages : accueil.html -> index.html, index.html -> serre.html, onglets/, logos/, maquette ;
2. ajoute statique.js en tête de chaque page (lecture des JSON au lieu du serveur, écritures bloquées) ;
3. interroge Sigrow et PVGIS avec le code du serveur (serveur_3d.py) et écrit api_statique/*.json :
   sites, dernières mesures, positions, actionneurs, historiques 48 h (toutes variables), années météo type.

Clés Sigrow : variables d'environnement nommées dans sites.json (secrets GitHub dans la tâche Actions),
sinon le fichier local .cles_sigrow. Elles ne sont jamais écrites dans le site produit.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP))
import serveur_3d as S  # noqa: E402

HEURES = 48


def nombre(x: float) -> str:
    """Même écriture qu'un nombre JavaScript (45.566 -> '45.566', 45.0 -> '45')."""
    s = repr(float(x))
    return s[:-2] if s.endswith(".0") else s


def ecrire(f: Path, d) -> None:
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def injecter(html: str, chemin_script: str) -> str:
    balise = f'<script src="{chemin_script}"></script>'
    assert "<head>" in html
    return html.replace("<head>", "<head>\n" + balise, 1)


def pages(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / ".nojekyll").write_text("")
    shutil.copy(APP / "statique" / "statique.js", out / "statique.js")
    (out / "index.html").write_text(injecter((APP / "accueil.html").read_text(encoding="utf-8"), "statique.js"), encoding="utf-8")
    (out / "serre.html").write_text(injecter((APP / "index.html").read_text(encoding="utf-8"), "statique.js"), encoding="utf-8")
    for dossier in ("logos", "onglets"):
        shutil.copytree(APP / dossier, out / dossier, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.py"))
    for f in (out / "onglets").glob("*.html"):
        f.write_text(injecter(f.read_text(encoding="utf-8"), "../statique.js"), encoding="utf-8")
    (out / "modele").mkdir(exist_ok=True)
    for s in S.INFOS.values():
        if s.get("modele"):
            shutil.copy(APP / s["modele"], out / "modele" / s["modele"])


def donnees(out: Path) -> list[str]:
    api, notes = out / "api_statique", []
    ecrire(api / "sites.json", {sid: {**{k: v for k, v in s.items() if not k.startswith("_") and k != "sources"},
                                      "centrals": [src["central"] for src in s.get("_sources", [])]}
                                for sid, s in S.INFOS.items()})
    for sid, s in S.INFOS.items():
        ecrire(api / f"actionneurs_{sid}.json", S.lire_actionneurs(sid))
        lieu = s.get("lieu") or {}
        if "lat" in lieu:
            try:
                ecrire(api / f"tmy_{nombre(lieu['lat'])}_{nombre(lieu['lon'])}.json",
                       S.pvgis("tmy", {"lat": lieu["lat"], "lon": lieu["lon"]}))
            except Exception as e:                       # PVGIS en panne : les onglets le signalent
                notes.append(f"[{sid}] PVGIS : {e}")
    for sid in S.SITES:
        ecrire(api / f"capteurs_{sid}.json", S.lire_positions(sid))
        lat = S.latest(sid)
        ecrire(api / f"latest_{sid}.json", lat)
        debut = datetime.now(S.PARIS) - timedelta(hours=HEURES)
        fin = datetime.now(S.PARIS) + timedelta(minutes=10)
        for rid in lat["remotes"]:
            src = S._ORIGINE[sid].get(rid)
            if src is None:
                continue
            try:
                lignes = sorted(S._tirer(src, rid, debut, fin), key=lambda x: x[0])
            except Exception as e:
                notes.append(f"[{sid}] historique {rid} : {e}")
                continue
            vu, par_var = set(), {}
            for t, vals in lignes:
                if t in vu:
                    continue
                vu.add(t)
                ts = t.strftime("%Y-%m-%dT%H:%M:%S%z")
                for k, v in vals.items():
                    if v is not None:
                        d = par_var.setdefault(k, {"t": [], "y": []})
                        d["t"].append(ts); d["y"].append(v)
            ecrire(api / f"series_{sid}_{rid}.json", par_var)
        notes.append(f"[{sid}] {len(lat['remotes'])} capteurs, maj {lat['updated']}")
    return notes


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "_site").resolve()
    S.charger_sites()
    pages(out)
    for n in donnees(out):
        print(n)
    # garde-fou : aucune clé Sigrow ne doit se retrouver dans le site
    cles = [src["_cle"] for s in S.SITES.values() for src in s["_sources"] if src.get("_cle")]
    for f in out.rglob("*"):
        if f.is_file() and f.suffix in (".json", ".html", ".js"):
            texte = f.read_text(encoding="utf-8", errors="ignore")
            if any(c in texte for c in cles):
                raise SystemExit(f"ARRÊT : une clé Sigrow apparaît dans {f}")
    print(f"site statique prêt : {out}")


if __name__ == "__main__":
    main()
