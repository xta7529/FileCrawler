#!/usr/bin/env python3
"""
File Crawler Script
Downloads files from a website that match specified keywords in their content.
Supports PDFs, DOCX files, and images (using OCR).
"""

import os
import sys
import re
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path
from typing import List, Set, Tuple
import logging

from bs4 import BeautifulSoup
import PyPDF2
import pdfplumber
from PIL import Image
from docx import Document
import pytesseract
import io


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileCrawler:
    """Main class for crawling websites and downloading files matching keywords."""
    
    def __init__(self, base_url: str, keywords: List[str], output_dir: str = "downloaded_files", max_depth: int = 2):
        """
        Initialize the file crawler.
        
        Args:
            base_url: The website URL to scrape
            keywords: List of keywords to search for
            output_dir: Directory to save downloaded files
            max_depth: Maximum crawling depth (default: 2)
        """
        self.base_url = base_url
        self.keywords = [kw.strip().lower() for kw in keywords]
        self.output_dir = output_dir
        self.max_depth = max_depth
        self.visited_urls: Set[str] = set()
        self.downloaded_files: List[str] = []
        self.base_domain = urlparse(base_url).netloc
        self.tesseract_checked = False
        self.tesseract_available = False
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Supported file extensions
        self.file_extensions = {'.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        
        # Prepare valid domains list for easier checking
        self.valid_domains = {self.base_domain}
        if self.base_domain.startswith('www.'):
            self.valid_domains.add(self.base_domain[4:])
        else:
            self.valid_domains.add(f"www.{self.base_domain}")
        
        logger.info(f"Initialized FileCrawler for {base_url}")
        if self.keywords:
            logger.info(f"Keywords: {', '.join(self.keywords)}")
        else:
            logger.info("No keywords specified — all files will be downloaded")
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and belongs to the same domain."""
        try:
            parsed = urlparse(url)
            # Check if it's a valid URL with scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            # Only follow links within the same domain
            return parsed.netloc in self.valid_domains
        except Exception:
            return False
    
    def is_file_url(self, url: str) -> bool:
        """Check if URL points to a downloadable file."""
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        return any(path.endswith(ext) for ext in self.file_extensions)
    
    def download_file(self, url: str) -> Tuple[bytes, str]:
        """
        Download file from URL.
        
        Args:
            url: File URL to download
            
        Returns:
            Tuple of (file content as bytes, file extension)
        """
        try:
            response = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            # Determine file extension
            parsed_url = urlparse(url)
            path = parsed_url.path
            ext = os.path.splitext(path)[1].lower()
            
            if not ext or ext not in self.file_extensions:
                # Try to get from content-type
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' in content_type:
                    ext = '.pdf'
                elif 'word' in content_type or 'document' in content_type:
                    ext = '.docx'
                elif 'image' in content_type:
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'png' in content_type:
                        ext = '.png'
                    else:
                        ext = '.jpg'  # Default for images
            
            return response.content, ext
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None, None
    
    def extract_text_from_pdf(self, content: bytes) -> str:
        """
        Extract text from PDF file.
        
        Args:
            content: PDF file content as bytes
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            # Try with pdfplumber first (better for complex PDFs)
            pdf_file = io.BytesIO(content)
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")
            try:
                # Fallback to PyPDF2
                pdf_file = io.BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            except Exception as e2:
                logger.error(f"Error extracting text from PDF: {e2}")
        
        return text
    
    def extract_text_from_docx(self, content: bytes) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            content: DOCX file content as bytes
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            doc_file = io.BytesIO(content)
            doc = Document(doc_file)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
        
        return text
    
    def extract_text_from_image(self, content: bytes) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            content: Image file content as bytes
            
        Returns:
            Extracted text
        """
        text = ""
        try:
            # Check tesseract availability on first use
            if not self.tesseract_checked:
                self.tesseract_checked = True
                try:
                    pytesseract.get_tesseract_version()
                    self.tesseract_available = True
                except Exception:
                    logger.warning("Tesseract OCR not found. Image text extraction will be skipped.")
                    logger.warning("Install tesseract: sudo apt-get install tesseract-ocr (Linux) or brew install tesseract (Mac)")
                    self.tesseract_available = False
            
            if not self.tesseract_available:
                return text
            
            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image)
        except Exception as e:
            logger.error(f"Error performing OCR on image: {e}")
        
        return text
    
    def extract_text(self, content: bytes, file_ext: str) -> str:
        """
        Extract text from file based on its type.
        
        Args:
            content: File content as bytes
            file_ext: File extension
            
        Returns:
            Extracted text
        """
        file_ext = file_ext.lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(content)
        elif file_ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(content)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']:
            return self.extract_text_from_image(content)
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return ""
    
    def contains_keywords(self, text: str) -> bool:
        """
        Check if text contains any of the keywords.
        Returns True unconditionally when no keywords are specified (download all files).
        
        Args:
            text: Text to search
            
        Returns:
            True if any keyword is found, or if no keywords were specified
        """
        if not self.keywords:
            return True
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.keywords)
    
    def save_file(self, content: bytes, url: str, file_ext: str) -> str:
        """
        Save file to output directory.
        
        Args:
            content: File content
            url: Original URL
            file_ext: File extension
            
        Returns:
            Path to saved file
        """
        # Create a safe filename
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # If filename is empty or doesn't have extension, create one
        if not filename or '.' not in filename:
            filename = f"file_{len(self.downloaded_files)}{file_ext}"
        
        # Ensure unique filename
        filepath = os.path.join(self.output_dir, filename)
        counter = 1
        while os.path.exists(filepath):
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(self.output_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        try:
            with open(filepath, 'wb') as f:
                f.write(content)
            logger.info(f"Saved file: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving file {filepath}: {e}")
            return None
    
    def process_file_url(self, url: str) -> bool:
        """
        Download and process a file URL.
        
        Args:
            url: File URL to process
            
        Returns:
            True if file was downloaded (contained keywords)
        """
        if url in self.visited_urls:
            return False
        
        self.visited_urls.add(url)
        logger.info(f"Processing file: {url}")
        
        # Download file
        content, file_ext = self.download_file(url)
        if not content:
            return False
        
        # Extract text
        text = self.extract_text(content, file_ext)
        
        # Check for keywords (or download unconditionally when no keywords set)
        if self.contains_keywords(text):
            if self.keywords:
                logger.info(f"Keywords found in {url}")
            else:
                logger.info(f"Downloading file: {url}")
            filepath = self.save_file(content, url, file_ext)
            if filepath:
                self.downloaded_files.append(filepath)
                return True
        else:
            logger.debug(f"No keywords found in {url}")
        
        return False
    
    def crawl_page(self, url: str, depth: int = 2) -> None:
        """
        Crawl a webpage and extract links.
        
        Args:
            url: Page URL to crawl
            depth: Maximum depth to crawl
        """
        if depth <= 0 or url in self.visited_urls:
            return
        
        if not self.is_valid_url(url):
            return
        
        # If it's a file URL, process it directly
        if self.is_file_url(url):
            self.process_file_url(url)
            return
        
        self.visited_urls.add(url)
        logger.info(f"Crawling page: {url} (depth: {depth})")
        
        try:
            response = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links
            links = set()
            for tag in soup.find_all(['a', 'link']):
                href = tag.get('href')
                if href:
                    absolute_url = urljoin(url, href)
                    links.add(absolute_url)
            
            # Process links
            for link in links:
                if link in self.visited_urls:
                    continue
                
                if self.is_file_url(link):
                    self.process_file_url(link)
                elif self.is_valid_url(link):
                    self.crawl_page(link, depth - 1)
        
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
    
    def start(self) -> None:
        """Start the crawling process."""
        logger.info("Starting file crawler...")
        
        try:
            self.crawl_page(self.base_url, depth=self.max_depth)
            
            # Print summary
            print("\n=== Crawling Complete ===")
            print(f"Total files downloaded: {len(self.downloaded_files)}")
            print(f"Files saved to: {os.path.abspath(self.output_dir)}")
            
            if self.downloaded_files:
                print("\nDownloaded files:")
                for filepath in self.downloaded_files:
                    print(f"  - {filepath}")
            else:
                print("\nNo files were found on the site.")
        
        except KeyboardInterrupt:
            logger.info("\nCrawling interrupted by user")
            print(f"\nPartially downloaded files saved to: {os.path.abspath(self.output_dir)}")
        except Exception as e:
            logger.error(f"Error during crawling: {e}")


def main():
    """Main entry point."""
    print("\n" + "="*50)
    print("File Crawler - Download files matching keywords")
    print("="*50)
    
    # Get user input
    url = input("\nEnter the URL of the website to scrape: ").strip()
    keywords_input = input("Enter the keywords to search for (comma-separated): ").strip()
    
    if not url:
        print("Error: URL is required")
        sys.exit(1)
    
    keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
    
    if not keywords:
        print("No keywords entered — all files on the site will be downloaded.")
    
    # Create crawler and start
    crawler = FileCrawler(url, keywords)
    crawler.start()


if __name__ == "__main__":
    main()
