"""Unit tests for MockGeminiClient and staged edge case simulations."""

from src.engine.mock_client import MockGeminiClient


def test_mock_client_pass_scenario() -> None:
    """Verify pass scenario immediately returns conforming output."""
    client = MockGeminiClient(scenario="pass")
    chat = client.create_chat()
    text, tokens = client.send_prompt(chat, "Translate page")
    assert "## Core Synthesis" in text
    assert "## Technical Taxonomy" in text
    assert "## Analytical Formulations" in text
    assert tokens["prompt_tokens"] > 0
    assert tokens["output_tokens"] > 0
    assert tokens["model_version"] == "mock-model"
    assert len(chat.get_history()) == 2

    client_custom = MockGeminiClient(scenario="pass", model_name="gemini-3.8-flash")
    chat_custom = client_custom.create_chat()
    _, tokens_custom = client_custom.send_prompt(chat_custom, "Translate")
    assert tokens_custom["model_version"] == "gemini-3.8-flash"


def test_mock_client_rework_scenario() -> None:
    """Verify rework scenario returns defect on turn 1 and conforming on turn 2."""
    client = MockGeminiClient(scenario="rework")
    chat = client.create_chat()

    # Initial turn
    text1, tokens1 = client.send_prompt(chat, "Initial prompt")
    assert "## Technical Taxonomy" not in text1

    # Rework turn
    rework_prompt = (
        "# QUALITY GATE REJECTION (Rework Iteration 1)\nMissing section"
    )
    text2, tokens2 = client.send_prompt(chat, rework_prompt)
    assert "## Technical Taxonomy" in text2
    assert tokens2["prompt_tokens"] > tokens1["prompt_tokens"]


def test_mock_client_latex_scenario() -> None:
    """Verify latex scenario simulates unclosed latex then corrected latex."""
    client = MockGeminiClient(scenario="latex")
    chat = client.create_chat()

    text1, _ = client.send_prompt(chat, "Prompt")
    assert text1.count("$$") == 1  # Unclosed

    text2, _ = client.send_prompt(
        chat, "# QUALITY GATE REJECTION (Rework Iteration 1)"
    )
    assert text2.count("$$") % 2 == 0  # Balanced


def test_mock_client_empty_math_scenario() -> None:
    """Verify empty_math scenario fails empty rule then emits NONE RECORDED."""
    client = MockGeminiClient(scenario="empty_math")
    chat = client.create_chat()

    text1, _ = client.send_prompt(chat, "Prompt")
    assert "NONE RECORDED" not in text1

    text2, _ = client.send_prompt(
        chat, "# QUALITY GATE REJECTION (Rework Iteration 1)"
    )
    assert "NONE RECORDED" in text2


def test_mock_client_fail_scenario() -> None:
    """Verify fail scenario continues returning defect even after rework prompt."""
    client = MockGeminiClient(scenario="fail")
    chat = client.create_chat()

    text1, _ = client.send_prompt(chat, "Prompt")
    assert "## Technical Taxonomy" not in text1

    text2, _ = client.send_prompt(
        chat, "# QUALITY GATE REJECTION (Rework Iteration 1)"
    )
    assert "## Technical Taxonomy" not in text2


def test_mock_client_count_tokens() -> None:
    """Verify mock count_tokens handles empty, text, and history lists."""
    client = MockGeminiClient()
    assert client.count_tokens("") == 0
    assert client.count_tokens([]) == 0
    assert client.count_tokens("one two three four") == 5
    history = [{"parts": [{"text": "one two"}]}, {"parts": [{"text": "three four"}]}]
    assert client.count_tokens(history) == 520
