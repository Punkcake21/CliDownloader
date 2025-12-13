# CLI Downloader

A robust Python command-line tool designed to reconnoiter a webpage, extract download links, and download files with a visual progress bar.

## Features

- 🕷️ **Web Crawler**: Recursively crawls websites (user-defined depth) to discover files across multiple pages.
- 🔍 **Auto-Discovery**: Scrapes web pages for potential download links.
- 📂 **Smart Filtering**: Automatically detects common file extensions (PDF, ZIP, EXE, MP4, ISO, etc.).
- 🎛️ **Interactive Menu**: User-friendly CLI to select files, refresh lists, or quit.
- 📊 **Progress Bar**: Visual feedback during downloads using `tqdm`.
- 📝 **Logging Levels**: Adjustable verbosity (Quiet, Normal, Verbose) for debugging or silent operation.
- 🛡️ **Safety & Robustness**: Filename sanitization to prevent filesystem errors and connection timeouts.
- 🛠 **Dependency Check**: Automatically checks and attempts to install missing libraries.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/punkcake21/CliDownloader.git
   cd CliDownloader
   ```

2. Install requirements (optional, as the script attempts to self-install):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script using Python:

```bash
python CliDownloader.py
```

Follow the on-screen prompts:
1. Select logging level (Quiet, Normal, Verbose).
2. Choose whether to crawl a website or analyze a single page.
   - If crawling: Enter start URL and max depth.
   - If single page: Enter the target URL.
3. View the list of detected files.
4. Select a file number to download, 'r' to refresh, or 'q' to quit.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
