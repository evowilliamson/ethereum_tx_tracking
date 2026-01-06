#!/usr/bin/env python3
"""
Check progress of top1000 download
Shows: number of coins processed, CSV files created, QuestDB stats
"""

import os
from pathlib import Path
from questdb import get_questdb_connection

def check_progress():
    """Check progress of top1000 download"""
    print("="*80)
    print("Top1000 Download Progress Check")
    print("="*80)
    
    # Check CSV files
    csv_dir = Path.home() / ".dex_trades_extractor" / ".files" / "price" / "cryptocompare"
    if csv_dir.exists():
        csv_files = list(csv_dir.glob("*.csv"))
        print(f"\nCSV Files Created: {len(csv_files)}")
        if csv_files:
            # Get newest files
            csv_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            print("\nMost recently created CSV files:")
            for f in csv_files[:10]:
                size = f.stat().st_size / 1024  # KB
                print(f"  {f.name:20} : {size:>8.1f} KB")
    else:
        print("\nCSV directory not found")
    
    # Check QuestDB
    print("\n" + "="*80)
    print("QuestDB Statistics")
    print("="*80)
    conn = get_questdb_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Count distinct coins
                cur.execute("SELECT COUNT(DISTINCT coin) FROM crypto_hourly")
                coin_count = cur.fetchone()[0]
                print(f"\nCoins with data in QuestDB: {coin_count}")
                
                # Total rows
                cur.execute("SELECT COUNT(*) FROM crypto_hourly")
                total_rows = cur.fetchone()[0]
                print(f"Total rows in QuestDB: {total_rows:,}")
                
                # Rows per coin (top 20)
                cur.execute("""
                    SELECT coin, COUNT(*) as rows 
                    FROM crypto_hourly 
                    GROUP BY coin 
                    ORDER BY rows DESC 
                    LIMIT 20
                """)
                print("\nTop 20 coins by row count:")
                print(f"  {'Coin':<12} {'Rows':>12}")
                print("  " + "-"*26)
                for row in cur.fetchall():
                    print(f"  {row[0]:<12} {row[1]:>12,}")
        except Exception as e:
            print(f"Error querying QuestDB: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()
    else:
        print("\nQuestDB not available")
    
    print("\n" + "="*80)
    print(f"Progress: {coin_count}/1000 coins ({coin_count/1000*100:.1f}%)")
    print("="*80)

if __name__ == "__main__":
    check_progress()





