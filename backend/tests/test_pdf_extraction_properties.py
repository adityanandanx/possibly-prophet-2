"""
Property-based tests for PDF text extraction functionality
**Validates: Requirements 1.1**
"""

import pytest
import io
from unittest.mock import Mock, patch
from fastapi import UploadFile

try:
    from hypothesis import given, strategies as st, assume, settings, HealthCheck
    import hypothesis
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False

from app.services.document_parser import DocumentParser, DocumentParsingError


@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
class TestPDFExtractionProperties:
    """Property-based tests for PDF text extraction"""
    
    @pytest.fixture
    def parser(self):
        """Create a DocumentParser instance for testing"""
        return DocumentParser()
    
    @given(st.text(min_size=20, max_size=2000, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po'))))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_pdf_content_preservation_property(self, parser, sample_text):
        """
        **Validates: Requirements 1.1**
        Property: PDF text extraction must preserve the core educational content
        
        For any valid text content that could be in a PDF, the extraction process
        should preserve the essential information without corruption.
        """
        # Skip if text is too short or only whitespace
        assume(len(sample_text.strip()) >= 20)
        assume(any(c.isalnum() for c in sample_text))  # Must contain alphanumeric characters
        
        # Create a mock PDF file
        upload_file = UploadFile(
            file=io.BytesIO(b"%PDF-mock-content"),
            filename="test_property.pdf",
            headers={"content-type": "application/pdf"}
        )
        
        # Mock the PDF extraction to return our sample text
        with patch.object(parser, '_extract_pdf_with_pdfplumber') as mock_pdfplumber:
            mock_pdfplumber.return_value = (sample_text, {
                "page_count": 1,
                "successful_pages": 1,
                "failed_pages": 0,
                "tables_found": 0,
                "extraction_method": "pdfplumber"
            })
            
            result = await parser.extract_text_from_file(upload_file)
            
            # Property 1: Result must be well-formed
            assert isinstance(result, dict)
            assert "text" in result
            assert "metadata" in result
            
            # Property 2: Extracted text must not be empty
            extracted_text = result["text"]
            assert len(extracted_text.strip()) > 0
            
            # Property 3: Core content preservation
            # The extracted text should contain the essential words from the original
            original_words = set(w.lower() for w in sample_text.split() if len(w) > 2)
            extracted_words = set(w.lower() for w in extracted_text.split() if len(w) > 2)
            
            if original_words:
                preserved_words = original_words.intersection(extracted_words)
                preservation_ratio = len(preserved_words) / len(original_words)
                
                # At least 90% of significant words should be preserved
                assert preservation_ratio >= 0.9, (
                    f"Content preservation failed: only {preservation_ratio:.2%} of words preserved. "
                    f"Original: {len(original_words)} words, Preserved: {len(preserved_words)} words"
                )
            
            # Property 4: Metadata completeness
            metadata = result["metadata"]
            assert metadata["filename"] == "test_property.pdf"
            assert metadata["file_type"] == ".pdf"
            assert metadata["character_count"] > 0
            assert metadata["word_count"] > 0
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_pdf_page_count_consistency_property(self, parser, page_count):
        """
        **Validates: Requirements 1.1**
        Property: PDF metadata should accurately reflect the document structure
        
        The page count and extraction statistics should be consistent and accurate.
        """
        upload_file = UploadFile(
            file=io.BytesIO(b"%PDF-mock-content"),
            filename=f"test_{page_count}_pages.pdf",
            headers={"content-type": "application/pdf"}
        )
        
        # Mock PDF with specified page count
        mock_metadata = {
            "page_count": page_count,
            "successful_pages": min(page_count, page_count - (page_count // 10)),  # 90% success rate
            "failed_pages": max(0, page_count // 10),
            "tables_found": 0,
            "extraction_method": "pdfplumber"
        }
        
        sample_text = f"Sample content from {page_count} page PDF document."
        
        with patch.object(parser, '_extract_pdf_with_pdfplumber') as mock_pdfplumber:
            mock_pdfplumber.return_value = (sample_text, mock_metadata)
            
            result = await parser.extract_text_from_file(upload_file)
            
            # Property 1: Page count consistency
            metadata = result["metadata"]
            assert metadata["page_count"] == page_count
            
            # Property 2: Success/failure counts should sum to total pages
            successful = metadata.get("successful_pages", 0)
            failed = metadata.get("failed_pages", 0)
            assert successful + failed == page_count
            
            # Property 3: At least some pages should be processed successfully for valid PDFs
            assert successful > 0, "No pages were successfully processed"
            
            # Property 4: Success rate should be reasonable (at least 50% for valid PDFs)
            success_rate = successful / page_count
            assert success_rate >= 0.5, f"Success rate too low: {success_rate:.2%}"
    
    @given(st.lists(st.text(min_size=10, max_size=500), min_size=1, max_size=10))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_pdf_multi_page_content_aggregation_property(self, parser, page_contents):
        """
        **Validates: Requirements 1.1**
        Property: Multi-page PDF content should be properly aggregated
        
        When extracting text from multi-page PDFs, all page content should be
        combined in a coherent manner without loss of information.
        """
        # Filter out empty or whitespace-only content
        valid_pages = [content.strip() for content in page_contents if content.strip()]
        assume(len(valid_pages) > 0)
        
        upload_file = UploadFile(
            file=io.BytesIO(b"%PDF-mock-multipage"),
            filename="multipage_test.pdf",
            headers={"content-type": "application/pdf"}
        )
        
        # Simulate multi-page extraction
        combined_text = "\n\n".join(valid_pages)
        mock_metadata = {
            "page_count": len(valid_pages),
            "successful_pages": len(valid_pages),
            "failed_pages": 0,
            "tables_found": 0,
            "extraction_method": "pdfplumber"
        }
        
        with patch.object(parser, '_extract_pdf_with_pdfplumber') as mock_pdfplumber:
            mock_pdfplumber.return_value = (combined_text, mock_metadata)
            
            result = await parser.extract_text_from_file(upload_file)
            
            extracted_text = result["text"]
            
            # Property 1: All page content should be present
            for page_content in valid_pages:
                # Check that significant words from each page are preserved
                page_words = set(w.lower() for w in page_content.split() if len(w) > 2)
                extracted_words = set(w.lower() for w in extracted_text.split())
                
                if page_words:
                    preserved = page_words.intersection(extracted_words)
                    preservation_ratio = len(preserved) / len(page_words)
                    assert preservation_ratio >= 0.8, (
                        f"Page content not properly preserved: {preservation_ratio:.2%} of words found"
                    )
            
            # Property 2: Content should be properly separated (no run-on text)
            # The combined text should have reasonable structure
            lines = extracted_text.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            assert len(non_empty_lines) >= len(valid_pages), "Content not properly structured"
            
            # Property 3: Total character count should be reasonable
            expected_min_chars = sum(len(page.strip()) for page in valid_pages)
            actual_chars = len(extracted_text.strip())
            assert actual_chars >= expected_min_chars * 0.9, "Significant content loss detected"
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(max_codepoint=127)))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_pdf_filename_handling_property(self, parser, filename_base):
        """
        **Validates: Requirements 1.1**
        Property: PDF processing should handle various filename formats correctly
        
        The system should correctly process PDFs regardless of filename variations
        while preserving the original filename in metadata.
        """
        # Clean filename to avoid filesystem issues
        clean_filename = "".join(c for c in filename_base if c.isalnum() or c in "._-")
        assume(len(clean_filename) > 0)
        
        pdf_filename = f"{clean_filename}.pdf"
        
        upload_file = UploadFile(
            file=io.BytesIO(b"%PDF-mock-content"),
            filename=pdf_filename,
            headers={"content-type": "application/pdf"}
        )
        
        sample_text = f"Content from file: {pdf_filename}"
        mock_metadata = {
            "page_count": 1,
            "successful_pages": 1,
            "failed_pages": 0,
            "tables_found": 0,
            "extraction_method": "pdfplumber"
        }
        
        with patch.object(parser, '_extract_pdf_with_pdfplumber') as mock_pdfplumber:
            mock_pdfplumber.return_value = (sample_text, mock_metadata)
            
            result = await parser.extract_text_from_file(upload_file)
            
            # Property 1: Original filename should be preserved in metadata
            assert result["metadata"]["filename"] == pdf_filename
            
            # Property 2: File type should be correctly identified
            assert result["metadata"]["file_type"] == ".pdf"
            
            # Property 3: Content should be extracted regardless of filename
            assert len(result["text"].strip()) > 0
            
            # Property 4: Metadata should be complete
            metadata = result["metadata"]
            required_fields = ["filename", "file_type", "character_count", "word_count"]
            for field in required_fields:
                assert field in metadata, f"Required metadata field '{field}' missing"
    
    @pytest.mark.asyncio
    async def test_pdf_error_handling_property(self, parser):
        """
        **Validates: Requirements 1.1**
        Property: PDF processing should handle errors gracefully
        
        When PDF processing fails, the system should provide clear error messages
        and fail gracefully without crashing.
        """
        # Test various error conditions
        error_conditions = [
            (b"not-a-pdf", "invalid.pdf", "Invalid PDF"),
            (b"", "empty.pdf", "Empty file"),
            (b"%PDF-encrypted", "encrypted.pdf", "Password-protected"),
        ]
        
        for content, filename, error_type in error_conditions:
            upload_file = UploadFile(
                file=io.BytesIO(content),
                filename=filename,
                headers={"content-type": "application/pdf"}
            )
            
            # Should raise DocumentParsingError, not crash
            with pytest.raises(DocumentParsingError) as exc_info:
                await parser.extract_text_from_file(upload_file)
            
            # Error message should be informative
            error_message = str(exc_info.value)
            assert len(error_message) > 10, "Error message too short"
            assert filename in error_message or error_type.lower() in error_message.lower(), (
                f"Error message should mention the issue: {error_message}"
            )


@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
class TestPDFExtractionEdgeCases:
    """Edge case tests for PDF extraction using property-based testing"""
    
    @pytest.fixture
    def parser(self):
        return DocumentParser()
    
    @given(st.integers(min_value=0, max_value=1000))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_pdf_size_handling_property(self, parser, content_size):
        """
        **Validates: Requirements 1.1**
        Property: PDF processing should handle various content sizes appropriately
        """
        # Generate content of specified size
        if content_size == 0:
            content = ""
        else:
            content = "A" * content_size
        
        upload_file = UploadFile(
            file=io.BytesIO(b"%PDF-mock"),
            filename="size_test.pdf",
            headers={"content-type": "application/pdf"}
        )
        
        mock_metadata = {
            "page_count": 1,
            "successful_pages": 1 if content_size > 0 else 0,
            "failed_pages": 0 if content_size > 0 else 1,
            "tables_found": 0,
            "extraction_method": "pdfplumber"
        }
        
        with patch.object(parser, '_extract_pdf_with_pdfplumber') as mock_pdfplumber:
            if content_size < 10:
                # Should raise error for insufficient content
                mock_pdfplumber.side_effect = DocumentParsingError("Insufficient content")
                
                with pytest.raises(DocumentParsingError):
                    await parser.extract_text_from_file(upload_file)
            else:
                # Should succeed for sufficient content
                mock_pdfplumber.return_value = (content, mock_metadata)
                
                result = await parser.extract_text_from_file(upload_file)
                
                # Content size should be preserved
                assert len(result["text"]) >= content_size * 0.9  # Allow for some cleaning
                assert result["metadata"]["character_count"] > 0