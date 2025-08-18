# cogs/gamertag_cog.py
import discord
from discord.ext import commands
from .utils import config_manager
import logging

logger = logging.getLogger(__name__)

class GamertagView(discord.ui.View):
    """
    Uma View persistente que será preenchida dinamicamente com botões de cargo.
    A lógica de clique é tratada no listener on_interaction do Cog.
    """
    def __init__(self):
        super().__init__(timeout=None)

class GamertagCog(commands.Cog):
    """Cog para o sistema de cargos por botão (Gamertag)."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Ouve todos os cliques em botões e processa os de gamertag."""
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get("custom_id")
        if not custom_id or not custom_id.startswith("gamertag_role_"):
            return

        try:
            # Extrai o ID do cargo do custom_id do botão
            role_id = int(custom_id.split("_")[2])
            role = interaction.guild.get_role(role_id)
            
            if not role:
                return await interaction.response.send_message("❌ O cargo associado a este botão não existe mais.", ephemeral=True)

            member = interaction.user
            
            # Adiciona ou remove o cargo
            if role in member.roles:
                await member.remove_roles(role, reason="Cargo removido via painel Gamertag")
                await interaction.response.send_message(f"✅ Cargo `{role.name}` removido!", ephemeral=True)
            else:
                await member.add_roles(role, reason="Cargo adicionado via painel Gamertag")
                await interaction.response.send_message(f"✅ Cargo `{role.name}` adicionado!", ephemeral=True)

        except (ValueError, IndexError):
            # O custom_id está mal formatado
            await interaction.response.send_message("❌ Erro no botão. O ID do cargo parece ser inválido.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Não tenho permissão para gerir os seus cargos. O meu cargo pode estar abaixo do cargo que você está a tentar obter.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro na interação do botão gamertag: {e}")
            await interaction.response.send_message("❌ Ocorreu um erro inesperado.", ephemeral=True)

    # --- COMANDOS DE SETUP ---
    @commands.hybrid_group(name="gamertag", description="Comandos para configurar o painel de cargos.")
    @commands.has_permissions(administrator=True)
    async def gamertag(self, ctx: commands.Context):
        """Grupo de comandos para configurar o painel de cargos."""
        if ctx.invoked_subcommand is None:
            await ctx.reply("Use um subcomando: `/gamertag add`, `/gamertag remove`, `/gamertag painel`.", ephemeral=True)

    @gamertag.command(name="add", description="Adiciona um novo cargo/botão ao painel.")
    @commands.has_permissions(administrator=True)
    async def add_role_button(self, ctx: commands.Context, cargo: discord.Role, emoji: str, label: str):
        """Adiciona um cargo à configuração do painel."""
        config = config_manager.get_server_config(ctx.guild.id)
        
        if 'gamertag_buttons' not in config:
            config['gamertag_buttons'] = []

        # Verifica se o cargo já foi adicionado
        if any(b['role_id'] == cargo.id for b in config['gamertag_buttons']):
            return await ctx.reply(f"❌ O cargo {cargo.mention} já está no painel.", ephemeral=True)

        config['gamertag_buttons'].append({
            'role_id': cargo.id,
            'emoji': emoji,
            'label': label
        })
        
        config_manager.save_server_config(ctx.guild.id, config)
        await ctx.reply(f"✅ O botão para o cargo {cargo.mention} com o label '{label}' foi adicionado à configuração.", ephemeral=True)

    @gamertag.command(name="remove", description="Remove um cargo/botão do painel.")
    @commands.has_permissions(administrator=True)
    async def remove_role_button(self, ctx: commands.Context, cargo: discord.Role):
        """Remove um cargo da configuração do painel."""
        config = config_manager.get_server_config(ctx.guild.id)
        
        if 'gamertag_buttons' not in config:
            return await ctx.reply("❌ Nenhum botão de cargo configurado.", ephemeral=True)

        buttons = config['gamertag_buttons']
        button_to_remove = next((b for b in buttons if b['role_id'] == cargo.id), None)

        if not button_to_remove:
            return await ctx.reply(f"❌ O cargo {cargo.mention} não está configurado no painel.", ephemeral=True)

        config['gamertag_buttons'].remove(button_to_remove)
        config_manager.save_server_config(ctx.guild.id, config)
        await ctx.reply(f"✅ O botão para o cargo {cargo.mention} foi removido da configuração.", ephemeral=True)
        
    @gamertag.command(name="painel", description="Envia o painel de cargos para um canal.")
    @commands.has_permissions(administrator=True)
    async def send_panel(self, ctx: commands.Context, canal: discord.TextChannel, titulo: str, imagem: discord.Attachment):
        """Envia o painel de cargos com os botões configurados."""
        config = config_manager.get_server_config(ctx.guild.id)
        buttons_config = config.get('gamertag_buttons', [])

        if not buttons_config:
            return await ctx.reply("❌ Não há cargos configurados. Use `/gamertag add` primeiro.", ephemeral=True)
            
        embed = discord.Embed(title=titulo, color=discord.Color.blue())
        embed.set_image(url=imagem.url)

        view = GamertagView()
        for button_config in buttons_config:
            view.add_item(discord.ui.Button(
                label=button_config['label'],
                emoji=button_config['emoji'],
                style=discord.ButtonStyle.secondary, # Botão cinza
                custom_id=f"gamertag_role_{button_config['role_id']}"
            ))

        try:
            await canal.send(embed=embed, view=view)
            await ctx.reply(f"✅ Painel de Gamertag enviado para {canal.mention}!", ephemeral=True)
        except discord.Forbidden:
            await ctx.reply(f"❌ Não tenho permissão para enviar mensagens em {canal.mention}.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Carrega o Cog de Gamertag no bot."""
    await bot.add_cog(GamertagCog(bot))