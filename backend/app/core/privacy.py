import re

RE_NIK = re.compile(r"(?:\d[\s-]?){16}")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

def mask_pii(text: str) -> str:
    def _masknik(m):
        nik = re.sub(r"[\s-]", "", m.group())
        return "[NIK]" if len(nik)==16 else m.group()
    masked = RE_NIK.sub(_masknik, text)
    return RE_EMAIL.sub("[EMAIL]", masked)
