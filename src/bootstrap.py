from __future__ import annotations

from dataclasses import dataclass

from src.config import get_settings
from src.infrastructure.llm_client import LLMClient
from src.infrastructure.qdrant import QdrantStore
from src.services.embedder import Embedder
from src.services.ask_service import AskService
from src.services.generator import GeneratorService
from src.services.material_pipeline import MaterialPipeline
from src.services.prompt_builder import PromptBuilder
from src.services.retriever import Retriever


@dataclass
class Container:
    embedder: Embedder
    qdrant_store: QdrantStore
    llm_client: LLMClient
    material_pipeline: MaterialPipeline
    retriever: Retriever
    prompt_builder: PromptBuilder
    generator: GeneratorService
    ask_service: AskService


_container: Container | None = None


def build_container() -> Container:
    settings = get_settings()
    embedder = Embedder(settings.embedding_model)
    safe_model_name = settings.embedding_model.split("/")[-1].replace(":", "_")
    collection_name = f"{settings.qdrant_collection_prefix}_{safe_model_name}"
    qdrant_store = QdrantStore(
        url=settings.qdrant_url,
        collection_name=collection_name,
        vector_size=embedder.get_dimension(),
    )
    llm_client = LLMClient(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=settings.llm_api_key or "EMPTY",
        enable_thinking=settings.llm_enable_thinking,
    )
    material_pipeline = MaterialPipeline(embedder=embedder, qdrant_store=qdrant_store)
    retriever = Retriever(embedder=embedder, qdrant_store=qdrant_store)
    prompt_builder = PromptBuilder()
    generator = GeneratorService(
        retriever=retriever,
        prompt_builder=prompt_builder,
        llm_client=llm_client,
    )
    ask_service = AskService(
        retriever=retriever,
        prompt_builder=prompt_builder,
        llm_client=llm_client,
    )
    return Container(
        embedder=embedder,
        qdrant_store=qdrant_store,
        llm_client=llm_client,
        material_pipeline=material_pipeline,
        retriever=retriever,
        prompt_builder=prompt_builder,
        generator=generator,
        ask_service=ask_service,
    )


def get_container() -> Container:
    global _container
    if _container is None:
        _container = build_container()
    return _container
