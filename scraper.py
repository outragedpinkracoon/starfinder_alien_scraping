import requests
import re
import json
from bs4 import BeautifulSoup
from functools import reduce

PAGE_URL = 'http://glasstopgames.com/sfrpg/alien-list.html'
ROOT_URL = 'http://glasstopgames.com'

page = requests.get(PAGE_URL)
content = page.text

soup = BeautifulSoup(content, 'html.parser')
links = soup.table.find_all('a')

all_monster_links = [
    (lambda tag, url: url+tag['href'])(tag, ROOT_URL)
    for tag in links
]

arch_type_links = [href for href in all_monster_links if "#" not in href]

individual_monster_pages = [
    (lambda url: requests.get(url).text)(url)
    for url in [arch_type_links[2]]
]


def stat_block(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.find_all('section', class_='stat-block')

stat_block_by_arch_type = [
    stat_block(page)
    for page in [individual_monster_pages[0]]
]

monster_stat_blocks = reduce(lambda x, y: x+y, stat_block_by_arch_type)


def monster_hp(stat_block):
    hp_container = stat_block.find('span', text=re.compile('HP'))
    stripped_hp = hp_container.parent.text.strip('HP ').split(';')[0]
    return int(stripped_hp)


def monster_cr(stat_block):
    cr_container = stat_block.find('span', class_='challenge-rating').text
    stripped_cr = cr_container.strip('CR ')

    if '/' in stripped_cr:
        return cr_from_parts(stripped_cr)
    elif '-' in stripped_cr:
        return 2
    else:
        return int(stripped_cr)


def cr_from_parts(value):
    parts = value.split('/')
    numeric_parts = [(lambda x: int(x))(x) for x in parts]
    divided = numeric_parts[0] / numeric_parts[1]
    return "{0:.2f}".format(divided)


def monster_exp(stat_block):
    exp = stat_block.find('strong').text

    if 'XP' in exp:
        return int(exp.strip('XP ').replace(',', ''))
    else:
        return 600


def monster_type(monster_attributes, stat_block):
    type_container = stat_block.find_all('p')
    index = 1
    if 'constituent' in monster_attributes['name']:
        index = 0

    type_text = type_container[index].text
    update_type_parts(type_text, monster_attributes)


def build_monster_attributes(stat_block, id):
    monster_attributes = {}

    monster_attributes['id'] = id

    monster_attributes['name'] = stat_block.h2.text

    monster_attributes['hp'] = monster_hp(stat_block)

    monster_attributes['cr'] = monster_cr(stat_block)

    monster_attributes['exp'] = monster_exp(stat_block)

    monster_type(monster_attributes, stat_block)

    return monster_attributes


def update_type_parts(value, result):
    parts = value.split(' ')
    if len(parts) == 3:
        result['alignment'] = parts[0].upper()
        result['size'] = parts[1].title()
        result['type'] = parts[2].title()
        return result
    if '(' in parts[3]:
        result['alignment'] = parts[0].upper()
        result['size'] = parts[1].title()
        result['type'] = parts[2].title()
        return result
    if len(parts) == 4:
        result['alignment'] = parts[0].upper()
        result['size'] = parts[1].title()
        result['type'] = parts[3].title()
        return result

bullshit = [
    build_monster_attributes(stat_block, index + 1)
    for index, stat_block in enumerate(monster_stat_blocks)
]

with open('monsters_hp.json', 'w') as outfile:
    json.dump(bullshit, outfile)
