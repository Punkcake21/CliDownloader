import os 
import subprocess
import sys
import logging
import warnings
import time

try:
    import requests
    import re
    from tqdm import tqdm 
    from fake_useragent import UserAgent
    from collections import deque
    from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
    from urllib.parse import urljoin, urlparse, unquote, parse_qs
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    pass

##CONFIGURATION
REPO_OWNER = "Punkcake21"
REPO_NAME = "CliDownloader"
FILE_PATH = "CliDownloader.py"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits/main"
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH}"
VERSION_FILE = "last_commit.txt"

def get_latest_commit_sha():
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        return response.json()['sha']
    except Exception as e:
        print(f"Error in update control: {e}")
        return None
    
def update_and_restart(new_sha):
    print("Updating...")
    try:
        response = requests.get(GITHUB_RAW_URL, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 

        with open(FILE_PATH, "wb") as f, tqdm(
            desc="Downloading new version",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        )as bar:
            for data in response.iter_content(block_size):
                f.write(data)
                bar.update(len(data))
        

        with open(VERSION_FILE, "w") as f:
            f.write(new_sha)

        print("Done Updating. Rebooting now...")
        os.execv(sys.executable, ['python'] + sys.argv)
        os.remove(VERSION_FILE) if os.path.exists(VERSION_FILE) else None
    except Exception as e:
        print(f"Error during updating: {e}")

def check_for_updates():
    local_sha = ""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            local_sha = f.read().strip()

    remote_sha = get_latest_commit_sha()

    if remote_sha and remote_sha != local_sha:
        update_and_restart(remote_sha)
    else:
        print("The script is alredy Up-to-date")
        os.remove(VERSION_FILE) if os.path.exists(VERSION_FILE) else None


def check_and_install_dependencies():
    REQUIRED_PACKAGES = {
        "requests": "requests",
        "bs4": "beautifulsoup4",
        "tqdm": "tqdm",
        "fake_useragent": "fake_useragent"
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


global HEADERS
HEADERS = {}

def is_same_domain(url1, url2):
    d1 = urlparse(url1).netloc.lower().lstrip("www.")
    d2 = urlparse(url2).netloc.lower().lstrip("www.")
    return d1 == d2 or d1.endswith("." + d2)

def start_crawler(start_url, max_depth=2, max_pages=100):
    visited = set()
    downloads = []
    seen_download_urls = set()

    queue = deque()
    queue.append((start_url, 0))

    pages_crawled = 0

    try:
        while queue and pages_crawled < max_pages:
            current_url, depth = queue.popleft()

            if current_url in visited:
                continue

            if depth > max_depth:
                continue

            logging.info("Crawling (%d/%d): %s", pages_crawled + 1, max_pages, current_url)

            soup, base_url = fetch_and_parse(current_url)
            visited.add(current_url)
            pages_crawled += 1

            if not soup:
                continue

            links = extract_all_links(soup, base_url)

            # download detection (fast mode: no HEAD/GET checks)
            for item in filter_download_links(links, deep_check=False):
                if item["url"] not in seen_download_urls:
                    downloads.append(item)
                    seen_download_urls.add(item["url"])

            # enqueue next links
            for link in links:
                if (
                    link not in visited
                    and is_same_domain(link, start_url)
                ):
                    queue.append((link, depth + 1))

    except KeyboardInterrupt:
        print(f"\n\n[!] Crawling interrupted by user (CTRL+C).")
        logging.info("Crawling interrupted. Processed %d pages, found %d files.", pages_crawled, len(downloads))

    logging.info(
        "Crawling finished: %d pages, %d downloadable files found",
        pages_crawled,
        len(downloads)
    )

    return downloads


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
        response = requests.get(target_url, timeout=1, headers=HEADERS, allow_redirects=True)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        logging.debug("HTTP request failed for %s: %s", target_url, e)
        return None, None

    # 2. HTML Parsing
    soup = BeautifulSoup(response.text, 'html.parser')
    logging.debug("HTML parsing completed for: %s", target_url)

    # 3. Base domain extraction (normalization)
    parsed_url = urlparse(target_url)
    # Use scheme and netloc to form a reliable base URL
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

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

DOWNLOAD_EXTENSIONS = (
    tuple(line.strip() for line in open('extensions.txt').read().split('\n') if line.strip())
)

def _get_filename_from_content_disposition(headers):
    cd = headers.get('content-disposition')
    if not cd:
        return None

    import re
    m = re.search(r"filename\*=[^']*''(?P<name>[^;]+)", cd)
    if m:
        try:
            return unquote(m.group('name'))
        except Exception:
            return m.group('name')

    m = re.search(r'filename="(?P<name>[^"]+)"', cd)
    if m:
        return m.group('name')

    m = re.search(r'filename=(?P<name>[^;]+)', cd)
    if m:
        return m.group('name').strip(' \"')

    return None


def filter_download_links(all_links, session=None, head_timeout=1, deep_check=False):
   
    download_list = []
    sess = session or requests.Session()

    for url in all_links:
        try:
            parsed_url = urlparse(url)
            path = unquote(parsed_url.path or '')
            file_name = os.path.basename(path)
            ext = os.path.splitext(file_name)[1].lower()

            # 1) direct extension in path
            if file_name and ext in DOWNLOAD_EXTENSIONS:
                download_list.append({'name': file_name, 'url': url})
                continue

            # 2) query params like ?file=..., ?filename=...
            qs = parse_qs(parsed_url.query or '')
            found_in_query = False
            for key in ('file', 'filename', 'download', 'name', 'attachment'):
                if key in qs and qs[key]:
                    candidate = unquote(qs[key][-1])
                    if os.path.splitext(candidate)[1].lower() in DOWNLOAD_EXTENSIONS:
                        download_list.append({'name': os.path.basename(candidate), 'url': url})
                        found_in_query = True
                        break

            if found_in_query:
                continue

            # 3) deep check: HEAD/GET request to inspect headers (optional, slow)
            if not deep_check:
                continue

            try:
                resp = sess.head(url, allow_redirects=True, timeout=head_timeout, headers=HEADERS)
            except requests.RequestException:
                resp = None

            # If HEAD not informative, try lightweight GET
            if resp is None or resp.status_code >= 400 or 'content-disposition' not in (k.lower() for k in resp.headers):
                try:
                    resp = sess.get(url, stream=True, allow_redirects=True, timeout=head_timeout, headers=HEADERS)
                except requests.RequestException:
                    resp = None

            if resp is None:
                continue

            # prefer filename from Content-Disposition
            fname = _get_filename_from_content_disposition(resp.headers)
            final_url = resp.url

            if not fname:
                final_path = unquote(urlparse(final_url).path or '')
                fname = os.path.basename(final_path)

            if not fname:
                continue

            fext = os.path.splitext(fname)[1].lower()
            if fext in DOWNLOAD_EXTENSIONS:
                download_list.append({'name': fname, 'url': final_url})
                continue

            # 4) check Content-Type for common downloadable types
            ctype = resp.headers.get('content-type', '').split(';')[0].lower()
            ctype_map = {
                'application/pdf': '.pdf',
                'application/zip': '.zip',
                'application/x-gzip': '.gz',
                'application/x-7z-compressed': '.7z',
                'application/vnd.rar': '.rar',
                'application/octet-stream': '',
                'application/vnd.android.package-archive': '.apk',
            }

            if ctype in ctype_map:
                if not fext and ctype_map[ctype]:
                    fname = fname + ctype_map[ctype]

                download_list.append({'name': fname, 'url': final_url})

        except StopIteration:
            continue
        except Exception:
            logging.debug("Error processing URL: %s, %s", url, e)

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
                "Enter file No. to download, 'r' to refresh list, 'n' for new URL, 'q' to quit:" 
            ).strip().lower()

            if user_input == 'q':
                print("[*] Exiting program.")
                return None

            if user_input == 'n':
                return 'NEW_URL'

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
    
    filename = re.sub(r'[^\w\s.-]', '_', filename)
    filename = os.path.basename(filename)
    
    download_dir = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    save_path = os.path.join(download_dir, filename)

    print(f"\n[*] Starting download: '{filename}'")
    print(f"[*] URL: {url}")

    r = None
    try:
        r = requests.get(url, stream=True, timeout=1, headers=HEADERS)
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

    while True:
        print("\n[*] start crawler? (y/n) or 'q' to quit: ", end='')
        choice = input().strip().lower()

        if choice == 'q':
            break

        if choice == 'y':
            target_url = input("Enter the starting URL for crawling: ").strip()

            if not target_url:
                print("[-] URL not provided.")
                continue

            while True:
                try:
                    max_depth = int(input("Enter crawler max depth (default 2): ").strip() or "2")
                    if max_depth > 0:
                        break
                    print("[-] Depth must be positive.")
                except ValueError:
                    print("[-] Invalid input. Enter a number.")

            while True:
                try:
                    max_pages = int(input("Enter max pages to crawl (default 100): ").strip() or "100")
                    if max_pages > 0:
                        break
                    print("[-] Pages must be positive.")
                except ValueError:
                    print("[-] Invalid input. Enter a number.")

            print(f"[*] Starting crawler at: {target_url} (Max Depth: {max_depth}, Max Pages: {max_pages})")

            all_downloads = start_crawler(target_url, max_depth=max_depth, max_pages=max_pages)

            if all_downloads:
                while True:
                    selected_item = present_cli_menu(all_downloads)

                    if selected_item == 'NEW_URL':
                        break

                    if selected_item is None:
                        return

                    download_file(selected_item['url'], selected_item['name'])
                
                if selected_item == 'NEW_URL':
                    continue
            else:
                print("\n[-] No download files found during crawling.")
            
            continue

        target_url = input("Enter the web page URL to analyze: ").strip()

        if not target_url:
            print("[-] URL not provided.")
            continue

        soup, base_url = fetch_and_parse(target_url)

        if not soup:
            continue

        raw_links = extract_all_links(soup, base_url)
        final_download_list = filter_download_links(raw_links, deep_check=True)
        final_download_list = deduplicate_downloads(final_download_list)

        if final_download_list:
            while True:
                selected_item = present_cli_menu(final_download_list)

                if selected_item == 'NEW_URL':
                    break

                if selected_item is None:
                    return

                download_file(selected_item['url'], selected_item['name'])
            
            if selected_item == 'NEW_URL':
                continue
        else:
            print("\n[-] No download files found with defined extensions.")

if __name__ == '__main__':

    # ensure dependencies before running
    check_and_install_dependencies()

    import requests
    import re
    from tqdm import tqdm 
    from fake_useragent import UserAgent
    from collections import deque
    from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
    from urllib.parse import urljoin, urlparse, unquote, parse_qs
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

    # check for newer versions and autoinstall
    check_for_updates()

    try:
        ua_obj = UserAgent()

        HEADERS = {
            'User-Agent': ua_obj.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        print(f"[*] Using User-Agent: {HEADERS['User-Agent'][:60]}...")

    except Exception as e:
        print(f"[-] Error generating User-Agent: {e}")
        HEADERS={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    # ask for logging level
    print("\nLogging level: (q)uiet, (n)ormal, (v)erbose? [n]: ", end='')
    log_choice = input().strip().lower() or 'n'
    
    if log_choice == 'q':
        level = logging.WARNING
    elif log_choice == 'v':
        level = logging.DEBUG
    elif log_choice == 'n':
        level = logging.INFO
    else:
        print("[-] Unrecognized choice, defaulting to normal.")
        level = logging.INFO
        time.sleep(2.5)

    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

    main()
