# cogs/utils/db_manager.py
import sqlite3
import logging

DB_FILE = "bot_database.db"
logger = logging.getLogger(__name__)

def init_database():
    """Cria a base de dados e a nova tabela simplificada."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # A tabela agora só precisa de guardar o recorde de maior sessão
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_stats (
                user_id INTEGER PRIMARY KEY,
                longest_session_seconds INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
        logger.info("Base de dados 'voice_stats' (simplificada) inicializada.")
    except Exception as e:
        logger.error(f"Erro ao inicializar a base de dados: {e}")

def update_longest_session(user_id: int, session_duration: int):
    """Verifica e atualiza a maior sessão de um usuário, se necessário."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("INSERT OR IGNORE INTO voice_stats (user_id) VALUES (?)", (user_id,))
        
        cursor.execute("SELECT longest_session_seconds FROM voice_stats WHERE user_id = ?", (user_id,))
        current_longest = cursor.fetchone()[0]
        
        # Atualiza apenas se a nova sessão for maior que o recorde
        if session_duration > current_longest:
            cursor.execute("UPDATE voice_stats SET longest_session_seconds = ? WHERE user_id = ?", (session_duration, user_id))
            conn.commit()

        conn.close()
    except Exception as e:
        logger.error(f"Erro ao atualizar maior sessão para {user_id}: {e}")

def get_longest_session(user_id: int):
    """Obtém a maior sessão de um usuário a partir do banco de dados."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT longest_session_seconds FROM voice_stats WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Erro ao obter maior sessão para {user_id}: {e}")
        return 0