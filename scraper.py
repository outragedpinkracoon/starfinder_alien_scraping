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

monster_stuff = [
    (lambda tag, url: url+tag['href'])(tag, ROOT_URL)
    for tag in links
]

monster_filter = [href for href in monster_stuff if "#" not in href]

individual_monster_pages = [
    (lambda url: requests.get(url).text)(url)
    for url in [monster_filter[3]]
]


def find_the_thing(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.find_all('section', class_='stat-block')

monster_stats = [
    find_the_thing(page)
    for page in [individual_monster_pages[0]]
]

flattened_stats = reduce(lambda x, y: x+y, monster_stats)


def build_result(thing, id):
    result = {}

    result['id'] = id

    result['name'] = thing.h2.text
    print(result['name'])

    hp_container = thing.find('span', text=re.compile('HP'))
    stripped_hp = hp_container.parent.text.strip('HP ').split(';')[0]
    result['hp'] = int(stripped_hp)

    cr_container = thing.find('span', class_='challenge-rating').text
    stripped_cr = cr_container.strip('CR ')

    if '/' in stripped_cr:
        result['cr'] = get_cr(stripped_cr)
    elif '-' in stripped_cr:
        result['cr'] = 2
    else:
        result['cr'] = int(stripped_cr)

    exp = thing.find('strong').text

    if 'XP' in exp:
        result['exp'] = int(exp.strip('XP ').replace(',', ''))
    else:
        result['exp'] = 600

    type_container = thing.find_all('p')
    index = 1
    if 'constituent' in result['name']:
        index = 0

    type_stuff = type_container[index].text
    get_type_parts(type_stuff, result)

    return result


def get_type_parts(value, result):
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


def get_cr(value):
    parts = value.split('/')
    numeric_parts = [(lambda x: int(x))(x) for x in parts]
    divided = numeric_parts[0] / numeric_parts[1]
    return "{0:.2f}".format(divided)

bullshit = [
    build_result(thing, index + 1)
    for index, thing in enumerate(flattened_stats)
]

# with open('monsters_hp.json', 'w') as outfile:
#     json.dump(bullshit, outfile)

print(bullshit)




# for url in monster_filter:
#     page = requests.get(url)
#     page.text
