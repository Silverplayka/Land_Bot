import asyncio
import json
import os
import shutil
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)


# =========================================================
# НАСТРОЙКИ
# =========================================================

BOT_TOKEN = "8905746280:AAE4V2SGguR2HgxCqy3usretY3ZTVBvayfA"

# Вставь сюда свой Telegram ID
ADMIN_ID = 8526566408

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REPORTS_FOLDER = os.path.join(
    BASE_DIR,
    "reports"
)

os.makedirs(
    REPORTS_FOLDER,
    exist_ok=True
)

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# =========================================================
# СОСТОЯНИЯ
# =========================================================

class StatusState(StatesGroup):
    waiting_for_track = State()


class ReportState(StatesGroup):
    waiting_for_location = State()
    waiting_for_photo = State()
    waiting_for_description = State()


class SearchState(StatesGroup):
    waiting_for_track = State()


# =========================================================
# КАТЕГОРИИ
# =========================================================

PROBLEM_TYPES = {
    "construction": "🏗 Стройка",
    "land_capture": "🚧 Захват земли",
    "unused_land": "🌱 Неиспользование",
    "dump": "🗑 Свалка",
    "boundaries": "📐 Границы",
    "other": "📌 Другое"
}


# =========================================================
# СТАТУСЫ
# =========================================================

STATUS_INFO = {

    "🟡 На рассмотрении":
        "Обращение зарегистрировано и ожидает проверки специалистом.",

    "🔵 Назначен выезд инспектора":
        "По обращению назначена проверка на месте.",

    "🟢 Одобрено":
        "Обращение рассмотрено. По результатам проверки принято положительное решение.",

    "🔴 Отказ":
        "Обращение рассмотрено. По результатам проверки принято решение об отказе."
}


# =========================================================
# КЛАВИАТУРА ПОЛЬЗОВАТЕЛЯ
# =========================================================

def main_kb():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="🔍 Проверить статус заявления"
                )
            ],

            [
                KeyboardButton(
                    text="📚 База знаний и регламенты"
                )
            ],

            [
                KeyboardButton(
                    text="⚠️ Сообщить о нарушении"
                )
            ]

        ],

        resize_keyboard=True
    )


# =========================================================
# КЛАВИАТУРА АДМИНА
# =========================================================

def admin_kb():

    return ReplyKeyboardMarkup(

        keyboard=[

            [
                KeyboardButton(
                    text="🟡 Нерассмотренные заявки"
                )
            ],

            [
                KeyboardButton(
                    text="📋 Все обращения"
                ),

                KeyboardButton(
                    text="🔎 Найти обращение"
                )
            ],

            [
                KeyboardButton(
                    text="📊 Статистика"
                )
            ],

            [
                KeyboardButton(
                    text="🏠 Главное меню"
                )
            ]

        ],

        resize_keyboard=True
    )


# =========================================================
# ПРОВЕРКА АДМИНА
# =========================================================

def is_admin(user):

    return (
        ADMIN_ID != 0
        and user.from_user.id == ADMIN_ID
    )


# =========================================================
# СОЗДАНИЕ НОМЕРА ЗАЯВКИ
# =========================================================

def create_track_number():

    now = datetime.now()

    base = now.strftime(
        "KZ-%Y%m%d-%H%M%S"
    )

    track = base

    counter = 1

    while os.path.exists(
        os.path.join(
            REPORTS_FOLDER,
            track
        )
    ):

        track = f"{base}-{counter}"

        counter += 1

    return track


# =========================================================
# ПОЛУЧЕНИЕ ЗАЯВКИ
# =========================================================

def get_report_by_track(track):

    report_file = os.path.join(

        REPORTS_FOLDER,

        track,

        "report.json"

    )

    if not os.path.exists(
        report_file
    ):

        return None

    try:

        with open(
            report_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            "Ошибка чтения заявки:",
            error
        )

        return None


# =========================================================
# ВСЕ ЗАЯВКИ
# =========================================================

def get_all_reports():

    result = []

    if not os.path.exists(
        REPORTS_FOLDER
    ):

        return result

    for folder_name in os.listdir(
        REPORTS_FOLDER
    ):

        folder_path = os.path.join(

            REPORTS_FOLDER,

            folder_name

        )

        if not os.path.isdir(
            folder_path
        ):

            continue

        report_file = os.path.join(

            folder_path,

            "report.json"

        )

        if not os.path.exists(
            report_file
        ):

            continue

        try:

            with open(
                report_file,
                "r",
                encoding="utf-8"
            ) as file:

                report = json.load(file)

            result.append(
                report
            )

        except Exception as error:

            print(
                "Ошибка:",
                error
            )

    result.sort(

        key=lambda x: x.get(
            "created_at",
            ""
        ),

        reverse=True

    )

    return result


# =========================================================
# НЕРАССМОТРЕННЫЕ
# =========================================================

def get_unreviewed_reports():

    reports = get_all_reports()

    return [

        report

        for report in reports

        if report.get(
            "status"
        ) == "🟡 На рассмотрении"

    ]


# =========================================================
# START
# =========================================================

@dp.message(
    Command("start")
)
async def start_command(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(

        "🌍 <b>Цифровой мониторинг земель</b>\n\n"

        "Добро пожаловать!\n\n"

        "Здесь вы можете:\n"

        "🔍 проверить статус заявления;\n"

        "📚 узнать порядок получения земельных услуг;\n"

        "⚠️ сообщить о нарушении с геолокацией и фотографией.\n\n"

        "Выберите нужный раздел:",

        reply_markup=main_kb(),

        parse_mode="HTML"
    )


# =========================================================
# ПОЛУЧИТЬ СВОЙ TELEGRAM ID
# =========================================================

@dp.message(
    Command("id")
)
async def my_id(
    message: Message
):

    await message.answer(

        "🆔 Ваш Telegram ID:\n\n"

        f"<code>{message.from_user.id}</code>",

        parse_mode="HTML"
    )


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

@dp.message(
    F.text == "🏠 Главное меню"
)
async def main_menu(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(

        "🏠 Главное меню",

        reply_markup=main_kb()
    )


# =========================================================
# ПРОВЕРКА СТАТУСА
# =========================================================

@dp.message(
    F.text == "🔍 Проверить статус заявления"
)
async def check_status_start(
    message: Message,
    state: FSMContext
):

    await state.set_state(

        StatusState.waiting_for_track

    )

    await message.answer(

        "🔍 Введите трек-номер обращения.\n\n"

        "Например:\n"

        "<code>KZ-20260929-101530</code>",

        parse_mode="HTML"
    )


@dp.message(
    StatusState.waiting_for_track
)
async def check_status_finish(
    message: Message,
    state: FSMContext
):

    track = message.text.strip()

    report = get_report_by_track(
        track
    )

    if report is None:

        await message.answer(

            "❌ Обращение с таким номером не найдено.\n\n"

            "Проверьте номер и попробуйте снова."

        )

        return

    status = report.get(

        "status",

        "🟡 На рассмотрении"

    )

    category = report.get(

        "problem_type",

        "📌 Другое"

    )

    description = report.get(

        "description",

        "-"

    )

    created_at = report.get(

        "created_at",

        "-"

    )

    explanation = STATUS_INFO.get(

        status,

        "Информация о статусе отсутствует."

    )

    text = (

        "🔍 <b>Статус обращения</b>\n\n"

        f"📌 <b>Номер:</b>\n"
        f"{track}\n\n"

        f"🏷 <b>Категория:</b>\n"
        f"{category}\n\n"

        f"📊 <b>Статус:</b>\n"
        f"{status}\n\n"

        f"💬 <b>Что означает:</b>\n"
        f"{explanation}\n\n"

        f"📝 <b>Описание:</b>\n"
        f"{description}\n\n"

        f"📅 <b>Создано:</b>\n"
        f"{created_at}"

    )

    history = report.get(
        "history",
        []
    )

    if history:

        text += (
            "\n\n📜 <b>История:</b>\n"
        )

        for item in history[-10:]:

            text += (

                f"\n• {item.get('status', '-')}\n"

                f"  {item.get('date', '-')}\n"

            )

    await message.answer(

        text,

        parse_mode="HTML"

    )

    await state.clear()


# =========================================================
# БАЗА ЗНАНИЙ
# =========================================================

@dp.message(
    F.text == "📚 База знаний и регламенты"
)
async def knowledge_base(
    message: Message
):

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="1️⃣ Изменение назначения земли",

                    callback_data="kb_1"

                )

            ],

            [

                InlineKeyboardButton(

                    text="2️⃣ Продление аренды",

                    callback_data="kb_2"

                )

            ],

            [

                InlineKeyboardButton(

                    text="3️⃣ Участок под ИЖС",

                    callback_data="kb_3"

                )

            ]

        ]

    )

    await message.answer(

        "📚 <b>База знаний и регламенты</b>\n\n"

        "Выберите интересующий раздел:",

        reply_markup=keyboard,

        parse_mode="HTML"

    )


@dp.callback_query(
    F.data == "kb_1"
)
async def knowledge_1(
    callback: CallbackQuery
):

    text = (

        "1️⃣ <b>Изменение целевого назначения земли</b>\n\n"

        "📄 Обычно могут потребоваться:\n"

        "• удостоверение личности;\n"
        "• документы на земельный участок;\n"
        "• заявление;\n"
        "• документы, подтверждающие основание изменения.\n\n"

        "📋 Порядок:\n"

        "1. Подготовить документы.\n"
        "2. Подать заявление.\n"
        "3. Дождаться рассмотрения.\n"
        "4. Получить решение.\n\n"

        "⏱ Срок зависит от конкретной процедуры.\n\n"

        "🌐 Государственные услуги:\n"
        "eGov.kz"

    )

    await callback.message.answer(

        text,

        parse_mode="HTML"

    )

    await callback.answer()


@dp.callback_query(
    F.data == "kb_2"
)
async def knowledge_2(
    callback: CallbackQuery
):

    text = (

        "2️⃣ <b>Продление договора аренды</b>\n\n"

        "📄 Обычно используются:\n"

        "• удостоверение личности;\n"
        "• действующий договор аренды;\n"
        "• документы на участок;\n"
        "• заявление.\n\n"

        "📋 Общий порядок:\n"

        "1. Проверить срок договора.\n"
        "2. Подготовить документы.\n"
        "3. Подать заявление.\n"
        "4. Дождаться решения.\n\n"

        "⏱ Срок зависит от конкретной услуги.\n\n"

        "🌐 Государственные услуги:\n"
        "eGov.kz"

    )

    await callback.message.answer(

        text,

        parse_mode="HTML"

    )

    await callback.answer()


@dp.callback_query(
    F.data == "kb_3"
)
async def knowledge_3(
    callback: CallbackQuery
):

    text = (

        "3️⃣ <b>Получение участка под ИЖС</b>\n\n"

        "📄 В зависимости от процедуры могут потребоваться:\n"

        "• удостоверение личности;\n"
        "• заявление;\n"
        "• сведения о земельном участке;\n"
        "• дополнительные документы согласно требованиям услуги.\n\n"

        "📋 Общий порядок:\n"

        "1. Проверить доступность участка.\n"
        "2. Подать заявление.\n"
        "3. Дождаться рассмотрения.\n"
        "4. Получить решение.\n\n"

        "⏱ Срок зависит от конкретной процедуры.\n\n"

        "🌐 Государственные услуги:\n"
        "eGov.kz"

    )

    await callback.message.answer(

        text,

        parse_mode="HTML"

    )

    await callback.answer()


# =========================================================
# НАРОДНЫЙ КОНТРОЛЬ
# =========================================================

@dp.message(
    F.text == "⚠️ Сообщить о нарушении"
)
async def report_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🏗 Стройка",
                    callback_data="type_construction"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🚧 Захват земли",
                    callback_data="type_land_capture"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🌱 Неиспользование",
                    callback_data="type_unused_land"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🗑 Свалка",
                    callback_data="type_dump"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📐 Границы",
                    callback_data="type_boundaries"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📌 Другое",
                    callback_data="type_other"
                )
            ]

        ]

    )

    await message.answer(

        "⚠️ <b>Народный контроль</b>\n\n"

        "Выберите тип нарушения:",

        reply_markup=keyboard,

        parse_mode="HTML"

    )


# =========================================================
# ВЫБОР КАТЕГОРИИ
# =========================================================

@dp.callback_query(
    F.data.startswith("type_")
)
async def report_type(
    callback: CallbackQuery,
    state: FSMContext
):

    code = callback.data.replace(
        "type_",
        ""
    )

    problem_type = PROBLEM_TYPES.get(

        code,

        "📌 Другое"

    )

    await state.update_data(

        problem_type=problem_type

    )

    await state.set_state(

        ReportState.waiting_for_location

    )

    location_keyboard = ReplyKeyboardMarkup(

        keyboard=[

            [

                KeyboardButton(

                    text="📍 Отправить геолокацию",

                    request_location=True

                )

            ]

        ],

        resize_keyboard=True,

        one_time_keyboard=True

    )

    await callback.message.answer(

        f"Вы выбрали: <b>{problem_type}</b>\n\n"

        "📍 Теперь отправьте геолокацию "
        "места нарушения.",

        reply_markup=location_keyboard,

        parse_mode="HTML"

    )

    await callback.answer()


# =========================================================
# ГЕОЛОКАЦИЯ
# =========================================================

@dp.message(
    ReportState.waiting_for_location,
    F.location
)
async def report_location(
    message: Message,
    state: FSMContext
):

    await state.update_data(

        latitude=message.location.latitude,

        longitude=message.location.longitude

    )

    await state.set_state(

        ReportState.waiting_for_photo

    )

    keyboard = ReplyKeyboardMarkup(

        keyboard=[

            [

                KeyboardButton(
                    text="🏠 Главное меню"
                )

            ]

        ],

        resize_keyboard=True

    )

    await message.answer(

        "📍 Геолокация получена.\n\n"

        "📷 Теперь отправьте фотографию нарушения.",

        reply_markup=keyboard

    )


@dp.message(
    ReportState.waiting_for_location
)
async def location_required(
    message: Message
):

    await message.answer(

        "📍 Пожалуйста, отправьте именно "
        "геолокацию через кнопку "
        "«Отправить геолокацию»."

    )


# =========================================================
# ФОТО
# =========================================================

@dp.message(
    ReportState.waiting_for_photo,
    F.photo
)
async def report_photo(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    track = create_track_number()

    report_folder = os.path.join(

        REPORTS_FOLDER,

        track

    )

    os.makedirs(

        report_folder,

        exist_ok=True

    )

    photo = message.photo[-1]

    photo_path = os.path.join(

        report_folder,

        "photo.jpg"

    )

    await bot.download(

        photo,

        destination=photo_path

    )

    await state.update_data(

        track_number=track,

        photo="photo.jpg"

    )

    await state.set_state(

        ReportState.waiting_for_description

    )

    await message.answer(

        "📷 Фотография получена.\n\n"

        "📝 Теперь напишите короткое "
        "описание нарушения."

    )


@dp.message(
    ReportState.waiting_for_photo
)
async def photo_required(
    message: Message
):

    await message.answer(

        "📷 Пожалуйста, отправьте фотографию нарушения."

    )


# =========================================================
# ОПИСАНИЕ
# =========================================================

@dp.message(
    ReportState.waiting_for_description,
    F.text
)
async def report_description(
    message: Message,
    state: FSMContext
):

    description = message.text.strip()

    if not description:

        await message.answer(
            "📝 Напишите описание нарушения."
        )

        return

    data = await state.get_data()

    track = data["track_number"]

    created_at = datetime.now().strftime(

        "%d.%m.%Y %H:%M:%S"

    )

    # Telegram ID пользователя
    user_id = message.from_user.id

    # Username
    username = message.from_user.username

    report = {

        "track_number": track,

        "user_id": user_id,

        "username": username,

        "problem_type": data.get(
            "problem_type",
            "📌 Другое"
        ),

        "status": "🟡 На рассмотрении",

        "status_code": "review",

        "description": description,

        "latitude": data.get(
            "latitude"
        ),

        "longitude": data.get(
            "longitude"
        ),

        "photo": data.get(
            "photo",
            "photo.jpg"
        ),

        "created_at": created_at,

        "history": [

            {
                "status":
                    "🟡 На рассмотрении",

                "date":
                    created_at

            }

        ]

    }

    report_folder = os.path.join(

        REPORTS_FOLDER,

        track

    )

    os.makedirs(

        report_folder,

        exist_ok=True

    )

    report_file = os.path.join(

        report_folder,

        "report.json"

    )

    with open(

        report_file,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            report,

            file,

            ensure_ascii=False,

            indent=4

        )

    await state.clear()

    await message.answer(

        "✅ <b>Обращение зарегистрировано!</b>\n\n"

        f"📌 <b>Номер:</b>\n"
        f"<code>{track}</code>\n\n"

        f"🏷 <b>Категория:</b>\n"
        f"{report['problem_type']}\n\n"

        "📊 <b>Статус:</b>\n"
        "🟡 На рассмотрении\n\n"

        "Сохраните номер обращения — "
        "по нему можно проверить статус.",

        reply_markup=main_kb(),

        parse_mode="HTML"

    )

    # =====================================================
    # УВЕДОМЛЕНИЕ АДМИНА
    # =====================================================

    if ADMIN_ID != 8526566408:

        try:

            await bot.send_message(

                ADMIN_ID,

                "🚨 <b>Новое обращение!</b>\n\n"

                f"📌 Номер: "
                f"<code>{track}</code>\n"

                f"🏷 Категория: "
                f"{report['problem_type']}\n"

                f"📊 Статус: "
                f"{report['status']}\n"

                f"📅 Дата: "
                f"{created_at}\n\n"

                f"👤 Telegram ID: "
                f"<code>{user_id}</code>\n"

                f"🔹 Username: "
                f"@{username if username else 'нет'}\n\n"

                f"📝 {description}",

                parse_mode="HTML"

            )

        except Exception as error:

            print(
                "Ошибка уведомления админа:",
                error
            )


# =========================================================
# АДМИН-ПАНЕЛЬ
# =========================================================

@dp.message(
    Command("admin")
)
async def admin_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    if not is_admin(message):

        await message.answer(

            "⛔ У вас нет доступа "
            "к админ-панели."

        )

        return

    await message.answer(

        "👨‍💼 <b>Админ-панель</b>\n\n"

        "Здесь можно:\n"

        "🟡 просматривать новые заявки;\n"
        "📋 смотреть все обращения;\n"
        "🔎 искать заявку;\n"
        "📊 смотреть статистику;\n"
        "📷 смотреть фотографии;\n"
        "📜 смотреть историю;\n"
        "🗑 удалять заявки.\n\n"

        "Выберите раздел:",

        reply_markup=admin_kb(),

        parse_mode="HTML"

    )


# =========================================================
# НЕРАССМОТРЕННЫЕ
# =========================================================

@dp.message(
    F.text == "🟡 Нерассмотренные заявки"
)
async def unreviewed_reports(
    message: Message
):

    if not is_admin(message):
        return

    reports = get_unreviewed_reports()

    if not reports:

        await message.answer(

            "✅ Нерассмотренных заявок сейчас нет.",

            reply_markup=admin_kb()

        )

        return

    text = (

        "🟡 <b>Нерассмотренные заявки</b>\n\n"

        f"Всего: <b>{len(reports)}</b>\n\n"

        "Выберите заявку:"

    )

    buttons = []

    for report in reports:

        track = report.get(

            "track_number",

            "Без номера"

        )

        category = report.get(

            "problem_type",

            "📌 Другое"

        )

        buttons.append([

            InlineKeyboardButton(

                text=f"📋 {track} — {category}",

                callback_data=f"open_report|{track}"

            )

        ])

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=buttons

    )

    await message.answer(

        text,

        reply_markup=keyboard,

        parse_mode="HTML"

    )


# =========================================================
# ОТКРЫТЬ ЗАЯВКУ
# =========================================================

@dp.callback_query(
    F.data.startswith("open_report|")
)
async def open_report(
    callback: CallbackQuery
):

    if not is_admin(callback):

        await callback.answer(

            "⛔ Нет доступа",

            show_alert=True

        )

        return

    track = callback.data.split(

        "|",

        1

    )[1]

    report = get_report_by_track(

        track

    )

    if report is None:

        await callback.answer(

            "❌ Заявка не найдена",

            show_alert=True

        )

        return

    category = report.get(

        "problem_type",

        "📌 Другое"

    )

    status = report.get(

        "status",

        "🟡 На рассмотрении"

    )

    description = report.get(

        "description",

        "-"

    )

    created = report.get(

        "created_at",

        "-"

    )

    latitude = report.get(

        "latitude",

        "-"

    )

    longitude = report.get(

        "longitude",

        "-"

    )

    user_id = report.get(

        "user_id",

        "-"

    )

    username = report.get(

        "username"

    )

    if username:

        username_text = f"@{username}"

    else:

        username_text = "нет"

    text = (

        f"📋 <b>Заявка {track}</b>\n\n"

        f"🏷 <b>Категория:</b>\n"
        f"{category}\n\n"

        f"📊 <b>Статус:</b>\n"
        f"{status}\n\n"

        f"👤 <b>Telegram ID:</b>\n"
        f"<code>{user_id}</code>\n\n"

        f"🔹 <b>Username:</b>\n"
        f"{username_text}\n\n"

        f"📝 <b>Описание:</b>\n"
        f"{description}\n\n"

        f"📅 <b>Дата:</b>\n"
        f"{created}\n\n"

        f"📍 <b>Координаты:</b>\n"
        f"{latitude}, {longitude}"

    )

    buttons = []

    # -------------------------
    # СТАТУСЫ
    # -------------------------

    if status == "🟡 На рассмотрении":

        buttons.append([

            InlineKeyboardButton(

                text="🔵 Назначить выезд",

                callback_data=f"status_visit|{track}"

            )

        ])

        buttons.append([

            InlineKeyboardButton(

                text="🟢 Решено / Одобрено",

                callback_data=f"status_approved|{track}"

            )

        ])

        buttons.append([

            InlineKeyboardButton(

                text="🔴 Отказать",

                callback_data=f"status_rejected|{track}"

            )

        ])

    elif status == "🔵 Назначен выезд инспектора":

        buttons.append([

            InlineKeyboardButton(

                text="🟢 Решено / Одобрено",

                callback_data=f"status_approved|{track}"

            )

        ])

        buttons.append([

            InlineKeyboardButton(

                text="🔴 Отказать",

                callback_data=f"status_rejected|{track}"

            )

        ])

    # -------------------------
    # ФОТО
    # -------------------------

    if report.get("photo"):

        buttons.append([

            InlineKeyboardButton(

                text="📷 Посмотреть фото",

                callback_data=f"photo_report|{track}"

            )

        ])

    # -------------------------
    # ИСТОРИЯ
    # -------------------------

    buttons.append([

        InlineKeyboardButton(

            text="📜 История",

            callback_data=f"history_report|{track}"

        )

    ])

    # -------------------------
    # УДАЛЕНИЕ
    # -------------------------

    buttons.append([

        InlineKeyboardButton(

            text="🗑 Удалить заявку",

            callback_data=f"delete_confirm|{track}"

        )

    ])

    # -------------------------
    # НАЗАД
    # -------------------------

    buttons.append([

        InlineKeyboardButton(

            text="⬅️ Назад",

            callback_data="back_unreviewed"

        )

    ])

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=buttons

    )

    await callback.message.edit_text(

        text,

        reply_markup=keyboard,

        parse_mode="HTML"

    )

    await callback.answer()


# =========================================================
# ФОТО ЗАЯВКИ
# =========================================================

@dp.callback_query(
    F.data.startswith("photo_report|")
)
async def photo_report(
    callback: CallbackQuery
):

    if not is_admin(callback):

        await callback.answer(

            "⛔ Нет доступа",

            show_alert=True

        )

        return

    track = callback.data.split(

        "|",

        1

    )[1]

    report = get_report_by_track(

        track

    )

    if report is None:

        await callback.answer(

            "❌ Заявка не найдена",

            show_alert=True

        )

        return

    photo_name = report.get(

        "photo"

    )

    if not photo_name:

        await callback.answer(

            "📷 Фото отсутствует",

            show_alert=True

        )

        return

    photo_path = os.path.join(

        REPORTS_FOLDER,

        track,

        photo_name

    )

    if not os.path.exists(

        photo_path

    ):

        await callback.answer(

            "📷 Файл фотографии не найден",

            show_alert=True

        )

        return

    await callback.message.answer_photo(

        FSInputFile(

            photo_path

        ),

        caption=(

            f"📷 Фото заявки {track}"

        )

    )

    await callback.answer()


# =========================================================
# ИСТОРИЯ
# =========================================================

@dp.callback_query(
    F.data.startswith("history_report|")
)
async def history_report(
    callback: CallbackQuery
):

    if not is_admin(callback):

        await callback.answer(

            "⛔ Нет доступа",

            show_alert=True

        )

        return

    track = callback.data.split(

        "|",

        1

    )[1]

    report = get_report_by_track(

        track

    )

    if report is None:

        await callback.answer(

            "❌ Заявка не найдена",

            show_alert=True

        )

        return

    history = report.get(

        "history",

        []

    )

    if not history:

        text = (

            f"📜 <b>История {track}</b>\n\n"

            "История пока отсутствует."

        )

    else:

        text = (

            f"📜 <b>История {track}</b>\n\n"

        )

        for item in history:

            text += (

                f"• {item.get('status', '-')}\n"

                f"  📅 {item.get('date', '-')}\n\n"

            )

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="⬅️ К заявке",

                    callback_data=f"open_report|{track}"

                )

            ]

        ]

    )

    await callback.message.edit_text(

        text,

        reply_markup=keyboard,

        parse_mode="HTML"

    )

    await callback.answer()


# =========================================================
# НАЗАД
# =========================================================

@dp.callback_query(
    F.data == "back_unreviewed"
)
async def back_unreviewed(
    callback: CallbackQuery
):

    if not is_admin(callback):

        await callback.answer(

            "⛔ Нет доступа",

            show_alert=True

        )

        return

    reports = get_unreviewed_reports()

    if not reports:

        await callback.message.edit_text(

            "✅ Нерассмотренных заявок больше нет."

        )

        await callback.answer()

        return

    text = (

        "🟡 <b>Нерассмотренные заявки</b>\n\n"

        f"Всего: <b>{len(reports)}</b>\n\n"

        "Выберите заявку:"

    )

    buttons = []

    for report in reports:

        track = report.get(

            "track_number",

            "Без номера"

        )

        category = report.get(

            "problem_type",

            "📌 Другое"

        )

        buttons.append([

            InlineKeyboardButton(

                text=f"📋 {track} — {category}",

                callback_data=f"open_report|{track}"

            )

        ])

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=buttons

    )

    await callback.message.edit_text(

        text,

        reply_markup=keyboard,

        parse_mode="HTML"

    )

    await callback.answer()


# =========================================================
# ВСЕ ОБРАЩЕНИЯ
# =========================================================

@dp.message(
    F.text == "📋 Все обращения"
)
async def all_reports(
    message: Message
):

    if not is_admin(message):
        return

    reports = get_all_reports()

    if not reports:

        await message.answer(

            "📭 Обращений пока нет.",

            reply_markup=admin_kb()

        )

        return

    text = (

        "📋 <b>Все обращения</b>\n\n"

        f"Всего: <b>{len(reports)}</b>\n\n"

        "Выберите заявку:"

    )

    buttons = []

    for report in reports[:30]:

        track = report.get(

            "track_number",

            "-"

        )

        status = report.get(

            "status",

            "-"

        )

        buttons.append([

            InlineKeyboardButton(

                text=f"📋 {track} — {status}",

                callback_data=f"open_report|{track}"

            )

        ])

    if len(reports) > 30:

        text += (

            f"\nПоказаны первые 30 "
            f"из {len(reports)}."

        )

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=buttons

    )

    await message.answer(

        text,

        reply_markup=keyboard

    )


# =========================================================
# ПОИСК
# =========================================================

@dp.message(
    F.text == "🔎 Найти обращение"
)
async def search_report_start(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):
        return

    await state.set_state(

        SearchState.waiting_for_track

    )

    await message.answer(

        "🔎 Введите номер обращения.\n\n"

        "Например:\n"

        "<code>KZ-20260929-101530</code>",

        parse_mode="HTML"

    )


@dp.message(
    SearchState.waiting_for_track
)
async def search_report_finish(
    message: Message,
    state: FSMContext
):

    if not is_admin(message):

        await state.clear()

        return

    track = message.text.strip()

    report = get_report_by_track(

        track

    )

    if report is None:

        await message.answer(

            "❌ Заявка не найдена.\n\n"

            "Проверьте номер."

        )

        return

    await state.clear()

    await send_admin_report(

        message,

        report

    )


# =========================================================
# ОТОБРАЖЕНИЕ НАЙДЕННОЙ ЗАЯВКИ
# =========================================================

async def send_admin_report(
    message,
    report
):

    track = report.get(
        "track_number",
        "-"
    )

    category = report.get(
        "problem_type",
        "📌 Другое"
    )

    status = report.get(
        "status",
        "🟡 На рассмотрении"
    )

    description = report.get(
        "description",
        "-"
    )

    created = report.get(
        "created_at",
        "-"
    )

    latitude = report.get(
        "latitude",
        "-"
    )

    longitude = report.get(
        "longitude",
        "-"
    )

    user_id = report.get(
        "user_id",
        "-"
    )

    username = report.get(
        "username"
    )

    username_text = (

        f"@{username}"

        if username

        else "нет"

    )

    text = (

        f"📋 <b>Заявка {track}</b>\n\n"

        f"🏷 <b>Категория:</b>\n"
        f"{category}\n\n"

        f"📊 <b>Статус:</b>\n"
        f"{status}\n\n"

        f"👤 <b>Telegram ID:</b>\n"
        f"<code>{user_id}</code>\n\n"

        f"🔹 <b>Username:</b>\n"
        f"{username_text}\n\n"

        f"📝 <b>Описание:</b>\n"
        f"{description}\n\n"

        f"📅 <b>Дата:</b>\n"
        f"{created}\n\n"

        f"📍 <b>Координаты:</b>\n"
        f"{latitude}, {longitude}"

    )

    buttons = []

    if status == "🟡 На рассмотрении":

        buttons.append([

            InlineKeyboardButton(

                text="🔵 Назначить выезд",

                callback_data=f"status_visit|{track}"

            )

        ])

        buttons.append([

            InlineKeyboardButton(

                text="🟢 Решено / Одобрено",

                callback_data=f"status_approved|{track}"

            )

        ])

        buttons.append([

            InlineKeyboardButton(

                text="🔴 Отказать",

                callback_data=f"status_rejected|{track}"

            )

        ])

    elif status == "🔵 Назначен выезд инспектора":

        buttons.append([

            InlineKeyboardButton(

                text="🟢 Решено / Одобрено",

                callback_data=f"status_approved|{track}"

            )

        ])

        buttons.append([

            InlineKeyboardButton(

                text="🔴 Отказать",

                callback_data=f"status_rejected|{track}"

            )

        ])

    if report.get("photo"):

        buttons.append([

            InlineKeyboardButton(

                text="📷 Посмотреть фото",

                callback_data=f"photo_report|{track}"

            )

        ])

    buttons.append([

        InlineKeyboardButton(

            text="📜 История",

            callback_data=f"history_report|{track}"

        )

    ])

    buttons.append([

        InlineKeyboardButton(

            text="🗑 Удалить заявку",

            callback_data=f"delete_confirm|{track}"

        )

    ])

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=buttons

    )

    await message.answer(

        text,

        reply_markup=keyboard,

        parse_mode="HTML"

    )


# =========================================================
# ИЗМЕНЕНИЕ СТАТУСА
# =========================================================

@dp.callback_query(
    F.data.startswith("status_")
)
async def change_status(
    callback: CallbackQuery
):

    if not is_admin(callback):

        await callback.answer(

            "⛔ Нет доступа",

            show_alert=True

        )

        return

    parts = callback.data.split(

        "|",

        1

    )

    if len(parts) != 2:

        await callback.answer(

            "Ошибка данных",

            show_alert=True

        )

        return

    status_code = parts[0].replace(

        "status_",

        ""

    )

    track = parts[1]

    status_map = {

        "review":
            "🟡 На рассмотрении",

        "visit":
            "🔵 Назначен выезд инспектора",

        "approved":
            "🟢 Одобрено",

        "rejected":
            "🔴 Отказ"

    }

    new_status = status_map.get(

        status_code

    )

    if not new_status:

        await callback.answer(

            "Неизвестный статус",

            show_alert=True

        )

        return

    report_file = os.path.join(

        REPORTS_FOLDER,

        track,

        "report.json"

    )

    if not os.path.exists(

        report_file

    ):

        await callback.answer(

            "❌ Заявка не найдена",

            show_alert=True

        )

        return

    try:

        with open(

            report_file,

            "r",

            encoding="utf-8"

        ) as file:

            report = json.load(file)

    except Exception:

        await callback.answer(

            "Ошибка чтения заявки",

            show_alert=True

        )

        return

    report["status"] = new_status

    report["status_code"] = status_code

    if "history" not in report:

        report["history"] = []

    report["history"].append({

        "status":
            new_status,

        "date":
            datetime.now().strftime(
                "%d.%m.%Y %H:%M:%S"
            )

    })

    with open(

        report_file,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            report,

            file,

            ensure_ascii=False,

            indent=4

        )

    await callback.answer(

        f"Статус изменён:\n{new_status}"

    )

    # -----------------------------------------
    # Уведомление пользователя
    # -----------------------------------------

    user_id = report.get(
        "user_id"
    )

    if user_id:

        try:

            explanation = STATUS_INFO.get(

                new_status,

                ""

            )

            await bot.send_message(

                user_id,

                "📢 <b>Обновление обращения</b>\n\n"

                f"📌 Номер: "
                f"<code>{track}</code>\n"

                f"📊 Новый статус: "
                f"{new_status}\n\n"

                f"💬 {explanation}",

                parse_mode="HTML"

            )

        except Exception as error:

            print(

                "Не удалось отправить уведомление:",

                error

            )

    # -----------------------------------------
    # Обновляем сообщение админа
    # -----------------------------------------

    try:

        updated = get_report_by_track(

            track

        )

        if updated:

            await callback.message.edit_text(

                "✅ <b>Статус изменён</b>\n\n"

                f"📌 Номер: "
                f"<code>{track}</code>\n\n"

                f"📊 Новый статус:\n"
                f"{new_status}\n\n"

                "Откройте заявку снова через "
                "поиск или список обращений.",

                parse_mode="HTML"

            )

    except Exception:

        pass


# =========================================================
# ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
# =========================================================

@dp.callback_query(
    F.data.startswith("delete_confirm|")
)
async def delete_confirm(
    callback: CallbackQuery
):

    if not is_admin(callback):

        await callback.answer(

            "⛔ Нет доступа",

            show_alert=True

        )

        return

    track = callback.data.split(

        "|",

        1

    )[1]

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="✅ Да, удалить",

                    callback_data=f"delete_yes|{track}"

                ),

                InlineKeyboardButton(

                    text="❌ Отмена",

                    callback_data=f"open_report|{track}"

                )

            ]

        ]

    )

    await callback.message.edit_text(

        "⚠️ <b>Удаление заявки</b>\n\n"

        f"Вы действительно хотите удалить:\n"
        f"<code>{track}</code>?\n\n"

        "Будут удалены:\n"

        "📝 данные заявки;\n"
        "📷 фотография;\n"
        "📁 папка обращения.\n\n"

        "Это действие нельзя отменить.",

        reply_markup=keyboard,

        parse_mode="HTML"

    )

    await callback.answer()


# =========================================================
# УДАЛЕНИЕ
# =========================================================

@dp.callback_query(
    F.data.startswith("delete_yes|")
)
async def delete_yes(
    callback: CallbackQuery
):

    if not is_admin(callback):

        await callback.answer(

            "⛔ Нет доступа",

            show_alert=True

        )

        return

    track = callback.data.split(

        "|",

        1

    )[1]

    report_folder = os.path.join(

        REPORTS_FOLDER,

        track

    )

    if not os.path.exists(

        report_folder

    ):

        await callback.answer(

            "❌ Заявка уже удалена "
            "или не найдена.",

            show_alert=True

        )

        return

    try:

        shutil.rmtree(

            report_folder

        )

        await callback.message.edit_text(

            "✅ <b>Заявка удалена</b>\n\n"

            f"📌 Номер:\n"
            f"<code>{track}</code>\n\n"

            "📝 Данные заявки удалены.\n"
            "📷 Фотография удалена.\n"
            "📁 Папка обращения удалена.\n\n"

            "Точка исчезнет с карты после "
            "обновления данных.",

            parse_mode="HTML"

        )

        await callback.answer(

            "🗑 Заявка удалена"

        )

    except Exception as error:

        print(

            "Ошибка удаления:",

            error

        )

        await callback.answer(

            "❌ Не удалось удалить заявку.",

            show_alert=True

        )


# =========================================================
# СТАТИСТИКА
# =========================================================

@dp.message(
    F.text == "📊 Статистика"
)
async def statistics(
    message: Message
):

    if not is_admin(message):
        return

    reports = get_all_reports()

    total = len(reports)

    review = sum(

        1

        for r in reports

        if r.get("status")
        == "🟡 На рассмотрении"

    )

    visit = sum(

        1

        for r in reports

        if r.get("status")
        == "🔵 Назначен выезд инспектора"

    )

    approved = sum(

        1

        for r in reports

        if r.get("status")
        == "🟢 Одобрено"

    )

    rejected = sum(

        1

        for r in reports

        if r.get("status")
        == "🔴 Отказ"

    )

    text = (

        "📊 <b>Статистика обращений</b>\n\n"

        f"📋 Всего: <b>{total}</b>\n\n"

        f"🟡 На рассмотрении: <b>{review}</b>\n"

        f"🔵 Назначен выезд: <b>{visit}</b>\n"

        f"🟢 Одобрено: <b>{approved}</b>\n"

        f"🔴 Отказ: <b>{rejected}</b>"

    )

    await message.answer(

        text,

        parse_mode="HTML",

        reply_markup=admin_kb()

    )


# =========================================================
# ЗАПУСК
# =========================================================

async def main():

    print(
        "=========================================="
    )

    print(
        "     ЦИФРОВОЙ МОНИТОРИНГ ЗЕМЕЛЬ"
    )

    print(
        "=========================================="
    )

    print(
        "Telegram-бот запускается..."
    )

    await dp.start_polling(
        bot
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print(
            "Бот остановлен."
        )

