"""
Tests for URL processing functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import requests
from bs4 import BeautifulSoup

from app.main import app
from app.services.content_service import ContentService

client = TestClient(app)

class TestURLProcessingEndpoint:
    """Test the URL processing endpoint"""
    
    def test_url_endpoint_valid_request(self):
        """Test URL endpoint with valid request"""
        with patch('app.services.content_service.ContentService.generate_from_url') as mock_generate:
            mock_generate.return_value = {
                "generation_id": "test-123",
                "status": "completed",
                "educational_script": {
                    "title": "Test Content",
                    "learning_objectives": [],
                    "sections": [],
                    "assessments": [],
                    "metadata": {}
                }
            }
            
            response = client.post("/api/v1/content/url", data={
                "url": "https://example.com/article",
                "topic": "Test Topic",
                "difficulty_level": "intermediate",
                "target_audience": "students",
                "learning_goals": "understand concepts, apply knowledge"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["generation_id"] == "test-123"
            assert data["status"] == "completed"
            
            # Verify the service was called with correct parameters
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[1]["url"] == "https://example.com/article"
            assert call_args[1]["topic"] == "Test Topic"
            assert call_args[1]["learning_goals"] == ["understand concepts", "apply knowledge"]
    
    def test_url_endpoint_invalid_url_format(self):
        """Test URL endpoint with invalid URL format"""
        response = client.post("/api/v1/content/url", data={
            "url": "not-a-valid-url",
            "difficulty_level": "intermediate",
            "target_audience": "students"
        })
        
        assert response.status_code == 400
        assert "Invalid URL format" in response.json()["error"]["message"]
    
    def test_url_endpoint_empty_url(self):
        """Test URL endpoint with empty URL"""
        response = client.post("/api/v1/content/url", data={
            "url": "",
            "difficulty_level": "intermediate",
            "target_audience": "students"
        })
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_url_endpoint_invalid_difficulty_level(self):
        """Test URL endpoint with invalid difficulty level"""
        response = client.post("/api/v1/content/url", data={
            "url": "https://example.com",
            "difficulty_level": "invalid",
            "target_audience": "students"
        })
        
        assert response.status_code == 422
        assert "Invalid difficulty level" in response.json()["error"]["message"]
    
    def test_url_endpoint_empty_target_audience(self):
        """Test URL endpoint with empty target audience"""
        # Test with empty string - FastAPI treats this as missing field
        response = client.post("/api/v1/content/url", data={
            "url": "https://example.com",
            "difficulty_level": "intermediate",
            "target_audience": ""
        })
        
        assert response.status_code == 422
        # FastAPI validation error for missing required field
        assert "validation failed" in response.json()["error"]["message"].lower()
        
        # Test with whitespace-only string - this should trigger our custom validation
        with patch('app.services.content_service.ContentService.generate_from_url') as mock_generate:
            mock_generate.return_value = {
                "generation_id": "test-123",
                "status": "completed",
                "educational_script": {"title": "Test", "learning_objectives": [], "sections": [], "assessments": [], "metadata": {}}
            }
            
            response = client.post("/api/v1/content/url", data={
                "url": "https://example.com",
                "difficulty_level": "intermediate",
                "target_audience": "   "  # Whitespace only
            })
            
            assert response.status_code == 422
            assert "Target audience cannot be empty" in response.json()["error"]["message"]
    
    def test_url_endpoint_too_many_learning_goals(self):
        """Test URL endpoint with too many learning goals"""
        learning_goals = ",".join([f"goal{i}" for i in range(15)])  # 15 goals, max is 10
        
        response = client.post("/api/v1/content/url", data={
            "url": "https://example.com",
            "difficulty_level": "intermediate",
            "target_audience": "students",
            "learning_goals": learning_goals
        })
        
        assert response.status_code == 422
        assert "Too many learning goals" in response.json()["error"]["message"]
    
    def test_url_endpoint_long_url(self):
        """Test URL endpoint with very long URL"""
        long_url = "https://example.com/" + "a" * 2050  # Exceeds 2048 char limit
        
        response = client.post("/api/v1/content/url", data={
            "url": long_url,
            "difficulty_level": "intermediate",
            "target_audience": "students"
        })
        
        assert response.status_code == 400
        assert "URL too long" in response.json()["error"]["message"]


class TestEnhancedWebScraping:
    """Test the enhanced web scraping functionality"""
    
    @pytest.fixture
    def content_service(self):
        """Create a content service instance"""
        return ContentService()
    
    @pytest.fixture
    def mock_complex_html_response(self):
        """Mock complex HTML response for testing enhanced extraction"""
        return """
        <html>
        <head>
            <title>Advanced Machine Learning Concepts</title>
            <meta name="description" content="Comprehensive guide to machine learning">
            <meta name="keywords" content="machine learning, AI, neural networks">
            <meta name="author" content="Dr. Jane Smith">
        </head>
        <body>
            <nav class="navigation">
                <ul>
                    <li><a href="/">Home</a></li>
                    <li><a href="/about">About</a></li>
                </ul>
            </nav>
            <header class="site-header">
                <h1>AI Research Blog</h1>
            </header>
            <main>
                <article class="post-content">
                    <h1>Advanced Machine Learning Concepts</h1>
                    <p class="meta">Published on January 15, 2024 by Dr. Jane Smith</p>
                    
                    <h2>Introduction to Neural Networks</h2>
                    <p>Neural networks are computational models inspired by biological neural networks. 
                    They consist of interconnected nodes (neurons) that process information through weighted connections.</p>
                    
                    <h2>Deep Learning Fundamentals</h2>
                    <p>Deep learning is a subset of machine learning that uses neural networks with multiple layers. 
                    These deep architectures can learn complex patterns and representations from data.</p>
                    
                    <h3>Key Components</h3>
                    <ul>
                        <li>Input layer: Receives the raw data</li>
                        <li>Hidden layers: Process and transform the data</li>
                        <li>Output layer: Produces the final predictions</li>
                    </ul>
                    
                    <blockquote>
                        "The power of deep learning lies in its ability to automatically learn hierarchical representations of data."
                    </blockquote>
                    
                    <h2>Applications in Modern AI</h2>
                    <p>Deep learning has revolutionized many fields including computer vision, natural language processing, 
                    and speech recognition. Major breakthroughs include image classification, machine translation, and 
                    autonomous driving systems.</p>
                </article>
                
                <aside class="sidebar">
                    <h3>Related Articles</h3>
                    <ul>
                        <li><a href="/article1">Introduction to AI</a></li>
                        <li><a href="/article2">Computer Vision Basics</a></li>
                    </ul>
                    <div class="advertisement">
                        <p>Advertisement: Learn AI with our courses!</p>
                    </div>
                </aside>
            </main>
            
            <footer class="site-footer">
                <p>© 2024 AI Research Blog. All rights reserved.</p>
                <div class="social-links">
                    <a href="/twitter">Follow us on Twitter</a>
                    <a href="/newsletter">Subscribe to our newsletter</a>
                </div>
            </footer>
            
            <div class="cookie-banner">
                <p>This site uses cookies. <a href="/privacy">Privacy Policy</a></p>
                <button>Accept all cookies</button>
            </div>
            
            <script>
                console.log('Page loaded');
                // Analytics code
            </script>
        </body>
        </html>
        """
    
    @pytest.mark.asyncio
    async def test_enhanced_scraping_with_structured_content(self, content_service, mock_complex_html_response):
        """Test enhanced scraping with structured content"""
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            mock_response = Mock()
            mock_response.content = mock_complex_html_response.encode('utf-8')
            mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
            mock_response.encoding = 'utf-8'
            mock_request.return_value = mock_response
            
            content = await content_service._scrape_url_content("https://example.com/ml-article")
            
            # Verify main content is extracted
            assert "Advanced Machine Learning Concepts" in content
            assert "Introduction to Neural Networks" in content
            assert "Deep Learning Fundamentals" in content
            assert "Input layer: Receives the raw data" in content
            assert "hierarchical representations" in content
            assert "Applications in Modern AI" in content
            
            # Verify unwanted content is removed
            assert "Navigation" not in content
            assert "Follow us on Twitter" not in content
            assert "Subscribe to our newsletter" not in content
            assert "Advertisement" not in content
            assert "Accept all cookies" not in content
            assert "console.log" not in content
            
            # Verify content length is reasonable
            assert len(content) > 200
            assert len(content) < 1000  # Should be cleaned and concise
    
    @pytest.mark.asyncio
    async def test_enhanced_scraping_with_retry_logic(self, content_service):
        """Test enhanced scraping with retry logic"""
        with patch('requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # First call fails with timeout, second succeeds
            mock_response = Mock()
            mock_response.content = b"<html><body><p>Test content for retry logic testing with sufficient length to pass validation checks and demonstrate the retry mechanism working properly.</p></body></html>"
            mock_response.headers = {'content-type': 'text/html'}
            mock_response.encoding = 'utf-8'
            
            mock_session.get.side_effect = [
                requests.exceptions.Timeout(),
                mock_response
            ]
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                content = await content_service._scrape_url_content("https://example.com/retry-test")
            
            assert "Test content for retry logic testing" in content
            assert mock_session.get.call_count == 2  # One retry
    
    @pytest.mark.asyncio
    async def test_enhanced_scraping_large_response_handling(self, content_service):
        """Test handling of large responses"""
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            # Create a response that's too large (>10MB)
            large_content = "x" * (11 * 1024 * 1024)  # 11MB
            mock_response = Mock()
            mock_response.content = large_content.encode('utf-8')
            mock_request.side_effect = HTTPException(status_code=413, detail="Response too large")
            
            with pytest.raises(HTTPException) as exc_info:
                await content_service._scrape_url_content("https://example.com/large-page")
            
            assert exc_info.value.status_code == 413
            assert "too large" in exc_info.value.detail.lower()
    
    def test_extract_page_metadata(self, content_service):
        """Test page metadata extraction"""
        html = """
        <html lang="en">
        <head>
            <title>Test Article Title</title>
            <meta name="description" content="This is a test article description">
            <meta name="keywords" content="test, article, metadata">
            <meta name="author" content="Test Author">
        </head>
        <body><p>Content</p></body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        metadata = content_service._extract_page_metadata(soup)
        
        assert metadata['title'] == "Test Article Title"
        assert metadata['description'] == "This is a test article description"
        assert metadata['keywords'] == "test, article, metadata"
        assert metadata['author'] == "Test Author"
        assert metadata['language'] == "en"
    
    def test_enhanced_text_extraction_strategies(self, content_service):
        """Test different text extraction strategies"""
        # Test article-style content
        article_html = """
        <html>
        <body>
            <article class="post-content">
                <h1>Article Title</h1>
                <p>This is article content that should be extracted using article selectors.</p>
            </article>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(article_html, 'html.parser')
        text = content_service._extract_meaningful_text_enhanced(soup, "https://example.com/article")
        
        assert "Article Title" in text
        assert "article content that should be extracted" in text
        
        # Test documentation-style content
        docs_html = """
        <html>
        <body>
            <div class="docs-content">
                <h2>Documentation Section</h2>
                <p>This is documentation content with technical details and examples.</p>
            </div>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(docs_html, 'html.parser')
        text = content_service._extract_meaningful_text_enhanced(soup, "https://example.com/docs")
        
        assert "Documentation Section" in text
        assert "technical details and examples" in text
    
    def test_enhanced_text_cleaning(self, content_service):
        """Test enhanced text cleaning functionality"""
        dirty_text = """
        Skip to main content    Cookie policy   Accept all cookies
        
        This is the actual educational content that we want to keep and preserve.
        
        Share this article    Follow us on Twitter    Subscribe to our newsletter
        
        This is another important paragraph with valuable information for learning.
        
        Advertisement    Sponsored content    Related articles you might like
        
        Final paragraph with educational value and substance.
        """
        
        cleaned = content_service._clean_scraped_text_enhanced(dirty_text)
        
        # Should keep educational content
        assert "actual educational content" in cleaned
        assert "important paragraph with valuable information" in cleaned
        assert "Final paragraph with educational value" in cleaned
        
        # Should remove UI/navigation elements
        assert "Skip to main content" not in cleaned
        assert "Cookie policy" not in cleaned
        assert "Share this article" not in cleaned
        assert "Follow us on Twitter" not in cleaned
        assert "Subscribe to our newsletter" not in cleaned
        assert "Advertisement" not in cleaned
        assert "Sponsored content" not in cleaned
        assert "Related articles" not in cleaned
    
    def test_enhanced_title_extraction(self, content_service):
        """Test enhanced title extraction from URLs"""
        # Test with meaningful path
        title1 = content_service._extract_title_from_url("https://blog.example.com/machine-learning-fundamentals")
        assert "Machine Learning Fundamentals" in title1
        assert "blog.example.com" in title1
        
        # Test with nested path and file extension
        title2 = content_service._extract_title_from_url("https://docs.example.com/guides/neural-networks.html")
        assert "Neural Networks" in title2
        assert "docs.example.com" in title2
        
        # Test with subdomain
        title3 = content_service._extract_title_from_url("https://research.university.edu/")
        assert "Research" in title3
        assert "university.edu" in title3
        
        # Test with domain only
        title4 = content_service._extract_title_from_url("https://example.com/")
        assert "example.com" in title4
    
    def test_meaningful_text_validation(self, content_service):
        """Test meaningful text validation"""
        # Should accept meaningful content
        assert content_service._is_meaningful_text("This is a substantial piece of educational content about machine learning.")
        assert content_service._is_meaningful_text("Neural networks are computational models inspired by biological systems.")
        
        # Should reject UI/navigation text
        assert not content_service._is_meaningful_text("Skip to main content")
        assert not content_service._is_meaningful_text("privacy")  # Single word that matches pattern
        assert not content_service._is_meaningful_text("Follow us on Twitter")
        assert not content_service._is_meaningful_text("Subscribe to newsletter")
        
        # Should reject very short or low-quality text
        assert not content_service._is_meaningful_text("123")
        assert not content_service._is_meaningful_text("...")
        assert not content_service._is_meaningful_text("x")  # Single character
        assert not content_service._is_meaningful_text("aaaaaaaaaaaaaaaa")  # Low diversity
        
        # Should accept short but meaningful text (like headings)
        assert content_service._is_meaningful_text("Introduction")
        assert content_service._is_meaningful_text("Chapter 1")
    
    def test_meaningful_sentence_validation(self, content_service):
        """Test meaningful sentence validation"""
        # Should accept educational sentences
        assert content_service._is_meaningful_sentence("Machine learning algorithms can identify patterns in large datasets.")
        assert content_service._is_meaningful_sentence("The process of photosynthesis converts sunlight into chemical energy.")
        
        # Should reject UI/call-to-action sentences
        assert not content_service._is_meaningful_sentence("Click here to learn more about our services.")
        assert not content_service._is_meaningful_sentence("Sign up for our newsletter to get updates.")
        assert not content_service._is_meaningful_sentence("Follow us on social media for more content.")
        
        # Should reject very short sentences
        assert not content_service._is_meaningful_sentence("Yes.")
        assert not content_service._is_meaningful_sentence("OK")


class TestContentServiceURLScraping:
    """Test the content service URL scraping functionality"""
    
    @pytest.fixture
    def content_service(self):
        """Create a content service instance"""
        return ContentService()
    
    @pytest.fixture
    def mock_html_response(self):
        """Mock HTML response for testing"""
        return """
        <html>
        <head><title>Test Article</title></head>
        <body>
            <nav>Navigation menu</nav>
            <header>Site header</header>
            <main>
                <article>
                    <h1>Educational Article Title</h1>
                    <p>This is the first paragraph with educational content about machine learning concepts.</p>
                    <p>This is the second paragraph explaining neural networks and their applications in modern AI systems.</p>
                    <h2>Key Concepts</h2>
                    <p>Deep learning involves multiple layers of neural networks that can learn complex patterns from data.</p>
                    <ul>
                        <li>Supervised learning uses labeled data</li>
                        <li>Unsupervised learning finds patterns in unlabeled data</li>
                        <li>Reinforcement learning learns through trial and error</li>
                    </ul>
                </article>
            </main>
            <footer>Site footer</footer>
            <script>console.log('test');</script>
        </body>
        </html>
        """
    
    @pytest.mark.asyncio
    async def test_scrape_url_content_success(self, content_service, mock_html_response):
        """Test successful URL content scraping"""
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            mock_response = Mock()
            mock_response.content = mock_html_response.encode('utf-8')
            mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
            mock_response.encoding = 'utf-8'
            mock_request.return_value = mock_response
            
            content = await content_service._scrape_url_content("https://example.com/article")
            
            assert len(content) > 100
            assert "Educational Article Title" in content
            assert "machine learning concepts" in content
            assert "neural networks" in content
            assert "Supervised learning" in content
            # Navigation and script content should be removed
            assert "Navigation menu" not in content
            assert "console.log" not in content
    
    @pytest.mark.asyncio
    async def test_scrape_url_content_timeout(self, content_service):
        """Test URL scraping with timeout"""
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            mock_request.side_effect = requests.exceptions.Timeout()
            
            with pytest.raises(HTTPException) as exc_info:
                await content_service._scrape_url_content("https://example.com")
            
            assert exc_info.value.status_code == 408
            assert "timeout" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_scrape_url_content_connection_error(self, content_service):
        """Test URL scraping with connection error"""
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            mock_request.side_effect = requests.exceptions.ConnectionError()
            
            with pytest.raises(HTTPException) as exc_info:
                await content_service._scrape_url_content("https://example.com")
            
            assert exc_info.value.status_code == 503
            assert "connection error" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_scrape_url_content_404_error(self, content_service):
        """Test URL scraping with 404 error"""
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.reason = "Not Found"
            http_error = requests.exceptions.HTTPError(response=mock_response)
            mock_request.side_effect = http_error
            
            with pytest.raises(HTTPException) as exc_info:
                await content_service._scrape_url_content("https://example.com/notfound")
            
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_scrape_url_content_forbidden(self, content_service):
        """Test URL scraping with 403 forbidden error"""
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_response.reason = "Forbidden"
            http_error = requests.exceptions.HTTPError(response=mock_response)
            mock_request.side_effect = http_error
            
            with pytest.raises(HTTPException) as exc_info:
                await content_service._scrape_url_content("https://example.com/forbidden")
            
            assert exc_info.value.status_code == 403
            assert "forbidden" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_scrape_url_content_unsupported_content_type(self, content_service):
        """Test URL scraping with unsupported content type"""
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            mock_response = Mock()
            mock_response.content = b"PDF content"
            mock_response.headers = {'content-type': 'application/pdf'}
            mock_response.encoding = None
            mock_request.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc_info:
                await content_service._scrape_url_content("https://example.com/document.pdf")
            
            assert exc_info.value.status_code == 415
            assert "unsupported content type" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_scrape_url_content_insufficient_content(self, content_service):
        """Test URL scraping with insufficient content"""
        minimal_html = "<html><body><p>Short</p></body></html>"
        
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            mock_response = Mock()
            mock_response.content = minimal_html.encode('utf-8')
            mock_response.headers = {'content-type': 'text/html'}
            mock_response.encoding = 'utf-8'
            mock_request.return_value = mock_response
            
            with pytest.raises(HTTPException) as exc_info:
                await content_service._scrape_url_content("https://example.com/minimal")
            
            assert exc_info.value.status_code == 400
            assert "insufficient content" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_generate_from_url_integration(self, content_service, mock_html_response):
        """Test full URL processing integration"""
        with patch('app.services.content_service.ContentService._make_request_with_retry') as mock_request:
            mock_response = Mock()
            mock_response.content = mock_html_response.encode('utf-8')
            mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
            mock_response.encoding = 'utf-8'
            mock_request.return_value = mock_response
            
            result = await content_service.generate_from_url(
                url="https://example.com/ml-article",
                topic="Machine Learning",
                difficulty_level="intermediate",
                target_audience="students",
                learning_goals=["understand ML", "apply concepts"]
            )
            
            assert result["status"] == "completed"
            assert result["generation_id"]
            assert "educational_script" in result
            
            # Check that URL metadata is included
            script = result["educational_script"]
            assert script["metadata"]["source_url"] == "https://example.com/ml-article"
            assert script["metadata"]["content_length"] > 0


class TestURLValidation:
    """Test URL validation functionality"""
    
    def test_valid_urls(self):
        """Test various valid URL formats"""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://www.example.com/path",
            "https://subdomain.example.com/path/to/article",
            "https://example.com/path?query=value",
            "https://example.com/path#section"
        ]
        
        for url in valid_urls:
            response = client.post("/api/v1/content/url", data={
                "url": url,
                "difficulty_level": "intermediate",
                "target_audience": "students"
            })
            # Should not fail on URL validation (may fail on actual scraping)
            assert response.status_code != 400 or "Invalid URL format" not in response.json().get("error", {}).get("message", "")
    
    def test_invalid_urls(self):
        """Test various invalid URL formats"""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "example.com",
            "//example.com",
            "https://",
            "https:///path"
        ]
        
        for url in invalid_urls:
            response = client.post("/api/v1/content/url", data={
                "url": url,
                "difficulty_level": "intermediate",
                "target_audience": "students"
            })
            assert response.status_code == 400
            assert "Invalid URL format" in response.json()["error"]["message"]