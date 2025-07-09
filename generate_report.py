# generate_report.py
import os
import glob
import json
import pandas as pd
from datetime import datetime
import ccxt
import my_key

# --- 설정 ---
HISTORY_PATH = 'history'
OUTPUT_HTML_FILE = 'index.html'
YOUR_BOT_NAME = 'Dynamic Grid Bot'

def load_trade_history():
    """history 폴더의 모든 json 거래 기록을 읽어 하나의 데이터프레임으로 합칩니다."""
    all_trades = []
    json_files = glob.glob(os.path.join(HISTORY_PATH, '*.json'))
    
    for file_path in sorted(json_files, reverse=True):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                trades = json.load(f)
                all_trades.extend(trades)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    if not all_trades:
        return pd.DataFrame()

    df = pd.DataFrame(all_trades)
    # 타임스탬프를 datetime 객체로 변환
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values(by='timestamp', ascending=False).reset_index(drop=True)
    return df

def get_live_status():
    """거래소 API에 직접 연결하여 실시간 현황을 가져옵니다."""
    print("Connecting to Binance for live status...")
    try:
        exchange = ccxt.binance({
            'apiKey': my_key.binance_api_key,
            'secret': my_key.binance_secret_key,
            'options': {'defaultType': 'future'}
        })
        
        balance = exchange.fetch_balance(params={"type": "future"})
        
        usdt_balance = balance['total']['USDT']
        positions = [p for p in balance['info']['positions'] if float(p['positionAmt']) != 0]
        
        live_data = {
            'total_equity': float(balance['info']['totalWalletBalance']) + float(balance['info']['totalUnrealizedProfit']),
            'usdt_balance': usdt_balance,
            'positions': positions
        }
        print("Live status fetched successfully.")
        return live_data
    except Exception as e:
        print(f"Error fetching live status: {e}")
        return None

def generate_html_report(history_df, live_status):
    """데이터를 바탕으로 최종 HTML 리포트를 생성합니다."""
    
    # 마지막 업데이트 시간
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 라이브 현황 HTML 생성
    status_html = "<h3>데이터 조회 실패</h3>"
    if live_status:
        positions_html = ""
        unrealized_pnl = 0
        for p in live_status['positions']:
            pnl = float(p['unrealizedProfit'])
            unrealized_pnl += pnl
            pnl_class = "text-green" if pnl > 0 else "text-red" if pnl < 0 else ""
            positions_html += f"""
                <tr>
                    <td>{p['symbol']}</td>
                    <td>{p['positionSide']}</td>
                    <td>{float(p['positionAmt']):.4f}</td>
                    <td>${float(p['entryPrice']):,.2f}</td>
                    <td>${float(p['markPrice']):,.2f}</td>
                    <td class="{pnl_class}">${pnl:,.2f}</td>
                </tr>
            """
        
        equity_class = "text-green" if unrealized_pnl > 0 else "text-red" if unrealized_pnl < 0 else ""
        
        status_html = f"""
            <div class="status-grid">
                <div><span>총 평가 자산 (Equity)</span><strong class="{equity_class}">${live_status['total_equity']:,.2f}</strong></div>
                <div><span>USDT 잔고</span><strong>${live_status['usdt_balance']:,.2f}</strong></div>
                <div><span>미실현 손익 (Unrealized PNL)</span><strong class="{equity_class}">${unrealized_pnl:,.2f}</strong></div>
            </div>
            <h4>현재 포지션</h4>
            <table class="styled-table">
                <thead><tr><th>Symbol</th><th>Side</th><th>Amount</th><th>Entry Price</th><th>Mark Price</th><th>Unrealized PNL</th></tr></thead>
                <tbody>{positions_html if positions_html else "<tr><td colspan='6'>현재 활성 포지션이 없습니다.</td></tr>"}</tbody>
            </table>
        """

    # 거래 내역 HTML 생성
    history_html = "<h3>거래 내역이 없습니다.</h3>"
    if not history_df.empty:
        # 보기 좋게 컬럼 순서 및 이름 변경
        df_display = history_df[['timestamp', 'action', 'side', 'price', 'amount']].copy()
        df_display.columns = ['시간', '작업', '포지션', '가격', '수량']
        df_display['시간'] = df_display['시간'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_display['가격'] = df_display['가격'].apply(lambda x: f"${x:,.2f}")
        df_display['수량'] = df_display['수량'].apply(lambda x: f"{x:.4f}")
        history_html = df_display.to_html(classes='styled-table history-table', index=False, escape=False)

    # 최종 HTML 템플릿
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{YOUR_BOT_NAME} 상태 대시보드</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: auto; background-color: #1e1e1e; padding: 20px; border-radius: 8px; box-shadow: 0 0 20px rgba(0,0,0,0.5); }}
            h1, h2, h4 {{ color: #ffffff; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; }}
            .header span {{ font-size: 0.9em; color: #888; }}
            .status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .status-grid div {{ background-color: #2a2a2a; padding: 20px; border-radius: 5px; text-align: center; }}
            .status-grid span {{ display: block; margin-bottom: 10px; color: #aaa; }}
            .status-grid strong {{ font-size: 1.8em; color: #fff; }}
            .text-green {{ color: #4caf50 !important; }}
            .text-red {{ color: #f44336 !important; }}
            .styled-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .styled-table th, .styled-table td {{ padding: 12px 15px; border: 1px solid #333; text-align: center; }}
            .styled-table thead tr {{ background-color: #007bff; color: #ffffff; }}
            .styled-table tbody tr:nth-of-type(even) {{ background-color: #2a2a2a; }}
            .styled-table tbody tr:hover {{ background-color: #3a3a3a; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📈 {YOUR_BOT_NAME} 대시보드</h1>
                <span>Last Updated: {last_updated}</span>
            </div>

            <h2>실시간 현황</h2>
            {status_html}

            <h2>거래 기록</h2>
            {history_html}
        </div>
    </body>
    </html>
    """
    return html_template

def main():
    """메인 실행 함수"""
    print("Generating trading report...")
    
    history_df = load_trade_history()
    live_status = get_live_status()
    
    html_content = generate_html_report(history_df, live_status)
    
    with open(OUTPUT_HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Report '{OUTPUT_HTML_FILE}' generated successfully. You can open this file in your browser.")

if __name__ == "__main__":
    main()