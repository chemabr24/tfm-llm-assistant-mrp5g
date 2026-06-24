import uuid
from pypdf import PdfReader

class DocumentService:
    """Servicio para extraer y trocear texto de documentos PDF."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_by_page(self, file_bytes: bytes) -> list[dict]:
        """
        Extrae el texto de un PDF página a página.
        
        Devuelve una lista de diccionarios con el texto y número de página.
        """
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({
                    "text": text.strip(),
                    "page": i + 1
                })

        return pages

    def chunk_text(self, pages: list[dict], source: str) -> list[dict]:
        """
        Trocea el texto en chunks con solapamiento.
        
        Cada chunk incluye: id, text, page, source.
        """
        chunks = []

        for page_data in pages:
            text = page_data["text"]
            page_num = page_data["page"]
            words = text.split()

            start = 0
            while start < len(words):
                end = start + self.chunk_size
                chunk_words = words[start:end]
                chunk_text = " ".join(chunk_words)

                chunks.append({
                    "id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "page": page_num,
                    "source": source
                })

                if end >= len(words):
                    break

                start += self.chunk_size - self.chunk_overlap

        return chunks

    def process_pdf(self, file_bytes: bytes, filename: str) -> list[dict]:
        """
        Pipeline completo: extrae texto y genera chunks de un PDF.
        
        Devuelve la lista de chunks listos para ser embebidos.
        """
        pages = self.extract_text_by_page(file_bytes)
        chunks = self.chunk_text(pages, source=filename)
        return chunks