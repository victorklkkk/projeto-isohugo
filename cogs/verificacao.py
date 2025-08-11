# cogs/verificacao_cog.py
import discord
from discord.ext import commands
import logging
from .ui.verificacao_ui import VerificationView, AdminApprovalView # Importa as UIs
from .utils import config_manager # Importa o gestor de config

logger = logging.getLogger(__name__)

class VerificacaoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(VerificationView())
        self.bot.add_view(AdminApprovalView())

    @commands.hybrid_group(name="setup", description="Comandos de configuração do sistema de verificação.")
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Use um subcomando como `/setup config`, `/setup painel` ou `/setup ficha`.", ephemeral=True)

    @setup.command(name="config", description="Configura os canais e cargos do sistema.")
    @commands.has_permissions(administrator=True)
    async def config(self, ctx: commands.Context, canal_logs: discord.TextChannel, cargo_verificado: discord.Role):
        if cargo_verificado.position >= ctx.guild.me.top_role.position:
            return await ctx.send(f"❌ O cargo {cargo_verificado.mention} está numa posição hierárquica maior que a minha.", ephemeral=True)
        
        admin_roles = [role.id for role in ctx.guild.roles if role.permissions.administrator and not role.is_bot_managed()]
        
        # Pega a configuração existente para não apagar outras chaves
        server_config = config_manager.get_server_config(ctx.guild.id)
        server_config.update({
            'canal_logs': canal_logs.id,
            'cargo_verificado': cargo_verificado.id,
            'cargos_admin': admin_roles
        })
        
        config_manager.save_server_config(ctx.guild.id, server_config)
        await ctx.send(f"✅ Configuração salva! Logs em {canal_logs.mention} e cargo {cargo_verificado.mention} definido.", ephemeral=True)

    @setup.command(name="painel", description="Envia o painel de verificação para um canal.")
    @commands.has_permissions(administrator=True)
    async def painel(self, ctx: commands.Context, canal: discord.TextChannel, titulo: str = "Verificação", descricao: str = "Para obter acesso completo ao servidor, por favor clique no botão abaixo e siga as instruções.", cor: str = None, imagem: discord.Attachment = None, thumbnail: discord.Attachment = None):
        if not config_manager.get_server_config(ctx.guild.id):
            return await ctx.send("❌ Por favor, configure o sistema primeiro com `/setup config`.", ephemeral=True)
        try:
            embed_color = discord.Color.from_str(cor) if cor else discord.Color.from_str("#2f3136")
        except (ValueError, TypeError):
            await ctx.send("⚠️ Cor inválida! Usando a cor padrão.", ephemeral=True)
            embed_color = discord.Color.from_str("#2f3136")
        embed = discord.Embed(title=titulo, description=descricao, color=embed_color)
        if imagem: embed.set_image(url=imagem.url)
        if thumbnail: embed.set_thumbnail(url=thumbnail.url)
        try:
            await canal.send(embed=embed, view=VerificationView())
            await ctx.send(f"✅ Painel de verificação enviado para {canal.mention}!", ephemeral=True)
        except discord.Forbidden:
            await ctx.send(f"❌ Não tenho permissão para enviar mensagens em {canal.mention}.", ephemeral=True)

    # --- NOVO COMANDO PARA CONFIGURAR A FICHA ---
    @setup.command(name="ficha", description="Personaliza a aparência da ficha de verificação.")
    @commands.has_permissions(administrator=True)
    async def ficha(self, ctx: commands.Context, titulo: str = "📥 Novo Pedido de Verificação", cor: str = "#3498db"):
        """Personaliza o embed que chega para os admins."""
        server_config = config_manager.get_server_config(ctx.guild.id)
        if not server_config:
            return await ctx.send("❌ Por favor, configure o sistema primeiro com `/setup config`.", ephemeral=True)

        try:
            discord.Color.from_str(cor)
        except (ValueError, TypeError):
            return await ctx.send("❌ Cor inválida! Use um formato hexadecimal (ex: `#ff0000`).", ephemeral=True)
            
        # Cria ou atualiza a configuração do embed da ficha
        server_config['ficha_embed'] = {
            'titulo': titulo,
            'cor': cor
        }
        
        config_manager.save_server_config(ctx.guild.id, server_config)
        
        embed = discord.Embed(
            title="✅ Configuração da Ficha Salva!",
            description="A aparência dos novos pedidos de verificação foi atualizada.",
            color=discord.Color.green()
        )
        embed.add_field(name="Novo Título", value=titulo)
        embed.add_field(name="Nova Cor", value=cor)
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Carrega o Cog de Verificação no bot."""
    await bot.add_cog(VerificacaoCog(bot))