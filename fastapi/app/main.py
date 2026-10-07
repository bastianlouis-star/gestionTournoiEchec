import sys
from pathlib import Path

if __name__ == '__main__' and not __package__:
    # permet `python app/main.py` (ou le bouton "Run" de l'IDE) en plus de `python -m app.main`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, staticfiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import app.controllers as controllers
from app.models import user, tournament  # noqa: F401  (enregistre les modèles sur Base.metadata)
from app.models.base import Base, engine
from app.utils.application_utils import load_routers

app = FastAPI(title="Gestion de tournoi d'echec")

# autorise le front React (Vite) à appeler l'API en dev, quel que soit le port choisi
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r'http://(localhost|127\.0\.0\.1):\d+',
    allow_methods=['*'],
    allow_headers=['*'],
)

# créer les tables manquantes (users, ...) au démarrage
Base.metadata.create_all(bind=engine)

# charger tous les router se trouvant dans controllers
load_routers(app, controllers)

if __name__ == '__main__':
    # exposer FastAPI sur le port 8000
    uvicorn.run(
        'app.main:app',
        host='127.0.0.1',
        port=8000,
        reload=True
    )