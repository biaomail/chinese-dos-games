import hashlib
import os
import json
import urllib.request
import urllib.parse
import threading
from concurrent.futures import ThreadPoolExecutor, wait
import base64
import shutil

root = os.path.dirname(os.path.abspath(__file__))
PREFIX = "https://dos-bin.zczc.cz/"
DESTINATION = os.path.join(root, 'bin')
ROM_DEST = os.path.join(root, 'roms')
BUF_SIZE = 65536
THREAD_SIZE = 8
BATCH_SIZE = 600
WIP_FILE = os.path.join(root, 'wip.txt')
DONE_FILE = os.path.join(root, 'done.txt')
GAMES_JSON = os.path.join(root, 'games.json')
MAPPING_FILE = os.path.join(ROM_DEST, 'mapping.txt')

lock = threading.Lock()

def generate_sha256(file):
    sha256 = hashlib.sha256()
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()

def download(identifier, url, file, expected_sha):
    print(f'Downloading {identifier} ...')
    try:
        urllib.request.urlretrieve(url, file)
        if generate_sha256(file) != expected_sha:
            print(f"SHA256 mismatch for {identifier}, removing corrupt file!")
            os.remove(file)
            return False
        # Only add to wip.txt after verified
        with lock:
            with open(WIP_FILE, 'a', encoding='utf8') as wf:
                wf.write(identifier + '\n')
        print(f"Downloaded and verified: {identifier}")
        return True
    except Exception as e:
        print(f"Download failed for {identifier}: {e}")
        if os.path.exists(file):
            os.remove(file)
        return False

def get_already_downloaded():
    if not os.path.exists(WIP_FILE):
        return set()
    with open(WIP_FILE, encoding='utf8') as wf:
        return set(line.strip() for line in wf if line.strip())

def move_files_bin_to_roms():
    os.makedirs(ROM_DEST, exist_ok=True)
    # append is fine since batch runs are non-overlapping
    mapping = []
    for fname in os.listdir(DESTINATION):
        src = os.path.join(DESTINATION, fname)
        # encode filename to base64 (no extension as original is always .zip)
        b64name = base64.urlsafe_b64encode(fname.encode('utf-8')).decode('ascii').rstrip('=')
        dst = os.path.join(ROM_DEST, f"{b64name}.zip")
        print(f"Moving {fname} -> {dst}")
        shutil.move(src, dst)
        mapping.append((fname, f"{b64name}.zip"))
    # Update mapping.txt
    if mapping:
        with open(MAPPING_FILE, 'a', encoding='utf8') as f:
            for orig, b64ed in mapping:
                f.write(f"{orig} -> {b64ed}\n")

def main():
    # Step 1: Exit early if done.txt exists
    if os.path.exists(DONE_FILE):
        print("All downloads completed. Exiting.")
        return
    os.makedirs(DESTINATION, exist_ok=True)
    # Load all games
    with open(GAMES_JSON, encoding='utf8') as f:
        game_infos = json.load(f)["games"]
    all_ids = list(game_infos.keys())
    already = get_already_downloaded()
    left = [gid for gid in all_ids if gid not in already]

    if not left:
        # Step 5: All done, create done.txt, commit
        with open(DONE_FILE, 'w', encoding='utf8') as f:
            f.write('')
        print('All done, created done.txt')
        return

    now_batch = left[:BATCH_SIZE]
    print(f"Will try to download {len(now_batch)} games ...")

    # Download up to BATCH_SIZE files not in wip.txt
    executor = ThreadPoolExecutor(max_workers=THREAD_SIZE)
    all_tasks = []
    for identifier in now_batch:
        info = game_infos[identifier]
        file = os.path.normcase(os.path.join(DESTINATION, identifier + '.zip'))
        url = PREFIX + urllib.parse.quote(identifier) + '.zip'
        expected_sha = info['sha256']
        # Respect interrupted/incomplete downloads and verification per rules
        if os.path.isfile(file) and generate_sha256(file) == expected_sha:
            print(f"Already downloaded: {identifier}")
            with lock:
                with open(WIP_FILE, 'a', encoding='utf8') as wf:
                    wf.write(identifier + '\n')
            continue
        t = executor.submit(download, identifier, url, file, expected_sha)
        all_tasks.append(t)
    if all_tasks:
        wait(all_tasks)

    # Move newly downloaded files to roms/ after base64-encoding filenames
    move_files_bin_to_roms()
    print('Batch complete. Commit "roms/" and wip.txt.')
    # Step 4: The commit should be handled by caller/CI script as per workflow
    # Final check: All done?
    already = get_already_downloaded()
    left = [gid for gid in all_ids if gid not in already]
    if not left:
        print('Everything downloaded. Creating done.txt ...')
        with open(DONE_FILE, 'w', encoding='utf8') as f:
            f.write('')
        print('All done, created done.txt')

if __name__ == '__main__':
    main()
