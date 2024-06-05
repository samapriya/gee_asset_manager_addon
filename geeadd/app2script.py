__copyright__ = """

    Copyright 2024 Samapriya Roy

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
import requests
import jsbeautifier


def jsext(url, outfile):
    """
    Retrieve the application script from an Earth Engine app.

    Args:
        url (str): URL of the Earth Engine app.
        outfile (str, optional): Output file path for saving the JavaScript code.

    """
    head, tail = url.split("/view/")
    fetch_url = f"{head}/javascript/{tail}-modules.json"
    source_fetch = requests.get(
        fetch_url,
    )
    if source_fetch.status_code == 200:
        js_code = source_fetch.json()["dependencies"]
        script_path = source_fetch.json()["path"]
        js_code = js_code[script_path]

    formatted_code = jsbeautifier.beautify(js_code)
    try:
        if outfile == None:
            print(formatted_code)
        else:
            with open(outfile, 'w') as f:
                f.write(formatted_code)
    except Exception as e:
        print(e)


# jsext(url='https://bullocke.users.earthengine.app/view/amazon',outfile=None)
# jsext(url='https://bullocke.users.earthengine.app/view/amazon')
