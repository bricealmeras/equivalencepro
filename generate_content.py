import json
import os
import re
from datetime import date, datetime
from pathlib import Path

try:
    from google import genai
except Exception:
    genai = None

ROOT = Path(__file__).resolve().parent
THEMES_PATH = ROOT / "themes.json"
PRODUCTS_PATH = ROOT / "products.json"
OUTPUT_DIR = ROOT / "content" / "posts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AFFILIATE_TAG = os.getenv("AFFILIATE_TAG", "equivalencepro-21")
MODEL_NAME = "gemini-3.5-flash"


def load_themes() -> list[str]:
    with THEMES_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("themes", [])


def load_products() -> list[dict[str, str]]:
    if not PRODUCTS_PATH.exists():
        return []
    with PRODUCTS_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("products", [])


def choose_theme(themes: list[str]) -> str:
    start_date = date(2024, 1, 1)
    delta_days = (date.today() - start_date).days
    return themes[delta_days % len(themes)]


def build_prompt(title: str, theme: str, products: list[dict[str, str]]) -> str:
    prompt = [
        "Tu es un copywriter SEO français spécialisé en affiliation Amazon.",
        f"Rédige un article d'achat expert pour le produit suivant : {title}.",
        f"Le guide doit être optimisé pour la catégorie : {theme}.",
        "Exigences :",
        "- Longueur cible : 2000 mots.",
        "- Structure Markdown avec H1, H2 et H3.",
        "- Ajouter un tableau comparatif.",
        "- Optimiser le contenu pour le SEO avec une introduction claire, des sous-titres riches et une conclusion orientée conversion.",
        "- Ajouter une section FAQ et une section avis rapide.",
        "- Inclure un bloc de comparaison entre le produit principal et deux produits concurrents.",
        "- Réponds uniquement avec du Markdown prêt à publier."
    ]

    if products:
        prompt.append("Utilise les produits suivants et leurs ASIN dans le guide :")
        for product in products:
            name = product.get("name", "Produit inconnu")
            asin = product.get("asin", "B000000000")
            highlights = product.get("highlights", [])
            prompt.append(f"- {name} (ASIN : {asin}).")
            if highlights:
                prompt.append(f"  Points clés : {', '.join(highlights)}.")
        prompt.append("N'inclus pas de liens Amazon complets dans la réponse. Je vais convertir les ASINs en liens affiliés corrects après génération.")
        prompt.append("N'utilise pas d'ASIN fictifs si des ASIN produit sont fournis.")

    return "\n".join(prompt) + "\n"


def format_affiliate_links(text: str) -> str:
    # Force every Amazon /dp/ URL to use the affiliate tag exactly once.
    text = re.sub(
        r"https://www\.amazon\.fr/dp/([A-Z0-9]{10})(?:/)?(?:\?[^\s\)]*)?",
        lambda m: f"https://www.amazon.fr/dp/{m.group(1)}/?tag={AFFILIATE_TAG}",
        text,
    )

    # Convert plain ASIN mentions into affiliate markdown links.
    def wrap_asin(match: re.Match[str]) -> str:
        asin = match.group(1)
        before = match.string[max(0, match.start() - 10) : match.start()]
        after = match.string[match.end() : match.end() + 10]

        if "/dp/" in before or "/dp/" in after:
            return asin
        if before.endswith("[") or after.startswith("]("):
            return asin

        return f"[{asin}](https://www.amazon.fr/dp/{asin}/?tag={AFFILIATE_TAG})"

    return re.sub(r"(?<![A-Z0-9/\[\]\(])([A-Z0-9]{10})(?![A-Z0-9/\]\)])", wrap_asin, text)


def fallback_content(title: str, theme: str, products: list[dict[str, str]]) -> str:
    if products:
        product_lines = "\n".join(
            f"| {item.get('name', 'Produit')} | {', '.join(item.get('highlights', ['Bon rapport qualité-prix']))} | À vérifier | {item.get('asin', 'B000000000')} |"
            for item in products[:3]
        )
        return f"""# Guide d'achat : {title}

## Introduction
Le marché de {theme.lower()} est vaste, ce qui rend le choix d'un produit adapté difficile. Ce guide présente le produit principal et compare ses forces avec d'autres alternatives similaires.

## Produits comparés
| Produit | Points forts | Limites | ASIN |
| --- | --- | --- | --- |
{product_lines}

## Pourquoi ce produit ?
{title} se distingue par ses caractéristiques clés et sa valeur d'usage. Nous passons en revue ses principaux atouts, les points à surveiller et les recommandations d'utilisation.

## Critères d'achat
### Performance
Privilégiez les produits avec une connectivité fiable, une installation facile et un support durable.

### Qualité et design
Un bon produit connecté doit offrir une interface intuitive, une bonne finition et une intégration fluide avec les assistants vocaux.

### Rapport qualité-prix
Comparez les fonctionnalités, la durée de vie et les avis clients avant de choisir.

## Recommandations
### Produit principal
{title} est recommandé pour les utilisateurs qui veulent une expérience fluide et une compatibilité large.

### Alternatives
Les autres produits présentés dans le tableau sont de bonnes alternatives selon votre budget et vos besoins.

## FAQ
### Pourquoi ce produit est-il intéressant ?
Il combine fonctionnalités avancées, facilité d'utilisation et design moderne.

### Est-ce un bon achat Amazon ?
Oui, si vous cherchez un produit adapté à votre thème et capable de s'intégrer dans un environnement connecté.

## Conclusion
Pour un achat réussi dans le domaine de {theme.lower()}, focalisez-vous sur la qualité, la compatibilité et la durabilité du produit. {title} est une option sérieuse dans cette catégorie.
"""
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


def product_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "produit"


def filter_products_by_theme(products: list[dict[str, str]], theme: str) -> list[dict[str, str]]:
    return [product for product in products if product.get("category", "").lower() == theme.lower()]


def generate_content(title: str, theme: str, products: list[dict[str, str]]) -> tuple[str, str]:
    prompt = build_prompt(title, theme, products)
    print(f"Generating content for product: {title} in theme: {theme}")
    print(f"Using {len(products)} products for comparison")

    use_api = genai is not None and os.getenv("GEMINI_API_KEY")
    if use_api:
        print("Gemini API key detected. Generating with Gemini.")
    else:
        print("Gemini API unavailable. Using fallback content.")

    if use_api:
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.interactions.create(
                model=MODEL_NAME,
                input=prompt,
            )
            body = response.output_text.strip()
            print("Gemini content generation succeeded.")
        except Exception as exc:
            print(f"Gemini generation failed: {exc}")
            body = fallback_content(title, theme, products)
            print("Fallback content generated.")
    else:
        body = fallback_content(title, theme, products)

    formatted_body = format_affiliate_links(body)
    first_asin_match = re.search(rf"https://www\.amazon\.fr/dp/([A-Z0-9]{{10}})/\?tag={AFFILIATE_TAG}", formatted_body)
    if first_asin_match:
        affiliate_link = f"https://www.amazon.fr/dp/{first_asin_match.group(1)}/?tag={AFFILIATE_TAG}"
    else:
        affiliate_link = f"https://www.amazon.fr/?tag={AFFILIATE_TAG}"

    return formatted_body, affiliate_link


def write_post(title: str, theme: str, body: str, affiliate_link: str) -> None:
    slug = product_slug(title)
    file_path = OUTPUT_DIR / f"{slug}.md"
    date_stamp = datetime.now().strftime("%Y-%m-%d")
    content = f"""---
title: "Guide d'achat : {title}"
date: {date_stamp}
draft: false
description: "Guide d'achat SEO et orienté conversion pour {title}."
tags: [affiliation, amazon, guides]
category: "{theme}"
slug: "{slug}"
affiliate_link: "{affiliate_link}"
---

{body}
"""
    file_path.write_text(content, encoding="utf-8")


def main() -> None:
    themes = load_themes()
    products = load_products()
    if not themes:
        raise SystemExit("No themes found in themes.json")

    theme = choose_theme(themes)
    theme_products = filter_products_by_theme(products, theme)
    if not theme_products:
        print(f"Aucun produit réel trouvé pour le thème {theme}. Génération de contenu générique.")
        body, affiliate_link = generate_content(theme, theme, [])
        write_post(theme, theme, body, affiliate_link)
        return

    for product in theme_products:
        related = [p for p in theme_products if p != product][:2]
        body, affiliate_link = generate_content(product.get("name", "Produit"), theme, [product] + related)
        write_post(product.get("name", "Produit"), theme, body, affiliate_link)
    print(f"Generated {len(theme_products)} product articles for theme: {theme}")


if __name__ == "__main__":
    main()
