from pathlib import Path
import os

import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# 1. CONFIGURAÇÃO DO RECOMENDADOR
# ============================================================

FEATURES = [
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
]


# Peso atribuído a cada comportamento do usuário.
#
# Valores positivos:
# aproximam o perfil do usuário das características da música.
#
# Valores negativos:
# afastam o perfil das características daquela música.
EVENT_WEIGHTS = {
    "play": 1.0,
    "play_complete": 2.0,
    "like": 3.0,
    "save": 4.0,
    "skip": -2.0,
    "dislike": -4.0,
}


BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# 2. LOCALIZAÇÃO DO DATASET
# ============================================================

def _find_dataset():
    """
    Procura o dataset em diferentes locais possíveis.

    A variável de ambiente SPOTIFY_DATASET possui prioridade.
    """

    env = os.getenv("SPOTIFY_DATASET")

    candidates = [
        # Caminho definido externamente
        Path(env) if env else None,

        # Dataset na mesma pasta do recommender.py
        BASE_DIR / "dataset_clean.csv",
        BASE_DIR / "dataset_cleaned.csv",

        # Pasta Dataset dentro da pasta atual
        BASE_DIR / "Dataset" / "dataset_cleaned.csv",
        BASE_DIR / "Dataset" / "dataset.csv",

        # Pasta Dataset na raiz do projeto
        BASE_DIR.parent / "Dataset" / "dataset_cleaned.csv",
        BASE_DIR.parent / "Dataset" / "dataset.csv",

        # Possíveis estruturas antigas
        BASE_DIR.parent / "ricardo" / "dataset_clean.csv",
        BASE_DIR.parent / "ricardo" / "dataset_cleaned.csv",
    ]

    for path in candidates:

        if path is not None and path.exists():
            return path

    raise FileNotFoundError(
        "Dataset não encontrado. "
        "Defina a variável SPOTIFY_DATASET ou coloque "
        "dataset_clean.csv / dataset_cleaned.csv "
        "na pasta do projeto."
    )


# Descobre automaticamente o arquivo.
DATASET_PATH = _find_dataset()


# ============================================================
# 3. CARREGAMENTO DO DATASET
# ============================================================

df = pd.read_csv(DATASET_PATH)


# Colunas obrigatórias.
REQUIRED_COLUMNS = [
    "track_id",
    "track_name",
    "artists",
    "popularity",
] + FEATURES


missing = [
    column
    for column in REQUIRED_COLUMNS
    if column not in df.columns
]


if missing:
    raise ValueError(
        f"Colunas obrigatórias ausentes no dataset: {missing}"
    )


# ============================================================
# 4. PREPARAÇÃO DOS DADOS
# ============================================================

# Garante que as features matemáticas sejam numéricas.
for column in FEATURES:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# Popularidade também será tratada como número.
df["popularity"] = pd.to_numeric(
    df["popularity"],
    errors="coerce"
)


# Remove registros que não podem participar corretamente
# da recomendação.
df = df.dropna(
    subset=REQUIRED_COLUMNS
).copy()


# Padroniza o identificador como texto.
df["track_id"] = (
    df["track_id"]
    .astype(str)
    .str.strip()
)


# Remove possíveis IDs duplicados.
#
# Uma música deve possuir somente uma representação
# no espaço vetorial.
df = (
    df
    .drop_duplicates(
        subset="track_id",
        keep="first"
    )
    .reset_index(drop=True)
)


# ============================================================
# 5. PADRONIZAÇÃO DAS FEATURES
# ============================================================

scaler = StandardScaler()


# X será nossa matriz musical.
#
# linhas   -> músicas
# colunas  -> features
X = scaler.fit_transform(
    df[FEATURES]
)


# ============================================================
# 6. ÍNDICE track_id -> posição da matriz
# ============================================================

track_to_index = {
    track_id: index
    for index, track_id
    in enumerate(df["track_id"])
}


# ============================================================
# 7. COLUNAS DEVOLVIDAS PARA O FRONTEND
# ============================================================

# Estas são obrigatórias.
BASE_OUTPUT_COLUMNS = [
    "track_id",
    "track_name",
    "artists",
    "popularity",
]


# Estas são desejáveis, mas podem não existir
# em todos os datasets.
OPTIONAL_OUTPUT_COLUMNS = [
    "track_genre",
    "mood",
    "is_explicit",
]


def _output_columns():
    """
    Retorna apenas colunas realmente existentes no DataFrame.
    """

    columns = BASE_OUTPUT_COLUMNS.copy()

    for column in OPTIONAL_OUTPUT_COLUMNS:

        if column in df.columns:
            columns.append(column)

    return columns


# ============================================================
# 8. SERIALIZAÇÃO
# ============================================================

def _serialize(indices, scores=None):
    """
    Converte posições do DataFrame para estruturas Python
    que poderão ser transformadas em JSON pelo FastAPI.
    """

    output = []

    columns = _output_columns()

    for position, index in enumerate(indices):

        row = df.iloc[int(index)]

        item = {}

        for column in columns:

            value = row[column]

            # Evita colocar NaN dentro da resposta.
            if pd.isna(value):
                item[column] = None

            elif column == "popularity":
                item[column] = float(value)

            elif column == "is_explicit":
                item[column] = bool(value)

            else:
                item[column] = str(value)


        # Score somente existe para resultados de recomendação.
        if scores is not None:
            item["score"] = float(
                scores[position]
            )

        output.append(item)

    return output


# ============================================================
# 9. CATÁLOGO
# ============================================================

def catalog_sample(n=20):
    """
    Retorna músicas populares para exploração inicial.

    Esta função também funciona como fallback quando
    o usuário ainda não possui histórico suficiente.
    """

    n = max(
        1,
        min(
            int(n),
            len(df)
        )
    )

    top = (
        df
        .sort_values(
            "popularity",
            ascending=False
        )
        .head(n)
    )

    return _serialize(
        top.index.tolist()
    )


# ============================================================
# 10. BUSCA NO CATÁLOGO
# ============================================================

def search_catalog(query, n=20):
    """
    Pesquisa músicas por nome ou artista.
    """

    query = str(query).strip()

    if not query:
        return []


    n = max(
        1,
        min(
            int(n),
            100
        )
    )


    name_mask = (
        df["track_name"]
        .fillna("")
        .str.contains(
            query,
            case=False,
            regex=False
        )
    )


    artist_mask = (
        df["artists"]
        .fillna("")
        .str.contains(
            query,
            case=False,
            regex=False
        )
    )


    mask = (
        name_mask
        |
        artist_mask
    )


    # Entre os resultados encontrados,
    # mostramos primeiro os mais populares.
    result = (
        df.loc[mask]
        .sort_values(
            "popularity",
            ascending=False
        )
        .head(n)
    )


    return _serialize(
        result.index.tolist()
    )


# ============================================================
# 11. RECOMENDAÇÃO BASEADA NO PERFIL
# ============================================================

def profile_recommendations(
    interactions,
    n=12
):
    """
    Cria um perfil vetorial a partir das interações
    do usuário e retorna as músicas mais semelhantes.
    """

    usable = []

    interacted = set()


    # --------------------------------------------------------
    # 11.1 LER O HISTÓRICO
    # --------------------------------------------------------

    for interaction in interactions:

        track_id = str(
            interaction["track_id"]
        )

        event_type = str(
            interaction["event_type"]
        )


        # Guarda tudo que o usuário já avaliou.
        interacted.add(
            track_id
        )


        # Descobre a posição da música na matriz X.
        index = track_to_index.get(
            track_id
        )


        # Obtém o peso do comportamento.
        weight = EVENT_WEIGHTS.get(
            event_type,
            0.0
        )


        # Eventos desconhecidos ou músicas fora
        # do catálogo são ignorados.
        if index is not None and weight != 0:
            usable.append(
                (
                    index,
                    weight
                )
            )


    # --------------------------------------------------------
    # 11.2 USUÁRIO SEM HISTÓRICO ÚTIL
    # --------------------------------------------------------

    if not usable:
        return catalog_sample(n)


    # --------------------------------------------------------
    # 11.3 CRIAR O VETOR DO USUÁRIO
    # --------------------------------------------------------

    profile = np.zeros(
        X.shape[1],
        dtype=float
    )


    mass = 0.0


    for index, weight in usable:

        # Vetor da música multiplicado
        # pelo peso comportamental.
        profile += (
            weight
            *
            X[index]
        )


        # Quantidade total de evidência.
        mass += abs(
            weight
        )


    profile /= max(
        mass,
        1e-9
    )


    # --------------------------------------------------------
    # 11.4 PROTEÇÃO CONTRA PERFIL NULO
    # --------------------------------------------------------

    if np.linalg.norm(profile) < 1e-12:
        return catalog_sample(n)


    # --------------------------------------------------------
    # 11.5 SIMILARIDADE DO COSSENO
    # --------------------------------------------------------

    similarities = cosine_similarity(
        profile.reshape(
            1,
            -1
        ),
        X
    )[0]


    # --------------------------------------------------------
    # 11.6 REMOVER MÚSICAS JÁ INTERAGIDAS
    # --------------------------------------------------------

    candidates = [
        index
        for index, track_id
        in enumerate(df["track_id"])
        if track_id not in interacted
    ]


    # --------------------------------------------------------
    # 11.7 ORDENAR PELO SCORE
    # --------------------------------------------------------

    candidates.sort(
        key=lambda index:
            similarities[index],
        reverse=True
    )


    # --------------------------------------------------------
    # 11.8 TOP-N
    # --------------------------------------------------------

    n = max(
        1,
        min(
            int(n),
            len(candidates)
        )
    )


    top_indices = candidates[:n]


    top_scores = similarities[
        top_indices
    ]


    # --------------------------------------------------------
    # 11.9 CONVERTER PARA JSON
    # --------------------------------------------------------

    return _serialize(
        top_indices,
        top_scores
    )


# ============================================================
# 12. INFORMAÇÕES DO RECOMENDADOR
# ============================================================

def recommender_info():
    """
    Função auxiliar para diagnóstico da aplicação.
    """

    return {
        "dataset": str(DATASET_PATH),
        "tracks": int(len(df)),
        "features": FEATURES,
        "events": EVENT_WEIGHTS,
    }
    





# from pathlib import Path
# import os
# import numpy as np
# import pandas as pd
# from sklearn.preprocessing import StandardScaler
# from sklearn.metrics.pairwise import cosine_similarity

# FEATURES = ['danceability','energy','speechiness','acousticness','instrumentalness','liveness','valence','tempo']
# EVENT_WEIGHTS = {'play':1.0,'play_complete':2.0,'like':3.0,'save':4.0,'skip':-2.0,'dislike':-4.0}
# BASE_DIR = Path(__file__).resolve().parent

# def _find_dataset():
#     env = os.getenv('SPOTIFY_DATASET')
#     candidates = [Path(env) if env else None,
#                   BASE_DIR/'dataset_cleaned.csv',
#                   BASE_DIR/'Dataset'/'dataset_cleaned.csv',
#                   BASE_DIR.parent/'ricardo'/'dataset_cleaned.csv',
#                   BASE_DIR.parent/'Dataset'/'dataset_cleaned.csv',
#                   BASE_DIR.parent/'Dataset'/'dataset.csv']
#     for p in candidates:
#         if p and p.exists():
#             return p
#     raise FileNotFoundError('Dataset não encontrado. Defina SPOTIFY_DATASET ou copie dataset_clean.csv para esta pasta.')

# DATASET_PATH = _find_dataset()
# df = pd.read_csv(DATASET_PATH)
# required = ['track_id','track_name','artists','popularity'] + FEATURES
# missing = [c for c in required if c not in df.columns]
# if missing:
#     raise ValueError(f'Colunas ausentes: {missing}')
# df = df.dropna(subset=required).copy()
# df['track_id'] = df['track_id'].astype(str)
# df = df.drop_duplicates('track_id').reset_index(drop=True)
# scaler = StandardScaler()
# X = scaler.fit_transform(df[FEATURES])
# track_to_index = {tid:i for i, tid in enumerate(df['track_id'])}

# def _serialize(indices, scores=None):
#     out=[]
#     for pos, idx in enumerate(indices):
#         row=df.iloc[int(idx)]
#         item={'track_id':str(row.track_id),'track_name':str(row.track_name),'artists':str(row.artists),'popularity':float(row.popularity)}
#         if 'track_genre' in df.columns: item['track_genre']=str(row['track_genre'])
#         if scores is not None: item['score']=float(scores[pos])
#         out.append(item)
#     return out

# def catalog_sample(n=20):
#     top=df.sort_values('popularity',ascending=False).head(n)
#     return _serialize(top.index.tolist())

# def profile_recommendations(interactions,n=10):
#     usable=[]; interacted=set()
#     for e in interactions:
#         tid=str(e['track_id']); interacted.add(tid)
#         idx=track_to_index.get(tid); w=EVENT_WEIGHTS.get(e['event_type'],0.0)
#         if idx is not None and w != 0: usable.append((idx,w))
#     if not usable: return catalog_sample(n)
#     profile=np.zeros(X.shape[1]); mass=0.0
#     for idx,w in usable:
#         profile += w*X[idx]; mass += abs(w)
#     profile /= max(mass,1e-9)
#     sims=cosine_similarity(profile.reshape(1,-1),X)[0]
#     candidates=[i for i,tid in enumerate(df['track_id']) if tid not in interacted]
#     candidates.sort(key=lambda i:sims[i], reverse=True)
#     top=candidates[:n]
#     return _serialize(top,sims[top])

# OUTPUT_COLUMNS = [
#     "track_id",
#     "track_name",
#     "artists",
#     "track_genre",
#     "popularity",
#     "mood",
#     "is_explicit",
# ]

# def catalog_sample(n=20):

#     sample = df.sample(
#         n=min(
#             n,
#             len(df)
#         )
#     )

#     return (
#         sample[OUTPUT_COLUMNS]
#         .to_dict(
#             orient="records"
#         )
#     )
    

# def search_catalog(
#     query,
#     n=20
# ):

#     q = query.strip().lower()


#     mask = (
#         df["track_name"]
#             .fillna("")
#             .str.lower()
#             .str.contains(
#                 q,
#                 regex=False
#             )

#         |

#         df["artists"]
#             .fillna("")
#             .str.lower()
#             .str.contains(
#                 q,
#                 regex=False
#             )
#     )


#     result = (
#         df.loc[
#             mask,
#             OUTPUT_COLUMNS
#         ]
#         .head(n)
#     )


#     return result.to_dict(
#         orient="records"
#     )

# def profile_recommendations(
#     interactions,
#     n=12
# ):
    

