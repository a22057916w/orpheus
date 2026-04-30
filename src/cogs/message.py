import asyncio

import discord
from discord.ext import commands

from src.utils import llm_utils


class Message(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _invoke_existing_command(self, message: discord.Message, command_name: str, **kwargs) -> bool:
        # Keep execution inside the existing command flow so the LLM only decides intent.
        ctx = await self.bot.get_context(message)
        command = self.bot.get_command(command_name)
        if ctx.command is not None or command is None:
            print(
                f"LLM DEBUG: Command invoke skipped -> "
                f"ctx.command={getattr(ctx.command, 'qualified_name', None)}, target_command={command_name}, exists={command is not None}"
            )
            return False

        print(f"LLM DEBUG: Invoking command -> {command_name}, kwargs={kwargs}")
        await ctx.invoke(command, **kwargs)
        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        content = message.content.strip()
        if not content:
            return

        if isinstance(self.bot.command_prefix, str) and content.startswith(self.bot.command_prefix):
            # Let normal prefix commands like !play continue through the regular path.
            return

        if not self.bot.user or self.bot.user not in message.mentions:
            print(f"LLM DEBUG: Message skipped because bot was not mentioned -> {content}")
            return

        parsed = await asyncio.to_thread(llm_utils.parse_music_request, content)
        if not parsed or parsed.action == "none":
            print(f"LLM DEBUG: No actionable command for message -> {content}")
            return

        if parsed.action == "play":
            query = parsed.query.strip()
            if not query:
                print("LLM DEBUG: Play action returned an empty query.")
                return
            await self._invoke_existing_command(message, "play", search=query)
            return

        command_mapping = {
            "pause": "pause",
            "resume": "resume",
            "skip": "skip",
            "stop": "stop",
            "now_playing": "now_playing",
        }
        command_name = command_mapping.get(parsed.action)
        if not command_name:
            print(f"LLM DEBUG: Unsupported parsed action -> {parsed.action}")
            return

        await self._invoke_existing_command(message, command_name)


async def setup(bot: commands.Bot):
    await bot.add_cog(Message(bot))
