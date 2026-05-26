from PyPDF2 import PdfReader
from typing import Optional

class PDFParser:
    MAX_PAGES = 30  # 最多提取前30页
    MAX_CHARS = 15000  # 最多15000字符

    @staticmethod
    def extract_text(file_path: str, max_pages: int = None, max_chars: int = None) -> Optional[str]:
        try:
            max_pages = max_pages or PDFParser.MAX_PAGES
            max_chars = max_chars or PDFParser.MAX_CHARS

            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                total_pages = len(reader.pages)

                text = ""
                pages_to_extract = min(max_pages, total_pages)

                for i in range(pages_to_extract):
                    page = reader.pages[i]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                        if len(text) >= max_chars:
                            text = text[:max_chars]
                            break

                return text if text.strip() else None

        except Exception as e:
            print(f"PDF解析错误: {e}")
            return None

    @staticmethod
    def is_scanned_pdf(file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                check_pages = min(5, len(reader.pages))

                for i in range(check_pages):
                    page = reader.pages[i]
                    text = page.extract_text()
                    if text and len(text.strip()) > 50:
                        return False

                return True
        except Exception as e:
            return True

    @staticmethod
    def get_pdf_info(file_path: str) -> dict:
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                return {
                    "total_pages": len(reader.pages),
                    "is_encrypted": reader.is_encrypted,
                    "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2)
                }
        except:
            return {"error": "无法读取文件信息"}

import os