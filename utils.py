# utils.py
import logging
import time
import json
import os
from datetime import datetime, timezone
from line_alert import SendMessage
from config import CONFIG

# --- 캐시 관리 ---
price_cache = {}
min_amount_cache = {'ETH/USDT:USDT': {'amount': 0.001, 'timestamp': time.time()}}
position_cache = {}
amount_cache = {}
funding_cache = {}
last_notification = {}
cumulative_funding = {}

DEBUG_MODE = os.getenv('DEBUG_MODE', 'False') == 'True'

def log_debug_as_info(message):
    """디버깅 메시지를 INFO 레벨로 로깅"""
    if DEBUG_MODE:
        logging.info(f"[DEBUG] {message}")
    else:
        logging.debug(message)

def get_cached_data(cache, key, fetch_func, duration):
    """제네릭 캐시 데이터 조회 함수"""
    current_time = time.time()
    if key in cache and current_time - cache[key]['timestamp'] < duration:
        log_debug_as_info(f"Using cached data for {key}")
        return cache[key]['data']
    
    data = fetch_func()
    cache[key] = {'data': data, 'timestamp': current_time}
    log_debug_as_info(f"Fetched new data for {key}")
    return data

def invalidate_cache(ticker, position_side):
    """포지션 관련 캐시 무효화"""
    keys_to_delete = [
        f"{ticker}_{position_side}_amount",
        f"{ticker}_{position_side}"
    ]
    for key in keys_to_delete:
        if key in amount_cache:
            del amount_cache[key]
            log_debug_as_info(f"Invalidated amount cache for {key}")
        if key in position_cache:
            del position_cache[key]
            log_debug_as_info(f"Invalidated position cache for {key}")

def clear_all_cache():
    """모든 캐시 강제 무효화"""
    global price_cache, min_amount_cache, position_cache, amount_cache, funding_cache, last_notification, cumulative_funding
    price_cache.clear()
    min_amount_cache.clear()
    position_cache.clear()
    amount_cache.clear()
    funding_cache.clear()
    last_notification.clear()
    cumulative_funding.clear()
    logging.info("All caches cleared.")

# --- 예외 및 알림 처리 ---
def handle_exception(ticker, action, e, notify_type):
    """예외 처리 및 알림"""
    error_msg = f"{action} 오류: {str(e)[:50]}"
    logging.error(f"{ticker} - {error_msg}")
    if can_notify(ticker, notify_type):
        SendMessage(f"[{ticker}] {error_msg}")

def can_notify(ticker, event_type, cooldown=None):
    """알림 쿨다운 관리"""
    current_time = time.time()
    if ticker not in last_notification:
        last_notification[ticker] = {}
    
    cooldown_time = cooldown if cooldown is not None else CONFIG.get('NOTIFICATION_COOLDOWN', 300)
    
    if event_type not in last_notification[ticker] or current_time - last_notification[ticker][event_type] > cooldown_time:
        last_notification[ticker][event_type] = current_time
        return True
    return False

# --- 기록 저장 ---
def save_history(data):
    """거래 기록 저장"""
    try:
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = os.path.join(CONFIG['HISTORY_DIR'], f"{date_str}.json")
        history = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    history = json.load(f)
                    if not isinstance(history, list):
                        history = []
                except json.JSONDecodeError:
                    history = []
        history.append(data)
        with open(file_path, 'w') as f:
            json.dump(history, f, indent=2)
        log_debug_as_info(f"Saved history: {data}")
    except Exception as e:
        logging.error(f"Failed to save history: {e}")