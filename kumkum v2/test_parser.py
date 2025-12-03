# -*- coding: utf-8 -*-
import sys
from html_to_excel import (
    parse_html_transactions,
    create_daily_summary,
    create_detailed_transactions_df,
    create_items_summary_df
)

def test_parser():
    print("=" * 50)
    print("Testing HTML Parser")
    print("=" * 50)
    
    # Load example HTML
    try:
        with open('example_report.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        print("OK - HTML file loaded successfully")
    except FileNotFoundError:
        print("ERROR - example_report.html not found")
        return False
    except Exception as e:
        print(f"ERROR - reading file: {e}")
        return False
    
    # Parse transactions
    try:
        transactions = parse_html_transactions(html_content)
        print(f"OK - Found {len(transactions)} transactions")
        
        if len(transactions) == 0:
            print("WARNING - No transactions found")
            return False
    except Exception as e:
        print(f"ERROR - processing: {e}")
        return False
    
    # Create summaries
    try:
        daily_df = create_daily_summary(transactions)
        total_sales = daily_df['total_sales'].sum()
        avg_sales = daily_df['total_sales'].mean()
        print(f"OK - Daily report {len(daily_df)} days")
        print(f"   Total sales: {total_sales:.2f}")
        print(f"   Average: {avg_sales:.2f}")
    except Exception as e:
        print(f"ERROR - daily report: {e}")
        return False
    
    try:
        trans_df = create_detailed_transactions_df(transactions)
        print(f"OK - Transaction list {len(trans_df)} rows")
    except Exception as e:
        print(f"ERROR - transaction list: {e}")
        return False
    
    try:
        items_df = create_items_summary_df(transactions)
        print(f"OK - Item summary {len(items_df)} products")
        if len(items_df) > 0:
            top = items_df.iloc[0]
            print(f"   Top: {top['item_name']} ({top['total_amount']:.2f})")
    except Exception as e:
        print(f"ERROR - item summary: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("SUCCESS - All tests passed!")
    print("=" * 50)
    print("\nReady to run:")
    print("  streamlit run app.py")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = test_parser()
    sys.exit(0 if success else 1)
