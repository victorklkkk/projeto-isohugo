# cogs/gamertag_cog.py
import discord
from discord.ext import commands
from .utils import config_manager
import logging

logger = logging.getLogger(__name__)

class GamertagCog(commands.Cog):
    """Cog para o sistema de cargos por botão (Gamertag)."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Ouve todos os cliques em botões e processa os de gamertag."""
        if interaction.type != discord.InteractionType.component or not interaction.data:
            return
        
        custom_id = interaction.data.get("custom_id")
        if not custom_id or not custom_id.startswith("gamertag_role_"):
            return

        try:
            role_id = int(custom_id.split("_")[2])
            role = interaction.guild.get_role(role_id)
            
            if not role:
                return await interaction.response.send_message("❌ O cargo associado a este botão não existe mais.", ephemeral=True)

            member = interaction.user
            
            if role in member.roles:
                await member.remove_roles(role, reason="Cargo removido via painel Gamertag")
                await interaction.response.send_message(f"✅ Cargo `{role.name}` removido!", ephemeral=True)
            else:
                await member.add_roles(role, reason="Cargo adicionado via painel Gamertag")
                await interaction.response.send_message(f"✅ Cargo `{role.name}` adicionado!", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro na interação do botão gamertag: {e}")
            await interaction.response.send_message("❌ Ocorreu um erro inesperado.", ephemeral=True)

    # --- COMANDOS DE SETUP ---
    @commands.hybrid_group(name="gamertag", description="Comandos para configurar o painel de cargos.")
    @commands.has_permissions(administrator=True)
    async def gamertag(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.reply("Use um subcomando: `/gamertag add`, `/gamertag remove`, `/gamertag painel`.", ephemeral=True)

    @gamertag.command(name="add", description="Adiciona um novo cargo/botão ao painel.")
    @commands.has_permissions(administrator=True)
    async def add_role_button(self, ctx: commands.Context, cargo: discord.Role, emoji: str, label: str = None):
        """Adiciona um cargo à configuração do painel. O label é opcional."""
        config = config_manager.get_server_config(ctx.guild.id)
        
        if 'gamertag_buttons' not in config:
            config['gamertag_buttons'] = []

        if any(b['role_id'] == cargo.id for b in config['gamertag_buttons']):
            return await ctx.reply(f"❌ O cargo {cargo.mention} já está no painel.", ephemeral=True)

        config['gamertag_buttons'].append({
            'role_id': cargo.id,
            'emoji': emoji,
            'label': label  # Pode ser None
        })
        
        config_manager.save_server_config(ctx.guild.id, config)
        await ctx.reply(f"✅ O botão para o cargo {cargo.mention} foi adicionado à configuração.", ephemeral=True)

    @gamertag.command(name="remove", description="Remove um cargo/botão do painel.")
    @commands.has_permissions(administrator=True)
    async def remove_role_button(self, ctx: commands.Context, cargo: discord.Role):
        config = config_manager.get_server_config(ctx.guild.id)
        buttons = config.get('gamertag_buttons', [])
        button_to_remove = next((b for b in buttons if b['role_id'] == cargo.id), None)

        if not button_to_remove:
            return await ctx.reply(f"❌ O cargo {cargo.mention} não está configurado no painel.", ephemeral=True)

        config['gamertag_buttons'].remove(button_to_remove)
        config_manager.save_server_config(ctx.guild.id, config)
        await ctx.reply(f"✅ O botão para o cargo {cargo.mention} foi removido da configuração.", ephemeral=True)
        
    @gamertag.command(name="painel", description="Envia o painel de cargos para um canal.")
    @commands.has_permissions(administrator=True)
    async def send_panel(self, ctx: commands.Context, canal: discord.TextChannel, imagem: discord.Attachment, titulo: str = None, cor: str = None):
        """Envia o painel de cargos com os botões configurados."""
        config = config_manager.get_server_config(ctx.guild.id)
        buttons_config = config.get('gamertag_buttons', [])

        if not buttons_config:
            return await ctx.reply("❌ Não há cargos configurados. Use `/gamertag add` primeiro.", ephemeral=True)
            
        try:
            embed_color = discord.Color.from_str(cor) if cor else discord.Color.blue()
        except (ValueError, TypeError):
            embed_color = discord.Color.blue()

        embed = discord.Embed(title=titulo, color=embed_color)
        embed.set_image(url=imagem.url)

        # Criar o view com timeout None para persistir
        view = discord.ui.View(timeout=None)
        
        # Organizar os botões em linhas (máximo 5 botões por linha)
        buttons_per_row = 4  # Como na imagem, 4 botões por linha
        
        for i in range(0, len(buttons_config), buttons_per_row):
            # Pegar um grupo de botões para esta linha
            row_buttons = buttons_config[i:i + buttons_per_row]
            
            # Criar os botões para esta linha
            for button_config in row_buttons:
                role = ctx.guild.get_role(button_config['role_id'])
                if not role:
                    continue  # Pula se o cargo não existe mais
                
                button = discord.ui.Button(
                    label=button_config.get('label') or role.name,  # Use o nome do cargo se não houver label
                    emoji=button_config.get('emoji'),
                    style=discord.ButtonStyle.secondary,  # Botão cinza
                    custom_id=f"gamertag_role_{button_config['role_id']}"
                )
                view.add_item(button)

        try:
            message = await canal.send(embed=embed, view=view)
            
            # Salvar o message_id para poder recriar a view se o bot reiniciar
            config['gamertag_panel'] = {
                'channel_id': canal.id,
                'message_id': message.id
            }
            config_manager.save_server_config(ctx.guild.id, config)
            
            await ctx.reply(f"✅ Painel de Gamertag enviado para {canal.mention}!", ephemeral=True)
        except discord.Forbidden:
            await ctx.reply(f"❌ Não tenho permissão para enviar mensagens em {canal.mention}.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro ao enviar painel: {e}")
            await ctx.reply("❌ Ocorreu um erro ao enviar o painel.", ephemeral=True)

    @gamertag.command(name="recarregar", description="Recarrega o painel de cargos após reinicialização do bot.")
    @commands.has_permissions(administrator=True)
    async def reload_panel(self, ctx: commands.Context):
        """Recarrega as views dos painéis após restart do bot."""
        config = config_manager.get_server_config(ctx.guild.id)
        panel_config = config.get('gamertag_panel')
        buttons_config = config.get('gamertag_buttons', [])
        
        if not panel_config or not buttons_config:
            return await ctx.reply("❌ Não há painéis configurados para recarregar.", ephemeral=True)
        
        try:
            channel = self.bot.get_channel(panel_config['channel_id'])
            if not channel:
                return await ctx.reply("❌ Canal do painel não encontrado.", ephemeral=True)
            
            message = await channel.fetch_message(panel_config['message_id'])
            if not message:
                return await ctx.reply("❌ Mensagem do painel não encontrada.", ephemeral=True)
            
            # Recriar a view
            view = discord.ui.View(timeout=None)
            buttons_per_row = 4
            
            for i in range(0, len(buttons_config), buttons_per_row):
                row_buttons = buttons_config[i:i + buttons_per_row]
                
                for button_config in row_buttons:
                    role = ctx.guild.get_role(button_config['role_id'])
                    if not role:
                        continue
                    
                    button = discord.ui.Button(
                        label=button_config.get('label') or role.name,
                        emoji=button_config.get('emoji'),
                        style=discord.ButtonStyle.secondary,
                        custom_id=f"gamertag_role_{button_config['role_id']}"
                    )
                    view.add_item(button)
            
            await message.edit(view=view)
            await ctx.reply("✅ Painel de Gamertag recarregado com sucesso!", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao recarregar painel: {e}")
            await ctx.reply("❌ Erro ao recarregar o painel.", ephemeral=True)

async def setup(bot: commands.Bot):
    """Carrega o Cog de Gamertag no bot."""
    await bot.add_cog(GamertagCog(bot))