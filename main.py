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
ANSWER = 1


def start(update: Update, context: CallbackContext):
    question_keyboard = [['Новый вопрос'], ['Мой счет']]
    keyboard = ReplyKeyboardMarkup(question_keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Привет! Я бот для викторин',
        reply_markup=keyboard
    )
    return NEW_QUESTION


def current_count(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Ваш текущий счет {} баллов'.format(
            context.chat_data.get('count', 0)
        )
    )


def handle_new_question_request(update: Update, context: CallbackContext):
    answer_keyboard = [['Сдаться'], ['Мой счет']]
    keyboard = ReplyKeyboardMarkup(answer_keyboard)
    question = random.choice(
        list(context.bot_data.get('questions', {}).values())
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=question.get('вопрос'),
        reply_markup=keyboard
    )
    context.chat_data['answer'] = question.get('ответ').split('.')[0]
    print('Вопрос:\n{}'.format(question.get('вопрос')))
    print('Ответ:\n{}'.format(question.get('ответ')))
    return ANSWER


def handle_solution_attempt(update: Update, context: CallbackContext):
    answer = context.chat_data.get('answer')
    if answer:
        if update.message.text.lower() == answer.lower():
            question_keyboard = [['Новый вопрос'], ['Мой счет']]
            keyboard = ReplyKeyboardMarkup(question_keyboard)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Верно!',
                reply_markup=keyboard
            )
            context.chat_data['count'] = context.chat_data.get('count', 0) + 1
            return NEW_QUESTION
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
    return ANSWER


def rejected_question(update: Update, context: CallbackContext):
    answer = context.chat_data.get('answer')
    question_keyboard = [['Новый вопрос'], ['Мой счет']]
    keyboard = ReplyKeyboardMarkup(question_keyboard)
    if answer:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Правильный ответ\n{}'.format(answer),
            reply_markup=keyboard
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
                    Filters.text(['Новый вопрос']),
                    handle_new_question_request
                ),
                MessageHandler(
                    Filters.text(['Мой счет']),
                    current_count
                )
            ],
            ANSWER: [
                MessageHandler(
                    (
                        Filters.text &
                        (~Filters.text(['Сдаться', 'Мой счет']))
                        & (~Filters.command)
                    ),
                    handle_solution_attempt
                ),
                MessageHandler(
                    Filters.text(['Мой счет']),
                    current_count
                ),
                MessageHandler(
                    (Filters.text(['Сдаться'])),
                    rejected_question
                )
            ]
        },
        fallbacks=[]
    )

    dispatcher.add_handler(conversation)
    updater.start_polling()


if __name__ == '__main__':
    main()
