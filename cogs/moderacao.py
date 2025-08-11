# cogs/moderacao.py
import discord
from discord.ext import commands

class ModeracaoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='nuke', description='Deleta o canal atual e recria com as mesmas configurações.')
    @commands.has_permissions(manage_channels=True)
    async def nuke_channel(self, ctx: commands.Context):
        """Deleta o canal atual e recria com as mesmas configurações."""
        try:
            channel = ctx.channel
            channel_data = {
                'name': channel.name, 'category': channel.category, 'position': channel.position,
                'topic': getattr(channel, 'topic', None), 'slowmode_delay': getattr(channel, 'slowmode_delay', 0),
                'nsfw': getattr(channel, 'nsfw', False), 'overwrites': channel.overwrites.copy(), 'type': channel.type
            }

            if isinstance(channel, discord.VoiceChannel):
                channel_data.update({'bitrate': channel.bitrate, 'user_limit': channel.user_limit, 'rtc_region': channel.rtc_region})

            # Usando reply para a confirmação inicial
            await ctx.reply("💣 **NUKE INICIADO!** Este canal será recriado em breve...", delete_after=5)
            
            await channel.delete(reason=f"Nuke executado por {ctx.author}")

            new_channel = await channel.category.create_text_channel(
                name=channel_data['name'], position=channel_data['position'],
                topic=channel_data['topic'], slowmode_delay=channel_data['slowmode_delay'],
                nsfw=channel_data['nsfw'], overwrites=channel_data['overwrites'],
                reason=f"Canal recriado via nuke por {ctx.author}"
            )

            await new_channel.send(f"Canal recriado por {ctx.author.mention} 💥")
            
        except discord.Forbidden:
            await ctx.reply("❌ Não tenho permissão para gerenciar canais!", delete_after=10)
        except discord.HTTPException as e:
            await ctx.reply(f"❌ Erro ao recriar o canal: {e}", delete_after=10)
        except Exception as e:
            await ctx.reply(f"❌ Erro inesperado: {e}", delete_after=10)

    @nuke_channel.error
    async def nuke_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ Você não tem permissão para usar este comando! (Necessário: Gerenciar Canais)", delete_after=10)
        else:
            await ctx.reply(f"❌ Erro ao executar o comando: {error}", delete_after=10)
            
    # --- COMANDO DE LIMPEZA PESSOAL ---
    @commands.hybrid_command(name="cl", description="Apaga as últimas 100 mensagens do próprio usuário no canal.")
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def clear_self(self, ctx: commands.Context):
        # Este comando mantém o send/delete para uma experiência mais "limpa"
        msg_confirmacao = await ctx.send(f"{ctx.author.mention}, estou a apagar as suas últimas mensagens...")
        
        def is_author(m):
            return m.author == ctx.author

        try:
            apagadas = await ctx.channel.purge(limit=101, check=is_author, before=msg_confirmacao)
            await msg_confirmacao.delete()
            await ctx.send(f"✅ {len(apagadas)} mensagens suas foram apagadas.", delete_after=10)
        except Exception as e:
            await msg_confirmacao.edit(content=f"Ocorreu um erro ao tentar apagar as mensagens.")
            print(f"Erro no comando !cl: {e}")

    @clear_self.error
    async def clear_self_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.Cooldown):
            await ctx.reply(f"🌊 Calma aí! Você só pode usar este comando a cada 2 minutos. Tente novamente em **{error.retry_after:.0f} segundos**.", delete_after=15)
        else:
            await ctx.reply(f"Ocorreu um erro inesperado ao executar o comando `cl`.", delete_after=10)

    # --- COMANDOS BAN E UNBAN ---
    @commands.hybrid_command(name="ban", description="Bane um usuário do servidor por menção ou ID.")
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx: commands.Context, usuario: discord.User, *, motivo: str = "Nenhum motivo fornecido."):
        if usuario.id == ctx.author.id:
            return await ctx.reply("❌ Você não pode banir a si mesmo.")

        try:
            embed_dm = discord.Embed(title=f"Você foi banido de {ctx.guild.name}", description=f"**Motivo:** {motivo}", color=discord.Color.red())
            await usuario.send(embed=embed_dm)
        except discord.Forbidden:
            await ctx.reply("⚠️ Não foi possível notificar o usuário por mensagem privada.", ephemeral=True)
        
        try:
            await ctx.guild.ban(usuario, reason=f"Banido por {ctx.author.name}: {motivo}", delete_message_days=0)
            embed_confirmacao = discord.Embed(
                title="🔨 Usuário Banido",
                description=f"**Usuário:** {usuario.mention} (`{usuario.id}`)\n**Motivo:** {motivo}",
                color=discord.Color.dark_red()
            )
            embed_confirmacao.set_footer(text=f"Ação por: {ctx.author.name}")
            await ctx.reply(embed=embed_confirmacao)
        except discord.Forbidden:
            await ctx.reply("❌ Erro de permissão. Não tenho poder para banir este usuário.")
        except Exception as e:
            await ctx.reply(f"❌ Ocorreu um erro inesperado: {e}")

    @commands.hybrid_command(name="unban", description="Desbane um usuário do servidor usando o seu ID.")
    @commands.has_permissions(ban_members=True)
    async def unban_member(self, ctx: commands.Context, usuario: discord.User, *, motivo: str = "N/A"):
        try:
            await ctx.guild.unban(usuario, reason=f"Desbanido por {ctx.author.name}. Motivo: {motivo}")
            embed_confirmacao = discord.Embed(
                title="✨ Usuário Desbanido",
                description=f"**Usuário:** {usuario.mention} (`{usuario.id}`)",
                color=discord.Color.green()
            )
            embed_confirmacao.set_footer(text=f"Ação por: {ctx.author.name}")
            await ctx.reply(embed=embed_confirmacao)
        except discord.NotFound:
            await ctx.reply("❌ Usuário não encontrado na lista de banidos.")
        except discord.Forbidden:
            await ctx.reply("❌ Erro de permissão. Não tenho poder para desbanir usuários.")
        except Exception as e:
            await ctx.reply(f"❌ Ocorreu um erro inesperado: {e}")

# A função setup que o bot procura em cada ficheiro de Cog.
async def setup(bot: commands.Bot):
    await bot.add_cog(ModeracaoCog(bot))