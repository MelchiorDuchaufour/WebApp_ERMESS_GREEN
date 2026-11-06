// Liens des logos (accueil et vue d'un site). Un lien vide = logo non cliquable.
import { t } from "../onglets/i18n.js";
export const ERMESS = "https://www.univ-smb.fr/locie/2025/12/15/ermess-green-project";
// e : coefficient de hauteur, pour que les logos larges et les logos carrés paraissent de même importance.
export const PARTENAIRES = [
  { img: "logos/interreg.png",    alt: "Interreg Alcotra",              e: 0.66, url: "https://www.interreg-alcotra.eu/" },
  { img: "logos/usmb.png",        alt: "Université Savoie Mont Blanc",  e: 0.77, url: "https://www.univ-smb.fr/" },
  { img: "logos/locie.png",       alt: "LOCIE",                         e: 1, url: "https://www.univ-smb.fr/locie/" },
  { img: "logos/unige.png",       alt: "Università di Genova",          e: 0.62, url: "https://unige.it/" },
  { img: "logos/dime.png",        alt: "DIME, Università di Genova",    e: 0.78, url: "https://dime.unige.it/" },
  { img: "logos/agrithermic.png", alt: "Agrithermic",                   e: 1, url: "" },   // adresse à fournir
];
export function remplirPartenaires(conteneur) {
  conteneur.replaceChildren(...PARTENAIRES.map(p => {
    const img = Object.assign(document.createElement("img"), { src: p.img, alt: p.alt, title: p.alt });
    img.style.setProperty("--e", p.e);
    if (!p.url) return img;
    const a = Object.assign(document.createElement("a"), { href: p.url, target: "_blank", rel: "noopener" });
    a.title = t("commun.ouvrir_site", { nom: p.alt }); a.append(img); return a;
  }));
}
