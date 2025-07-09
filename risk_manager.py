# risk_manager.py
import logging
import time
from config import CONFIG
from utils import get_cached_data, log_debug_as_info
import myBinance as mb

def calculate_position_size(exchange_handler, ticker, current_price):
    """자본 대비 포지션 크기를 계산합니다."""
    try:
        balance = exchange_handler.fetch_balance()
        total_balance = balance['total']['USDT']
        position_usdt = total_balance * CONFIG['POSITION_SIZE']

        # 동적 최소 주문 금액 (변동성 기반)
        leverage = CONFIG['LEVERAGE']
        min_order_usdt = max(25, current_price * 0.001 * leverage)
        if position_usdt < min_order_usdt:
            position_usdt = min_order_usdt

        amount = position_usdt / current_price
        logging.info(f"{ticker} - Position calculation: balance={total_balance:.2f}, position_usdt={position_usdt:.2f}, amount={amount:.6f}")
        
        return amount if amount > 0 else 0.0
    except Exception as e:
        logging.error(f"Error calculating position size for {ticker}: {e}")
        return 0.0

def adjust_dynamic_ratio(exchange_handler, ticker, long_value, short_value, current_price):
    """1분봉 변화율에 기반하여 동적 비율을 조정합니다."""
    try:
        total_value = long_value + short_value
        if total_value <= 10:
            return
        
        current_ratio = long_value / total_value
        target_ratio = 0.5

        df_1m = mb.GetOhlcv(exchange_handler.exchange, ticker, '1m', 3)
        if len(df_1m) >= 2:
            prev_price = float(df_1m['close'].iloc[-2])
            change_1m = (current_price - prev_price) / prev_price
            
            if abs(change_1m) > CONFIG['MIN_VOLUME_CHANGE']:
                target_ratio = max(0.3, min(0.7, 0.5 + change_1m * 0.15))
                log_debug_as_info(f"{ticker} - 1m change: {change_1m:.2%}, Target ratio: {target_ratio:.2%}")

        if abs(current_ratio - target_ratio) > CONFIG['HEDGE_REBALANCE_THRESHOLD']:
            min_amount = mb.GetMinimumAmount(exchange_handler.exchange, ticker)
            adjustment_value = min(total_value * abs(current_ratio - target_ratio) * 0.3, total_value * 0.1)
            adjustment_amount = adjustment_value / current_price

            if adjustment_amount >= min_amount:
                if current_ratio > target_ratio:
                    exchange_handler.place_order(ticker, 'sell', 'SHORT', adjustment_amount, current_price, f'Dynamic Ratio Short ({target_ratio:.2%})', 'dynamic_ratio_short')
                else:
                    exchange_handler.place_order(ticker, 'buy', 'LONG', adjustment_amount, current_price, f'Dynamic Ratio Long ({target_ratio:.2%})', 'dynamic_ratio_long')
    except Exception as e:
        logging.error(f"동적 비율 조정 오류 {ticker}: {e}")

def auto_delete_grid_by_exposure(exchange_handler, ticker, long_value, short_value, current_price, existing_orders):
    """보유 비율에 기반하여 그리드 주문을 자동 삭제합니다."""
    try:
        balance = exchange_handler.fetch_balance()
        total_balance = balance['total']['USDT']
        if total_balance == 0: return

        total_exposure = long_value + short_value
        exposure_ratio = total_exposure / total_balance
        
        if exposure_ratio > CONFIG['MAX_EXPOSURE']:
            logging.info(f"{ticker} - 노출 비율 초과: {exposure_ratio:.2%} > {CONFIG['MAX_EXPOSURE']:.2%}")
            
            orders_with_distance = sorted(
                [(order, abs(float(order['price']) - current_price) / current_price) for order in existing_orders],
                key=lambda x: x[1],
                reverse=True
            )
            
            for order, distance in orders_with_distance[:2]: # 최대 2개 삭제
                try:
                    exchange_handler.cancel_order(order['id'], ticker)
                    logging.info(f"{ticker} - 노출 비율 초과로 주문 삭제: ${float(order['price']):.2f} (거리: {distance:.2%})")
                except Exception as e:
                    logging.error(f"Error deleting order {order['id']}: {e}")
    except Exception as e:
        logging.error(f"Error auto-deleting grid by exposure for {ticker}: {e}")

def check_position_timeout(ticker):
    """포지션 타임아웃을 체크합니다."""
    # 이 함수는 utils의 position_cache를 직접 참조하므로 utils에 두는 것이 더 적합할 수 있으나,
    # 리스크 관리의 일부로 보고 여기에 둡니다. 필요시 utils로 이동 가능합니다.
    from utils import position_cache
    try:
        if ticker not in position_cache:
            position_cache[ticker] = {}
        
        # 현재 포지션 확인 (이 부분은 get_cached_amount를 호출해야 함)
        # 로직 간결화를 위해 이 함수는 process_ticker 내에서 직접 호출되는 것으로 가정하고 구현
        if 'position_timestamp' in position_cache.get(ticker, {}):
            elapsed_time = time.time() - position_cache[ticker]['position_timestamp']
            if elapsed_time > CONFIG['POSITION_TIMEOUT']:
                logging.info(f"{ticker} - 포지션 타임아웃: {elapsed_time/60:.1f}분 경과")
                return True
        return False
    except Exception as e:
        logging.error(f"Error checking position timeout for {ticker}: {e}")
        return False