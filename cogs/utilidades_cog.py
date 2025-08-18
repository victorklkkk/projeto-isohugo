# cogs/utilidades_cog.py
import discord
from discord.ext import commands
import datetime
from .utils import db_manager

class UtilidadesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_join_times = {}

    def _format_seconds(self, total_seconds: int) -> str:
        if total_seconds == 0:
            return "Nenhum tempo registado"
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = []
        if days > 0: parts.append(f"{days}d")
        if hours > 0: parts.append(f"{hours}h")
        if minutes > 0: parts.append(f"{minutes}m")
        if not any([days, hours, minutes]) and seconds > 0:
            parts.append(f"{seconds}s")
        return " ".join(parts) if parts else "0s"

    @commands.hybrid_command(name="av", description="Mostra o avatar de um usuário.")
    async def avatar(self, ctx: commands.Context, *, usuario: discord.User = None):
        try:
            target_user = None
            if ctx.message.reference and ctx.message.reference.resolved:
                target_user = ctx.message.reference.resolved.author
            elif usuario:
                target_user = usuario
            else:
                target_user = ctx.author

            avatar_url = target_user.display_avatar.with_size(1024).url
            cor_embed = getattr(target_user, 'color', 0xFFFFFF) or 0xFFFFFF
            embed = discord.Embed(title=f"Avatar de {target_user.display_name}", color=cor_embed)
            embed.set_image(url=avatar_url)
            embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Baixar", style=discord.ButtonStyle.secondary, url=avatar_url))
            await ctx.reply(embed=embed, view=view)
        except Exception as e:
            await ctx.reply(f"❌ Ocorreu um erro ao buscar o avatar: {e}", ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot: return
        if after.channel is not None and before.channel != after.channel:
            self.voice_join_times[member.id] = datetime.datetime.now(datetime.timezone.utc)
        elif before.channel is not None and after.channel is None:
            if member.id in self.voice_join_times:
                join_time = self.voice_join_times.pop(member.id)
                duration_seconds = int((datetime.datetime.now(datetime.timezone.utc) - join_time).total_seconds())
                if duration_seconds > 0:
                    db_manager.update_user_voicetime(member.id, duration_seconds)

    @commands.hybrid_command(name="wcalltime", description="Mostra o seu tempo total em canais de voz.")
    async def wcalltime(self, ctx: commands.Context, *, usuario: discord.Member = None):
        try:
            target_user = None
            if ctx.message.reference and ctx.message.reference.resolved:
                target_user = ctx.message.reference.resolved.author
            elif usuario:
                target_user = usuario
            else:
                target_user = ctx.author

            user_stats = db_manager.get_user_voicetime(target_user.id)
            total_time_str = self._format_seconds(user_stats['total'])
            longest_session_str = self._format_seconds(user_stats['longest'])

            embed = discord.Embed(title="Call Time", color=0xFFFFFF)
            embed.set_thumbnail(url=target_user.display_avatar.url)

            # --- EMOJIS ATUALIZADOS PARA VERSÕES PADRÃO ---
            # Se o seu bot tiver acesso aos emojis personalizados, pode trocá-los de volta.
            embed.add_field(name="⏰ Tempo em call", value=f"`{total_time_str}`", inline=False)
            embed.add_field(name="👤 Usuário", value=target_user.mention, inline=False)
            
            if target_user.voice and target_user.voice.channel:
                embed.add_field(name="🎤 Canal Atual", value=target_user.voice.channel.mention, inline=False)
            else:
                embed.add_field(name="🎤 Canal Atual", value="Não está em um canal de voz.", inline=False)
            
            embed.add_field(name="👑 Maior tempo em call", value=f"`{longest_session_str}`", inline=False)

            await ctx.reply(embed=embed)
        except Exception as e:
            # Tratamento de erro para garantir que o bot sempre responda
            await ctx.reply(f"❌ Ocorreu um erro ao executar o comando: `{e}`", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilidadesCog(bot))