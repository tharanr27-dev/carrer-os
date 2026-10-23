from typing import Any, List

from app.modules.training.llm import LLMUnavailable, TrainingLLM


class FakeLLM(TrainingLLM):
    """Scripted LLM: no network. Each complete_json call pops the next scripted response."""

    def __init__(self, responses: List[Any] = None, available: bool = True):
        super().__init__("test-key" if available else None, "test-model", 1.0)
        self.responses = list(responses or [])
        self.calls: List[dict] = []

    async def complete_json(self, system: str, user: str, max_tokens: int = 1800):
        self.calls.append({"system": system, "user": user})
        if not self.available:
            raise LLMUnavailable("not configured")
        if not self.responses:
            raise LLMUnavailable("no scripted response")
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    async def complete_text(self, system: str, messages, max_tokens: int = 600):
        self.calls.append({"system": system, "messages": messages})
        if not self.available:
            raise LLMUnavailable("not configured")
        if not self.responses:
            raise LLMUnavailable("no scripted response")
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


# ── Real (tiny) documents for extraction tests ───────────────────────────────
import io as _io
import zipfile as _zipfile


def make_pdf(lines):
    """A valid single-page text PDF (uncompressed, Helvetica) containing the given lines."""

    def esc(s):
        return s.replace("\\", "\\\\").replace("(", r"\(").replace(")", r"\)")

    stream = "BT /F1 10 Tf 40 800 Td 12 TL\n" + "\n".join(f"({esc(l)}) Tj T*" for l in lines) + "\nET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
    ]
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def make_docx(paragraphs):
    """A minimal valid .docx whose body holds the given paragraphs."""
    body = "".join(f"<w:p><w:r><w:t xml:space=\"preserve\">{p}</w:t></w:r></w:p>" for p in paragraphs)
    xml = f'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>'
    buf = _io.BytesIO()
    with _zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", xml)
    return buf.getvalue()


GOOD_RESUME = [
    "Priya Raman",
    "priya.raman@example.com | +91 98765 43210 | github.com/priyaraman",
    "Summary",
    "Final-year Computer Science student interested in backend development.",
    "Education",
    "B.E. Computer Science, Anna University, 2026, CGPA 8.4",
    "Skills",
    "Python, FastAPI, PostgreSQL, Docker, Git, REST APIs, SQL, Linux",
    "Projects",
    "- Built a student attendance API with FastAPI and PostgreSQL serving 300 users",
    "- Implemented JWT authentication and reduced login latency by 35%",
    "- Designed a Docker based deployment and automated tests with pytest",
    "- Developed a React dashboard that visualises attendance for 12 classes",
    "Experience",
    "- Responsible for fixing bugs during a 2 month internship at Acme Labs",
    "- Led a team of 4 students to deliver a hackathon prototype in 24 hours",
]
