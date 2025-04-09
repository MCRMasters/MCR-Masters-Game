import uvicorn


def start_dev_server() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)


def start_prod_server() -> None:
    """프로덕션 서버를 시작합니다."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001)
