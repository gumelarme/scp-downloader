import os
import re
from typing import List, Dict
from dataclasses import dataclass, field

import requests as req
from bs4 import BeautifulSoup

class_indicator = "Object Class:"
index_indicator = "Item #:"

SCP_TITLE = re.compile('SCP-(\d+)\s?-\s?(.+)')
BASE_URL = 'http://www.scp-wiki.net/'
MAXLEN_INLINE_SECTION = 35

@dataclass
class SCPInfo:
    index: int
    title: str
    link: str
    object_class: str = '<unknown>'
    sections:  Dict = field(default_factory=dict)

    def get_friendly_title(self):
        return "SCP-{:>03} {}".format(self.index, self.title)

    def __str__(self):
        return "{} [{}]".format(
            self.get_friendly_title(),
            self.link
            )

    def to_md(self):
        text = "## {}\n```Object Class: {}```\n".format(
            self.get_friendly_title(),
            self.object_class
        )

        section_text = []
        for section in self.sections:
            subtitle = f"**{section[0]}**"
            paragraph = "\n".join(section[1:])

            if len(subtitle + paragraph) <= MAXLEN_INLINE_SECTION:
                section_text.append(subtitle + " "+ paragraph + "\n")
            else:
                section_text.append(subtitle + "<br/>" + paragraph + "\n")

        return "\n".join([text, *section_text])



def get_scp_info(series=1) -> List[SCPInfo]:
    URL = BASE_URL+'scp-series' + ('' if series == 1 else f'-{series}')
    html = req.get(URL)
    bs = BeautifulSoup(html.text, 'html.parser')
    toc = bs.select("div.content-panel.standalone.series > ul li")

    articles :List[SCPInfo] = []
    for li in toc:
        re_result = SCP_TITLE.match(li.text)

        if not re_result:
            continue

        index = int(re_result.group(1))
        title = re_result.group(2)
        articles += [SCPInfo(index, title, li.find('a', href=True)['href'])]

    return articles

def parse_article(text) -> Dict:
    scp = {}
    bs = BeautifulSoup(text, 'html.parser')
    scp['class'] = '<unknown>'
    scp['sections'] = []
    cursection = ''
    for p in bs.select('div#page-content > p'):
        # sections
        if bold := p.find('strong'):
            content = p.find(text=True, recursive=False)
            content = strip_colon(content) if content is not None else ''


            if bold.text == class_indicator:
                scp['class'] = content
            else:
                scp['sections'].append([bold.text, content])
                cursection = len(scp['sections']) - 1

        # paragraph
        else:
            x = strip_colon(p.text)
            scp['sections'][cursection].append(x)


    return scp

def strip_colon(text: str):
    result = text if text != None else ''

    if result.startswith(':'):
        result = result[1:].strip()

    return result

series_num = 1
filepath = 'dist/series-{}'
for scp in get_scp_info(series_num)[1:50]:
    try:
        scpurl = BASE_URL + scp.link
        html = req.get(scpurl)
        parsed = parse_article(html.text)

        scp.object_class = parsed['class']

        if parsed['sections'][0][0] == index_indicator:
            scp.sections = parsed['sections'][1:]
        else:
            scp.sections = parsed['sections']


        folder = filepath.format(series_num)
        os.makedirs(folder, exist_ok=True)
        with open(f'{folder}/{scp.index:>03}.md', 'w+') as f:
            f.write(scp.to_md())

        print(f'SCP-{scp.index} =====> DONE')
    except Exception as e:
        print(f'Failed obtaining {scp.index}. Skipping.')
        continue
