# FileCrawler

A Python script that downloads files from a website matching specified keywords in their content. Supports PDFs, Word documents (.docx), and images with OCR capabilities.

## Features

- 🔍 **Web Crawling**: Automatically traverses websites to find downloadable files
- 📄 **Multiple File Types**: Supports PDF, DOCX, and image files (PNG, JPG, GIF, etc.)
- 🔎 **Keyword Search**: Searches file content for specified keywords
- 🖼️ **OCR Support**: Uses Tesseract OCR to extract text from images
- 📁 **Organized Downloads**: Saves matching files to a local directory
- 🛡️ **Error Handling**: Gracefully handles inaccessible URLs and unsupported file types
- 📝 **Detailed Logging**: Provides progress updates and summary of results

## Requirements

- Python 3.7 or higher
- Tesseract OCR (for image text extraction)

### Installing Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download the installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/xta7529/FileCrawler.git
cd FileCrawler
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python file_crawler.py
```

The script will prompt you for:
1. **URL**: The website to scrape (e.g., `https://cigreireland.ie/`)
2. **Keywords**: Comma-separated keywords to search for (e.g., `technology, innovation, research`)

### Example

```
==================================================
File Crawler - Download files matching keywords
==================================================

Enter the URL of the website to scrape: https://cigreireland.ie/
Enter the keywords to search for (comma-separated): technology, research

2024-01-12 10:00:00 - INFO - Initialized FileCrawler for https://cigreireland.ie/
2024-01-12 10:00:00 - INFO - Keywords: technology, research
2024-01-12 10:00:00 - INFO - Starting file crawler...
...

=== Crawling Complete ===
Total files downloaded: 5
Files saved to: /path/to/downloaded_files

Downloaded files:
  - downloaded_files/document1.pdf
  - downloaded_files/report2.docx
  - downloaded_files/image3.png
  - downloaded_files/paper4.pdf
  - downloaded_files/presentation5.pdf
```

## How It Works

1. **Web Scraping**: The script starts at the provided URL and extracts all links
2. **File Discovery**: Identifies downloadable files (PDFs, DOCX, images) on the page and linked pages
3. **Content Extraction**: 
   - PDFs: Text extracted using `pdfplumber` and `PyPDF2`
   - DOCX: Text extracted using `python-docx`
   - Images: Text extracted using Tesseract OCR
4. **Keyword Matching**: Searches extracted text for specified keywords (case-insensitive)
5. **File Download**: Downloads and saves matching files to `downloaded_files/` directory

## Dependencies

- `requests`: HTTP library for downloading content
- `beautifulsoup4`: HTML parsing and link extraction
- `PyPDF2`: PDF text extraction (fallback)
- `pdfplumber`: PDF text extraction (primary)
- `pytesseract`: Python wrapper for Tesseract OCR
- `Pillow`: Image processing
- `python-docx`: Word document text extraction
- `lxml`: HTML/XML parser

## Configuration

The script can be customized by modifying the `FileCrawler` class parameters:

- `output_dir`: Directory for downloaded files (default: `downloaded_files`)
- `depth`: Maximum crawling depth (default: 2 levels deep)
- `file_extensions`: Supported file types (default: PDF, DOCX, images)

## Error Handling

The script handles common errors:
- Inaccessible URLs (timeouts, connection errors)
- Unsupported file formats
- Missing OCR dependencies
- Invalid user input

## Limitations

- Only crawls within the same domain to avoid excessive external link following
- Maximum crawl depth is limited to prevent infinite loops
- Large files may take time to download and process
- OCR accuracy depends on image quality

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Troubleshooting

### "Tesseract not found" error
Make sure Tesseract OCR is installed and in your system PATH. See the installation instructions above.

### No files downloaded
- Verify the URL is accessible
- Check that keywords match content in the files
- Ensure file types are supported (PDF, DOCX, images)
- Check the logs for any error messages

### Slow performance
- The script processes each file sequentially
- Large PDFs and high-resolution images take longer to process
- Consider reducing the crawl depth or being more specific with the URL
