// Liens des logos (accueil et vue d'un site). Un lien vide = logo non cliquable.
export const ERMESS = "https://www.univ-smb.fr/locie/2025/12/15/ermess-green-project";
export const PARTENAIRES = [
  { img: "/logos/interreg.png",    alt: "Interreg Alcotra",              url: "https://www.interreg-alcotra.eu/" },
  { img: "/logos/usmb.png",        alt: "Université Savoie Mont Blanc",  url: "https://www.univ-smb.fr/" },
  { img: "/logos/locie.png",       alt: "LOCIE",                         url: "https://www.univ-smb.fr/locie/" },
  { img: "/logos/unige.png",       alt: "Università di Genova",          url: "https://unige.it/" },
  { img: "/logos/dime.png",        alt: "DIME, Università di Genova",    url: "https://dime.unige.it/" },
  { img: "/logos/agrithermic.png", alt: "Agrithermic",                   url: "" },   // adresse à fournir
];
export function remplirPartenaires(conteneur) {
  conteneur.replaceChildren(...PARTENAIRES.map(p => {
    const img = Object.assign(document.createElement("img"), { src: p.img, alt: p.alt, title: p.alt });
    if (!p.url) return img;
    const a = Object.assign(document.createElement("a"), { href: p.url, target: "_blank", rel: "noopener" });
    a.title = `${p.alt} : ouvrir le site`; a.append(img); return a;
  }));
}
