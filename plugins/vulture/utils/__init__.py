"""Utils package for stock analysis

pykrx 기반 데이터 조회 및 기술지표 유틸리티
네이버 금융 웹 스크래핑 유틸리티
"""
from utils.data_fetcher import (
    get_ohlcv,
    get_ticker_name,
    get_ticker_list,
    get_fundamental,
    get_market_cap,
)
from utils.deprecated import (
    get_investor_trading,
    get_short_selling,
)
from utils.indicators import (
    sma,
    ema,
    rsi,
    macd,
    bollinger,
    stochastic,
    support_resistance,
)
from utils.web_scraper import (
    get_naver_stock_info,
    get_naver_stock_news,
    get_naver_discussion,
    clean_playwright_result,
)
from utils.ti_analyzer import (
    get_ti_full_analysis,
    print_ti_report,
    get_rsi_signal,
    get_ma_alignment,
)
from utils.financial_scraper import (
    get_financial_data,
    get_fnguide_financial,
    get_naver_financial,
    print_fi_report,
    calculate_peg,
)

__all__ = [
    # data_fetcher
    'get_ohlcv',
    'get_ticker_name',
    'get_ticker_list',
    'get_fundamental',
    'get_market_cap',
    'get_investor_trading',
    'get_short_selling',
    # indicators
    'sma',
    'ema',
    'rsi',
    'macd',
    'bollinger',
    'stochastic',
    'support_resistance',
    # web_scraper
    'get_naver_stock_info',
    'get_naver_stock_news',
    'get_naver_discussion',
    'clean_playwright_result',
    # ti_analyzer
    'get_ti_full_analysis',
    'print_ti_report',
    'get_rsi_signal',
    'get_ma_alignment',
    # financial_scraper
    'get_financial_data',
    'get_fnguide_financial',
    'get_naver_financial',
    'print_fi_report',
    'calculate_peg',
]
