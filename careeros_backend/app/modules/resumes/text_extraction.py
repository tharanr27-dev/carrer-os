"""Local text extraction for uploaded résumés. No network, no AI."""

import html
import io
import re
import zipfile
from dataclasses import dataclass, field
from typing import List

MAX_PAGES = 15
MAX_TEXT_CHARS = 60_000
MAX_DOCX_XML_BYTES = 20 * 1024 * 1024
PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@dataclass
class ExtractionResult:
    text: str = ""
    method: str = "none"  # pypdf | docx_xml | none
    pages: int = 0
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.text.split()) >= 20


def extract_pdf(data: bytes) -> ExtractionResult:
    try:
        from pypdf import PdfReader
        from pypdf.errors import PyPdfError
    except ImportError:
        return ExtractionResult(method="none", warnings=["PDF text extraction is unavailable on this server (pypdf is not installed)."])
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            return ExtractionResult(method="pypdf", warnings=["The PDF is password-protected, so its text cannot be read."])
        n = len(reader.pages)
        parts = []
        for page in reader.pages[:MAX_PAGES]:
            try:
                parts.append(page.extract_text() or "")
            except Exception:  # one unreadable page should not lose the others
                parts.append("")
        text = "\n".join(parts)
    except (PyPdfError, ValueError, KeyError, OSError, RecursionError):
        return ExtractionResult(method="pypdf", warnings=["The PDF could not be parsed (it may be corrupted)."])
    warnings = []
    if n > MAX_PAGES:
        warnings.append(f"Only the first {MAX_PAGES} pages were analysed.")
    res = ExtractionResult(text=_clean(text), method="pypdf", pages=min(n, MAX_PAGES), warnings=warnings)
    if not res.ok:
        res.warnings.append("Almost no text could be extracted. The PDF may be a scanned image, which ATS systems cannot read either.")
    return res


_P_END = re.compile(r"</w:p>")
_BREAKS = re.compile(r"<w:br\s*/?>|<w:cr\s*/?>")
_TABS = re.compile(r"<w:tab\s*/?>")
_RUN = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)


def extract_docx(data: bytes) -> ExtractionResult:
    # Regex over the XML instead of an XML parser: nothing is expanded, so entity-bomb style files are harmless.
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            info = z.getinfo("word/document.xml")
            if info.file_size > MAX_DOCX_XML_BYTES:
                return ExtractionResult(method="docx_xml", warnings=["The document is too large to analyse."])
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
    except (zipfile.BadZipFile, KeyError, ValueError, OSError):
        return ExtractionResult(method="docx_xml", warnings=["The DOCX file could not be read."])
    xml = _TABS.sub("<w:t>\t</w:t>", xml)
    xml = _BREAKS.sub("</w:p>", xml)
    out = []
    for para in _P_END.split(xml):
        line = "".join(html.unescape(m) for m in _RUN.findall(para))
        out.append(line)
    res = ExtractionResult(text=_clean("\n".join(out)), method="docx_xml", pages=0)
    if not res.ok:
        res.warnings.append("Very little text was found in the document.")
    return res


def _clean(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()[:MAX_TEXT_CHARS]


def extract_text(content_type: str, data: bytes) -> ExtractionResult:
    if content_type == PDF:
        return extract_pdf(data)
    if content_type == DOCX:
        return extract_docx(data)
    return ExtractionResult(warnings=["Unsupported file type."])
