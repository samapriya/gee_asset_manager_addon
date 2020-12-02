__copyright__ = """

    Copyright 2020 Samapriya Roy

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
import csv
from bs4 import BeautifulSoup


def jsext(url, outfile):
    source = requests.get(url)
    html_content = source.text
    soup = BeautifulSoup(html_content, "html.parser")
    try:
        for articles in soup.find_all("script"):
            if not articles.string == None and articles.string.strip().startswith(
                "init"
            ):
                url = articles.string.strip().split('"')[1]
                if url.startswith("https"):
                    iscript = requests.get(url).json()
                    pt = iscript["path"]
                    if outfile == None:
                        print("\n")
                        print(
                            iscript["dependencies"][pt]
                            .encode("utf-8")
                            .decode("utf-8")
                            .strip()
                        )
                    else:
                        file = open(outfile, "w", encoding="utf-8")
                        file.write(str(iscript["dependencies"][pt]).strip())
                        file.close()
                        clean_lines = []
                        with open(outfile, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            clean_lines = [l.strip("\n") for l in lines if l.strip()]
                        with open(outfile, "w", encoding="utf-8") as f:
                            f.writelines("\n".join(clean_lines))
    except Exception as e:
        print(e)


# jsext(url='https://bullocke.users.earthengine.app/view/amazon',outfile=None)
# jsext(url='https://bullocke.users.earthengine.app/view/amazon')
