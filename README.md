# MVP Audiência Musical — V1

Objetivo: provar o ciclo **usuário → interação → persistência → perfil → nova recomendação**.

## VS Code / PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copie `dataset_clean.csv` do projeto-base para esta pasta, ou indique o caminho:

```powershell
$env:SPOTIFY_DATASET="C:\caminho\dataset_clean.csv"
```

Execute:

```powershell
uvicorn app:app --reload
```

Abra `http://127.0.0.1:8000`.

## O que acontece

1. O navegador cria um `session_id` anônimo.
2. Gostei/Salvar/Pular/Não gostei vira um evento.
3. O FastAPI grava o evento no SQLite `audiencia.db`.
4. O recomendador recupera o histórico.
5. Cada evento recebe um peso: like +3, save +4, skip -2, dislike -4.
6. As 8 features musicais normalizadas formam um vetor de perfil.
7. Similaridade de cosseno compara o perfil ao catálogo.
8. A lista “Para você” muda após cada nova interação.

Esses pesos são hipóteses de MVP, não verdades universais; versões futuras devem validá-los com métricas e experimentos.
