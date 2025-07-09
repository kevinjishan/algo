# config.py

# 설정값 - 그록 제안 반영: 진정한 헷징 전략 구현
CONFIG = {
    'SYMBOLS': ['ETH/USDT:USDT'],
    'SYMBOL_WEIGHTS': {'ETH/USDT': 1.0},  # ETH 100% 가중치
    'LEVERAGE': 5,  # 10배 → 5배로 안전성 강화 (포지션 과다 방지)
    'MA_PERIOD': 20,
    'RSI_PERIOD': 14,
    'POSITION_SIZE': 0.01,  # 총 자본의 1% - 포지션 과다 방지
    'MAX_STEPS': 6,  # 그리드 단계 유지
    'STOP_LOSS_RATE': 0.06,  # 6% 스톱로스
    'TAKE_PROFIT_RATE': 0.04,  # 4% 익절
    'GRID_INTERVAL_MIN': 0.0012,  # 🔧 그록 권고: 0.08% → 0.12% (매매 빈도 감소)
    'GRID_INTERVAL_MAX': 0.0020,  # 🔧 그록 권고: 0.15% → 0.20% (매매 빈도 감소)
    'HEDGE_ENABLED': True,
    'HEDGE_REBALANCE_THRESHOLD': 0.15,  # 🔧 그록 권고: 12% → 15% (매매 빈도 감소)
    'HEDGE_RATIO_THRESHOLD': 0.7,  # 70% 이상 한쪽으로 치우치면 헷징
    'HEDGE_AMOUNT_RATIO': 0.3,  # 불균형 해소를 위한 헷징 비율
    'FUNDING_RATE_THRESHOLD': 0.01,  # 1% 이상 펀딩비 시 헷징
    'MA_DEVIATION': 0.015,  # 1.5% MA 편차
    'RSI_OVERSOLD': 30,
    'RSI_OVERBOUGHT': 70,
    'RSI_THRESHOLD_LONG': 35,  # 🔧 그록 권고: 진입 조건 강화
    'RSI_THRESHOLD_SHORT': 65,  # 🔧 그록 권고: 진입 조건 강화
    'RSI_SIGNAL_THRESHOLD': 30,  # RSI 신호 임계값
    'ADX_THRESHOLD': 25,  # 🔧 그록 권고: 추세 강도 임계값
    'CCI_THRESHOLD': 100,  # CCI 임계값
    'MFI_THRESHOLD': 20,  # MFI 임계값
    'STOCH_K_THRESHOLD': 20,  # Stochastic K 임계값
    'STOCH_D_THRESHOLD': 20,  # Stochastic D 임계값
    'BB_EXPANSION_THRESHOLD': 1.5,  # 볼린저 밴드 확장 임계값
    'TIMEFRAME_CONFIRMATION': True,  # 🔧 그록 권고: 다중 시간프레임 확인
    'VOLUME_THRESHOLD': 1.5,  # 거래량 임계값
    'VOLUME_SPIKE_THRESHOLD': 2.0,  # 거래량 급증 임계값
    'MAX_EXPOSURE': 3.0,  # 🔧 그록 권고: 노출 비율 제한 완화 (70% → 300%)
    'EMERGENCY_STOP_LOSS': 0.10,  # 10% 긴급 손절
    'POSITION_TIMEOUT': 1800,  # 30분 포지션 타임아웃
    'MIN_PROFIT_RATE': 0.001,  # 최소 수익률 0.1%
    'DYNAMIC_GRID_ENABLED': True,
    'PROGRESSIVE_ADJUSTMENT_ENABLED': True,
    'ATR_MULTIPLIER': 2.0,  # ATR 기반 그리드 간격
    'LOG_DIR': 'logs',
    'HISTORY_DIR': 'history',
    'HISTORY_FILE': 'history/trading_history.json',
    'LOG_FILE': 'logs/grid_trading.log',
    'LOG_MAX_BYTES': 10 * 1024 * 1024,
    'LOG_BACKUP_COUNT': 5,
    'CACHE_DURATION': 15,
    'FUNDING_CACHE_DURATION': 3600,
    'NOTIFY_COOLDOWN': 300,
    'NOTIFICATION_COOLDOWN': 300,  # 5분 알림 쿨다운
    'TRADE_FREQUENCY_TARGET': 55,  # 🔧 그록 목표: 주간 55회 매매
    'ENTRY_CONDITION_STRICTNESS': 0.8,  # 🔧 그록 권고: 진입 조건 강화 (0.5 → 0.8)
    'PROGRESSIVE_THRESHOLD_MULTIPLIER': 2.5,  # 🔧 그록 권고: 점진적 조정 완화 (2.0 → 2.5)
    'MIN_VOLUME_CHANGE': 0.01,  # 🔧 그록 권고: 최소 변화율 조건 완화 (0.015 → 0.01)
    'SLEEP_TIME': 5,  # 🔧 그록 권고: 매매 빈도 증가 (15초 → 10초 → 5초)
}