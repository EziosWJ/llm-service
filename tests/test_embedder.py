import types
from unittest.mock import Mock

from src.services.embedder import Embedder


def test_lazy_load_model(monkeypatch):
    constructor = Mock()
    fake_module = types.SimpleNamespace(SentenceTransformer=constructor)
    import_module = Mock(return_value=fake_module)
    monkeypatch.setattr("src.services.embedder.importlib.import_module", import_module)

    embedder = Embedder(model_name="mock-model")

    import_module.assert_not_called()
    constructor.assert_not_called()

    model = Mock()
    model.encode.return_value = Mock(tolist=Mock(return_value=[[0.1, 0.2]]))
    constructor.return_value = model
    result = embedder.embed_texts(["hello"])

    assert result == [[0.1, 0.2]]
    import_module.assert_called_once_with("sentence_transformers")
    constructor.assert_called_once_with("mock-model")


def test_embed_texts_reuses_model(monkeypatch):
    model = Mock()
    model.encode.return_value = Mock(tolist=Mock(return_value=[[0.1], [0.2]]))

    constructor = Mock(return_value=model)
    fake_module = types.SimpleNamespace(SentenceTransformer=constructor)
    import_module = Mock(return_value=fake_module)
    monkeypatch.setattr("src.services.embedder.importlib.import_module", import_module)

    embedder = Embedder(model_name="mock-model")
    first = embedder.embed_texts(["a", "b"])
    second = embedder.embed_texts(["c", "d"])

    assert first == [[0.1], [0.2]]
    assert second == [[0.1], [0.2]]
    assert constructor.call_count == 1
    assert model.encode.call_count == 2


def test_embed_texts_empty_list_no_model_load(monkeypatch):
    import_module = Mock()
    monkeypatch.setattr("src.services.embedder.importlib.import_module", import_module)

    embedder = Embedder(model_name="mock-model")
    result = embedder.embed_texts([])

    assert result == []
    import_module.assert_not_called()


def test_get_dimension_from_model_api(monkeypatch):
    model = Mock()
    model.get_sentence_embedding_dimension.return_value = 768

    constructor = Mock(return_value=model)
    fake_module = types.SimpleNamespace(SentenceTransformer=constructor)
    import_module = Mock(return_value=fake_module)
    monkeypatch.setattr("src.services.embedder.importlib.import_module", import_module)

    embedder = Embedder(model_name="mock-model")
    dimension = embedder.get_dimension()

    assert dimension == 768
    model.get_sentence_embedding_dimension.assert_called_once()


def test_get_dimension_fallback_to_embedding_length(monkeypatch):
    class FakeModelWithoutDimension:
        def encode(self, texts, convert_to_numpy, normalize_embeddings):
            assert texts == ["dimension_probe"]
            assert convert_to_numpy is True
            assert normalize_embeddings is True
            return types.SimpleNamespace(tolist=lambda: [[0.1, 0.2, 0.3]])

    constructor = Mock(return_value=FakeModelWithoutDimension())
    fake_module = types.SimpleNamespace(SentenceTransformer=constructor)
    import_module = Mock(return_value=fake_module)
    monkeypatch.setattr("src.services.embedder.importlib.import_module", import_module)

    embedder = Embedder(model_name="mock-model")
    dimension = embedder.get_dimension()

    assert dimension == 3
