import requests
import re
import json
from bs4 import BeautifulSoup
from functools import reduce


def main():
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
        for url in arch_type_links
    ]

    stat_block_by_arch_type = [
        stat_block(page)
        for page in individual_monster_pages
    ]

    monster_stat_blocks = reduce(lambda x, y: x+y, stat_block_by_arch_type)

    full_monster_list = [
        build_monster_attributes(stat_block, index + 1)
        for index, stat_block in enumerate(monster_stat_blocks)
    ]

    with open('monsters_hp.json', 'w') as outfile:
        json.dump(full_monster_list, outfile)

    print(full_monster_list)


def stat_block(content):
    soup = BeautifulSoup(content, 'html.parser')
    return soup.find_all('section', class_='stat-block')


def monster_hp(line_text):
    stripped_hp = line_text.strip('HP ').split(';')[0]
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


def monster_exp(stat_line):
    if 'XP' in stat_line:
        return int(stat_line.strip('XP ').replace(',', ''))
    else:
        return 600


def monster_type(monster_attributes, line_parts):
    index = 1
    if 'constituent' in monster_attributes['name']:
        index = 0
    update_type_parts(line_parts, monster_attributes)


def monster_ac(monster_attributes, line_text):
    line_parts = line_text.split(';')
    print(monster_attributes)
    print(line_parts)
    monster_attributes['eac'] = line_parts[0].strip('EAC ')
    monster_attributes['kac'] = line_parts[1].strip(' KAC')


def monster_stats(monster_attributes, line_text):
    line_parts = line_text.split(';')

    # any of these could be a dash
    monster_attributes['str'] = line_parts[0].strip('Str +')
    monster_attributes['dex'] = line_parts[1].strip('Dex +')
    monster_attributes['con'] = line_parts[2].strip('Con +')
    monster_attributes['int'] = line_parts[3].strip('Int +')
    monster_attributes['wis'] = line_parts[4].strip('Wis +')
    monster_attributes['cha'] = line_parts[5].strip('Cha +')


def update_type_parts(parts, result):
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


def attach_xp(monster_attributes, line_text):
    if 'XP' in line_text:
        monster_attributes['exp'] = monster_exp(line_text)


def attach_alignment_etc(monster_attributes, line_text, stat_block):
    alignments = ["LG", "NG", "CG", "LN", "N", "CN", "LE", "NE", "CE"]
    line_parts = line_text.split(' ')

    if line_parts[0].upper() in alignments:
        monster_type(monster_attributes, line_parts)


def attach_hp(monster_attributes, line_text):
    if 'HP' in line_text and 'hp' not in monster_attributes:
        monster_attributes['hp'] = monster_hp(line_text)


def attach_id(monster_attributes, index):
    monster_attributes['id'] = index + 1


def attach_cr(monster_attributes, stat_block):
    monster_attributes['cr'] = monster_cr(stat_block)


def attach_name(monster_attributes, stat_block):
    monster_attributes['name'] = stat_block.h2.text


def attach_ac(monster_attributes, line_text):
    if 'EAC' in line_text and 'eac' not in monster_attributes:
        monster_ac(monster_attributes, line_text)


def attach_stats(monster_attribues, line_text):
    if 'Str' in line_text:
        monster_stats(monster_attribues, line_text)


def build_monster_attributes(stat_block, id):
    stat_lines = stat_block.find_all('p', class_='stat-line')
    monster_attributes = {}

    attach_name(monster_attributes, stat_block)

    for index, line in enumerate(stat_lines):
        line_text = line.text

        attach_id(monster_attributes, index)
        attach_cr(monster_attributes, stat_block)
        attach_xp(monster_attributes, line_text)
        attach_alignment_etc(monster_attributes, line_text, stat_block)
        attach_hp(monster_attributes, line_text)
        attach_ac(monster_attributes, line_text)
        attach_stats(monster_attributes, line_text)

    return monster_attributes

if __name__ == '__main__':
    main()
