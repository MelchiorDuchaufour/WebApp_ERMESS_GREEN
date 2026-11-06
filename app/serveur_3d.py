#!/usr/bin/env python3
"""
serveur_3d.py — Vue 3D en continu des capteurs Sigrow, plusieurs sites.

Chaque site (sites.json) a son central, sa clé API, une maquette 3D facultative
et son fichier de positions. Chaque capteur est un point à sa position réelle,
coloré par sa dernière mesure. Pas de champ interpolé.

Lancer :
  source ../env.sh                 # clé Bocage (SIGROW_API_KEY)
  python3 serveur_3d.py            # port 8766 -> http://localhost:8766
  python3 serveur_3d.py --hote 0.0.0.0     # ouvert au réseau local

Clés : variable d'environnement nommée dans sites.json (champ "cle"), sinon
le fichier local .cles_sigrow (NOM=clé, chmod 600, à ne pas partager).

Routes (toutes prennent ?site=<id>) :
  GET  /                    accueil : carte France–Italie, mini-serres cliquables
  GET  /serre#<site>        vue 3D d'un site (onglets : suivi, PV, énergie, contrôle)
  GET/POST /api/actionneurs écrans, ouvrants, chauffage (lu par blender/blender_live.py)
  GET  /api/pv, /api/tmy    passerelles PVGIS (JRC) : production PV, année météo type
  GET  /api/sites           liste des sites (sans les clés)
  GET  /api/latest          dernières mesures (cache 60 s, repli si l'API tombe)
  GET  /api/capteurs        positions enregistrées
  POST /api/capteurs        enregistre les positions (mode édition)
  GET  /api/series          historique : &remotes=..&var=..&hours=..
  GET  /modele/<fichier>    maquette .glb ;  GET /logos/<fichier>  logos
"""
from __future__ import annotations

import argparse
import json
import os
import re
import threading
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import requests

ICI = Path(__file__).resolve().parent
BASE = "https://api3.sigrow.com/v3/partners"
PARIS, UTC = ZoneInfo("Europe/Paris"), ZoneInfo("UTC")
QFMT = "%Y%m%dT%H%M%SZ"
TTL_LATEST = 60.0
SITES: dict[str, dict] = {}
_LOCKS: dict[str, threading.Lock] = {}
_LAT: dict[str, dict] = {}
_SERIES: dict[tuple, list] = {}          # (site, rid) -> lignes triées par temps
_ORIGINE: dict[str, dict] = {}           # site -> {rid: source} (quelle clé interroge ce capteur)
MIME = {".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml",
        ".glb": "model/gltf-binary",
        ".js": "text/javascript; charset=utf-8",
        ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8"}


# ---------------------------------------------------------------- config
def lire_cles() -> dict:
    cles = {}
    f = ICI / ".cles_sigrow"
    if f.exists():
        for ligne in f.read_text().splitlines():
            m = re.match(r"\s*([A-Za-z0-9_]+)\s*=\s*(\S+)", ligne)
            if m and not ligne.lstrip().startswith("#"):
                cles[m.group(1)] = m.group(2)
    return cles


INFOS: dict[str, dict] = {}            # tous les sites de sites.json, même sans capteurs


def charger_sites():
    """Un site = une serre, alimentée par une ou plusieurs sources (central + clé)."""
    conf = json.loads((ICI / "sites.json").read_text(encoding="utf-8"))
    fichier = lire_cles()
    for sid, s in conf.items():
        INFOS[sid] = s
        sources = []
        for src in s.get("sources", []):
            src["_cle"] = os.environ.get(src["cle"]) or fichier.get(src["cle"])
            if src["_cle"]:
                sources.append(src)
            else:
                print(f"[{sid}] clé {src['cle']} absente : central {src['central']} ignoré")
        s["_sources"] = sources
        s["actif"] = bool(sources)
        if sources:
            SITES[sid] = s
            _LOCKS[sid] = threading.Lock()
            _ORIGINE[sid] = {}


def site(q) -> tuple[str, dict]:
    sid = q.get("site", [next(iter(SITES))])[0]
    if sid not in SITES:
        raise KeyError(f"site inconnu : {sid}")
    return sid, SITES[sid]


def _get(s, chemin, params=None, timeout=30):
    err = None
    for essai in range(2):                    # l'API coupe parfois la connexion
        try:
            r = requests.get(f"{BASE}{chemin}", params=params, timeout=timeout,
                             headers={"X-API-Key": s["_cle"], "Accept": "application/json"})
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            err = e
            time.sleep(1.5)
    raise RuntimeError(f"API Sigrow injoignable : {err}")


def _float(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- mesures
def latest(sid: str) -> dict:
    s = SITES[sid]
    with _LOCKS[sid]:
        c = _LAT.get(sid)
        if c and time.time() - c["t"] < TTL_LATEST:
            return c["data"]
        suivis = set(lire_positions(sid)["capteurs"])
        out, erreurs = {}, []
        for src in s["_sources"]:
            try:
                devs = _get(src, f"/central/{src['central']}/data/latest/")
            except RuntimeError as e:
                erreurs.append(f"central {src['central']} : {e}")
                if c:                                        # on garde ses dernières valeurs
                    out.update({r: v for r, v in c["data"]["remotes"].items() if v["central"] == src["central"]})
                continue
            for dev in devs:
                rid = str(dev["id"])
                if src.get("filtre") and src["filtre"].lower() not in (dev.get("name") or "").lower() \
                        and rid not in suivis:
                    continue
                _ORIGINE[sid][rid] = src
                out[rid] = _lecture(dev, src["central"])
        if not out and erreurs:
            raise RuntimeError(" ; ".join(erreurs))
        data = {"site": sid, "centrals": [src["central"] for src in s["_sources"]], "remotes": out,
                "updated": datetime.now(PARIS).strftime("%Y-%m-%dT%H:%M:%S%z")}
        if erreurs:
            data["erreur"] = " ; ".join(erreurs) + " — valeurs précédentes"
        _LAT[sid] = {"t": time.time() - (TTL_LATEST - 15 if erreurs else 0), "data": data}
        return data


def _lecture(dev, central) -> dict:
    rd = dev.get("readings") or {}
    data = rd.get("data", [])
    return {
        "name": dev.get("name"), "type": dev.get("device_type"), "central": central,
        "location": dev.get("physical_location"),
        "date": (rd.get("date") or dev.get("last_reading_date") or {}).get("in_centrals_timezone"),
        "values": {d["name"]: _float(d.get("value")) for d in data},
        "units": {d["name"]: d.get("unit") for d in data},
    }


def _tirer(s, rid, debut, fin) -> list:
    """Toutes les variables numériques d'un capteur sur [debut, fin), par tranches de 3 j."""
    lignes, t0 = [], debut
    while t0 < fin:
        t1 = min(t0 + timedelta(days=3), fin)
        j = _get(s, f"/remote/{rid}/data/", {"after": t0.astimezone(UTC).strftime(QFMT),
                                             "before": t1.astimezone(UTC).strftime(QFMT)}, 60)
        for rd in j.get("readings", []):
            t = datetime.fromisoformat(rd["date"]["in_gmt_timezone"]).astimezone(PARIS)
            vals = {k: _float(v) for k, v in rd.items() if k not in ("id", "date")}
            lignes.append((t, vals))
        t0 = t1
    return lignes


def series(sid, rid, var, heures) -> dict:
    if rid not in _ORIGINE[sid]:
        latest(sid)
    s = _ORIGINE[sid].get(rid)
    if s is None:
        raise KeyError(f"capteur {rid} inconnu sur ce site")
    besoin = datetime.now(PARIS) - timedelta(hours=heures)
    fin = datetime.now(PARIS) + timedelta(minutes=10)
    with _LOCKS[sid]:
        cur = _SERIES.get((sid, rid))
    if not cur or cur[0][0] > besoin:
        cur = _tirer(s, rid, besoin, fin)       # premier appel ou fenêtre élargie
    else:
        cur = cur + _tirer(s, rid, cur[-1][0] - timedelta(minutes=10), fin)
    vu, propre = set(), []
    for t, v in sorted(cur, key=lambda x: x[0]):
        if t not in vu:
            vu.add(t)
            propre.append((t, v))
    with _LOCKS[sid]:
        _SERIES[(sid, rid)] = propre
    pts = [(t, v.get(var)) for t, v in propre if t >= besoin and v.get(var) is not None]
    return {"t": [t.strftime("%Y-%m-%dT%H:%M:%S%z") for t, _ in pts], "y": [y for _, y in pts]}


# ---------------------------------------------------------------- positions
def _fichier_pos(sid) -> Path:
    return ICI / SITES[sid]["positions"]


def lire_positions(sid) -> dict:
    f = _fichier_pos(sid)
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {"capteurs": {}}


def disposer_par_defaut(sid):
    """Site sans positions : range les capteurs par type sur une grille, à valider."""
    if _fichier_pos(sid).exists():
        return
    devs = latest(sid)["remotes"]
    hauteur = {"pixel": 1.0, "air": 2.0, "airpro": 2.0, "soilpro": 0.05}
    larg = SITES[sid].get("emprise", [20, 20])[0]
    caps, y = {}, 2.0
    for typ in ("pixel", "air", "airpro", "soilpro"):
        ids = sorted((r for r, d in devs.items() if d["type"] == typ), key=int)
        for i, rid in enumerate(ids):
            x = (i + 1) * larg / (len(ids) + 1)
            caps[rid] = {"x": round(x, 2), "y": y, "z": hauteur[typ],
                         "label": devs[rid]["name"], "a_valider": True}
        if ids:
            y += 4.0
    autres = [r for r in devs if r not in caps]
    for i, rid in enumerate(autres):
        caps[rid] = {"x": 2.0 + 2 * i, "y": y, "z": 1.0, "label": devs[rid]["name"], "a_valider": True}
    ecrire_positions(sid, {"capteurs": caps},
                     note="Disposition automatique par type (rangées Pixel+, Air+, AirPro+, SoilPro+) : "
                          "positions fictives, à remplacer dans la page (mode édition).")


def ecrire_positions(sid, payload, note=None) -> dict:
    caps = payload.get("capteurs")
    if not isinstance(caps, dict):
        raise ValueError("champ 'capteurs' manquant")
    propres = {}
    for rid, c in caps.items():
        int(rid)
        x, y, z = (float(c[k]) for k in ("x", "y", "z"))
        if not (-50 <= x <= 80 and -50 <= y <= 90 and -1 <= z <= 15):
            raise ValueError(f"position hors limites pour {rid}")
        propres[str(rid)] = {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3),
                             "label": str(c.get("label", ""))[:40],
                             "a_valider": bool(c.get("a_valider", False))}
    with _LOCKS[sid]:
        cur = lire_positions(sid)
        if note:
            cur["note"] = note
        cur["capteurs"] = propres
        cur["maj"] = datetime.now(PARIS).strftime("%Y-%m-%d %H:%M")
        f = _fichier_pos(sid)
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(f)
    return cur


# ---------------------------------------------------------------- actionneurs
ACT_DEFAUT = {"ecrans": [0.0, 0.0, 0.0, 0.0], "ouvrants_deg": 0.0, "chauffage": 0.0,
              "source": "manuel", "maj": None}


def _fichier_act(sid) -> Path:
    return ICI / f"actionneurs_{sid}.json"


def lire_actionneurs(sid) -> dict:
    f = _fichier_act(sid)
    return {**ACT_DEFAUT, **(json.loads(f.read_text(encoding="utf-8")) if f.exists() else {})}


def ecrire_actionneurs(sid, d) -> dict:
    ec = [min(1.0, max(0.0, float(x))) for x in d.get("ecrans", [])][:6]
    out = {"ecrans": ec or ACT_DEFAUT["ecrans"],
           "ouvrants_deg": min(45.0, max(0.0, float(d.get("ouvrants_deg", 0)))),
           "chauffage": min(1.0, max(0.0, float(d.get("chauffage", 0)))),
           "source": str(d.get("source", "manuel"))[:30],
           "maj": datetime.now(PARIS).strftime("%Y-%m-%d %H:%M:%S")}
    tmp = _fichier_act(sid).with_suffix(".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_fichier_act(sid))
    return out


# ---------------------------------------------------------------- PVGIS (JRC)
PVGIS = "https://re.jrc.ec.europa.eu/api/v5_3"
_PV_CACHE: dict[str, dict] = {}
CACHE_DIR = ICI / "donnees" / "cache_pvgis"


def pvgis(outil: str, params: dict) -> dict:
    """Passerelle PVGIS (pas de CORS côté JRC), cache mémoire + disque."""
    params = {**{k: v for k, v in params.items() if v not in (None, "")}, "outputformat": "json"}
    cle = outil + "_" + "_".join(f"{k}={params[k]}" for k in sorted(params))
    if cle in _PV_CACHE:
        return _PV_CACHE[cle]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    f = CACHE_DIR / (re.sub(r"[^A-Za-z0-9_.=-]", "_", cle) + ".json")
    if f.exists():
        d = json.loads(f.read_text())
    else:
        r = requests.get(f"{PVGIS}/{outil}", params=params, timeout=90)
        if r.status_code != 200:
            raise RuntimeError(f"PVGIS {r.status_code} : {r.text[:200]}")
        d = r.json()
        if outil == "tmy":      # on ne garde que ce qui sert : T air et rayonnement horaire
            h = d["outputs"]["tmy_hourly"]
            d = {"T2m": [x["T2m"] for x in h], "Gh": [x["G(h)"] for x in h],
                 "WS10m": [x["WS10m"] for x in h], "meta": d.get("inputs", {}).get("location", {})}
        f.write_text(json.dumps(d))
    _PV_CACHE[cle] = d
    return d


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _statique(self, dossier: Path, nom: str):
        p = (dossier / nom).resolve()
        if p.parent != dossier.resolve() or not p.is_file():   # pas de ../
            return self._send(404, json.dumps({"error": "absent"}))
        return self._send(200, p.read_bytes(), MIME.get(p.suffix.lower(), "application/octet-stream"))

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/":
                return self._send(200, (ICI / "accueil.html").read_bytes(), "text/html; charset=utf-8")
            if u.path in ("/serre", "/serre.html"):
                return self._send(200, (ICI / "index.html").read_bytes(), "text/html; charset=utf-8")
            if u.path.startswith("/logos/"):
                return self._statique(ICI / "logos", u.path[len("/logos/"):])
            if u.path.startswith("/donnees/carte/"):
                return self._statique(ICI / "donnees" / "carte", u.path[len("/donnees/carte/"):])
            if u.path.startswith("/modele/"):
                nom = u.path[len("/modele/"):]
                if nom not in {s.get("modele") for s in INFOS.values()}:
                    return self._send(404, json.dumps({"error": "absent"}))
                return self._statique(ICI, nom)
            if u.path == "/api/sites":
                return self._send(200, json.dumps({sid: {
                    **{k: v for k, v in s.items() if not k.startswith("_") and k != "sources"},
                    "centrals": [src["central"] for src in s.get("_sources", [])]}
                    for sid, s in INFOS.items()}))
            if u.path == "/api/pv":
                keep = ("lat", "lon", "peakpower", "loss", "angle", "aspect")
                return self._send(200, json.dumps(pvgis("PVcalc", {k: q[k][0] for k in keep if k in q})))
            if u.path == "/api/tmy":
                return self._send(200, json.dumps(pvgis("tmy", {k: q[k][0] for k in ("lat", "lon") if k in q})))
            if u.path.startswith("/onglets/"):
                return self._statique(ICI / "onglets", u.path[len("/onglets/"):])
            if u.path == "/api/actionneurs":
                sid = q.get("site", ["bocage"])[0]
                if sid not in INFOS:
                    raise KeyError(f"site inconnu : {sid}")
                return self._send(200, json.dumps(lire_actionneurs(sid)))
            sid, _ = site(q)
            if u.path == "/api/latest":
                return self._send(200, json.dumps(latest(sid)))
            if u.path == "/api/capteurs":
                return self._send(200, json.dumps(lire_positions(sid)))
            if u.path == "/api/series":
                var = q.get("var", ["temp"])[0]
                heures = min(float(q.get("hours", ["48"])[0]), 24 * 31)
                rids = [r for r in q.get("remotes", [""])[0].split(",") if r.isdigit()]
                return self._send(200, json.dumps({"var": var, "series": {
                    r: series(sid, r, var, heures) for r in rids}}))
            return self._send(404, json.dumps({"error": "not found"}))
        except Exception as e:
            return self._send(500, json.dumps({"error": str(e)}))

    def do_POST(self):
        u = urlparse(self.path)
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n > 200_000:
                raise ValueError("requête trop grosse")
            corps = json.loads(self.rfile.read(n) or b"{}")
            q = parse_qs(u.query)
            if u.path == "/api/actionneurs":
                sid = q.get("site", ["bocage"])[0]
                if sid not in INFOS:
                    raise KeyError(f"site inconnu : {sid}")
                return self._send(200, json.dumps(ecrire_actionneurs(sid, corps)))
            if u.path != "/api/capteurs":
                return self._send(404, json.dumps({"error": "not found"}))
            sid, _ = site(q)
            return self._send(200, json.dumps(ecrire_positions(sid, corps)))
        except Exception as e:
            return self._send(400, json.dumps({"error": str(e)}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--hote", default="127.0.0.1", help="0.0.0.0 pour l'ouvrir au réseau local")
    args = ap.parse_args()
    charger_sites()
    if not SITES:
        raise SystemExit("aucun site utilisable : vérifier les clés (source ../env.sh, .cles_sigrow)")
    for sid, s in SITES.items():
        try:
            disposer_par_defaut(sid)
            n = len(latest(sid)["remotes"])
            print(f"[{sid}] {s['nom']} : centrals {', '.join(str(x['central']) for x in s['_sources'])}, {n} capteurs")
        except Exception as e:
            print(f"[{sid}] {s['nom']} : API indisponible au démarrage ({e})")
    for sid, s in INFOS.items():
        if not s["actif"]:
            print(f"[{sid}] {s['nom']} : pas de capteurs connectés (affiché sur la carte seulement)")
    print(f"ouvrir  http://localhost:{args.port}")
    ThreadingHTTPServer((args.hote, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
