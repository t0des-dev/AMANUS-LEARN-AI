"""URL Extractor Service for web article ingestion with SSRF protection."""

import ipaddress
import re
import socket
import urllib.parse
import urllib.request
from html.parser import HTMLParser


class HTMLTextExtractor(HTMLParser):
    """Clean HTML text extractor that strips scripts, styles, and unwanted markup."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self._skip_depth = 0
        self._skip_tags = {"script", "style", "noscript", "svg", "nav", "footer", "header"}
        self._chunks = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in self._skip_tags:
            self._skip_depth += 1
        elif tag_lower == "title" and not self.title:
            self._in_title = True
        elif tag_lower in ("p", "div", "h1", "h2", "h3", "h4", "li", "br", "article", "section"):
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag_lower == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        if self._in_title:
            self.title += data.strip()
        else:
            text = data.strip()
            if text:
                self._chunks.append(f"{text} ")

    def get_text(self) -> str:
        raw = "".join(self._chunks)
        # Collapse multi-newlines and spaces
        cleaned = re.sub(r"[ \t]+", " ", raw)
        cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
        return cleaned.strip()


class URLExtractorService:
    """Extracts readable text content and title from a web URL securely."""

    @staticmethod
    def validate_url(url: str):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Seuls les protocoles HTTP et HTTPS sont autorisés.")

        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URL invalide : nom d'hôte manquant.")

        # SSRF Protection: resolve host and check private IP
        try:
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local:
                raise ValueError("L'accès aux adresses IP privées, locales ou réservées est interdit.")
        except socket.gaierror:
            raise ValueError(f"Impossible de résoudre le nom d'hôte '{hostname}'.")

    @classmethod
    def fetch_and_extract(cls, url: str) -> tuple[str, str]:
        """Fetches page content, strips HTML markup, and returns (title, extracted_text)."""
        cls.validate_url(url)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36 (AmanusBot/1.0)"
                ),
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr,en;q=0.9",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as response:
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type and "text/plain" not in content_type:
                    raise ValueError(f"Type de contenu non supporté : {content_type}")

                raw_bytes = response.read(10 * 1024 * 1024)  # Max 10 MB
                charset = response.headers.get_content_charset() or "utf-8"
                html_content = raw_bytes.decode(charset, errors="replace")
        except Exception as exc:
            if isinstance(exc, ValueError):
                raise
            raise ValueError(f"Échec de récupération de la page ({url}) : {exc}")

        parser = HTMLTextExtractor()
        parser.feed(html_content)

        extracted_text = parser.get_text()
        title = parser.title or urllib.parse.urlparse(url).netloc

        if len(extracted_text) < 100:
            raise ValueError("Le contenu extrait de cette URL est trop court ou vide.")

        return title, extracted_text
