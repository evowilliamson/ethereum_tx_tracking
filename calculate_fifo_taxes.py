#!/usr/bin/env python3
"""
FIFO Capital Gains Tax Calculator
Calculates capital gains/losses using FIFO method for DEX trades
"""

import csv
import sys
from datetime import datetime
from collections import defaultdict
from decimal import Decimal, ROUND_DOWN


class Lot:
    """Represents a lot of tokens in inventory"""
    def __init__(self, trade_id, amount, cost_basis_usd, acquisition_date, token_symbol):
        self.trade_id = trade_id
        self.amount = Decimal(str(amount))
        self.cost_basis_usd = Decimal(str(cost_basis_usd))
        self.acquisition_date = acquisition_date
        self.token_symbol = token_symbol
        self.cost_per_token = self.cost_basis_usd / self.amount if self.amount > 0 else Decimal('0')


class FIFOTaxCalculator:
    """FIFO-based tax calculator for crypto trades"""
    
    def __init__(self):
        # Inventory: token_symbol -> list of Lot objects (FIFO order)
        self.inventory = defaultdict(list)
        # Track all trades with IDs
        self.all_trades = []
        self.next_trade_id = 1
    
    def add_lot(self, token_symbol, amount, cost_basis_usd, trade_id, acquisition_date):
        """Add a lot to inventory"""
        lot = Lot(trade_id, amount, cost_basis_usd, acquisition_date, token_symbol)
        self.inventory[token_symbol].append(lot)
    
    def match_sell_fifo(self, token_symbol, amount_to_sell, sale_price_per_token):
        """
        Match a sell against inventory using FIFO
        Returns: (total_cost_basis, matched_trade_ids)
        """
        if token_symbol not in self.inventory or len(self.inventory[token_symbol]) == 0:
            # No inventory - assume cost basis equals sale price (zero gain)
            total_cost = Decimal(str(amount_to_sell)) * Decimal(str(sale_price_per_token))
            return total_cost, []
        
        amount_remaining = Decimal(str(amount_to_sell))
        total_cost_basis = Decimal('0')
        matched_trade_ids = []
        
        lots = self.inventory[token_symbol]
        
        # Process lots in FIFO order (oldest first)
        while amount_remaining > 0 and lots:
            lot = lots[0]  # Oldest lot
            
            if lot.amount <= amount_remaining:
                # Consume entire lot
                total_cost_basis += lot.cost_basis_usd
                matched_trade_ids.append(lot.trade_id)
                amount_remaining -= lot.amount
                lots.pop(0)  # Remove consumed lot
            else:
                # Partially consume lot
                fraction = amount_remaining / lot.amount
                cost_from_lot = lot.cost_basis_usd * fraction
                total_cost_basis += cost_from_lot
                matched_trade_ids.append(lot.trade_id)
                
                # Update lot with remaining amount
                lot.amount -= amount_remaining
                lot.cost_basis_usd -= cost_from_lot
                amount_remaining = Decimal('0')
        
        # If we still have remaining amount, assume cost basis = sale price for that portion
        if amount_remaining > 0:
            remaining_cost = amount_remaining * Decimal(str(sale_price_per_token))
            total_cost_basis += remaining_cost
            # No trade ID for assumed purchases
        
        return total_cost_basis, matched_trade_ids
    
    def process_trades(self, trades_file):
        """Process trades from CSV and calculate taxes"""
        tax_records = []
        
        with open(trades_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            for row in reader:
                trade_id = self.next_trade_id
                self.next_trade_id += 1
                
                date_time = row['date_time']
                source_currency = row['source_currency']
                source_amount_str = row['source_amount']
                target_currency = row['target_currency']
                target_amount_str = row['target_amount']
                platform = row['platform']
                address = row['address']
                
                # Skip rows with N/A values
                if target_amount_str == 'N/A' or source_amount_str == 'N/A':
                    continue
                
                try:
                    source_amount = Decimal(str(source_amount_str))
                    target_amount = Decimal(str(target_amount_str))
                except (ValueError, TypeError) as e:
                    print(f"Warning: Could not parse amounts for trade {self.next_trade_id}: {e}")
                    continue
                
                # Parse date
                try:
                    trade_date = datetime.strptime(date_time, '%Y/%m/%d %H:%M:%S')
                except ValueError:
                    print(f"Warning: Could not parse date '{date_time}', skipping trade {trade_id}")
                    continue
                
                # Identify BUY vs SELL
                if target_currency == 'USD':
                    # SELL transaction: source_token -> USD
                    sale_proceeds = target_amount
                    token_sold = source_currency
                    amount_sold = source_amount
                    
                    if sale_proceeds > 0:
                        sale_price_per_token = sale_proceeds / amount_sold
                    else:
                        sale_price_per_token = Decimal('0')
                    
                    # Match against inventory using FIFO
                    cost_basis, buy_tx_ids = self.match_sell_fifo(
                        token_sold, amount_sold, sale_price_per_token
                    )
                    
                    profit = sale_proceeds - cost_basis
                    
                    # Create tax record
                    tax_record = {
                        'trade_id': trade_id,
                        'date_time': date_time,
                        'token_sold': token_sold,
                        'amount_sold': str(amount_sold.quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)),
                        'sale_proceeds_usd': str(sale_proceeds.quantize(Decimal('0.01'), rounding=ROUND_DOWN)),
                        'cost_basis_usd': str(cost_basis.quantize(Decimal('0.01'), rounding=ROUND_DOWN)),
                        'profit_usd': str(profit.quantize(Decimal('0.01'), rounding=ROUND_DOWN)),
                        'buy_tx_ids': ','.join(map(str, buy_tx_ids)) if buy_tx_ids else '',
                        'platform': platform,
                        'address': address,
                    }
                    tax_records.append(tax_record)
                    
                    # Store trade info
                    self.all_trades.append({
                        'trade_id': trade_id,
                        'type': 'SELL',
                        'token': token_sold,
                        'amount': amount_sold,
                        'usd_value': sale_proceeds,
                        'date': trade_date,
                    })
                
                elif source_currency == 'USD':
                    # BUY transaction: USD -> target_token
                    cost_basis = source_amount
                    token_bought = target_currency
                    amount_bought = target_amount
                    
                    # Add to inventory
                    self.add_lot(token_bought, amount_bought, cost_basis, trade_id, trade_date)
                    
                    # Store trade info
                    self.all_trades.append({
                        'trade_id': trade_id,
                        'type': 'BUY',
                        'token': token_bought,
                        'amount': amount_bought,
                        'usd_value': cost_basis,
                        'date': trade_date,
                    })
        
        return tax_records
    
    def export_tax_csv(self, tax_records, output_file):
        """Export tax records to CSV"""
        if not tax_records:
            print("No tax records to export")
            return
        
        fieldnames = [
            'trade_id', 'date_time', 'token_sold', 'amount_sold',
            'sale_proceeds_usd', 'cost_basis_usd', 'profit_usd',
            'buy_tx_ids', 'platform', 'address'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            
            # Sort by date (most recent first)
            sorted_records = sorted(tax_records, key=lambda x: x['date_time'], reverse=True)
            writer.writerows(sorted_records)
        
        print(f"✓ Exported {len(tax_records)} tax records to {output_file}")
        
        # Print summary
        total_profit = sum(Decimal(r['profit_usd']) for r in tax_records)
        total_sales = sum(Decimal(r['sale_proceeds_usd']) for r in tax_records)
        total_cost = sum(Decimal(r['cost_basis_usd']) for r in tax_records)
        
        print(f"\nTax Summary:")
        print(f"  Total sales: ${total_sales:,.2f}")
        print(f"  Total cost basis: ${total_cost:,.2f}")
        print(f"  Total capital gain/loss: ${total_profit:,.2f}")


def main():
    """Main function"""
    input_csv = "evm_trades.csv"
    output_csv = "tax_calculations.csv"
    
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]
    if len(sys.argv) > 2:
        output_csv = sys.argv[2]
    
    print("=" * 80)
    print("FIFO Capital Gains Tax Calculator")
    print("=" * 80)
    print(f"Input file: {input_csv}")
    print(f"Output file: {output_csv}")
    print("=" * 80)
    print()
    
    calculator = FIFOTaxCalculator()
    
    print("Processing trades...")
    tax_records = calculator.process_trades(input_csv)
    
    print(f"✓ Processed {len(tax_records)} sell transactions")
    print()
    
    print("Exporting tax calculations...")
    calculator.export_tax_csv(tax_records, output_csv)
    
    print()
    print("=" * 80)
    print("Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

