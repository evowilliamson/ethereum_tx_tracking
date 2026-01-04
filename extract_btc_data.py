#!/usr/bin/env python3
"""
Extract BTC historical data from CoinGecko page HTML.
The browser has loaded the page, so we need to get the HTML from it.
"""

import csv
import re
from datetime import datetime

def extract_table_data(html):
    """Extract table data from HTML"""
    data_rows = []
    
    # Look for table rows
    table_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    
    for row in table_rows:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
        if len(cells) >= 2:
            clean_cells = []
            for cell in cells:
                # Remove HTML tags
                clean = re.sub(r'<[^>]+>', '', cell)
                clean = re.sub(r'\s+', ' ', clean).strip()
                clean_cells.append(clean)
            
            # Check if it looks like data (has date or price)
            if any(re.search(r'\$|^\d{4}-\d{2}-\d{2}', cell) for cell in clean_cells):
                data_rows.append(clean_cells)
    
    return data_rows

if __name__ == "__main__":
    print("This script needs the HTML from the browser.")
    print("Since the browser has loaded the page, the data should be accessible.")
    print("=" * 80)
