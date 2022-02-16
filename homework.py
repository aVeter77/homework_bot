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

    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    return response


def check_response(response):

    if response.get('current_date'):
        return True
    return False


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    # ...

    verdict = HOMEWORK_STATUSES[homework_status]

    # ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка заполнения переменных окружения."""
    if not PRACTICUM_TOKEN:
        return 'PRACTICUM_TOKEN'
    elif not TELEGRAM_TOKEN:
        return 'TELEGRAM_TOKEN'
    elif not TELEGRAM_CHAT_ID:
        return 'TELEGRAM_CHAT_ID'
    return False


def main():
    """Основная логика работы бота."""
    cache_message = ''
    check_token = check_tokens()
    if check_token:
        logger.critical(f'Не заполнена переменная окружения {check_token}')
        logger.critical('Работа программы остановлена')
        raise ValueError(f'Не заполнена переменная окружения {check_token}')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 25 * 24 * 60 * 60

    logger.debug(f'Временная метка в формате Unix time: {current_timestamp}')

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if isinstance(response, requests.models.Response):
                message = (
                    f'Сбой в работе программы: Эндпоинт {ENDPOINT} '
                    f'недоступен. Код ответа API: {response.status_code}'
                )
                logger.error(message)
                if cache_message != message:
                    send_message(bot, message)
                    logger.info(f'Бот отправил сообщение: {message}')
                    cache_message = message
            else:
                if check_response(response):
                    logger.debug('Ответ API прошел проверку на корректность')
                    if response.get('homeworks'):
                        homework, *_ = response.get('homeworks')
                        message = parse_status(homework)
                        send_message(bot, message)
                        current_timestamp = int(response.get('current_date'))
                        logger.info(f'Бот отправил сообщение: {message}')
                        cache_message = message
                else:

                    logger.error(
                        'Ответ API не прошел проверку на корректность'
                    )
                    if cache_message != message:
                        send_message(
                            bot, 'Ответ API не прошел проверку на корректность'
                        )
                        logger.info(
                            'Бот отправил сообщение: Ответ API не прошел '
                            'проверку на корректность'
                        )
                        cache_message = message

            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            print(message)
            # ...
            time.sleep(RETRY_TIME)
        # else:
        # ...


if __name__ == '__main__':
    main()
