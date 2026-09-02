"""
Módulos 2 e 5 — Recomendador por similaridade e por perfil do usuário.
"""
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from .dados import get_df, get_matrix


def search_track(query):
    """
    Busca uma música pelo nome ou artista.

    Parâmetros:
        query (str): nome da música ou artista

    Retorna:
        DataFrame com até 8 resultados encontrados
    """
    df = get_df()
    query = query.lower().strip()
    mask = (
        df['track_name'].str.lower().str.contains(query, na=False) |
        df['artists'].str.lower().str.contains(query, na=False)
    )
    results = df[mask][['track_name', 'artists', 'popularity', 'mood', 'genre_main']].head(8)
    return results.reset_index()


def recommend_similar(track_index, n=10, exclude_explicit=False, same_mood=False):
    """
    Retorna as N músicas mais similares a uma música de referência.
    Usa cosine similarity nas features de áudio normalizadas.

    Parâmetros:
        track_index (int): índice da música no DataFrame
        n (int): número de recomendações
        exclude_explicit (bool): remove conteúdo explícito
        same_mood (bool): restringe ao mesmo quadrante emocional

    Retorna:
        DataFrame com as músicas recomendadas e score de similaridade
    """
    df = get_df()
    matrix = get_matrix()

    query_vec = matrix[track_index].reshape(1, -1)
    sims = cosine_similarity(query_vec, matrix)[0]

    df_sim = df.copy()
    df_sim['similarity'] = sims.round(4)
    df_sim = df_sim[df_sim.index != track_index]

    if exclude_explicit:
        df_sim = df_sim[~df_sim['is_explicit']]

    if same_mood:
        ref_mood = df.loc[track_index, 'mood']
        df_sim = df_sim[df_sim['mood'] == ref_mood]

    df_sim = df_sim.sort_values(['similarity', 'popularity'], ascending=[False, False])

    # Diversidade: 1 música por artista
    seen_artists = set()
    results = []
    for _, row in df_sim.iterrows():
        artist = row['artists'].split(';')[0].strip()
        if artist not in seen_artists:
            seen_artists.add(artist)
            results.append(row)
        if len(results) >= n:
            break

    result_df = pd.DataFrame(results)[[
        'track_name', 'artists', 'similarity', 'popularity',
        'mood', 'genre_main', 'duration_min', 'is_explicit'
    ]].reset_index(drop=True)
    result_df.index = result_df.index + 1
    return result_df


def get_user_profile_recommendations(favorite_tracks_indices, n=10, exclude_explicit=False):
    """
    Recomendações baseadas no perfil do usuário (média das músicas favoritas).
    Estilo 'Sua Biblioteca' do Spotify.

    Parâmetros:
        favorite_tracks_indices (list): lista de índices das músicas favoritas
        n (int): número de recomendações
        exclude_explicit (bool): remove conteúdo explícito

    Retorna:
        DataFrame com músicas compatíveis com o perfil do usuário
    """
    df = get_df()
    matrix = get_matrix()

    user_vector = matrix[favorite_tracks_indices].mean(axis=0).reshape(1, -1)
    sims = cosine_similarity(user_vector, matrix)[0]

    df_sim = df.copy()
    df_sim['similarity'] = sims.round(4)
    df_sim = df_sim[~df_sim.index.isin(favorite_tracks_indices)]

    if exclude_explicit:
        df_sim = df_sim[~df_sim['is_explicit']]

    df_sim = df_sim.sort_values(['similarity', 'popularity'], ascending=[False, False])

    seen_artists = set()
    results = []
    for _, row in df_sim.iterrows():
        artist = row['artists'].split(';')[0].strip()
        if artist not in seen_artists:
            seen_artists.add(artist)
            results.append(row)
        if len(results) >= n:
            break

    result_df = pd.DataFrame(results)[[
        'track_name', 'artists', 'similarity', 'popularity',
        'mood', 'genre_main', 'duration_min', 'is_explicit'
    ]].reset_index(drop=True)
    result_df.index = result_df.index + 1
    return result_df


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from spotify.dados import load_data
    load_data('dataset_clean.csv')

    print("\n🔍 Buscando 'Sam Smith':")
    results = search_track("Sam Smith")
    print(results[['track_name', 'artists', 'popularity', 'mood']].to_string())

    ref_idx = results.iloc[0]['index']
    print(f"\n🎯 Músicas similares a: '{results.iloc[0]['track_name']}'")
    recs = recommend_similar(ref_idx, n=5)
    for i, row in recs.iterrows():
        print(f"  {i}. sim={row['similarity']:.3f} | [{row['popularity']}] {row['track_name'][:35]}")
