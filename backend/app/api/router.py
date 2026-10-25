from fastapi import APIRouter

from app.api.routes import auth, health, learning, programme

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(auth.WORKSPACE_ROUTER, tags=["workspaces"])
api_router.include_router(learning.learner_router, tags=["learner modules"])
api_router.include_router(learning.supervisor_router, tags=["module publishing"])
api_router.include_router(programme.learner_programme_router, tags=["learner programme"])
api_router.include_router(programme.facilitator_router, tags=["facilitator programme"])
api_router.include_router(programme.supervisor_programme_router, tags=["programme reports"])
api_router.include_router(programme.administrator_router, tags=["programme administration"])
