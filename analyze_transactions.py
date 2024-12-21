import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import argparse

def load_transactions(filename: str) -> pd.DataFrame:
    """Load transaction data from JSON file and convert to DataFrame"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Convert time strings to datetime
        df['OCCTIME'] = pd.to_datetime(df['OCCTIME'])
        
        # Clean up merchant names (remove trailing spaces)
        df['MERCNAME'] = df['MERCNAME'].str.strip()
        
        # Convert amount to numeric
        df['TRANAMT'] = pd.to_numeric(df['TRANAMT'])
        
        # Filter out positive transactions (deposits/refunds)
        df = df[df['TRANAMT'] < 0]
        print(f"Filtered out {len(data) - len(df)} positive transactions")
        
        return df
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found!")
        return None
    except json.JSONDecodeError:
        print(f"Error: File '{filename}' is not a valid JSON file!")
        return None
    except Exception as e:
        print(f"Error loading file: {str(e)}")
        return None

def find_latest_transaction_file() -> str:
    """Find the most recent transaction JSON file in the current directory"""
    json_files = [f for f in os.listdir() if f.startswith('card_transactions_') and f.endswith('.json')]
    return max(json_files) if json_files else None

def create_visualizations(df: pd.DataFrame, output_dir: str):
    """Create various visualizations from the transaction data"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Set font for Chinese characters
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 1. Daily spending pattern
    plt.figure(figsize=(12, 6))
    daily_spending = df.groupby(df['OCCTIME'].dt.date)['TRANAMT'].sum().abs()
    daily_spending.plot(kind='line', marker='o')
    plt.title('Daily Spending Pattern')
    plt.xlabel('Date')
    plt.ylabel('Amount (CNY)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'daily_spending.png'))
    plt.close()
    
    # 2. Spending by merchant (top 10)
    plt.figure(figsize=(12, 6))
    merchant_spending = df.groupby('MERCNAME')['TRANAMT'].sum().abs()  # Always show positive
    merchant_spending.nlargest(10).plot(kind='bar')
    plt.title('Top 10 Merchants by Spending')
    plt.xlabel('Merchant')
    plt.ylabel('Total Amount (CNY)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'merchant_spending.png'))
    plt.close()
    
    # 3. Hourly spending pattern
    plt.figure(figsize=(10, 6))
    hourly_spending = df.groupby(df['OCCTIME'].dt.hour)['TRANAMT'].sum().abs()
    hourly_spending.plot(kind='bar')
    plt.title('Spending by Hour of Day')
    plt.xlabel('Hour')
    plt.ylabel('Total Amount (CNY)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'hourly_spending.png'))
    plt.close()
    
    # 4. Spending heatmap by day and hour
    plt.figure(figsize=(12, 8))
    heatmap_data = df.pivot_table(
        values='TRANAMT',
        index=df['OCCTIME'].dt.day_name(),
        columns=df['OCCTIME'].dt.hour,
        aggfunc=lambda x: abs(sum(x))  # Always show positive values
    )
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(day_order)
    
    sns.heatmap(heatmap_data, cmap='YlOrRd', annot=True, fmt='.0f')
    plt.title('Spending Heatmap by Day and Hour')
    plt.xlabel('Hour of Day')
    plt.ylabel('Day of Week')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'spending_heatmap.png'))
    plt.close()

def generate_summary(df: pd.DataFrame) -> str:
    """Generate a text summary of the transaction data"""
    summary = []
    summary.append("Transaction Analysis Summary")
    summary.append("=" * 30)
    
    # Date range
    date_range = df['OCCTIME'].agg(['min', 'max'])
    summary.append(f"\nDate Range: {date_range['min'].date()} to {date_range['max'].date()}")
    
    # Total spending
    total_spent = abs(df['TRANAMT'].sum())  # Always show positive
    summary.append(f"Total Amount Spent: {total_spent:.2f} CNY")
    
    # Average daily spending
    days = (date_range['max'] - date_range['min']).days + 1
    summary.append(f"Average Daily Spending: {total_spent/days:.2f} CNY")
    
    # Transaction count
    summary.append(f"Total Transactions: {len(df)}")
    
    # Most common merchants
    top_merchants = df.groupby('MERCNAME').agg({
        'TRANAMT': [
            ('total_spent', lambda x: abs(sum(x))),
            ('transaction_count', 'count')
        ],
        'CARDBAL': ('last', 'last')
    }).droplevel(0, axis=1)
    
    # Sort by total spent in descending order
    top_merchants = top_merchants.sort_values('total_spent', ascending=False)
    
    summary.append("\nTop 5 Merchants by Spending:")
    for merchant, data in top_merchants.head(5).iterrows():
        avg_transaction = data['total_spent'] / data['transaction_count']
        summary.append(
            f"- {merchant}: {data['total_spent']:.2f} CNY "
            f"({int(data['transaction_count'])} transactions, "
            f"avg {avg_transaction:.2f} CNY/transaction)"
        )
    
    # Busiest times
    busy_hours = df.groupby(df['OCCTIME'].dt.hour)['TRANAMT'].agg(lambda x: abs(sum(x)))
    peak_hour = busy_hours.idxmax()
    peak_hour_spending = busy_hours[peak_hour]
    summary.append(f"\nPeak Spending Hour: {peak_hour:02d}:00 (Total: {peak_hour_spending:.2f} CNY)")
    
    return "\n".join(summary)

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Analyze PKU card transaction data')
    parser.add_argument('file', nargs='?', help='Path to the transaction JSON file')
    parser.add_argument('-o', '--output', default='transaction_analysis',
                        help='Output directory for analysis results (default: transaction_analysis)')
    args = parser.parse_args()

    # Determine which file to analyze
    if args.file:
        input_file = args.file
        print(f"Using specified file: {input_file}")
    else:
        input_file = find_latest_transaction_file()
        if not input_file:
            print("Error: No transaction files found and no file specified!")
            parser.print_help()
            return
        print(f"Using most recent file: {input_file}")
    
    # Load and process the data
    df = load_transactions(input_file)
    if df is None:
        return
    
    # Create output directory
    output_dir = args.output
    
    # Generate visualizations
    create_visualizations(df, output_dir)
    
    # Generate and save summary
    summary = generate_summary(df)
    with open(os.path.join(output_dir, 'summary.txt'), 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\nAnalysis complete! Results saved in '{output_dir}' directory")
    print("\nSummary:")
    print(summary)

if __name__ == "__main__":
    main() 