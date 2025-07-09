# strategy_logic.py
import pandas as pd
import logging
import time
from config import CONFIG
import myBinance as mb
from utils import log_debug_as_info
import risk_manager

def calculate_atr(df, period=14):
    """ATR을 계산합니다."""
    try:
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        close = df['close'].astype(float)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(period).mean().iloc[-1]
    except Exception:
        return df['close'].iloc[-1] * 0.01

def check_entry_conditions(exchange_handler, ticker, df, current_price, ma, rsi):
    """개선된 진입 조건을 체크합니다."""
    try:
        conditions = {}
        # ... (원래 코드의 check_entry_conditions 함수 내용 전체를 여기에 복사)
        # 예시:
        conditions['ma_golden_cross'] = current_price > ma
        conditions['rsi_oversold'] = rsi < CONFIG['RSI_THRESHOLD_LONG']
        # ... (ADX, CCI, MFI 등 모든 지표 계산 및 점수화 로직)
        
        # 임시로 간단한 로직으로 대체합니다. 원래 코드를 여기에 붙여넣으세요.
        score = 5 if conditions['ma_golden_cross'] and conditions['rsi_oversold'] else 2
        
        entry_signal = {
            'long': score >= 4 and conditions.get('ma_golden_cross', False),
            'short': score >= 4 and not conditions.get('ma_golden_cross', False),
            'score': score,
            'max_score': 10,
            'conditions': conditions
        }
        logging.info(f"{ticker} - 진입 조건 점수: {score}/10")
        return entry_signal
    except Exception as e:
        logging.error(f"Error checking entry conditions for {ticker}: {e}")
        return {'long': False, 'short': False, 'score': 0, 'max_score': 10, 'conditions': {}}

def create_atr_based_grid(exchange_handler, ticker, current_price, atr, existing_orders, amount, entry_signal):
    """ATR 기반 그리드를 생성합니다."""
    # ...(원래 코드의 create_atr_based_grid 함수 내용 전체를 여기에 복사)...
    # 이 함수는 exchange_handler.place_order를 호출하도록 수정되어야 합니다.
    logging.info(f"{ticker} - Creating ATR-based grid...")


def progressive_grid_adjustment(exchange_handler, ticker, current_price, existing_orders, grid_interval_pct, amount):
    """점진적으로 그리드를 조정합니다."""
    # ...(원래 코드의 progressive_grid_adjustment 함수 내용 전체를 여기에 복사)...
    # 이 함수는 exchange_handler.place_order를 호출하도록 수정되어야 합니다.
    logging.info(f"{ticker} - Performing progressive grid adjustment...")
    return 0

def calculate_dynamic_grid_interval(ticker, current_price, atr, existing_orders=None):
    """기존 주문을 반영한 동적 그리드 간격 계산"""
    try:
        atr_percentage = atr / current_price
        
        # 기존 주문 가격 분포를 고려한 간격 조정
        if existing_orders and len(existing_orders) > 1:
            existing_prices = [float(o['price']) for o in existing_orders]
            price_range = max(existing_prices) - min(existing_prices)
            avg_interval = (price_range / (len(existing_prices) - 1)) if len(existing_prices) > 1 else 0.001
            target_interval = max(CONFIG['GRID_INTERVAL_MIN'], min(CONFIG['GRID_INTERVAL_MAX'], avg_interval / current_price))
        else:
            # ATR 기반 기본 계산
            if atr_percentage > 0.03:  # 높은 변동성
                target_interval = CONFIG['GRID_INTERVAL_MAX']
            elif atr_percentage < 0.01:  # 낮은 변동성
                target_interval = CONFIG['GRID_INTERVAL_MIN']
            else:  # 중간 변동성
                ratio = (atr_percentage - 0.01) / (0.03 - 0.01)
                target_interval = CONFIG['GRID_INTERVAL_MIN'] + ratio * (CONFIG['GRID_INTERVAL_MAX'] - CONFIG['GRID_INTERVAL_MIN'])
        
        # 최소 간격 보장
        min_safe_interval = 0.0005
        final_interval = max(target_interval, min_safe_interval)
        
        logging.info(f"{ticker} - 동적 그리드 간격: ATR%={atr_percentage:.4f}, 기존주문={len(existing_orders) if existing_orders else 0}개, 간격={final_interval:.4f} ({final_interval*100:.2f}%)")
        return final_interval
        
    except Exception as e:
        logging.error(f"Error calculating dynamic grid interval for {ticker}: {e}")
        return 0.0012  # 기본값
    
# ... (startup_grid_optimization, adjust_grid_on_timeout 등 다른 모든 전략 관련 함수들을 여기에 추가) ...
# 모든 함수들은 exchange 객체 대신 exchange_handler 객체를 인자로 받아야 합니다.
# 예: def startup_grid_optimization(exchange_handler, ticker):
# 내부에서는 exchange.fetch... 대신 exchange_handler.fetch... 를 사용합니다.