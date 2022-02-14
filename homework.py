import os
import time

from pprint import pprint

import requests
import telegram

from dotenv import load_dotenv

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

    return response.json()


def check_response(response):
    if response.get('current_date'):
        return True
    elif response.get('message'):
        pprint(response.get('message'))
    return False


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    # ...

    verdict = HOMEWORK_STATUSES[homework_status]

    # ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    not_env = ''
    if not PRACTICUM_TOKEN:
        not_env = 'PRACTICUM_TOKEN'
    elif not TELEGRAM_TOKEN:
        not_env = 'TELEGRAM_TOKEN'
    elif not TELEGRAM_CHAT_ID:
        not_env = 'TELEGRAM_CHAT_ID'
    if not_env:
        raise ValueError(f'Не заполнена переменная окружения {not_env}')


def main():
    """Основная логика работы бота."""

    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 20 * 24 * 60 * 60

    # ...

    while True:
        try:
            response = get_api_answer(current_timestamp)
            if check_response(response):
                if response.get('homeworks'):
                    homework, *_ = response.get('homeworks')
                    send_message(bot, parse_status(homework))
            else:
                print('ошибка')

            current_timestamp = int(response.get('current_date'))
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
