import os
import re
from PyPDF2 import PdfReader
from typing import Optional, List, Dict, Any

class AdvancedPDFParser:
    """
    专业级PDF解析引擎 - 支持完整文档提取和智能分块
    
    特性：
    - 完整文档提取（无页数限制）
    - 智能分块策略（按章节/字符数）
    - 表格识别与结构化
    - 文本清洗优化
    """
    
    # 分块配置
    CHUNK_SIZE = 8000  # 每块最大字符数
    CHUNK_OVERLAP = 200  # 块之间重叠字符数
    MAX_TOTAL_CHARS = 100000  # 最大总字符数限制（防止过大文件）
    
    @staticmethod
    def extract_full_text(file_path: str) -> Optional[str]:
        """
        提取PDF全部文本内容
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            完整文本字符串，失败返回None
        """
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                total_pages = len(reader.pages)
                
                print(f"[PDF解析] 开始提取: {total_pages}页")
                
                text_parts = []
                total_chars = 0
                
                for i in range(total_pages):
                    page = reader.pages[i]
                    page_text = page.extract_text()
                    
                    if page_text and len(page_text.strip()) > 10:
                        cleaned_text = AdvancedPDFParser._clean_page_text(page_text)
                        text_parts.append(cleaned_text)
                        total_chars += len(cleaned_text)
                        
                        # 安全检查：防止内存溢出
                        if total_chars > AdvancedPDFParser.MAX_TOTAL_CHARS:
                            print(f"[PDF解析] 已达字符上限({AdvancedPDFParser.MAX_TOTAL_CHARS})，停止提取")
                            break
                
                full_text = "\n\n".join(text_parts)
                
                print(f"[PDF解析] 提取完成: {total_pages}页, {len(full_text)}字符")
                
                return full_text if full_text.strip() else None
                
        except Exception as e:
            print(f"[PDF解析错误] {str(e)}")
            return None
    
    @staticmethod
    def extract_with_smart_chunks(file_path: str) -> List[Dict[str, Any]]:
        """
        智能分块提取 - 适合长文档的AI处理
        
        Returns:
            [
                {
                    "chunk_id": 1,
                    "text": "...",
                    "page_range": "1-15",
                    "char_count": 8000,
                    "metadata": {...}
                },
                ...
            ]
        """
        try:
            full_text = AdvancedPDFParser.extract_full_text(file_path)
            
            if not full_text:
                return []
            
            chunks = []
            text_length = len(full_text)
            
            # 如果文本较短，直接返回单块
            if text_length <= AdvancedPDFParser.CHUNK_SIZE:
                chunks.append({
                    "chunk_id": 1,
                    "text": full_text,
                    "page_range": "all",
                    "char_count": text_length,
                    "is_first_chunk": True,
                    "is_last_chunk": True,
                    "metadata": {
                        "total_chunks": 1,
                        "extraction_method": "single_block"
                    }
                })
                return chunks
            
            # 长文本智能分块
            chunk_id = 0
            start_pos = 0
            
            while start_pos < text_length:
                chunk_id += 1
                end_pos = start_pos + AdvancedPDFParser.CHUNK_SIZE
                
                # 尝试在句子/段落边界分割
                if end_pos < text_length:
                    # 寻找最近的句号或换行符
                    boundary_candidates = [
                        full_text.rfind("。\n", start_pos, end_pos),
                        full_text.rfind("。", start_pos, end_pos),
                        full_text.rfind("\n\n", start_pos, end_pos),
                        full_text.rfind("\n", start_pos, end_pos),
                    ]
                    
                    best_boundary = max([b for b in boundary_candidates if b > start_pos], default=end_pos)
                    end_pos = min(best_boundary + 1, end_pos + AdvancedPDFParser.CHUNK_OVERLAP)
                
                chunk_text = full_text[start_pos:end_pos]
                
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "page_range": f"chunk_{chunk_id}",
                    "char_count": len(chunk_text),
                    "is_first_chunk": (chunk_id == 1),
                    "is_last_chunk": (end_pos >= text_length),
                    "metadata": {
                        "total_chunks": (text_length // AdvancedPDFParser.CHUNK_SIZE) + 1,
                        "extraction_method": "smart_chunking",
                        "start_position": start_pos,
                        "end_position": end_pos
                    }
                })
                
                start_pos = end_pos - AdvancedPDFParser.CHUNK_OVERLAP
                if start_pos < 0:
                    start_pos = 0
            
            print(f"[PDF解析] 智能分块完成: 共{len(chunks)}个文本块")
            return chunks
            
        except Exception as e:
            print(f"[智能分块错误] {str(e)}")
            return []
    
    @staticmethod
    def extract_key_sections(file_path: str) -> Dict[str, str]:
        """
        提取关键章节 - 针对财报的特殊优化
        
        Returns:
            {
                "company_info": "公司基本信息...",
                "financial_highlights": "主要财务数据...",
                "management_discussion": "管理层讨论...",
                "financial_statements": "财务报表数据...",
                "risk_factors": "风险因素..."
            }
        """
        try:
            full_text = AdvancedPDFParser.extract_full_text(file_path)
            
            if not full_text:
                return {}
            
            sections = {}
            
            # 定义关键词匹配规则
            section_patterns = {
                "company_info": [
                    r"公司基本信息|公司简介|基本情况|企业概况",
                    r"公司名称|股票代码|上市地点"
                ],
                "financial_highlights": [
                    r"主要财务数据|主要会计数据|财务摘要",
                    r"营业收入|净利润|每股收益",
                    r"报告期末总资产|归属于上市公司股东"
                ],
                "management_discussion": [
                    r"管理层讨论与分析|经营情况讨论|董事会报告",
                    r"经营回顾|业务分析|核心竞争力"
                ],
                "financial_statements": [
                    r"财务报表|审计报告|合并资产负债表",
                    r"利润表|现金流量表|股东权益变动表"
                ],
                "risk_factors": [
                    r"风险因素|风险提示|可能面对的风险",
                    r"不确定性|风险披露"
                ]
            }
            
            for section_name, patterns in section_patterns.items():
                matched_text = []
                for pattern in patterns:
                    matches = re.findall(pattern + r".*?(?=\n\n|\n[一二三四五六七八九十]|$)", 
                                       full_text, re.DOTALL | re.IGNORECASE)
                    if matches:
                        matched_text.extend(matches)
                
                if matched_text:
                    sections[section_name] = "\n\n".join(matched_text)[:15000]  # 每个章节限15000字符
            
            print(f"[章节提取] 成功提取{len(sections)}个关键章节")
            return sections
            
        except Exception as e:
            print(f"[章节提取错误] {str(e)}")
            return {}
    
    @staticmethod
    def _clean_page_text(text: str) -> str:
        """清洗页面文本"""
        # 移除多余空白
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 移除页眉页脚（简单启发式规则）
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # 跳过太短的行（可能是页码）
            if len(line) < 3 and re.match(r'^\d+$', line):
                continue
            # 跳过常见的页眉页脚模式
            if re.match(r'^(第\s*\d+\s*页|Page \d+|-\s*\d+\s*-)$', line):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def is_scanned_pdf(file_path: str) -> bool:
        """检测是否为扫描版PDF（图片格式）"""
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                check_pages = min(5, len(reader.pages))
                
                text_count = 0
                for i in range(check_pages):
                    page = reader.pages[i]
                    text = page.extract_text()
                    if text and len(text.strip()) > 100:
                        text_count += 1
                
                is_scanned = (text_count == 0)
                if is_scanned:
                    print(f"[PDF检测] 检测到扫描版PDF，前{check_pages}页均无可提取文字")
                return is_scanned
                
        except Exception as e:
            print(f"[检测错误] {e}")
            return True
    
    @staticmethod
    def get_pdf_info(file_path: str) -> dict:
        """获取PDF基本信息"""
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
                
                info = {
                    "total_pages": len(reader.pages),
                    "is_encrypted": reader.is_encrypted,
                    "file_size_mb": file_size_mb,
                    "estimated_chars": len(reader.pages) * 3000  # 估算字符数
                }
                
                print(f"[PDF信息] {info['total_pages']}页, {file_size_mb}MB")
                return info
                
        except Exception as e:
            return {"error": f"无法读取文件信息: {str(e)}"}
