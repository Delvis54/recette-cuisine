# Application de recettes africaines (Tkinter)

Mini-application Python (Tkinter) affichant 10 recettes africaines.

Caractéristiques :
- Données stockées dans une liste de dictionnaires (nom, pays, ingrédients, étapes, image_url).
- Vérifie si une image existe dans `images/`; sinon télécharge l'image via `requests` et la stocke.
- Interface avec barre latérale (liste des plats) et zone principale (image, ingrédients, préparation).
- Utilise `Pillow` pour redimensionner les images.

Installation :
1. Crée un environnement virtuel (optionnel) :
   python -m venv venv; .\venv\Scripts\Activate
2. Installer les dépendances :
   pip install -r requirements.txt

Usage :
  python recettes_tk.py

Notes :
- Les URLs d'images sont fournies dans les données; si le téléchargement échoue une image placeholder est utilisée.
- N'hésite pas à remplacer les URLs dans `recettes_tk.py` par des images de ton choix.
