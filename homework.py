import logging
import os
import sys
import time

import requests
import telegram

from dotenv import load_dotenv

logger = logging.getLogger()
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def send_message(bot, message):
    """Отправка сообщения ботом."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Запрос к API, проверка статуса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            raise Exception(response.status_code)
        return response.json()

    except Exception as error:
        raise Exception(
            f'Эндпоинт {ENDPOINT} недоступен. Код ответа API: {error}'
        )


def check_response(response):
    """Проверка ответа от API."""
    if 'homeworks' not in response:
        raise TypeError('Ответ не содержит ключ homeworks')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Неправильный тип данных homeworks')
    if homeworks:
        homework, *_ = homeworks
        if not isinstance(homework, dict):
            raise TypeError('Неправильный тип данных homework')

    return homeworks


def parse_status(homework):
    """Извлекает статус этой работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except Exception:
        raise KeyError(f'Неизвестный статус работы {homework_status}')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка заполнения переменных окружения."""
    if not PRACTICUM_TOKEN:
        return False
    elif not TELEGRAM_TOKEN:
        return False
    elif not TELEGRAM_CHAT_ID:
        return False
    return True


def main():
    """Основная логика работы бота."""
    cache_message = ''
    if not check_tokens():
        logger.critical(
            'Не заполнены переменные окружения. Работа программы остановлена'
        )
        raise ValueError(
            'Не заполнены переменные окружения. Работа программы остановлена'
        )

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    logger.debug(f'Временная метка в формате Unix time: {current_timestamp}')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            logger.debug('Ответ API прошел проверку на корректность')
            if homeworks:
                homework, *_ = homeworks
                message = parse_status(homework)
                send_message(bot, message)
                current_timestamp = int(response.get('current_date'))
                logger.info(f'Бот отправил сообщение: {message}')
                cache_message = message
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if cache_message != message:
                send_message(bot, message)
                logger.info(f'Бот отправил сообщение: {message}')
                cache_message = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
