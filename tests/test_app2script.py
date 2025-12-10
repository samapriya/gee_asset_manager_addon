import builtins
from unittest import mock

from geeadd import app2script
import jsbeautifier
import pytest
import requests
from requests import adapters
from urllib3.util import retry


def test_create_session():
    """Test create_session function."""
    session = app2script.create_session()
    assert isinstance(session, requests.Session)
    adapter = session.adapters.get("https://")
    assert isinstance(adapter, adapters.HTTPAdapter)
    retry_strategy = adapter.max_retries
    assert isinstance(retry_strategy, retry.Retry)
    assert retry_strategy.total == 3
    assert retry_strategy.backoff_factor == 1
    assert retry_strategy.status_forcelist == [429, 500, 502, 503, 504]
    session.close()


def test_validate_ee_url_valid():
    """Test validate_ee_url with a valid URL."""
    url = "https://user.earthengine.app/view/appname"
    head, tail = app2script.validate_ee_url(url)
    assert head == "https://user.earthengine.app"
    assert tail == "appname"


def test_validate_ee_url_valid_http():
    """Test validate_ee_url with a valid HTTP URL."""
    url = "http://user.earthengine.app/view/appname"
    head, tail = app2script.validate_ee_url(url)
    assert head == "http://user.earthengine.app"
    assert tail == "appname"


@pytest.mark.parametrize(
    "invalid_url",
    [
        "user.earthengine.app/view/appname",  # No scheme
        "https://user.earthengine.app/foo/appname",  # No /view/
        "/view/appname",  # No scheme or netloc
    ],
)
def test_validate_ee_url_invalid(invalid_url):
    """Test validate_ee_url with invalid URLs."""
    with pytest.raises(app2script.EarthEngineJSExtractorError):
        app2script.validate_ee_url(invalid_url)


@pytest.fixture
def mock_session_get():
    """Fixture to mock requests.Session.get."""
    with mock.patch.object(requests.Session, "get") as mock_get:
        yield mock_get


def test_fetch_js_code_success(mock_session_get):
    """Test fetch_js_code with a successful response."""
    mock_response = mock.Mock()
    mock_response.json.return_value = {
        "dependencies": {"main": "console.log('hello');"},
        "path": "main",
    }
    mock_response.raise_for_status.return_value = None
    mock_response.encoding = "utf-8"
    mock_session_get.return_value = mock_response

    url = "https://user.earthengine.app/view/appname"
    js_code = app2script.fetch_js_code(url)

    assert js_code == "console.log('hello');"
    mock_session_get.assert_called_once_with(
        "https://user.earthengine.app/javascript/appname-modules.json",
        timeout=30
    )


def test_fetch_js_code_404(mock_session_get):
    """Test fetch_js_code with a 404 response."""
    mock_response = mock.Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_session_get.return_value = mock_response

    url = "https://user.earthengine.app/view/appname"
    with pytest.raises(
        app2script.EarthEngineJSExtractorError, match="App not found"
    ):
        app2script.fetch_js_code(url)


def test_fetch_js_code_timeout(mock_session_get):
    """Test fetch_js_code with a timeout."""
    mock_session_get.side_effect = requests.exceptions.Timeout()

    url = "https://user.earthengine.app/view/appname"
    with pytest.raises(
        app2script.EarthEngineJSExtractorError, match="Request timeout"
    ):
        app2script.fetch_js_code(url)


def test_fetch_js_code_http_error(mock_session_get):
    """Test fetch_js_code with a non-404 HTTP error."""
    mock_response = mock.Mock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_session_get.return_value = mock_response

    url = "https://user.earthengine.app/view/appname"
    with pytest.raises(
        app2script.EarthEngineJSExtractorError, match="HTTP error 500"
    ):
        app2script.fetch_js_code(url)


def test_fetch_js_code_invalid_json(mock_session_get):
    """Test fetch_js_code with invalid JSON response."""
    mock_response = mock.Mock()
    mock_response.json.side_effect = ValueError()
    mock_response.raise_for_status.return_value = None
    mock_response.encoding = "utf-8"
    mock_session_get.return_value = mock_response

    url = "https://user.earthengine.app/view/appname"
    with pytest.raises(
        app2script.EarthEngineJSExtractorError,
        match="Error parsing response JSON"
    ):
        app2script.fetch_js_code(url)


def test_fetch_js_code_missing_fields(mock_session_get):
    """Test fetch_js_code with JSON missing 'dependencies'."""
    mock_response = mock.Mock()
    mock_response.json.return_value = {"path": "main"}
    mock_response.raise_for_status.return_value = None
    mock_response.encoding = "utf-8"
    mock_session_get.return_value = mock_response

    url = "https://user.earthengine.app/view/appname"
    with pytest.raises(
        app2script.EarthEngineJSExtractorError,
        match="Invalid response format",
    ):
        app2script.fetch_js_code(url)


def test_fetch_js_code_path_not_in_dependencies(mock_session_get):
    """Test fetch_js_code where path is not in dependencies."""
    mock_response = mock.Mock()
    mock_response.json.return_value = {
        "dependencies": {"other": "code"},
        "path": "main",
    }
    mock_response.raise_for_status.return_value = None
    mock_response.encoding = "utf-8"
    mock_session_get.return_value = mock_response

    url = "https://user.earthengine.app/view/appname"
    with pytest.raises(
        app2script.EarthEngineJSExtractorError,
        match="Script path 'main' not found",
    ):
        app2script.fetch_js_code(url)


def test_sanitize_code_null_bytes():
    """Test sanitize_code removes null bytes."""
    code = "var x = 1;\x00var y = 2;"
    sanitized = app2script.sanitize_code(code)
    assert "\x00" not in sanitized
    assert sanitized == "var x = 1;var y = 2;"


def test_sanitize_code_bom():
    """Test sanitize_code removes BOM."""
    code = "\ufeffvar x = 1;"
    sanitized = app2script.sanitize_code(code)
    assert not sanitized.startswith("\ufeff")
    assert sanitized == "var x = 1;"


def test_sanitize_code_line_endings():
    """Test sanitize_code normalizes line endings."""
    code = "var x = 1;\r\nvar y = 2;\rvar z = 3;"
    sanitized = app2script.sanitize_code(code)
    assert sanitized == "var x = 1;\nvar y = 2;\nvar z = 3;"


def test_sanitize_code_problematic_chars():
    """Test sanitize_code removes problematic Unicode characters."""
    code = "var x = 1;\u200b\u200c\u200d\ufeff"
    sanitized = app2script.sanitize_code(code)
    assert sanitized == "var x = 1;"


def test_sanitize_code_unicode_normalization():
    """Test sanitize_code with Unicode normalization."""
    code = "var s = '−';"  # Using U+2212 MINUS SIGN
    sanitized = app2script.sanitize_code(code, normalize_unicode=True)
    # Should normalize to U+002D HYPHEN-MINUS
    assert sanitized == "var s = '-';"


@mock.patch.object(app2script, "pyperclip", create=True)
def test_copy_to_clipboard_success(mock_pyperclip):
    """Test copy_to_clipboard with pyperclip available and successful copy."""
    with mock.patch("geeadd.app2script.CLIPBOARD_AVAILABLE", True):
        result = app2script.copy_to_clipboard("test text")
        assert result
        mock_pyperclip.copy.assert_called_once_with("test text")


@mock.patch.object(app2script, "pyperclip", create=True)
def test_copy_to_clipboard_failure(mock_pyperclip):
    """Test copy_to_clipboard with pyperclip available but copy fails."""
    mock_pyperclip.copy.side_effect = Exception("Copy failed")
    with mock.patch("geeadd.app2script.CLIPBOARD_AVAILABLE", True):
        result = app2script.copy_to_clipboard("test text")
        assert not result
        mock_pyperclip.copy.assert_called_once_with("test text")


def test_copy_to_clipboard_unavailable():
    """Test copy_to_clipboard with pyperclip unavailable."""
    with mock.patch("geeadd.app2script.CLIPBOARD_AVAILABLE", False):
        result = app2script.copy_to_clipboard("test text")
        assert not result


@mock.patch.object(app2script, "fetch_js_code")
@mock.patch.object(app2script, "sanitize_code")
@mock.patch.object(jsbeautifier, "beautify")
@mock.patch.object(app2script, "copy_to_clipboard")
class TestJsext:
    """Tests for the jsext function."""

    def test_jsext_clipboard_success(
        self,
        mock_copy,
        mock_beautify,
        mock_sanitize,
        mock_fetch,
    ):
        """Test jsext with clipboard output."""
        mock_fetch.return_value = "raw_code"
        mock_sanitize.return_value = "sanitized_code"
        mock_beautify.return_value = "beautified_code"
        mock_copy.return_value = True

        result = app2script.jsext("http://test.url/view/app")
        assert result == "beautified_code"
        mock_fetch.assert_called_once()
        mock_sanitize.assert_called_once_with(
            "raw_code", normalize_unicode=False
        )
        mock_beautify.assert_called_once_with("sanitized_code", mock.ANY)
        mock_copy.assert_called_once_with("beautified_code")

    def test_jsext_outfile_success(
        self, mock_copy, mock_beautify, mock_sanitize, mock_fetch, tmp_path
    ):
        """Test jsext with file output."""
        mock_fetch.return_value = "raw_code"
        mock_sanitize.return_value = "sanitized_code"
        mock_beautify.return_value = "beautified_code"
        outfile = tmp_path / "output.js"

        result = app2script.jsext(
            "http://test.url/view/app", outfile=str(outfile), clipboard=False
        )
        assert result == "beautified_code"
        mock_fetch.assert_called_once()
        mock_sanitize.assert_called_once()
        mock_beautify.assert_called_once()
        mock_copy.assert_not_called()
        assert outfile.read_text() == "beautified_code"

    def test_jsext_no_beautify_no_sanitize(
        self, mock_copy, mock_beautify, mock_sanitize, mock_fetch
    ):
        """Test jsext without beautify and sanitize."""
        mock_fetch.return_value = "raw_code"
        mock_copy.return_value = True

        result = app2script.jsext(
            "http://test.url/view/app", beautify=False, sanitize=False
        )
        assert result == "raw_code"
        mock_fetch.assert_called_once()
        mock_sanitize.assert_not_called()
        mock_beautify.assert_not_called()
        mock_copy.assert_called_once_with("raw_code")

    @mock.patch.object(builtins, "print")
    def test_jsext_stdout(
        self, mock_print, mock_copy, mock_beautify, mock_sanitize, mock_fetch
    ):
        """Test jsext prints to stdout when no outfile and clipboard fails."""
        mock_fetch.return_value = "raw_code"
        mock_sanitize.return_value = "sanitized_code"
        mock_beautify.return_value = "beautified_code"
        mock_copy.return_value = False  # Simulate clipboard failure

        result = app2script.jsext("http://test.url/view/app", outfile=None)
        assert result == "beautified_code"
        mock_copy.assert_called_once_with("beautified_code")
        mock_print.assert_called_once_with("beautified_code")

    def test_jsext_fetch_error(
        self, mock_copy, mock_beautify, mock_sanitize, mock_fetch
    ):
        """Test jsext when fetch_js_code raises an error."""
        mock_fetch.side_effect = app2script.EarthEngineJSExtractorError(
            "Fetch failed")

        with pytest.raises(app2script.EarthEngineJSExtractorError,
                           match="Fetch failed"):
            app2script.jsext("http://test.url/view/app")

        mock_sanitize.assert_not_called()
        mock_beautify.assert_not_called()
        mock_copy.assert_not_called()
