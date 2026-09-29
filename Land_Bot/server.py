from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_FOLDER = os.path.join(BASE_DIR, "reports")
MAP_FILE = os.path.join(BASE_DIR, "map.html")

os.makedirs(REPORTS_FOLDER, exist_ok=True)

app = FastAPI(
    title="Цифровой мониторинг земель"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==========================================
# ВСЕ ОБРАЩЕНИЯ
# ==========================================

@app.get("/api/reports")
def get_reports():

    reports = []

    if not os.path.exists(REPORTS_FOLDER):
        return []

    for folder_name in os.listdir(REPORTS_FOLDER):

        folder_path = os.path.join(
            REPORTS_FOLDER,
            folder_name
        )

        if not os.path.isdir(folder_path):
            continue

        report_file = os.path.join(
            folder_path,
            "report.json"
        )

        if not os.path.exists(report_file):
            continue

        try:

            with open(
                report_file,
                "r",
                encoding="utf-8"
            ) as file:

                report = json.load(file)

            # Проверяем координаты
            latitude = report.get("latitude")
            longitude = report.get("longitude")

            if latitude is None or longitude is None:
                continue

            # Приводим координаты к числу
            report["latitude"] = float(latitude)
            report["longitude"] = float(longitude)

            # Ссылка на фотографию
            photo_name = report.get(
                "photo",
                "photo.jpg"
            )

            report["photo_url"] = (
                "/reports/"
                + folder_name
                + "/"
                + photo_name
            )

            reports.append(report)

        except Exception as error:

            print(
                "Ошибка:",
                report_file,
                error
            )

    reports.sort(
        key=lambda x: x.get(
            "created_at",
            ""
        ),
        reverse=True
    )

    return reports


# ==========================================
# ОДНО ОБРАЩЕНИЕ
# ==========================================

@app.get("/api/reports/{track_number}")
def get_report(track_number: str):

    report_file = os.path.join(
        REPORTS_FOLDER,
        track_number,
        "report.json"
    )

    if not os.path.exists(report_file):
        return {
            "error": "Обращение не найдено"
        }

    with open(
        report_file,
        "r",
        encoding="utf-8"
    ) as file:

        report = json.load(file)

    report["photo_url"] = (
        "/reports/"
        + track_number
        + "/"
        + report.get(
            "photo",
            "photo.jpg"
        )
    )

    return report


# ==========================================
# ФОТОГРАФИИ
# ==========================================

app.mount(
    "/reports",
    StaticFiles(
        directory=REPORTS_FOLDER
    ),
    name="reports"
)


# ==========================================
# КАРТА
# ==========================================

@app.get("/")
def home():

    if os.path.exists(MAP_FILE):
        return FileResponse(MAP_FILE)

    return {
        "error": "map.html не найден"
    }


# ==========================================
# ПРОВЕРКА СЕРВЕРА
# ==========================================

@app.get("/api/health")
def health():

    return {
        "status": "online",
        "reports": len(get_reports())
    }


# ==========================================
# ЗАПУСК
# ==========================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
