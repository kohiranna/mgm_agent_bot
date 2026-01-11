from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)
from cities import MOLDOVA_CITIES, CHISINAU_DISTRICTS

import os

TOKEN = os.getenv("BOT_TOKEN")
TEST_CHAT_ID = -1003663485405

# --- Состояния ---
(
    CLIENT_TYPE, CITY, DISTRICT, PLACE_NAME, LEGAL_NAME,
    PLACE_TYPE, ADDRESS, CONTACT, COFFEE, SYRUPS,
    MILK, OFFERED, COMMENT, LOCATION, PHOTO, PHOTO_MORE
) = range(16)


# --- Утилиты ---
def capitalize_message(text: str) -> str:
    return ". ".join([s.strip().capitalize() for s in text.split('.') if s]) + ('.' if text.endswith('.') else '')

def new_report_keyboard():
    return ReplyKeyboardMarkup([["Новый отчет"]], resize_keyboard=True, one_time_keyboard=True)


# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    await update.message.reply_text(
        f"Здравствуйте, {user.first_name}!\nНажмите кнопку ниже, чтобы начать новый отчет.",
        reply_markup=new_report_keyboard()
    )


# --- Начало отчета ---
async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text != "/report" and text.lower() != "новый отчет":
        await update.message.reply_text('Чтобы начать отчет, нажмите кнопку "Новый отчет" или /report.')
        return ConversationHandler.END

    context.user_data.clear()
    user = update.effective_user
    context.user_data.update({
        "agent_id": user.id,
        "agent_name": f"{user.first_name} {user.last_name or ''}".strip(),
        "agent_username": user.username,
        "photos": [],
        "location": None,
    })

    keyboard = [["🆕 Новый клиент", "🔁 Существующий клиент"]]
    await update.message.reply_text(
        "Выберите тип клиента:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CLIENT_TYPE


# --- Выбор типа клиента ---
async def client_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in ["🆕 Новый клиент", "🔁 Существующий клиент"]:
        await update.message.reply_text("Выберите тип клиента кнопкой.")
        return CLIENT_TYPE

    context.user_data["client_type"] = choice
    keyboard = [MOLDOVA_CITIES[i:i+3] for i in range(0, len(MOLDOVA_CITIES), 3)]
    keyboard.append(["Другой город"])
    await update.message.reply_text(
        "Выберите город из списка или 'Другой город':",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CITY


# --- Город ---
async def city_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    if city == "Другой город":
        await update.message.reply_text("Введите название города вручную:")
        return CITY

    if city.lower() in ["кишинев", "кишинёв", "chisinau"]:
        context.user_data["city"] = "Кишинёв"
        keyboard = [CHISINAU_DISTRICTS[i:i+3] for i in range(0, len(CHISINAU_DISTRICTS), 3)]
        await update.message.reply_text(
            "Выберите район:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return DISTRICT
    elif city in MOLDOVA_CITIES:
        context.user_data["city"] = city
        await update.message.reply_text("Введите название заведения:", reply_markup=ReplyKeyboardRemove())
        return PLACE_NAME
    else:
        await update.message.reply_text("Город не найден. Выберите из списка или введите вручную.")
        return CITY


# --- Район ---
async def district_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["district"] = capitalize_message(update.message.text.strip())
    await update.message.reply_text("Введите название заведения:", reply_markup=ReplyKeyboardRemove())
    return PLACE_NAME


# --- Название заведения ---
async def place_name_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["place_name"] = capitalize_message(update.message.text.strip())
    await update.message.reply_text("Введите юридическое название заведения:")
    return LEGAL_NAME


# --- Юридическое название ---
async def legal_name_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["legal_name"] = capitalize_message(update.message.text.strip())
    if context.user_data["client_type"] == "🆕 Новый клиент":
        keyboard = [["кофейня", "кафе", "патисерия", "togo"], ["drive", "бар", "ресторан", "другое"]]
        await update.message.reply_text(
            "Выберите тип заведения:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return PLACE_TYPE
    else:
        await update.message.reply_text("Комментарий агента:")
        return COMMENT


# --- Тип заведения (для нового клиента) ---
async def place_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["place_type"] = capitalize_message(update.message.text.strip())
    await update.message.reply_text("Введите адрес заведения:", reply_markup=ReplyKeyboardRemove())
    return ADDRESS


# --- Адрес ---
async def address_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = capitalize_message(update.message.text.strip())
  
    await update.message.reply_text(
        "Введите контактный номер вручную или отправьте контакт через 📎 → Контакт.",
        
    )
    return CONTACT


# --- Контакт ---
async def contact_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["contact"] = update.message.contact.phone_number
    else:
        text = update.message.text.strip()
        context.user_data["contact"] = text if text.lower() != "пропустить" else "-"
    if context.user_data["client_type"] == "🆕 Новый клиент":
        await update.message.reply_text("С каким кофе работают?", reply_markup=ReplyKeyboardRemove())
        return COFFEE
    else:
        await update.message.reply_text("Комментарий агента:", reply_markup=ReplyKeyboardRemove())
        return COMMENT


# --- Кофе / Сиропы / Молоко / Предложение (только для нового клиента) ---
async def coffee_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["coffee"] = capitalize_message(update.message.text.strip())
    await update.message.reply_text("С какими сиропами/пюре работают?")
    return SYRUPS

async def syrups_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["syrups"] = capitalize_message(update.message.text.strip())
    await update.message.reply_text("С каким растительным молоком работают?")
    return MILK

async def milk_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["milk"] = capitalize_message(update.message.text.strip())
    await update.message.reply_text("Что предложили клиенту?")
    return OFFERED

async def offered_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["offered"] = capitalize_message(update.message.text.strip())
    await update.message.reply_text("Комментарий агента:")
    return COMMENT


# --- Комментарий ---
async def comment_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["comment"] = capitalize_message(update.message.text.strip())
    keyboard = [
        [KeyboardButton(text="Отправить локацию", request_location=True)]
       
    ]
    await update.message.reply_text(
        "Отправьте геолокацию:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return LOCATION


# --- Геолокация ---
async def location_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.location:
        loc = update.message.location
        context.user_data["location"] = (loc.latitude, loc.longitude)
    else:
        text = update.message.text.strip().lower()
        context.user_data["location"] = None if text == "пропустить" else None
    await update.message.reply_text("Отправьте фото заведения:", reply_markup=ReplyKeyboardRemove())
    return PHOTO


# --- Фото ---
async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Пожалуйста, отправьте фотографию.")
        return PHOTO
    context.user_data["photos"].append(update.message.photo[-1].file_id)
    keyboard = ReplyKeyboardMarkup([["more", "end"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Фото получено. Добавить ещё? «more» / «end»", reply_markup=keyboard)
    return PHOTO_MORE


async def photo_more_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text == "more":
        await update.message.reply_text("Отправьте следующее фото:", reply_markup=ReplyKeyboardRemove())
        return PHOTO
    elif text == "end":
        # --- Формируем отчет ---
        data = context.user_data
        lines = [
            f"**• Отчет от агента:** {data.get('agent_name')}",
            f"**• Клиент:** {data.get('client_type')}",
            f"**• Город:** {data.get('city')}",
        ]
        if "district" in data:
            lines.append(f"**• Район:** {data.get('district')}")
        lines.append(f"**• Название заведения:** {data.get('place_name')}")
        lines.append(f"**• Юридическое название:** {data.get('legal_name')}")
        if data.get("client_type") == "🆕 Новый клиент":
            lines.extend([
                f"**• Тип заведения:** {data.get('place_type')}",
                f"**• Адрес:** {data.get('address')}",
                f"**• Контактный номер:** {data.get('contact')}",
                f"**• Кофе:** {data.get('coffee')}",
                f"**• Сиропы/пюре:** {data.get('syrups')}",
                f"**• Растительное молоко:** {data.get('milk')}",
                f"**• Что предложили:** {data.get('offered')}",
            ])
        else:
            lines.append(f"**• Контактный номер:** {data.get('contact', '-')}")
        lines.append(f"**• Комментарий:** {data.get('comment')}")
        report_text = "\n".join(lines)

        # Отправка в чат
        await context.bot.send_message(chat_id=TEST_CHAT_ID, text=report_text, parse_mode=ParseMode.MARKDOWN)
        if data.get("location"):
            lat, lon = data["location"]
            await context.bot.send_location(chat_id=TEST_CHAT_ID, latitude=lat, longitude=lon)
        for photo_id in data.get("photos", []):
            await context.bot.send_photo(chat_id=TEST_CHAT_ID, photo=photo_id)

        await update.message.reply_text("Отчет отправлен. ✅", reply_markup=new_report_keyboard())
        context.user_data.clear()
        return ConversationHandler.END
    else:
        await update.message.reply_text("Нажмите «more» для фото или «end» для завершения.", reply_markup=ReplyKeyboardMarkup([["more","end"]], resize_keyboard=True, one_time_keyboard=True))
        return PHOTO_MORE


# --- Отмена ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отчет отменён.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


# --- Основной Application ---
app = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("report", report_start),
        MessageHandler(filters.Regex("^(Новый отчет|новый отчет)$"), report_start),
    ],
    states={
        CLIENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_type_chosen)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_chosen)],
        DISTRICT: [MessageHandler(filters.TEXT & ~filters.COMMAND, district_chosen)],
        PLACE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, place_name_chosen)],
        LEGAL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, legal_name_chosen)],
        PLACE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, place_type_chosen)],
        ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address_chosen)],
        CONTACT: [MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), contact_chosen)],
        COFFEE: [MessageHandler(filters.TEXT & ~filters.COMMAND, coffee_chosen)],
        SYRUPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, syrups_chosen)],
        MILK: [MessageHandler(filters.TEXT & ~filters.COMMAND, milk_chosen)],
        OFFERED: [MessageHandler(filters.TEXT & ~filters.COMMAND, offered_chosen)],
        COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment_chosen)],
        LOCATION: [MessageHandler((filters.LOCATION | (filters.TEXT & ~filters.COMMAND)), location_received)],
        PHOTO: [MessageHandler(filters.PHOTO, photo_received)],
        PHOTO_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, photo_more_chosen)],
    },
    fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    allow_reentry=True
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)

app.run_polling()

