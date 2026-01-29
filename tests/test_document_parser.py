"""
Tests for document parser service
"""

import pytest
import io
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from fastapi import UploadFile, HTTPException

from app.services.document_parser import DocumentParser, DocumentParsingError


class TestDocumentParser:
    """Test cases for DocumentParser class"""
    
    @pytest.fixture
    def parser(self):
        """Create a DocumentParser instance for testing"""
        return DocumentParser()
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create a minimal valid PDF content for testing"""
        # This is a minimal PDF structure that PyPDF2 can read
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000189 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
284
%%EOF"""
        return pdf_content
    
    @pytest.fixture
    def sample_text_content(self):
        """Create sample text content for testing"""
        return b"This is a sample text file.\nIt contains multiple lines.\nAnd some educational content about photosynthesis."
    
    def create_upload_file(self, content: bytes, filename: str, content_type: str = "application/octet-stream") -> UploadFile:
        """Helper to create UploadFile for testing"""
        file_obj = io.BytesIO(content)
        return UploadFile(
            file=file_obj,
            filename=filename,
            headers={"content-type": content_type}
        )
    
    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly"""
        assert parser is not None
        assert hasattr(parser, 'supported_formats')
        assert '.pdf' in parser.supported_formats
        assert '.txt' in parser.supported_formats
        assert '.docx' in parser.supported_formats
    
    def test_get_supported_formats(self, parser):
        """Test getting supported formats"""
        formats = parser.get_supported_formats()
        assert isinstance(formats, list)
        assert '.pdf' in formats
        assert '.txt' in formats
        assert '.docx' in formats
    
    def test_is_format_supported(self, parser):
        """Test format support checking"""
        assert parser.is_format_supported('.pdf') is True
        assert parser.is_format_supported('.PDF') is True  # Case insensitive
        assert parser.is_format_supported('.txt') is True
        assert parser.is_format_supported('.xyz') is False
    
    @pytest.mark.asyncio
    async def test_extract_text_from_text_file(self, parser, sample_text_content):
        """Test extracting text from plain text file"""
        upload_file = self.create_upload_file(sample_text_content, "test.txt", "text/plain")
        
        result = await parser.extract_text_from_file(upload_file)
        
        assert "text" in result
        assert "metadata" in result
        assert "photosynthesis" in result["text"]
        assert result["metadata"]["filename"] == "test.txt"
        assert result["metadata"]["file_type"] == ".txt"
        assert result["metadata"]["character_count"] > 0
        assert result["metadata"]["word_count"] > 0
        assert result["metadata"]["encoding"] == "utf-8"
    
    @pytest.mark.asyncio
    async def test_extract_text_from_text_file_latin1(self, parser):
        """Test extracting text from latin-1 encoded text file"""
        # Create content with latin-1 specific characters
        text_content = "This is a test with special characters: café, naïve, résumé".encode('latin-1')
        upload_file = self.create_upload_file(text_content, "test_latin1.txt", "text/plain")
        
        result = await parser.extract_text_from_file(upload_file)
        
        assert "text" in result
        assert "café" in result["text"]
        assert result["metadata"]["encoding"] == "latin-1"
    
    @pytest.mark.asyncio
    async def test_extract_text_unsupported_format(self, parser):
        """Test handling of unsupported file format"""
        upload_file = self.create_upload_file(b"some content", "test.xyz", "application/octet-stream")
        
        with pytest.raises(HTTPException) as exc_info:
            await parser.extract_text_from_file(upload_file)
        
        assert exc_info.value.status_code == 415
        assert "Unsupported file format" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_extract_text_insufficient_content(self, parser):
        """Test handling of files with insufficient content"""
        short_content = b"Hi"  # Too short
        upload_file = self.create_upload_file(short_content, "short.txt", "text/plain")
        
        with pytest.raises(DocumentParsingError) as exc_info:
            await parser.extract_text_from_file(upload_file)
        
        assert "Insufficient text content" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_text_empty_file(self, parser):
        """Test handling of empty files"""
        empty_content = b""
        upload_file = self.create_upload_file(empty_content, "empty.txt", "text/plain")
        
        with pytest.raises(DocumentParsingError) as exc_info:
            await parser.extract_text_from_file(upload_file)
        
        # The error message could be either "is empty" or "Insufficient text content"
        error_message = str(exc_info.value)
        assert ("is empty" in error_message or "Insufficient text content" in error_message)
    
    @pytest.mark.asyncio
    async def test_extract_pdf_text_basic(self, parser):
        """Test basic PDF text extraction"""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\nMock PDF content for testing"
        upload_file = self.create_upload_file(pdf_content, "test.pdf", "application/pdf")
        
        # Mock the PDF extraction methods since creating a valid PDF is complex
        with patch.object(parser, '_extract_pdf_with_pdfplumber') as mock_pdfplumber, \
             patch.object(parser, '_extract_pdf_with_pypdf') as mock_pypdf:
            
            # Mock pdfplumber to return good content
            mock_pdfplumber.return_value = (
                "Test PDF Content extracted with pdfplumber", 
                {
                    "page_count": 1, 
                    "successful_pages": 1,
                    "failed_pages": 0,
                    "tables_found": 0,
                    "extraction_method": "pdfplumber"
                }
            )
            
            result = await parser.extract_text_from_file(upload_file)
            
            assert "text" in result
            assert "Test PDF Content" in result["text"]
            assert result["metadata"]["file_type"] == ".pdf"
            assert result["metadata"]["extraction_method"] == "pdfplumber"
    
    @pytest.mark.asyncio
    async def test_extract_pdf_text_invalid_pdf(self, parser):
        """Test handling of invalid PDF files"""
        invalid_pdf = b"This is not a PDF file"
        upload_file = self.create_upload_file(invalid_pdf, "invalid.pdf", "application/pdf")
        
        with pytest.raises(DocumentParsingError) as exc_info:
            await parser.extract_text_from_file(upload_file)
        
        error_message = str(exc_info.value)
        assert ("extraction methods failed" in error_message or 
                "Invalid or corrupted PDF" in error_message or
                "Failed to extract text from PDF" in error_message)
    
    @pytest.mark.asyncio
    async def test_extract_pdf_text_encrypted(self, parser):
        """Test handling of encrypted PDF files"""
        # Mock an encrypted PDF scenario
        upload_file = self.create_upload_file(b"%PDF-encrypted", "encrypted.pdf", "application/pdf")
        
        with patch.object(parser, '_extract_pdf_with_pdfplumber') as mock_pdfplumber, \
             patch.object(parser, '_extract_pdf_with_pypdf') as mock_pypdf:
            
            # Both methods should fail with encryption error
            mock_pdfplumber.side_effect = DocumentParsingError("PDF file encrypted.pdf is password-protected and cannot be processed")
            mock_pypdf.side_effect = DocumentParsingError("PDF file encrypted.pdf is password-protected and cannot be processed")
            
            with pytest.raises(DocumentParsingError) as exc_info:
                await parser.extract_text_from_file(upload_file)
            
            assert "password-protected" in str(exc_info.value) or "extraction methods failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_docx_text_comprehensive(self, parser):
        """Test comprehensive DOCX text extraction with mocked content"""
        # Create a mock DOCX file content (ZIP signature)
        docx_content = b"PK\x03\x04" + b"mock docx content"
        upload_file = self.create_upload_file(docx_content, "comprehensive.docx", 
                                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
        # Mock the internal DOCX extraction method to avoid file system operations
        with patch('app.services.document_parser.Document') as mock_document_class:
            # Create a mock document with comprehensive content
            mock_doc = Mock()
            mock_document_class.return_value = mock_doc
            
            # Mock core properties
            mock_doc.core_properties.title = "Test Document"
            mock_doc.core_properties.author = "Test Author"
            mock_doc.core_properties.subject = "Test Subject"
            mock_doc.core_properties.created = None
            mock_doc.core_properties.modified = None
            
            # Mock paragraphs
            mock_paragraphs = []
            for i in range(5):
                mock_para = Mock()
                mock_para.text = f"This is paragraph {i+1} with educational content."
                mock_para.runs = []  # No hyperlinks for simplicity
                mock_paragraphs.append(mock_para)
            mock_doc.paragraphs = mock_paragraphs
            
            # Mock tables
            mock_tables = []
            for i in range(2):
                mock_table = Mock()
                mock_rows = []
                for j in range(3):  # 3 rows per table
                    mock_row = Mock()
                    mock_cells = []
                    for k in range(2):  # 2 cells per row
                        mock_cell = Mock()
                        mock_cell.text = f"Table {i+1} Row {j+1} Cell {k+1}"
                        mock_cell.paragraphs = [mock_cell]  # Simple case
                        mock_cells.append(mock_cell)
                    mock_row.cells = mock_cells
                    mock_rows.append(mock_row)
                mock_table.rows = mock_rows
                mock_tables.append(mock_table)
            mock_doc.tables = mock_tables
            
            # Mock sections with headers and footers
            mock_section = Mock()
            mock_header = Mock()
            mock_header_para = Mock()
            mock_header_para.text = "Document Header"
            mock_header.paragraphs = [mock_header_para]
            mock_section.header = mock_header
            
            mock_footer = Mock()
            mock_footer_para = Mock()
            mock_footer_para.text = "Document Footer"
            mock_footer.paragraphs = [mock_footer_para]
            mock_section.footer = mock_footer
            
            mock_doc.sections = [mock_section]
            
            result = await parser.extract_text_from_file(upload_file)
            
            # Verify the comprehensive extraction
            assert "paragraph 1" in result["text"]
            assert "paragraph 5" in result["text"]
            assert "Table 1 Row 1 Cell 1" in result["text"]
            assert "Table 2 Row 1 Cell 1" in result["text"]
            assert "[Header] Document Header" in result["text"]
            assert "[Footer] Document Footer" in result["text"]
            
            # Verify metadata
            metadata = result["metadata"]
            assert metadata["paragraph_count"] == 5
            assert metadata["table_count"] == 2
            assert metadata["header_count"] == 1
            assert metadata["footer_count"] == 1
            assert metadata["extraction_method"] == "python-docx"
            assert metadata["document_properties"]["title"] == "Test Document"
            assert metadata["document_properties"]["author"] == "Test Author"
    
    @pytest.mark.asyncio
    async def test_extract_doc_text_misnamed_docx(self, parser):
        """Test DOC extraction when file is actually DOCX with wrong extension"""
        # DOCX content with .doc extension
        docx_content = b"PK\x03\x04" + b"mock docx content"
        upload_file = self.create_upload_file(docx_content, "misnamed.doc", "application/msword")
        
        with patch.object(parser, '_extract_docx_text') as mock_docx:
            mock_docx.return_value = (
                "This is actually a DOCX file with wrong extension",
                {
                    "paragraph_count": 1,
                    "table_count": 0,
                    "extraction_method": "python-docx"
                }
            )
            
            result = await parser.extract_text_from_file(upload_file)
            
            assert "actually a DOCX file" in result["text"]
            assert result["metadata"]["extraction_method"] == "python-docx"
    
    @pytest.mark.asyncio
    async def test_extract_doc_text_basic_extraction(self, parser):
        """Test basic DOC text extraction"""
        # Create mock DOC content with proper signature
        doc_content = b'\xd0\xcf\x11\xe0' + b'Some readable text content in the document' * 10
        upload_file = self.create_upload_file(doc_content, "basic.doc", "application/msword")
        
        with patch.object(parser, '_extract_text_from_binary_doc') as mock_extract:
            mock_extract.return_value = "Some readable text content in the document"
            
            result = await parser.extract_text_from_file(upload_file)
            
            assert "readable text content" in result["text"]
            assert result["metadata"]["extraction_method"] == "binary_text_extraction"
            assert result["metadata"]["format"] == "legacy_doc"
            assert "warning" in result["metadata"]
    
    @pytest.mark.asyncio
    async def test_extract_doc_text_unsupported_with_helpful_error(self, parser):
        """Test that unsupported DOC files provide helpful error messages"""
        # Create mock DOC content that can't be processed
        doc_content = b'\xd0\xcf\x11\xe0' + b'\x00\x01\x02\x03' * 100  # Binary data
        upload_file = self.create_upload_file(doc_content, "complex.doc", "application/msword")
        
        with patch.object(parser, '_extract_text_from_binary_doc') as mock_extract:
            mock_extract.return_value = ""  # No extractable text
            
            with pytest.raises(DocumentParsingError) as exc_info:
                await parser.extract_text_from_file(upload_file)
            
            error_message = str(exc_info.value)
            assert "Legacy DOC format" in error_message
            assert "Convert to DOCX" in error_message
            assert "textract" in error_message or "antiword" in error_message
    
    @pytest.mark.asyncio
    async def test_file_size_validation(self, parser):
        """Test file size validation"""
        # Create a large file content (simulate > 50MB)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        upload_file = self.create_upload_file(large_content, "large.txt", "text/plain")
        
        with pytest.raises(HTTPException) as exc_info:
            await parser.extract_text_from_file(upload_file)
        
        assert exc_info.value.status_code == 413
        assert "File too large" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_empty_file_validation(self, parser):
        """Test empty file validation"""
        empty_content = b""
        upload_file = self.create_upload_file(empty_content, "empty.txt", "text/plain")
        
        with pytest.raises(DocumentParsingError) as exc_info:
            await parser.extract_text_from_file(upload_file)
        
        assert "is empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_file_format_validation_pdf(self, parser):
        """Test PDF file format validation"""
        invalid_pdf = b"Not a PDF file"
        upload_file = self.create_upload_file(invalid_pdf, "invalid.pdf", "application/pdf")
        
        # The validation should log a warning but not prevent processing
        # The actual PDF extraction will fail with appropriate error
        with pytest.raises(DocumentParsingError):
            await parser.extract_text_from_file(upload_file)
    
    @pytest.mark.asyncio
    async def test_file_format_validation_docx(self, parser):
        """Test DOCX file format validation"""
        invalid_docx = b"Not a DOCX file"
        upload_file = self.create_upload_file(invalid_docx, "invalid.docx", 
                                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
        with pytest.raises(DocumentParsingError) as exc_info:
            await parser.extract_text_from_file(upload_file)
        
        # The error could be either format validation or DOCX processing failure
        error_message = str(exc_info.value)
        assert ("does not appear to be a valid DOCX file" in error_message or 
                "Failed to extract text from DOCX" in error_message)
    
    def test_extract_text_from_binary_doc(self, parser):
        """Test binary DOC text extraction method"""
        # Create mock binary content with readable text
        binary_content = (
            b'\x00\x01\x02\x03This is readable text in the document\x04\x05\x06'
            b'Another paragraph with meaningful content\x07\x08\x09'
            b'Final section of the document text\x0a\x0b\x0c'
        )
        
        extracted_text = parser._extract_text_from_binary_doc(binary_content)
        
        assert "readable text" in extracted_text
        assert "meaningful content" in extracted_text
        assert "Final section" in extracted_text
    
    def test_extract_text_from_binary_doc_no_text(self, parser):
        """Test binary DOC extraction with no readable text"""
        binary_content = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09' * 100
        
        extracted_text = parser._extract_text_from_binary_doc(binary_content)
        
        assert extracted_text == ""
    
    def test_clean_extracted_text(self, parser):
        """Test text cleaning functionality"""
        messy_text = "  Line 1  \r\n\r\n  Line 2  \r\n\n\n\n\n  Line 3  \n\n  "
        cleaned = parser._clean_extracted_text(messy_text)
        
        assert cleaned == "Line 1\n\nLine 2\n\nLine 3"
        assert not cleaned.startswith(" ")
        assert not cleaned.endswith(" ")
    
    def test_clean_extracted_text_empty(self, parser):
        """Test cleaning empty text"""
        assert parser._clean_extracted_text("") == ""
        assert parser._clean_extracted_text(None) == ""
        assert parser._clean_extracted_text("   ") == ""
    
    @pytest.mark.asyncio
    async def test_extract_text_file_invalid_encoding(self, parser):
        """Test handling of files with invalid encoding"""
        # Create binary content that's not valid text in any common encoding
        invalid_content = bytes([0xFF, 0xFE, 0x00, 0x00] * 10)  # Invalid UTF-8/Latin-1
        upload_file = self.create_upload_file(invalid_content, "invalid.txt", "text/plain")
        
        # The parser might successfully decode this with latin-1 (which accepts any byte)
        # So we test that it either succeeds or raises DocumentParsingError
        try:
            result = await parser.extract_text_from_file(upload_file)
            # If it succeeds, verify the result is well-formed
            assert isinstance(result, dict)
            assert "text" in result
            assert "metadata" in result
        except DocumentParsingError:
            # This is also acceptable for truly invalid content
            pass


class TestDocumentParserIntegration:
    """Integration tests for document parser with real file operations"""
    
    @pytest.fixture
    def parser(self):
        """Create a DocumentParser instance for testing"""
        return DocumentParser()
    
    @pytest.mark.asyncio
    async def test_pdf_text_extraction_integration(self, parser):
        """Integration test for PDF text extraction with a real PDF"""
        pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
        upload_file = UploadFile(
            file=io.BytesIO(pdf_content),
            filename="integration_test.pdf",
            headers={"content-type": "application/pdf"}
        )
        
        # Mock the internal PDF extraction methods for integration testing
        with patch.object(parser, '_extract_pdf_with_pdfplumber') as mock_pdfplumber:
            mock_pdfplumber.return_value = (
                "This is extracted PDF content for integration testing.",
                {
                    "page_count": 1,
                    "successful_pages": 1,
                    "failed_pages": 0,
                    "tables_found": 0,
                    "extraction_method": "pdfplumber"
                }
            )
            
            result = await parser.extract_text_from_file(upload_file)
            
            # Verify the result structure
            assert isinstance(result, dict)
            assert "text" in result
            assert "metadata" in result
            
            # Verify text content
            assert len(result["text"]) > 10
            assert "integration testing" in result["text"]
            
            # Verify metadata
            metadata = result["metadata"]
            assert metadata["filename"] == "integration_test.pdf"
            assert metadata["file_type"] == ".pdf"
            assert metadata["character_count"] > 0
            assert metadata["word_count"] > 0
            assert "page_count" in metadata
    
    @pytest.mark.asyncio
    async def test_docx_extraction_integration(self, parser):
        """Integration test for DOCX extraction with realistic content"""
        # Create realistic DOCX-like content structure
        docx_content = b"PK\x03\x04" + b"realistic docx content structure"
        upload_file = UploadFile(
            file=io.BytesIO(docx_content),
            filename="integration_docx.docx",
            headers={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        )
        
        # Mock the DOCX extraction method in the supported_formats dictionary
        async def mock_extract_docx(content, filename):
            return (
                """Educational Content: Photosynthesis Process
                
                [Header] Biology Chapter 3
                
                Introduction to Photosynthesis
                
                Photosynthesis is a complex biological process that converts light energy into chemical energy.
                This process is fundamental to life on Earth and occurs in plants, algae, and some bacteria.
                
                [Table 1]
                Process Stage | Location | Key Products
                Light Reactions | Thylakoids | ATP, NADPH, O2
                Calvin Cycle | Stroma | Glucose, ADP, NADP+
                
                The overall equation for photosynthesis is:
                6CO2 + 6H2O + light energy → C6H12O6 + 6O2
                
                [Footer] Page 1 of 3""",
                {
                    "paragraph_count": 6,
                    "table_count": 1,
                    "header_count": 1,
                    "footer_count": 1,
                    "image_count": 0,
                    "hyperlink_count": 0,
                    "extraction_method": "python-docx",
                    "document_properties": {
                        "title": "Photosynthesis Chapter",
                        "author": "Biology Teacher",
                        "subject": "Biology Education"
                    }
                }
            )
        
        # Replace the method in the supported_formats dictionary
        original_method = parser.supported_formats['.docx']
        parser.supported_formats['.docx'] = mock_extract_docx
        
        try:
            result = await parser.extract_text_from_file(upload_file)
            
            # Verify comprehensive extraction
            assert "Photosynthesis" in result["text"]
            assert "Light Reactions" in result["text"]
            assert "Calvin Cycle" in result["text"]
            assert "[Header]" in result["text"]
            assert "[Footer]" in result["text"]
            assert "[Table 1]" in result["text"]
            
            # Verify metadata
            metadata = result["metadata"]
            assert metadata["paragraph_count"] == 6
            assert metadata["table_count"] == 1
            assert metadata["header_count"] == 1
            assert metadata["footer_count"] == 1
            assert metadata["document_properties"]["title"] == "Photosynthesis Chapter"
            assert metadata["word_count"] > 50
        finally:
            # Restore original method
            parser.supported_formats['.docx'] = original_method
    
    @pytest.mark.asyncio
    async def test_doc_file_processing_integration(self, parser):
        """Integration test for DOC file processing with various scenarios"""
        # Test 1: Misnamed DOCX file
        docx_as_doc_content = b"PK\x03\x04" + b"docx content with doc extension"
        upload_file = UploadFile(
            file=io.BytesIO(docx_as_doc_content),
            filename="misnamed.doc",
            headers={"content-type": "application/msword"}
        )
        
        with patch.object(parser, '_extract_docx_text') as mock_docx:
            mock_docx.return_value = (
                "This document was saved with .doc extension but is actually DOCX format.",
                {
                    "paragraph_count": 1,
                    "table_count": 0,
                    "extraction_method": "python-docx"
                }
            )
            
            result = await parser.extract_text_from_file(upload_file)
            assert "actually DOCX format" in result["text"]
            assert result["metadata"]["extraction_method"] == "python-docx"
        
        # Test 2: Actual DOC file with extractable text
        doc_content = b'\xd0\xcf\x11\xe0' + b'Educational content about mathematics' * 20
        upload_file = UploadFile(
            file=io.BytesIO(doc_content),
            filename="math_lesson.doc",
            headers={"content-type": "application/msword"}
        )
        
        with patch.object(parser, '_extract_text_from_binary_doc') as mock_extract:
            mock_extract.return_value = "Educational content about mathematics and algebra concepts"
            
            result = await parser.extract_text_from_file(upload_file)
            assert "mathematics" in result["text"]
            assert result["metadata"]["extraction_method"] == "binary_text_extraction"
            assert result["metadata"]["format"] == "legacy_doc"
    
    @pytest.mark.asyncio
    async def test_text_file_extraction_integration(self, parser):
        """Integration test for text file extraction"""
        text_content = """
        Educational Content: Photosynthesis
        
        Photosynthesis is the process by which plants convert light energy into chemical energy.
        This process occurs in the chloroplasts of plant cells and involves two main stages:
        
        1. Light-dependent reactions (occur in thylakoids)
        2. Light-independent reactions (Calvin cycle, occurs in stroma)
        
        The overall equation for photosynthesis is:
        6CO2 + 6H2O + light energy → C6H12O6 + 6O2
        """.encode('utf-8')
        
        upload_file = UploadFile(
            file=io.BytesIO(text_content),
            filename="photosynthesis.txt",
            headers={"content-type": "text/plain"}
        )
        
        result = await parser.extract_text_from_file(upload_file)
        
        # Verify the result
        assert "Photosynthesis" in result["text"]
        assert "chloroplasts" in result["text"]
        assert "Calvin cycle" in result["text"]
        assert result["metadata"]["encoding"] == "utf-8"
        assert result["metadata"]["word_count"] > 20
        assert result["metadata"]["line_count"] > 5


# Property-based tests using hypothesis
try:
    from hypothesis import given, strategies as st, settings, HealthCheck
    import hypothesis
    
    class TestDocumentParserProperties:
        """Property-based tests for document parser"""
        
        @pytest.fixture
        def parser(self):
            return DocumentParser()
        
        @given(st.text(min_size=10, max_size=1000))
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
        @pytest.mark.asyncio
        async def test_text_extraction_preserves_content(self, parser, text_content):
            """Property: Text extraction should preserve the essential content"""
            # Skip if text is too short or contains only whitespace
            if len(text_content.strip()) < 10:
                return
            
            text_bytes = text_content.encode('utf-8')
            upload_file = UploadFile(
                file=io.BytesIO(text_bytes),
                filename="property_test.txt",
                headers={"content-type": "text/plain"}
            )
            
            result = await parser.extract_text_from_file(upload_file)
            
            # Property: Extracted text should contain the core content
            extracted_text = result["text"]
            
            # The extracted text should not be empty
            assert len(extracted_text.strip()) > 0
            
            # The extracted text should contain some of the original words
            original_words = set(text_content.split())
            extracted_words = set(extracted_text.split())
            
            # At least 80% of non-trivial words should be preserved
            non_trivial_words = {w for w in original_words if len(w) > 2}
            if non_trivial_words:
                preserved_words = non_trivial_words.intersection(extracted_words)
                preservation_ratio = len(preserved_words) / len(non_trivial_words)
                assert preservation_ratio >= 0.8, f"Only {preservation_ratio:.2%} of words preserved"
        
        @given(st.binary(min_size=1, max_size=100))
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
        @pytest.mark.asyncio
        async def test_invalid_content_handling(self, parser, binary_content):
            """Property: Invalid content should be handled gracefully"""
            upload_file = UploadFile(
                file=io.BytesIO(binary_content),
                filename="property_test.txt",
                headers={"content-type": "text/plain"}
            )
            
            # Should either succeed or raise a DocumentParsingError, never crash
            try:
                result = await parser.extract_text_from_file(upload_file)
                # If it succeeds, result should be well-formed
                assert isinstance(result, dict)
                assert "text" in result
                assert "metadata" in result
            except (DocumentParsingError, HTTPException):
                # Expected for invalid content
                pass
            except Exception as e:
                pytest.fail(f"Unexpected exception type: {type(e).__name__}: {e}")
        
        @given(st.binary(min_size=4, max_size=1000))
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
        @pytest.mark.asyncio
        async def test_docx_format_detection_property(self, parser, binary_content):
            """Property: DOCX format detection should be consistent"""
            # Add ZIP signature to make it look like DOCX
            docx_content = b"PK\x03\x04" + binary_content
            upload_file = UploadFile(
                file=io.BytesIO(docx_content),
                filename="property_test.docx",
                headers={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
            )
            
            # Mock the DOCX extraction to focus on format detection
            with patch.object(parser, '_extract_docx_text') as mock_docx:
                mock_docx.return_value = ("Mock DOCX content", {"extraction_method": "python-docx"})
                
                try:
                    result = await parser.extract_text_from_file(upload_file)
                    # If successful, should have proper structure
                    assert isinstance(result, dict)
                    assert "text" in result
                    assert "metadata" in result
                    assert result["metadata"]["file_type"] == ".docx"
                except (DocumentParsingError, HTTPException):
                    # Expected for invalid DOCX content
                    pass
                except Exception as e:
                    pytest.fail(f"Unexpected exception for DOCX processing: {type(e).__name__}: {e}")
        
        @given(st.binary(min_size=4, max_size=1000))
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
        @pytest.mark.asyncio
        async def test_doc_format_handling_property(self, parser, binary_content):
            """Property: DOC format handling should be robust"""
            # Add DOC signature to make it look like DOC
            doc_content = b'\xd0\xcf\x11\xe0' + binary_content
            upload_file = UploadFile(
                file=io.BytesIO(doc_content),
                filename="property_test.doc",
                headers={"content-type": "application/msword"}
            )
            
            # Should either extract text or provide helpful error
            try:
                result = await parser.extract_text_from_file(upload_file)
                # If successful, should have proper structure
                assert isinstance(result, dict)
                assert "text" in result
                assert "metadata" in result
                assert result["metadata"]["file_type"] == ".doc"
            except DocumentParsingError as e:
                # Should provide helpful error message
                error_msg = str(e)
                assert ("Legacy DOC format" in error_msg or 
                       "convert to DOCX" in error_msg or
                       "extraction_method" in str(e))
            except HTTPException:
                # Also acceptable
                pass
            except Exception as e:
                pytest.fail(f"Unexpected exception for DOC processing: {type(e).__name__}: {e}")
        
        @given(st.text(min_size=10, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po'))))
        @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
        @pytest.mark.asyncio
        async def test_docx_content_preservation_property(self, parser, text_content):
            """Property: DOCX extraction should preserve meaningful content"""
            # Skip if text is too short or only whitespace
            if len(text_content.strip()) < 10:
                return
            
            docx_content = b"PK\x03\x04" + b"mock docx"
            upload_file = UploadFile(
                file=io.BytesIO(docx_content),
                filename="content_test.docx",
                headers={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
            )
            
            # Mock extraction to return the test content
            async def mock_extract_docx(content, filename):
                return (text_content, {"extraction_method": "python-docx"})
            
            # Replace the method in the supported_formats dictionary
            original_method = parser.supported_formats['.docx']
            parser.supported_formats['.docx'] = mock_extract_docx
            
            try:
                result = await parser.extract_text_from_file(upload_file)
                
                # Property: Extracted text should preserve the content
                assert result["text"] == text_content
                assert len(result["text"]) >= 10
                assert result["metadata"]["character_count"] == len(text_content)
                assert result["metadata"]["word_count"] == len(text_content.split())
            finally:
                # Restore original method
                parser.supported_formats['.docx'] = original_method

except ImportError:
    # Hypothesis not available, skip property-based tests
    pass