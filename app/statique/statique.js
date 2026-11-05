// Mode statique (GitHub Pages) : le site n'a pas de serveur Python.
// Ce script, chargé avant les autres, détourne les appels /api/... vers les fichiers JSON
// produits toutes les ~15 min par la tâche GitHub Actions (statique/construire.py).
// Les écritures (positions des capteurs, onglet Contrôle) sont désactivées.
(function () {
  "use strict";
  window.ERMESS_STATIQUE = true;
  const vrai = window.fetch.bind(window);
  const racine = new URL(".", document.currentScript.src).pathname;          // racine du site
  const lang = (() => {
    const q = new URLSearchParams(location.search).get("lang");
    if (q) return q;
    try { const m = localStorage.getItem("ermess.lang"); if (m) return m; } catch {}
    return (navigator.language || "fr").slice(0, 2);
  })();
  const MSG = {
    fr: { bandeau: "Version publique · lecture seule · mesures mises à jour toutes les 15 min environ",
          ecriture: "Version publique en lecture seule : enregistrement désactivé.", indispo: "Donnée indisponible en version publique." },
    it: { bandeau: "Versione pubblica · sola lettura · misure aggiornate circa ogni 15 min",
          ecriture: "Versione pubblica in sola lettura: salvataggio disattivato.", indispo: "Dato non disponibile nella versione pubblica." },
    en: { bandeau: "Public version · read-only · measurements updated about every 15 min",
          ecriture: "Public read-only version: saving is disabled.", indispo: "Data not available in the public version." },
  }[lang] || null;
  const M = MSG || { bandeau: "", ecriture: "Read-only", indispo: "Unavailable" };
  const json = (o, code = 200) => new Response(JSON.stringify(o), { status: code, headers: { "Content-Type": "application/json" } });
  // évite le cache de GitHub Pages (10 min) : paramètre qui change chaque minute
  const fichier = nom => vrai(`${racine}api_statique/${nom}?v=${Math.floor(Date.now() / 60000)}`);

  window.fetch = async (entree, opts = {}) => {
    const u = new URL(typeof entree === "string" ? entree : entree.url, location.href);
    const m = u.origin === location.origin && u.pathname.match(/\/api\/(\w+)$/);
    if (!m) return vrai(entree, opts);
    if ((opts.method || "GET").toUpperCase() !== "GET") return json({ error: M.ecriture }, 403);
    const q = u.searchParams, site = (q.get("site") || "bocage").replace(/\W/g, "");
    switch (m[1]) {
      case "sites": return fichier("sites.json");
      case "latest": return fichier(`latest_${site}.json`);
      case "capteurs": return fichier(`capteurs_${site}.json`);
      case "actionneurs": return fichier(`actionneurs_${site}.json`);
      case "tmy": return fichier(`tmy_${+q.get("lat")}_${+q.get("lon")}.json`);
      case "series": {
        const v = q.get("var") || "temp", depuis = Date.now() - (+q.get("hours") || 48) * 3600e3, out = {};
        for (const r of (q.get("remotes") || "").split(",").filter(x => /^\d+$/.test(x))) {
          try {
            const s = (await (await fichier(`series_${site}_${r}.json`)).json())[v] || { t: [], y: [] };
            const k = s.t.findIndex(t => new Date(t).getTime() >= depuis);
            out[r] = k < 0 ? { t: [], y: [] } : { t: s.t.slice(k), y: s.y.slice(k) };
          } catch { out[r] = { t: [], y: [] }; }
        }
        return json({ var: v, series: out });
      }
      default: return json({ error: M.indispo }, 404);
    }
  };

  // interface : pas d'édition, curseurs du Contrôle figés, bandeau sur la page principale
  const css = document.createElement("style");
  css.textContent = `#b-edit,#edition,#envoyer,#nuit,#jour{display:none!important}
    input[type=range]{pointer-events:none;opacity:.55}
    #mode-statique{position:fixed;z-index:40;right:12px;bottom:12px;max-width:calc(100% - 24px);font:12px/1.3 system-ui,sans-serif;
      color:#5f4a12;background:#fff4d6;border:1px solid #e8cf8a;border-radius:10px;padding:4px 10px;pointer-events:none}
    @media (prefers-color-scheme: dark){#mode-statique{color:#f3dfa5;background:#3a3220;border-color:#6b5a2e}}`;
  document.head.appendChild(css);
  addEventListener("DOMContentLoaded", () => {
    if (window.top !== window) return;                    // onglets en iframe : bandeau dans la page parente
    const b = document.createElement("div"); b.id = "mode-statique"; b.textContent = M.bandeau;
    if (document.getElementById("partenaires") && document.getElementById("titre")) b.style.bottom = "104px";   // accueil
    document.body.appendChild(b);
  });
})();
