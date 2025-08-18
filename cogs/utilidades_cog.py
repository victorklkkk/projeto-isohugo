# cogs/utilidades_cog.py
import discord
from discord.ext import commands
import datetime
from .utils import db_manager # Importa o nosso novo gestor de base de dados

class UtilidadesCog(commands.Cog):
    """Cog para comandos de utilidade geral e rastreamento de tempo em call."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dicionário para armazenar o tempo de entrada dos membros (temporário, em memória)
        self.voice_join_times = {}

    def _format_seconds(self, total_seconds: int) -> str:
        """Formata segundos para um formato legível (dias, horas, minutos)."""
        if total_seconds == 0:
            return "Nenhum tempo registado"
        
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} dia{'s' if days > 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hora{'s' if hours > 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minuto{'s' if minutes > 1 else ''}")
        
        # Se o tempo total for menos de um minuto, mostramos os segundos.
        if not parts and seconds > 0:
            parts.append(f"{seconds} segundo{'s' if seconds > 1 else ''}")

        return ", ".join(parts)

    # --- COMANDO DE AVATAR (sem alterações) ---
    @commands.hybrid_command(name="av", description="Mostra o avatar de um usuário.")
    async def avatar(self, ctx: commands.Context, *, usuario: discord.User = None):
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

    # --- NOVO SISTEMA DE CONTADOR DE CALL ---

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Ouve eventos de voz para registrar entradas e saídas e salvar no DB."""
        # Ignora bots
        if member.bot:
            return

        # Usuário saiu de um canal de voz (ou foi para AFK/silenciado no servidor)
        if before.channel is not None and (after.channel is None or after.channel != before.channel):
            if member.id in self.voice_join_times:
                join_time = self.voice_join_times.pop(member.id)
                duration_seconds = int((datetime.datetime.now(datetime.timezone.utc) - join_time).total_seconds())
                
                # Atualiza a base de dados com a duração da sessão que terminou
                if duration_seconds > 0:
                    db_manager.update_user_voicetime(member.id, duration_seconds)
        
        # Usuário entrou num canal de voz (vindo do nada ou mudando de canal)
        if after.channel is not None:
            # Regista o (novo) tempo de entrada
            self.voice_join_times[member.id] = datetime.datetime.now(datetime.timezone.utc)


    @commands.hybrid_command(name="wcalltime", description="Mostra o seu tempo total em canais de voz.")
    async def wcalltime(self, ctx: commands.Context, *, usuario: discord.Member = None):
        """Verifica o tempo total de um usuário em canais de voz."""
        target_user = None
        if ctx.message.reference and ctx.message.reference.resolved:
            target_user = ctx.message.reference.resolved.author
        elif usuario:
            target_user = usuario
        else:
            target_user = ctx.author

        # Pega os dados do banco de dados
        user_stats = db_manager.get_user_voicetime(target_user.id)
        total_time_str = self._format_seconds(user_stats['total'])
        longest_session_str = self._format_seconds(user_stats['longest'])

        # Cria a embed com o seu design
        embed = discord.Embed(
            title="Call Time",
            color=0xFFFFFF # Cor branca
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Adiciona os campos
        embed.add_field(name="<:temposuki:1377981862261030912> Tempo em call", value=f"`{total_time_str}`", inline=False)
        embed.add_field(name="<:membros:1406847577445634068> Usuário", value=target_user.mention, inline=False)
        
        # Verifica se o usuário está em call no momento
        if target_user.voice and target_user.voice.channel:
            embed.add_field(name="<:c_mic:1406848406776840192> Canal Atual", value=target_user.voice.channel.mention, inline=False)
        else:
            embed.add_field(name="<:c_mic:1406848406776840192> Canal Atual", value="Não está em um canal de voz.", inline=False)
            
        embed.add_field(name="<:white_coroa:1251022395905409135> Maior tempo em call", value=f"`{longest_session_str}`", inline=False)

        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    """Carrega o Cog de Utilidades no bot."""
    await bot.add_cog(UtilidadesCog(bot))