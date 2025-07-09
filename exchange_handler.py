# exchange_handler.py
import ccxt
import logging
import time
import my_key
from config import CONFIG
from utils import handle_exception, invalidate_cache, save_history, can_notify
from line_alert import SendMessage

class ExchangeHandler:
    def __init__(self):
        self.exchange = self._create_exchange()

    def get_position_amount(self, balance, ticker, position_side):
            """특정 심볼과 사이드의 포지션 수량을 잔고 객체에서 파싱합니다."""
            symbol_id = ticker.replace("/", "").replace(":USDT", "")
            try:
                for position in balance.get('info', {}).get('positions', []):
                    if position['symbol'] == symbol_id and position['positionSide'] == position_side:
                        return abs(float(position.get('positionAmt', 0.0))) # 항상 양수로 반환
            except Exception as e:
                logging.error(f"포지션 수량 파싱 오류: {e}")
            return 0.0

    def _create_exchange(self):
        """ccxt exchange 객체를 생성합니다."""
        try:
            exchange = ccxt.binance({
                'apiKey': my_key.binance_api_key,
                'secret': my_key.binance_secret_key,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
            return exchange
        except Exception as e:
            logging.error(f"거래소 객체 생성 실패: {e}")
            raise

    def set_leverage(self, ticker, leverage):
        """계정 레버리지를 설정합니다."""
        try:
            current_leverage = self.exchange.fetch_leverage(ticker)['longLeverage']
            if current_leverage != leverage:
                logging.info(f"{ticker} - 레버리지 변경: {current_leverage}x -> {leverage}x")
                self.exchange.set_leverage(leverage, ticker)
                logging.info(f"{ticker} - 레버리지 설정 완료: {leverage}x")
        except Exception as e:
            logging.error(f"{ticker} - 레버리지 설정 실패: {e}")

    def ensure_hedge_mode(self):
        """헤지 모드를 활성화합니다."""
        try:
            response = self.exchange.fapiPrivateGetPositionSideDual()
            if not response.get('dualSidePosition', False):
                self.exchange.fapiPrivatePostPositionSideDual({'dualSidePosition': 'true'})
                logging.info("Hedge mode enabled.")
            else:
                logging.info("Hedge mode already enabled.")
        except Exception as e:
            handle_exception("System", "Hedge mode setting", e, "hedge_mode_error")

    def place_order(self, ticker, side, position_side, amount, price, action, notify_type):
        """주문을 실행합니다."""
        try:
            params = {'positionSide': position_side}
            is_close_order = any(keyword in action.lower() for keyword in ['close', 'stop', 'partial'])

            if is_close_order:
                # 포지션 감소 주문(reduceOnly)을 위한 로직 (원래 코드 유지)
                balance = self.exchange.fetch_balance(params={"type": "future"})
                symbol_id = ticker.replace("/", "").replace(":USDT", "")
                position_exists = False
                position_amt = 0.0
                
                for posi in balance['info']['positions']:
                    if posi['symbol'] == symbol_id and posi['positionSide'] == position_side:
                        position_amt = float(posi.get('positionAmt', 0.0))
                        if (position_side == 'LONG' and position_amt > 0) or \
                           (position_side == 'SHORT' and position_amt < 0):
                            position_exists = True
                            break
                
                if position_exists and abs(position_amt) >= amount:
                    params['reduceOnly'] = True
                    logging.info(f"ReduceOnly applied for {action}")
            
            # 주문 실행
            self.exchange.create_order(ticker, 'LIMIT', side, amount, price, params)
            invalidate_cache(ticker, position_side)
            logging.info(f"{action} order for {ticker}: Price {price}, Amount {amount}")

            if can_notify(ticker, notify_type):
                SendMessage(f"[{ticker}] {action}: {price:,.0f} USDT")
            
            save_history({
                'timestamp': time.time(),
                'ticker': ticker,
                'action': action.lower().replace(' ', '_'),
                'side': position_side.lower(),
                'price': price,
                'amount': amount
            })
        except ccxt.InvalidOrder as e:
            error_details = f"Order details: side={side}, position_side={position_side}, amount={amount}, price={price}, params={params}"
            logging.error(f"{ticker} - {action} invalid order: {e} | {error_details}")
            handle_exception(ticker, f"{action} invalid order", e, f"{notify_type}_invalid")
        except ccxt.InsufficientFunds as e:
            handle_exception(ticker, f"{action} insufficient funds", e, f"{notify_type}_funds")
        except ccxt.RateLimitExceeded:
            logging.error(f"Rate limit exceeded for {action}, waiting 60s")
            time.sleep(60)
        except Exception as e:
            handle_exception(ticker, action, e, notify_type)

    def fetch_balance(self):
        return self.exchange.fetch_balance(params={"type": "future"})

    def fetch_open_orders(self, ticker):
        return self.exchange.fetch_open_orders(ticker)

    def cancel_order(self, order_id, ticker):
        return self.exchange.cancel_order(order_id, ticker)
        
    def create_market_order(self, ticker, side, amount, params):
        return self.exchange.create_market_order(ticker, side, amount, params)

    def price_to_precision(self, ticker, price):
        return self.exchange.price_to_precision(ticker, price)