# cogs/utilidades_cog.py
import discord
from discord.ext import commands
import datetime

class UtilidadesCog(commands.Cog):
    """Cog para comandos de utilidade geral."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dicionário para armazenar o tempo de entrada dos membros em canais de voz
        self.voice_join_times = {}

    # --- COMANDO DE AVATAR ---
    @commands.hybrid_command(name="av", description="Mostra o avatar de um usuário.")
    async def avatar(self, ctx: commands.Context, *, usuario: discord.User = None):
        """Mostra o avatar de um usuário (membro do servidor ou por ID)."""
        target_user = None
        if ctx.message.reference and ctx.message.reference.resolved:
            target_user = ctx.message.reference.resolved.author
        elif usuario:
            target_user = usuario
        else:
            target_user = ctx.author

        avatar_asset = target_user.display_avatar
        avatar_url = avatar_asset.with_size(1024).url
        cor_embed = getattr(target_user, 'color', 0xFFFFFF) or 0xFFFFFF

        embed = discord.Embed(title=f"Avatar de {target_user.display_name}", color=cor_embed)
        embed.set_image(url=avatar_url)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Baixar", style=discord.ButtonStyle.secondary, url=avatar_url))
        await ctx.reply(embed=embed, view=view)

    # --- SISTEMA DE CONTADOR DE CALL ---

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Ouve eventos de voz para registrar entradas e saídas."""
        # Usuário entrou num canal de voz
        if before.channel is None and after.channel is not None:
            self.voice_join_times[member.id] = datetime.datetime.now(datetime.timezone.utc)
        
        # Usuário saiu de um canal de voz
        elif before.channel is not None and after.channel is None:
            if member.id in self.voice_join_times:
                del self.voice_join_times[member.id]

    @commands.hybrid_command(name="calltime", description="Mostra há quanto tempo um usuário está em call.")
    async def call_time(self, ctx: commands.Context, *, usuario: discord.Member = None):
        """Verifica o tempo de um usuário em um canal de voz."""
        target_user = None
        if ctx.message.reference and ctx.message.reference.resolved:
            target_user = ctx.message.reference.resolved.author
        elif usuario:
            target_user = usuario
        else:
            target_user = ctx.author
        
        # Verifica se temos o registro de entrada do usuário
        if target_user.id not in self.voice_join_times:
            return await ctx.reply(f"❌ {target_user.display_name} não está num canal de voz (ou entrou antes de eu ser iniciado).")

        # Calcula a duração
        join_time = self.voice_join_times[target_user.id]
        duration = datetime.datetime.now(datetime.timezone.utc) - join_time

        # Formata a duração para HH:MM:SS
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_duration = f"{hours:02}:{minutes:02}:{seconds:02}"

        embed = discord.Embed(
            title="🎤 Tempo em Canal de Voz",
            description=f"**Usuário:** {target_user.mention}\n**Canal:** {target_user.voice.channel.mention}",
            color=0x7289DA
        )
        embed.add_field(name="Tempo na chamada atual", value=f"`{formatted_duration}`")
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")

        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    """Carrega o Cog de Utilidades no bot."""
    await bot.add_cog(UtilidadesCog(bot))