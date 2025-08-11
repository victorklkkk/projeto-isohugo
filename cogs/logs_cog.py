# cogs/logs_cog.py
import discord
from discord.ext import commands
import datetime
import asyncio # Precisaremos para o delay do registo de auditoria
from .utils import config_manager

class LogsCog(commands.Cog):
    """Cog para registrar diversas atividades do servidor em canais específicos."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- COMANDOS DE CONFIGURAÇÃO (Sem alterações) ---
    @commands.hybrid_group(name="logs", description="Configura os canais de logs do servidor.")
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("Comando de logs inválido. Use `/logs set <tipo> <canal>` para configurar.", ephemeral=True)

    @logs.command(name="set", description="Define um canal para um tipo específico de log.")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx: commands.Context, tipo: str, canal: discord.TextChannel):
        tipos_validos = ["membros", "cargos", "voz", "moderacao"]
        if tipo.lower() not in tipos_validos:
            return await ctx.send(f"❌ Tipo de log inválido. Use um dos seguintes: `{', '.join(tipos_validos)}`", ephemeral=True)
        server_config = config_manager.get_server_config(ctx.guild.id)
        if 'log_channels' not in server_config:
            server_config['log_channels'] = {}
        server_config['log_channels'][tipo.lower()] = canal.id
        config_manager.save_server_config(ctx.guild.id, server_config)
        await ctx.send(f"✅ Canal de logs para `{tipo.lower()}` definido como {canal.mention}.", ephemeral=True)

    # --- EVENT LISTENERS (Com Melhorias) ---

    async def _send_log(self, guild_id: int, log_type: str, embed: discord.Embed):
        server_config = config_manager.get_server_config(guild_id)
        channel_id = server_config.get('log_channels', {}).get(log_type)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel and channel.permissions_for(channel.guild.me).send_messages:
                await channel.send(embed=embed)

    # -- Eventos de Membros (Sem alterações) --
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = discord.Embed(title="📥 Membro Entrou", description=f"{member.mention} (`{member.id}`)", color=discord.Color.green(), timestamp=datetime.datetime.now(datetime.timezone.utc))
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Conta Criada em", value=f"<t:{int(member.created_at.timestamp())}:F>")
        await self._send_log(member.guild.id, "membros", embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = discord.Embed(title="📤 Membro Saiu", description=f"{member.mention} (`{member.id}`)", color=discord.Color.dark_orange(), timestamp=datetime.datetime.now(datetime.timezone.utc))
        embed.set_thumbnail(url=member.display_avatar.url)
        await self._send_log(member.guild.id, "membros", embed)

    # -- Eventos de Moderação (ATUALIZADOS) --
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        autor = "Desconhecido"
        # Procura no registo de auditoria quem realizou o ban
        await asyncio.sleep(1) # Pequeno delay para garantir que o log foi escrito
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target == user:
                    autor = entry.user.mention
                    break
        except discord.Forbidden:
            autor = "Permissão de ver registo de auditoria em falta"

        embed = discord.Embed(title="🔨 Membro Banido", description=f"**Usuário:** {user.mention} (`{user.id}`)", color=discord.Color.red(), timestamp=datetime.datetime.now(datetime.timezone.utc))
        embed.add_field(name="Ação por", value=autor, inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        await self._send_log(guild.id, "moderacao", embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        autor = "Desconhecido"
        await asyncio.sleep(1)
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
                if entry.target == user:
                    autor = entry.user.mention
                    break
        except discord.Forbidden:
            autor = "Permissão de ver registo de auditoria em falta"

        embed = discord.Embed(title="✨ Membro Desbanido", description=f"**Usuário:** {user.mention} (`{user.id}`)", color=discord.Color.blue(), timestamp=datetime.datetime.now(datetime.timezone.utc))
        embed.add_field(name="Ação por", value=autor, inline=False)
        await self._send_log(guild.id, "moderacao", embed)

    # -- Eventos de Cargos (ATUALIZADOS) --
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles != after.roles:
            autor = "Desconhecido"
            await asyncio.sleep(1)
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    if entry.target == after and (set(before.roles) != set(entry.before.roles) or set(after.roles) != set(entry.after.roles)):
                        autor = entry.user.mention
                        break
            except discord.Forbidden:
                autor = "Permissão de ver registo de auditoria em falta"

            # Cargo adicionado
            if len(before.roles) < len(after.roles):
                added_role = next(role for role in after.roles if role not in before.roles)
                embed = discord.Embed(title="➕ Cargo Adicionado", description=f"O cargo {added_role.mention} foi **adicionado** a {after.mention}.", color=discord.Color.light_grey(), timestamp=datetime.datetime.now(datetime.timezone.utc))
                embed.add_field(name="Ação por", value=autor, inline=False)
                await self._send_log(after.guild.id, "cargos", embed)
            # Cargo removido
            else:
                removed_role = next(role for role in before.roles if role not in after.roles)
                embed = discord.Embed(title="➖ Cargo Removido", description=f"O cargo {removed_role.mention} foi **removido** de {after.mention}.", color=discord.Color.dark_grey(), timestamp=datetime.datetime.now(datetime.timezone.utc))
                embed.add_field(name="Ação por", value=autor, inline=False)
                await self._send_log(after.guild.id, "cargos", embed)
    
    # -- Eventos de Voz (Sem alterações) --
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(title="🎤 Entrou em Canal de Voz", description=f"{member.mention} entrou em {after.channel.mention}", color=0x99aab5, timestamp=datetime.datetime.now(datetime.timezone.utc))
            await self._send_log(member.guild.id, "voz", embed)
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(title="🔇 Saiu de Canal de Voz", description=f"{member.mention} saiu de {before.channel.mention}", color=0x738bd7, timestamp=datetime.datetime.now(datetime.timezone.utc))
            await self._send_log(member.guild.id, "voz", embed)
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            embed = discord.Embed(title="🔁 Mudou de Canal de Voz", description=f"{member.mention} moveu-se de {before.channel.mention} para {after.channel.mention}", color=0x7289da, timestamp=datetime.datetime.now(datetime.timezone.utc))
            await self._send_log(member.guild.id, "voz", embed)

async def setup(bot: commands.Bot):
    """Carrega o Cog de Logs no bot."""
    await bot.add_cog(LogsCog(bot))