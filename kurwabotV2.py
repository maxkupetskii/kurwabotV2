#!/usr/bin/python3
from match_regex import RegexEqual
from strings import Strings
from secrets import ALLOWED_IDS, KURWA_TOKEN
from actions import Action
import logging
from functools import wraps
from telegram import __version__ as TG_VER
from tasting import Tasting, REMOVE_ID_INDEX
import asyncio

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
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
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
            logger.info(Strings.RESTRICTED.format(user))
            return
        return await func(update, context, *args, **kwargs)

    return wrapped


current_tasting: Tasting | None = None


@restricted
async def create_tasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_tasting
    if current_tasting is None:
        current_tasting = Tasting(chat_id=update.message.chat_id)
        # удаляем сообщение с командой
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
        # пустая табличка с дегой, надо запомнить id
        init_message = await update.message.reply_text(Strings.TITLE, reply_markup=current_tasting.generate_keyboard())
        current_tasting.tasting_message_id = init_message.message_id
    else:
        reply_keyboard = [[Strings.REPLY_DELETE, Strings.REPLY_CANCEL]]
        await update.message.reply_text(
            Strings.REPLY_TITLE_DELETE,
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True)
        )


@restricted
async def kill_tasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_tasting
    current_tasting = None
    await create_tasting(update, context)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    match RegexEqual(query.data):
        case Action.ROLL.value:
            await roll_tasting(update, context)
        case Action.MINUS.value:
            if current_tasting.people > 0 and update.effective_user.id in ALLOWED_IDS:
                current_tasting.people -= 1
                await query.edit_message_reply_markup(reply_markup=current_tasting.generate_keyboard())
        case Action.PLUS.value:
            if update.effective_user.id in ALLOWED_IDS:
                current_tasting.people += 1
                await query.edit_message_reply_markup(reply_markup=current_tasting.generate_keyboard())
        case Action.ADD_ME.value:
            await add_me(update, context)
        case Action.REMOVE_ME.value:
            triggered_id = f'{update.effective_user.id}'
            id_to_delete = query.data[REMOVE_ID_INDEX:]
            if triggered_id == id_to_delete:
                await remove_me(update, context)
        case _:
            return


@restricted
async def roll_tasting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if current_tasting.people == 0:
        reply_message = await update.callback_query.message.reply_text(Strings.REPLY_0_PEOPLE)
        await asyncio.sleep(1)
        await context.bot.delete_message(chat_id=update.callback_query.message.chat_id, message_id=reply_message.message_id)
        return
    if len(current_tasting.users) == 0:
        reply_message = await update.callback_query.message.reply_text(Strings.REPLY_0_USERS)
        await asyncio.sleep(1)
        await context.bot.delete_message(chat_id=update.callback_query.message.chat_id, message_id=reply_message.message_id)
        return
    reply_keyboard = [[Strings.REPLY_START, Strings.REPLY_CANCEL]]
    await update.callback_query.message.reply_text(
        Strings.REPLY_TITLE_ROLL,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, selective=True)
    )


@restricted
async def choose_winners(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global current_tasting
    if current_tasting is None:
        return
    current_tasting.roll(initiated_user=update.effective_user)
    winners = current_tasting.winners_message()
    # удаляем сообщение "Стартуём!"
    await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    # удаляем сообщение с кнопками/участниками
    await context.bot.delete_message(chat_id=update.message.chat_id, message_id=current_tasting.tasting_message_id)
    # засылаем победителей
    await update.message.reply_text(winners, reply_markup=ReplyKeyboardRemove())
    current_tasting = None


async def add_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if current_tasting.add(update.effective_user):
        await update.callback_query.edit_message_reply_markup(reply_markup=current_tasting.generate_keyboard())


async def remove_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if current_tasting.remove(update.effective_user):
        await update.callback_query.edit_message_reply_markup(reply_markup=current_tasting.generate_keyboard())


def main() -> None:
    application = Application.builder().token(KURWA_TOKEN).build()
    application.add_handler(CommandHandler("kurwa_bobr", create_tasting))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.Regex(f'^({Strings.REPLY_DELETE})$'), kill_tasting))
    application.add_handler(MessageHandler(filters.Regex(f'^({Strings.REPLY_START})$'), choose_winners))
    application.run_polling()


if __name__ == "__main__":
    main()
