"""
Módulo de carregamento e acesso ao dataset limpo.
"""
import pandas as pd

_df = None
_matrix = None

FEATURES_SCALED = [
    'danceability_scaled', 'energy_scaled', 'speechiness_scaled',
    'acousticness_scaled', 'instrumentalness_scaled',
    'liveness_scaled', 'valence_scaled', 'tempo_scaled'
]

def load_data(path='dataset_clean.csv'):
    """Carrega o dataset e pré-computa a matriz de features para o recomendador."""
    global _df, _matrix
    _df = pd.read_csv(path)
    _matrix = _df[FEATURES_SCALED].values
    print(f"✅ Dataset carregado: {len(_df):,} músicas | {_df['track_genre'].nunique()} gêneros")
    return _df

def get_df():
    """Retorna o DataFrame global. Lança erro se não foi carregado ainda."""
    if _df is None:
        raise RuntimeError("Dataset não carregado. Chame load_data() primeiro.")
    return _df

def get_matrix():
    """Retorna a matriz de features normalizada."""
    if _matrix is None:
        raise RuntimeError("Dataset não carregado. Chame load_data() primeiro.")
    return _matrix
