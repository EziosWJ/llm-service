"""文本向量化服务：使用 sentence-transformers 将文本转为归一化向量，延迟加载模型以加快启动。"""

from __future__ import annotations

import importlib
import logging
from typing import Iterable

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        """延迟加载 SentenceTransformer 模型，首次调用时才导入并实例化。"""
        if self._model is None:
            module = importlib.import_module("sentence_transformers")
            self._model = module.SentenceTransformer(self._model_name)
        return self._model

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        """将文本列表编码为归一化向量列表。"""
        text_list = list(texts)
        if not text_list:
            return []

        logger.debug("Embedding %d texts", len(text_list))
        model = self._get_model()
        embeddings = model.encode(text_list, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        """获取向量维度，优先用模型内置方法，否则通过一次实际编码来探测。"""
        model = self._get_model()
        if hasattr(model, "get_sentence_embedding_dimension"):
            return int(model.get_sentence_embedding_dimension())

        vector = self.embed_texts(["dimension_probe"])
        if not vector or not vector[0]:
            raise ValueError("Embedding model returned empty vector.")
        return len(vector[0])
