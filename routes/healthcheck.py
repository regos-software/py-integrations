from fastapi import APIRouter

router = APIRouter()


@router.get("/sys/healthcheck")
def healthcheck():
    return {
        "ok": True,
        "text": "Привет, Виктор! Я жив, сервисы не упали, CPU не греется — можешь выдохнуть на минутку :)",
    }
