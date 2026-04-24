"""Tests for ModelFetcher (urllib mocked)."""

import json
from unittest.mock import patch, MagicMock

import pytest

import claude_3p_gui as app


def _resp(data: dict, status: int = 200) -> MagicMock:
    """Build a mock response object for urlopen."""
    m = MagicMock()
    m.read.return_value = json.dumps(data).encode("utf-8")
    m.getcode.return_value = status
    m.__enter__.return_value = m
    m.__exit__.return_value = False
    return m


class TestModelFetcher:
    def test_v1_models_success(self):
        resp = _resp({"data": [{"id": "m-1"}, {"id": "m-2"}]})
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp) as u:
            models = app.ModelFetcher.fetch("https://x.com/", "sk-test")
        assert models == ["m-1", "m-2"]
        called_url = u.call_args.args[0].full_url
        assert called_url == "https://x.com/v1/models"

    def test_deduplicates_and_sorts(self):
        resp = _resp({"data": [{"id": "b"}, {"id": "a"}, {"id": "b"}]})
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp):
            assert app.ModelFetcher.fetch("https://x.com/", "sk") == ["a", "b"]

    def test_fallback_to_models_endpoint(self):
        """If /v1/models 404s, fall back to /models."""
        def side_effect(req, timeout=0):
            if req.full_url.endswith("/v1/models"):
                raise app.urllib.error.HTTPError(
                    req.full_url, 404, "Not Found", {}, None
                )
            return _resp({"data": [{"id": "m"}]})

        with patch(
            "claude_3p_gui.urllib.request.urlopen",
            side_effect=side_effect,
        ):
            assert app.ModelFetcher.fetch("https://x.com/", "sk") == ["m"]

    def test_401_surfaces_as_auth_error(self):
        def side_effect(req, timeout=0):
            raise app.urllib.error.HTTPError(
                req.full_url, 401, "Unauthorized", {}, None
            )

        with patch(
            "claude_3p_gui.urllib.request.urlopen",
            side_effect=side_effect,
        ):
            with pytest.raises(app.ModelFetchError) as exc:
                app.ModelFetcher.fetch("https://x.com/", "sk")
        assert "鉴权失败" in str(exc.value)

    def test_timeout_error_message(self):
        import socket

        def side_effect(req, timeout=0):
            raise socket.timeout("timed out")

        with patch(
            "claude_3p_gui.urllib.request.urlopen",
            side_effect=side_effect,
        ):
            with pytest.raises(app.ModelFetchError) as exc:
                app.ModelFetcher.fetch("https://x.com/", "sk")
        assert "超时" in str(exc.value)

    def test_sends_expected_headers(self):
        resp = _resp({"data": [{"id": "m"}]})
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp) as u:
            app.ModelFetcher.fetch("https://x.com/", "sk-test")
        # Headers stored lowercase by Request.add_header's internals -> use .headers
        req = u.call_args.args[0]
        assert req.headers.get("Authorization".capitalize()) == "Bearer sk-test"
        assert req.headers.get("X-api-key") == "sk-test"
        assert req.headers.get("Anthropic-version") == "2023-06-01"

    def test_malformed_json_surfaces_as_fetch_error(self):
        resp = MagicMock()
        resp.read.return_value = b"<html>not json</html>"
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp):
            with pytest.raises(app.ModelFetchError) as exc:
                app.ModelFetcher.fetch("https://x.com/", "sk")
        msg = str(exc.value)
        assert "响应格式异常" in msg
        # Must NOT be wrapped as "未知错误: 响应格式异常: ..." — that's the bug we just fixed.
        assert "未知错误" not in msg

    def test_missing_data_field_surfaces_clean_error(self):
        """Bug fix: self-raised ModelFetchError must not be caught by except Exception."""
        resp = _resp({"not_data": []})
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp):
            with pytest.raises(app.ModelFetchError) as exc:
                app.ModelFetcher.fetch("https://x.com/", "sk")
        msg = str(exc.value)
        assert "响应格式异常" in msg
        assert "未知错误" not in msg

    def test_empty_data_list_surfaces_clean_error(self):
        resp = _resp({"data": []})
        with patch("claude_3p_gui.urllib.request.urlopen", return_value=resp):
            with pytest.raises(app.ModelFetchError) as exc:
                app.ModelFetcher.fetch("https://x.com/", "sk")
        assert "未知错误" not in str(exc.value)
