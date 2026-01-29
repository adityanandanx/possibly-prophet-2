#!/usr/bin/env python3
"""
Demo script to showcase enhanced web scraping functionality
"""

import asyncio
from app.services.content_service import ContentService

async def demo_enhanced_scraping():
    """Demonstrate the enhanced web scraping capabilities"""
    
    print("🚀 Enhanced Web Scraping Demo")
    print("=" * 50)
    
    # Initialize content service
    service = ContentService()
    
    # Test with a mock HTML response (simulating a real website)
    mock_html = """
    <html>
    <head>
        <title>Machine Learning Fundamentals</title>
        <meta name="description" content="A comprehensive guide to machine learning">
        <meta name="author" content="Dr. AI Expert">
    </head>
    <body>
        <nav class="navigation">
            <a href="/">Home</a>
            <a href="/about">About</a>
        </nav>
        
        <header>
            <h1>AI Learning Hub</h1>
        </header>
        
        <main>
            <article class="post-content">
                <h1>Machine Learning Fundamentals</h1>
                <p class="meta">Published on January 2024</p>
                
                <h2>Introduction to Machine Learning</h2>
                <p>Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed for every task.</p>
                
                <h2>Types of Machine Learning</h2>
                <ul>
                    <li>Supervised Learning: Uses labeled data to train models</li>
                    <li>Unsupervised Learning: Finds patterns in unlabeled data</li>
                    <li>Reinforcement Learning: Learns through trial and error</li>
                </ul>
                
                <h2>Key Algorithms</h2>
                <p>Popular machine learning algorithms include linear regression, decision trees, neural networks, and support vector machines. Each has its strengths and is suited for different types of problems.</p>
                
                <blockquote>
                    "The goal is to turn data into information, and information into insight." - Carly Fiorina
                </blockquote>
            </article>
            
            <aside class="sidebar">
                <h3>Related Articles</h3>
                <p>You might also like our articles on deep learning and data science.</p>
                <div class="advertisement">
                    <p>Advertisement: Learn AI with our premium courses!</p>
                </div>
            </aside>
        </main>
        
        <footer>
            <p>© 2024 AI Learning Hub</p>
            <div class="social">
                <a href="/twitter">Follow us on Twitter</a>
                <a href="/newsletter">Subscribe to our newsletter</a>
            </div>
        </footer>
        
        <div class="cookie-banner">
            <p>This site uses cookies. <a href="/privacy">Privacy Policy</a></p>
            <button>Accept all cookies</button>
        </div>
        
        <script>
            console.log('Page analytics loaded');
        </script>
    </body>
    </html>
    """
    
    # Simulate the enhanced scraping process
    from bs4 import BeautifulSoup
    from unittest.mock import Mock
    
    # Parse the HTML
    soup = BeautifulSoup(mock_html, 'html.parser')
    
    print("📄 Original HTML Content:")
    print(f"   - Total HTML length: {len(mock_html)} characters")
    print(f"   - Contains navigation, ads, scripts, and footer content")
    print()
    
    # Extract metadata
    metadata = service._extract_page_metadata(soup)
    print("📊 Extracted Metadata:")
    for key, value in metadata.items():
        print(f"   - {key}: {value}")
    print()
    
    # Extract meaningful text using enhanced extraction
    extracted_text = service._extract_meaningful_text_enhanced(soup, "https://example.com/ml-guide")
    
    print("🧹 Enhanced Text Extraction:")
    print(f"   - Extracted length: {len(extracted_text)} characters")
    print(f"   - Content preview:")
    print("   " + "-" * 40)
    print("   " + extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text)
    print("   " + "-" * 40)
    print()
    
    # Clean the extracted text
    cleaned_text = service._clean_scraped_text_enhanced(extracted_text)
    
    print("✨ Enhanced Text Cleaning:")
    print(f"   - Cleaned length: {len(cleaned_text)} characters")
    print(f"   - Removed UI elements, ads, and navigation")
    print(f"   - Final content:")
    print("   " + "=" * 40)
    print("   " + cleaned_text)
    print("   " + "=" * 40)
    print()
    
    # Demonstrate content quality validation
    print("🔍 Content Quality Validation:")
    try:
        service._validate_content_quality(cleaned_text, "https://example.com/ml-guide")
        print("   ✅ Content passed quality validation")
        print(f"   - Length: {len(cleaned_text)} characters (minimum: 100)")
        print("   - Contains substantial educational content")
    except Exception as e:
        print(f"   ❌ Content failed validation: {str(e)}")
    print()
    
    # Test title extraction
    title = service._extract_title_from_url("https://ai-learning-hub.com/guides/machine-learning-fundamentals")
    print("🏷️  Title Extraction:")
    print(f"   - Extracted title: {title}")
    print()
    
    print("🎉 Enhanced Web Scraping Demo Complete!")
    print("Key improvements demonstrated:")
    print("   ✅ Multiple content extraction strategies")
    print("   ✅ Enhanced text cleaning and normalization")
    print("   ✅ Metadata extraction")
    print("   ✅ Content quality validation")
    print("   ✅ Robust error handling")
    print("   ✅ Better title extraction")

if __name__ == "__main__":
    asyncio.run(demo_enhanced_scraping())