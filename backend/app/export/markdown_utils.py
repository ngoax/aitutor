# renderText splits on these and treats the odd-numbered pieces as LaTeX and media.
DELIMITERS = ("$$", "##")


def to_oatutor_text(text: str) -> str:
    """Escape line breaks and drop markdown bold which OATutor renders as caret"""
    return text.replace("\r\n", "\n").replace("\n", r"\n").replace("**", "")


IGNORED_DELIMITERS = (r"\(", r"\)", r"\[", r"\]")


def unbalanced_delimiters(text: str) -> list[str]:
    """Delimiters that appear an odd number of times, so renderText splits wrongly"""
    return [delimiter for delimiter in DELIMITERS if text.count(delimiter) % 2]


def ignored_delimiters(text: str) -> list[str]:
    """Delimiters that OATutor renders as plain text instead of as maths"""
    return [delimiter for delimiter in IGNORED_DELIMITERS if delimiter in text]
