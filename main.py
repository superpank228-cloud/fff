# -*- coding: utf-8 -*-

import os
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден")

PRIVATE_CHANNEL_ID = -1003336905435
ADMIN_CHANNEL_ID = -1003109975028

TARIFF_NAME = "PrivatForFap🍑"
PRICE = "200 ₽"
SUBSCRIPTION_DAYS = ∞

PENDING_PAYMENTS = {}
SUBSCRIPTIONS = {}  # user_id -> expire_date


def get_main_menu():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("🛒 Тарифы"), KeyboardButton("📊 Подписка")]],
        resize_keyboard=True
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\nВыбери пункт меню 👇",
        reply_markup=get_main_menu()
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "🛒 Тарифы":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🍑 {TARIFF_NAME} — {PRICE}", callback_data="buy")]
        ])
        await update.message.reply_text("📦 Доступные тарифы:", reply_markup=keyboard)

    elif text == "📊 Подписка":
        now = datetime.now()
        expire = SUBSCRIPTIONS.get(user_id)

        if expire and expire > now:
            await update.message.reply_text(
                "📊 *Информация о подписке*\n\n"
                f"✅ Активна до: *{expire.strftime('%d.%m.%Y %H:%M')}*",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "📊 *Информация о подписке*\n\n"
                "❌ У тебя нет активной подписки.",
                parse_mode="Markdown"
            )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "buy":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 СБП (200 ₽)", callback_data="sbp")]
        ])
        await query.message.reply_text(
            f"📦 Тариф: {TARIFF_NAME}\n💰 Цена: {PRICE}\n\nВыбери способ оплаты:",
            reply_markup=keyboard
        )

    elif query.data == "sbp":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏳ Я оплатил", callback_data="wait")]
        ])
        await query.message.reply_text(
            "💳 *Оплата по СБП*\n\n"
            "Переведи *200 ₽* по реквизитам:\n"
            "👉 ТУТ ТВОИ РЕКВИЗИТЫ\n\n"
            "После оплаты нажми кнопку ниже 👇",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif query.data == "wait":
        PENDING_PAYMENTS[user.id] = True
        time = datetime.now().strftime("%d.%m.%Y %H:%M")

        admin_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"approve_{user.id}")]
        ])

        await context.bot.send_message(
            ADMIN_CHANNEL_ID,
            "💸 *Заявка на оплату*\n\n"
            f"👤 @{user.username or 'без username'}\n"
            f"🆔 ID: {user.id}\n"
            f"📦 Тариф: {TARIFF_NAME}\n"
            f"🕒 Время: {time}",
            reply_markup=admin_keyboard,
            parse_mode="Markdown"
        )

        await query.message.reply_text("⏳ Заявка отправлена. Ожидай подтверждения.")

    elif query.data.startswith("approve_"):
        user_id = int(query.data.split("_")[1])

        if user_id not in PENDING_PAYMENTS:
            await query.message.reply_text("❌ Заявка уже обработана")
            return

        expire_date = datetime.now() + timedelta(days=SUBSCRIPTION_DAYS)
        SUBSCRIPTIONS[user_id] = expire_date
        del PENDING_PAYMENTS[user_id]

        link = await context.bot.create_chat_invite_link(
            chat_id=PRIVATE_CHANNEL_ID,
            member_limit=1
        )

        await context.bot.send_message(
            user_id,
            "🎉 *Оплата подтверждена!*\n\n"
            f"✅ Подписка активна до: *{expire_date.strftime('%d.%m.%Y %H:%M')}*\n\n"
            f"🔗 Ссылка для входа:\n{link.invite_link}",
            parse_mode="Markdown"
        )

        await query.message.edit_text("✅ Оплата подтверждена\nПодписка активирована")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.run_polling()


if __name__ == "__main__":
    main()
