import asyncio

# Fix for Python 3.10+: ib_insync requires an event loop at import time
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import pandas as pd
import time
from ib_insync import *

def fetch_massive_historical_data(symbol, expiry, total_months, bar_size):
    """
    自動抓取 IBKR 期貨歷史數據並儲存為 CSV

    :param symbol:       期貨代碼 (如 'NQ', 'CL', 'GC')
    :param expiry:       到期年月，格式 'YYYYMM' (如 '202606' 代表 JUN 2026)
    :param total_months: 總共想要回溯抓取的月數
    :param bar_size:     K線時間框架 (如 '1 hour', '15 mins')
    """
    # 1. 建立連線
    ib = IB()
    try:
        ib.connect('127.0.0.1', 7497, clientId=11)
        print("成功連接到 IBKR TWS/Gateway!")
    except Exception as e:
        print(f"連線失敗，請檢查 TWS 是否開啟並允許 API 連線。錯誤訊息: {e}")
        return

    # 2. 指定特定合約月份 (NQ JUN 2026)
    contract = Future(
        symbol=symbol,
        lastTradeDateOrContractMonth=expiry,
        exchange='CME',
        currency='USD'
    )
    ib.qualifyContracts(contract)
    print(f"合約資訊: {contract}")

    print(f"開始抓取 {symbol} {expiry} 的 {bar_size} K線數據，目標：回溯 {total_months} 個月...")

    end_date = ''   # 從最新時間開始往回
    all_bars = []

    # 3. 分批抓取 (每批 1 個月，往過去推進)
    for i in range(total_months):
        print(f"正在抓取第 {i+1} 批數據 (截至 {end_date if end_date else '最新'})...")

        bars = ib.reqHistoricalData(
            contract,
            endDateTime=end_date,
            durationStr='1 M',
            barSizeSetting=bar_size,
            whatToShow='TRADES',
            useRTH=False,       # 包含電子盤 (期貨建議設 False)
            formatDate=1
        )

        if not bars:
            print("警告：此區間無數據返回，可能已到達可獲取的最早時間。")
            break

        all_bars.extend(bars)
        end_date = bars[0].date     # 下一批的結束時間 = 這批最早的時間
        time.sleep(2)               # 防止 pacing violation

    # 4. 斷開連線
    ib.disconnect()
    print("數據抓取完畢，已斷開連線。")

    # 5. 數據清洗與儲存
    if all_bars:
        df = util.df(all_bars)
        df.drop_duplicates(subset=['date'], inplace=True)
        df.sort_values(by='date', inplace=True)
        df.reset_index(drop=True, inplace=True)

        print("\n數據預覽:")
        print(df.head())
        print(f"\n總共獲取 {len(df)} 筆 K 線數據。")

        filename = f"{symbol}_{expiry}_{bar_size.replace(' ', '')}_historical.csv"
        df.to_csv(filename, index=False)
        print(f"資料已成功儲存至 {filename}，可以準備丟入機器學習模型了！")
    else:
        print("沒有獲取到任何數據。")


# 執行腳本：抓取 NQ JUN 2026 過去 6 個月的 1小時 K線
if __name__ == '__main__':
    fetch_massive_historical_data(
        symbol='NQ',
        expiry='202606',      # JUN 2026
        total_months=6,
        bar_size='1 hour'
    )
