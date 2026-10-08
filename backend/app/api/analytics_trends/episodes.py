"""Topic map endpoints: episodes of the bubble with their lineage
(computed by app.services.topic_episodes, weekly or on demand)."""
from fastapi import APIRouter, HTTPException

from app.services import topic_episodes

router = APIRouter()


@router.get("/episodes")
def get_episodes():
    """Latest topic map: families, episodes (without example texts), lineage links."""
    topic_map = topic_episodes.latest_map()
    return {'available': topic_map is not None, 'map': topic_map, 'rebuild': topic_episodes.rebuild_status()}


@router.post("/episodes/rebuild", status_code=202)
def rebuild_episodes():
    """Recompute the topic map in the background (~10 s, a few minutes when many episodes need names)."""
    if not topic_episodes.start_rebuild_in_background():
        raise HTTPException(status_code=409, detail='A rebuild is already running')
    return {'started': True}


@router.get("/episodes/rebuild/status")
def rebuild_episodes_status():
    return topic_episodes.rebuild_status()


@router.get("/episodes/{episode_id}")
def get_episode(episode_id: int):
    """One episode of the latest map with example texts and first movers."""
    return topic_episodes.episode_detail(episode_id)
