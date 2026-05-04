from src.services.prompt_builder import PromptBuilder


def test_build_outline_renders_topic_sources_content() -> None:
    builder = PromptBuilder()
    prompt = builder.build_outline(
        topic="AI 写作",
        sources=["来源A", "来源B"],
        content="先写框架",
    )
    assert "AI 写作" in prompt
    assert "- 来源A" in prompt
    assert "- 来源B" in prompt
    assert "先写框架" in prompt


def test_build_draft_uses_string_sources() -> None:
    builder = PromptBuilder()
    prompt = builder.build_draft(
        topic="自动化测试",
        sources="内部知识库",
        content="包含 3 个段落",
    )
    assert "自动化测试" in prompt
    assert "内部知识库" in prompt
    assert "包含 3 个段落" in prompt


def test_build_polished_keeps_required_markers() -> None:
    builder = PromptBuilder()
    prompt = builder.build_polished(
        topic="工程质量",
        sources=["规范1"],
        content="原稿文本",
    )
    assert "工程质量" in prompt
    assert "原稿文本" in prompt
    assert "润色" in prompt


def test_build_title_fallback_for_empty_sources() -> None:
    builder = PromptBuilder()
    prompt = builder.build_title(
        topic="平台演进",
        sources=[],
        content="讲述架构变化",
    )
    assert "平台演进" in prompt
    assert "(无来源)" in prompt
    assert "讲述架构变化" in prompt
