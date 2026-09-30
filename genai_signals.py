import re
# regular expression support, to parse through and find the genai tag, ordered from strongest -> weakest evidence
PATTERNS = {
    "assisted_by_tag": re.compile(r"^\s*assisted[- ]by\s*:\s*(.+)$", re.I | re.M), 
    "ai_coauthor": re.compile(
        r"^\s*co-authored-by\s*:.*\b(claude|copilot|chatgpt|gemini|cursor|codex)\b.*$",
        re.I | re.M),
    "ai.keyword": re.compile(
        r"\b(chatgpt|copilot|claude|gemini|llm|gpt-?\d\w*"
        r"|generated (?:by|with|using) (?:ai|an? llm))\b", re.I),
}

def detect_genai(text):
    # return candidate flag, which signals fired, and the matched text to go with it
    empty = {"genai_candidate": False, "signal_types": "", "matched_text": ""}
    if not text:
        return empty
    types, matched = [], []
    for name, pattern in PATTERNS.items():
        for m in pattern.finditer(text): # catch case in case there's an ai model unconsidered yet
            if name not in types:
                types.append(name)
            matched.append(m.group(0).strip())
    if not types:
        return empty
    return {
        "genai_candidate": True,
        "signal_types": ";" .join(types),
        "matched_text": " | " .join(matched[:5]), # caps length 
    }