from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.logger import Logger
import hashlib
import os
import requests
import threading
from urllib.parse import urlparse

# Minimal copy of recipes (keeps file self-contained)
RECIPES = [
    {
        "name": "Thieboudienne",
        "country": "Sénégal",
        "ingredients": ["Riz", "Poisson (grouper ou similaire)", "Tomates", "Oignons", "Huile", "Carottes", "Chou"],
        "steps": [
            "Préparer la sauce tomate et faire cuire le poisson.",
            "Faire mijoter les légumes dans la sauce.",
            "Ajouter le riz et cuire jusqu'à absorption.",
        ],
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/3/30/Ceebu_jenn_-_thiebou_djenn.jpg",
    },
    # ... (truncated for brevity in prototype) copy the rest as needed
]


class RecipeList(GridLayout):
    def __init__(self, recipes, select_callback, **kwargs):
        super().__init__(cols=1, spacing=6, size_hint_y=None, **kwargs)
        self.bind(minimum_height=self.setter('height'))
        self.recipes = recipes
        self.select_callback = select_callback
        for i, r in enumerate(self.recipes):
            text = f"{r['name']}  —  {r['country']}"
            btn = Button(text=text, size_hint_y=None, height=44)
            btn.recipe_index = i
            btn.bind(on_release=self._on_press)
            self.add_widget(btn)

    def _on_press(self, btn):
        idx = btn.recipe_index
        self.select_callback(idx)


class DetailView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=8, **kwargs)
        self.image = AsyncImage(size_hint_y=0.5, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.image)

        self.ing_label = Label(text='', halign='left', valign='top')
        self.ing_label.bind(size=self._update_ing_text_size)
        ing_scroll = ScrollView()
        ing_scroll.add_widget(self.ing_label)
        self.add_widget(ing_scroll)

        self.steps_label = Label(text='', halign='left', valign='top')
        self.steps_label.bind(size=self._update_steps_text_size)
        steps_scroll = ScrollView(size_hint_y=0.6)
        steps_scroll.add_widget(self.steps_label)
        self.add_widget(steps_scroll)

    def _update_ing_text_size(self, instance, value):
        instance.text_size = (instance.width, None)

    def _update_steps_text_size(self, instance, value):
        instance.text_size = (instance.width, None)

    @mainthread
    def update(self, recipe):
        # ask the app cache for a local image path (downloads in background if missing)
        app = App.get_running_app()
        cache = app.cache if app is not None else None
        img_url = recipe.get('image_url') or ''
        if img_url and cache is not None:
            # provide a callback to set the image when cached or fallback to remote URL
            def cb(local_path):
                if local_path:
                    self.image.source = local_path
                else:
                    self.image.source = img_url

            cache.get_image(img_url, cb)
        else:
            self.image.source = img_url

        ing = '\n'.join(f'• {i}' for i in recipe.get('ingredients', []))
        self.ing_label.text = '[b]Ingrédients[/b]\n' + ing

        steps = '\n\n'.join(f"{i+1}. {s}" for i, s in enumerate(recipe.get('steps', [])))
        self.steps_label.text = '[b]Préparation[/b]\n' + steps


class RecettesApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache = None

    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        root = BoxLayout(orientation='horizontal', spacing=8, padding=8)

        # prepare cache directory and manager; without a usable cache the app
        # still works by loading images directly from their remote URL
        base = os.path.join(self.user_data_dir, 'cache') if self.user_data_dir else None
        try:
            self.cache = ImageCache(base_dir=base)
        except OSError as exc:
            Logger.warning(
                'Recettes: cache d\'images indisponible (%s), lecture directe depuis le réseau', exc
            )
            self.cache = None

        left = BoxLayout(orientation='vertical', size_hint_x=0.36)
        lbl = Label(text='Recettes', size_hint_y=None, height=36)
        left.add_widget(lbl)
        scroll = ScrollView()
        self.list_grid = RecipeList(RECIPES, self.show_recipe, size_hint_y=None)
        scroll.add_widget(self.list_grid)
        left.add_widget(scroll)

        self.detail = DetailView()

        root.add_widget(left)
        root.add_widget(self.detail)

        # show first recipe
        if RECIPES:
            self.show_recipe(0)

        return root

    def show_recipe(self, idx):
        if not 0 <= idx < len(RECIPES):
            raise IndexError(f'Index de recette invalide: {idx}')
        recipe = RECIPES[idx]
        self.detail.update(recipe)


class ImageCache:
    """Simple image cache that stores images in the app user_data_dir/images.
    Downloads happen on a background thread and call the provided callback with the
    local file path (or None on failure).
    """
    def __init__(self, base_dir=None):
        # base_dir will be set later when App is running; use a temp fallback
        self.base_dir = base_dir or os.path.join(os.getcwd(), 'cache_images')
        self.images_dir = os.path.join(self.base_dir, 'images')
        os.makedirs(self.images_dir, exist_ok=True)

    def _filename_for_url(self, url: str) -> str:
        parsed = urlparse(url)
        name = os.path.basename(parsed.path)
        digest = hashlib.sha1(url.encode('utf-8')).hexdigest()[:10]
        return f'{digest}_{name}' if name else digest

    @staticmethod
    def _call_on_main_thread(callback, value):
        @mainthread
        def _cb():
            callback(value)

        _cb()

    def get_image(self, url: str, callback):
        """Appelle callback(local_path) une fois l'image en cache, callback(None) sinon.

        Le callback est toujours invoqué exactement une fois sur le thread
        principal, y compris lorsque le téléchargement échoue.
        """
        local_path = os.path.join(self.images_dir, self._filename_for_url(url))

        if os.path.exists(local_path):
            self._call_on_main_thread(callback, local_path)
            return

        threading.Thread(
            target=self._download, args=(url, local_path, callback), daemon=True
        ).start()

    def _download(self, url: str, local_path: str, callback):
        tmp_path = local_path + '.tmp'
        try:
            resp = requests.get(url, stream=True, timeout=20)
            resp.raise_for_status()
            with open(tmp_path, 'wb') as f:
                for chunk in resp.iter_content(1024):
                    f.write(chunk)
            os.replace(tmp_path, local_path)
        except (requests.RequestException, OSError) as exc:
            Logger.warning('Recettes: téléchargement de %s échoué: %s', url, exc)
            self._remove_partial_file(tmp_path)
            self._call_on_main_thread(callback, None)
            return
        except BaseException:
            # ne jamais laisser le callback en attente si une erreur inattendue
            # survient dans ce thread d'arrière-plan
            Logger.exception('Recettes: erreur inattendue en téléchargeant %s', url)
            self._remove_partial_file(tmp_path)
            self._call_on_main_thread(callback, None)
            raise
        self._call_on_main_thread(callback, local_path)

    @staticmethod
    def _remove_partial_file(path: str):
        if not os.path.exists(path):
            return
        try:
            os.remove(path)
        except OSError as exc:
            Logger.warning('Recettes: fichier temporaire %s non supprimé: %s', path, exc)


if __name__ == '__main__':
    RecettesApp().run()
