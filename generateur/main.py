"""
Point d'entrée de l'application Générateur de Classes.

Lance le serveur FastAPI avec l'interface web.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .api.routes import chemins_router, etats_router, ia_router, images_router
from .api.routes.actions import router as actions_router
from .config import DEBUG, HOST, PORT, STATIC_DIR, TEMPLATES_DIR, is_claude_available

# Créer l'application FastAPI
app = FastAPI(
    title="Générateur de Classes",
    description="Interface web pour générer les classes Etat, Chemin et Action",
    version="1.0.0",
    debug=DEBUG,
)

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Configurer les templates Jinja2
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Enregistrer les routes API
app.include_router(etats_router, prefix="/api")
app.include_router(chemins_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(ia_router, prefix="/api")
app.include_router(actions_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Page d'accueil."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Générateur de Classes",
            "claude_available": is_claude_available(),
        },
    )


@app.get("/etat", response_class=HTMLResponse)
async def etat_page(request: Request):
    """Page de création d'état."""
    return templates.TemplateResponse(
        "views/etat.html",
        {
            "request": request,
            "title": "Créer un État",
            "claude_available": is_claude_available(),
        },
    )


@app.get("/chemin", response_class=HTMLResponse)
async def chemin_page(request: Request):
    """Page de création de chemin."""
    return templates.TemplateResponse(
        "views/chemin.html",
        {
            "request": request,
            "title": "Créer un Chemin",
            "claude_available": is_claude_available(),
        },
    )


@app.get("/action-longue", response_class=HTMLResponse)
async def action_longue_page(request: Request):
    """Page de création d'ActionLongue avec Blockly."""
    return templates.TemplateResponse(
        "views/action-longue.html",
        {
            "request": request,
            "title": "Créer une ActionLongue",
            "claude_available": is_claude_available(),
        },
    )


@app.get("/health")
async def health_check():
    """Vérification de santé du serveur."""
    return {
        "status": "ok",
        "claude_available": is_claude_available(),
    }


def run():
    """Lance le serveur de développement."""
    import uvicorn

    print(f"\n{'='*60}")
    print("  Générateur de Classes - Mafia City Automation")
    print(f"{'='*60}")
    print(f"\n  → Interface web: http://{HOST}:{PORT}")
    print(f"  → API docs:      http://{HOST}:{PORT}/docs")
    print(f"  → Claude API:    {'✓ Configurée' if is_claude_available() else '✗ Non configurée'}")
    print(f"\n{'='*60}\n")

    uvicorn.run(
        "generateur.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
    )


if __name__ == "__main__":
    run()
