from __future__ import annotations

import importlib
from typing import Iterable


class Embedder:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            module = importlib.import_module("sentence_transformers")
            self._model = module.SentenceTransformer(self._model_name)
        return self._model

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        text_list = list(texts)
        if not text_list:
            return []

        model = self._get_model()
        embeddings = model.encode(text_list, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        model = self._get_model()
        if hasattr(model, "get_sentence_embedding_dimension"):
            return int(model.get_sentence_embedding_dimension())

        vector = self.embed_texts(["dimension_probe"])
        if not vector or not vector[0]:
            raise ValueError("Embedding model returned empty vector.")
        return len(vector[0])
