import os

from telegram import Update
from telegram.ext import Updater, CallbackContext, MessageHandler, Filters

from dotenv import load_dotenv


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.text
    )


def main():
    load_dotenv()
    tg_token = os.getenv('TG_TOKEN')
    updater = Updater(token=tg_token)
    dispatcher = updater.dispatcher
    echo_hanlder = MessageHandler(
        Filters.text,
        echo
    )

    dispatcher.add_handler(echo_hanlder)
    updater.start_polling()


if __name__ == '__main__':
    main()
