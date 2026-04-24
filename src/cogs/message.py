import re

import discord
from discord.ext import commands


class Message(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _looks_like_natural_language_command(self, content: str) -> bool:
        # Step 2 spike: keep the trigger detection simple so we can validate
        # the wiring from a plain message into the existing command system.
        if not content:
            return False

        trigger_patterns = [
            r"^播放.+",
            r"^幫我暫停$",
            r"^暫停$",
            r"^幫我繼續播放$",
            r"^繼續播放$",
            r"^繼續$",
            r"^下一首$",
            r"^跳過$",
            r"^停止播放$",
            r"^停止$",
            r"^現在在播什麼$",
            r"^現在播放什麼$",
            r"^目前在播什麼$",
        ]
        return any(re.fullmatch(pattern, content) for pattern in trigger_patterns)

    def _parse_natural_language_command(self, content: str) -> tuple[str, dict] | None:
        # This parser is intentionally rule-based for now.
        # Later we can swap this small piece for an LLM that returns the same
        # command name + kwargs shape without changing the playback flow.
        original_text = content
        comparable_text = content.lower()

        # For this spike we only key off the action word itself.
        play_match = re.fullmatch(r"播放\s*(.+)", comparable_text)
        if play_match:
            query = original_text[-len(play_match.group(1)) :].strip()
            if query:
                return ("play", {"search": query})

        mapping = {
            "幫我暫停": ("pause", {}),
            "暫停": ("pause", {}),
            "幫我繼續播放": ("resume", {}),
            "繼續播放": ("resume", {}),
            "繼續": ("resume", {}),
            "下一首": ("skip", {}),
            "跳過": ("skip", {}),
            "停止播放": ("stop", {}),
            "停止": ("stop", {}),
            "現在在播什麼": ("now_playing", {}),
            "現在播放什麼": ("now_playing", {}),
            "目前在播什麼": ("now_playing", {}),
        }
        return mapping.get(comparable_text)

    async def _invoke_existing_command(self, message: discord.Message, command_name: str, **kwargs) -> bool:
        # Reuse the existing commands instead of duplicating play/pause logic here.
        # That keeps this spike focused on validating:
        # message -> intent parsing -> ctx.invoke(existing command)
        ctx = await self.bot.get_context(message)
        command = self.bot.get_command(command_name)
        if ctx.command is not None or command is None:
            return False

        await ctx.invoke(command, **kwargs)
        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content.strip().lower()
        if not content:
            return

        if isinstance(self.bot.command_prefix, str) and content.startswith(self.bot.command_prefix):
            # Let normal prefix commands like !play continue through the regular path.
            return

        if not self._looks_like_natural_language_command(content):
            return

        parsed = self._parse_natural_language_command(content)
        if not parsed:
            return

        command_name, kwargs = parsed
        await self._invoke_existing_command(message, command_name, **kwargs)


async def setup(bot: commands.Bot):
    await bot.add_cog(Message(bot))
