# -*- coding: utf-8 -*-

import os
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# 🔐 Токен из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Добавь его в переменные окружения.")

PRIVATE_CHANNEL_ID = -1003336905435
ADMIN_CHANNEL_ID = -1003109975028

TARIFF_NAME = "PrivatForFap🍑"
PRICE = "200 ₽"

# временное хранилище заявок
PENDING_PAYMENTS = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(
            f"🍑 {TARIFF_NAME} — {PRICE}",
            callback_data="buy"
        )]
    ]

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Выбери тариф для покупки 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user

    if query.data == "buy":
        keyboard = [
            [InlineKeyboardButton("💳 СБП (200 ₽)", callback_data="sbp")]
        ]

        await query.message.reply_text(
            f"📦 Тариф: {TARIFF_NAME}\n"
            f"💰 Цена: {PRICE}\n\n"
            "Выбери способ оплаты:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "sbp":
        keyboard = [
            [InlineKeyboardButton(
                "⏳ Я оплатил (ожидание)",
                callback_data="wait"
            )]
        ]

        await query.message.reply_text(
            "💳 *Оплата по СБП*\n\n"
            "Переведи *200 ₽* по реквизитам:\n"
            "👉 ТУТ ТВОИ РЕКВИЗИТЫ\n\n"
            "После оплаты нажми кнопку ниже 👇",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "wait":
        time = datetime.now().strftime("%d.%m.%Y %H:%M")

        PENDING_PAYMENTS[user.id] = True

        admin_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "✅ Подтвердить оплату",
                callback_data=f"approve_{user.id}"
            )]
        ])

        await context.bot.send_message(
            chat_id=ADMIN_CHANNEL_ID,
            text=(
                "💸 *Заявка на оплату*\n\n"
                f"👤 @{user.username or 'без username'}\n"
                f"🆔 ID: {user.id}\n"
                f"📦 Тариф: {TARIFF_NAME}\n"
                f"💳 Способ: СБП\n"
                f"🕒 Время: {time}"
            ),
            reply_markup=admin_keyboard,
            parse_mode="Markdown"
        )

        await query.message.reply_text(
            "⏳ *Заявка отправлена*\n\n"
            "Ожидай подтверждения оплаты администратором.",
            parse_mode="Markdown"
        )

    elif query.data.startswith("approve_"):
        user_id = int(query.data.split("_")[1])

        if user_id not in PENDING_PAYMENTS:
            await query.message.reply_text("❌ Заявка уже обработана")
            return

        link = await context.bot.create_chat_invite_link(
            chat_id=PRIVATE_CHANNEL_ID,
            member_limit=1
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 *Оплата подтверждена!*\n\n"
                "Вот ссылка для входа в приват 👇\n\n"
                f"{link.invite_link}"
            ),
            parse_mode="Markdown"
        )

        del PENDING_PAYMENTS[user_id]

        await query.message.edit_text(
            "✅ Оплата подтверждена\nДоступ выдан"
        )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.run_polling()


if __name__ == "__main__":
    main()
