from PyPDF2 import PdfReader
from typing import Optional

class PDFParser:
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                text = ""
                for page in reader.pages:
                    if page.extract_text():
                        text += page.extract_text()
                return text if text.strip() else None
        except Exception as e:
            return None
    
    @staticmethod
    def is_scanned_pdf(file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if not text or not text.strip():
                        return True
            return False
        except Exception as e:
            return True