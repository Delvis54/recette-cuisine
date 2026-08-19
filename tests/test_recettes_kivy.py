import os

import pytest

recettes_kivy = pytest.importorskip("recettes_kivy")

from kivy.clock import Clock  # noqa: E402  (imported after the kivy env setup)


def _window_available():
    try:
        from kivy.core.window import Window
    except Exception:
        return False
    return Window is not None


# Building kivy widgets requires a window provider, i.e. a display (xvfb is enough).
requires_window = pytest.mark.skipif(
    not _window_available(), reason="no kivy window provider available"
)


class FakeResponse:
    def __init__(self, chunks=(b"data",), error=None):
        self._chunks = chunks
        self._error = error

    def raise_for_status(self):
        if self._error is not None:
            raise self._error

    def iter_content(self, chunk_size):
        return iter(self._chunks)


def run_clock(iterations=20):
    """Flush the callbacks scheduled by kivy's @mainthread decorator."""
    for _ in range(iterations):
        Clock.tick()


@pytest.fixture
def cache(tmp_path):
    return recettes_kivy.ImageCache(base_dir=str(tmp_path))


def patch_running_app(monkeypatch, cache):
    class FakeApp:
        pass

    app = FakeApp()
    app.cache = cache
    monkeypatch.setattr(recettes_kivy.App, "get_running_app", staticmethod(lambda: app))
    return app


def test_image_cache_creates_base_dir(tmp_path):
    base = tmp_path / "nested" / "cache"
    recettes_kivy.ImageCache(base_dir=str(base))
    assert base.is_dir()


def test_image_cache_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache = recettes_kivy.ImageCache()
    assert cache.base_dir == os.path.join(str(tmp_path), "cache_images")
    assert os.path.isdir(cache.base_dir)


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://example.com/a/b/photo.jpg", "photo.jpg"),
        ("https://example.com/photo.jpg?size=large", "photo.jpg"),
        ("https://example.com/", "img"),
        ("https://example.com", "img"),
    ],
)
def test_filename_for_url(cache, url, expected):
    assert cache._filename_for_url(url) == expected


def test_get_image_returns_cached_path_without_download(cache, monkeypatch):
    local_dir = os.path.join(cache.base_dir, "images")
    os.makedirs(local_dir, exist_ok=True)
    cached = os.path.join(local_dir, "photo.jpg")
    with open(cached, "wb") as f:
        f.write(b"cached")

    def fail(*args, **kwargs):
        raise AssertionError("cached images must not be re-downloaded")

    monkeypatch.setattr(recettes_kivy.requests, "get", fail)

    results = []
    cache.get_image("https://example.com/photo.jpg", results.append)
    run_clock()

    assert results == [cached]


def test_get_image_downloads_missing_image(cache, monkeypatch):
    monkeypatch.setattr(
        recettes_kivy.requests,
        "get",
        lambda url, **kwargs: FakeResponse([b"ab", b"cd"]),
    )

    results = []
    cache.get_image("https://example.com/new.jpg", results.append)
    run_clock(200)

    expected = os.path.join(cache.base_dir, "images", "new.jpg")
    assert results == [expected]
    with open(expected, "rb") as f:
        assert f.read() == b"abcd"
    assert not os.path.exists(expected + ".tmp")


def test_get_image_calls_back_with_none_on_failure(cache, monkeypatch):
    def boom(url, **kwargs):
        raise recettes_kivy.requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(recettes_kivy.requests, "get", boom)

    results = []
    cache.get_image("https://example.com/broken.jpg", results.append)
    run_clock(200)

    assert results == [None]
    assert not os.path.exists(os.path.join(cache.base_dir, "images", "broken.jpg"))


@requires_window
def test_recipe_list_builds_one_button_per_recipe():
    recipes = [
        {"name": "Jollof Rice", "country": "Nigeria"},
        {"name": "Mafé", "country": "Mali"},
    ]
    grid = recettes_kivy.RecipeList(recipes, lambda idx: None)

    labels = [child.text for child in reversed(grid.children)]
    assert labels == ["Jollof Rice  —  Nigeria", "Mafé  —  Mali"]
    assert [child.recipe_index for child in reversed(grid.children)] == [0, 1]


@requires_window
def test_recipe_list_press_forwards_index():
    recipes = [{"name": "A", "country": "X"}, {"name": "B", "country": "Y"}]
    selected = []
    grid = recettes_kivy.RecipeList(recipes, selected.append)

    second_button = list(reversed(grid.children))[1]
    second_button.dispatch("on_release")

    assert selected == [1]


@requires_window
def test_detail_view_update_renders_ingredients_and_steps(monkeypatch):
    patch_running_app(monkeypatch, None)
    view = recettes_kivy.DetailView()

    view.update(
        {
            "name": "Egusi",
            "ingredients": ["Egusi", "Huile"],
            "steps": ["Préparer la pâte.", "Cuire."],
            "image_url": "https://example.com/egusi.jpg",
        }
    )
    run_clock()

    assert view.ing_label.text == "[b]Ingrédients[/b]\n• Egusi\n• Huile"
    assert view.steps_label.text == "[b]Préparation[/b]\n1. Préparer la pâte.\n\n2. Cuire."
    assert view.image.source == "https://example.com/egusi.jpg"


@requires_window
def test_detail_view_update_handles_missing_fields(monkeypatch):
    patch_running_app(monkeypatch, None)
    view = recettes_kivy.DetailView()

    view.update({"name": "Vide"})
    run_clock()

    assert view.ing_label.text == "[b]Ingrédients[/b]\n"
    assert view.steps_label.text == "[b]Préparation[/b]\n"
    assert view.image.source == ""


@requires_window
def test_detail_view_update_uses_cached_local_path(monkeypatch, tmp_path):
    class FakeCache:
        def __init__(self):
            self.requested = []

        def get_image(self, url, callback):
            self.requested.append(url)
            callback(str(tmp_path / "local.jpg"))

    fake_cache = FakeCache()
    patch_running_app(monkeypatch, fake_cache)
    view = recettes_kivy.DetailView()

    view.update({"image_url": "https://example.com/x.jpg"})
    run_clock()

    assert fake_cache.requested == ["https://example.com/x.jpg"]
    assert view.image.source == str(tmp_path / "local.jpg")


@requires_window
def test_detail_view_update_falls_back_to_remote_url_when_cache_fails(monkeypatch):
    class FakeCache:
        def get_image(self, url, callback):
            callback(None)

    patch_running_app(monkeypatch, FakeCache())
    view = recettes_kivy.DetailView()

    view.update({"image_url": "https://example.com/remote.jpg"})
    run_clock()

    assert view.image.source == "https://example.com/remote.jpg"


@requires_window
def test_app_build_wires_the_list_the_detail_view_and_the_cache(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = recettes_kivy.RecettesApp()
    monkeypatch.setattr(recettes_kivy.App, "get_running_app", staticmethod(lambda: app))

    root = app.build()
    cache = app.cache
    # the pending DetailView.update must not hit the network when the clock ticks
    app.cache = None
    run_clock()

    assert isinstance(cache, recettes_kivy.ImageCache)
    assert len(app.list_grid.children) == len(recettes_kivy.RECIPES)
    assert len(root.children) == 2
    assert recettes_kivy.RECIPES[0]["ingredients"][0] in app.detail.ing_label.text


@requires_window
def test_app_show_recipe_updates_the_detail_view(monkeypatch):
    patch_running_app(monkeypatch, None)
    app = recettes_kivy.RecettesApp()
    app.detail = recettes_kivy.DetailView()

    app.show_recipe(0)
    run_clock()

    recipe = recettes_kivy.RECIPES[0]
    assert recipe["ingredients"][0] in app.detail.ing_label.text
    assert recipe["steps"][0] in app.detail.steps_label.text


@requires_window
def test_detail_view_label_text_size_follows_width(monkeypatch):
    patch_running_app(monkeypatch, None)
    view = recettes_kivy.DetailView()

    view.ing_label.width = 321
    view.steps_label.width = 123

    assert tuple(view.ing_label.text_size) == (321, None)
    assert tuple(view.steps_label.text_size) == (123, None)
