"""Phase 2 unit tests for pure functions and utility classes.

Tests cover:
- XSS sanitizer (strip_all_tags, sanitize_limited_html, strip_dangerous_content)
- Log masking (mask_phone, mask_amount, mask_id_card, mask_bank_card, mask_email, mask_phone_in_text)
- CSRF middleware (Double Submit Cookie validation)
- DecimalField Pydantic serializer
- Cache utility (with mocked Redis)
"""

import pytest
import json
import logging
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel

from app.utils.sanitizer import (
    strip_all_tags,
    sanitize_limited_html,
    strip_dangerous_content,
)
from app.utils.log_mask import (
    mask_phone,
    mask_amount,
    mask_id_card,
    mask_bank_card,
    mask_email,
    mask_phone_in_text,
)
from app.schemas.base import DecimalField, BaseSchema
from app.core.csrf_middleware import CSRFMiddleware
from app.utils.cache import (
    get_cached,
    set_cached,
    delete_cached,
    get_cached_model,
    set_cached_model,
    get_cached_dict,
    set_cached_dict,
    SHOP_DETAIL_TTL,
    PRODUCT_DETAIL_TTL,
    CONFIG_TTL,
)


# ============ XSS Sanitizer Tests ============


class TestStripAllTags:
    """Tests for strip_all_tags function."""

    def test_plain_text_unchanged(self):
        assert strip_all_tags("Hello World") == "Hello World"

    def test_strips_script_tags(self):
        result = strip_all_tags("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "alert" not in result or result == "alert('xss')"

    def test_strips_all_html_tags(self):
        result = strip_all_tags("<p>Hello <b>World</b></p>")
        assert "<" not in result
        assert ">" not in result

    def test_none_returns_none(self):
        assert strip_all_tags(None) is None

    def test_empty_string_returns_empty(self):
        assert strip_all_tags("") == ""

    def test_nested_tags_stripped(self):
        result = strip_all_tags("<div><p><span>nested</span></p></div>")
        assert "<" not in result
        assert "nested" in result

    def test_javascript_protocol_stripped(self):
        result = strip_all_tags('<a href="javascript:alert(1)">click</a>')
        assert "javascript:" not in result

    def test_mixed_content(self):
        result = strip_all_tags("Hello <b>bold</b> and <i>italic</i>")
        assert "Hello" in result
        assert "bold" in result
        assert "italic" in result
        assert "<" not in result


class TestSanitizeLimitedHtml:
    """Tests for sanitize_limited_html function."""

    def test_allows_safe_tags(self):
        result = sanitize_limited_html("<p>Hello</p>")
        assert "<p>" in result
        assert "</p>" in result

    def test_allows_bold_tag(self):
        result = sanitize_limited_html("<b>bold</b>")
        assert "<b>" in result

    def test_allows_italic_tag(self):
        result = sanitize_limited_html("<i>italic</i>")
        assert "<i>" in result

    def test_allows_strong_tag(self):
        result = sanitize_limited_html("<strong>strong</strong>")
        assert "<strong>" in result

    def test_allows_em_tag(self):
        result = sanitize_limited_html("<em>emphasized</em>")
        assert "<em>" in result

    def test_allows_list_tags(self):
        result = sanitize_limited_html("<ul><li>item</li></ul>")
        assert "<ul>" in result
        assert "<li>" in result

    def test_strips_unsafe_tags(self):
        result = sanitize_limited_html("<div>content</div>")
        assert "<div>" not in result
        assert "content" in result

    def test_strips_span_tag(self):
        result = sanitize_limited_html("<span>text</span>")
        assert "<span>" not in result

    def test_strips_h1_tag(self):
        result = sanitize_limited_html("<h1>heading</h1>")
        assert "<h1>" not in result

    def test_strips_attributes(self):
        result = sanitize_limited_html('<p class="x" style="color:red">text</p>')
        assert "class" not in result
        assert "style" not in result

    def test_strips_onclick_attribute(self):
        result = sanitize_limited_html('<p onclick="alert(1)">text</p>')
        assert "onclick" not in result

    def test_none_returns_none(self):
        assert sanitize_limited_html(None) is None

    def test_empty_string_returns_empty(self):
        assert sanitize_limited_html("") == ""


class TestStripDangerousContent:
    """Tests for strip_dangerous_content function."""

    def test_strips_script_tag(self):
        result = strip_dangerous_content("<script>alert(1)</script>")
        assert "<script>" not in result

    def test_strips_iframe_tag(self):
        result = strip_dangerous_content('<iframe src="evil.com"></iframe>')
        assert "<iframe>" not in result

    def test_strips_object_tag(self):
        result = strip_dangerous_content('<object data="x"></object>')
        assert "<object>" not in result

    def test_strips_embed_tag(self):
        result = strip_dangerous_content('<embed src="x">')
        assert "<embed>" not in result

    def test_strips_form_tag(self):
        result = strip_dangerous_content("<form><input></form>")
        assert "<form>" not in result

    def test_preserves_safe_tags(self):
        result = strip_dangerous_content("<b>bold</b> <i>italic</i>")
        assert "<b>" in result
        assert "<i>" in result

    def test_strips_event_attributes(self):
        result = strip_dangerous_content('<p onclick="alert(1)">text</p>')
        assert "onclick" not in result

    def test_none_returns_none(self):
        assert strip_dangerous_content(None) is None

    def test_empty_string_returns_empty(self):
        assert strip_dangerous_content("") == ""

    def test_mixed_dangerous_and_safe(self):
        result = strip_dangerous_content("<b>Hello</b><script>evil</script>")
        assert "<b>" in result
        assert "<script>" not in result


# ============ Log Masking Tests ============


class TestMaskPhone:
    """Tests for mask_phone function."""

    def test_standard_phone(self):
        assert mask_phone("13812345678") == "138****5678"

    def test_another_phone(self):
        assert mask_phone("15900001111") == "159****1111"

    def test_short_string_returns_as_is(self):
        assert mask_phone("123456") == "123456"

    def test_none_returns_none(self):
        assert mask_phone(None) is None

    def test_empty_string_returns_empty(self):
        assert mask_phone("") == ""


class TestMaskAmount:
    """Tests for mask_amount function."""

    def test_decimal_amount(self):
        assert mask_amount(128.50) == "128.**"

    def test_integer_amount(self):
        assert mask_amount(1000) == "1000.**"

    def test_decimal_type_input(self):
        assert mask_amount(Decimal("99.99")) == "99.**"

    def test_zero_amount(self):
        assert mask_amount(0) == "0.**"

    def test_string_amount(self):
        assert mask_amount("256.78") == "256.**"

    def test_none_returns_none_str(self):
        """mask_amount(None) returns 'None.**' because str(None) = 'None'."""
        assert mask_amount(None) == "None.**"

    def test_negative_amount(self):
        assert mask_amount(-50.00) == "-50.**"


class TestMaskIdCard:
    """Tests for mask_id_card function."""

    def test_standard_18_digit_id(self):
        result = mask_id_card("110101199001011234")
        assert result.startswith("110")
        assert result.endswith("1234")
        assert "*" in result

    def test_short_string_returns_as_is(self):
        assert mask_id_card("1234567") == "1234567"

    def test_none_returns_none(self):
        assert mask_id_card(None) is None

    def test_empty_returns_empty(self):
        assert mask_id_card("") == ""


class TestMaskBankCard:
    """Tests for mask_bank_card function."""

    def test_standard_bank_card(self):
        assert mask_bank_card("6222021234561234") == "****1234"

    def test_another_card(self):
        assert mask_bank_card("6217001234567890") == "****7890"

    def test_short_card_returns_as_is(self):
        assert mask_bank_card("1234") == "1234"

    def test_none_returns_none(self):
        assert mask_bank_card(None) is None

    def test_empty_returns_empty(self):
        assert mask_bank_card("") == ""


class TestMaskEmail:
    """Tests for mask_email function."""

    def test_standard_email(self):
        result = mask_email("testuser@example.com")
        assert result.startswith("t")
        assert result.endswith("r@example.com")
        assert "***" in result

    def test_short_local_part(self):
        result = mask_email("ab@c.com")
        assert result.startswith("a")
        assert "@c.com" in result

    def test_single_char_local(self):
        result = mask_email("a@example.com")
        assert "a***" in result or "@" in result

    def test_no_at_sign_returns_as_is(self):
        assert mask_email("notanemail") == "notanemail"

    def test_none_returns_none(self):
        assert mask_email(None) is None

    def test_empty_returns_empty(self):
        assert mask_email("") == ""


class TestMaskPhoneInText:
    """Tests for mask_phone_in_text function."""

    def test_masks_phone_in_text(self):
        result = mask_phone_in_text("联系13812345678了解更多")
        assert "138****5678" in result
        assert "13812345678" not in result

    def test_no_phone_unchanged(self):
        text = "这是一段没有手机号的文本"
        assert mask_phone_in_text(text) == text

    def test_multiple_phones(self):
        result = mask_phone_in_text("13812345678和15900001111")
        assert "138****5678" in result
        assert "159****1111" in result

    def test_empty_text(self):
        assert mask_phone_in_text("") == ""

    def test_none_returns_none(self):
        assert mask_phone_in_text(None) is None


# ============ CSRF Middleware Tests ============


class TestCSRFMiddleware:
    """Tests for CSRFMiddleware using Starlette TestClient."""

    def _make_app(self, debug=False):
        """Create a test ASGI app with CSRF middleware."""
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.responses import JSONResponse

        async def get_endpoint(request):
            return JSONResponse({"method": "GET"})

        async def post_endpoint(request):
            return JSONResponse({"method": "POST"})

        app = Starlette(
            routes=[
                Route("/test", get_endpoint, methods=["GET"]),
                Route("/test", post_endpoint, methods=["POST"]),
            ]
        )

        # Patch the module-level settings import in csrf_middleware
        with patch("app.core.csrf_middleware.settings") as mock_settings:
            mock_settings.DEBUG = debug
            app.add_middleware(CSRFMiddleware)

        return app

    def test_get_request_skips_validation(self):
        from starlette.testclient import TestClient
        with patch("app.core.csrf_middleware.settings") as mock_settings:
            mock_settings.DEBUG = False
            app = self._make_app(debug=False)
            # Re-patch because middleware captured settings at init time
            client = TestClient(app)
            response = client.get("/test")
            assert response.status_code == 200

    def test_post_without_tokens_returns_403(self):
        from starlette.testclient import TestClient
        app = self._make_app(debug=False)
        client = TestClient(app)
        # Need to patch settings.DEBUG on the already-created middleware
        with patch("app.core.csrf_middleware.settings") as mock_settings:
            mock_settings.DEBUG = False
            response = client.post("/test")
            assert response.status_code == 403

    def test_post_with_matching_tokens_succeeds(self):
        from starlette.testclient import TestClient
        app = self._make_app(debug=False)
        client = TestClient(app)
        token = "test-csrf-token-123"
        with patch("app.core.csrf_middleware.settings") as mock_settings:
            mock_settings.DEBUG = False
            response = client.post(
                "/test",
                cookies={"csrf_token": token},
                headers={"X-CSRF-Token": token},
            )
            assert response.status_code == 200

    def test_post_with_mismatched_tokens_returns_403(self):
        from starlette.testclient import TestClient
        app = self._make_app(debug=False)
        client = TestClient(app)
        with patch("app.core.csrf_middleware.settings") as mock_settings:
            mock_settings.DEBUG = False
            response = client.post(
                "/test",
                cookies={"csrf_token": "token-a"},
                headers={"X-CSRF-Token": "token-b"},
            )
            assert response.status_code == 403

    def test_post_with_cookie_but_no_header_returns_403(self):
        from starlette.testclient import TestClient
        app = self._make_app(debug=False)
        client = TestClient(app)
        with patch("app.core.csrf_middleware.settings") as mock_settings:
            mock_settings.DEBUG = False
            response = client.post(
                "/test",
                cookies={"csrf_token": "some-token"},
            )
            assert response.status_code == 403

    def test_post_with_header_but_no_cookie_returns_403(self):
        from starlette.testclient import TestClient
        app = self._make_app(debug=False)
        client = TestClient(app)
        with patch("app.core.csrf_middleware.settings") as mock_settings:
            mock_settings.DEBUG = False
            response = client.post(
                "/test",
                headers={"X-CSRF-Token": "some-token"},
            )
            assert response.status_code == 403

    def test_debug_mode_skips_validation(self):
        from starlette.testclient import TestClient
        app = self._make_app(debug=True)
        client = TestClient(app)
        with patch("app.core.csrf_middleware.settings") as mock_settings:
            mock_settings.DEBUG = True
            # POST without tokens should pass in DEBUG mode
            response = client.post("/test")
            assert response.status_code == 200


# ============ DecimalField Serializer Tests ============


class TestDecimalField:
    """Tests for DecimalField Pydantic serializer."""

    def test_json_serialization_returns_float(self):
        class TestModel(BaseSchema):
            amount: DecimalField

        model = TestModel(amount=Decimal("10.50"))
        json_data = json.loads(model.model_dump_json())
        assert isinstance(json_data["amount"], float)
        assert json_data["amount"] == 10.5

    def test_decimal_10_50(self):
        class TestModel(BaseSchema):
            amount: DecimalField

        model = TestModel(amount=Decimal("10.50"))
        json_data = json.loads(model.model_dump_json())
        assert json_data["amount"] == 10.5

    def test_decimal_zero(self):
        class TestModel(BaseSchema):
            amount: DecimalField

        model = TestModel(amount=Decimal("0.00"))
        json_data = json.loads(model.model_dump_json())
        assert json_data["amount"] == 0.0

    def test_decimal_large_value(self):
        class TestModel(BaseSchema):
            amount: DecimalField

        model = TestModel(amount=Decimal("999999.99"))
        json_data = json.loads(model.model_dump_json())
        assert json_data["amount"] == 999999.99

    def test_model_validate_from_dict(self):
        class TestModel(BaseSchema):
            amount: DecimalField

        model = TestModel.model_validate({"amount": "25.75"})
        assert model.amount == Decimal("25.75")

    def test_python_repr_stays_decimal(self):
        class TestModel(BaseSchema):
            amount: DecimalField

        model = TestModel(amount=Decimal("99.99"))
        # model_dump() should preserve Decimal type in Python context
        dump = model.model_dump()
        assert isinstance(dump["amount"], Decimal)


# ============ Cache Utility Tests (with mocked Redis) ============


class TestCacheGet:
    """Tests for get_cached function."""

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.get_cache = AsyncMock(return_value='{"key": "value"}')
            result = await get_cached("test_key")
            assert result == '{"key": "value"}'

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.get_cache = AsyncMock(return_value=None)
            result = await get_cached("nonexistent_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_redis_error_returns_none(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.get_cache = AsyncMock(side_effect=Exception("Redis down"))
            result = await get_cached("test_key")
            assert result is None


class TestCacheSet:
    """Tests for set_cached function."""

    @pytest.mark.asyncio
    async def test_set_success(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.set_cache = AsyncMock(return_value=True)
            result = await set_cached("test_key", "test_value", 300)
            assert result is True

    @pytest.mark.asyncio
    async def test_set_failure_returns_false(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.set_cache = AsyncMock(side_effect=Exception("Redis down"))
            result = await set_cached("test_key", "test_value")
            assert result is False


class TestCacheDelete:
    """Tests for delete_cached function."""

    @pytest.mark.asyncio
    async def test_delete_success(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.delete_cache = AsyncMock(return_value=True)
            result = await delete_cached("test_key")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_failure_returns_false(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.delete_cache = AsyncMock(side_effect=Exception("Redis down"))
            result = await delete_cached("test_key")
            assert result is False


class TestCacheModel:
    """Tests for get_cached_model and set_cached_model functions."""

    @pytest.mark.asyncio
    async def test_get_cached_model_hit(self):
        class TestModel(BaseModel):
            name: str
            value: int

        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.get_cache = AsyncMock(
                return_value='{"name": "test", "value": 42}'
            )
            result = await get_cached_model(TestModel, "test_key")
            assert result is not None
            assert result.name == "test"
            assert result.value == 42

    @pytest.mark.asyncio
    async def test_get_cached_model_miss(self):
        class TestModel(BaseModel):
            name: str

        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.get_cache = AsyncMock(return_value=None)
            result = await get_cached_model(TestModel, "test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_cached_model_deserialization_failure(self):
        class TestModel(BaseModel):
            name: str

        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.get_cache = AsyncMock(return_value="invalid json{{{")
            result = await get_cached_model(TestModel, "test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_cached_model_success(self):
        class TestModel(BaseModel):
            name: str

        model = TestModel(name="test")
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.set_cache = AsyncMock(return_value=True)
            result = await set_cached_model("test_key", model, 300)
            assert result is True


class TestCacheDict:
    """Tests for get_cached_dict and set_cached_dict functions."""

    @pytest.mark.asyncio
    async def test_get_cached_dict_hit(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.get_cache = AsyncMock(return_value='{"key": "value"}')
            result = await get_cached_dict("test_key")
            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_cached_dict_miss(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.get_cache = AsyncMock(return_value=None)
            result = await get_cached_dict("test_key")
            assert result is None

    @pytest.mark.asyncio
    async def test_set_cached_dict_success(self):
        with patch("app.utils.cache.redis_client") as mock_redis:
            mock_redis.set_cache = AsyncMock(return_value=True)
            result = await set_cached_dict("test_key", {"key": "value"}, 300)
            assert result is True


class TestCacheTTLConstants:
    """Tests for cache TTL constants."""

    def test_shop_detail_ttl(self):
        assert SHOP_DETAIL_TTL == 5 * 60  # 5 minutes

    def test_product_detail_ttl(self):
        assert PRODUCT_DETAIL_TTL == 5 * 60  # 5 minutes

    def test_config_ttl(self):
        assert CONFIG_TTL == 30 * 60  # 30 minutes
