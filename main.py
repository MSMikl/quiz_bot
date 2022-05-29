import json
import os
import random

import redis

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater, CallbackContext, MessageHandler,
    Filters, CommandHandler, ConversationHandler
)

from dotenv import load_dotenv


NEW_QUESTION = 0


def start(update: Update, context: CallbackContext):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    keyboard = ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Привет! Я бот для викторин',
        reply_markup=keyboard
    )
    return NEW_QUESTION


def handle_new_question_request(update: Update, context: CallbackContext):
    print('question')
    question = random.choice(
        list(context.bot_data.get('questions', {}).values())
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=question.get('вопрос')
    )
    context.chat_data['answer'] = question.get('ответ').split('.')[0]
    print('Вопрос:\n{}'.format(question.get('вопрос')))
    print('Ответ:\n{}'.format(question.get('ответ')))
    return NEW_QUESTION


def handle_solution_attempt(update: Update, context: CallbackContext):
    print('answer')
    answer = context.chat_data.get('answer')
    if answer:
        if update.message.text.lower() == answer.lower():
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Верно!'
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Неправильный ответ'
            )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Прежде чем отвечать, получите вопрос'
        )
    return NEW_QUESTION


def main():
    load_dotenv()
    tg_token = os.getenv('TG_TOKEN')
    redis_pass = os.getenv('REDIS_PASS')
    updater = Updater(token=tg_token)
    dispatcher = updater.dispatcher
    with open(
        os.path.join(os.path.curdir, 'questions', 'questions.json'),
        'r'
    ) as file:
        questions = json.load(file)
    dispatcher.bot_data['questions'] = questions
    db = redis.Redis(
        host='redis-19730.c279.us-central1-1.gce.cloud.redislabs.com',
        port=19730,
        password=redis_pass,
        db=0
    )
    dispatcher.bot_data['db'] = db
    print('Бот запущен')

    start_handler = CommandHandler('start', start)

    conversation = ConversationHandler(
        entry_points=[(start_handler)],
        states={
            NEW_QUESTION: [
                MessageHandler(
                    (Filters.text(['Новый вопрос']) & (~Filters.command)),
                    handle_new_question_request
                ),
                MessageHandler(
                    (Filters.text & (~Filters.text(['Новый вопрос'])) & (~Filters.command)),
                    handle_solution_attempt
                )
            ]
        },
        fallbacks=[]
    )

    dispatcher.add_handler(conversation)
    updater.start_polling()


if __name__ == '__main__':
    main()
