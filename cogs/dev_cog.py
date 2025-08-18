# cogs/dev_cog.py
import discord
from discord.ext import commands

class ContainerView(discord.ui.View):
    """View personalizada para o container com botões funcionais."""
    
    def __init__(self):
        super().__init__(timeout=300)  # 5 minutos de timeout
    
    @discord.ui.button(label="Voltar", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def voltar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Voltando...", ephemeral=True)
    
    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.green, emoji="✅")
    async def confirmar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ação confirmada!", ephemeral=True)
    
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.red, emoji="❌")
    async def cancelar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ação cancelada!", ephemeral=True)
    
    @discord.ui.button(label="Recarregar", style=discord.ButtonStyle.primary, emoji="🔄")
    async def recarregar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Atualiza a mensagem original
        novo_conteudo = """```ansi
[2;32m╭─────────────────────────────────╮[0m
[2;32m│[0m [1;37mEste é um container[0m            [2;32m│[0m
[2;32m│[0m [0;36m• Parecido com os embeds[0m       [2;32m│[0m
[2;32m│[0m [0;33m• Recarregado com sucesso![0m     [2;32m│[0m
[2;32m╰─────────────────────────────────╯[0m
```"""
        await interaction.response.edit_message(content=novo_conteudo, view=self)

class DevCog(commands.Cog):
    """Cog para comandos de desenvolvedor."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, spec: str = None):
        """Sincroniza os comandos de barra (/) com o Discord."""
        try:
            fmt = 0
            if spec == "guild":
                synced = await self.bot.tree.sync(guild=ctx.guild)
                fmt = len(synced)
                await ctx.reply(f"✅ Sincronizados **{fmt}** comandos para este servidor.")
            else:
                synced = await self.bot.tree.sync()
                fmt = len(synced)
                await ctx.reply(f"✅ Sincronizados **{fmt}** comandos globais.")
        except Exception as e:
            await ctx.reply(f"❌ Falha ao sincronizar: {e}")

    @commands.hybrid_command(name="container-simples", description="Container básico com texto simples")
    async def container_simples(self, ctx: commands.Context):
        """Versão mais simples do container."""
        
        texto = """**Este é um container**
• Parecido com os embeds
• Funciona com botões"""
        
        view = ContainerView()
        await ctx.send(content=texto, view=view)

    @commands.hybrid_command(name="container-box", description="Container com bordas usando caracteres especiais")
    async def container_box(self, ctx: commands.Context):
        """Container com visual de caixa usando caracteres Unicode."""
        
        texto = """```
╭─────────────────────────────────╮
│ Este é um container             │
│ • Parecido com os embeds        │
│ • Com bordas visuais            │
╰─────────────────────────────────╯
```"""
        
        view = ContainerView()
        await ctx.send(content=texto, view=view)

    @commands.hybrid_command(name="container-ansi", description="Container colorido usando ANSI")
    async def container_ansi(self, ctx: commands.Context):
        """Container com cores usando códigos ANSI."""
        
        texto = """```ansi
[2;32m╭─────────────────────────────────╮[0m
[2;32m│[0m [1;37mEste é um container[0m            [2;32m│[0m
[2;32m│[0m [0;36m• Parecido com os embeds[0m       [2;32m│[0m
[2;32m│[0m [0;33m• Com cores ANSI[0m               [2;32m│[0m
[2;32m╰─────────────────────────────────╯[0m
```"""
        
        view = ContainerView()
        await ctx.send(content=texto, view=view)

    @commands.hybrid_command(name="container-avancado", description="Container com múltiplas seções")
    async def container_avancado(self, ctx: commands.Context):
        """Container mais elaborado com múltiplas seções."""
        
        class AdvancedView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)
            
            @discord.ui.select(
                placeholder="Escolha uma opção...",
                options=[
                    discord.SelectOption(label="Opção 1", description="Primeira opção", emoji="1️⃣"),
                    discord.SelectOption(label="Opção 2", description="Segunda opção", emoji="2️⃣"),
                    discord.SelectOption(label="Opção 3", description="Terceira opção", emoji="3️⃣"),
                ]
            )
            async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
                await interaction.response.send_message(f"Você selecionou: {select.values[0]}", ephemeral=True)
            
            @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.green, row=1)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message("Confirmado!", ephemeral=True)
            
            @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.red, row=1)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message("Cancelado!", ephemeral=True)
        
        texto = """```ansi
[2;34m╭─────────────────────────────────╮[0m
[2;34m│[0m [1;33m⚡ Container Avançado[0m           [2;34m│[0m
[2;34m├─────────────────────────────────┤[0m
[2;34m│[0m [0;37mRecursos disponíveis:[0m          [2;34m│[0m
[2;34m│[0m [0;32m• Select menu interativo[0m       [2;34m│[0m
[2;34m│[0m [0;32m• Botões funcionais[0m            [2;34m│[0m
[2;34m│[0m [0;32m• Layout organizado[0m            [2;34m│[0m
[2;34m╰─────────────────────────────────╯[0m
```"""
        
        view = AdvancedView()
        await ctx.send(content=texto, view=view)

    # Comando original mantido para compatibilidade
    @commands.hybrid_command(name="teste-efeito", description="Cria uma mensagem com texto e componentes, sem embed.")
    async def teste_efeito(self, ctx: commands.Context):
        """Cria o efeito visual de 'container' usando texto simples + view."""
        
        texto_da_mensagem = "Este é um container\n• Parecido com os embeds"
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Voltar", style=discord.ButtonStyle.secondary))
        view.add_item(discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.green))
        view.add_item(discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.red))
        view.add_item(discord.ui.Button(label="Recarregar", style=discord.ButtonStyle.primary))
        
        await ctx.send(content=texto_da_mensagem, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(DevCog(bot))