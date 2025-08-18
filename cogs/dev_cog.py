# cogs/dev_cog.py
from discord.ext import commands

class DevCog(commands.Cog):
    """Cog para comandos de desenvolvedor."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, spec: str = None):
        """
        Sincroniza os comandos de barra (/) com o Discord.
        Uso: y!sync (global) ou y!sync guild (para este servidor)
        """
        try:
            fmt = 0
            # Sincroniza apenas para o servidor atual (instantâneo)
            if spec == "guild":
                synced = await self.bot.tree.sync(guild=ctx.guild)
                fmt = len(synced)
                await ctx.reply(f"✅ Sincronizados **{fmt}** comandos para este servidor.")
            # Sincroniza globalmente (pode demorar até 1 hora)
            else:
                synced = await self.bot.tree.sync()
                fmt = len(synced)
                await ctx.reply(f"✅ Sincronizados **{fmt}** comandos globais.")
        except Exception as e:
            await ctx.reply(f"❌ Falha ao sincronizar: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(DevCog(bot))