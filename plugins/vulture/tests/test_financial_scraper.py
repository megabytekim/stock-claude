"""재무제표 스크래핑 모듈 테스트

FnGuide 스크래핑 함수들에 대한 단위 테스트
실제 네트워크 호출 없이 mock을 사용하여 테스트
"""
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from utils.financial_scraper import (
    get_financial_data,
    get_fnguide_financial,
    get_naver_financial,
    calculate_peg,
    print_fi_report,
    _parse_fnguide_number,
    _parse_fnguide_table,
    _extract_company_name,
    _calculate_growth,
    _calculate_ratios,
    _parse_number,
)


# Fixtures 디렉토리 경로
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    """테스트 픽스처 파일 로드"""
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


class TestGetFinancialData:
    """get_financial_data 함수 테스트"""

    def test_returns_dict_or_none(self, sample_ticker_kr):
        """성공 시 dict 반환, 실패 시 None 반환"""
        with patch('utils.financial_scraper.get_fnguide_financial') as mock:
            mock.return_value = {
                'source': 'FnGuide',
                'ticker': sample_ticker_kr,
                'annual': {'2024': {'revenue': 3008709}},
            }
            result = get_financial_data(sample_ticker_kr)

        assert isinstance(result, dict) or result is None

    def test_returns_fnguide_result_on_success(self, sample_ticker_kr):
        """FnGuide 성공 시 해당 결과 반환"""
        expected_data = {
            'source': 'FnGuide',
            'ticker': sample_ticker_kr,
            'name': '삼성전자',
            'annual': {'2024': {'revenue': 3008709}},
        }
        with patch('utils.financial_scraper.get_fnguide_financial') as mock:
            mock.return_value = expected_data
            result = get_financial_data(sample_ticker_kr)

        assert result == expected_data
        assert result['source'] == 'FnGuide'

    def test_returns_none_when_fnguide_fails(self, sample_ticker_kr):
        """FnGuide 실패 시 None 반환"""
        with patch('utils.financial_scraper.get_fnguide_financial') as mock:
            mock.return_value = None
            result = get_financial_data(sample_ticker_kr)

        assert result is None

    def test_passes_retry_parameter(self, sample_ticker_kr):
        """retry 파라미터 전달 확인"""
        with patch('utils.financial_scraper.get_fnguide_financial') as mock:
            mock.return_value = None
            get_financial_data(sample_ticker_kr, retry=5)

        mock.assert_called_once_with(sample_ticker_kr, retry=5)


class TestGetFnguideFinancial:
    """get_fnguide_financial 함수 테스트"""

    @patch('utils.financial_scraper.requests.get')
    def test_returns_dict_on_success(self, mock_get, sample_ticker_kr):
        """성공 시 dict 반환"""
        mock_response = Mock()
        mock_response.text = load_fixture("fnguide_financial_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_fnguide_financial(sample_ticker_kr)

        assert isinstance(result, dict)

    @patch('utils.financial_scraper.requests.get')
    def test_has_required_keys(self, mock_get, sample_ticker_kr):
        """필수 키 존재 확인"""
        mock_response = Mock()
        mock_response.text = load_fixture("fnguide_financial_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_fnguide_financial(sample_ticker_kr)

        assert result is not None
        assert 'source' in result
        assert 'ticker' in result
        assert 'annual' in result
        assert 'growth' in result
        assert 'ratios' in result
        assert result['source'] == 'FnGuide'

    @patch('utils.financial_scraper.requests.get')
    def test_parses_income_data(self, mock_get, sample_ticker_kr):
        """손익계산서 데이터 파싱"""
        mock_response = Mock()
        mock_response.text = load_fixture("fnguide_financial_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_fnguide_financial(sample_ticker_kr)

        assert result is not None
        annual = result.get('annual', {})
        assert '2024' in annual
        assert 'revenue' in annual['2024']

    @patch('utils.financial_scraper.requests.get')
    def test_returns_none_on_network_error(self, mock_get, sample_ticker_kr):
        """네트워크 에러 시 None 반환"""
        mock_get.side_effect = Exception("Network error")

        result = get_fnguide_financial(sample_ticker_kr, retry=0)

        assert result is None

    @patch('utils.financial_scraper.requests.get')
    def test_returns_none_on_http_error(self, mock_get, sample_ticker_kr):
        """HTTP 에러 시 None 반환"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        result = get_fnguide_financial(sample_ticker_kr, retry=0)

        assert result is None

    @patch('utils.financial_scraper.requests.get')
    def test_returns_none_on_empty_html(self, mock_get, sample_ticker_kr):
        """빈 HTML 시 None 반환"""
        mock_response = Mock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_fnguide_financial(sample_ticker_kr, retry=0)

        assert result is None

    @patch('utils.financial_scraper.requests.get')
    def test_uses_correct_url(self, mock_get, sample_ticker_kr):
        """올바른 URL 사용 확인"""
        mock_response = Mock()
        mock_response.text = load_fixture("fnguide_financial_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        get_fnguide_financial("048910")

        call_args = mock_get.call_args
        assert "A048910" in call_args[0][0]
        assert "comp.fnguide.com" in call_args[0][0]

    @patch('utils.financial_scraper.requests.get')
    def test_retries_on_failure(self, mock_get, sample_ticker_kr):
        """실패 시 재시도"""
        mock_response = Mock()
        mock_response.text = load_fixture("fnguide_financial_page.html")
        mock_response.raise_for_status = Mock()

        # 처음 2번 실패, 3번째 성공
        mock_get.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            mock_response
        ]

        result = get_fnguide_financial(sample_ticker_kr, retry=2)

        assert result is not None
        assert mock_get.call_count == 3


class TestGetNaverFinancial:
    """get_naver_financial 함수 테스트 (fallback용)"""

    @patch('utils.financial_scraper.requests.get')
    def test_returns_dict_or_none(self, mock_get, sample_ticker_kr):
        """성공 시 dict 반환, 실패 시 None 반환"""
        mock_response = Mock()
        mock_response.text = """
        <html><body>
            <div class="wrap_company"><h2><a>삼성전자</a></h2></div>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_financial(sample_ticker_kr)

        assert isinstance(result, dict) or result is None

    @patch('utils.financial_scraper.requests.get')
    def test_has_source_naver_finance(self, mock_get, sample_ticker_kr):
        """source가 'Naver Finance'인지 확인"""
        mock_response = Mock()
        mock_response.text = """
        <html><body>
            <div class="wrap_company"><h2><a>삼성전자</a></h2></div>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_financial(sample_ticker_kr)

        if result:
            assert result['source'] == 'Naver Finance'

    @patch('utils.financial_scraper.requests.get')
    def test_returns_none_on_error(self, mock_get, sample_ticker_kr):
        """에러 시 None 반환"""
        mock_get.side_effect = Exception("Network error")

        result = get_naver_financial(sample_ticker_kr)

        assert result is None


class TestCalculatePeg:
    """calculate_peg 함수 테스트 (PEG 비율 계산)"""

    def test_calculates_correctly(self):
        """PEG = PER / EPS Growth Rate"""
        result = calculate_peg(per=20.0, eps_growth=10.0)

        assert result == 2.0  # 20 / 10 = 2.0

    def test_handles_zero_growth(self):
        """EPS 성장률 0일 때 None 반환"""
        result = calculate_peg(per=20.0, eps_growth=0.0)

        assert result is None

    def test_handles_negative_growth(self):
        """음수 EPS 성장률 처리"""
        result = calculate_peg(per=20.0, eps_growth=-10.0)

        assert result == -2.0  # 20 / -10 = -2.0

    def test_handles_none_per(self):
        """PER이 None일 때 None 반환"""
        result = calculate_peg(per=None, eps_growth=10.0)

        assert result is None

    def test_handles_none_eps_growth(self):
        """EPS 성장률이 None일 때 None 반환"""
        result = calculate_peg(per=20.0, eps_growth=None)

        assert result is None

    def test_rounds_to_two_decimals(self):
        """소수점 2자리로 반올림"""
        result = calculate_peg(per=15.0, eps_growth=7.0)

        assert result == 2.14  # 15 / 7 = 2.142857... -> 2.14


class TestParseFnguideNumber:
    """_parse_fnguide_number 함수 테스트"""

    def test_parses_simple_number(self):
        """단순 숫자 파싱"""
        assert _parse_fnguide_number("12345") == 12345.0

    def test_removes_commas(self):
        """콤마 제거"""
        assert _parse_fnguide_number("1,234,567") == 1234567.0

    def test_parses_negative_number(self):
        """음수 파싱"""
        assert _parse_fnguide_number("-500") == -500.0

    def test_parses_float(self):
        """소수점 파싱"""
        assert _parse_fnguide_number("123.45") == 123.45

    def test_returns_none_on_empty(self):
        """빈 문자열 시 None 반환"""
        assert _parse_fnguide_number("") is None

    def test_returns_none_on_dash(self):
        """대시(-) 시 None 반환"""
        assert _parse_fnguide_number("-") is None

    def test_returns_none_on_na(self):
        """N/A 시 None 반환"""
        assert _parse_fnguide_number("N/A") is None

    def test_returns_none_on_none_input(self):
        """None 입력 시 None 반환"""
        assert _parse_fnguide_number(None) is None

    def test_removes_whitespace(self):
        """공백 제거"""
        assert _parse_fnguide_number("  1,234  ") == 1234.0


class TestCalculateGrowth:
    """_calculate_growth 함수 테스트"""

    def test_calculates_revenue_yoy(self):
        """매출 YoY 성장률 계산"""
        income_data = {
            '2024': {'revenue': 110},
            '2023': {'revenue': 100},
        }

        result = _calculate_growth(income_data)

        assert result['revenue_yoy'] == 10.0  # (110-100)/100 * 100

    def test_calculates_operating_profit_yoy(self):
        """영업이익 YoY 성장률 계산"""
        income_data = {
            '2024': {'operating_profit': 50},
            '2023': {'operating_profit': 40},
        }

        result = _calculate_growth(income_data)

        assert result['operating_profit_yoy'] == 25.0  # (50-40)/40 * 100

    def test_returns_none_on_empty_data(self):
        """빈 데이터 시 None 값 반환"""
        result = _calculate_growth({})

        assert result['revenue_yoy'] is None
        assert result['operating_profit_yoy'] is None

    def test_returns_none_on_single_year(self):
        """단일 연도 데이터 시 None 값 반환"""
        income_data = {
            '2024': {'revenue': 110},
        }

        result = _calculate_growth(income_data)

        assert result['revenue_yoy'] is None

    def test_excludes_accumulated_periods(self):
        """누적 연도 제외하고 계산"""
        income_data = {
            '2025': {'revenue': 80},   # 누적
            '2024': {'revenue': 110},
            '2023': {'revenue': 100},
        }
        period_labels = {'2025': '3Q누적'}

        result = _calculate_growth(income_data, period_labels)

        # 2025 제외, 2024 vs 2023 비교
        assert result['comparison'] == '2024 vs 2023'
        assert result['revenue_yoy'] == 10.0


class TestCalculateRatios:
    """_calculate_ratios 함수 테스트"""

    def test_calculates_debt_ratio(self):
        """부채비율 계산"""
        balance_data = {
            '2024': {
                'total_liabilities': 50,
                'total_equity': 100,
            },
        }

        result = _calculate_ratios(None, balance_data)

        assert result['debt_ratio'] == 50.0  # 50/100 * 100

    def test_calculates_current_ratio(self):
        """유동비율 계산"""
        balance_data = {
            '2024': {
                'current_assets': 150,
                'current_liabilities': 100,
            },
        }

        result = _calculate_ratios(None, balance_data)

        assert result['current_ratio'] == 150.0  # 150/100 * 100

    def test_calculates_roe(self):
        """ROE 계산"""
        income_data = {
            '2024': {'net_income': 10},
        }
        balance_data = {
            '2024': {'total_equity': 100},
        }

        result = _calculate_ratios(income_data, balance_data)

        assert result['roe'] == 10.0  # 10/100 * 100

    def test_calculates_roa(self):
        """ROA 계산"""
        income_data = {
            '2024': {'net_income': 5},
        }
        balance_data = {
            '2024': {'total_assets': 200},
        }

        result = _calculate_ratios(income_data, balance_data)

        assert result['roa'] == 2.5  # 5/200 * 100

    def test_returns_none_on_empty_balance(self):
        """빈 재무상태표 시 None 값 반환"""
        result = _calculate_ratios(None, None)

        assert result['debt_ratio'] is None
        assert result['current_ratio'] is None
        assert result['roe'] is None
        assert result['roa'] is None


class TestParseNumber:
    """_parse_number 함수 테스트"""

    def test_parses_simple_number(self):
        """단순 숫자 파싱"""
        assert _parse_number("12345") == 12345

    def test_removes_commas(self):
        """콤마 제거"""
        assert _parse_number("1,234,567") == 1234567

    def test_parses_negative_number(self):
        """음수 파싱"""
        assert _parse_number("-500") == -500

    def test_returns_none_on_invalid(self):
        """유효하지 않은 입력 시 None 반환"""
        assert _parse_number("text") is None

    def test_returns_none_on_empty(self):
        """빈 문자열 시 None 반환"""
        # _parse_number는 try-except로 None 반환
        result = _parse_number("")
        assert result is None


class TestPrintFiReport:
    """print_fi_report 함수 테스트"""

    @patch('utils.financial_scraper.get_financial_data')
    @patch('builtins.print')
    def test_prints_report_on_success(self, mock_print, mock_get_data, sample_ticker_kr):
        """성공 시 리포트 출력"""
        mock_get_data.return_value = {
            'source': 'FnGuide',
            'ticker': sample_ticker_kr,
            'name': '삼성전자',
            'period': '2024/12',
            'annual': {
                '2024': {'revenue': 3008709, 'operating_profit': 659108, 'net_income': 543423},
                '2023': {'revenue': 2589356, 'operating_profit': 65401, 'net_income': 154877},
            },
            'growth': {'revenue_yoy': 16.21, 'operating_profit_yoy': 907.9, 'comparison': '2024 vs 2023'},
            'ratios': {'debt_ratio': 30.5, 'current_ratio': 180.2, 'roe': 8.5, 'roa': 4.2},
            'cash_flow': {
                '2024': {'operating_cash_flow': 730000, 'fcf': 450000},
            },
            'period_labels': {},
        }

        print_fi_report(sample_ticker_kr)

        # print가 호출되었는지 확인
        assert mock_print.called
        # 최소한 몇 번 이상 호출 (헤더 + 데이터)
        assert mock_print.call_count > 5

    @patch('utils.financial_scraper.get_financial_data')
    @patch('builtins.print')
    def test_prints_error_on_failure(self, mock_print, mock_get_data, sample_ticker_kr):
        """실패 시 에러 메시지 출력"""
        mock_get_data.return_value = None

        print_fi_report(sample_ticker_kr)

        # 에러 메시지 출력 확인
        mock_print.assert_called()
        # 첫 번째 호출에 '실패' 또는 ticker가 포함되어 있는지 확인
        call_args = str(mock_print.call_args_list)
        assert '실패' in call_args or sample_ticker_kr in call_args

    @patch('utils.financial_scraper.get_financial_data')
    @patch('builtins.print')
    def test_handles_accumulated_period_labels(self, mock_print, mock_get_data, sample_ticker_kr):
        """누적 기간 라벨 처리"""
        mock_get_data.return_value = {
            'source': 'FnGuide',
            'ticker': sample_ticker_kr,
            'name': '삼성전자',
            'period': '2025/09',
            'annual': {
                '2025': {'revenue': 2000000},
                '2024': {'revenue': 3008709},
            },
            'growth': {},
            'ratios': {},
            'cash_flow': {},
            'period_labels': {'2025': '3Q누적'},
        }

        print_fi_report(sample_ticker_kr)

        # print가 호출되었는지 확인
        assert mock_print.called


class TestExtractCompanyName:
    """_extract_company_name 함수 테스트"""

    def test_extracts_from_giname_class(self):
        """h1.giName에서 회사명 추출"""
        from bs4 import BeautifulSoup

        html = '<html><body><h1 class="giName">삼성전자</h1></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        result = _extract_company_name(soup)

        assert result == '삼성전자'

    def test_extracts_from_title(self):
        """title에서 회사명 추출"""
        from bs4 import BeautifulSoup

        html = '<html><head><title>SK하이닉스(000660) 재무제표</title></head><body></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        result = _extract_company_name(soup)

        assert result == 'SK하이닉스'

    def test_returns_none_on_no_name(self):
        """회사명 없으면 None 반환"""
        from bs4 import BeautifulSoup

        html = '<html><body></body></html>'
        soup = BeautifulSoup(html, 'html.parser')

        result = _extract_company_name(soup)

        assert result is None
