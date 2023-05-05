#!/usr/bin/python3
from datetime import datetime
from match_regex import RegexEqual
import telegram
from secrets import ALLOWED_IDS, KURWA_TOKEN
from actions import Action
import logging
from functools import wraps
from telegram import __version__ as TG_VER
import random

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def restricted(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user = update.effective_user
        if user.id not in ALLOWED_IDS:
            logger.info(f'юзер {user} не шмог')
            return
        return await func(update, context, *args, **kwargs)

    return wrapped


current_tasting = None
people: int = 0
users: dict[int, telegram.User] = {}


def generate_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Choose winners!🎲", callback_data=Action.ROLL.value)],
        [
            InlineKeyboardButton("(-)", callback_data=Action.MINUS.value),
            InlineKeyboardButton(f'{people}', callback_data=Action.NUM.value),
            InlineKeyboardButton("(+)", callback_data=Action.PLUS.value)
        ],
        [InlineKeyboardButton("Add me!🍇", callback_data=Action.ADD_ME.value)]
    ]
    if len(users) > 0:
        for user_id, user in users.items():
            # use last_name if username is not present
            last = f'(@{user.username})' if user.username else user.last_name
            single_user = [
                InlineKeyboardButton(f'{user.first_name} {last}', callback_data=Action.NAME.value),
                InlineKeyboardButton("⛔️", callback_data=f'{Action.REMOVE_ME.value} id:{user_id}'),
            ]
            keyboard.append(single_user)
    return InlineKeyboardMarkup(keyboard)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global people, users
    query = update.callback_query
    await query.answer()
    match RegexEqual(query.data):
        case Action.ROLL.value:
            await roll_tasting(update, context)
        case Action.MINUS.value:
            if people > 0 and update.effective_user.id in ALLOWED_IDS:
                people -= 1
                await query.edit_message_reply_markup(reply_markup=generate_keyboard())
        case Action.PLUS.value:
            if update.effective_user.id in ALLOWED_IDS:
                people += 1
                await query.edit_message_reply_markup(reply_markup=generate_keyboard())
        case Action.ADD_ME.value:
            await add_me(update, context)
        case Action.REMOVE_ME.value:
            triggered_id = f'{update.effective_user.id}'
            id_to_delete = query.data[13:] # haha, magic number
            if triggered_id == id_to_delete:
                await remove_me(update, context)
        case _:
            return


@restricted
async def create_tasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_tasting
    if current_tasting is None:
        current_tasting = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        await update.message.reply_text("🍷Wine tasting roulette!🍷", reply_markup=generate_keyboard())
    else:
        reply_keyboard = [["Стираём всех!", "Не"]]
        await update.message.reply_text(
            "Дега уже создана, херим?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )


@restricted
async def kill_tasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_tasting, users
    current_tasting = None
    users.clear()
    await create_tasting(update, context)


@restricted
async def roll_tasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if people == 0:
        await update.callback_query.message.reply_text("Мест 0, тыкай плюсики!")
        await update.callback_query.message.reply_text("🍷Wine tasting roulette!🍷", reply_markup=generate_keyboard())
        return

    reply_keyboard = [["Стартуём!", "Не"]]
    await update.callback_query.message.reply_text(
        "Вращаем барабан?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, input_field_placeholder="Го?")
    )


@restricted
async def choose_winners(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global users, current_tasting, people
    if current_tasting is None:
        return
    initiated_user = update.effective_user
    all_ids = list(users.keys())
    random.shuffle(all_ids)
    winners = winners_message(all_ids)
    winners += f'\n@{initiated_user.username}'
    await update.message.reply_text(winners, reply_markup=ReplyKeyboardRemove())
    current_tasting = None
    people = 0
    users.clear()


def winners_message(shuffled_ids: list) -> str:
    def get_user_info(num: int, user_id: int) -> str:
        user = users.get(user_id)
        user_string = f'{num + 1}) {user.full_name}'
        if user.username:
            user_string += f' (@{user.username})'
        user_string += "\n"
        return user_string

    winners = "🍷Wine tasting roulette!🍷\n\n"
    winners += "The winners are:\n"
    for counter, shuffle_id in enumerate(shuffled_ids):
        if counter < people:
            winners += get_user_info(counter, shuffle_id)
        elif counter == people:
            winners += "Waiting list:\n"
            winners += get_user_info(counter, shuffle_id)
        else:
            winners += get_user_info(counter, shuffle_id)
    return winners


async def add_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global users
    user = update.effective_user
    if user.id not in users.keys():
        users[user.id] = user
        await update.callback_query.edit_message_reply_markup(reply_markup=generate_keyboard())


async def remove_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global users
    user = update.effective_user
    if user.id in users.keys():
        del users[update.effective_user.id]
        await update.callback_query.edit_message_reply_markup(reply_markup=generate_keyboard())


def main() -> None:
    application = Application.builder().token(KURWA_TOKEN).build()

    application.add_handler(CommandHandler("kurwa_bobr", create_tasting))
    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(MessageHandler(filters.Regex("^(Стираём всех!)$"), kill_tasting))
    application.add_handler(MessageHandler(filters.Regex("^(Стартуём!)$"), choose_winners))
    application.run_polling()


if __name__ == "__main__":
    main()
