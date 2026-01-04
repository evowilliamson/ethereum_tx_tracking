#!/usr/bin/env python3
"""
Download historical data for the top 10 coins from CoinGecko.
Uses the symbol mapping to get coin IDs, downloads each, and organizes them in feeds/ directory.
"""

import json
import os
import subprocess
import time
import requests
from pathlib import Path
from typing import List, Tuple

MAPPING_FILE = 'coingecko_symbol_mapping.json'
FEEDS_DIR = 'feeds'
DOWNLOADS_DIR = os.path.expanduser('~/Downloads')
DOWNLOAD_SCRIPT = 'download_coingecko_historical.py'


def load_mapping() -> dict:
    """Load the symbol to coin_id mapping"""
    if not os.path.exists(MAPPING_FILE):
        raise FileNotFoundError(f"Mapping file not found: {MAPPING_FILE}")
    
    with open(MAPPING_FILE, 'r') as f:
        return json.load(f)


def get_top10_coin_ids() -> List[str]:
    """Get the top 10 coin IDs by market cap from CoinGecko"""
    print("  Fetching top 10 coins from CoinGecko API...")
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {'vs_currency': 'usd', 'per_page': 10, 'order': 'market_cap_desc', 'page': 1}
        time.sleep(0.5)  # Rate limit protection
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            top10 = response.json()
            coin_ids = [coin.get('id') for coin in top10 if coin.get('id')]
            print(f"  ✓ Got {len(coin_ids)} coin IDs")
            return coin_ids
        else:
            print(f"  ⚠ API error: {response.status_code}")
            return []
    except Exception as e:
        print(f"  ⚠ Error fetching top 10: {e}")
        return []


def get_newest_csv_file(downloads_path: Path) -> Path:
    """
    Get the newest CSV file in Downloads directory.
    Returns the Path to the newest file, or None if no CSV files found.
    """
    csv_files = list(downloads_path.glob('*.csv'))
    if not csv_files:
        return None
    
    # Sort by modification time, newest first
    newest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
    return newest_file


def download_and_move_coin(coin_id: str, feeds_dir: Path) -> bool:
    """
    Download historical data for a coin and move it to feeds directory.
    Returns True if successful, False otherwise.
    """
    print(f"\n{'='*60}")
    print(f"Processing: {coin_id}")
    print(f"{'='*60}")
    
    try:
        downloads_path = Path(DOWNLOADS_DIR)
        if not downloads_path.exists():
            downloads_path.mkdir(parents=True, exist_ok=True)
        
        # Call the download script (use sys.executable to use same Python as this script)
        print(f"  Calling download script for {coin_id}...")
        import sys
        result = subprocess.run(
            [sys.executable, DOWNLOAD_SCRIPT, coin_id, DOWNLOADS_DIR],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout (to allow for manual captcha solving)
        )
        
        if result.returncode != 0:
            print(f"  ✗ Download script failed for {coin_id}")
            print(f"    Error: {result.stderr}")
            return False
        
        # Wait a moment for file to finish downloading
        time.sleep(2)
        
        # Find the newest CSV file in Downloads
        newest_csv = get_newest_csv_file(downloads_path)
        if not newest_csv:
            print(f"  ✗ No CSV file found in Downloads directory")
            return False
        
        print(f"  Found downloaded file: {newest_csv.name}")
        
        # Rename the file in Downloads to <coin_id>.csv
        renamed_path = downloads_path / f"{coin_id}.csv"
        print(f"  Renaming {newest_csv.name} -> {coin_id}.csv in Downloads...")
        newest_csv.rename(renamed_path)
        
        # Target path in feeds directory
        target_path = feeds_dir / f"{coin_id}.csv"
        
        # Remove target if it exists (overwrite)
        if target_path.exists():
            print(f"  Overwriting existing file: feeds/{coin_id}.csv")
            target_path.unlink()
        
        # Move the file to feeds directory
        print(f"  Moving {coin_id}.csv -> feeds/{coin_id}.csv")
        renamed_path.rename(target_path)
        
        print(f"  ✓ Successfully downloaded and moved {coin_id}.csv")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"  ✗ Download script timed out for {coin_id}")
        return False
    except Exception as e:
        print(f"  ✗ Error processing {coin_id}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to download top 10 coins"""
    print("="*60)
    print("Downloading Historical Data for Top 10 Coins")
    print("="*60)
    
    # Get top 10 coin IDs (from API, ordered by market cap)
    coin_ids = get_top10_coin_ids()
    print(f"\nTop 10 coin IDs to download:")
    for i, coin_id in enumerate(coin_ids, 1):
        print(f"  {i}. {coin_id}")
    
    # Create feeds directory
    feeds_dir = Path(FEEDS_DIR)
    feeds_dir.mkdir(exist_ok=True)
    print(f"\n✓ Created/verified {FEEDS_DIR}/ directory")
    
    # Download each coin
    print(f"\nStarting downloads...")
    failed_coins = []
    
    for coin_id in coin_ids:
        success = download_and_move_coin(coin_id, feeds_dir)
        if not success:
            failed_coins.append(coin_id)
        
        # Small delay between downloads
        if coin_id != coin_ids[-1]:  # Don't wait after the last one
            print("\n  Waiting 5 seconds before next download...")
            print("  (You can solve any captcha that appears during this time)")
            time.sleep(5)
    
    # Summary
    print(f"\n{'='*60}")
    print("Download Summary")
    print(f"{'='*60}")
    print(f"Total coins: {len(coin_ids)}")
    print(f"Successful: {len(coin_ids) - len(failed_coins)}")
    print(f"Failed: {len(failed_coins)}")
    
    if failed_coins:
        print(f"\nFailed coins:")
        for coin_id in failed_coins:
            print(f"  - {coin_id}")
    else:
        print("\n✓ All downloads completed successfully!")
    
    print(f"\nFiles saved in: {feeds_dir.absolute()}")


if __name__ == "__main__":
    main()

