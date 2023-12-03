import re
from typing import Union

import discord
from loguru import logger
from envs import DISCORD_DISPLAY_BOT_TOKEN

from models import db, Channel, TraderTask
from utils.create_tables import make_migrations

from .mixins import MessageMixin
from .helpers import (
    save_channel, remove_channel, check_exist, save_trader_task, get_db_object
)


class DiscordSynergy(discord.Client, MessageMixin):
    activate = '!activateshadowcopy'
    deactivate = '!deactivatechannel'
    key_for_get_signals = 'New'

    async def on_ready(self):
        logger.info('Logged on as', self.user)

    async def on_message(self, message):
        """Get message from bot"""
        msg_object = message
        msg_content = message.content
        await self.react_on_command(msg_object, msg_content)

    async def react_on_command(self, msg_object, msg_content):
        """Script for reacting to required commands
        and run function if command exists
        """
        if msg_object.author == self.user:
            return

        if self.activate == msg_content.strip().lower():
            return await self.activate_channel(msg_object)

        elif self.deactivate == msg_content.strip().lower():
            return await self.deactivate_channel(msg_object)

        elif not check_exist(Channel, msg_object.channel.id):
            return await msg_object.channel.send(self.CHANNEL_IS_NOT_ACTIVATE_MSG.format(
                channel_name=msg_object.channel.name,
                activate=self.activate
            ))
        msg_data = self.get_message_template(msg_object)
        validated = await self.validate_data(msg_data, msg_object)
        try:
            coroutine, status = validated
            if status:
                logger.info(msg_data)
                save_trader_task(TraderTask, get_db_object(
                    Channel, msg_object.channel.id).id, **msg_data)
                await msg_object.channel.send(self.TEMPLATE_SUCCESS_MSG)
            return coroutine
        except Exception as e:
            logger.error(e)
            await msg_object.channel.send(self.DATABASE_ERROR_MSG)

    async def activate_channel(self, msg_object):
        type_of_source = 'discord'
        channel_id = msg_object.channel.id
        name = msg_object.channel.name

        if check_exist(Channel, channel_id):
            return await msg_object.channel.send(self.CHANNEL_EXISTS_MSG.format(name))

        save_channel(
            Channel,
            type_src=type_of_source,
            channel_id=channel_id,
            name=name
        )
        logger.info(self.CHANNEL_SUCCESS_ADD_MSG)
        await msg_object.channel.send(self.CHANNEL_SUCCESS_ADD_MSG)

    async def deactivate_channel(self, msg_object):
        logger.info(self.CHANNEL_SUCCESS_REMOVE_MSG)
        channel_id = msg_object.channel.id
        remove_channel(
            Channel,
            channel_id=channel_id
        )
        await msg_object.channel.send(self.CHANNEL_SUCCESS_REMOVE_MSG)

    @staticmethod
    def get_message_template(msg) -> Union[dict, None]:
        keys_values_msg = msg.content.strip().split("\n")
        template_dict = {}
        for key in keys_values_msg:
            try:
                k, v = key.split(":")
                template_dict[k.lower().strip()] = v.strip()
            except ValueError as e:
                logger.error(e)
                return
        return template_dict

    async def validate_data(self, msg, msg_object):
        required_template_result, status = self.required_template(msg, msg_object.content)
        if msg is None:
            return await msg_object.channel.send(self.TEMPLATE_ERROR_MSG), False
        elif not status:
            return await msg_object.channel.send(self.TEMPLATE_ERROR_KEY_MSG.format(required_template_result)), False
        else:
            return True, True

    @staticmethod
    def required_template(msg: dict, msg_data: str) -> Union[(list, bool)]:
        """Full check signal templates"""
        targets = re.findall(r"Target", msg_data, re.IGNORECASE)
        status = True
        required_keys = ['Type', 'Token', 'Direction', 'Entry', 'Target1', 'Stop loss', 'Leverage']
        for index, target in enumerate(targets, start=1):
            required_keys.append(f"Target{index}")
        unique_required_keys = list(set(required_keys))

        for_errors = []
        if not msg:
            return for_errors, False

        for key in unique_required_keys:
            if key.lower() not in msg:
                for_errors.append(key)
            else:
                continue

        if not for_errors:
            return unique_required_keys, status
        status = False
        return for_errors, status


if __name__ == '__main__':
    make_migrations()
    client = DiscordSynergy()
    with db.atomic():
        client.run(DISCORD_DISPLAY_BOT_TOKEN)
