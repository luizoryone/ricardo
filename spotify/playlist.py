"""
Módulo 3 — Playlist por gênero e humor (mood).
"""
import pandas as pd
from .dados import get_df


def build_playlist(genre=None, mood=None, n=20, exclude_explicit=False):
    """
    Monta uma playlist filtrando por gênero e/ou humor.
    Aplica diversidade de artistas e ordena por energia crescente
    para criar uma transição suave do início ao fim.

    Parâmetros:
        genre (str): 'samba', 'sertanejo', 'pop' ou qualquer genre_main
        mood (str): 'Animado 🟡', 'Intenso 🔴', 'Triste 🔵', 'Relaxado 🟢'
        n (int): tamanho da playlist
        exclude_explicit (bool): remove conteúdo explícito

    Retorna:
        DataFrame com a playlist montada
    """
    df = get_df()
    df = df[df['popularity'] > 0].copy()

    if exclude_explicit:
        df = df[~df['is_explicit']]

    if genre:
        df = df[df['genre_main'] == genre.lower()]

    if mood:
        df = df[df['mood'] == mood]

    if len(df) == 0:
        print(f"⚠️  Nenhuma música encontrada para: gênero='{genre}' mood='{mood}'")
        return pd.DataFrame()

    df = df.sort_values('popularity', ascending=False)

    # Máximo 2 músicas por artista
    artist_count = {}
    selected = []
    for _, row in df.iterrows():
        artist = row['artists'].split(';')[0].strip()
        count = artist_count.get(artist, 0)
        if count < 2:
            artist_count[artist] = count + 1
            selected.append(row)
        if len(selected) >= n:
            break

    result = pd.DataFrame(selected)
    result = result.sort_values('energy', ascending=True)

    return result[[
        'track_name', 'artists', 'popularity', 'mood',
        'energy', 'danceability', 'duration_min',
        'is_explicit', 'genre_main'
    ]].reset_index(drop=True)


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from spotify.dados import load_data
    load_data('dataset_clean.csv')

    print("\n🎼 Playlist SAMBA — Animado 🟡:")
    pl = build_playlist(genre='samba', mood='Animado 🟡', n=8)
    for i, row in pl.iterrows():
        print(f"  {i+1}. [{row['popularity']}] {row['track_name'][:35]:<35} | energy={row['energy']:.2f}")

    print("\n🎼 Playlist POP (sem filtro de mood):")
    pl2 = build_playlist(genre='pop', n=8)
    for i, row in pl2.iterrows():
        print(f"  {i+1}. [{row['popularity']}] {row['track_name'][:35]:<35} | {row['mood']}")
