"""
PROJETO SPOTIFY — Ponto de entrada principal
Residência em IA — UnB

Execute: python main.py
"""

from spotify.dados import load_data
from spotify.top5 import get_top5
from spotify.recomendador import search_track, recommend_similar, get_user_profile_recommendations
from spotify.playlist import build_playlist
from spotify.podcasts import get_podcasts

def main():
    # ── Carregar dataset ──
    load_data('dataset_clean.csv')
    sep = "=" * 55

    # ── MÓDULO 1: TOP 5 ──
    print(f"\n{sep}")
    print("  🏆 TOP 5 MÚSICAS MAIS POPULARES")
    print(sep)
    top5 = get_top5()
    for i, row in top5.iterrows():
        exp = '🔞' if row['is_explicit'] else '  '
        print(f"  {i}. {exp} [{row['popularity']}] {row['track_name'][:35]:<35} | {row['artists'][:25]:<25} | {row['mood']}")

    print(f"\n  🏆 TOP 5 SERTANEJO:")
    for i, row in get_top5(genre='sertanejo').iterrows():
        print(f"  {i}. [{row['popularity']}] {row['track_name'][:40]:<40} | {row['artists'][:25]}")

    # ── MÓDULO 2: RECOMENDADOR ──
    print(f"\n{sep}")
    print("  🎵 RECOMENDADOR POR SIMILARIDADE")
    print(sep)
    results = search_track("Sam Smith")
    ref_idx = results.iloc[0]['index']
    ref_name = results.iloc[0]['track_name']
    print(f"\n  🎯 Referência: '{ref_name}'")
    recs = recommend_similar(ref_idx, n=5)
    for i, row in recs.iterrows():
        exp = '🔞' if row['is_explicit'] else '  '
        print(f"  {i}. {exp} sim={row['similarity']:.3f} | [{row['popularity']:3d}] {row['track_name'][:35]:<35} | {row['artists'][:20]}")

    # ── MÓDULO 3: PLAYLIST ──
    print(f"\n{sep}")
    print("  🎼 PLAYLIST POR GÊNERO E MOOD")
    print(sep)
    pl = build_playlist(genre='samba', mood='Animado 🟡', n=8)
    print("\n  Playlist SAMBA | Animado 🟡:")
    for i, row in pl.iterrows():
        print(f"  {i+1:2d}. [{row['popularity']:3d}] {row['track_name'][:35]:<35} | energy={row['energy']:.2f}")

    # ── MÓDULO 4: PODCASTS ──
    print(f"\n{sep}")
    print("  🎙️  PODCASTS / FAIXAS LONGAS")
    print(sep)
    pods = get_podcasts(n=5)
    for i, row in pods.iterrows():
        print(f"  {i+1}. {row['duration_min']:6.1f}min | {row['track_name'][:35]:<35} | {row['artists'][:20]}")

    # ── MÓDULO 5: PERFIL DO USUÁRIO ──
    print(f"\n{sep}")
    print("  👤 PERFIL DO USUÁRIO — Sua Biblioteca")
    print(sep)
    from spotify.dados import get_df
    fav_indices = list(get_df().nlargest(3, 'popularity').index)
    fav_names = get_df().loc[fav_indices, 'track_name'].tolist()
    print(f"\n  Favoritas: {fav_names}")
    profile_recs = get_user_profile_recommendations(fav_indices, n=5)
    for i, row in profile_recs.iterrows():
        exp = '🔞' if row['is_explicit'] else '  '
        print(f"  {i}. {exp} sim={row['similarity']:.3f} | [{row['popularity']:3d}] {row['track_name'][:35]:<35} | {row['mood']}")

    print(f"\n{sep}")
    print("  ✅ TODOS OS MÓDULOS EXECUTADOS COM SUCESSO")
    print(sep)


if __name__ == '__main__':
    main()
