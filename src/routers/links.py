from fastapi import Depends, HTTPException, APIRouter
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.models import User, Link
import src.schemas as schemas
from src.redis_client import redis_client
from src.config import BASE_URL
from src.utils import create_and_add_link, get_db, get_current_user, check_user_authorization

router = APIRouter(tags=["links"])


@router.post("/links/shorten")
def shorten(
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
    user: User | None = Depends(check_user_authorization)
):
    _expires_at = link.expires_at
    _user_id = user.id if user else None

    if user is None:
        max_date_expire = datetime.now() + timedelta(hours=6)
        if _expires_at is None or _expires_at > max_date_expire:
            _expires_at = max_date_expire

    db_link = create_and_add_link(
        db,
        link.original_url,
        _expires_at,
        _user_id
    )

    return {
        "short_code": db_link.short_code,
        "short_url": f"{BASE_URL}/{db_link.short_code}"
    }


@router.get("/{short_code}")
def redirect(short_code: str, db: Session = Depends(get_db)):

    cached = redis_client.get(f"link:{short_code}")

    if cached:
        link = db.query(Link).filter(Link.short_code == short_code).first()

        if link.expires_at and link.expires_at < datetime.now():
            raise HTTPException(410, "Link expired")
        
        if link:
            link.click_count += 1
            link.last_used_at = datetime.now()
            db.commit()

        return RedirectResponse(cached, status_code=307)

    link = db.query(Link).filter(Link.short_code == short_code).first()

    if not link:
        raise HTTPException(404)

    if link.expires_at and link.expires_at < datetime.now():
        raise HTTPException(410, "Link expired")

    redis_client.setex(
        f"link:{short_code}",
        3600,
        link.original_url
    )

    link.click_count += 1
    link.last_used_at = datetime.now()
    db.commit()

    return RedirectResponse(link.original_url, status_code=307)


@router.get("/links/{short_code}/stats")
def stats(short_code: str, db: Session = Depends(get_db)):

    link = db.query(Link).filter(Link.short_code == short_code).first()

    if not link:
        raise HTTPException(404, "No such link")

    return {
        "original_url": link.original_url,
        "created_at": link.created_at,
        "click_count": link.click_count,
        "last_used_at": link.last_used_at
    }


@router.get("/links/search")
def search(original_url: str, db: Session = Depends(get_db)):

    links = db.query(Link).filter(
        Link.original_url == original_url
    ).all()

    return links


@router.put("/links/{short_code}")
def update(
    short_code: str,
    data: schemas.LinkUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    link = db.query(Link).filter(Link.short_code == short_code).first()

    if not link:
        raise HTTPException(404, "No such link")

    if link.user_id != user.id:
        raise HTTPException(403, "Not your link")

    link.original_url = data.new_url

    redis_client.delete(f"link:{short_code}")
    db.commit()

    return {"status": "updated"}


@router.delete("/links/{short_code}")
def delete(
    short_code: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    link = db.query(Link).filter(Link.short_code == short_code).first()

    if not link:
        raise HTTPException(404, "No such link")

    if link.user_id != user.id:
        raise HTTPException(403, "Not your link")

    db.delete(link)
    redis_client.delete(f"link:{short_code}")
    db.commit()

    return {"status": "deleted"}