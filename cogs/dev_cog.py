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
        """Sincroniza os comandos de barra (/) com o Discord."""
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

    # --- COMANDO DE TESTE ATUALIZADO PARA USAR TEXTO SIMPLES ---
    @commands.hybrid_command(name="teste-efeito", description="Cria uma mensagem com texto e componentes, sem embed.")
    async def teste_efeito(self, ctx: commands.Context):
        """Cria o efeito visual de 'container' usando texto simples + view."""
        
        # --- Peça 1: O Texto Simples (Content) ---
        # Em vez de um embed, agora usamos uma string de texto normal.
        # O \n cria uma quebra de linha.
        texto_da_mensagem = "Este é um container\n• Parecido com os embeds"

        # --- Peça 2: A View (O "Container" dos botões) ---
        # Esta parte continua igual, pois a View é o nosso container de botões.
        view = discord.ui.View()
        
        # Adicionamos a fileira de botões da imagem do vídeo
        view.add_item(discord.ui.Button(label="Voltar", style=discord.ButtonStyle.secondary))
        view.add_item(discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.green))
        view.add_item(discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.red))
        view.add_item(discord.ui.Button(label="Recarregar", style=discord.ButtonStyle.primary))
        
        # --- Juntando Tudo ---
        # A grande mudança está aqui: usamos 'content=' em vez de 'embed='.
        await ctx.send(content=texto_da_mensagem, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(DevCog(bot))