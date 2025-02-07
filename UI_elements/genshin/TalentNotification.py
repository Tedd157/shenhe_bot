import ast
from typing import Any

import aiohttp
import aiosqlite
from apps.genshin.utils import get_all_non_beta_characters, get_character
from data.game.elements import convert_elements, elements
from debug import DefaultView
from discord import Interaction, Locale, Member, SelectOption
from discord.ui import Button, Select
from apps.genshin.genshin_app import GenshinApp
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from utility.utils import default_embed, error_embed


class View(DefaultView):
    def __init__(self, author: Member, locale: Locale, user_locale: str, db: aiosqlite.Connection, genshin_app: GenshinApp, session: aiohttp.ClientSession):
        super().__init__(timeout=None)
        self.author = author
        self.locale = locale
        self.user_locale = user_locale
        self.db = db
        self.genshin_app = genshin_app
        self.session = session

        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 6):
            self.add_item(ElementButton(
                element_names[index], element_emojis[index], index//3))

    async def interaction_check(self, i: Interaction) -> bool:
        user_locale = await get_user_locale(i.user.id, self.db)
        if self.author.id != i.user.id:
            await i.response.send_message(embed=error_embed().set_author(name=text_map.get(143, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        return self.author.id == i.user.id


class ElementButton(Button):
    def __init__(self, element: str, element_emoji: str, row: int):
        super().__init__(emoji=element_emoji, row=row)
        self.element = element

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        user_locale = await get_user_locale(i.user.id, self.view.db)

        embed = default_embed(message=text_map.get(
            156, i.locale, user_locale))
        embed.set_author(name=text_map.get(
            157, i.locale, user_locale), icon_url=i.user.avatar)
        value = await self.view.genshin_app.get_user_talent_notification_enabled_str(i.user.id, i.locale)
        embed.add_field(name=text_map.get(
            159, i.locale, user_locale), value=value)

        c = await self.view.db.cursor()
        await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (i.user.id,))
        user_character_list: list = ast.literal_eval((await c.fetchone())[0])

        options = []
        characters = await get_all_non_beta_characters(self.view.session, user_locale or i.locale)
        for character_id, character_info in characters.items():
            if character_info['element'] == self.element:
                description = text_map.get(
                    161, i.locale, user_locale) if character_id in user_character_list else None
                options.append(SelectOption(
                    label=character_info['name'],
                    emoji=get_character(character_id)['emoji'],
                    value=character_id,
                    description=description)
                )

        # choose your character(s)
        placeholder = text_map.get(157, i.locale, user_locale)

        self.view.clear_items()
        self.view.add_item(GoBack())
        self.view.add_item(CharacterSelect(options, placeholder))
        await i.response.edit_message(embed=embed, view=self.view)


class GoBack(Button):
    def __init__(self):
        super().__init__(emoji='<:left:982588994778972171>', row=2)

    async def callback(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.view.db)
        self.view: View
        self.view.clear_items()

        element_names = list(convert_elements.values())
        element_emojis = list(elements.values())
        for index in range(0, 6):
            self.view.add_item(ElementButton(
                element_names[index], element_emojis[index], index//3))
        embed = default_embed(message=text_map.get(
            156, i.locale, user_locale))
        embed.set_author(name=text_map.get(
            157, i.locale, user_locale), icon_url=i.user.avatar)
        value = await self.view.genshin_app.get_user_talent_notification_enabled_str(i.user.id, i.locale)
        embed.add_field(name=text_map.get(
            159, i.locale, user_locale), value=value)
        await i.response.edit_message(embed=embed, view=self.view)


class CharacterSelect(Select):
    def __init__(self, options: list[SelectOption], placeholder: str):
        super().__init__(options=options, placeholder=placeholder, max_values=len(options))

    async def callback(self, i: Interaction) -> Any:
        self.view: View
        c = await self.view.db.cursor()
        user_locale = await get_user_locale(i.user.id, self.view.db)
        
        await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (i.user.id,))
        user_character_list: list = ast.literal_eval((await c.fetchone())[0])
        for character_id in self.values:
            if character_id in user_character_list:
                user_character_list.remove(character_id)
            else:
                user_character_list.append(character_id)
        await c.execute('UPDATE genshin_accounts SET talent_notif_toggle = 1, talent_notif_chara_list = ? WHERE user_id = ?', (str(user_character_list), i.user.id))
        await self.view.db.commit()
        
        embed = default_embed(message=text_map.get(
            156, i.locale, user_locale))
        embed.set_author(name=text_map.get(
            157, i.locale, user_locale), icon_url=i.user.avatar)
        value = await self.view.genshin_app.get_user_talent_notification_enabled_str(i.user.id, i.locale)
        embed.add_field(name=text_map.get(
            159, i.locale, user_locale), value=value)
        
        await c.execute('SELECT talent_notif_chara_list FROM genshin_accounts WHERE user_id = ?', (i.user.id,))
        user_character_list: list = ast.literal_eval((await c.fetchone())[0])
        for option in self.options:
            if option.value in user_character_list:
                option.description = text_map.get(161, i.locale, user_locale)
            else:
                option.description = None
                
        await i.response.edit_message(embed=embed, view=self.view)
