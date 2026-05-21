# 依赖注入容器：组装并缓存所有服务和基础设施实例

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
    """DI 容器，持有所有服务实例，避免全局散落的依赖关系"""
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
    """构建完整的依赖图：从配置出发，依次创建基础设施 → 服务 → 业务层"""
    settings = get_settings()
    embedder = Embedder(settings.embedding_model)
    # 将模型名转为安全的集合名后缀（去除路径前缀和冒号）
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
    """懒加载单例：首次调用时构建容器，后续直接返回缓存实例"""
    global _container
    if _container is None:
        _container = build_container()
    return _container
