import requests
import signal
import sys
import subprocess
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
import multiprocessing

# === CONFIGURATION ===
class Config:
    PLAYLIST_PATH = ""
    TIMEOUT = 5
    EXTENDED_TIMEOUT = None
    VERBOSITY = 0
    MAX_WORKERS = None
    MAX_CONNECTIONS = 3
    MAX_ACQUIRE_TIMEOUT = 10
    MAX_ACQUIRE_RETRIES = 3
    LOG_TO_FILE = True
    LOG_FILE_PATH = "iptv_check.log"

config = Config()
connection_semaphore = Semaphore(config.MAX_CONNECTIONS)
url_cache = {}

def setup_logging():
    handlers = [logging.StreamHandler(sys.stdout)]
    if config.LOG_TO_FILE:
        handlers.append(logging.FileHandler(config.LOG_FILE_PATH, mode='w'))

    logging.basicConfig(
        level=[logging.CRITICAL, logging.INFO, logging.DEBUG][config.VERBOSITY],
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

def check_channel_status(url, timeout, retries=None, extended_timeout=None):
    if retries is None:
        retries = 6

    if url in url_cache:
        return url_cache[url]

    headers = {'User-Agent': 'Mozilla/5.0 (...)'}
    min_data_threshold = 1024 * 500

    def attempt_check(current_timeout):
        accumulated_data = 0
        for attempt in range(retries):
            for _ in range(config.MAX_ACQUIRE_RETRIES):
                if connection_semaphore.acquire(timeout=config.MAX_ACQUIRE_TIMEOUT):
                    break
            else:
                logging.warning(f"Could not acquire connection slot for: {url}")
                continue

            try:
                with requests.get(url, stream=True, timeout=(5, current_timeout), headers=headers) as resp:
                    if resp.status_code == 200:
                        if 'video' in resp.headers.get('Content-Type', '') or '.ts' in url:
                            for chunk in resp.iter_content(1024 * 1024):
                                if not chunk:
                                    break
                                accumulated_data += len(chunk)
                                if accumulated_data >= min_data_threshold:
                                    return 'Alive'
                    return 'Dead'
            except Exception as e:
                logging.debug(f"Attempt {attempt + 1} failed for {url}: {e}")
            finally:
                connection_semaphore.release()
                time.sleep(attempt + 1)
        return 'Dead'

    status = attempt_check(timeout)
    if status == 'Dead' and extended_timeout:
        status = attempt_check(extended_timeout)

    if status == 'Alive':
        try:
            result = subprocess.run(['ffmpeg', '-i', url, '-t', '5', '-f', 'null', '-'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            if result.returncode != 0:
                logging.debug(f"ffmpeg stderr for {url}: {result.stderr.decode(errors='ignore')}")
                status = 'Dead'
        except subprocess.TimeoutExpired:
            status = 'Dead'

    url_cache[url] = status
    return status

def get_stream_info(url):
    try:
        result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                                 '-show_entries', 'stream=codec_name,width,height,r_frame_rate',
                                 '-of', 'default=noprint_wrappers=1', url],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        output = result.stdout.decode()
        codec = width = height = fps = None
        for line in output.splitlines():
            if line.startswith("codec_name="):
                codec = line.split("=")[1].upper()
            elif line.startswith("width="):
                width = int(line.split("=")[1])
            elif line.startswith("height="):
                height = int(line.split("=")[1])
            elif line.startswith("r_frame_rate="):
                num, den = map(int, line.split("=")[1].split("/"))
                fps = round(num / den) if den else None
        resolution = "SD"
        if width and height:
            if width >= 3840:
                resolution = "4K"
            elif width >= 1920:
                resolution = "1080p"
            elif width >= 1280:
                resolution = "720p"
        return resolution, fps, codec
    except Exception as e:
        logging.debug(f"ffprobe video failed for {url}: {e}")
        return None, None, None

def get_audio_info(url):
    try:
        result = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                                 '-show_entries', 'stream=codec_name,bit_rate',
                                 '-of', 'default=noprint_wrappers=1', url],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        output = result.stdout.decode()
        codec = bitrate = None
        for line in output.splitlines():
            if line.startswith("codec_name="):
                codec = line.split("=")[1].upper()
            elif line.startswith("bit_rate="):
                bitrate = int(line.split("=")[1]) // 1000
        return bitrate, codec
    except Exception as e:
        logging.debug(f"ffprobe audio failed for {url}: {e}")
        return None, None

def process_channel(args):
    index, channel_name, stream_url, timeout, extended_timeout = args
    if timeout is None:
        timeout = 5
    status = check_channel_status(stream_url, timeout, extended_timeout=extended_timeout)
    if status == 'Alive':
        resolution, fps, vcodec = get_stream_info(stream_url)
        abitrate, acodec = get_audio_info(stream_url)
        video_info = f"{resolution:<5} {str(fps).rjust(2)}fps {vcodec}" if resolution and vcodec and fps else "Unknown"
        audio_info = f"{str(abitrate).rjust(3)} kbps {acodec}" if abitrate and acodec else "Unknown"
        info = f"Video: {video_info:<15} | Audio: {audio_info}"
    else:
        info = ""
    return index, channel_name, status, info

def prompt_category_selection(file_path):
    categories = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.search(r'group-title="([^"]+)', line)
            if match:
                categories.add(match.group(1))
    if not categories:
        print("No categories found in the playlist.")
        return None
    sorted_categories = sorted(categories)
    print("\nAvailable Categories:")
    for idx, cat in enumerate(sorted_categories, 1):
        print(f"{idx}. {cat}")
    choice = input("\nSelect a category by number (or press Enter for all): ")
    if choice.strip() == "":
        return None
    try:
        idx = int(choice) - 1
        return sorted_categories[idx] if 0 <= idx < len(sorted_categories) else None
    except ValueError:
        print("Invalid selection. Proceeding with all channels.")
        return None

def parse_m3u8_file(file_path, timeout, extended_timeout, selected_category=None):
    if timeout is None:
        timeout = 5

    if selected_category is None:
        selected_category = prompt_category_selection(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    tasks = []
    index = 0
    for i in range(len(lines)):
        if lines[i].startswith('#EXTINF') and i + 1 < len(lines):
            if selected_category and f'group-title="{selected_category}"' not in lines[i]:
                continue
            parts = lines[i].split(',')
            channel_name = parts[1].strip() if len(parts) > 1 else 'Unknown'
            stream_url = lines[i + 1].strip()
            if stream_url:
                index += 1
                tasks.append((index, channel_name, stream_url, timeout, extended_timeout))

    if not tasks:
        print("No channels found for the selected category.")
        return

    print(f"\nProcessing {len(tasks)} channels with {config.MAX_CONNECTIONS} concurrent connections...\n")
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS or multiprocessing.cpu_count()) as executor:
        futures = [executor.submit(process_channel, task) for task in tasks]
        for future in as_completed(futures):
            idx, name, status, info = future.result()
            symbol = "✓" if status == 'Alive' else "✗"
            color = "green" if status == 'Alive' else "red"
            line = f"{idx:<4}/{len(tasks)} {symbol} {name.ljust(32)} | {info:<60}"
            print(line)

def run_check(playlist_path, timeout, max_connections):
    config.PLAYLIST_PATH = playlist_path
    config.TIMEOUT = timeout
    config.MAX_CONNECTIONS = max_connections
    setup_logging()
    parse_m3u8_file(config.PLAYLIST_PATH, config.TIMEOUT, config.EXTENDED_TIMEOUT)