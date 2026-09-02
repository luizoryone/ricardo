import sqlite3

from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# 1. CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "audiencia.db"



# ============================================================
# 2. HORÁRIO UTC
# ============================================================

def utc_now():
    """
    Retorna data/hora atual em UTC no formato ISO 8601.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()



# ============================================================
# 3. CONEXÃO
# ============================================================

def connect():
    """
    Cria uma conexão SQLite configurada para a aplicação.
    """

    conn = sqlite3.connect(
        DB_PATH,
        timeout=10
    )


    # Permite:
    #
    # row["user_id"]
    #
    # em vez de:
    #
    # row[0]
    conn.row_factory = sqlite3.Row


    # SQLite não ativa FOREIGN KEY
    # automaticamente em toda conexão.
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )


    return conn



# ============================================================
# 4. INICIALIZAÇÃO DO BANCO
# ============================================================

def init_db():
    """
    Cria tabelas e índices necessários.
    """

    with connect() as conn:


        # ----------------------------------------------------
        # USERS
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (

                user_id TEXT PRIMARY KEY,

                display_name TEXT,

                created_at TEXT NOT NULL,

                last_seen_at TEXT NOT NULL

            )
            """
        )


        # ----------------------------------------------------
        # INTERACTIONS
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interactions (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id TEXT NOT NULL,

                track_id TEXT NOT NULL,

                event_type TEXT NOT NULL,

                created_at TEXT NOT NULL,

                FOREIGN KEY(user_id)
                    REFERENCES users(user_id)

            )
            """
        )


        # ----------------------------------------------------
        # ÍNDICES
        # ----------------------------------------------------

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_interactions_user

            ON interactions(user_id)
            """
        )


        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_interactions_track

            ON interactions(track_id)
            """
        )



# ============================================================
# 5. CRIAR USUÁRIO
# ============================================================

def create_user(
    user_id,
    display_name=None
):
    """
    Cria um usuário.
    """

    now = utc_now()


    with connect() as conn:

        conn.execute(
            """
            INSERT INTO users (

                user_id,
                display_name,
                created_at,
                last_seen_at

            )

            VALUES (?, ?, ?, ?)
            """,

            (
                user_id,
                display_name,
                now,
                now
            )
        )



# ============================================================
# 6. CONSULTAR USUÁRIO
# ============================================================

def get_user(user_id):
    """
    Busca um usuário pelo ID.
    """

    with connect() as conn:

        row = conn.execute(
            """
            SELECT

                user_id,
                display_name,
                created_at,
                last_seen_at

            FROM users

            WHERE user_id = ?
            """,

            (user_id,)
        ).fetchone()


    if row is None:
        return None


    return dict(row)



# ============================================================
# 7. ATUALIZAR ÚLTIMO ACESSO
# ============================================================

def touch_user(user_id):
    """
    Atualiza o horário do último acesso.
    """

    now = utc_now()


    with connect() as conn:

        conn.execute(
            """
            UPDATE users

            SET last_seen_at = ?

            WHERE user_id = ?
            """,

            (
                now,
                user_id
            )
        )



# ============================================================
# 8. GRAVAR INTERAÇÃO
# ============================================================

def save_interaction(
    user_id,
    track_id,
    event_type
):
    """
    Registra uma nova interação do usuário.
    """

    now = utc_now()


    with connect() as conn:

        cursor = conn.execute(
            """
            INSERT INTO interactions (

                user_id,
                track_id,
                event_type,
                created_at

            )

            VALUES (?, ?, ?, ?)
            """,

            (
                user_id,
                str(track_id),
                str(event_type),
                now
            )
        )


        # Retorna o ID da interação criada.
        return cursor.lastrowid



# ============================================================
# 9. HISTÓRICO DO USUÁRIO
# ============================================================

def get_interactions(user_id):
    """
    Retorna o histórico completo de um usuário.
    """

    with connect() as conn:

        rows = conn.execute(
            """
            SELECT

                id,
                track_id,
                event_type,
                created_at

            FROM interactions

            WHERE user_id = ?

            ORDER BY id ASC
            """,

            (user_id,)
        ).fetchall()


    return [
        dict(row)
        for row in rows
    ]



# ============================================================
# 10. QUANTIDADE DE INTERAÇÕES
# ============================================================

def count_interactions(user_id):
    """
    Conta quantas interações pertencem ao usuário.
    """

    with connect() as conn:

        row = conn.execute(
            """
            SELECT COUNT(*) AS total

            FROM interactions

            WHERE user_id = ?
            """,

            (user_id,)
        ).fetchone()


    return int(
        row["total"]
    )



# ============================================================
# 11. DIAGNÓSTICO DO BANCO
# ============================================================

def database_info():
    """
    Retorna informações simples para diagnóstico.
    """

    with connect() as conn:

        users = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM users
            """
        ).fetchone()


        interactions = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM interactions
            """
        ).fetchone()


    return {

        "database":
            str(DB_PATH),

        "users":
            int(users["total"]),

        "interactions":
            int(interactions["total"])

    }
    

# import sqlite3
# from pathlib import Path
# from datetime import datetime, timezone


# # ---------------------------------------------------------
# # CAMINHO DO BANCO
# # ---------------------------------------------------------

# BASE_DIR = Path(__file__).resolve().parent
# DB_PATH = BASE_DIR / "audiencia.db"


# # ---------------------------------------------------------
# # CONEXÃO
# # ---------------------------------------------------------

# def connect():
#     conn = sqlite3.connect(DB_PATH)

#     # Permite acessar:
#     # row["user_id"]
#     # em vez de apenas row[0]
#     conn.row_factory = sqlite3.Row

#     # Ativa verificação de FOREIGN KEY no SQLite
#     conn.execute("PRAGMA foreign_keys = ON")

#     return conn


# # ---------------------------------------------------------
# # CRIAÇÃO DAS TABELAS
# # ---------------------------------------------------------

# def init_db():

#     with connect() as conn:

#         # Usuários
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS users (
#                 user_id TEXT PRIMARY KEY,
#                 display_name TEXT,
#                 created_at TEXT NOT NULL,
#                 last_seen_at TEXT NOT NULL
#             )
#         """)

#         # Interações
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS interactions (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,

#                 user_id TEXT NOT NULL,
#                 track_id TEXT NOT NULL,
#                 event_type TEXT NOT NULL,

#                 created_at TEXT NOT NULL,

#                 FOREIGN KEY(user_id)
#                     REFERENCES users(user_id)
#             )
#         """)

#         # Índices para pesquisas futuras
#         conn.execute("""
#             CREATE INDEX IF NOT EXISTS idx_interactions_user
#             ON interactions(user_id)
#         """)

#         conn.execute("""
#             CREATE INDEX IF NOT EXISTS idx_interactions_track
#             ON interactions(track_id)
#         """)

#         conn.commit()
        
# def create_user(user_id, display_name=None):

#     now = datetime.now(timezone.utc).isoformat()

#     with connect() as conn:

#         conn.execute(
#             """
#             INSERT INTO users(
#                 user_id,
#                 display_name,
#                 created_at,
#                 last_seen_at
#             )
#             VALUES (?, ?, ?, ?)
#             """,
#             (
#                 user_id,
#                 display_name,
#                 now,
#                 now
#             )
#         )

#         conn.commit()


# def get_user(user_id):

#     with connect() as conn:

#         row = conn.execute(
#             """
#             SELECT *
#             FROM users
#             WHERE user_id = ?
#             """,
#             (user_id,)
#         ).fetchone()

#     if row is None:
#         return None

#     return dict(row)

# def touch_user(user_id):

#     now = datetime.now(timezone.utc).isoformat()

#     with connect() as conn:

#         conn.execute(
#             """
#             UPDATE users
#             SET last_seen_at = ?
#             WHERE user_id = ?
#             """,
#             (
#                 now,
#                 user_id
#             )
#         )

#         conn.commit()

# def save_interaction(
#     user_id,
#     track_id,
#     event_type
# ):

#     now = datetime.now(timezone.utc).isoformat()

#     with connect() as conn:

#         conn.execute(
#             """
#             INSERT INTO interactions(
#                 user_id,
#                 track_id,
#                 event_type,
#                 created_at
#             )
#             VALUES (?, ?, ?, ?)
#             """,
#             (
#                 user_id,
#                 track_id,
#                 event_type,
#                 now
#             )
#         )

#         conn.commit()

# def get_interactions(user_id):

#     with connect() as conn:

#         rows = conn.execute(
#             """
#             SELECT
#                 id,
#                 track_id,
#                 event_type,
#                 created_at
#             FROM interactions

#             WHERE user_id = ?

#             ORDER BY id
#             """,
#             (user_id,)
#         ).fetchall()

#     return [
#         dict(row)
#         for row in rows
#     ]

        

# # import sqlite3
# # from pathlib import Path

# # DB_PATH = Path(__file__).parent / 'audiencia.db'

# # def connect():
# #     conn = sqlite3.connect(DB_PATH)
# #     conn.row_factory = sqlite3.Row
# #     return conn

# # def init_db():
# #     with connect() as conn:
# #         conn.execute('''CREATE TABLE IF NOT EXISTS interactions (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             session_id TEXT NOT NULL,
# #             track_id TEXT NOT NULL,
# #             event_type TEXT NOT NULL,
# #             created_at DATETIME DEFAULT CURRENT_TIMESTAMP
# #         )''')
# #         conn.execute('CREATE INDEX IF NOT EXISTS idx_interactions_session ON interactions(session_id)')
# #         conn.commit()

# # def save_interaction(session_id, track_id, event_type):
# #     with connect() as conn:
# #         conn.execute('INSERT INTO interactions(session_id, track_id, event_type) VALUES (?, ?, ?)',
# #                      (session_id, track_id, event_type))
# #         conn.commit()

# # def get_interactions(session_id):
# #     with connect() as conn:
# #         rows = conn.execute('SELECT track_id, event_type, created_at FROM interactions WHERE session_id=? ORDER BY id',
# #                             (session_id,)).fetchall()
# #     return [dict(r) for r in rows]
