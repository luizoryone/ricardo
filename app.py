from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from db import (
    init_db,
    create_user,
    get_user,
    touch_user,
    save_interaction,
    get_interactions,
)

from recommender import (
    catalog_sample,
    search_catalog,
    profile_recommendations,
)


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(
    title="SpotData Audience API",
    version="1.0"
)


# Inicializa o SQLite
init_db()



# Modelo para criação do usuário
class UserCreate(BaseModel):
    display_name: str | None = None
    

# Modelo da interação:
class InteractionCreate(BaseModel):
    user_id: str
    track_id: str
    event_type: str


# Endpoint da página
@app.get("/")
def home():

    return FileResponse(
        STATIC_DIR / "index.html"
    )

# Criando Usuário
@app.post("/api/users")
def new_user(payload: UserCreate):

    user_id = str(uuid4())

    create_user(
        user_id=user_id,
        display_name=payload.display_name
    )

    return {
        "user_id": user_id,
        "display_name": payload.display_name
    }

# recuperando usuário
@app.get("/api/users/{user_id}")
def user(user_id: str):

    item = get_user(user_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )

    touch_user(user_id)

    return item

#  catálogo real - ao invés de top 5 - músicas reais
@app.get("/api/catalog")
def catalog(
    n: int = Query(
        default=20,
        ge=1,
        le=50
    )
):

    return {
        "items": catalog_sample(n)
    }


# buscas reais no catálogo inteiro
@app.get("/api/search")
def search(
    q: str,
    n: int = 20
):

    if len(q.strip()) < 2:

        return {
            "items": []
        }

    return {
        "items":
            search_catalog(q, n)
    }


#  endpoint das escolhas 
VALID_EVENTS = {
    "play",
    "like",
    "save",
    "skip",
    "dislike"
}


@app.post("/api/interactions")
def interaction(
    payload: InteractionCreate
):

    if payload.event_type not in VALID_EVENTS:

        raise HTTPException(
            status_code=400,
            detail="Evento inválido"
        )

    user = get_user(
        payload.user_id
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )

    save_interaction(
        user_id=payload.user_id,
        track_id=payload.track_id,
        event_type=payload.event_type
    )

    return {
        "ok": True
    }

#  histórico

@app.get(
    "/api/users/{user_id}/interactions"
)
def history(user_id: str):

    items = get_interactions(
        user_id
    )

    return {
        "user_id": user_id,
        "count": len(items),
        "items": items
    }


#  recomentações do usuário
@app.get(
    "/api/recommendations/{user_id}"
)
def recommendations(
    user_id: str,
    n: int = 12
):

    history = get_interactions(
        user_id
    )

    items = profile_recommendations(
        history,
        n=n
    )

    return {
        "user_id": user_id,
        "interaction_count":
            len(history),
        "items":
            items
    }






# from pathlib import Path
# from fastapi import FastAPI, HTTPException
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# from db import init_db, save_interaction, get_interactions
# from recommender import EVENT_WEIGHTS, catalog_sample, profile_recommendations

# BASE_DIR=Path(__file__).resolve().parent
# app=FastAPI(title='MVP Audiência Musical',version='0.1.0')

# class InteractionIn(BaseModel):
#     session_id:str
#     track_id:str
#     event_type:str

# @app.on_event('startup')
# def startup(): init_db()

# @app.get('/')
# def home(): return FileResponse(BASE_DIR/'static'/'index.html')

# @app.get('/api/catalog')
# def catalog(n:int=12): return {'items':catalog_sample(min(max(n,1),50))}

# @app.post('/api/interactions')
# def interaction(p:InteractionIn):
#     if p.event_type not in EVENT_WEIGHTS:
#         raise HTTPException(400,'event_type inválido')
#     save_interaction(p.session_id,p.track_id,p.event_type)
#     return {'ok':True}

# @app.get('/api/recommendations/{session_id}')
# def recommendations(session_id:str,n:int=12):
#     history=get_interactions(session_id)
#     return {'session_id':session_id,'interaction_count':len(history),'items':profile_recommendations(history,min(max(n,1),30))}
