# main.py
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from cogs.utils import db_manager

# Carrega as variáveis de ambiente e inicializa o banco de dados
load_dotenv()
db_manager.init_database()

# Configuração do Bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='y!', intents=intents)

TOKEN = os.getenv('DISCORD_TOKEN')

async def load_cogs():
    """Encontra e carrega todos os cogs na pasta principal /cogs."""
    for filename in os.listdir('./cogs'):
        # Carrega apenas ficheiros .py que estão na raiz de /cogs e não começam com __
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Cog carregado: {filename}')
            except Exception as e:
                print(f'❌ Falha ao carregar o cog {filename}: {e}')

@bot.event
async def on_ready():
    """Função executada quando o bot está pronto."""
    print('-------------------')
    print(f'Bot conectado como {bot.user.name}')
    print(f'ID do Bot: {bot.user.id}')
    print('Bot está pronto e funcional!')
    print('-------------------')

async def main():
    """Função principal que carrega os cogs e inicia a conexão do bot."""
    if TOKEN is None:
        print("ERRO: O DISCORD_TOKEN não foi encontrado. Certifique-se de que o ficheiro .env existe e está correto.")
        return
    
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

# Inicia a execução do bot
if __name__ == '__main__':
    asyncio.run(main())