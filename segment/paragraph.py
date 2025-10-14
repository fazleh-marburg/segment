def is_valid_paragraph(paragraph):
    """Return True if paragraph has 3 or more words, else False."""
    word_count = len(paragraph.split())
    return word_count >= 3

def filter_paragraphs(text):
    """Keep only valid paragraphs (3 or more words)."""
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    valid_paragraphs = [p for p in paragraphs if is_valid_paragraph(p)]
    return "\n\n".join(valid_paragraphs)

# Example usage
text = "Hi there bangladesh is a biggest counbtry"

result = filter_paragraphs(text)

if not (is_valid_paragraph(text)):
    print(text)
