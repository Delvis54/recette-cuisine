import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from recettes_common import (
    RECIPES,
    download_image,
    format_ingredients,
    format_recipe_label,
    format_steps,
    slugify,
)

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
os.makedirs(IMAGES_DIR, exist_ok=True)


def local_image_path(recipe: dict) -> str:
    name = slugify(recipe["name"]) + ".jpg"
    return os.path.join(IMAGES_DIR, name)


def ensure_image(recipe: dict) -> str:
    path = local_image_path(recipe)
    if os.path.exists(path):
        return path
    # essayer de télécharger
    url = recipe.get("image_url")
    if url:
        ok = download_image(url, path)
        if ok:
            return path
    # fallback : créer une image placeholder
    placeholder = Image.new("RGB", (800, 600), (200, 200, 200))
    placeholder.save(path, "JPEG")
    return path


# UI Application
class RecipeApp(tk.Tk):
    def __init__(self, recipes):
        super().__init__()
        self.title("Recettes africaines – Mini application")
        self.geometry("900x600")
        self.recipes = recipes
        self.pil_images = [None] * len(recipes)  # stocke PIL images originales
        self.tk_images = {}  # cache des PhotoImage pour affichage

        self._build_ui()
        self._load_images()
        self.recipe_listbox.selection_set(0)
        self.show_recipe(0)

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Barre latérale
        sidebar = ttk.Frame(self)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.columnconfigure(0, weight=1)

        lbl = ttk.Label(sidebar, text="Recettes", font=(None, 12, "bold"))
        lbl.pack(padx=6, pady=(6, 0))

        self.recipe_listbox = tk.Listbox(sidebar, width=28, activestyle="none")
        for r in self.recipes:
            self.recipe_listbox.insert(tk.END, format_recipe_label(r))
        self.recipe_listbox.pack(fill="y", expand=True, padx=6, pady=6)
        self.recipe_listbox.bind("<<ListboxSelect>>", self._on_select)

        # Zone principale
        main = ttk.Frame(self)
        main.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # Image
        self.image_label = ttk.Label(main)
        self.image_label.grid(row=0, column=0, sticky="nsew")

        # Split ingredients / préparation
        bottom = ttk.Frame(main)
        bottom.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)

        ing_frame = ttk.LabelFrame(bottom, text="Ingrédients")
        ing_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        prep_frame = ttk.LabelFrame(bottom, text="Préparation")
        prep_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.ing_text = tk.Text(ing_frame, wrap="word", height=12)
        self.ing_text.pack(fill="both", expand=True, padx=6, pady=6)
        self.ing_text.configure(state="disabled")

        self.prep_text = tk.Text(prep_frame, wrap="word", height=12)
        self.prep_text.pack(fill="both", expand=True, padx=6, pady=6)
        self.prep_text.configure(state="disabled")

        # Bind resize to refresh image
        self.image_label.bind("<Configure>", lambda e: self._refresh_image())

    def _load_images(self):
        for idx, r in enumerate(self.recipes):
            path = ensure_image(r)
            try:
                img = Image.open(path).convert("RGB")
            except Exception:
                img = Image.new("RGB", (800, 600), (200, 200, 200))
            self.pil_images[idx] = img

    def _on_select(self, event):
        sel = event.widget.curselection()
        if not sel:
            return
        idx = sel[0]
        self.show_recipe(idx)

    def show_recipe(self, idx: int):
        r = self.recipes[idx]
        # ingrédients
        self.ing_text.configure(state="normal")
        self.ing_text.delete("1.0", tk.END)
        ingredients = format_ingredients(r.get("ingredients", []))
        if ingredients:
            self.ing_text.insert(tk.END, ingredients + "\n")
        self.ing_text.configure(state="disabled")

        # préparation
        self.prep_text.configure(state="normal")
        self.prep_text.delete("1.0", tk.END)
        steps = format_steps(r.get("steps", []))
        if steps:
            self.prep_text.insert(tk.END, steps + "\n\n")
        self.prep_text.configure(state="disabled")

        # image
        self.current_index = idx
        self._refresh_image()

    def _refresh_image(self):
        idx = getattr(self, "current_index", 0)
        pil_img = self.pil_images[idx]
        if pil_img is None:
            return
        # calc target size based on label size
        w = self.image_label.winfo_width() or 400
        h = int(self.winfo_height() * 0.4) or 300
        # maintain aspect ratio
        img = pil_img.copy()
        img.thumbnail((w, h), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        # avoid garbage collection
        self.tk_images[idx] = tk_img
        self.image_label.configure(image=tk_img)


def main():
    app = RecipeApp(RECIPES)
    app.mainloop()


if __name__ == "__main__":
    main()
