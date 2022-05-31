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


def redis_get(db, key, default=None):
    result = db.get(key)
    print(result)
    if result:
        return int(result)
    else:
        return default


def main():
    load_dotenv()
    vk_token = os.getenv('VK_TOKEN')
    redis_pass = os.getenv('REDIS_PASS')
    redis_host = os.getenv('REDIS_HOST')
    redis_port = int(os.getenv('REDIS_PORT'))
    with open(
        os.path.join(os.path.curdir, 'questions.json'),
        'r'
    ) as file:
        questions = json.load(file)

    db = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_pass,
        db=0
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
                db.set(
                    str(event.user_id) + '_answer',
                    json.dumps(question.get('ответ').replace('.', ''))
                )
                ask_question(event, vk_api, question.get('вопрос'))
            elif event.text == 'Сдаться':
                answer = db.get(str(event.user_id) + '_answer')
                if not answer:
                    continue
                retire(event, vk_api, json.loads(answer))
                db.delete(str(event.user_id) + '_answer')
            elif event.text == 'Мой счет':
                fetch_count(
                    event,
                    vk_api,
                    redis_get(db, str(event.user_id) + '_score', 0)
                )
            elif event.text:
                answer = db.get(str(event.user_id) + '_answer')
                if not answer:
                    continue
                if answer_attempt(event, vk_api, json.loads(answer)):
                    db.set(
                        str(event.user_id) + '_score',
                        redis_get(db, str(event.user_id) + '_score', 0) + 1
                    )


if __name__ == '__main__':
    main()
