import discord
from discord.ext import commands,tasks

import os
import random
import re

class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #當有訊息時
    @commands.Cog.listener()
    async def on_message(self, message):
        evil_reponse = [
            "Fuck you",
            "Go fuck yourself",
            "Fuck Off",
            "Fuck you, too",
            "幹三小",
            "幹你老師",
            "賽你娘",
            "幹",
            "哭阿"
        ]

        #排除自己的訊息，避免陷入無限循環
        if message.author == self.bot.user:
            return

        #如果以「說」開頭
        if message.content.startswith('說'):
          #分割訊息成兩份
          tmp = message.content.split(" ", 2)
          #如果分割後串列長度只有1
          if len(tmp) == 1:
            await message.channel.send("你要我說什麼啦？")
          else:
            await message.channel.send(tmp[1])

        if re.fullmatch(r'r+', message.content, re.IGNORECASE):
            await message.channel.send("RRRRRRRRRRRRRRRRR\n幫我開直播")

        if "幹" in message.content:
            await message.channel.send(f"{message.author.name} {random.choice(evil_reponse)}")

        for member in message.mentions:
            await message.channel.send(member.mention + "你過來一下!")




# An extension must have a global function, setup defined as the entry point on what to do when the extension is loaded.
# This entry point must have a single argument, the bot.
def setup(bot):
    bot.add_cog(Message(bot))
