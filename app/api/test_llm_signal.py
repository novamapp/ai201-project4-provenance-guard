import os
from unittest.mock import patch, MagicMock

os.environ["GROQ_API_KEY"] = "mock_key_for_testing_purposes"

from llm_signal import analyze_text_with_llm

def test_analyze_text_with_llm_empty_input():
    """Empty inputs should short-circuit before hitting the API network client layer."""
    assert analyze_text_with_llm("") == {"human_likely": 0.5, "AI_likely": 0.5}

@patch("llm_signal.client.chat.completions.create")
def test_analyze_text_with_llm_success(mock_create):
    """Verify successful JSON payload extractions from a mocked Groq API client completion wrapper."""
    # 1. Structure the mock return object chain to reflect the Groq choice message structure
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"human_likely": 0.25, "AI_likely": 0.75}'))
    ]
    mock_create.return_value = mock_response

    # 2. Fire execution
    result = analyze_text_with_llm("Some sample poem content text.")

    # 3. Validation assertions
    assert result == {"human_likely": 0.25, "AI_likely": 0.75}
    mock_create.assert_called_once()

@patch("llm_signal.client.chat.completions.create")
def test_analyze_text_with_llm_malformed_json_fallback(mock_create):
    """If the LLM returns invalid JSON or text formatting breaks, it must recover gracefully with safe defaults."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='Invalid non-json raw text string payload.'))
    ]
    mock_create.return_value = mock_response

    result = analyze_text_with_llm("Some sample poem content text.")
    
    # Recovers cleanly with a balanced fallback configuration matrix
    assert result == {"human_likely": 0.5, "AI_likely": 0.5}

@patch("llm_signal.client.chat.completions.create")
def test_analyze_text_with_llm_api_timeout_exception(mock_create):
    """If a critical network connection error occurs, verify the method catches it safely instead of throwing an unhandled exception."""
    mock_create.side_effect = Exception("API Connection Timeout or Token Allocation Exhaustion limit.")

    result = analyze_text_with_llm("Some sample poem content text.")
    
    # Pipeline remains operational via defensive safety catch
    assert result == {"human_likely": 0.5, "AI_likely": 0.5}