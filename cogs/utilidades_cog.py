# cogs/utilidades_cog.py
import discord
from discord.ext import commands
import datetime
import traceback # Para log de erros detalhado
from .utils import db_manager

class UtilidadesCog(commands.Cog):
    """Cog para comandos de utilidade geral e rastreamento de tempo em call."""
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
        # ... (código do avatar sem alterações) ...
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

    # --- COMANDO CALLTIME ATUALIZADO ---
    @commands.hybrid_command(name="calltime", description="Mostra o seu tempo total em canais de voz.")
    async def calltime(self, ctx: commands.Context, *, usuario: discord.Member = None):
        """Verifica o tempo total de um usuário em canais de voz."""
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

            embed = discord.Embed(
                title="Call Time",
                color=0xFFFFFF # Cor branca
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Adiciona os campos com os seus emojis personalizados
            embed.add_field(name="<:temposuki:1377981862261030912> Tempo em call", value=f"`{total_time_str}`", inline=False)
            embed.add_field(name="<:membros:1406847577445634068> Usuário", value=target_user.mention, inline=False)
            
            if target_user.voice and target_user.voice.channel:
                embed.add_field(name="<:c_mic:1406848406776840192> Canal Atual", value=target_user.voice.channel.mention, inline=False)
            else:
                embed.add_field(name="<:c_mic:1406848406776840192> Canal Atual", value="Não está em um canal de voz.", inline=False)
                
            embed.add_field(name="<:white_coroa:1251022395905409135> Maior tempo em call", value=f"`{longest_session_str}`", inline=False)

            await ctx.reply(embed=embed)
        
        except Exception as e:
            # Novo sistema de log de erros: vai imprimir o erro detalhado na sua consola
            print(f"Ocorreu um erro no comando /calltime:")
            traceback.print_exc()
            
            # Responde ao usuário de forma genérica para não falhar a interação
            if ctx.interaction: # Verifica se é um slash command
                await ctx.interaction.response.send_message("❌ Ocorreu um erro interno ao executar este comando.", ephemeral=True)
            else:
                await ctx.reply("❌ Ocorreu um erro interno ao executar este comando.")


async def setup(bot: commands.Bot):
    """Carrega o Cog de Utilidades no bot."""
    await bot.add_cog(UtilidadesCog(bot))