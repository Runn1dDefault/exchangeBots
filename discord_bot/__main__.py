import asyncio
import time
from datetime import datetime

import discord
from discord import Member, Role

from envs import DISCORD_BOT_ROLE_USER, DISCORD_BOT_GUILD_ID, DISCORD_BOT_TOKEN
from models import create_tables, db, DBUser

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"{client.user} is online")


@client.event
async def on_member_join(member: Member):
    try:
        with db.transaction() as tx_db:
            try:
                user_db: DBUser = DBUser.get_or_none(DBUser.discord_id == str(member.id))

                role_user = discord.utils.get(member.guild.roles, id=DISCORD_BOT_ROLE_USER)
                if user_db and user_db.dt_end_subscription > datetime.now():
                    await member.add_roles(role_user)
                    user_db.discord_role = "user"
                else:
                    user_db.discord_role = "not_user"
                user_db.save()
            except Exception as ex:
                tx_db.rollback()
                print("ERROR.on_member_join.tx_db:", ex)
    except Exception as ex:
        print("ERROR.on_member_join.tx_db:", ex)


@client.event
async def on_member_remove(member: Member):
    try:
        with db:
            user_db: DBUser = DBUser.get_or_none(DBUser.discord_id == str(member.id))

            if user_db:
                user_db.discord_role = "none"
                user_db.save()
    except Exception as ex:
        print("ERROR.on_member_remove:", ex)


async def check_statuses():
    await asyncio.sleep(5)
    guild = client.get_guild(DISCORD_BOT_GUILD_ID)
    role_user = guild.get_role(DISCORD_BOT_ROLE_USER)
    while True:
        members_discord = guild.members

        try:
            with db:
                for member in members_discord:
                    member: Member
                    role: Role
                    user_db: DBUser = DBUser.get_or_none(DBUser.discord_id == str(member.id))
                    if not user_db or (user_db.dt_end_subscription < datetime.now()):
                        try:
                            if role_user in member.roles:
                                print(f'----------> {member.id=} {member.name=} {member.roles=}')
                                if user_db:
                                    print(f"End sub {user_db.dt_end_subscription}")
                                print(role_user, role_user in member.roles)
                                await member.remove_roles(role_user)
                        except Exception as ex:
                            print(2, ex)
                        try:
                            user_db.discord_role = "not_user"
                        except:
                            pass

                    if user_db and (user_db.dt_end_subscription > datetime.now()):
                        try:
                            if role_user not in member.roles:
                                print(f'----------> {member.id=} {member.name=} {member.roles=}')
                                if user_db:
                                    print(f"End sub {user_db.dt_end_subscription}")
                                print(role_user, role_user in member.roles)
                                await member.add_roles(role_user)
                        except:
                            pass
                        try:
                            user_db.discord_role = "user"
                        except:
                            pass

                    try:
                        user_db.save()
                    except:
                        pass
        except Exception as ex:
            print(1, ex)

        await asyncio.sleep(5)


while True:
    try:
        create_tables()
        break
    except Exception as e:
        print("Wait MySQL connection...", e)
        time.sleep(1)

client.loop.create_task(check_statuses())
client.run(DISCORD_BOT_TOKEN)
