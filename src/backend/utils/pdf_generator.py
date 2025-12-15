"""
PDF generator for creating market research reports with citation markers.
Supports embedding charts and formatting report sections.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

from utils.citation_manager import CitationManager
from config import settings

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """
    Generates PDF reports with citations and visualizations.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize PDF generator.
        
        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = output_dir or Path(settings.reports_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        logger.info("PDF Report Generator initialized")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=12,
            keepWithNext=True
        ))
        
        # Subsection heading style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceBefore=16,
            spaceAfter=10
        ))
        
        # Body text with justification
        self.styles.add(ParagraphStyle(
            name='JustifiedBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
        
        # Citation style
        self.styles.add(ParagraphStyle(
            name='Citation',
            parent=self.styles['BodyText'],
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            leftIndent=20
        ))
    
    def generate_report(
        self,
        report_data: Dict[str, Any],
        citation_manager: CitationManager,
        output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate a PDF report.
        
        Args:
            report_data: Report data dictionary
            citation_manager: Citation manager instance
            output_filename: Optional output filename
            
        Returns:
            Path to generated PDF
        """
        try:
            # Generate filename
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                topic = report_data.get("topic", "research").replace(" ", "_")[:30]
                output_filename = f"report_{topic}_{timestamp}.pdf"
            
            output_path = self.output_dir / output_filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build content
            story = []
            
            # Title page
            story.extend(self._create_title_page(report_data))
            story.append(PageBreak())
            
            # Table of contents (optional)
            if report_data.get("include_toc", False):
                story.extend(self._create_toc(report_data))
                story.append(PageBreak())
            
            # Report sections
            sections = report_data.get("sections", [])
            for section in sections:
                story.extend(self._create_section(section))
            
            # Visualizations
            visualizations = report_data.get("visualizations", [])
            if visualizations:
                story.append(PageBreak())
                story.extend(self._create_visualizations_section(visualizations))
            
            # References
            story.append(PageBreak())
            story.extend(self._create_references(citation_manager))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"PDF report generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    def _create_title_page(self, report_data: Dict[str, Any]) -> List:
        """Create title page elements."""
        elements = []
        
        # Title
        title = report_data.get("title", "Market Research Report")
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Subtitle/Topic
        topic = report_data.get("topic", "")
        if topic:
            elements.append(Paragraph(topic, self.styles['Heading2']))
            elements.append(Spacer(1, 0.3*inch))
        
        # Date
        date = report_data.get("date", datetime.now().strftime("%B %d, %Y"))
        elements.append(Paragraph(f"Generated: {date}", self.styles['Normal']))
        
        # Metadata
        metadata = report_data.get("metadata", {})
        if metadata:
            elements.append(Spacer(1, 1*inch))
            for key, value in metadata.items():
                elements.append(Paragraph(f"<b>{key}:</b> {value}", self.styles['Normal']))
        
        return elements
    
    def _create_toc(self, report_data: Dict[str, Any]) -> List:
        """Create table of contents."""
        elements = []
        
        elements.append(Paragraph("Table of Contents", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.3*inch))
        
        sections = report_data.get("sections", [])
        for i, section in enumerate(sections, 1):
            title = section.get("title", f"Section {i}")
            elements.append(Paragraph(f"{i}. {title}", self.styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _create_section(self, section: Dict[str, Any]) -> List:
        """Create a report section."""
        elements = []
        
        # Section title
        title = section.get("title", "Untitled Section")
        elements.append(Paragraph(title, self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Section content
        content = section.get("content", "")
        
        # Split content by paragraphs
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                # Check if it's a subsection heading (starts with ##)
                if para.strip().startswith('##'):
                    heading_text = para.strip().replace('##', '').strip()
                    elements.append(Paragraph(heading_text, self.styles['SubsectionHeading']))
                else:
                    # Add citation markers [1], [2], etc. as superscript
                    formatted_para = self._format_citations(para)
                    elements.append(Paragraph(formatted_para, self.styles['JustifiedBody']))
                
                elements.append(Spacer(1, 0.15*inch))
        
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _format_citations(self, text: str) -> str:
        """Format citation markers in text."""
        # Convert [1] style citations to superscript
        import re
        
        def replace_citation(match):
            num = match.group(1)
            return f'<super><a href="#ref{num}">[{num}]</a></super>'
        
        formatted = re.sub(r'\[(\d+)\]', replace_citation, text)
        return formatted
    
    def _create_visualizations_section(self, visualizations: List[Dict[str, Any]]) -> List:
        """Create visualizations section."""
        elements = []
        
        elements.append(Paragraph("Visualizations", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        for viz in visualizations:
            # Visualization title
            title = viz.get("title", "Chart")
            elements.append(Paragraph(title, self.styles['SubsectionHeading']))
            
            # Add image if path provided
            image_path = viz.get("png_path") or viz.get("html_path")
            if image_path and Path(image_path).exists():
                try:
                    img = Image(image_path, width=6*inch, height=4*inch)
                    elements.append(img)
                except Exception as e:
                    logger.warning(f"Could not add image {image_path}: {e}")
                    elements.append(Paragraph(f"[Chart: {title}]", self.styles['Normal']))
            else:
                elements.append(Paragraph(f"[Chart: {title}]", self.styles['Normal']))
            
            # Description
            description = viz.get("description", "")
            if description:
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph(description, self.styles['Normal']))
            
            elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_references(self, citation_manager: CitationManager) -> List:
        """Create references section."""
        elements = []
        
        elements.append(Paragraph("References", self.styles['SectionHeading']))
        elements.append(Spacer(1, 0.2*inch))
        
        citations = citation_manager.get_all_citations()
        
        if not citations:
            elements.append(Paragraph("No references available.", self.styles['Normal']))
            return elements
        
        for citation in citations:
            # Format citation with anchor for linking
            citation_text = f'<a name="ref{citation.citation_id}"></a>[{citation.citation_id}] {citation.source}'
            if citation.url:
                citation_text += f' - <link href="{citation.url}">{citation.url}</link>'
            if citation.retrieved_at:
                if isinstance(citation.retrieved_at, datetime):
                    date_str = citation.retrieved_at.strftime('%Y-%m-%d')
                else:
                    date_str = str(citation.retrieved_at)[:10]
                citation_text += f' (Retrieved: {date_str})'
            
            elements.append(Paragraph(citation_text, self.styles['Citation']))
            elements.append(Spacer(1, 0.1*inch))
        
        return elements


def create_pdf_generator(output_dir: Optional[Path] = None) -> PDFReportGenerator:
    """
    Factory function to create a PDF generator.
    
    Args:
        output_dir: Optional output directory
        
    Returns:
        PDFReportGenerator instance
    """
    return PDFReportGenerator(output_dir=output_dir)

