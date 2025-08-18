# cogs/dev_cog.py
import discord
from discord.ext import commands

class DevCog(commands.Cog):
    """Cog para comandos de desenvolvedor."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, spec: str = None):
        # ... (código do sync sem alterações)
        try:
            fmt = 0
            if spec == "guild":
                synced = await self.bot.tree.sync(guild=ctx.guild)
                fmt = len(synced)
                await ctx.reply(f"✅ Sincronizados **{fmt}** comandos para este servidor.")
            else:
                synced = await self.bot.tree.sync()
                fmt = len(synced)
                await ctx.reply(f"✅ Sincronizados **{fmt}** comandos globais.")
        except Exception as e:
            await ctx.reply(f"❌ Falha ao sincronizar: {e}")

    # --- COMANDO DE EXEMPLO ATUALIZADO ---
    @commands.hybrid_command(name="teste-efeito", description="Recria o efeito de embed com componentes.")
    async def teste_efeito(self, ctx: commands.Context):
        """Recria o efeito visual da imagem de exemplo."""
        
        # --- Peça 1: O Embed (com a cor corrigida) ---
        embed = discord.Embed(
            title="Damas de fumovadias (1/8)",
            description="<@492089145271779328> (`fumovadias` | 492089145271779328)",
            color=0x5865F2 # Uma cor púrpura/azulada similar à do Discord (Blurple)
        )

        # --- Peça 2: A View (O "Container") ---
        view = discord.ui.View()

        view.add_item(discord.ui.Button(
            label="Remover PD", 
            style=discord.ButtonStyle.secondary # Cinza
        ))
        
        view.add_item(discord.ui.Select(
            placeholder="Adicionar Primeira Dama",
            options=[
                discord.SelectOption(label="Opção 1", value="1"),
                discord.SelectOption(label="Opção 2", value="2")
            ]
        ))
        
        # --- Juntando Tudo ---
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(DevCog(bot))