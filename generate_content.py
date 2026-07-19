import json
import os
import re
from datetime import date, datetime
from pathlib import Path

try:
    import google.generativeai as genai
except Exception:
    genai = None

ROOT = Path(__file__).resolve().parent
THEMES_PATH = ROOT / "themes.json"
OUTPUT_DIR = ROOT / "content" / "posts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AFFILIATE_TAG = "equivalencepro-21"
MODEL_NAME = "gemini-2.5-flash"


def load_themes() -> list[str]:
    with THEMES_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("themes", [])


def choose_theme(themes: list[str]) -> str:
    start_date = date(2024, 1, 1)
    delta_days = (date.today() - start_date).days
    return themes[delta_days % len(themes)]


def build_prompt(theme: str) -> str:
    return f"""Tu es un copywriter SEO français spécialisé en affiliation Amazon.
Rédige un guide d'achat complet sur le thème suivant : {theme}.
Exigences :
- Longueur cible : 2500 mots.
- Structure Markdown avec H1, H2 et H3.
- Ajouter un tableau comparatif.
- Optimiser le contenu pour le SEO avec une introduction forte, des sous-titres riches et une conclusion orientée conversion.
- Intégrer au moins trois produits distincts avec leurs ASIN sous forme de codes alphanumériques de 10 caractères, par exemple B0ABC12345.
- Ajouter une section FAQ et une section avis rapide.
- Termine par une synthèse finale orientée achat.
- Réponds uniquement avec du Markdown prêt à publier.
"""


def format_affiliate_links(text: str) -> str:
    pattern = re.compile(r"\b([A-Z0-9]{10})\b")

    def replace(match: re.Match[str]) -> str:
        asin = match.group(1)
        return f"[{asin}](https://www.amazon.fr/dp/{asin}/?tag={AFFILIATE_TAG})"

    return pattern.sub(replace, text)


def fallback_content(theme: str) -> str:
    return f"""# Guide d'achat complet : {theme}

## Introduction
Le marché de {theme.lower()} regorge d'options, ce qui rend le choix difficile. Ce guide a pour objectif de vous aider à identifier les critères essentiels, les points de vigilance et les produits qui offrent le meilleur rapport qualité-prix.

## Pourquoi ce guide est utile
Les produits de {theme.lower()} varient en fonction de la qualité de fabrication, de la finition, de l'autonomie et du support client. Une bonne décision d'achat repose sur une comparaison claire des caractéristiques les plus importantes.

## Tableau comparatif

| Produit | Points forts | Limites | ASIN |
| --- | --- | --- | --- |
| Modèle premium | Performance, durabilité, finition | Prix plus élevé | B0PREMIUM12 |
| Modèle milieu de gamme | Bon rapport qualité-prix | Moins de réglages | B0MIDRANGE34 |
| Modèle compact | Facile à transporter | Capacité plus limitée | B0COMPACT56 |

## Critères de sélection
### Performance
Privilégiez les modèles qui offrent une bonne autonomie, des matériaux durables et une expérience utilisateur fluide.

### Valeur à long terme
Un produit économique au départ peut coûter plus cher à l'usage s'il nécessite des réparations fréquentes.

### Confort d'utilisation
Testez la simplicité de mise en route, la qualité du support et l'ergonomie générale.

## Recommandations
Voici trois options à considérer selon votre budget et votre usage quotidien.

### Recommandation 1
Le modèle premium est idéal si vous recherchez la meilleure qualité de fabrication et une expérience sans compromis. Consultez ce produit via son lien affilié : B0PREMIUM12.

### Recommandation 2
Le modèle milieu de gamme reste un excellent choix pour les utilisateurs qui veulent un bon rapport qualité-prix sans trop dépenser. Retrouvez-le ici : B0MIDRANGE34.

### Recommandation 3
Le modèle compact convient parfaitement aux petits espaces ou aux déplacements fréquents. Découvrez-le ici : B0COMPACT56.

## FAQ
### Quel modèle choisir ?
Choisissez le modèle premium si vous souhaitez la meilleure expérience, ou le milieu de gamme si vous recherchez un excellent compromis.

### Est-ce que ces produits sont adaptés à un usage intensif ?
Oui, à condition de vérifier la garantie, la disponibilité des pièces et les notes clients avant l'achat.

## Conclusion
Pour un achat réussi dans le domaine de {theme.lower()}, il faut comparer les fonctions essentielles, la durabilité et le prix. Le meilleur choix dépend de votre budget, de votre niveau d'exigence et de l'usage que vous voulez en faire.
"""


def generate_content(theme: str) -> tuple[str, str]:
    prompt = build_prompt(theme)

    if genai is not None and os.getenv("GEMINI_API_KEY"):
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(prompt)
            body = response.text.strip()
        except Exception:
            body = fallback_content(theme)
    else:
        body = fallback_content(theme)

    formatted_body = format_affiliate_links(body)
    first_asin_match = re.search(r"https://www\.amazon\.fr/dp/([A-Z0-9]{10})/\?tag=equivalencepro-21", formatted_body)
    if first_asin_match:
        affiliate_link = f"https://www.amazon.fr/dp/{first_asin_match.group(1)}/?tag={AFFILIATE_TAG}"
    else:
        affiliate_link = f"https://www.amazon.fr/?tag={AFFILIATE_TAG}"

    return formatted_body, affiliate_link


def write_post(theme: str, body: str, affiliate_link: str) -> None:
    slug = re.sub(r"[^a-z0-9]+", "-", theme.lower()).strip("-") or "guide-achat"
    file_path = OUTPUT_DIR / f"{slug}.md"
    date_stamp = datetime.now().strftime("%Y-%m-%d")
    content = f"""---
title: "Guide d'achat : {theme}"
date: {date_stamp}
draft: false
description: "Guide d'achat SEO et orienté conversion pour {theme.lower()}."
tags: [affiliation, amazon, guides]
slug: "{slug}"
affiliate_link: "{affiliate_link}"
---

{body}
"""
    file_path.write_text(content, encoding="utf-8")


def main() -> None:
    themes = load_themes()
    if not themes:
        raise SystemExit("No themes found in themes.json")

    theme = choose_theme(themes)
    body, affiliate_link = generate_content(theme)
    write_post(theme, body, affiliate_link)
    print(f"Generated content for theme: {theme}")


if __name__ == "__main__":
    main()
