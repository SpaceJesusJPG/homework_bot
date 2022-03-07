import requests
import os
import time
import logging
import sys
from types import CodeType
from dotenv import load_dotenv
from telegram import Bot

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
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправляем сообщение в телеграмм со статусом работы."""
    chat_id = TELEGRAM_CHAT_ID
    bot.send_message(chat_id, message)
    logger.info('Сообщение отправлено')


def get_api_answer(current_timestamp):
    """Получаем ответ от сервера API в формате JSON."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == 200:
        response = response
        return response.json()
    else:
        logger.error('Эндпоинт недоступен')
        raise CodeType('Неожиданные ответ от сервера')


def check_response(response):
    """Проверяем ответ от сервера API на корректность."""
    if type(response) is dict:
        if 'homeworks' in response:
            homeworks = response.get('homeworks')
            if len(homeworks) == 0:
                logger.debug('В ответе отсутсвуют новые статусы')
            if type(homeworks) is list:
                return homeworks
            else:
                raise TypeError(
                    'Ответ от API под ключем "homeworks" пришел '
                    'в неожиданном типе'
                )
        else:
            logger.error('Ожидаемые ключи в ответе API отсутствуют')
            raise KeyError('Ответ API не содержит ключа "homeworks"')
    else:
        raise TypeError('Ответ API вернул неожиданные тип данных')


def parse_status(homework):
    """Обрабатываем ответ от сервера API."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем наличие всех необходимых токенов для работы бота."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID is not None:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            if check_tokens() is True:
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)
                current_timestamp = response.get('current_date')
                time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            logger.critical('Отсутствуют обязательные переменные окружения')


if __name__ == '__main__':
    main()
