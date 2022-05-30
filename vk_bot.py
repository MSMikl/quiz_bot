import json
import os
import random

import vk_api as vk
import redis

from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType


def start(event, vk_api):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Мой счет')
    vk_api.messages.send(
        user_id=event.user_id,
        message='Хотите, задам вам вопрос?',
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def ask_question(event, vk_api, question):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Сдаться')
    keyboard.add_button('Мой счет')
    vk_api.messages.send(
        user_id=event.user_id,
        message=question,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def answer_attempt(event, vk_api, answer):
    if event.text.lower() == answer.lower():
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('Новый вопрос')
        keyboard.add_button('Мой счет')
        vk_api.messages.send(
            user_id=event.user_id,
            message='Верно!',
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )
        return True
    else:
        keyboard = VkKeyboard()
        keyboard.add_button('Сдаться')
        keyboard.add_button('Мой счет')
        vk_api.messages.send(
            user_id=event.user_id,
            message='Пока неверно, попробуй еще',
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )


def retire(event, vk_api, answer):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Мой счет')
    vk_api.messages.send(
        user_id=event.user_id,
        message='Правильный ответ:\n{}'.format(answer),
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def fetch_count(event, vk_api, count):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Сдаться')
    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Мой счет')
    vk_api.messages.send(
        user_id=event.user_id,
        message='Ваш счет: {} баллов'.format(count),
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )


def main():
    load_dotenv()
    vk_token = os.getenv('VK_TOKEN')
    redis_pass = os.getenv('REDIS_PASS')
    redis_host = os.getenv('REDIS_HOST')
    redis_port = int(os.getenv('REDIS_PORT'))
    with open(
        os.path.join(os.path.curdir, 'questions', 'questions.json'),
        'r'
    ) as file:
        questions = json.load(file)

    # База Redis с ответом на текущий вопрос
    answer_db = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        db=0
    )

    # База Redis со счетом
    count_db = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        db=1
    )
    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Начать':
                start(event, vk_api)
            elif event.text == 'Новый вопрос':
                question = random.choice(list(questions.values()))
                answer_db.set(
                    event.user_id,
                    json.dumps(question.get('ответ'))
                )
                ask_question(event, vk_api, question.get('вопрос'))
            elif event.text == 'Сдаться':
                try:
                    answer = answer_db.get(event.user_id)
                except redis.exceptions.ResponseError:
                    continue
                retire(event, vk_api, json.loads(answer))
            elif event.text == 'Мой счет':
                try:
                    count = count_db.get(event.user_id)
                except redis.exceptions.ResponseError:
                    count = 0
                fetch_count(event, vk_api, count)
            elif event.text:
                try:
                    answer = answer_db.get(event.user_id)
                except redis.exceptions.ResponseError:
                    continue
                if answer_attempt(event, vk_api, json.loads(answer)):
                    try:
                        count = count_db.get(event.user_id)
                    except redis.exceptions.ResponseError:
                        count = 0
                    count_db.set(event.user_id, count + 1)


if __name__ == '__main__':
    main()
