"""
Módulo 1 — TOP 5 músicas mais populares.
"""
from .dados import get_df

def get_top5(exclude_explicit=False, genre=None):
    """
    Retorna as 5 músicas mais populares.

    Parâmetros:
        exclude_explicit (bool): remove músicas com linguagem explícita
        genre (str): filtra por gênero — ex: 'pop', 'samba', 'sertanejo'

    Retorna:
        DataFrame com as 5 músicas mais populares
    """
    df = get_df().copy()
    df = df[df['popularity'] > 0]

    if exclude_explicit:
        df = df[~df['is_explicit']]

    if genre:
        df = df[df['genre_main'] == genre.lower()]

    top = df.nlargest(5, 'popularity')[[
        'track_name', 'artists', 'popularity', 'mood',
        'genre_main', 'duration_min', 'is_explicit', 'track_genre'
    ]].reset_index(drop=True)

    top.index = top.index + 1
    return top


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from spotify.dados import load_data
    load_data('dataset_clean.csv')

    print("\n🏆 TOP 5 GERAL:")
    top = get_top5()
    for i, row in top.iterrows():
        exp = '🔞' if row['is_explicit'] else '  '
        print(f"  {i}. {exp} [{row['popularity']}] {row['track_name'][:35]:<35} | {row['artists'][:25]}")

    print("\n🏆 TOP 5 SERTANEJO:")
    top_s = get_top5(genre='sertanejo')
    for i, row in top_s.iterrows():
        print(f"  {i}. [{row['popularity']}] {row['track_name'][:35]:<35} | {row['artists'][:25]}")
