// Outils communs aux onglets de prévisualisation (PV, énergie, rénovation, contrôle).
// Modèle volontairement simple : ordres de grandeur pour l'outil de calcul ERMESS
// Green (WP3.4). Le calcul détaillé reste celui de GreenhousesJL.

import { LOCALE, SEPARATEURS, champSite } from "/onglets/i18n.js";
export const SITE_DEFAUT = "bocage";

export async function lieuDuSite(sid = SITE_DEFAUT) {
  const sites = await (await fetch("/api/sites")).json();
  const s = sites[sid] || Object.values(sites)[0];
  return { ...s.lieu, nom: champSite(s, "nom"), description: champSite(s, "description") };
}

// Géométrie d'une serre multi-chapelles rectangulaire.
// L : longueur le long des faîtages (m), W : largeur totale (m), n : nombre de nefs,
// h : hauteur au chéneau (m), pente : pente de toiture (°).
export function geometrie({ L, W, n, h, pente }) {
  const w = W / n, t = Math.tan(pente * Math.PI / 180);
  const pan = (w / 2) / Math.cos(pente * Math.PI / 180);       // longueur d'un pan
  const hf = (w / 2) * t;                                       // hauteur faîtage - chéneau
  const sol = L * W;
  const toit = 2 * n * L * pan;
  const panParCote = n * L * pan;                               // tous les pans d'un même côté
  const murs = 2 * (L + W) * h;
  const pignons = 2 * n * 0.5 * w * hf;
  const volume = sol * h + n * 0.5 * w * hf * L;
  return { w, pan, hf, sol, toit, panParCote, murs, pignons, parois: murs + pignons, volume, enveloppe: toit + murs + pignons };
}

export const RIGERIE = { L: 29.5, W: 35.5, n: 3, h: 4.0, pente: 23 };   // plan_rigerie.py

// Besoin de chauffage horaire sur une année météo type (PVGIS TMY).
// p : { Utoit, Uparois, ach, tau, eta, Tjour, Tnuit, ecran (0..1 d'économie la nuit sur la toiture),
//       fracIsol, Uisol }  ;  g : geometrie()
export function besoinChauffage(tmy, g, p) {
  const H_inf = 0.335 * p.ach * g.volume;                       // W/K (ρ·cp/3600)
  const Aiso = g.parois * (p.fracIsol || 0);
  const UAparois = (g.parois - Aiso) * p.Uparois + Aiso * (p.Uisol ?? p.Uparois);
  const mois = new Array(12).fill(0);
  let total = 0, pointe = 0;
  const jours = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let h = 0;
  for (let m = 0; m < 12; m++) for (let k = 0; k < jours[m] * 24; k++, h++) {
    const Te = tmy.T2m[h], G = tmy.Gh[h];
    const nuit = G < 10;
    const Ttoit = p.Utoit * g.toit * (nuit ? 1 - (p.ecran || 0) : 1);
    const Tc = nuit ? p.Tnuit : p.Tjour;
    const pertes = (Ttoit + UAparois + H_inf) * (Tc - Te);
    const gains = p.tau * p.eta * g.sol * G;
    const q = Math.max(0, pertes - gains);                       // W
    mois[m] += q / 1000; total += q / 1000; pointe = Math.max(pointe, q / 1000);
  }
  return { mois, total, pointe, parM2: total / g.sol };
}

export const PARAM_BASE = { Utoit: 6.0, Uparois: 6.0, ach: 1.0, tau: 0.80, eta: 0.5, Tjour: 16, Tnuit: 12,
                            ecran: 0, fracIsol: 0, Uisol: 0.5 };

export async function tmy(lat, lon) {
  const r = await fetch(`/api/tmy?lat=${lat}&lon=${lon}`);
  const j = await r.json(); if (j.error) throw new Error(j.error); return j;
}

export async function pvgis(lat, lon, angle, aspect, loss = 14) {
  const r = await fetch(`/api/pv?lat=${lat}&lon=${lon}&peakpower=1&loss=${loss}&angle=${angle}&aspect=${aspect}`);
  const j = await r.json(); if (j.error) throw new Error(j.error); return j;
}

export const MOIS = Array.from({ length: 12 }, (_, m) => new Date(2001, m, 15).toLocaleString(LOCALE, { month: "short" }));
export const fmt = (v, d = 0) => v.toLocaleString(LOCALE, { maximumFractionDigits: d, minimumFractionDigits: d });

// Graphique en barres à une série, couleurs prises dans les jetons CSS de la page.
export function barres(el, x, y, { unite, titre, survol, couleurs } = {}) {
  const css = getComputedStyle(document.documentElement), v = k => css.getPropertyValue(k).trim();
  Plotly.react(el, [{
    type: "bar", x, y, marker: { color: couleurs || v("--serie"), cornerradius: 4 },
    hovertemplate: survol || `%{x} : %{y:,.0f} ${unite || ""}<extra></extra>`,
  }], {
    margin: { l: 56, r: 12, t: titre ? 30 : 10, b: 40 }, bargap: 0.35,
    title: titre ? { text: titre, font: { size: 13 }, x: 0, xanchor: "left" } : undefined,
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", separators: SEPARATEURS,
    font: { color: v("--ink"), size: 12, family: "system-ui, sans-serif" },
    xaxis: { showgrid: false, linecolor: v("--line"), tickfont: { color: v("--muted") } },
    yaxis: { gridcolor: v("--line"), zeroline: false, tickfont: { color: v("--muted") },
             title: { text: unite || "", font: { size: 11, color: v("--muted") } }, separatethousands: true },
    hoverlabel: { bgcolor: v("--panel"), bordercolor: v("--line"), font: { color: v("--ink") } },
  }, { displayModeBar: false, responsive: true });
}

// Tableau HTML (vue accessible des graphiques)
export function tableau(el, entetes, lignes) {
  el.innerHTML = `<table><thead><tr>${entetes.map(h => `<th>${h}</th>`).join("")}</tr></thead><tbody>${
    lignes.map(l => `<tr>${l.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}
