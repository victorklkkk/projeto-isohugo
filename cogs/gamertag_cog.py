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
            'label': label  # Pode ser None para aparecer só o emoji
        })
        
        config_manager.save_server_config(ctx.guild.id, config)
        
        label_text = f" com label '{label}'" if label else " (somente emoji)"
        await ctx.reply(f"✅ O botão para o cargo {cargo.mention}{label_text} foi adicionado à configuração.", ephemeral=True)

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
        """Envia o painel de cargos com os botões configurados usando Components v2."""
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

        # Criar as action rows (máximo 5 components por row, máximo 5 rows)
        components = []
        buttons_per_row = 4  # Como na imagem original
        
        for i in range(0, len(buttons_config), buttons_per_row):
            row_buttons = buttons_config[i:i + buttons_per_row]
            
            # Criar uma action row
            action_row = {
                "type": 1,  # ACTION_ROW
                "components": []
            }
            
            for button_config in row_buttons:
                role = ctx.guild.get_role(button_config['role_id'])
                if not role:
                    continue
                
                # Criar o botão usando Components v2
                button_component = {
                    "type": 2,  # BUTTON
                    "style": 2,  # SECONDARY (cinza)
                    "custom_id": f"gamertag_role_{button_config['role_id']}",
                    "emoji": {
                        "name": button_config.get('emoji', '❓')
                    }
                }
                
                # Só adiciona label se existir
                if button_config.get('label'):
                    button_component["label"] = button_config['label']
                
                action_row["components"].append(button_component)
            
            if action_row["components"]:  # Só adiciona se tiver botões
                components.append(action_row)

        try:
            # Enviar usando a API raw do Discord para garantir Components v2
            payload = {
                "embed": embed.to_dict(),
                "components": components
            }
            
            # Usar o método send do canal com a payload customizada
            message = await canal.send(embed=embed, view=self._create_persistent_view(buttons_config))
            
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

    def _create_persistent_view(self, buttons_config):
        """Cria uma view persistente para os botões."""
        view = discord.ui.View(timeout=None)
        buttons_per_row = 4
        
        for i, button_config in enumerate(buttons_config):
            role_id = button_config['role_id']
            emoji = button_config.get('emoji', '❓')
            label = button_config.get('label')  # None se não houver label
            
            button = discord.ui.Button(
                label=label,  # None = só emoji, string = emoji + texto
                emoji=emoji,
                style=discord.ButtonStyle.secondary,
                custom_id=f"gamertag_role_{role_id}"
            )
            
            view.add_item(button)
            
            # Quebrar linha a cada 4 botões (visual)
            if (i + 1) % buttons_per_row == 0 and i < len(buttons_config) - 1:
                # O discord.py automaticamente organiza os botões em rows
                pass
        
        return view

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
            
            # Recriar a view persistente
            view = self._create_persistent_view(buttons_config)
            
            await message.edit(view=view)
            await ctx.reply("✅ Painel de Gamertag recarregado com sucesso!", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Erro ao recarregar painel: {e}")
            await ctx.reply("❌ Erro ao recarregar o painel.", ephemeral=True)

    @gamertag.command(name="listar", description="Lista todos os botões configurados.")
    @commands.has_permissions(administrator=True)
    async def list_buttons(self, ctx: commands.Context):
        """Lista todos os botões configurados no painel."""
        config = config_manager.get_server_config(ctx.guild.id)
        buttons_config = config.get('gamertag_buttons', [])
        
        if not buttons_config:
            return await ctx.reply("❌ Não há botões configurados.", ephemeral=True)
        
        embed = discord.Embed(title="📋 Botões Configurados", color=discord.Color.blue())
        
        for i, button_config in enumerate(buttons_config, 1):
            role = ctx.guild.get_role(button_config['role_id'])
            role_name = role.name if role else "Cargo não encontrado"
            emoji = button_config.get('emoji', '❓')
            label = button_config.get('label', 'Sem label (só emoji)')
            
            embed.add_field(
                name=f"{i}. {emoji} {role_name}",
                value=f"Label: `{label}`\nID: `{button_config['role_id']}`",
                inline=True
            )
        
        await ctx.reply(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    """Carrega o Cog de Gamertag no bot."""
    await bot.add_cog(GamertagCog(bot))