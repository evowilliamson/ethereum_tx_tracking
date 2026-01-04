#!/usr/bin/env python3
"""
Export filtered Sui trades JSON to CSV
"""

import json
import csv
from datetime import datetime
from fetch_all_trades import export_to_csv

def main():
    enriched_json = 'sui_trades_enriched_priced_82acf572.json'
    output_csv = 'sui_trades.csv'
    blockchain = 'sui'
    address = '0x6525b9a3a48a54e518cf57618c68621074be2ffd724f8a51e7b3048682acf572'
    
    print("=" * 80)
    print("Exporting Filtered Sui Trades to CSV")
    print("=" * 80)
    
    # Export using the existing function
    export_to_csv(enriched_json, output_csv, blockchain, address, append_mode=False)
    
    print("\n✓ Export complete!")

if __name__ == '__main__':
    main()





