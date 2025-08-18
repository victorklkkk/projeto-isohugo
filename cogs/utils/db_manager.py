# cogs/utils/db_manager.py
import sqlite3
import logging

# Define o nome do nosso ficheiro de base de dados
DB_FILE = "bot_database.db"
logger = logging.getLogger(__name__)

def init_database():
    """
    Cria o ficheiro da base de dados e a tabela de estatísticas de voz, se não existirem.
    Esta função será chamada uma vez quando o bot iniciar.
    """
    try:
        # Conecta-se ao ficheiro (cria-o se não existir)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Cria a tabela 'voice_stats'
        # user_id: O ID do usuário no Discord. É a chave primária.
        # total_voice_seconds: O tempo total acumulado em segundos.
        # longest_session_seconds: A maior sessão única em segundos.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_stats (
                user_id INTEGER PRIMARY KEY,
                total_voice_seconds INTEGER DEFAULT 0,
                longest_session_seconds INTEGER DEFAULT 0
            )
        """)
        
        conn.commit() # Salva as alterações
        conn.close()  # Fecha a conexão
        logger.info("Base de dados 'voice_stats' inicializada com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao inicializar a base de dados: {e}")

def update_user_voicetime(user_id: int, session_duration: int):
    """
    Pega a duração de uma sessão de voz e atualiza os totais do usuário no banco de dados.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Garante que o usuário existe na tabela antes de tentar atualizar.
        # Se não existir, insere-o com valores padrão (0).
        cursor.execute("INSERT OR IGNORE INTO voice_stats (user_id) VALUES (?)", (user_id,))
        
        # Pega os valores atuais do usuário no banco de dados
        cursor.execute("SELECT total_voice_seconds, longest_session_seconds FROM voice_stats WHERE user_id = ?", (user_id,))
        current_total, current_longest = cursor.fetchone()
        
        # Calcula os novos valores
        new_total = current_total + session_duration
        new_longest = max(current_longest, session_duration)
        
        # Atualiza a tabela com os novos totais
        cursor.execute("""
            UPDATE voice_stats 
            SET total_voice_seconds = ?, longest_session_seconds = ?
            WHERE user_id = ?
        """, (new_total, new_longest, user_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao atualizar tempo de voz para {user_id}: {e}")

def get_user_voicetime(user_id: int):
    """
    Busca no banco de dados o tempo total e a maior sessão de um usuário específico.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT total_voice_seconds, longest_session_seconds FROM voice_stats WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        # Se encontrarmos um resultado, retornamos os dados.
        if result:
            return {'total': result[0], 'longest': result[1]}
        
        # Se o usuário ainda não estiver no banco de dados, retorna 0.
        return {'total': 0, 'longest': 0}
    except Exception as e:
        logger.error(f"Erro ao obter tempo de voz para {user_id}: {e}")
        return {'total': 0, 'longest': 0}