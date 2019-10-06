import requests
from bs4 import BeautifulSoup


def jsext(url,outfile):
    source = requests.get(url).text
    soup = BeautifulSoup(source ,'lxml')

    for article in soup.find_all('script'):
        try:
            if (article.text.strip()).startswith('init'):
                url=article.text.strip().split('"')[3]
                if url.startswith('https'):
                    iscript=requests.get(url).json()
                    pt=iscript['path']
                    if outfile==None:
                        print('\n')
                        print(iscript['dependencies'][pt].encode('utf-8').strip())
                    else:
                        file=open(outfile, 'w')
                        file.write(iscript['dependencies'][pt].encode('utf-8').strip())
                        file.close()
                        clean_lines = []
                        with open(outfile, "r") as f:
                            lines = f.readlines()
                            clean_lines = [l.strip() for l in lines if l.strip()]
                        with open(outfile, "w") as f:
                            f.writelines('\n'.join(clean_lines))
        except Exception as e:
            print(e)
#jsext(url='https://globalfires.earthengine.app/view/gfedv4s-monthly-ba-animated')
#jsext(url='https://bullocke.users.earthengine.app/view/amazon')

