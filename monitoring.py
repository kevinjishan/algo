# monitoring.py
import logging
from line_alert import SendMessage
from utils import cumulative_funding, handle_exception
import myBinance as mb
from config import CONFIG

def send_daily_pnl(exchange_handler):
    """일일 PnL 보고서를 전송합니다."""
    try:
        total_pnl = 0
        message = "[일일 PnL 보고]\n"
        
        for ticker in CONFIG['SYMBOLS']:
            long_value = mb.GetCoinRealMoney(exchange_handler.fetch_balance(), ticker, 'LONG')
            short_value = mb.GetCoinRealMoney(exchange_handler.fetch_balance(), ticker, 'SHORT')
            ticker_pnl = long_value + short_value - cumulative_funding.get(ticker, 0)
            total_pnl += ticker_pnl
            message += f"- {ticker}: {ticker_pnl:.2f} USDT\n"

        message += f"💰 총 PnL: {total_pnl:.2f} USDT"
        SendMessage(message)
        logging.info("Daily PnL report sent.")
    except Exception as e:
        handle_exception("System", "Daily PnL report", e, "daily_pnl_error")

def send_status_report(exchange_handler):
    """주기적인 상태 보고서를 전송합니다."""
    try:
        logging.info("6시간 상태 보고 시작")
        report = ""
        for ticker in CONFIG['SYMBOLS']:
            current_price = mb.GetCoinNowPrice(exchange_handler.exchange, ticker)
            long_value = mb.GetCoinRealMoney(exchange_handler.fetch_balance(), ticker, 'LONG')
            short_value = mb.GetCoinRealMoney(exchange_handler.fetch_balance(), ticker, 'SHORT')
            orders = exchange_handler.fetch_open_orders(ticker)
            funding_rate = exchange_handler.exchange.fetch_funding_rate(ticker)['fundingRate']
            
            report += f"""
📊 {ticker} 상태 보고
- 현재가: ${current_price:.2f}
- 롱 포지션: ${long_value:.2f}
- 숏 포지션: ${short_value:.2f}
- 활성 주문: {len(orders)}개
- 펀딩비: {funding_rate*100:.4f}%
"""
        SendMessage(report)
        logging.info("6시간 상태 보고 완료")
    except Exception as e:
        logging.error(f"Error sending status report: {e}")

def clean_old_logs():
    """오래된 로그 파일을 삭제합니다."""
    # 이 함수는 다른 모듈 의존성이 없으므로 그대로 사용 가능
    # ... (원래 코드의 clean_old_logs 함수 내용) ...
    pass