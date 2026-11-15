import asyncio
import json
import logging
import os
from pathlib import Path
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# =====================================================================
# ГОТОВЫЕ НАСТРОЙКИ: ПРИЁМНАЯ АДВОКАТА МИРЗОЯНА С.Э. (@Advokat_Mirzoyan_bot)
# =====================================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = "advokat_seyran"
LAWYER_PHONE = "+7 (919) 890-07-78"

# Надёжный путь к файлу настроек в папке пользователя + дублирование в памяти
CONFIG_FILE = os.path.join(
    os.path.expanduser("~"), "mirzoyan_bot_config.json"
)
RUNTIME_CONFIG = {"admin_id": None, "video_note_id": None}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_category = {}


def load_config():
    global RUNTIME_CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                RUNTIME_CONFIG.update(data)
        except Exception as e:
            logging.warning(f"Чтение настроек из памяти: {e}")
    return RUNTIME_CONFIG


def save_config(data):
    global RUNTIME_CONFIG
    RUNTIME_CONFIG.update(data)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(RUNTIME_CONFIG, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(
            f"Настройки сохранены в оперативной памяти (запись на диск ограничена Windows): {e}"
        )


def check_and_bind_admin(user: types.User) -> int | None:
    config = load_config()
    if user.username and user.username.lower() == ADMIN_USERNAME.lower():
        if config.get("admin_id") != user.id:
            config["admin_id"] = user.id
            save_config(config)
    return config.get("admin_id")


# =====================================================================
# КЛАВИАТУРЫ ПРИЁМНОЙ (КАТЕГОРИИ ДЕЛ)
# =====================================================================
def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💼 Арбитражные споры / Защита бизнеса",
                    callback_data="cat_arbitrazh",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚖️ Гражданские и имущественные споры",
                    callback_data="cat_civil",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏛️ Административные дела и госорганы",
                    callback_data="cat_admin",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡️ Защита по уголовным делам (УК РФ)",
                    callback_data="cat_criminal",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚨 Срочный вопрос / Нужен звонок сегодня",
                    callback_data="cat_urgent",
                )
            ],
        ]
    )


def get_client_reply_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Отправить мой номер телефона", request_contact=True
                )
            ],
            [KeyboardButton(text="🔄 В главное меню")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


# =====================================================================
# УПРАВЛЕНИЕ ДЛЯ АДВОКАТА (@advokat_seyran)
# =====================================================================
@dp.message(Command("delvideo"))
async def cmd_delvideo(message: types.Message):
    admin_id = check_and_bind_admin(message.from_user)
    if message.from_user.id == admin_id:
        config = load_config()
        config["video_note_id"] = None
        save_config(config)
        await message.answer("✅ Приветственный видео-кружочек отключен.")


@dp.message(F.video_note)
async def handle_video_note(message: types.Message):
    admin_id = check_and_bind_admin(message.from_user)
    if message.from_user.id == admin_id:
        config = load_config()
        config["video_note_id"] = message.video_note.file_id
        save_config(config)
        await message.answer(
            "✅ <b>Видео-кружочек успешно установлен в качестве приветствия!</b>\n\n"
            "Теперь каждый новый доверитель при нажатии /start сначала увидит ваше личное видеообращение.\n"
            "Чтобы удалить его, отправьте команду /delvideo.",
            parse_mode="HTML",
        )
    else:
        await forward_to_lawyer(message, "Видеосообщение от доверителя")


# =====================================================================
# СТАРТ БОТА И ВЫБОР КАТЕГОРИИ
# =====================================================================
@dp.message(CommandStart())
@dp.message(F.text == "🔄 В главное меню")
async def cmd_start(message: types.Message):
    admin_id = check_and_bind_admin(message.from_user)
    config = load_config()

    if message.from_user.id == admin_id and message.text == "/start":
        await message.answer(
            "🔑 <b>Режим владельца активирован (@advokat_seyran).</b>\n"
            "Ваш аккаунт привязан к приёмной. Все обращения, документы и контакты доверителей приходят прямо в этот чат.\n"
            "<i>Ниже показано финальное меню, которое видят ваши доверители:</i>",
            parse_mode="HTML",
        )

    video_id = config.get("video_note_id")
    if video_id and message.text == "/start":
        try:
            await message.answer_video_note(video_note=video_id)
        except Exception as e:
            logging.warning(f"Ошибка отправки видео-кружочка: {e}")

    welcome_text = (
        "<b>Приёмная адвоката Мирзояна Сейрана Эдиковича</b>\n"
        "<i>Регистрационный номер 61/5634 в Едином государственном реестре адвокатов\n"
        "Удостоверение № 7401 выдано 17.01.2019 г.</i>\n\n"
        "Прямо сейчас я могу находиться в судебном заседании. Оставьте материалы по вашему делу ниже — я лично изучу их и свяжусь с вами с готовым правовым решением.\n\n"
        "<b>Основные направления практики:</b>\n"
        "• <b>Арбитражные споры / Защита бизнеса</b>\n"
        "• <b>Гражданские и имущественные споры</b> <i>(договоры, семья, наследство, земля, недвижимость, автомобили, взыскание, кредиты и т.д., апелляция/кассация и Верховный Суд РФ)</i>\n"
        "• <b>Административные дела и споры с госорганами</b>\n"
        "• <b>Защита по уголовным делам (УК РФ)</b>\n\n"
        "🔒 <b>Гарантия конфиденциальности:</b> все переданные вами сведения и документы строго защищены адвокатской тайной (ст. 8 ФЗ-63 «Об адвокатской деятельности и адвокатуре в РФ»).\n\n"
        "<b>Выберите категорию вашего вопроса:</b>"
    )
    await message.answer(
        welcome_text, parse_mode="HTML", reply_markup=get_main_menu()
    )


@dp.callback_query(F.data.startswith("cat_"))
async def select_category(callback: types.CallbackQuery):
    code = callback.data
    user_id = callback.from_user.id

    if code == "cat_arbitrazh":
        user_category[user_id] = "💼 Арбитражные споры / Защита бизнеса"
        text = (
            "<b>Направление: Арбитражные споры / Защита бизнеса</b>\n\n"
            "Чтобы предметно оценить судебную перспективу до звонка, пришлите сюда в свободной форме:\n"
            "1️⃣ <b>ИНН оппонента</b> или <b>номер дела</b> в суде (если процесс уже идет);\n"
            "2️⃣ <b>Фото или файлы</b> договора, претензии, иска или судебного акта;\n"
            "3️⃣ <b>Краткую суть задачи</b> (текстом или голосовым сообщением).\n\n"
            "👇 <i>Отправьте материалы в чат и нажмите кнопку «📱 Отправить мой номер телефона» внизу экрана:</i>"
        )
    elif code == "cat_civil":
        user_category[user_id] = "⚖️ Гражданские и имущественные споры"
        text = (
            "<b>Направление: Гражданские и имущественные споры</b>\n"
            "<i>(договоры, семья, наследство, земля, недвижимость, автомобили, взыскание, кредиты и т.д., апелляция/кассация и Верховный Суд РФ)</i>\n\n"
            "Опишите вашу ситуацию <b>текстом или голосовым сообщением</b> и прикрепите фотографии имеющихся документов (договор, претензия, иск, решение суда или отказ).\n\n"
            "👇 <i>Отправьте материалы в этот чат и оставьте контакт по кнопке внизу экрана — я изучу документы и лично свяжусь с вами:</i>"
        )
    elif code == "cat_admin":
        user_category[user_id] = "🏛️ Административные дела (КоАП / КАС РФ)"
        text = (
            "<b>Направление: Административные дела и споры с государственными органами (КоАП РФ, КАС РФ)</b>\n"
            "<i>Обжалование постановлений, штрафов, предписаний, решений и действий (бездействия) государственных органов и должностных лиц.</i>\n\n"
            "Пришлите сюда <b>фото или файл протокола, акта, предписания или постановления</b> (важно для проверки сроков обжалования) и кратко опишите обстоятельства дела текстом или голосовым сообщением.\n\n"
            "👇 <i>Отправьте документы в чат и нажмите кнопку «📱 Отправить мой номер телефона» внизу экрана:</i>"
        )
    elif code == "cat_criminal":
        user_category[user_id] = "🛡️ Уголовная защита (УК РФ)"
        text = (
            "<b>Направление: Защита и представительство по уголовным делам и доследственным проверкам (ст. 144–145 УПК РФ)</b>\n\n"
            "⚠️ <b>ВАЖНОЕ ПРАВИЛО БЕЗОПАСНОСТИ:</b>\n"
            "В целях вашей защиты <b>не описывайте подробности и фактические обстоятельства дела текстом в мессенджере</b> до личного разговора с адвокатом.\n\n"
            "Напишите сюда только:\n"
            "1️⃣ <b>Статью УК РФ</b> (если известна) и процессуальный статус (проверка, свидетель, подозреваемый, обвиняемый, потерпевший);\n"
            "2️⃣ Нажмите кнопку <b>«📱 Отправить мой номер телефона»</b> внизу экрана для созвона или согласования очной встречи.\n\n"
            f"📞 При экстренной ситуации (обыск, задержание, допрос) звоните напрямую: <b>{LAWYER_PHONE}</b>"
        )
    else:
        user_category[user_id] = "🚨 СРОЧНЫЙ ЗВОНОК"
        text = (
            "<b>Срочная связь с адвокатом Мирзояном С.Э.</b>\n\n"
            "Нажмите кнопку <b>«📱 Отправить мой номер телефона»</b> внизу экрана (или напишите номер цифрами) и укажите:\n"
            "• Кратко тему вопроса;\n"
            "• В какое время сегодня вам удобно принять звонок.\n\n"
            f"Прямой контакт адвоката в Telegram: @{ADMIN_USERNAME} | Тел.: <b>{LAWYER_PHONE}</b>"
        )

    await callback.message.answer(
        text, parse_mode="HTML", reply_markup=get_client_reply_kb()
    )
    await callback.answer()


# =====================================================================
# МГНОВЕННАЯ ПЕРЕСЫЛКА ДОКУМЕНТОВ, ГОЛОСОВЫХ И КОНТАКТОВ АДВОКАТУ
# =====================================================================
async def forward_to_lawyer(message: types.Message, content_type_label: str):
    user = message.from_user
    admin_id = check_and_bind_admin(user)

    if user.id == admin_id:
        await message.answer(
            "ℹ️ Вы пишете со своего аккаунта владельца (@advokat_seyran).\n"
            "Чтобы установить видеоприветствие — отправьте сюда <b>видео-кружочек</b>.\n"
            "Все сообщения от доверителей автоматически пересылаются вам.",
            parse_mode="HTML",
        )
        return

    category = user_category.get(user.id, "Рубрика не выбрана")
    username_str = f"@{user.username}" if user.username else "ник скрыт"
    full_name = user.full_name or "Доверитель"

    header = (
        f"🔔 <b>НОВОЕ ОБРАЩЕНИЕ В ПРИЁМНУЮ</b>\n"
        f"📂 <b>Направление:</b> {category}\n"
        f"👤 <b>Доверитель:</b> {full_name} ({username_str})\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code> | <a href='tg://user?id={user.id}'>Написать доверителю в 1 клик</a>\n"
        f"📎 <b>Получено:</b> {content_type_label}"
    )

    if admin_id:
        try:
            await bot.send_message(
                chat_id=admin_id, text=header, parse_mode="HTML"
            )
            await message.forward(chat_id=admin_id)
        except Exception as e:
            logging.error(f"Ошибка пересылки адвокату: {e}")

    await message.answer(
        "✅ <b>Принято в работу и передано лично адвокату Мирзояну С.Э.</b>\n"
        "Вы можете дослать сюда дополнительные фотографии документов, голосовое пояснение или нажать кнопку <b>«📱 Отправить мой номер телефона»</b> ниже.",
        parse_mode="HTML",
        reply_markup=get_client_reply_kb(),
    )


@dp.message(F.contact)
async def handle_contact(message: types.Message):
    await forward_to_lawyer(
        message, f"📞 Номер телефона: {message.contact.phone_number}"
    )


@dp.message(F.voice)
async def handle_voice(message: types.Message):
    await forward_to_lawyer(message, "🎤 Голосовое сообщение")


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await forward_to_lawyer(message, "📷 Фотография документа")


@dp.message(F.document)
async def handle_document(message: types.Message):
    await forward_to_lawyer(message, "📄 Файл / Документ")


@dp.message(F.text)
async def handle_text(message: types.Message):
    if message.text.startswith("/"):
        return
    await forward_to_lawyer(message, "💬 Текстовое сообщение")


async def main():
    load_config()
    print("===============================================================")
    print("Защищенная версия Приёмной адвоката Мирзояна С.Э. ЗАПУЩЕНА!")
    print("===============================================================")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())