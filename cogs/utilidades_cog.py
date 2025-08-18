# cogs/utilidades_cog.py
import discord
from discord.ext import commands
import datetime
import traceback
from .utils import db_manager

class UtilidadesCog(commands.Cog):
    """Cog para comandos de utilidade geral e rastreamento de tempo em call."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dicionário para armazenar o tempo de entrada da SESSÃO ATUAL (em memória)
        self.voice_join_times = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """Verifica quem já está em canais de voz quando o bot inicia."""
        print("COG Utilidades: Verificando membros em canais de voz...")
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if not member.bot and member.id not in self.voice_join_times:
                        self.voice_join_times[member.id] = datetime.datetime.now(datetime.timezone.utc)
        print(f"COG Utilidades: Rastreando {len(self.voice_join_times)} membro(s) que já estavam em call.")

    def _format_seconds(self, total_seconds: int) -> str:
        """Formata segundos para um formato HH:MM:SS."""
        if total_seconds == 0:
            return "00:00:00"
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

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

    # --- LÓGICA DE VOZ FINAL ---
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        # Usuário ENTROU em call (veio do nada para um canal)
        if before.channel is None and after.channel is not None:
            self.voice_join_times[member.id] = datetime.datetime.now(datetime.timezone.utc)
        
        # Usuário SAIU de call (foi de um canal para NENHUM)
        elif before.channel is not None and after.channel is None:
            if member.id in self.voice_join_times:
                join_time = self.voice_join_times.pop(member.id)
                duration_seconds = int((datetime.datetime.now(datetime.timezone.utc) - join_time).total_seconds())
                
                # Atualiza o recorde na base de dados, se a sessão for maior
                if duration_seconds > 0:
                    db_manager.update_longest_session(member.id, duration_seconds)
        
        # Se o usuário apenas mudou de canal, não fazemos nada. O cronómetro continua.

    @commands.hybrid_command(name="calltime", description="Mostra o tempo da sua sessão atual em call.")
    async def calltime(self, ctx: commands.Context, *, usuario: discord.Member = None):
        try:
            target_user = None
            if ctx.message.reference and ctx.message.reference.resolved:
                target_user = ctx.message.reference.resolved.author
            elif usuario:
                target_user = usuario
            else:
                target_user = ctx.author

            # Pega o recorde de maior sessão do banco de dados
            maior_sessao_db = db_manager.get_longest_session(target_user.id)
            longest_session_str = self._format_seconds(maior_sessao_db)
            
            # Calcula o tempo da sessão ATUAL a partir da memória
            tempo_sessao_atual = 0
            if target_user.id in self.voice_join_times:
                join_time = self.voice_join_times[target_user.id]
                tempo_sessao_atual = int((datetime.datetime.now(datetime.timezone.utc) - join_time).total_seconds())
            
            current_session_str = self._format_seconds(tempo_sessao_atual)

            embed = discord.Embed(title="Call Time", color=0xFFFFFF)
            embed.set_thumbnail(url=target_user.display_avatar.url)
            
            # Campo "Tempo em call" agora mostra a sessão atual
            embed.add_field(name="<:temposuki:1406861880990892142> Tempo na call atual", value=f"`{current_session_str}`", inline=False)
            embed.add_field(name="<:membros:1406847577445634068> Usuário", value=target_user.mention, inline=False)
            
            if target_user.voice and target_user.voice.channel:
                embed.add_field(name="<:c_mic:1406848406776840192> Canal Atual", value=target_user.voice.channel.mention, inline=False)
            else:
                embed.add_field(name="<:c_mic:1406848406776840192> Canal Atual", value="Não está em um canal de voz.", inline=False)
            
            # Campo "Maior tempo em call" mostra o recorde guardado
            embed.add_field(name="<:white_coroa:1406849978781138974> Maior tempo em call", value=f"`{longest_session_str}`", inline=False)

            await ctx.reply(embed=embed)
        
        except Exception as e:
            print(f"Ocorreu um erro no comando /calltime:")
            traceback.print_exc()
            await ctx.reply("❌ Ocorreu um erro interno ao executar este comando.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilidadesCog(bot))