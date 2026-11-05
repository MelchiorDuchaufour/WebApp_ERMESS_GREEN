// Traductions de la webapp ERMESS Green : français (référence), italien, anglais.
// Langue choisie : ?lang=xx dans l'adresse, sinon dernier choix mémorisé, sinon langue du navigateur.
// Usage : t("cle", {var: valeur}) ; éléments HTML : data-i18n="cle" (texte), data-i18n-title, data-i18n-aria,
// data-i18n-html (contenu HTML de confiance, venant de ce fichier seulement).

export const LANGUES = { fr: "FR", it: "IT", en: "EN" };

function detecter() {
  const q = new URLSearchParams(location.search).get("lang");
  if (q && LANGUES[q]) { try { localStorage.setItem("ermess.lang", q); } catch {} return q; }
  try { const m = localStorage.getItem("ermess.lang"); if (LANGUES[m]) return m; } catch {}
  const n = (navigator.language || "fr").slice(0, 2).toLowerCase();
  return LANGUES[n] ? n : "fr";
}
export const LANG = detecter();
export const LOCALE = { fr: "fr-FR", it: "it-IT", en: "en-GB" }[LANG];
// séparateurs Plotly : décimale puis milliers
export const SEPARATEURS = { fr: ", ", it: ",.", en: ".," }[LANG];

const D = {
  // ---------- commun ----------
  "commun.ermess_plus":      { fr: "En savoir plus ↗", it: "Scopri di più ↗", en: "Learn more ↗" },
  "commun.ermess_plus_long": { fr: "En savoir plus sur ERMESS Green ↗", it: "Scopri di più su ERMESS Green ↗", en: "Learn more about ERMESS Green ↗" },
  "commun.ermess_titre":     { fr: "En savoir plus sur le projet ERMESS Green", it: "Scopri di più sul progetto ERMESS Green", en: "Learn more about the ERMESS Green project" },
  "commun.partenaires":      { fr: "Partenaires", it: "Partner", en: "Partners" },
  "commun.ouvrir_site":      { fr: "{nom} : ouvrir le site", it: "{nom}: apri il sito", en: "{nom}: open website" },
  "commun.langue":           { fr: "Langue", it: "Lingua", en: "Language" },
  "commun.apercu":           { fr: "aperçu", it: "anteprima", en: "preview" },
  "commun.echec":            { fr: "Échec : {msg}", it: "Errore: {msg}", en: "Failed: {msg}" },
  "commun.tableau":          { fr: "Voir le tableau", it: "Mostra la tabella", en: "Show table" },
  "commun.hypotheses":       { fr: "Hypothèses", it: "Ipotesi", en: "Assumptions" },
  "commun.serre":            { fr: "Serre", it: "Serra", en: "Greenhouse" },
  "commun.L":                { fr: "Longueur des faîtages (m)", it: "Lunghezza dei colmi (m)", en: "Ridge length (m)" },
  "commun.W":                { fr: "Largeur totale (m)", it: "Larghezza totale (m)", en: "Total width (m)" },
  "commun.n":                { fr: "Nombre de nefs", it: "Numero di campate", en: "Number of spans" },
  "commun.h":                { fr: "Hauteur au chéneau (m)", it: "Altezza in gronda (m)", en: "Gutter height (m)" },
  "commun.pente":            { fr: "Pente de toiture (°)", it: "Pendenza della copertura (°)", en: "Roof slope (°)" },
  "commun.tmy_charge":       { fr: "Année météo type PVGIS…", it: "Anno meteorologico tipo PVGIS…", en: "PVGIS typical meteorological year…" },
  "commun.badge_base":       { fr: "Prévisualisation · version de base", it: "Anteprima · versione base", en: "Preview · base version" },
  "commun.badge_controle":   { fr: "Prévisualisation · version de contrôle", it: "Anteprima · versione di controllo", en: "Preview · control version" },
  "commun.mois":             { fr: "Mois", it: "Mese", en: "Month" },
  "commun.annee":            { fr: "Année", it: "Anno", en: "Year" },

  // ---------- accueil ----------
  "acc.titre_page":   { fr: "ERMESS Green · Serres", it: "ERMESS Green · Serre", en: "ERMESS Green · Greenhouses" },
  "acc.h1":           { fr: "Serres instrumentées France – Italie", it: "Serre strumentate Francia – Italia", en: "Instrumented greenhouses France – Italy" },
  "acc.sous":         { fr: "Capteurs Sigrow en temps réel · Interreg Alcotra ERMESS Green", it: "Sensori Sigrow in tempo reale · Interreg Alcotra ERMESS Green", en: "Real-time Sigrow sensors · Interreg Alcotra ERMESS Green" },
  "acc.chargement":   { fr: "Chargement du relief…", it: "Caricamento del rilievo…", en: "Loading terrain…" },
  "acc.aide":         { fr: "Survole une serre, clique pour l'ouvrir · glisser pour tourner, molette pour zoomer", it: "Passa sopra una serra, clicca per aprirla · trascina per ruotare, rotellina per lo zoom", en: "Hover a greenhouse, click to open it · drag to rotate, scroll to zoom" },
  "acc.source":       { fr: "Relief : Mapzen Terrarium (AWS) · Frontières : Natural Earth", it: "Rilievo: Mapzen Terrarium (AWS) · Confini: Natural Earth", en: "Terrain: Mapzen Terrarium (AWS) · Borders: Natural Earth" },
  "acc.relief_ko":    { fr: "Relief indisponible ({msg}) : carte plate.", it: "Rilievo non disponibile ({msg}): mappa piatta.", en: "Terrain unavailable ({msg}): flat map." },
  "acc.a_confirmer":  { fr: "localisation à confirmer", it: "posizione da confermare", en: "location to be confirmed" },
  "acc.mesures_charge": { fr: "Mesures en cours de chargement…", it: "Caricamento delle misure…", en: "Loading measurements…" },
  "acc.pas_capteurs": { fr: "Pas encore de capteurs connectés", it: "Nessun sensore ancora collegato", en: "No sensors connected yet" },
  "acc.actifs":       { fr: "{n}/{tot} capteurs actifs", it: "{n}/{tot} sensori attivi", en: "{n}/{tot} sensors active" },
  "acc.t_air":        { fr: "T air", it: "T aria", en: "Air T" },
  "acc.hr":           { fr: "HR", it: "UR", en: "RH" },
  "acc.indispo":      { fr: "Mesures indisponibles", it: "Misure non disponibili", en: "Measurements unavailable" },
  "acc.suisse":       { fr: "SUISSE · SVIZZERA", it: "SVIZZERA · SUISSE", en: "SWITZERLAND" },

  // ---------- vue serre : onglets ----------
  "rail.onglets":     { fr: "Onglets", it: "Schede", en: "Tabs" },
  "rail.carte":       { fr: "Carte des serres", it: "Mappa delle serre", en: "Greenhouse map" },
  "rail.suivi":       { fr: "Suivi", it: "Monitoraggio", en: "Monitoring" },
  "rail.suivi_t":     { fr: "Capteurs en temps réel dans la serre 3D", it: "Sensori in tempo reale nella serra 3D", en: "Real-time sensors in the 3D greenhouse" },
  "rail.pv":          { fr: "Potentiel PV", it: "Potenziale FV", en: "PV potential" },
  "rail.pv_t":        { fr: "Potentiel photovoltaïque en toiture", it: "Potenziale fotovoltaico in copertura", en: "Rooftop photovoltaic potential" },
  "rail.energie":     { fr: "Énergie", it: "Energia", en: "Energy" },
  "rail.energie_t":   { fr: "Besoins de chauffage", it: "Fabbisogno di riscaldamento", en: "Heating demand" },
  "rail.renovation":  { fr: "Rénovation", it: "Efficientamento", en: "Retrofit" },
  "rail.renovation_t":{ fr: "Gains d'efficacité par rénovation", it: "Guadagni di efficienza con l'efficientamento", en: "Efficiency gains from retrofit" },
  "rail.controle":    { fr: "Contrôle", it: "Controllo", en: "Control" },
  "rail.controle_t":  { fr: "Écrans, ouvrants, chauffage", it: "Schermi, aperture, riscaldamento", en: "Screens, vents, heating" },

  // ---------- vue serre : barre et panneau ----------
  "serre.titre_page": { fr: "Serre 3D · ERMESS Green", it: "Serra 3D · ERMESS Green", en: "3D greenhouse · ERMESS Green" },
  "serre.variable":   { fr: "Variable affichée", it: "Variabile visualizzata", en: "Displayed variable" },
  "serre.toit":       { fr: "Toit et vitrage", it: "Tetto e vetri", en: "Roof and glazing" },
  "serre.dessus":     { fr: "Vue de dessus", it: "Vista dall'alto", en: "Top view" },
  "serre.placer":     { fr: "Placer les capteurs", it: "Posiziona i sensori", en: "Place sensors" },
  "serre.h1":         { fr: "Capteurs Sigrow en 3D", it: "Sensori Sigrow in 3D", en: "Sigrow sensors in 3D" },
  "serre.retour":     { fr: "← Carte des serres", it: "← Mappa delle serre", en: "← Greenhouse map" },
  "serre.site":       { fr: "Site", it: "Sito", en: "Site" },
  "serre.chargement": { fr: "Chargement…", it: "Caricamento…", en: "Loading…" },
  "serre.capteurs":   { fr: "Capteurs", it: "Sensori", en: "Sensors" },
  "serre.detail":     { fr: "Détail", it: "Dettaglio", en: "Details" },
  "serre.clique":     { fr: "Clique un capteur dans la scène ou la liste.", it: "Clicca un sensore nella scena o nell'elenco.", en: "Click a sensor in the scene or the list." },
  "serre.ed_aide0":   { fr: "Clique dans la scène pour poser le capteur (x, y), puis ajuste la hauteur.", it: "Clicca nella scena per posizionare il sensore (x, y), poi regola l'altezza.", en: "Click in the scene to place the sensor (x, y), then adjust the height." },
  "serre.ed_aide":    { fr: "{nom} : clique dans la scène pour le poser (x, y), puis ajuste la hauteur z.", it: "{nom}: clicca nella scena per posizionarlo (x, y), poi regola l'altezza z.", en: "{nom}: click in the scene to place it (x, y), then adjust the height z." },
  "serre.ed_choisir": { fr: "Choisis un capteur dans la liste.", it: "Scegli un sensore nell'elenco.", en: "Choose a sensor in the list." },
  "serre.ed_save":    { fr: "Enregistrer les positions", it: "Salva le posizioni", en: "Save positions" },
  "serre.annuler":    { fr: "Annuler", it: "Annulla", en: "Cancel" },
  "serre.enreg":      { fr: "Enregistrement…", it: "Salvataggio…", en: "Saving…" },
  "serre.enregistre": { fr: "Enregistré ({maj}) dans {f}", it: "Salvato ({maj}) in {f}", en: "Saved ({maj}) to {f}" },
  "serre.hors_ligne": { fr: "hors ligne", it: "offline", en: "offline" },
  "serre.a_valider":  { fr: "position à valider", it: "posizione da validare", en: "position to be validated" },
  "serre.non_places": { fr: "Non placés : ", it: "Non posizionati: ", en: "Not placed: " },
  "serre.mesure":     { fr: "Mesure {age}", it: "Misura {age}", en: "Measured {age}" },
  "serre.aucune":     { fr: "Aucune valeur", it: "Nessun valore", en: "No value" },
  "serre.statut":     { fr: "Central {c} · {n} capteurs · {p} placés{off} · mis à jour {h}", it: "Centrale {c} · {n} sensori · {p} posizionati{off} · aggiornato alle {h}", en: "Central {c} · {n} sensors · {p} placed{off} · updated {h}" },
  "serre.statut_off": { fr: " · {n} hors ligne", it: " · {n} offline", en: " · {n} offline" },
  "serre.provisoires":{ fr: "Positions provisoires : à valider avec « Placer les capteurs »", it: "Posizioni provvisorie: da validare con «Posiziona i sensori»", en: "Provisional positions: validate them with “Place sensors”" },
  "serre.erreur_api": { fr: "Erreur API : {msg}", it: "Errore API: {msg}", en: "API error: {msg}" },
  "serre.maquette_ko":{ fr: "Maquette {m} introuvable : lancer export_glb.py dans Blender.", it: "Modello {m} non trovato: eseguire export_glb.py in Blender.", en: "Model {m} not found: run export_glb.py in Blender." },
  "serre.courbe":     { fr: "{v} ({u}) · 48 h", it: "{v} ({u}) · 48 h", en: "{v} ({u}) · 48 h" },
  "age.jamais":       { fr: "jamais", it: "mai", en: "never" },
  "age.instant":      { fr: "à l'instant", it: "adesso", en: "just now" },
  "age.min":          { fr: "il y a {n} min", it: "{n} min fa", en: "{n} min ago" },
  "age.h":            { fr: "il y a {n} h", it: "{n} h fa", en: "{n} h ago" },
  "age.j":            { fr: "il y a {n} j", it: "{n} g fa", en: "{n} d ago" },

  // variables
  "var.temp":         { fr: "T° air", it: "T aria", en: "Air temperature" },
  "var.humid":        { fr: "Humidité relative", it: "Umidità relativa", en: "Relative humidity" },
  "var.vpd":          { fr: "VPD air", it: "VPD aria", en: "Air VPD" },
  "var.par":          { fr: "PAR", it: "PAR", en: "PAR" },
  "var.pixel_object1_temp": { fr: "T° feuille", it: "T foglia", en: "Leaf temperature" },
  "var.vpd_plant":    { fr: "VPD plante", it: "VPD pianta", en: "Plant VPD" },
  "var.t_dew":        { fr: "Point de rosée", it: "Punto di rugiada", en: "Dew point" },
  "var.vbat":         { fr: "Batterie", it: "Batteria", en: "Battery" },
  "var.g_water":      { fr: "Humidité absolue", it: "Umidità assoluta", en: "Absolute humidity" },
  "var.dli":          { fr: "DLI", it: "DLI", en: "DLI" },
  "var.co2":          { fr: "CO₂", it: "CO₂", en: "CO₂" },
  "var.soil_hum":     { fr: "Humidité du sol", it: "Umidità del suolo", en: "Soil moisture" },
  "var.soil_temp":    { fr: "T° du sol", it: "T del suolo", en: "Soil temperature" },
  "var.pore_ec":      { fr: "CE solution du sol", it: "CE soluzione del suolo", en: "Soil pore-water EC" },

  // ---------- onglet énergie ----------
  "en.titre_page":    { fr: "Besoins énergétiques", it: "Fabbisogno energetico", en: "Energy demand" },
  "en.h1":            { fr: "Besoins de chauffage", it: "Fabbisogno di riscaldamento", en: "Heating demand" },
  "en.chapo":         { fr: "Bilan horaire simplifié sur une année météo type du lieu (PVGIS) : déperditions par l'enveloppe et le renouvellement d'air, moins les apports solaires utiles. Pour un ordre de grandeur et des comparaisons ; le modèle détaillé (GreenhousesJL) reste la référence.",
                        it: "Bilancio orario semplificato su un anno meteorologico tipo del sito (PVGIS): dispersioni dall'involucro e dal ricambio d'aria, meno gli apporti solari utili. Per un ordine di grandezza e dei confronti; il modello dettagliato (GreenhousesJL) resta il riferimento.",
                        en: "Simplified hourly balance over a typical meteorological year for the site (PVGIS): envelope and air-exchange losses minus useful solar gains. For orders of magnitude and comparisons; the detailed model (GreenhousesJL) remains the reference." },
  "en.enveloppe":     { fr: "Enveloppe et consignes", it: "Involucro e set-point", en: "Envelope and set-points" },
  "en.Utoit":         { fr: "U toiture (W/m²·K)", it: "U copertura (W/m²·K)", en: "Roof U-value (W/m²·K)" },
  "en.Utoit_aide":    { fr: "verre simple ≈ 6", it: "vetro singolo ≈ 6", en: "single glass ≈ 6" },
  "en.Uparois":       { fr: "U parois (W/m²·K)", it: "U pareti (W/m²·K)", en: "Wall U-value (W/m²·K)" },
  "en.ach":           { fr: "Renouvellement d'air (vol/h)", it: "Ricambio d'aria (vol/h)", en: "Air exchange (vol/h)" },
  "en.ach_aide":      { fr: "infiltrations", it: "infiltrazioni", en: "infiltration" },
  "en.tau":           { fr: "Transmission solaire", it: "Trasmissione solare", en: "Solar transmission" },
  "en.eta":           { fr: "Part solaire utile", it: "Quota solare utile", en: "Useful solar fraction" },
  "en.eta_aide":      { fr: "chaleur sensible", it: "calore sensibile", en: "sensible heat" },
  "en.Tjour":         { fr: "Consigne jour (°C)", it: "Set-point giorno (°C)", en: "Day set-point (°C)" },
  "en.Tnuit":         { fr: "Consigne nuit (°C)", it: "Set-point notte (°C)", en: "Night set-point (°C)" },
  "en.calculer":      { fr: "Calculer", it: "Calcola", en: "Compute" },
  "en.t_tot":         { fr: "Besoin annuel de chauffage", it: "Fabbisogno annuo di riscaldamento", en: "Annual heating demand" },
  "en.t_m2":          { fr: "Par m² de serre", it: "Per m² di serra", en: "Per m² of greenhouse" },
  "en.t_pointe":      { fr: "Puissance de pointe", it: "Potenza di picco", en: "Peak power" },
  "en.t_ua":          { fr: "Déperditions totales (UA + air)", it: "Dispersioni totali (UA + aria)", en: "Total losses (UA + air)" },
  "en.mensuel":       { fr: "Besoin mensuel", it: "Fabbisogno mensile", en: "Monthly demand" },
  "en.col_besoin":    { fr: "Besoin (MWh)", it: "Fabbisogno (MWh)", en: "Demand (MWh)" },
  "en.a_jour":        { fr: "Calcul à jour.", it: "Calcolo aggiornato.", en: "Calculation up to date." },
  "en.hyp":           { fr: "{nom}, {ville} ({lat}°, {lon}°). Sol {sol} m², toiture {toit} m², parois {parois} m², volume {vol} m³. Nuit = rayonnement global &lt; 10 W/m². Besoin horaire = max(0, (U·A + 0,335·n·V)(T consigne − T ext) − τ·part utile·rayonnement·surface au sol), sans inertie, sans déshumidification ni rayonnement vers le ciel : ordre de grandeur seulement.",
                        it: "{nom}, {ville} ({lat}°, {lon}°). Suolo {sol} m², copertura {toit} m², pareti {parois} m², volume {vol} m³. Notte = radiazione globale &lt; 10 W/m². Fabbisogno orario = max(0, (U·A + 0,335·n·V)(T set-point − T est) − τ·quota utile·radiazione·superficie al suolo), senza inerzia, senza deumidificazione né irraggiamento verso il cielo: solo ordine di grandezza.",
                        en: "{nom}, {ville} ({lat}°, {lon}°). Floor {sol} m², roof {toit} m², walls {parois} m², volume {vol} m³. Night = global irradiance &lt; 10 W/m². Hourly demand = max(0, (U·A + 0.335·n·V)(T set-point − T out) − τ·useful fraction·irradiance·floor area), no thermal inertia, no dehumidification or sky radiation: order of magnitude only." },

  // ---------- onglet rénovation ----------
  "ren.titre_page":   { fr: "Gains de rénovation", it: "Guadagni di efficientamento", en: "Retrofit gains" },
  "ren.h1":           { fr: "Gains d'efficacité par rénovation", it: "Guadagni di efficienza con l'efficientamento", en: "Efficiency gains from retrofit" },
  "ren.chapo":        { fr: "Économie de chauffage de chaque mesure, seule puis combinée, par rapport à la serre actuelle (même modèle horaire que l'onglet Énergie). Les valeurs d'efficacité sont des hypothèses courantes, modifiables.",
                        it: "Risparmio di riscaldamento di ogni misura, singola e poi combinata, rispetto alla serra attuale (stesso modello orario della scheda Energia). I valori di efficienza sono ipotesi correnti, modificabili.",
                        en: "Heating savings of each measure, alone and then combined, compared with the current greenhouse (same hourly model as the Energy tab). Efficiency values are common assumptions and can be edited." },
  "ren.mesures":      { fr: "Mesures", it: "Misure", en: "Measures" },
  "ren.ecran":        { fr: "Écran thermique nocturne", it: "Schermo termico notturno", en: "Night thermal screen" },
  "ren.ecran_aide":   { fr: "économie sur les déperditions de toiture la nuit :", it: "risparmio sulle dispersioni della copertura di notte:", en: "saving on night-time roof losses:" },
  "ren.double":       { fr: "Double paroi (polycarbonate)", it: "Doppia parete (policarbonato)", en: "Double wall (polycarbonate)" },
  "ren.double_aide":  { fr: "W/m²·K, transmission −10 %", it: "W/m²·K, trasmissione −10 %", en: "W/m²·K, transmission −10 %" },
  "ren.isol":         { fr: "Isolation du mur nord et des pignons", it: "Isolamento della parete nord e dei timpani", en: "Insulation of north wall and gables" },
  "ren.isol_aide":    { fr: "% des parois à U 0,5 W/m²·K", it: "% delle pareti a U 0,5 W/m²·K", en: "% of walls at U 0.5 W/m²·K" },
  "ren.etanch":       { fr: "Étanchéité à l'air", it: "Tenuta all'aria", en: "Airtightness" },
  "ren.etanch_aide":  { fr: "renouvellement ramené à", it: "ricambio ridotto a", en: "air exchange reduced to" },
  "ren.consigne":     { fr: "Consigne de nuit abaissée", it: "Set-point notturno ridotto", en: "Lower night set-point" },
  "ren.consigne_aide":{ fr: "de", it: "di", en: "by" },
  "ren.comparer":     { fr: "Comparer", it: "Confronta", en: "Compare" },
  "ren.t_base":       { fr: "Serre actuelle", it: "Serra attuale", en: "Current greenhouse" },
  "ren.t_comb":       { fr: "Avec toutes les mesures cochées", it: "Con tutte le misure selezionate", en: "With all selected measures" },
  "ren.t_gain":       { fr: "Économie combinée", it: "Risparmio combinato", en: "Combined saving" },
  "ren.graphe":       { fr: "Besoin annuel de chauffage par scénario", it: "Fabbisogno annuo di riscaldamento per scenario", en: "Annual heating demand by scenario" },
  "ren.note":         { fr: "Les économies ne s'additionnent pas : la combinaison est recalculée, pas sommée.", it: "I risparmi non si sommano: la combinazione viene ricalcolata, non sommata.", en: "Savings do not add up: the combination is recomputed, not summed." },
  "ren.n_ecran":      { fr: "Écran thermique", it: "Schermo termico", en: "Thermal screen" },
  "ren.n_double":     { fr: "Double paroi", it: "Doppia parete", en: "Double wall" },
  "ren.n_isol":       { fr: "Isolation mur nord", it: "Isolamento parete nord", en: "North wall insulation" },
  "ren.n_etanch":     { fr: "Étanchéité", it: "Tenuta all'aria", en: "Airtightness" },
  "ren.n_consigne":   { fr: "Consigne nuit", it: "Set-point notte", en: "Night set-point" },
  "ren.n_comb":       { fr: "Combinaison", it: "Combinazione", en: "Combination" },
  "ren.reference":    { fr: "référence", it: "riferimento", en: "reference" },
  "ren.col_scen":     { fr: "Scénario", it: "Scenario", en: "Scenario" },
  "ren.col_besoin":   { fr: "Besoin (MWh/an)", it: "Fabbisogno (MWh/anno)", en: "Demand (MWh/yr)" },
  "ren.col_eco":      { fr: "Économie", it: "Risparmio", en: "Saving" },
  "ren.etat":         { fr: "{ville}, serre {sol} m² (géométrie Rigerie).", it: "{ville}, serra di {sol} m² (geometria Rigerie).", en: "{ville}, {sol} m² greenhouse (Rigerie geometry)." },
  "u.mwh_an":         { fr: "MWh/an", it: "MWh/anno", en: "MWh/yr" },
  "u.kwh_m2_an":      { fr: "kWh/m²·an", it: "kWh/m²·anno", en: "kWh/m²·yr" },

  // ---------- onglet contrôle ----------
  "ctl.titre_page":   { fr: "Contrôle des actionneurs", it: "Controllo degli attuatori", en: "Actuator control" },
  "ctl.h1":           { fr: "Contrôle : écrans, ouvrants, chauffage", it: "Controllo: schermi, aperture, riscaldamento", en: "Control: screens, vents, heating" },
  "ctl.chapo":        { fr: "État des actionneurs de la serre Rigerie. Aucun signal du régulateur climatique n'est encore relié : l'état est saisi ici, enregistré par le serveur (<code>actionneurs_bocage.json</code>) et affiché en direct dans Blender (<code>blender/blender_live.py</code>). La version de contrôle reliera ces valeurs à l'automate de la serre.",
                        it: "Stato degli attuatori della serra Rigerie. Nessun segnale dal regolatore climatico è ancora collegato: lo stato viene inserito qui, salvato dal server (<code>actionneurs_bocage.json</code>) e visualizzato in diretta in Blender (<code>blender/blender_live.py</code>). La versione di controllo collegherà questi valori al controllore della serra.",
                        en: "Actuator state of the Rigerie greenhouse. No climate-controller signal is connected yet: the state is entered here, saved by the server (<code>actionneurs_bocage.json</code>) and shown live in Blender (<code>blender/blender_live.py</code>). The control version will link these values to the greenhouse controller." },
  "ctl.consignes":    { fr: "Consignes", it: "Comandi", en: "Settings" },
  "ctl.ecran":        { fr: "Écran nef {n}", it: "Schermo campata {n}", en: "Screen span {n}" },
  "ctl.ouvrants":     { fr: "Ouvrants de faîtage", it: "Aperture di colmo", en: "Ridge vents" },
  "ctl.chauffage":    { fr: "Chauffage", it: "Riscaldamento", en: "Heating" },
  "ctl.envoyer":      { fr: "Enregistrer l'état", it: "Salva lo stato", en: "Save state" },
  "ctl.nuit":         { fr: "Préréglage nuit", it: "Preimpostazione notte", en: "Night preset" },
  "ctl.jour":         { fr: "Préréglage jour chaud", it: "Preimpostazione giorno caldo", en: "Hot-day preset" },
  "ctl.coupe":        { fr: "Coupe transversale (3 nefs)", it: "Sezione trasversale (3 campate)", en: "Cross-section (3 spans)" },
  "ctl.coupe_aria":   { fr: "Coupe de la serre avec écrans et ouvrants", it: "Sezione della serra con schermi e aperture", en: "Greenhouse cross-section with screens and vents" },
  "ctl.dernier":      { fr: "Dernier enregistrement : {maj} ({src})", it: "Ultimo salvataggio: {maj} ({src})", en: "Last saved: {maj} ({src})" },
  "ctl.jamais":       { fr: "Jamais enregistré", it: "Mai salvato", en: "Never saved" },
  "ctl.enregistre":   { fr: "Enregistré. Blender le reprend au prochain rafraîchissement.", it: "Salvato. Blender lo riprende al prossimo aggiornamento.", en: "Saved. Blender picks it up at the next refresh." },
  "ctl.src_manuel":   { fr: "manuel (onglet Contrôle)", it: "manuale (scheda Controllo)", en: "manual (Control tab)" },
  "ctl.src_nuit":     { fr: "préréglage nuit", it: "preimpostazione notte", en: "night preset" },
  "ctl.src_jour":     { fr: "préréglage jour chaud", it: "preimpostazione giorno caldo", en: "hot-day preset" },
  "ctl.svg_chauffage":{ fr: "chauffage {n} %", it: "riscaldamento {n} %", en: "heating {n} %" },
  "ctl.svg_nef":      { fr: "nef {i} · écran {n} %", it: "campata {i} · schermo {n} %", en: "span {i} · screen {n} %" },
  "ctl.svg_ouv":      { fr: "ouvrants {n}°", it: "aperture {n}°", en: "vents {n}°" },
};

export function t(cle, v = {}) {
  const e = D[cle];
  let s = e ? (e[LANG] ?? e.fr) : cle;
  for (const [k, x] of Object.entries(v)) s = s.replaceAll(`{${k}}`, x);
  return s;
}

// Champs traduits d'un site de sites.json : "traductions": {"it": {"nom": …, "description": …}, "en": {…}}
export const champSite = (s, champ) => s?.traductions?.[LANG]?.[champ] ?? (champ === "description" ? s?.lieu?.description : s?.[champ]) ?? "";

// Libellés de position des capteurs (écrits en français dans capteurs_positions.json)
const MOTS = {
  it: [[/^entre (.+) et (.+)$/i, "tra $1 e $2"], [/\bExtérieur\b/, "Esterno"], [/\bFond\b/, "Fondo"], [/\bMilieu\b/, "Centro"],
       [/\bHaut\b/, "Alto"], [/\bTablette\b/, "Bancale"], [/\bNord entre rang\b/, "Nord tra le file"], [/\bSud-Bord\b/, "Bordo sud"]],
  en: [[/^entre (.+) et (.+)$/i, "between $1 and $2"], [/\bExtérieur\b/, "Outdoor"], [/\bFond\b/, "Back"], [/\bMilieu\b/, "Middle"],
       [/\bHaut\b/, "High"], [/\bTablette\b/, "Bench"], [/\bNord entre rang\b/, "North between rows"], [/\bSud-Bord\b/, "South edge"]],
};
export function libelle(s) {
  if (!s || !MOTS[LANG]) return s;
  return s.split(" · ").map(p => MOTS[LANG].reduce((a, [re, r]) => a.replace(re, r), p)).join(" · ");
}

export function appliquer(racine = document) {
  document.documentElement.lang = LANG;
  racine.querySelectorAll("[data-i18n]").forEach(e => e.textContent = t(e.dataset.i18n));
  racine.querySelectorAll("[data-i18n-html]").forEach(e => e.innerHTML = t(e.dataset.i18nHtml));
  racine.querySelectorAll("[data-i18n-title]").forEach(e => e.title = t(e.dataset.i18nTitle));
  racine.querySelectorAll("[data-i18n-aria]").forEach(e => e.setAttribute("aria-label", t(e.dataset.i18nAria)));
}

// Sélecteur FR · IT · EN : recharge la page dans la langue choisie (le choix est mémorisé).
export function selecteurLangue(conteneur) {
  conteneur.setAttribute("role", "group"); conteneur.setAttribute("aria-label", t("commun.langue"));
  conteneur.replaceChildren(...Object.entries(LANGUES).map(([code, nom]) => {
    const b = document.createElement("button"); b.type = "button"; b.textContent = nom; b.lang = code;
    b.setAttribute("aria-pressed", code === LANG);
    b.onclick = () => {
      if (code === LANG) return;
      try { localStorage.setItem("ermess.lang", code); } catch {}
      const u = new URL(location); u.searchParams.set("lang", code); location.href = u;
    };
    return b;
  }));
}

// Ajoute ?lang= à une adresse interne (iframes des onglets, liens entre pages)
export function avecLangue(url) {
  const u = new URL(url, location.href); u.searchParams.set("lang", LANG); return u.href;
}
