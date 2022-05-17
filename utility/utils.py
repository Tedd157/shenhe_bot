import re
import discord
import genshin
import yaml
from utility.character_name import character_names


def defaultEmbed(title: str, message: str=''):
    return discord.Embed(title=title, description=message, color=0xa68bd3)


def errEmbed(title: str, message: str):
    return discord.Embed(title=title, description=message, color=0xfc5165)


def log(is_system: bool, is_error: bool, log_type: str, log_msg: str):
    system = "SYSTEM"
    if not is_system:
        system = "USER"
    if not is_error:
        result = f"[{system}][{log_type}] {log_msg}"
    else:
        result = f"[{system}][ERROR][{log_type}] {log_msg}"
    return result


def getCharacterName(character: genshin.models.BaseCharacter) -> str:
    chinese_name = character_names.get(character.id)
    return chinese_name if chinese_name != None else character.name


def trimCookie(cookie: str) -> str:
    try:
        new_cookie = ' '.join([
            re.search('ltoken=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('ltuid=[0-9]{3,}', cookie).group(),
            re.search('cookie_token=[0-9A-Za-z]{20,}', cookie).group(),
            re.search('account_id=[0-9]{3,}', cookie).group()
        ])
    except:
        new_cookie = None
    return new_cookie


weekday_dict = {0: '週一', 1: '週二', 2: '週三', 3: '週四', 4: '週五', 5: '週六', 6: '週日'}


def getWeekdayName(n: int) -> str:
    return weekday_dict.get(n)


def openFile(file_name: str) -> dict:
    with open(f'data/{file_name}.yaml', 'r', encoding='utf-8') as file:
        result = yaml.unsafe_load(file)
    if result is None:
        result = {}
    return result


def saveFile(data: dict, file_name: str):
    with open(f'data/{file_name}.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
