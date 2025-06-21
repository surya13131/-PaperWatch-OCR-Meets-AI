def find_keyword(text, keywords):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, line in enumerate(lines):
        for key in keywords:
            if key.lower() in line.lower():
                next_line = lines[i+1] if i+1 < len(lines) else ""
                return next_line if next_line else line
    return "Not found"
