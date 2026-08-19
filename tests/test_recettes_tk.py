import os

import pytest
from PIL import Image

recettes_tk = pytest.importorskip("recettes_tk")


class FakeResponse:
    def __init__(self, chunks=(b"data",), error=None):
        self._chunks = chunks
        self._error = error

    def raise_for_status(self):
        if self._error is not None:
            raise self._error

    def iter_content(self, chunk_size):
        assert chunk_size > 0
        return iter(self._chunks)


def test_recipes_data_is_consistent():
    assert len(recettes_tk.RECIPES) == 10
    names = [r["name"] for r in recettes_tk.RECIPES]
    assert len(set(names)) == len(names)
    for recipe in recettes_tk.RECIPES:
        assert recipe["name"] and recipe["country"]
        assert recipe["ingredients"] and all(recipe["ingredients"])
        assert recipe["steps"] and all(recipe["steps"])
        assert recipe["image_url"].startswith("https://")


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Jollof Rice", "jollof_rice"),
        ("JOLLOF RICE", "jollof_rice"),
        ("Tagine d'agneau", "tagine_dagneau"),
        ("Mafé", "mafé"),
        ("Doro  Wat", "doro__wat"),
        ("Attiéké 2", "attiéké_2"),
        ("", ""),
        ("!!!", ""),
    ],
)
def test_slugify(name, expected):
    assert recettes_tk.slugify(name) == expected


def test_slugify_output_has_no_separators_other_than_underscore():
    slug = recettes_tk.slugify("Bunny Chow (Afrique du Sud)")
    assert "/" not in slug and " " not in slug and "(" not in slug


def test_local_image_path_is_inside_images_dir():
    path = recettes_tk.local_image_path({"name": "Jollof Rice"})
    assert os.path.dirname(path) == recettes_tk.IMAGES_DIR
    assert os.path.basename(path) == "jollof_rice.jpg"


def test_download_image_writes_all_chunks(tmp_path, monkeypatch):
    target = tmp_path / "img.jpg"
    calls = {}

    def fake_get(url, **kwargs):
        calls["url"] = url
        calls["kwargs"] = kwargs
        return FakeResponse([b"abc", b"def"])

    monkeypatch.setattr(recettes_tk.requests, "get", fake_get)

    assert recettes_tk.download_image("http://example.com/i.jpg", str(target)) is True
    assert target.read_bytes() == b"abcdef"
    assert calls["url"] == "http://example.com/i.jpg"
    assert calls["kwargs"]["stream"] is True
    assert calls["kwargs"]["timeout"] == 15


def test_download_image_returns_false_on_http_error(tmp_path, monkeypatch, capsys):
    target = tmp_path / "img.jpg"
    monkeypatch.setattr(
        recettes_tk.requests,
        "get",
        lambda url, **kwargs: FakeResponse(error=RuntimeError("404")),
    )

    assert recettes_tk.download_image("http://example.com/i.jpg", str(target)) is False
    assert not target.exists()
    assert "Téléchargement échoué" in capsys.readouterr().out


def test_download_image_returns_false_on_connection_error(tmp_path, monkeypatch):
    def boom(url, **kwargs):
        raise recettes_tk.requests.exceptions.ConnectionError("offline")

    monkeypatch.setattr(recettes_tk.requests, "get", boom)

    assert recettes_tk.download_image("http://example.com/i.jpg", str(tmp_path / "i.jpg")) is False


def test_ensure_image_returns_existing_file_without_downloading(tmp_path, monkeypatch):
    monkeypatch.setattr(recettes_tk, "IMAGES_DIR", str(tmp_path))
    recipe = {"name": "Egusi", "image_url": "http://example.com/e.jpg"}
    existing = tmp_path / "egusi.jpg"
    Image.new("RGB", (2, 2), (1, 2, 3)).save(existing, "JPEG")

    def fail(*args, **kwargs):
        raise AssertionError("should not download an already cached image")

    monkeypatch.setattr(recettes_tk, "download_image", fail)

    assert recettes_tk.ensure_image(recipe) == str(existing)


def test_ensure_image_downloads_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(recettes_tk, "IMAGES_DIR", str(tmp_path))
    recipe = {"name": "Koshary", "image_url": "http://example.com/k.jpg"}
    downloaded = []

    def fake_download(url, path):
        downloaded.append((url, path))
        Image.new("RGB", (4, 4), (9, 9, 9)).save(path, "JPEG")
        return True

    monkeypatch.setattr(recettes_tk, "download_image", fake_download)

    path = recettes_tk.ensure_image(recipe)
    assert path == str(tmp_path / "koshary.jpg")
    assert downloaded == [("http://example.com/k.jpg", path)]


def test_ensure_image_creates_placeholder_when_download_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(recettes_tk, "IMAGES_DIR", str(tmp_path))
    monkeypatch.setattr(recettes_tk, "download_image", lambda url, path: False)

    path = recettes_tk.ensure_image({"name": "Mafé", "image_url": "http://example.com/m.jpg"})

    with Image.open(path) as img:
        assert img.size == (800, 600)
        assert img.convert("RGB").getpixel((0, 0)) == (200, 200, 200)


def test_ensure_image_creates_placeholder_when_no_url(tmp_path, monkeypatch):
    monkeypatch.setattr(recettes_tk, "IMAGES_DIR", str(tmp_path))

    def fail(*args, **kwargs):
        raise AssertionError("no URL means no download attempt")

    monkeypatch.setattr(recettes_tk, "download_image", fail)

    path = recettes_tk.ensure_image({"name": "Sans image"})
    assert os.path.exists(path)
    with Image.open(path) as img:
        assert img.size == (800, 600)
