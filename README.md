# CLI Downloader

A robust Python command-line tool designed to reconnoiter a webpage, extract download links, and download files with a visual progress bar.

## Features

- 🔍 **Auto-Discovery**: Scrapes web pages for potential download links.
- 📂 **Smart Filtering**: Automatically detects common file extensions (PDF, ZIP, EXE, MP4, ISO, etc.).
- 📊 **Progress Bar**: Visual feedback during downloads using `tqdm`.
- 🛠 **Dependency Check**: Automatically checks and attempts to install missing libraries if they are not present.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/CliDownloader.git
   cd CliDownloader
   ```

2. Install requirements (optional, as the script attempts to self-install):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script using Python:

```bash
python CliDownloader2.py
```

Follow the on-screen prompts:
1. Enter the target URL.
2. View the list of detected files.
3. Select a file number to download.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
