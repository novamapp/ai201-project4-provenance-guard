# stylometrics.py
import string
import math

def analyze_text(text):
    """
    Analyzes raw poem text using stylometric heuristics from scratch.
    Returns:
        dict: A dictionary containing human_likely and AI_likely weights based on:
              - Type-Token Ratio (Vocabulary diversity)
              - Punctuation Density (Predictive layouts)
              - Line-Length Variance (Structural stiffness vs freedom)
    """
    if not text or not text.strip():
        return {"human_likely": 0.5, "AI_likely": 0.5}

    # Split text into structural lines and words
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Strip punctuation to extract clean tokens/words
    translator = str.maketrans('', '', string.punctuation)
    clean_text = text.translate(translator)
    tokens = [word.lower() for word in clean_text.split() if word]

    if not tokens:
        return {"human_likely": 0.5, "AI_likely": 0.5}

    # 1. Type-Token Ratio (TTR)
    # Measures vocabulary diversity (Unique words / Total words)
    # AI models generating short text/poetry tend to over-index on a repetitive vocabulary loop.
    unique_types = set(tokens)
    ttr = len(unique_types) / len(tokens)

    # 2. Punctuation Density
    # Predictable punctuation habits (standardizing sentence-like endings for poem rows).
    total_chars = len(text)
    punctuation_count = sum(1 for char in text if char in string.punctuation)
    punctuation_density = punctuation_count / total_chars if total_chars > 0 else 0

    # 3. Line-Length Variance (Custom calculation from scratch)
    # AI generation often forces uniform visual structures/stiff syllable counts per line,
    # whereas human poetry displays fluid length variance.
    if len(lines) > 1:
        line_lengths = [len(line) for line in lines]
        mean_length = sum(line_lengths) / len(line_lengths)
        variance = sum((length - mean_length) ** 2 for length in line_lengths) / len(line_lengths)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0  # Singlet/short line boundary default

    # =========================================================================
    # HEURISTIC COMBINATION ENGINE & SCORE CALIBRATION
    # Normalizing empirical bounds into weights.
    # =========================================================================
    
    # High vocabulary diversity (TTR) favors human likelihood
    ttr_human_score = ttr 
    
    # Moderate punctuation density is normal; over-punctuated/rigid endings lean AI
    # If punctuation density stays under an artificial limit of 8%, it feels more organic
    punc_human_score = 1.0 - min(punctuation_density * 10, 1.0)
    
    # Healthy variation in line lengths indicates human expression
    # Standard deviation capping at a threshold of 25 characters for scaling
    line_human_score = min(std_dev / 25.0, 1.0)

    # Calculate average metric to serve as base human probability
    human_likely = round((ttr_human_score + punc_human_score + line_human_score) / 3.0, 2)
    AI_likely = round(1.0 - human_likely, 2)

    return {
        "human_likely": human_likely,
        "AI_likely": AI_likely
    }