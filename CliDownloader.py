import requests
import os 
import subprocess
import sys
from tqdm import tqdm 
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

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

def fetch_and_parse(target_url):
    """Downloads HTML content and parses it with BeautifulSoup."""
    print(f"[*] Connecting to: {target_url}")

    try:
        # 1. Execute HTTP Request
        response = requests.get(target_url, timeout=10)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"[-] Connection or HTTP error: {e}")
        return None, None

    # 2. HTML Parsing
    soup = BeautifulSoup(response.text, 'html.parser')
    print("[*] HTML parsing completed.")

    # 3. Base domain extraction (normalization)
    parsed_url = urlparse(target_url)
    if target_url.endswith('/'):
        base_url = target_url
    else:
        base_url = os.path.dirname(target_url) + '/'

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

    print(f"[*] Found {len(all_links)} unique links (raw).")
    return list(all_links)

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
    print(f"[*] Found {len(download_list)} downloadable files after filtering.")
    return download_list

def present_cli_menu(download_list):
    print("\n" + "="*70)
    print("         DOWNLOADS FOUND ON WEB PAGE")
    print("="*70)
    print("     [No.] | FILE NAME")
    print("-" * 70)

    for i, item in enumerate(download_list):
        display_name = item['name'][:60] + (item['name'][60:] and '...')
        print(f"    [{i+1:2}] | {display_name}")

    print("-" * 70)

    while True:
        try:
            user_input = input(
                "Enter file No. to download, 'r' to refresh list, 'q' to quit:" 
            ).strip().lower()

            if user_input == 'q':
                print("[*] Exiting program.")
                return None

            if user_input == 'r':
                print("--- REFRESH LIST ---")
                present_cli_menu(download_list)
                continue

            selected_index = int(user_input)

            if 1 <= selected_index <= len(download_list):
                return download_list[selected_index -1]
            else:
                print(f"[-] Invalid number. Enter a number between 1 and {len(download_list)}")

        except ValueError:
            print("[-] Unrecognized input. Enter a number, 'r' or 'q'.")

def download_file(url, filename):
    save_path = os.path.join(os.getcwd(), filename)

    print(f"\n[*] Starting download: '{filename}'")
    print(f"[*] URL: {url}")

    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))

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
        
def main():

    check_and_install_dependencies()

    print("\n" + "="*70)
    print("           CLI RECONNAISSANCE AND DOWNLOAD TOOL")
    print("="*70)

    target_url = input("Enter the web page URL to analyze: ").strip()

    if not target_url:
        print("[-] URL not provided. Exiting.")
        return

    soup, base_url = fetch_and_parse(target_url)

    if not soup:
        return

    raw_links = extract_all_links(soup, base_url)
    final_download_list = filter_download_links(raw_links)

    if final_download_list:
        selected_item = present_cli_menu(final_download_list)

        if selected_item:
            download_file(selected_item['url'], selected_item['name'])
    else:
        print("\n[-] No download files found with defined extensions.")

if __name__ == '__main__':
    main()
