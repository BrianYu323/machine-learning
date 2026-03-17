import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import xgboost as xgb

def main():
    file_path = "FVG_+_MA__CME_MINI_NQ1!_2026-03-13_9ab2d.xlsx"
    
    if not os.path.exists(file_path):
        print(f"Error: Could not find the file '{file_path}' in the current directory.")
        return

    # 1. Load data
    print("Loading data...")
    df = pd.read_excel(file_path, sheet_name='交易清單')

    # 2. Data Cleaning & Feature Engineering
    print("Cleaning data and engineering features...")
    # Filter for '進場' (Entry) in '類型' (Type)
    if '類型' in df.columns:
        df = df[df['類型'].astype(str).str.contains("進場", na=False)].copy()
    else:
        print("Warning: Column '類型' not found. Skipping filtering.")

    # Convert '日期和時間' to datetime and extract Hour and Day of Week
    if '日期和時間' in df.columns:
        df['日期和時間'] = pd.to_datetime(df['日期和時間'])
        df['Hour'] = df['日期和時間'].dt.hour
        df['Day of Week'] = df['日期和時間'].dt.dayofweek
    else:
        print("Error: Column '日期和時間' not found.")
        return

    # Define Target: Net Profit (淨損益 USD) > 0 -> 1 (Win), else 0 (Loss)
    if '淨損益 USD' in df.columns:
        # Some CSVs may have strings with currency symbols or commas
        if df['淨損益 USD'].dtype == object:
            df['淨損益 USD'] = df['淨損益 USD'].astype(str).str.replace(',', '').str.replace('$', '').astype(float)
        df['Target'] = (df['淨損益 USD'] > 0).astype(int)
    else:
        print("Error: Column '淨損益 USD' not found.")
        return

    # Check if we have enough data
    if len(df) == 0:
        print("Error: No data left after filtering for '進場'.")
        return

    # 3. Exploratory Data Analysis (EDA)
    print("Performing EDA...")
    # Calculate Win Rate and Total Profit by Hour
    hourly_stats = df.groupby('Hour').agg(
        Total_Trades=('Target', 'count'),
        Wins=('Target', 'sum'),
        Total_Profit=('淨損益 USD', 'sum')
    ).reset_index()
    
    hourly_stats['Win_Rate'] = hourly_stats['Wins'] / hourly_stats['Total_Trades']

    # Plot Win Rate and Total Profit by Hour
    sns.set_theme(style="whitegrid")
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Bar chart for Win Rate
    color1 = 'tab:blue'
    ax1.set_xlabel('Hour of Day')
    ax1.set_ylabel('Win Rate', color=color1)
    sns.barplot(data=hourly_stats, x='Hour', y='Win_Rate', ax=ax1, color=color1, alpha=0.6)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_ylim(0, 1) # Win rate is between 0 and 1

    # Line chart for Total Profit on secondary y-axis
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('Total Profit (USD)', color=color2)
    sns.lineplot(data=hourly_stats, x='Hour', y='Total_Profit', ax=ax2, color=color2, marker='o', linewidth=2)
    ax2.tick_params(axis='y', labelcolor=color2)

    plt.title('Win Rate and Total Profit by Entry Hour')
    plt.tight_layout()
    plt.savefig('hour_performance.png')
    print("Saved EDA chart to 'hour_performance.png'")

    # 4. Machine Learning (XGBoost)
    print("Training XGBoost Model...")
    features = ['Hour', 'Day of Week']
    X = df[features]
    y = df['Target']

    if len(df['Target'].unique()) < 2:
         print("Warning: Target only has one class. Cannot train a meaningful model.")
         return

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Initialize and train XGBoost
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    model.fit(X_train, y_train)

    # Predict and evaluate
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred)
    
    print("\n--- Classification Report ---")
    print(report)

    # Feature Importance
    importances = model.feature_importances_
    print("\n--- Feature Importance ---")
    for feature, imp in zip(features, importances):
        print(f"{feature}: {imp:.4f}")

    # Best Trading Time Recommendation
    best_hour_profit = hourly_stats.loc[hourly_stats['Total_Profit'].idxmax(), 'Hour']
    best_hour_winrate = hourly_stats.loc[hourly_stats['Win_Rate'].idxmax(), 'Hour']
    print(f"\n--- Recommendations ---")
    print(f"Most profitable trading hour: {best_hour_profit}:00")
    print(f"Hour with highest win rate: {best_hour_winrate}:00")

    print("\nAnalysis complete! Please review the output to update the Markdown report.")

if __name__ == "__main__":
    main()
