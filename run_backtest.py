import os
import datetime
import numpy as np
import pandas as pd
from backtesting import Backtest, Strategy

def _calc_fvg(highs, lows):
    bullish_top = np.full(len(highs), np.nan)
    bullish_bottom = np.full(len(highs), np.nan)
    bearish_top = np.full(len(highs), np.nan)
    bearish_bottom = np.full(len(highs), np.nan)
    active_bullish = None
    active_bearish = None
    for i in range(2, len(highs)):
        if lows[i] > highs[i-2]:
            active_bullish = (lows[i], highs[i-2])
            active_bearish = None 
        elif highs[i] < lows[i-2]:
            active_bearish = (lows[i-2], highs[i])
            active_bullish = None 

        if active_bullish:
            bullish_top[i] = active_bullish[0]
            bullish_bottom[i] = active_bullish[1]
            if lows[i] <= active_bullish[0]:
                active_bullish = None
        elif active_bearish:
            bearish_top[i] = active_bearish[0]
            bearish_bottom[i] = active_bearish[1]
            if highs[i] >= active_bearish[1]:
                active_bearish = None
    return bullish_top, bullish_bottom, bearish_top, bearish_bottom

def get_bullish_top(highs, lows): return _calc_fvg(highs, lows)[0]
def get_bullish_bot(highs, lows): return _calc_fvg(highs, lows)[1]
def get_bearish_top(highs, lows): return _calc_fvg(highs, lows)[2]
def get_bearish_bot(highs, lows): return _calc_fvg(highs, lows)[3]

class FvgStrategy(Strategy):
    def init(self):
        super().init()
        self.I(get_bullish_top, self.data.High, self.data.Low, name='Bullish FVG Top', overlay=True, color='green')
        self.I(get_bullish_bot, self.data.High, self.data.Low, name='Bullish FVG Bottom', overlay=True, color='green')
        self.I(get_bearish_bot, self.data.High, self.data.Low, name='Bearish FVG Bottom', overlay=True, color='red')
        self.I(get_bearish_top, self.data.High, self.data.Low, name='Bearish FVG Top', overlay=True, color='red')

    def next(self):
        if len(self.data) < 3:
            return

        high_1 = self.data.High[-3]
        low_1 = self.data.Low[-3]
        high_2 = self.data.High[-2]
        low_2 = self.data.Low[-2]
        high_3 = self.data.High[-1]
        low_3 = self.data.Low[-1]

        is_bullish_fvg = low_3 > high_1
        is_bearish_fvg = high_3 < low_1

        if self.position.is_long and is_bearish_fvg:
            self.position.close()
        elif self.position.is_short and is_bullish_fvg:
             self.position.close()

        if is_bullish_fvg or is_bearish_fvg:
            for order in self.orders:
                order.cancel()

            if is_bullish_fvg:
                entry = low_3       
                sl = low_2          
                risk = entry - sl
                if risk > 0 and not self.position.is_long:
                    tp = entry + (risk * 2)
                    self.buy(limit=entry, sl=sl, tp=tp)

            elif is_bearish_fvg:
                entry = high_3      
                sl = high_2         
                risk = sl - entry
                if risk > 0 and not self.position.is_short:
                    tp = entry - (risk * 2)
                    self.sell(limit=entry, sl=sl, tp=tp)

def load_and_format_data(csv_path, timeframe='1h'):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"找不到檔案: {csv_path}")
    
    df = pd.read_csv(csv_path)
    rename_map = {
        'date': 'Date', 'open': 'Open', 'high': 'High',
        'low': 'Low', 'close': 'Close', 'volume': 'Volume'
    }
    df.rename(columns=lambda x: rename_map.get(x.lower(), x.capitalize()), inplace=True)
    
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"缺少必要欄位: {col}")
            
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df.set_index('Date', inplace=True)
    elif 'Datetime' in df.columns:
        df.set_index('Datetime', inplace=True)
        df.index = pd.to_datetime(df.index, utc=True)
        
    df.sort_index(inplace=True)
    df = df[~df.index.duplicated(keep='last')]
    
    # 自動升頻降頻 (Resample) 來模擬 2h, 4h K線
    if timeframe and timeframe != '1h':
        # pandas resample 支援 'h', 'min', 'd'
        tf_map = {'2h': '2h', '4h': '4h', '1d': '1d'}
        tf = tf_map.get(timeframe, timeframe)
        df = df.resample(tf).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        })
        df.dropna(inplace=True)
    return df

def run_backtest_pipeline(csv_path, strategy_class, timeframe='1h'):
    print(f"載入資料: {csv_path} (目標週期化: {timeframe})")
    df = load_and_format_data(csv_path, timeframe)
    
    if len(df) < 50:
        print("資料筆數過少，略過此週期的測試...")
        return None
        
    print("\n--- 開始執行回測 ---")
    bt = Backtest(df, strategy_class, cash=100000, commission=0.002, exclusive_orders=True)
    stats = bt.run()
    
    print("\n=== 回測核心績效 ===")
    print(f"Sharpe Ratio:  {stats.get('Sharpe Ratio', 'N/A'):.4f}")
    print(f"Max Drawdown:  {stats.get('Max. Drawdown [%]', 'N/A'):.2f} %")
    print(f"Net Profit:    {stats.get('Return [%]', 'N/A'):.2f} %")
    print("===================\n")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, "backtest_reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    file_name = os.path.basename(csv_path)
    product_symbol = file_name.replace("_1hour_historical.csv", "").replace("_historical.csv", "").replace(".csv", "")
    
    product_info = f"{product_symbol}_{timeframe}"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    strategy_name = strategy_class.__name__
    
    run_dir = os.path.join(reports_dir, f"{strategy_name}_{product_info}_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    
    summary_path = os.path.join(run_dir, f"summary_{product_info}.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(str(stats))
        
    trades_path = os.path.join(run_dir, f"trades_{product_info}.csv")
    if '_trades' in stats and not stats['_trades'].empty:
        stats['_trades'].to_csv(trades_path, index=False)
        
    html_path = os.path.join(run_dir, f"chart_{product_info}.html")
    try:
        bt.plot(filename=html_path, open_browser=False, resample=False, superimpose=False)
    except Exception as e:
        print(f"圖表生成失敗: {e}")
        
    print(f">>> 完整報告已自動整理並儲存至資料夾: {run_dir}")
    return stats

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 設定批次回測陣列：(子資料夾, 檔名, 欲轉換的時區列表)
    batch_tasks = [
        ("CL", "CL_1hour_historical.csv", ["2h", "4h"]),
        ("GC", "GC_1hour_historical.csv", ["1h", "2h", "4h"]),
        ("SI", "SI_1hour_historical.csv",   ["1h", "2h", "4h"]),
        ("NQ", "NQ_202606_1hour_historical.csv", ["1h", "2h", "4h"])
    ]
    
    for folder, filename, timeframes in batch_tasks:
        csv_path = os.path.join(base_dir, folder, filename)
        if not os.path.exists(csv_path):
            print(f"\n[跳過] 尚未找到歷史資料: {csv_path}")
            continue
            
        for tf in timeframes:
            print(f"\n=======================================================")
            print(f"🔥 開始處理產品: {folder} | 目標時區: {tf}")
            print(f"=======================================================")
            try:
                run_backtest_pipeline(csv_path, FvgStrategy, timeframe=tf)
            except Exception as e:
                print(f"[{folder} {tf}] 發生錯誤而終止: {e}")
