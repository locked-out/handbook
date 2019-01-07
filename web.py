from urllib.request import urlopen, Request
from bs4 import BeautifulSoup as bs
from time import sleep
import json
import re

list_url = 'http://legacy.handbook.unsw.edu.au/vbook2018/brCoursesBySubjectArea.jsp?studyArea=COMP&StudyLevel=Undergraduate'

with urlopen(Request(list_url)) as f:
    html = f.read().decode('utf-8')
soup = bs(html, 'lxml')
table = soup.find('table', 'tabluatedInfo')
links = table.find_all('a')

data = {}

for link in links:

    url = link.attrs['href']
    sleep(0.2)

    with urlopen(Request(url)) as f:
        html = f.read().decode('utf-8')

    soup = bs(html, 'lxml')
    summary = soup.find('div', 'summary')
    title = summary.find_previous_sibling()
    name, code = title.text.rsplit("-", 1)

    name = name.strip()
    code = code.strip()

    info = {}
    info["name"] = name

    for child in summary.findChildren(recursive=False):
        text = child.text
        try:
            label, value = text.split(":", 1)
        except ValueError:
            pass
        else:
            info[label.strip().lower()] = value.strip()

    data[code] = info

with open('data.json', 'w') as outfile:
    json.dump(data, outfile)
