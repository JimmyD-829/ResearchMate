import fitz
from typing import Optional

class PDFParser:
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text if text.strip() else None
        except Exception as e:
            return None
    
    @staticmethod
    def is_scanned_pdf(file_path: str) -> bool:
        try:
            doc = fitz.open(file_path)
            for page in doc:
                if not page.get_text().strip():
                    return True
            return False
        except Exception as e:
            return True
