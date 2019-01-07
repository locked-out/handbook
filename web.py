from urllib.request import urlopen, Request
from bs4 import BeautifulSoup as bs
from time import sleep
import json
import re

list_url = 'http://legacy.handbook.unsw.edu.au/vbook2018/brCoursesBySubjectArea.jsp?studyArea=COMP&StudyLevel=Undergraduate'

with urlopen(Request(list_url)) as f:
    html = f.read().decode('utf-8')
soup = bs(html, 'html')
table = soup.find('table', 'tabluatedInfo')
links = table.find_all('a')

data = {}

for link in links:
    url = link.attrs['href']
    code = re.search(r"/(\w*)\.html", url).group(1)
    sleep(0.5)

    with urlopen(Request(url)) as f:
        html = f.read().decode('utf-8')

    soup = bs(html, 'html')
    summary = soup.find('div', 'summary')
    info = {}

    for child in summary.findChildren(recursive=False):
        text = child.text
        try:
            label, value = text.split(":", 1)
        except ValueError:
            pass
        else:
            info[label.strip()] = value.strip()

    data[code] = info

with open('data.json', 'w') as outfile:
    json.dump(data, outfile)
