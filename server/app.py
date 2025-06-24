from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from datetime import datetime
import os
import asyncio
import subprocess
import logging

# === Константы ===
DOWNLOAD_FOLDER = "downloads"
LOG_FOLDER = "logs"
CLIENT_LOG_FOLDER = "clients"
TITLE_FILE = "title.txt"

# === Создание папок ===
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(CLIENT_LOG_FOLDER, exist_ok=True)

# === Логирование ===
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)
log_file = os.path.join(LOG_FOLDER, f"app_{datetime.now().strftime('%Y%m%d')}.log")
handler = logging.FileHandler(log_file, encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())

# === FastAPI и шаблоны ===
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# === Прогресс загрузки ===
progress_data = {}

# === Генерация имени файла ===
def generate_base_filename():
    try:
        with open(TITLE_FILE, "r", encoding="utf-8") as f:
            base_title = f.read().strip().replace(" ", "_")
    except:
        base_title = "video"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_title}_{timestamp}"

# === Очистка файла после скачивания ===
def cleanup(path: str):
    try:
        os.remove(path)
        logger.info(f"🧹 Удалён файл: {path}")
    except Exception as e:
        logger.warning(f"❌ Ошибка удаления: {e}")

# === SSE прогресс ===
@app.get("/progress/{uid}")
async def progress_stream(uid: str):
    async def event_stream():
        while True:
            await asyncio.sleep(0.5)
            line = progress_data.get(uid)
            if line:
                yield f"data: {line}\n\n"
                if "||" in line and line.split("||")[1].strip() == "100":
                    break
    return StreamingResponse(event_stream(), media_type="text/event-stream")

# === Главная ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# === Загрузка ===
@app.post("/", response_class=HTMLResponse)
async def download(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    format: str = Form(...),
    uuid_: str = Form(...)
):
    progress_data[uuid_] = "0"
    client_ip = request.client.host
    today = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(CLIENT_LOG_FOLDER, f"clients_{today}.log")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | IP: {client_ip} | URL: {url} | Format: {format} | UID: {uuid_}\n")

    # Получаем заголовок
    try:
        result = subprocess.run(["yt-dlp", "--print", "%(title)s", url], capture_output=True, text=True, check=True)
        video_title = result.stdout.strip() or "Видео"
    except Exception as e:
        video_title = "Видео"
        logger.warning(f"⚠️ Не удалось получить название: {e}")

    # Сохраняем в title.txt
    try:
        with open(TITLE_FILE, "w", encoding="utf-8") as f:
            f.write(video_title)
    except Exception as e:
        logger.warning(f"⚠️ Ошибка записи в title.txt: {e}")

    base_filename = generate_base_filename()
    output_template = os.path.join(DOWNLOAD_FOLDER, f"{base_filename}.%(ext)s")

    if format == "mp3":
        cmd = [
            "yt-dlp", "-f", "bestaudio",
            "--extract-audio", "--audio-format", "mp3",
            "--progress-template", "%(progress._percent_str)s %(progress.eta)s",
            "--newline",
            "-o", output_template, url
        ]
        media_type = "audio/mpeg"
    else:
        cmd = [
            "yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "--progress-template", "%(progress._percent_str)s %(progress.eta)s",
            "--newline",
            "-o", output_template, url
        ]
        media_type = "video/mp4"

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        async for line in proc.stdout:
            decoded = line.decode().strip()
            if "%" in decoded:
                try:
                    percent, eta = decoded.split()
                    percent_clean = percent.replace("%", "")
                    progress_data[uuid_] = f"{video_title} || {percent_clean} || {eta}"
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка разбора строки прогресса: {e}")

        await proc.wait()

        for file in os.listdir(DOWNLOAD_FOLDER):
            if file.startswith(base_filename):
                path = os.path.join(DOWNLOAD_FOLDER, file)
                background_tasks.add_task(cleanup, path)
                return FileResponse(path, filename=file, media_type=media_type)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "message": "❌ Файл не найден после загрузки"
        })

    except Exception as e:
        logger.error(f"❌ Ошибка загрузки: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "message": f"⚠️ Ошибка: {e}"
        })
