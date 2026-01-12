#!/usr/bin/env python3
"""
Example script demonstrating programmatic usage of FileCrawler.
This is an alternative to the interactive mode.
"""

from file_crawler import FileCrawler

def main():
    # Configuration
    url = "https://example.com"  # Replace with your target URL
    keywords = ["technology", "innovation", "research"]  # Replace with your keywords
    output_directory = "downloaded_files"  # Optional: customize output directory
    
    # Create and run crawler
    print(f"Starting crawler for: {url}")
    print(f"Searching for keywords: {', '.join(keywords)}")
    print(f"Output directory: {output_directory}\n")
    
    crawler = FileCrawler(url, keywords, output_dir=output_directory)
    crawler.start()

if __name__ == "__main__":
    main()
