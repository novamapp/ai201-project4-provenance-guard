# test_stylometrics.py
from stylometrics import analyze_text

def test_analyze_text_empty_and_whitespace():
    """Ensure empty strings or pure spaces default to balanced fallback states."""
    fallback_result = {"human_likely": 0.5, "AI_likely": 0.5}
    assert analyze_text("") == fallback_result
    assert analyze_text("   ") == fallback_result
    assert analyze_text(None) == fallback_result

def test_analyze_text_structure_and_types():
    """Verify standard text returns correct key names, structures, and value clamping rules."""
    sample_poem = (
        "The sun dipped below the horizon line,\n"
        "A quiet whisper of golden twine."
    )
    result = analyze_text(sample_poem)
    
    assert "human_likely" in result
    assert "AI_likely" in result
    assert isinstance(result["human_likely"], float)
    assert isinstance(result["AI_likely"], float)
    
    # Assert values sit on a clean 0.0 to 1.0 probability matrix scale
    assert 0.0 <= result["human_likely"] <= 1.0
    assert 0.0 <= result["AI_likely"] <= 1.0
    
    # Ensure they stay complementary within rounding approximations
    assert abs((result["human_likely"] + result["AI_likely"]) - 1.0) < 0.05

def test_analyze_text_uniform_monotone_input():
    """Stiff, non-varying structures with low vocabulary diversity should tilt higher on AI_likely."""
    # A single repeating phrase with uniform structure and no line variance
    monotone_text = "the same line.\nthe same line.\nthe same line."
    result = analyze_text(monotone_text)
    
    # Lower vocabulary type-token ratio and minimal variance shifts weight toward AI signature traits
    assert result["AI_likely"] >= 0.5