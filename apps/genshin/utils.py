import os
import re
from typing import Dict, List, Literal, Tuple, Union

import aiohttp
from discord import Embed, Locale
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from data.game.elements import convert_elements
from data.game.artifacts import artifacts_map
from data.game.characters import characters_map
from data.game.consumables import consumables_map
from data.game.fight_prop import fight_prop
from data.game.weapons import weapons_map
from dotenv import load_dotenv

import genshin

from utility.utils import default_embed, get_weekday_int_with_name

load_dotenv()

def get_dummy_client() -> genshin.Client:
    cookies = {"ltuid": os.getenv('ltuid'),
               "ltoken": os.getenv('ltoken')}
    client = genshin.Client(cookies)
    client.lang = "zh-tw"
    client.default_game = genshin.Game.GENSHIN
    client.uids[genshin.Game.GENSHIN] = 901211014
    return client

def calculate_artifact_score(substats: dict):
    tier_four_val = {
        'FIGHT_PROP_HP': 1196,
        'FIGHT_PROP_HP_PERCENT': 5.8,
        'FIGHT_PROP_ATTACK': 76,
        'FIGHT_PROP_ATTACK_PERCENT': 5.8,
        'FIGHT_PROP_DEFENSE': 92,
        'FIGHT_PROP_DEFENSE_PERCENT': 7.3,
        'FIGHT_PROP_CHARGE_EFFICIENCY': 6.5,
        'FIGHT_PROP_ELEMENT_MASTERY': 23,
        'FIGHT_PROP_CRITICAL': 3.9,
        'FIGHT_PROP_CRITICAL_HURT': 7.8
    }
    result = 0
    for sub, val in substats.items():
        result += val/tier_four_val.get(sub)*11
    return result

async def get_farm_dict(session: aiohttp.ClientSession, locale: str | Locale) -> dict:
    ambr_top_locale = to_ambr_top(locale)
    async with session.get(f'https://api.ambr.top/v2/{ambr_top_locale}/dailyDungeon?vh=28R6') as r:
        daily_dungeon = await r.json()
    async with session.get('https://api.ambr.top/v2/static/upgrade?vh=28R6') as r:
        upgrade = await r.json()
    upgrade = upgrade['data']
    daily_dungeon = daily_dungeon['data']

    # get a dict of rewards first
    rewards = {}
    for weekday, domains in daily_dungeon.items():
        for domain, domain_info in domains.items():
            for reward_id in domain_info['reward']:
                if len(str(reward_id)) == 6:  # exclude mora and other stuff
                    if str(reward_id) not in rewards:
                        rewards[str(reward_id)] = {
                            'domain_id': domain_info['id'], 'domain_city': domain_info['city'], 'weekday': []}
                    if get_weekday_int_with_name(weekday) not in rewards[str(reward_id)]['weekday']:
                        rewards[str(reward_id)]['weekday'].append(
                            get_weekday_int_with_name(weekday))

    result = {'avatar': {}, 'weapon': {}}

    # then, organize the rewards according to characters
    for avatar_id, avatar_info in upgrade['avatar'].items():
        if 'beta' in avatar_info:  # skip beta characters
            continue
        result['avatar'][avatar_id] = {}
        for item_id, item_rarity in avatar_info['items'].items():
            if avatar_id not in result['avatar']:
                result['avatar'][avatar_id] = {}
            if item_id in rewards:
                result['avatar'][avatar_id][item_id] = rewards[item_id]

    # as well as weapons
    for weapon_id, weapon_info in upgrade['weapon'].items():
        if 'beta' in weapon_info:  # skip beta weapons
            continue
        result['weapon'][weapon_id] = {}
        for item_id, item_rarity in weapon_info['items'].items():
            if item_id in rewards:
                result['weapon'][weapon_id][item_id] = rewards[item_id]

    # "15509": {
    #     "114029": {
    #         "domain_id": 4353,
    #         "domain_city": 3,
    #         "weekday": 6
    #     },
    #     "114030": {
    #         "domain_id": 4353,
    #         "domain_city": 3,
    #         "weekday": 6
    #     }
    # }

    return result, daily_dungeon


async def get_all_non_beta_characters(session: aiohttp.ClientSession, locale: Literal['Locale', 'str']) -> dict:
    """Returns all genshin non-beta characters in the given ambr.top locale, elements are converted (i.e. from ice to cryo)

    Args:
        session (aiohttp.ClientSession): the aiohttp session
        locale (Literal['Locale', 'str']): the ambr.top locale
        user_locale (str): used to override the default locale if needed

    Returns:
        dict: a dict of all characters with their rarity, element, and name (from the textMap using the given locale)
    """

    ambr_top_locale = to_ambr_top(locale)
    async with session.get(f'https://api.ambr.top/v2/{ambr_top_locale}/avatar') as r:
        avatars = await r.json()
    avatars = avatars['data']['items']

    result = {}
    for avatar_id, avatar_info in avatars.items():
        result[avatar_id] = {
            'rank': avatar_info['rank'], 'element': convert_elements.get(avatar_info['element']),
            'name': text_map.get_character_name(avatar_id, locale)
        }

    return result


def get_character_builds(character_id: int, element_builds_dict: dict, locale: Locale, user_locale: str) -> Tuple[List[Union[Embed, str, str]], bool]:
    """Gets a character's builds

    Args:
        character_id (int): the id of the character
        element_builds_dict (dict): the dictionary of all characters of a given element, this is stored in data/builds
        locale (Locale): the discord locale 
        user_locale (str): the user locale

    Returns:
        Tuple[List[Embed], bool]: returns a list of lists of embeds, weapons, and artifacts of different builds + a boolean that indicates whether the character has artifact thoughts
    """
    character_name = text_map.get_character_name(character_id, 'zh-TW', None)
    translated_character_name = text_map.get_character_name(
        character_id, locale, user_locale)
    count = 1
    has_thoughts = False
    result = []

    for build in element_builds_dict[character_name]['builds']:
        statStr = ''
        for stat, value in build['stats'].items():
            statStr += f'{stat} ➜ {value}\n'
        embed = default_embed(
            f'{translated_character_name} - {text_map.get(90, locale, user_locale)}{count}',
            f"{text_map.get(91, locale, user_locale)} • {get_weapon(name=build['weapon'])['emoji']} {build['weapon']}\n"
            f"{text_map.get(92, locale, user_locale)} • {build['artifacts']}\n"
            f"{text_map.get(93, locale, user_locale)} • {build['main_stats']}\n"
            f"{text_map.get(94, locale, user_locale)} • {build['talents']}\n"
            f"{build['move']} • {build['dmg']}\n\n"
        )
        embed.add_field(
            name=text_map.get(95, locale, user_locale),
            value=statStr
        )
        count += 1
        embed.set_thumbnail(
            url=get_character(character_id)["icon"])
        embed.set_footer(
            text=f'[{text_map.get(96, locale, user_locale)}](https://bbs.nga.cn/read.php?tid=25843014)')
        result.append([embed, build['weapon'], build['artifacts']])

    if 'thoughts' in element_builds_dict[character_name]:
        has_thoughts = True
        count = 1
        embed = default_embed(text_map.get(97, locale, user_locale))
        for thought in element_builds_dict[character_name]['thoughts']:
            embed.add_field(name=f'#{count}',
                            value=thought, inline=False)
            count += 1
        embed.set_thumbnail(
            url=get_character(character_id)["icon"])
        result.append([embed, text_map.get(97, locale, user_locale), ''])

    return result, has_thoughts


def check_level_validity(levels: Dict[str, str], locale: Literal['Locale', 'str']) -> Tuple[bool, str]:
    for level_type, level in levels.items():
        if not level.isnumeric():
            return False, text_map.get(187, locale)
        if (level_type == 'current' or level_type == 'target') and (int(level) > 90 or int(level) < 1):
            return False, text_map.get(188, locale)
        if (level_type == 'a' or level_type == 'e' or level_type == 'q') and (int(level) > 10 or int(level) < 1):
            return False, text_map.get(189, locale)
    return True, ''

def trim_cookie(cookie: str) -> str:
    try:
        new_cookie = [
            int(re.search(
                r'\d+', (re.search('ltuid=[0-9]{3,}', cookie).group())).group()),
            re.search('[0-9A-Za-z]{20,}', cookie).group(),
            (re.search('cookie_token=[0-9A-Za-z]{20,}', cookie).group())[13:]
        ]
    except:
        new_cookie = None
    return new_cookie

def get_element(element: str):
    elements = {
        '風': {'emoji': '<:WIND_ADD_HURT:982138235239137290>', 'eng': 'Anemo', 'name': '風'},
        '冰': {'emoji': '<:ICE_ADD_HURT:982138229140635648>', 'eng': 'Cryo', 'name': '冰'},
        '雷': {'emoji': '<:ELEC_ADD_HURT:982138220248711178>', 'eng': 'Electro', 'name': '雷'},
        '岩': {'emoji': '<:ROCK_ADD_HURT:982138232391237632>', 'eng': 'Geo', 'name': '岩'},
        '水': {'emoji': '<:WATER_ADD_HURT:982138233813098556>', 'eng': 'Hydro', 'name': '水'},
        '火': {'emoji': '<:FIRE_ADD_HURT:982138221569900585>', 'eng': 'Pyro', 'name': '火'}
    }
    for element_name, element_info in elements.items():
        if element_name == element or element_info['eng'] == element or element_info['eng'].lower() == element:
            return element_info


def get_character(id: int = '', name: str = '', eng: str = ''):
    for character_id, character_info in characters_map.items():
        if str(id) == character_id or character_info['name'] == name or character_info['eng'] == eng:
            return character_info
    # print(f'Invalid character {id}{name}')
    return {'name': f'{id}{name}{eng}', 'element': 'Cryo', 'rarity': 5, 'icon': 'https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png', 'emoji': '<:WARNING:992552271378386944>', 'eng': 'Unknown'}


def get_weapon(id: int = '', name: str = ''):
    for weapon_id, weapon_info in weapons_map.items():
        if weapon_id == str(id) or weapon_info['name'] == name:
            return weapon_info
    # print(f'Invalid weapon {id}{name}')
    return {'name': f'{id}{name}', 'emoji': '⚠️', 'rarity': 5, 'icon': 'https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png', 'eng': 'Unknown'}


def get_material(id: int = '', name: str = ''):
    for consumable_id, consumable_info in consumables_map.items():
        if consumable_id == str(id) or consumable_info['name'] == name:
            return consumable_info
    return {'name': '自訂素材', 'emoji': '<:white_star:982456919224615002>'}


def get_artifact(id: int = '', name: str = ''):
    for artifact_id, artifact_info in artifacts_map.items():
        if artifact_id == str(id) or name in artifact_info['artifacts'] or name == artifact_info['name']:
            return artifact_info
    raise ValueError(f'Unknwon artifact {id}{name}')


def get_fight_prop(id: str = '', name: str = ''):
    for fight_prop_id, fight_prop_info in fight_prop.items():
        if fight_prop_id == str(id) or name == fight_prop_info['name']:
            return fight_prop_info
    raise ValueError(f'Unknwon fight prop {id}{name}')


def get_area_emoji(exploration_id: int):
    emoji_dict = {
        1: '<:Emblem_Mondstadt:982449412938809354>',
        2: '<:Emblem_Liyue:982449411047165992>',
        3: '<:Emblem_Dragonspine:982449405883977749>',
        4: '<:Emblem_Inazuma:982449409117806674>',
        5: '<:Emblem_Enkanomiya:982449407469441045>',
        6: '<:Emblem_Chasm:982449404076249138>',
        7: '<:Emblem_Chasm:982449404076249138>',
    }

    emoji = emoji_dict.get(exploration_id)
    return emoji or ''