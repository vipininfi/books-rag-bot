import fitz  # PyMuPDF
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ExtractedLine:
    text: str
    font_size: float
    is_bold: bool
    page: int
    y_position: float


@dataclass
class Section:
    title: str
    paragraphs: List[str]
    start_page: int
    end_page: int


class PDFProcessor:
    """Handles PDF text extraction with layout awareness."""
    
    def __init__(self):
        self.median_font_size = 12.0
    
    def extract_text_with_layout(self, pdf_path: str) -> List[ExtractedLine]:
        """Extract text with font and layout information."""
        doc = fitz.open(pdf_path)
        lines = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            blocks = page.get_text("dict")
            
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["text"].strip():
                                lines.append(ExtractedLine(
                                    text=span["text"].strip(),
                                    font_size=span["size"],
                                    is_bold="bold" in span["font"].lower(),
                                    page=page_num + 1,
                                    y_position=span["bbox"][1]
                                ))
        
        doc.close()
        
        # Calculate median font size for heading detection
        if lines:
            font_sizes = [line.font_size for line in lines]
            font_sizes.sort()
            self.median_font_size = font_sizes[len(font_sizes) // 2]
        
        return lines
    
    def detect_sections(self, lines: List[ExtractedLine]) -> List[Section]:
        """Convert lines into structured sections."""
        sections = []
        current_section = None
        current_paragraphs = []
        
        for line in lines:
            if self._is_heading(line):
                # Save previous section
                if current_section:
                    sections.append(Section(
                        title=current_section,
                        paragraphs=current_paragraphs,
                        start_page=sections[-1].end_page if sections else 1,
                        end_page=line.page
                    ))
                
                # Start new section
                current_section = line.text
                current_paragraphs = []
            else:
                current_paragraphs.append(line.text)
        
        # Add final section
        if current_section:
            sections.append(Section(
                title=current_section,
                paragraphs=current_paragraphs,
                start_page=sections[-1].end_page if sections else 1,
                end_page=line.page if lines else 1
            ))
        
        return sections
    
    def _is_heading(self, line: ExtractedLine) -> bool:
        """Determine if a line is a section heading."""
        # Font size larger than median
        if line.font_size > self.median_font_size * 1.2:
            return True
        
        # Bold and short
        if line.is_bold and len(line.text) < 120:
            return True
        
        # Pattern matching for numbered sections
        text = line.text.strip()
        if self._matches_heading_pattern(text):
            return True
        
        return False
    
    def _matches_heading_pattern(self, text: str) -> bool:
        """Check if text matches common heading patterns."""
        import re
        
        patterns = [
            r'^Chapter\s+\d+',
            r'^\d+\.\s',
            r'^\d+\.\d+\s',
            r'^\d+\.\d+\.\d+\s',
            r'^[A-Z\s]{10,}$',  # ALL CAPS
        ]
        
        for pattern in patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False