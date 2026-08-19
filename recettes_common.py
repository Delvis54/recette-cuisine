import os
import tempfile

import requests


# ------------------------------------------------------------------
# Données : 10 recettes africaines (liste de dictionnaires)
# Chaque recette : name, country, ingredients (list), steps (list), image_url
# ------------------------------------------------------------------
RECIPES = [
    {
        "name": "Thieboudienne",
        "country": "Sénégal",
        "ingredients": [
            "Riz", "Poisson (grouper ou similaire)", "Tomates", "Oignons",
            "Huile", "Carottes", "Chou"
        ],
        "steps": [
            "Préparer la sauce tomate et faire cuire le poisson.",
            "Faire mijoter les légumes dans la sauce.",
            "Ajouter le riz et cuire jusqu'à absorption.",
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/3/30/"
            "Ceebu_jenn_-_thiebou_djenn.jpg"
        )
    },
    {
        "name": "Yassa au poulet",
        "country": "Sénégal",
        "ingredients": [
            "Poulet", "Oignons", "Citron", "Moutarde", "Huile",
            "Piment (facultatif)"
        ],
        "steps": [
            "Mariner le poulet au citron et oignons.",
            "Faire dorer puis mijoter jusqu'à tendreté."
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/1/16/"
            "Poulet_yassa.jpg"
        )
    },
    {
        "name": "Mafé",
        "country": "Mali / Sénégal",
        "ingredients": [
            "Viande ou poulet", "Beurre de cacahuète", "Tomates",
            "Oignons", "Légumes"
        ],
        "steps": [
            "Préparer la sauce à la cacahuète.",
            "Cuire la viande puis mijoter dans la sauce.",
            "Servir avec du riz."
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/6/66/"
            "Mafe.jpg"
        )
    },
    {
        "name": "Attiéké",
        "country": "Côte d'Ivoire",
        "ingredients": [
            "Attiéké (manioc)", "Poisson ou viande", "Légumes", "Tomates"
        ],
        "steps": [
            "Réchauffer l'attiéké à la vapeur.",
            "Servir avec poisson frit et salade."
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/1/18/"
            "Attieke.jpg"
        )
    },
    {
        "name": "Jollof Rice",
        "country": "Afrique de l'Ouest",
        "ingredients": ["Riz", "Tomates", "Oignons", "Épices", "Huile"],
        "steps": [
            "Préparer une base tomate-épicée.",
            "Cuire le riz dans la sauce jusqu'à absorption."
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/8/8b/"
            "Jollof_rice_and_chicken.jpg"
        )
    },
    {
        "name": "Egusi",
        "country": "Nigeria",
        "ingredients": [
            "Farine d'egusi (graines)", "Légumes feuille",
            "Viande ou poisson", "Huile"
        ],
        "steps": [
            "Préparer la pâte d'egusi.", "Cuire avec légumes et protéines."
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/4/49/"
            "Egusi_Soup.jpg"
        )
    },
    {
        "name": "Tagine d'agneau",
        "country": "Maroc",
        "ingredients": [
            "Agneau", "Épices (ras el hanout)", "Fruits secs", "Légumes"
        ],
        "steps": [
            "Saisir la viande, ajouter épices et liquide.",
            "Mijoter lentement jusqu'à tendreté."
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/2/28/"
            "Tagine.jpg"
        )
    },
    {
        "name": "Bunny Chow",
        "country": "Afrique du Sud",
        "ingredients": [
            "Pain troué", "Curry (agneau ou légumes)", "Épices"
        ],
        "steps": [
            "Faire un curry épais.", "Remplir un pain évidé avec le curry."
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/b/bb/"
            "Bunny_chow.jpg"
        )
    },
    {
        "name": "Doro Wat",
        "country": "Éthiopie",
        "ingredients": [
            "Poulet", "Berbere (épice)", "Oignons", "Beurre clarifié"
        ],
        "steps": [
            "Cuire longuement les oignons lentement.",
            "Ajouter poulet et berbere, mijoter."
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/9/9b/"
            "Doro_wat.jpg"
        )
    },
    {
        "name": "Koshary",
        "country": "Égypte",
        "ingredients": [
            "Riz", "Lentilles", "Pâtes", "Sauce tomate", "Crispy onions"
        ],
        "steps": [
            "Cuire séparément riz, lentilles et pâtes.",
            "Assembler avec sauce tomate et oignons frits."
        ],
        "image_url": (
            "https://upload.wikimedia.org/wikipedia/commons/1/11/"
            "Koshary.jpg"
        )
    }
]


def slugify(name: str) -> str:
    return "".join(
        c for c in name.lower() if c.isalnum() or c == " "
    ).replace(" ", "_")


def download_image(url: str, path: str) -> bool:
    temp_path = None
    try:
        directory = os.path.dirname(os.path.abspath(path))
        prefix = f".{os.path.basename(path)}."
        fd, temp_path = tempfile.mkstemp(
            prefix=prefix, suffix=".tmp", dir=directory
        )
        os.close(fd)

        resp = requests.get(url, stream=True, timeout=15)
        resp.raise_for_status()
        with open(temp_path, "wb") as f:
            for chunk in resp.iter_content(1024):
                f.write(chunk)
        os.replace(temp_path, path)
        return True
    except Exception as e:
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        print(f"Téléchargement échoué pour {url}: {e}")
        return False


def format_recipe_label(recipe: dict) -> str:
    return f"{recipe['name']}  —  {recipe['country']}"


def format_ingredients(ingredients: list) -> str:
    return "\n".join(f"• {ingredient}" for ingredient in ingredients)


def format_steps(steps: list) -> str:
    return "\n\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1))
