"""Tests for the Tkinter UI class. They need a display (xvfb is enough)."""
import pytest
from PIL import Image

recettes_tk = pytest.importorskip("recettes_tk")
tk = pytest.importorskip("tkinter")


def _display_available():
    try:
        root = tk.Tk()
    except Exception:
        return False
    root.destroy()
    return True


requires_display = pytest.mark.skipif(not _display_available(), reason="no display available")

RECIPES = [
    {
        "name": "Jollof Rice",
        "country": "Nigeria",
        "ingredients": ["Riz", "Tomates"],
        "steps": ["Préparer la sauce.", "Cuire le riz."],
        "image_url": "https://example.com/jollof.jpg",
    },
    {
        "name": "Mafé",
        "country": "Mali",
        "ingredients": ["Viande"],
        "steps": ["Mijoter."],
        "image_url": "https://example.com/mafe.jpg",
    },
]


@pytest.fixture
def app(monkeypatch, tmp_path):
    """A RecipeApp whose images are generated locally instead of downloaded."""

    def fake_ensure_image(recipe):
        path = tmp_path / (recettes_tk.slugify(recipe["name"]) + ".jpg")
        Image.new("RGB", (40, 30), (10, 20, 30)).save(path, "JPEG")
        return str(path)

    monkeypatch.setattr(recettes_tk, "ensure_image", fake_ensure_image)
    application = recettes_tk.RecipeApp(RECIPES)
    yield application
    application.destroy()


def text_of(widget):
    return widget.get("1.0", tk.END)


@requires_display
def test_app_lists_every_recipe_and_selects_the_first(app):
    assert app.recipe_listbox.get(0, tk.END) == (
        "Jollof Rice  —  Nigeria",
        "Mafé  —  Mali",
    )
    assert app.recipe_listbox.curselection() == (0,)
    assert app.current_index == 0
    assert text_of(app.ing_text).startswith("• Riz")


@requires_display
def test_load_images_keeps_one_pil_image_per_recipe(app):
    assert len(app.pil_images) == len(RECIPES)
    assert all(img is not None for img in app.pil_images)


@requires_display
def test_load_images_falls_back_to_placeholder_for_unreadable_file(monkeypatch, tmp_path):
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"not an image")
    monkeypatch.setattr(recettes_tk, "ensure_image", lambda recipe: str(broken))

    application = recettes_tk.RecipeApp(RECIPES[:1])
    try:
        assert application.pil_images[0].size == (800, 600)
    finally:
        application.destroy()


@requires_display
def test_show_recipe_renders_ingredients_and_numbered_steps(app):
    app.show_recipe(0)

    assert text_of(app.ing_text) == "• Riz\n• Tomates\n\n"
    assert text_of(app.prep_text) == "1. Préparer la sauce.\n\n2. Cuire le riz.\n\n\n"
    assert app.current_index == 0


@requires_display
def test_show_recipe_replaces_previous_content(app):
    app.show_recipe(0)
    app.show_recipe(1)

    assert text_of(app.ing_text) == "• Viande\n\n"
    assert text_of(app.prep_text) == "1. Mijoter.\n\n\n"
    assert app.current_index == 1


@requires_display
def test_text_widgets_stay_read_only(app):
    assert app.ing_text.cget("state") == "disabled"
    assert app.prep_text.cget("state") == "disabled"


@requires_display
def test_on_select_shows_the_selected_recipe(app):
    app.recipe_listbox.selection_clear(0, tk.END)
    app.recipe_listbox.selection_set(1)
    app.recipe_listbox.event_generate("<<ListboxSelect>>")
    app.update()

    assert app.current_index == 1
    assert text_of(app.ing_text) == "• Viande\n\n"


@requires_display
def test_on_select_ignores_empty_selection(app):
    app.show_recipe(1)
    app.recipe_listbox.selection_clear(0, tk.END)
    app.recipe_listbox.event_generate("<<ListboxSelect>>")
    app.update()

    assert app.current_index == 1


@requires_display
def test_refresh_image_caches_a_photoimage_per_recipe(app):
    app.show_recipe(1)
    app._refresh_image()

    assert 1 in app.tk_images
    assert str(app.tk_images[1]) in app.image_label.cget("image")


def test_main_builds_the_app_and_starts_the_loop(monkeypatch):
    created = {}

    class FakeApp:
        def __init__(self, recipes):
            created["recipes"] = recipes

        def mainloop(self):
            created["started"] = True

    monkeypatch.setattr(recettes_tk, "RecipeApp", FakeApp)

    recettes_tk.main()

    assert created["recipes"] is recettes_tk.RECIPES
    assert created["started"] is True


@requires_display
def test_refresh_image_is_a_noop_without_a_loaded_image(app):
    app.pil_images[0] = None
    app.current_index = 0
    app.tk_images.pop(0, None)

    app._refresh_image()

    assert 0 not in app.tk_images
