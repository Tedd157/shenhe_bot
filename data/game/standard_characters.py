from typing import List

standard_characters = {
    "10000003": {
        "chs": "\u7434",
        "cht": "\u7434",
        "de": "Jean",
        "en": "Jean",
        "es": "Jean",
        "fr": "Jean",
        "jp": "\u30b8\u30f3",
        "kr": "\uc9c4",
        "th": "Jean",
        "pt": "Jean",
        "ru": "\u0414\u0436\u0438\u043d\u043d",
        "vi": "Jean"
    },
    "10000016": {
        "chs": "\u8fea\u5362\u514b",
        "cht": "\u8fea\u76e7\u514b",
        "de": "Diluc",
        "en": "Diluc",
        "es": "Diluc",
        "fr": "Diluc",
        "jp": "\u30c7\u30a3\u30eb\u30c3\u30af",
        "kr": "\ub2e4\uc774\ub8e8\ud06c",
        "th": "Diluc",
        "pt": "Diluc",
        "ru": "\u0414\u0438\u043b\u044e\u043a",
        "vi": "Diluc"
    },
    "10000035": {
        "chs": "\u4e03\u4e03",
        "cht": "\u4e03\u4e03",
        "de": "Qiqi",
        "en": "Qiqi",
        "es": "Qiqi",
        "fr": "Qiqi",
        "jp": "\u4e03\u4e03",
        "kr": "\uce58\uce58",
        "th": "Qiqi",
        "pt": "Qiqi",
        "ru": "\u0426\u0438 \u0426\u0438",
        "vi": "Qiqi"
    },
    "10000041": {
        "chs": "\u83ab\u5a1c",
        "cht": "\u83ab\u5a1c",
        "de": "Mona",
        "en": "Mona",
        "es": "Mona",
        "fr": "Mona",
        "jp": "\u30e2\u30ca",
        "kr": "\ubaa8\ub098",
        "th": "Mona",
        "pt": "Mona",
        "ru": "\u041c\u043e\u043d\u0430",
        "vi": "Mona"
    },
    "10000042": {
        "chs": "\u523b\u6674",
        "cht": "\u523b\u6674",
        "de": "Keqing",
        "en": "Keqing",
        "es": "Keching",
        "fr": "Keqing",
        "jp": "\u523b\u6674",
        "kr": "\uac01\uccad",
        "th": "Keqing",
        "pt": "Keqing",
        "ru": "\u041a\u044d \u0426\u0438\u043d",
        "vi": "Keqing"
    },
}


def get_standard_characters() -> List:
    result = []
    for character_id, character_names in standard_characters.items():
        for lang_code, character_name in character_names.items():
            result.append(character_name)
    return result
