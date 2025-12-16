Web Reconnaissance & Downloader CLI

A robust Python command-line tool designed to crawl websites, detect downloadable files based on user-defined extensions, and download them with an interactive interface.
🚀 Features

    Recursive Crawling: Scans entire website sections starting from a base URL, respecting user-defined depth and page limits.

    Single Page Analysis: Analyzes a specific URL to extract immediate download links.

    Auto-Dependency Management: Automatically checks and installs missing Python libraries upon launch.

    Smart File Detection:

        Detects extensions in the URL path.

        Analyzes query parameters (e.g., ?file=report.pdf).

        Performs HEAD requests to inspect Content-Type and Content-Disposition headers for hidden files.

    Stealthy: Uses randomized User-Agent strings to mimic real browsers.

    Interactive UI: Numbered CLI menu to select files for download.

    Resilient Downloading: Supports visual progress bars (tqdm) and handles file naming automatically.

📋 Prerequisites

    Python 3.6 or higher.

    An active internet connection.

The script will attempt to automatically install the following libraries if they are missing:

    requests

    beautifulsoup4

    tqdm

    fake_useragent

⚙️ Installation & Setup

    Clone or Download the script to your local machine.

    Create the Extensions File (Required): The program looks for a file named extensions.txt in the same directory to determine which file types to hunt for. Create this file and list the extensions you want to find (one per line).

    Example extensions.txt:
    Plaintext

.pdf
.zip
.csv
.xlsx
.docx
.jpg
.png
.exe

Run the script:
Bash

    python your_script_name.py

💻 Usage

Upon running the script, follow the interactive prompts:
1. Select Operation Mode

You will be asked: [*] start crawler? (y/n) or 'q' to quit:

    Crawler Mode (y):

        Enter the Start URL.

        Set Max Depth (e.g., 2 allows the crawler to follow links found on the first page).

        Set Max Pages to limit the scope.

        The tool will traverse the domain and aggregate all found files.

    Single Page Mode (n):

        Enter the specific URL you want to analyze.

        The tool will only look for files linked on that specific page.

2. Logging Level

Select how much detail you want to see in the console:

    q (Quiet): Only errors and critical info.

    n (Normal): Standard progress updates (Default).

    v (Verbose): Detailed debugging info (HTTP connections, parsing details).

3. Download Menu

Once scanning is complete, a list of files will appear:
Plaintext

======================================================================
         DOWNLOADS FOUND ON WEB PAGE
======================================================================
     [No.] | FILE NAME
----------------------------------------------------------------------
    [ 1] | annual_report_2024.pdf
    [ 2] | dataset_backup.zip
----------------------------------------------------------------------
Enter file No. to download, 'r' to refresh list, 'n' for new URL, 'q' to quit:

    Enter a number (e.g., 1) to download that specific file.

    Enter r to refresh the list.

    Enter n to enter a new URL.

    Enter q to quit the program.

📂 Project Structure
Plaintext

.
├── your_script_name.py     # Main application script
├── extensions.txt          # CONFIG FILE (You must create this)
└── [Downloaded Files]      # Files are saved to the current folder

⚠️ Disclaimer

This tool is intended for educational purposes and legitimate reconnaissance (e.g., analyzing your own websites, CTF challenges, or authorized testing). The author is not responsible for any misuse or violation of terms of service of third-party websites. Always ensure you have permission before crawling or downloading data from external domains.
