# main.py
import logging
from logging.handlers import RotatingFileHandler
import os
import time
import schedule
import pytz
from datetime import datetime

# --- 모듈 임포트 ---
from config import CONFIG
import utils
from exchange_handler import ExchangeHandler
import risk_manager
import strategy_logic
import monitoring
import myBinance as mb

# --- 로깅 및 디렉토리 설정 ---
os.makedirs(CONFIG['LOG_DIR'], exist_ok=True)
os.makedirs(CONFIG['HISTORY_DIR'], exist_ok=True)

log_handler = RotatingFileHandler(
    CONFIG['LOG_FILE'], maxBytes=CONFIG['LOG_MAX_BYTES'], backupCount=CONFIG['LOG_BACKUP_COUNT']
)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[log_handler, logging.StreamHandler()] # 파일 및 콘솔 출력
)

def process_ticker(exchange_handler, ticker):
    """단일 심볼에 대한 트레이딩 로직을 처리합니다."""
    try:
        logging.info(f"--- Processing {ticker} ---")
        
        # 데이터 가져오기 및 기본 지표 계산
        current_price = mb.GetCoinNowPrice(exchange_handler.exchange, ticker)
        if current_price <= 0:
            logging.warning(f"Invalid price for {ticker}: {current_price}")
            return

        df = mb.GetOhlcv(exchange_handler.exchange, ticker, '1m', 100)
        if df.empty or len(df) < CONFIG['MA_PERIOD']:
            logging.warning(f"Insufficient data for {ticker}")
            return
            
        ma = mb.GetMA(df, CONFIG['MA_PERIOD'], -1)
        rsi = mb.GetRSI(df, CONFIG['RSI_PERIOD'], -1)
        atr = strategy_logic.calculate_atr(df)

        # 포지션 및 주문 정보
        balance = exchange_handler.fetch_balance()
        long_amt = exchange_handler.get_position_amount(balance, ticker, 'LONG')
        short_amt = exchange_handler.get_position_amount(balance, ticker, 'SHORT')
        long_value = mb.GetCoinRealMoney(balance, ticker, 'LONG')
        short_value = mb.GetCoinRealMoney(balance, ticker, 'SHORT')
        existing_orders = exchange_handler.fetch_open_orders(ticker)
        
        logging.info(f"{ticker} - Price: ${current_price:.2f}, MA: ${ma:.2f}, RSI: {rsi:.1f}, Long: {long_amt:.4f}, Short: {short_amt:.4f}")

        # --- 리스크 관리 (선행) ---
        # 최대 노출 제한 체크 등
        
        # --- 전략 로직 실행 ---
        # 진입/청산 조건 확인
        entry_signal = strategy_logic.check_entry_conditions(exchange_handler, ticker, df, current_price, ma, rsi)
        # exit_signal, _ = strategy_logic.check_exit_conditions(...)
        
        # 그리드 조정
        grid_interval = strategy_logic.calculate_dynamic_grid_interval(ticker, current_price, atr, existing_orders)
        amount = risk_manager.calculate_position_size(exchange_handler, ticker, current_price)
        
        if len(existing_orders) < CONFIG['MAX_STEPS'] * 2:
            strategy_logic.progressive_grid_adjustment(exchange_handler, ticker, current_price, existing_orders, grid_interval, amount)

        # ... (기타 모든 process_ticker 내 로직을 여기에 모듈화된 함수 호출로 변경) ...

        # 동적 비율 조정
        risk_manager.adjust_dynamic_ratio(exchange_handler, ticker, long_value, short_value, current_price)


    except Exception as e:
        utils.handle_exception(ticker, "Processing ticker", e, "ticker_error")


def main():
    """메인 트레이딩 루프"""
    logging.info("=== Dynamic Grid Trading Bot Start ===")
    
    # 초기화
    utils.clear_all_cache()
    exchange = ExchangeHandler()
    exchange.ensure_hedge_mode()
    
    for ticker in CONFIG['SYMBOLS']:
        exchange.set_leverage(ticker, CONFIG['LEVERAGE'])
        # strategy_logic.startup_grid_optimization(exchange, ticker) # 시작 시 그리드 최적화
    
    # 스케줄 설정
    schedule.every().day.at("00:00", "Asia/Seoul").do(monitoring.send_daily_pnl, exchange_handler=exchange)
    schedule.every(6).hours.do(monitoring.send_status_report, exchange_handler=exchange)
    logging.info("Scheduled tasks are set.")

    while True:
        try:
            schedule.run_pending()
            
            for ticker in CONFIG['SYMBOLS']:
                process_ticker(exchange, ticker)
                time.sleep(1) # API 레이트 리밋 방지
            
            logging.info(f"Main loop finished. Waiting for {CONFIG['SLEEP_TIME']} seconds...")
            time.sleep(CONFIG['SLEEP_TIME'])
            
        except KeyboardInterrupt:
            logging.info("Bot stopped by user.")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            time.sleep(60)

if __name__ == "__main__":
    main()