import json
import os
import random

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater, CallbackContext, MessageHandler, Filters, CommandHandler
)

from dotenv import load_dotenv


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.text
    )


def start(update: Update, context: CallbackContext):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    keyboard = ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Привет! Я бот для викторин',
        reply_markup=keyboard
    )


def quiz(update: Update, context: CallbackContext):
    if update.message.text == 'Новый вопрос':
        question = random.choice(
            list(context.bot_data.get('questions', {}).values())
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=question.get('вопрос')
        )


def main():
    load_dotenv()
    tg_token = os.getenv('TG_TOKEN')
    updater = Updater(token=tg_token)
    dispatcher = updater.dispatcher
    with open(
        os.path.join(os.path.curdir, 'questions', 'questions.json'),
        'r'
    ) as file:
        questions = json.load(file)
    dispatcher.bot_data['questions'] = questions

    text_handler = MessageHandler(
        Filters.text & (~Filters.command),
        quiz
    )
    start_handler = CommandHandler('start', start)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(text_handler)
    updater.start_polling()


if __name__ == '__main__':
    main()
