"""
Earth Engine App JavaScript Extractor

Retrieves and formats JavaScript code from Earth Engine applications.
"""

__copyright__ = """
    Copyright 2025 Samapriya Roy

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
__license__ = "Apache 2.0"

import json
import logging
from pathlib import Path
import unicodedata
from urllib.parse import urlparse

import jsbeautifier
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Try to import clipboard library
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EarthEngineJSExtractorError(Exception):
    """Custom exception for Earth Engine JS extraction errors."""
    pass


def create_session() -> requests.Session:
    """
    Create a requests session with retry logic.

    Returns:
        requests.Session: Configured session with retry strategy.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def validate_ee_url(url: str) -> tuple[str, str]:
    """
    Validate and parse Earth Engine app URL.

    Args:
        url: The Earth Engine app URL to validate.

    Returns:
        tuple: (base_url, app_id) extracted from the URL.

    Raises:
        EarthEngineJSExtractorError: If URL format is invalid.
    """
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        raise EarthEngineJSExtractorError(
            f"Invalid URL format: {url}. Must be a complete URL with scheme."
        )

    if "/view/" not in url:
        raise EarthEngineJSExtractorError(
            f"Invalid Earth Engine app URL: {url}. Must contain '/view/' path."
        )

    try:
        head, tail = url.split("/view/")
        return head, tail
    except ValueError:
        raise EarthEngineJSExtractorError(
            f"Could not parse URL: {url}. Expected format: https://user.earthengine.app/view/appname"
        )


def fetch_js_code(url: str, session: requests.Session | None = None) -> str:
    """
    Fetch JavaScript code from Earth Engine app.

    Args:
        url: The Earth Engine app URL.
        session: Optional requests session to use.

    Returns:
        str: The JavaScript code from the app.

    Raises:
        EarthEngineJSExtractorError: If fetching or parsing fails.
    """
    head, tail = validate_ee_url(url)
    fetch_url = f"{head}/javascript/{tail}-modules.json"

    logger.info(f"Fetching JavaScript from: {fetch_url}")

    if session is None:
        session = create_session()

    try:
        response = session.get(fetch_url, timeout=30)
        response.raise_for_status()

        # Explicitly set encoding if not detected properly
        if response.encoding is None or response.encoding.lower() not in ['utf-8', 'utf8']:
            response.encoding = 'utf-8'

    except requests.exceptions.Timeout:
        raise EarthEngineJSExtractorError(
            f"Request timeout while fetching from: {fetch_url}"
        )
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise EarthEngineJSExtractorError(
                f"App not found. Please verify the URL: {url}"
            )
        raise EarthEngineJSExtractorError(
            f"HTTP error {response.status_code}: {e}"
        )
    except requests.exceptions.RequestException as e:
        raise EarthEngineJSExtractorError(
            f"Error fetching JavaScript: {e}"
        )

    try:
        # Handle potential encoding issues when parsing JSON
        try:
            json_data = response.json()
        except UnicodeDecodeError:
            # Fallback: try to decode with error handling
            content = response.content.decode('utf-8', errors='replace')
            import json
            json_data = json.loads(content)

        dependencies = json_data.get("dependencies")
        script_path = json_data.get("path")

        if not dependencies or not script_path:
            raise EarthEngineJSExtractorError(
                "Invalid response format: missing 'dependencies' or 'path' fields"
            )

        if script_path not in dependencies:
            raise EarthEngineJSExtractorError(
                f"Script path '{script_path}' not found in dependencies"
            )

        js_code = dependencies[script_path]

        # Ensure the code is a string and handle potential encoding issues
        if not isinstance(js_code, str):
            js_code = str(js_code)

        return js_code

    except (KeyError, ValueError) as e:
        raise EarthEngineJSExtractorError(
            f"Error parsing response JSON: {e}"
        )


def sanitize_code(code: str, normalize_unicode: bool = False) -> str:
    """
    Sanitize JavaScript code to handle special characters and text issues.

    Args:
        code: The JavaScript code to sanitize.
        normalize_unicode: Whether to normalize Unicode characters (default: False).

    Returns:
        str: Sanitized JavaScript code.
    """
    # Remove null bytes that might cause issues
    code = code.replace('\x00', '')

    # Remove BOM (Byte Order Mark) if present
    if code.startswith('\ufeff'):
        code = code[1:]

    # Normalize line endings to Unix style
    code = code.replace('\r\n', '\n').replace('\r', '\n')

    # Optionally normalize Unicode characters (e.g., different dash types)
    if normalize_unicode:
        code = unicodedata.normalize('NFKC', code)

    # Remove or replace common problematic characters while preserving code
    # This is conservative - only handling truly problematic chars
    problematic_chars = {
        '\u200b': '',  # Zero-width space
        '\u200c': '',  # Zero-width non-joiner
        '\u200d': '',  # Zero-width joiner
        '\ufeff': '',  # Zero-width no-break space (BOM)
    }

    for char, replacement in problematic_chars.items():
        code = code.replace(char, replacement)

    return code


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to clipboard.

    Args:
        text: The text to copy to clipboard.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not CLIPBOARD_AVAILABLE:
        logger.warning(
            "pyperclip not installed. Install it with: pip install pyperclip"
        )
        return False

    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        logger.error(f"Failed to copy to clipboard: {e}")
        return False


def jsext(
    url: str,
    outfile: str | None = None,
    clipboard: bool = True,
    beautify: bool = True,
    indent_size: int = 2,
    normalize_unicode: bool = False,
    sanitize: bool = True
) -> str | None:
    """
    Extract and optionally save JavaScript code from an Earth Engine app.

    Args:
        url: URL of the Earth Engine app.
        outfile: Optional output file path for saving the JavaScript code.
                If None and clipboard is False, prints to stdout.
        clipboard: Whether to copy the code to clipboard (default: False).
        beautify: Whether to beautify the JavaScript code (default: True).
        indent_size: Indentation size for beautified code (default: 2).
        normalize_unicode: Whether to normalize Unicode characters (default: False).
        sanitize: Whether to sanitize the code for special characters (default: True).

    Returns:
        str: The JavaScript code if outfile is None, otherwise None.

    Raises:
        EarthEngineJSExtractorError: If extraction or file writing fails.
    """
    session = create_session()

    try:
        js_code = fetch_js_code(url, session)

        # Sanitize code if requested
        if sanitize:
            js_code = sanitize_code(js_code, normalize_unicode=normalize_unicode)

        if beautify:
            try:
                options = jsbeautifier.default_options()
                options.indent_size = indent_size
                js_code = jsbeautifier.beautify(js_code, options)
            except Exception as e:
                logger.warning(f"Beautification failed: {e}. Using original formatting.")

        # Handle clipboard copy
        if clipboard:
            if copy_to_clipboard(js_code):
                logger.info("JavaScript code copied to clipboard!")
            else:
                logger.warning("Failed to copy to clipboard. Falling back to print.")
                print(js_code)

        # Handle file output
        if outfile is not None:
            output_path = Path(outfile)

            # Create parent directories if they don't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write with explicit UTF-8 encoding and error handling
            try:
                with output_path.open('w', encoding='utf-8', errors='surrogateescape') as f:
                    f.write(js_code)
            except UnicodeEncodeError:
                # Fallback: write with error replacement
                logger.warning("Unicode encoding issue detected. Using replacement strategy.")
                with output_path.open('w', encoding='utf-8', errors='replace') as f:
                    f.write(js_code)

            logger.info(f"JavaScript code saved to: {output_path.resolve()}")

        # If neither clipboard nor outfile specified, print to stdout
        if not clipboard and outfile is None:
            print(js_code)

        return js_code

    except EarthEngineJSExtractorError:
        raise
    except OSError as e:
        raise EarthEngineJSExtractorError(
            f"Error writing to file '{outfile}': {e}"
        )
    except Exception as e:
        raise EarthEngineJSExtractorError(
            f"Unexpected error: {e}"
        )
    finally:
        session.close()


# def main():
#     """Example usage of the jsext function."""
#     # Example 1: Copy to clipboard
#     try:
#         jsext(
#             url='https://bullocke.users.earthengine.app/view/amazon',
#             clipboard=True
#         )
#     except EarthEngineJSExtractorError as e:
#         logger.error(f"Extraction failed: {e}")

#     # Example 2: Save to file
#     try:
#         jsext(
#             url='https://bullocke.users.earthengine.app/view/amazon',
#             outfile='output/amazon_app.js'
#         )
#     except EarthEngineJSExtractorError as e:
#         logger.error(f"Extraction failed: {e}")

#     # Example 3: Both clipboard and file
#     try:
#         jsext(
#             url='https://bullocke.users.earthengine.app/view/amazon',
#             outfile='output/amazon_app.js',
#             clipboard=True
#         )
#     except EarthEngineJSExtractorError as e:
#         logger.error(f"Extraction failed: {e}")


# if __name__ == "__main__":
#     main()
