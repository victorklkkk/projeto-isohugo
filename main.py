# main.py
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from cogs.utils import db_manager

load_dotenv()
db_manager.init_database()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='y!', intents=intents)
TOKEN = os.getenv('DISCORD_TOKEN')

async def load_cogs():
    """Encontra e carrega todos os cogs na pasta /cogs, ignorando ficheiros especiais."""
    for folder in os.listdir('./cogs'):
        # Verifica se é uma pasta (como utils, ui)
        if os.path.isdir(f'./cogs/{folder}'):
            for filename in os.listdir(f'./cogs/{folder}'):
                # Condição para carregar ficheiros .py que não começam com __
                if filename.endswith('.py') and not filename.startswith('__'):
                    try:
                        await bot.load_extension(f'cogs.{folder}.{filename[:-3]}')
                        print(f'✅ Cog carregado: {folder}/{filename}')
                    except Exception as e:
                        print(f'❌ Falha ao carregar o cog {folder}/{filename}: {e}')
        # Verifica se é um ficheiro .py na raiz de cogs/
        elif folder.endswith('.py') and not folder.startswith('__'):
             try:
                await bot.load_extension(f'cogs.{folder[:-3]}')
                print(f'✅ Cog carregado: {folder}')
             except Exception as e:
                print(f'❌ Falha ao carregar o cog {folder}: {e}')


@bot.event
async def on_ready():
    print('-------------------')
    print(f'Bot conectado como {bot.user}')
    print(f'ID do Bot: {bot.user.id}')
    print('Bot está pronto e funcional!')
    print('-------------------')

async def main():
    if TOKEN is None:
        print("ERRO: O DISCORD_TOKEN não foi encontrado.")
        return
    
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())