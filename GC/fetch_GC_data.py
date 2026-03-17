import asyncio

# Fix for Python 3.10+: ib_insync requires an event loop at import time
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import pandas as pd
import time
from ib_insync import *

def fetch_massive_historical_data(symbol, total_months, bar_size):
    """
    自動抓取 IBKR 期貨歷史數據並儲存為 CSV

    :param symbol:       期貨代碼 ('GC' = Gold)
    :param total_months: 總共想要回溯抓取的月數
    :param bar_size:     K線時間框架 (如 '1 hour')
    """
    # 1. 建立連線
    ib = IB()
    try:
        ib.connect('127.0.0.1', 7497, clientId=13)
        print("成功連接到 IBKR TWS/Gateway!")
    except Exception as e:
        print(f"連線失敗，請檢查 TWS 是否開啟並允許 API 連線。錯誤訊息: {e}")
        return

    # 2. 使用連續合約 (ContFuture) — 自動處理換月，無需指定到期日
    # GC = Gold Futures on COMEX
    contract = ContFuture(symbol, exchange='COMEX', currency='USD')
    ib.qualifyContracts(contract)
    print(f"合約資訊: {contract}")

    print(f"開始抓取 {symbol} 的 {bar_size} K線數據，目標：回溯 {total_months} 個月...")

    # 3. 單次請求全部月份（ContFuture 只能 endDateTime=''）
    bars = ib.reqHistoricalData(
        contract,
        endDateTime='',
        durationStr=f'{total_months} M',
        barSizeSetting=bar_size,
        whatToShow='TRADES',
        useRTH=False,
        formatDate=1
    )
    time.sleep(2)

    # 4. 斷開連線
    ib.disconnect()
    print("數據抓取完畢，已斷開連線。")

    # 5. 數據清洗與儲存
    if bars:
        df = util.df(bars)
        df.drop_duplicates(subset=['date'], inplace=True)
        df.sort_values(by='date', inplace=True)
        df.reset_index(drop=True, inplace=True)

        print("\n數據預覽:")
        print(df.head())
        print(f"\n總共獲取 {len(df)} 筆 K 線數據。")

        filename = f"{symbol}_{bar_size.replace(' ', '')}_historical.csv"
        df.to_csv(filename, index=False)
        print(f"資料已成功儲存至 {filename}，可以準備丟入機器學習模型了！")
    else:
        print("沒有獲取到任何數據。")


# 執行腳本：抓取 GC (黃金期貨) 過去 6 個月的 1小時 K線
if __name__ == '__main__':
    fetch_massive_historical_data(symbol='GC', total_months=6, bar_size='1 hour')
