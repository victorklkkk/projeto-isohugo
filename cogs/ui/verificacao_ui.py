# cogs/ui/verificacao_ui.py
import discord
from discord import ui
import logging
from ..utils import config_manager

logger = logging.getLogger(__name__)

# As classes AdminApprovalView e VerificationView não precisam de alterações

class AdminApprovalView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    async def get_member_from_embed(self, interaction: discord.Interaction):
        try:
            embed = interaction.message.embeds[0]
            member_id = int(embed.footer.text.split(': ')[1])
            return interaction.guild.get_member(member_id)
        except Exception: return None
    @ui.button(label="Aprovar", style=discord.ButtonStyle.green, custom_id="aprovar_verificacao_v2")
    async def aprovar_callback(self, interaction: discord.Interaction, button: ui.Button):
        membro = await self.get_member_from_embed(interaction)
        if not membro: return await interaction.response.send_message("❌ Membro solicitante não encontrado.", ephemeral=True)
        config = config_manager.get_server_config(interaction.guild.id)
        cargo = interaction.guild.get_role(config.get('cargo_verificado'))
        if not cargo: return await interaction.response.send_message("❌ Cargo de verificação não configurado.", ephemeral=True)
        try:
            await membro.add_roles(cargo)
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Sem permissão para atribuir o cargo.", ephemeral=True)
        for item in self.children: item.disabled = True
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(name="✅ Status", value=f"Aprovado por {interaction.user.mention}", inline=False)
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"✅ {membro.mention} verificado!", ephemeral=True)
    @ui.button(label="Reprovar", style=discord.ButtonStyle.red, custom_id="reprovar_verificacao_v2")
    async def reprovar_callback(self, interaction: discord.Interaction, button: ui.Button):
        membro = await self.get_member_from_embed(interaction)
        for item in self.children: item.disabled = True
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(name="❌ Status", value=f"Reprovado por {interaction.user.mention}", inline=False)
        await interaction.message.edit(embed=embed, view=self)
        if membro: await interaction.response.send_message(f"❌ Verificação de {membro.mention} reprovada.", ephemeral=True)
        else: await interaction.response.send_message(f"❌ Verificação reprovada.", ephemeral=True)

# --- SELETOR DE USUÁRIO ATUALIZADO ---
class MemberUserSelect(ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="Selecione o membro que você conhece...")

    async def callback(self, interaction: discord.Interaction):
        selected_member = self.values[0]

        if selected_member.bot:
            return await interaction.response.send_message("❌ Você não pode selecionar um bot.", ephemeral=True)

        config = config_manager.get_server_config(interaction.guild.id)
        canal_logs = interaction.client.get_channel(config.get('canal_logs'))

        if not canal_logs:
            return await interaction.response.send_message("❌ Canal de logs não encontrado!", ephemeral=True)
        
        # Pega as configurações de personalização da ficha
        ficha_config = config.get('ficha_embed', {})
        ficha_titulo = ficha_config.get('titulo', '📥 Novo Pedido de Verificação')
        ficha_cor = discord.Color.from_str(ficha_config.get('cor', '#3498db'))

        embed = discord.Embed(title=ficha_titulo, color=ficha_cor)
        embed.add_field(name="👤 Solicitante", value=interaction.user.mention, inline=True)
        embed.add_field(name="👥 Indicou Conhecer", value=selected_member.mention, inline=True)
        embed.set_footer(text=f"ID: {interaction.user.id}")
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)

        await canal_logs.send(embed=embed, view=AdminApprovalView())
        await interaction.response.send_message("✅ Seu pedido foi enviado para análise!", ephemeral=True)

class VerificationView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Verify", style=discord.ButtonStyle.secondary, custom_id="iniciar_verificacao_v2")
    async def verify_button_callback(self, interaction: discord.Interaction, button: ui.Button):
        config = config_manager.get_server_config(interaction.guild.id)
        if not config:
            return await interaction.response.send_message("❌ Sistema de verificação não configurado.", ephemeral=True)
        
        view = ui.View(timeout=180)
        view.add_item(MemberUserSelect())
        await interaction.response.send_message("Selecione um membro da lista abaixo:", view=view, ephemeral=True)