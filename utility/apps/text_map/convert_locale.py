from typing import Literal
from discord import Locale


to_enka_dict = {
    'zh-CN': 'chs',
    'zh-TW': 'cht',
    'de': 'de',
    'en-US': 'en',
    'es-ES': 'es',
    'fr': 'fr',
    'ja': 'jp',
    'ko': 'kr',
    'th': 'th',
    'pt-BR': 'pt',
    'ru': 'ru',
    'vi': 'vi'
}

to_ambr_top_dict = {
    'zh-CN': 'chs',
    'zh-TW': 'cht',
    'de': 'de',
    'en-US': 'en',
    'es-ES': 'es',
    'fr': 'fr',
    'ja': 'jp',
    'ko': 'kr',
    'th': 'th',
    'pt-BR': 'pt',
    'ru': 'ru',
    'vi': 'vi'
}

to_genshin_py_dict = {
    'zh-CN': 'zh-cn',
    'zh-TW': 'zh-tw',
    'de': 'de-de',
    'en-US': 'en-us',
    'es-ES': 'es-es',
    'fr': 'fr-fr',
    'ja': 'ja-jp',
    'ko': 'ko-kr',
    'th': 'th-th',
    'pt-BR': 'pt-pt',
    'ru': 'ru-ru',
    'vi': 'vi-vn'
}

def to_enka(locale: Literal["Locale", "str"]):
    return to_enka_dict.get(str(locale))

def to_ambr_top(locale: Literal["Locale", "str"]):
    return to_ambr_top_dict.get(str(locale))

def to_genshin_py(locale: Literal["Locale", "str"]):
    return to_genshin_py_dict.get(str(locale))