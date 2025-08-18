# cogs/dev_cog.py
from discord.ext import commands
import discord # Adicione o import do discord

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

    # --- NOVO COMANDO DE EXEMPLO ---
    @commands.hybrid_command(name="teste-efeito", description="Recria o efeito de embed com componentes.")
    async def teste_efeito(self, ctx: commands.Context):
        """Recria o efeito visual da imagem de exemplo."""
        
        # --- Peça 1: O Embed ---
        # Criamos o conteúdo de texto da parte de cima.
        # O @c4 é apenas um texto de exemplo aqui.
        embed = discord.Embed(
            title="Damas de fumovadias (1/8)",
            description="<@492089145271779328> (`fumovadias` | 492089145271779328)",
            color=0x2f3136 # Uma cor escura similar
        )

        # --- Peça 2: A View (O "Container") ---
        # Criamos o container para os nossos componentes.
        view = discord.ui.View()

        # Adicionamos os componentes v2 (botão e menu de seleção) ao container.
        view.add_item(discord.ui.Button(
            label="Remover PD", 
            style=discord.ButtonStyle.secondary # Cinza
        ))
        
        # O segundo item é um Menu de Seleção (Dropdown)
        view.add_item(discord.ui.Select(
            placeholder="Adicionar Primeira Dama",
            options=[
                discord.SelectOption(label="Opção 1", value="1"),
                discord.SelectOption(label="Opção 2", value="2")
            ]
        ))
        
        # --- Juntando Tudo ---
        # Enviamos a mensagem com as DUAS peças separadas.
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(DevCog(bot))