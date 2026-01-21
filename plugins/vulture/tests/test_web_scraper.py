"""웹 스크래퍼 모듈 테스트

네이버 금융 스크래핑 함수들에 대한 단위 테스트
실제 네트워크 호출 없이 mock을 사용하여 테스트
"""
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from utils.web_scraper import (
    get_naver_stock_info,
    get_naver_stock_news,
    get_naver_discussion,
    get_naver_stock_list,
    clean_playwright_result,
    _parse_number,
    _parse_float,
    _parse_market_cap,
)


# Fixtures 디렉토리 경로
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> str:
    """테스트 픽스처 파일 로드"""
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


class TestGetNaverStockInfo:
    """get_naver_stock_info 함수 테스트"""

    @patch("utils.web_scraper.requests.get")
    def test_returns_dict_on_success(self, mock_get):
        """성공 시 dict 반환"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_stock_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_info("005930")

        assert isinstance(result, dict)
        mock_get.assert_called_once()

    @patch("utils.web_scraper.requests.get")
    def test_parses_stock_name(self, mock_get):
        """종목명 파싱"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_stock_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_info("005930")

        assert result["name"] == "삼성전자"

    @patch("utils.web_scraper.requests.get")
    def test_parses_market_cap(self, mock_get):
        """시가총액 파싱 (억 단위)"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_stock_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_info("005930")

        # 328조 4,300억 = 3284300 억
        assert result["market_cap"] == 3284300

    @patch("utils.web_scraper.requests.get")
    def test_parses_per_pbr(self, mock_get):
        """PER, PBR 파싱"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_stock_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_info("005930")

        assert result["per"] == 25.50
        assert result["pbr"] == 1.12

    @patch("utils.web_scraper.requests.get")
    def test_parses_foreign_ratio(self, mock_get):
        """외국인 비율 파싱"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_stock_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_info("005930")

        assert result["foreign_ratio"] == 52.34

    @patch("utils.web_scraper.requests.get")
    def test_returns_none_on_network_error(self, mock_get):
        """네트워크 에러 시 None 반환"""
        mock_get.side_effect = Exception("Network error")

        result = get_naver_stock_info("005930")

        assert result is None

    @patch("utils.web_scraper.requests.get")
    def test_returns_none_on_http_error(self, mock_get):
        """HTTP 에러 시 None 반환"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        result = get_naver_stock_info("005930")

        assert result is None

    @patch("utils.web_scraper.requests.get")
    def test_returns_none_on_empty_html(self, mock_get):
        """빈 HTML 시 None 반환"""
        mock_response = Mock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_info("005930")

        assert result is None

    @patch("utils.web_scraper.requests.get")
    def test_parses_stock_per_not_industry_per(self, mock_get):
        """종목 PER 파싱 (동일업종 PER 아님)"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_sise_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_info("005930")

        assert result["per"] == 31.04
        assert result["per"] != 21.33

    @patch("utils.web_scraper.requests.get")
    def test_parses_stock_pbr_not_industry_pbr(self, mock_get):
        """종목 PBR 파싱 (동일업종 PBR 아님)"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_sise_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_info("005930")

        assert result["pbr"] == 2.15
        assert result["pbr"] != 1.50

    @patch("utils.web_scraper.requests.get")
    def test_uses_correct_url(self, mock_get):
        """올바른 URL 사용 확인"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_stock_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        get_naver_stock_info("048910")

        call_args = mock_get.call_args
        assert "048910" in call_args[0][0]
        assert "finance.naver.com" in call_args[0][0]


class TestGetNaverStockNews:
    """get_naver_stock_news 함수 테스트"""

    @patch("utils.web_scraper.requests.get")
    def test_returns_list_on_success(self, mock_get):
        """성공 시 list 반환"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_news_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_news("005930")

        assert isinstance(result, list)

    @patch("utils.web_scraper.requests.get")
    def test_respects_limit_parameter(self, mock_get):
        """limit 파라미터 준수"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_news_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_news("005930", limit=3)

        assert len(result) <= 3

    @patch("utils.web_scraper.requests.get")
    def test_news_item_has_required_fields(self, mock_get):
        """뉴스 항목에 필수 필드 존재"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_news_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_news("005930", limit=1)

        assert len(result) >= 1
        news_item = result[0]
        assert "title" in news_item
        assert "date" in news_item
        assert "url" in news_item

    @patch("utils.web_scraper.requests.get")
    def test_url_is_full_path(self, mock_get):
        """URL이 전체 경로인지 확인"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_news_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_news("005930", limit=1)

        assert result[0]["url"].startswith("https://finance.naver.com")

    @patch("utils.web_scraper.requests.get")
    def test_returns_none_on_error(self, mock_get):
        """에러 시 None 반환"""
        mock_get.side_effect = Exception("Network error")

        result = get_naver_stock_news("005930")

        assert result is None


class TestGetNaverDiscussion:
    """get_naver_discussion 함수 테스트"""

    @patch("utils.web_scraper.requests.get")
    def test_returns_list_on_success(self, mock_get):
        """성공 시 list 반환"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_discussion_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_discussion("005930")

        assert isinstance(result, list)

    @patch("utils.web_scraper.requests.get")
    def test_respects_limit_parameter(self, mock_get):
        """limit 파라미터 준수"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_discussion_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_discussion("005930", limit=2)

        assert len(result) <= 2

    @patch("utils.web_scraper.requests.get")
    def test_discussion_item_has_required_fields(self, mock_get):
        """토론 항목에 필수 필드 존재"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_discussion_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_discussion("005930", limit=1)

        assert len(result) >= 1
        post = result[0]
        assert "title" in post
        assert "date" in post
        assert "url" in post

    @patch("utils.web_scraper.requests.get")
    def test_returns_none_on_error(self, mock_get):
        """에러 시 None 반환"""
        mock_get.side_effect = Exception("Network error")

        result = get_naver_discussion("005930")

        assert result is None

    @patch("utils.web_scraper.requests.get")
    def test_default_limit_is_10(self, mock_get):
        """기본 limit이 10인지 확인"""
        mock_response = Mock()
        mock_response.text = load_fixture("naver_discussion_page.html")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_discussion("005930")

        # 픽스처에 5개만 있으므로 최대 5개
        assert len(result) <= 10


class TestGetNaverStockList:
    """get_naver_stock_list 함수 테스트"""

    @patch("utils.web_scraper.requests.get")
    def test_returns_list_on_success(self, mock_get):
        """성공 시 list 반환"""
        mock_response = Mock()
        mock_response.text = """
        <html><body>
        <table class="type_2">
            <tr><a class="tltle" href="/item/main.naver?code=005930">삼성전자</a></tr>
            <tr><a class="tltle" href="/item/main.naver?code=000660">SK하이닉스</a></tr>
        </table>
        </body></html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = get_naver_stock_list("KOSPI")

        assert isinstance(result, list)

    @patch("utils.web_scraper.requests.get")
    def test_kospi_uses_market_code_0(self, mock_get):
        """KOSPI는 sosok=0 사용"""
        mock_response = Mock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        get_naver_stock_list("KOSPI")

        call_url = mock_get.call_args[0][0]
        assert "sosok=0" in call_url

    @patch("utils.web_scraper.requests.get")
    def test_kosdaq_uses_market_code_1(self, mock_get):
        """KOSDAQ은 sosok=1 사용"""
        mock_response = Mock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        get_naver_stock_list("KOSDAQ")

        call_url = mock_get.call_args[0][0]
        assert "sosok=1" in call_url

    @patch("utils.web_scraper.requests.get")
    def test_returns_none_on_error(self, mock_get):
        """에러 시 None 반환"""
        mock_get.side_effect = Exception("Network error")

        result = get_naver_stock_list("KOSPI")

        assert result is None


class TestCleanPlaywrightResult:
    """clean_playwright_result 함수 테스트"""

    def test_removes_ref_tags(self):
        """[ref=eXXX] 태그 제거"""
        text = "Hello [ref=e123] World [ref=e456]"
        result = clean_playwright_result(text)
        assert "[ref=" not in result
        assert "Hello" in result
        assert "World" in result

    def test_removes_cursor_tags(self):
        """[cursor=xxx] 태그 제거"""
        text = "Button [cursor=pointer] Click"
        result = clean_playwright_result(text)
        assert "[cursor=" not in result
        assert "Button" in result
        assert "Click" in result

    def test_removes_empty_brackets(self):
        """빈 괄호 제거"""
        text = "Text [] here []"
        result = clean_playwright_result(text)
        assert "[]" not in result

    def test_collapses_multiple_spaces(self):
        """연속 공백 정리"""
        text = "Hello    World"
        result = clean_playwright_result(text)
        assert "    " not in result
        assert "Hello World" in result

    def test_collapses_multiple_newlines(self):
        """연속 줄바꿈 정리"""
        text = "Line1\n\n\nLine2"
        result = clean_playwright_result(text)
        assert "\n\n\n" not in result

    def test_strips_whitespace(self):
        """앞뒤 공백 제거"""
        text = "   Hello World   "
        result = clean_playwright_result(text)
        assert result == "Hello World"

    def test_returns_string(self):
        """항상 문자열 반환"""
        result = clean_playwright_result("test")
        assert isinstance(result, str)

    def test_handles_empty_string(self):
        """빈 문자열 처리"""
        result = clean_playwright_result("")
        assert result == ""

    def test_complex_cleanup(self):
        """복합적인 정리 테스트"""
        text = "[ref=e1] Button [cursor=pointer]   Click []  \n\n\n  Next"
        result = clean_playwright_result(text)
        assert "[ref=e1]" not in result
        assert "[cursor=pointer]" not in result
        assert "[]" not in result
        assert "   " not in result
        assert "\n\n\n" not in result


class TestParseNumber:
    """_parse_number 함수 테스트"""

    def test_parses_simple_number(self):
        """단순 숫자 파싱"""
        assert _parse_number("12345") == 12345

    def test_removes_commas(self):
        """콤마 제거"""
        assert _parse_number("12,345,678") == 12345678

    def test_handles_negative(self):
        """음수 처리"""
        assert _parse_number("-500") == -500

    def test_handles_text_with_number(self):
        """텍스트가 섞인 숫자"""
        assert _parse_number("약 1,234원") == 1234

    def test_returns_zero_on_empty(self):
        """빈 문자열은 0 반환"""
        assert _parse_number("") == 0

    def test_returns_zero_on_no_digits(self):
        """숫자 없으면 0 반환"""
        assert _parse_number("텍스트만") == 0


class TestParseFloat:
    """_parse_float 함수 테스트"""

    def test_parses_float(self):
        """소수 파싱"""
        assert _parse_float("12.34") == 12.34

    def test_parses_integer_as_float(self):
        """정수를 실수로"""
        assert _parse_float("100") == 100.0

    def test_handles_percentage(self):
        """퍼센트 텍스트 처리"""
        assert _parse_float("25.5%") == 25.5

    def test_returns_zero_on_empty(self):
        """빈 문자열은 0.0 반환"""
        assert _parse_float("") == 0.0


class TestParseMarketCap:
    """_parse_market_cap 함수 테스트"""

    def test_parses_jo_and_eok(self):
        """조와 억 단위 파싱"""
        # 8조 9,014억 = 89014 억
        assert _parse_market_cap("8조 9,014억") == 89014

    def test_parses_large_jo(self):
        """큰 조 단위"""
        # 328조 4,300억 = 3284300 억
        assert _parse_market_cap("328조 4,300억") == 3284300

    def test_parses_only_eok(self):
        """억 단위만"""
        assert _parse_market_cap("500억") == 500

    def test_parses_only_jo(self):
        """조 단위만"""
        # 10조 = 100000 억
        assert _parse_market_cap("10조") == 100000

    def test_handles_newline(self):
        """줄바꿈 처리"""
        # 883조\n8,019 = 8838019 억
        assert _parse_market_cap("883조\n8,019") == 8838019

    def test_returns_zero_on_empty(self):
        """빈 문자열은 0 반환"""
        assert _parse_market_cap("") == 0

    def test_returns_zero_on_none(self):
        """None 유사 상황"""
        assert _parse_market_cap("") == 0
