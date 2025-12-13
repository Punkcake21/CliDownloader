import os 
import subprocess
import sys
import logging
import warnings

def check_and_install_dependencies():
    REQUIRED_PACKAGES = {
        "requests": "requests",
        "bs4": "beautifulsoup4",
        "tqdm": "tqdm"
    }

    missing_packages = []

    print("[*] Checking dependencies...")

    for module_name, package_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)

    if not missing_packages:
        print("[+] All dependencies are satisfied.")
        return
    
    print(f"[-] Missing dependencies detected: {', '.join(missing_packages)}")
    print("[*] Attempting to install missing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("[+] Dependency installation completed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"[-] Error installing dependencies: {e}")
        print("[-] Please install packages manually using: pip install requests beautifulsoup4 tqdm")
        sys.exit(1)
    except FileNotFoundError:
        print("[-] 'pip' command not found. Ensure python and pip are configured correctly.")
        sys.exit(1)

import requests
import re
from tqdm import tqdm 
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from urllib.parse import urljoin, urlparse

# Suppress BeautifulSoup XML-as-HTML warnings for mixed pages
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def is_same_domain(url1, url2):
    """Checks if two URLs belong to the same domain."""
    domain1 = urlparse(url1).netloc
    domain2 = urlparse(url2).netloc
    return domain1 == domain2

def start_crawler(start_url, max_depth=1):
    """crawls the website starting from start_url up to max_depth."""
    to_visit = {start_url}
    visited = set()
    all_download_links = []
    initial_domain = urlparse(start_url).netloc

    current_depth = 0

    pages_crawled = 0
    while to_visit and current_depth < max_depth and pages_crawled < MAX_PAGES:
        current_depth += 1
        next_to_visit = set()

        for url in to_visit:
            if url in visited or pages_crawled >= MAX_PAGES:
                continue

            logging.debug("Crawling: %s (Depth: %d)", url, current_depth)
            pages_crawled += 1
            if pages_crawled % 10 == 0:
                logging.info("[*] Crawled %d pages...", pages_crawled)

            soup, base_url = fetch_and_parse(url)
            visited.add(url)

            if not soup:
                continue

            all_links = extract_all_links(soup, base_url)
            current_downloads = filter_download_links(all_links)
            
            # deduplicate by URL
            all_download_links.extend(current_downloads)

            for link in all_links:
                if is_same_domain(link, start_url) and link not in visited:
                    next_to_visit.add(link)

        to_visit = next_to_visit

    logging.info("[*] Crawling completed. Found %d downloadable files.", len(all_download_links))
    return all_download_links

def fetch_and_parse(target_url):
    """Downloads HTML content and parses it with BeautifulSoup."""
    logging.debug("Connecting to: %s", target_url)

    # Validate URL scheme
    parsed = urlparse(target_url)
    if parsed.scheme not in ['http', 'https']:
        print("[-] Invalid URL scheme. Only HTTP and HTTPS are supported.")
        return None, None

    try:
        # 1. Execute HTTP Request
        response = requests.get(target_url, timeout=10)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"[-] Connection or HTTP error: {e}")
        return None, None

    # 2. HTML Parsing
    soup = BeautifulSoup(response.text, 'html.parser')
    logging.debug("HTML parsing completed for: %s", target_url)

    # 3. Base domain extraction (normalization)
    parsed_url = urlparse(target_url)
    # Use scheme and netloc to form a reliable base URL
    base_url = target_url

    return soup, base_url

def extract_all_links(soup, base_url):
    """Extracts all hrefs and normalizes them."""
    all_links = set()

    for tag in soup.find_all('a'):
        href = tag.get('href')

        if href:
            # 4. Normalization
            full_url = urljoin(base_url, href)
            all_links.add(full_url)

    for tag in soup.find_all(attrs={'data-download-url': True}):
        data_url = tag.get('data-download-url')

        if data_url:
            full_url = urljoin(base_url, data_url)
            all_links.add(full_url)

    logging.debug("Found %d unique links (raw).", len(all_links))
    return list(all_links)


def deduplicate_downloads(downloads):
    """Remove duplicate downloads by URL while preserving order."""
    seen = set()
    unique = []
    for d in downloads:
        if d['url'] not in seen:
            unique.append(d)
            seen.add(d['url'])
    return unique

MAX_PAGES = 100

DOWNLOAD_EXTENSIONS = (
    '.pdf', '.zip', '.tar', '.gz', '.7z', '.rar',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.mp3', '.mp4', '.avi', '.mov', '.ogg',
    '.iso', '.exe', '.dmg', '.apk',
    '.csv', '.xml', '.json', '.deb', '.rpm'
)

def filter_download_links(all_links):
    download_list = []

    for url in all_links:
        if url.lower().endswith(DOWNLOAD_EXTENSIONS):
            parsed_url = urlparse(url)
            file_name = parsed_url.path.split('/')[-1]

            if not file_name:
                continue

            download_list.append({
                'name' : file_name,
                'url' : url
            })
    logging.debug("Found %d downloadable files after filtering.", len(download_list))
    return download_list

def present_cli_menu(download_list):
    while True:
        print("\n" + "="*70)
        print("         DOWNLOADS FOUND ON WEB PAGE")
        print("="*70)
        print("     [No.] | FILE NAME")
        print("-" * 70)

        for i, item in enumerate(download_list):
            display_name = item['name'][:60] + ('...' if len(item['name']) > 60 else '')
            print(f"    [{i+1:2}] | {display_name}")

        print("-" * 70)

        try:
            user_input = input(
                "Enter file No. to download, 'r' to refresh list, 'q' to quit:" 
            ).strip().lower()

            if user_input == 'q':
                print("[*] Exiting program.")
                return None

            if user_input == 'r':
                print("--- REFRESH LIST ---")
                continue

            selected_index = int(user_input)

            if 1 <= selected_index <= len(download_list):
                return download_list[selected_index -1]
            else:
                print(f"[-] Invalid number. Enter a number between 1 and {len(download_list)}")

        except ValueError:
            print("[-] Unrecognized input. Enter a number, 'r' or 'q'.")

def download_file(url, filename):
    # Sanitize filename: remove invalid characters and get basename
    filename = re.sub(r'[^\w\s.-]', '_', filename)
    filename = os.path.basename(filename)
    
    save_path = os.path.join(os.getcwd(), filename)

    print(f"\n[*] Starting download: '{filename}'")
    print(f"[*] URL: {url}")

    r = None
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        total_size = int(r.headers.get('content-length') or 0)

        with open(save_path, 'wb') as f:
            with tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=filename,
                ncols=80
            ) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        print(f"\n[+] DOWNLOAD COMPLETED! File saved in: {save_path}")

    except KeyboardInterrupt:
        print(f"\n\n[!] Download interrupted by user (CTRL+C).")
        if os.path.exists(save_path):
            os.remove(save_path)
            print(f"[*] Partial file '{filename}' deleted.")
        return

    except requests.exceptions.RequestException as e:
        print(f"\n[-] Error downloading {filename}: {e}")
    except Exception as e:
        print(f"\n[-] Generic error: {e}")
    finally:
        try:
            if r is not None:
                r.close()
        except Exception:
            pass
        
def main():

    print("\n" + "="*70)
    print("           CLI RECONNAISSANCE AND DOWNLOAD TOOL")
    print("="*70)

    print("\n[*] start crawler? (y/n): ", end='')
    choice = input().strip().lower()
    if choice == 'y':
        target_url = input("Enter the starting URL for crawling: ").strip()

        if not target_url:
            print("[-] URL not provided. Exiting.")
            return

        while True:
            try:
                max_depth = int(input("Enter crawler max depth (default 2): ").strip() or "2")
                if max_depth > 0:
                    break
                print("[-] Depth must be positive.")
            except ValueError:
                print("[-] Invalid input. Enter a number.")
        print(f"[*] Starting crawler at: {target_url} (Max Depth: {max_depth})")

        all_downloads = start_crawler(target_url, max_depth=max_depth)
        all_downloads = deduplicate_downloads(all_downloads)

        if all_downloads:
            # compact summary
            print("\nCompact results:")
            print("[No.]  FILE NAME\n")
            for i, d in enumerate(all_downloads, start=1):
                print(f"[{i:2}]  {d['name']}")

            selected_item = present_cli_menu(all_downloads)

            if selected_item:
                download_file(selected_item['url'], selected_item['name'])
        else:
            print("\n[-] No download files found during crawling.")

        return

    target_url = input("Enter the web page URL to analyze: ").strip()

    if not target_url:
        print("[-] URL not provided. Exiting.")
        return

    soup, base_url = fetch_and_parse(target_url)

    if not soup:
        return

    raw_links = extract_all_links(soup, base_url)
    final_download_list = filter_download_links(raw_links)
    final_download_list = deduplicate_downloads(final_download_list)

    if final_download_list:
        print("\nCompact results:")
        print("[No.]  FILE NAME")
        for i, d in enumerate(final_download_list, start=1):
            print(f"[{i:2}]  {d['name']}")

        selected_item = present_cli_menu(final_download_list)

        if selected_item:
            download_file(selected_item['url'], selected_item['name'])
    else:
        print("\n[-] No download files found with defined extensions.")

if __name__ == '__main__':
    # ensure dependencies before running
    check_and_install_dependencies()

    # ask for logging level
    print("\nLogging level: (q)uiet, (n)ormal, (v)erbose? [n]: ", end='')
    log_choice = input().strip().lower() or 'n'
    
    if log_choice == 'q':
        level = logging.WARNING
    elif log_choice == 'v':
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

    main()
