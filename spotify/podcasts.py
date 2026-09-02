"""
Módulo 4 — Podcasts e faixas longas (> 20 minutos).
"""
from .dados import get_df


def get_podcasts(min_duration=20, genre=None, n=20):
    """
    Retorna faixas longas ou com alta presença de fala.

    Parâmetros:
        min_duration (int): duração mínima em minutos (padrão: 20)
        genre (str): filtrar por gênero específico
        n (int): número de resultados

    Retorna:
        DataFrame com os podcasts/faixas longas encontradas
    """
    df = get_df()
    df = df[df['is_podcast'] == True].copy()

    if genre:
        df = df[df['track_genre'].str.lower() == genre.lower()]

    df = df[df['duration_min'] >= min_duration]
    df = df.sort_values(['duration_min', 'popularity'], ascending=[False, False])

    return df[[
        'track_name', 'artists', 'duration_min',
        'speechiness', 'track_genre', 'popularity'
    ]].head(n).reset_index(drop=True)


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from spotify.dados import load_data
    load_data('dataset_clean.csv')

    print("\n🎙️  TOP 10 PODCASTS / FAIXAS LONGAS:")
    pods = get_podcasts(n=10)
    for i, row in pods.iterrows():
        print(f"  {i+1}. {row['duration_min']:6.1f}min | {row['track_name'][:35]:<35} | {row['artists'][:25]}")
