# cogs/utilidades_cog.py
import discord
from discord.ext import commands

class UtilidadesCog(commands.Cog):
    """Cog para comandos de utilidade geral."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="av", description="Mostra o avatar de um usuário.")
    async def avatar(self, ctx: commands.Context, *, usuario: discord.Member = None):
        """
        Mostra o avatar de um usuário em alta qualidade.
        - Se nenhum usuário for mencionado, mostra o seu próprio avatar.
        - Se mencionar um usuário, mostra o avatar dele.
        - Se responder a uma mensagem, mostra o avatar do autor da mensagem.
        """
        
        target_user = None
        
        # Cenário 1: Comando usado em resposta a uma mensagem
        if ctx.message.reference and ctx.message.reference.resolved:
            target_user = ctx.message.reference.resolved.author
        
        # Cenário 2: Um usuário é mencionado no comando
        elif usuario:
            target_user = usuario
        
        # Cenário 3: Nenhum usuário mencionado (comando simples)
        else:
            target_user = ctx.author

        # Pega o avatar do usuário alvo.
        avatar_asset = target_user.display_avatar
        
        # Pega a URL do avatar com uma boa resolução (1024 pixels)
        avatar_url = avatar_asset.with_size(1024).url

        # Cria o Embed
        embed = discord.Embed(
            title=f"Avatar de {target_user.display_name}",
            color=0xFFFFFF  # <-- ALTERAÇÃO: Cor definida para branco
        )
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")

        # Cria a View com o botão de download
        view = discord.ui.View()
        botao_download = discord.ui.Button(
            label="Baixar",
            style=discord.ButtonStyle.secondary, # Botão cinza
            url=avatar_url # O botão será um link direto para a imagem
        )
        view.add_item(botao_download)

        # Envia a mensagem como uma resposta
        await ctx.reply(embed=embed, view=view)


async def setup(bot: commands.Bot):
    """Carrega o Cog de Utilidades no bot."""
    await bot.add_cog(UtilidadesCog(bot))