import re
import yaml
import telebot
import requests
import datetime
import schedule
import time
from utils import Utils
from journal import logger
from functools import wraps
from threading import Thread
from markups import get_main_keyboard, hide_keyboard, reply_keyboard_choose, inline_keyboard_choose

log = logger("main")
with open('config_test.yaml', 'r') as stream:
    try:
        config = yaml.safe_load(stream)
        TOKEN = config['telegram']['token']
        group_id = config['telegram']['group_id']
    except yaml.YAMLError as exc:
        log.error(exc)
        exit()


bot = telebot.TeleBot(TOKEN)
utils = Utils()
buf_user = None  # Define a global variable to store user data temporarily
global send_messages
send_messages = []
global user

def check_command_or_menu():
    def decorator(func):
        @wraps(func)
        def wrapper(message):
            match message.text:
                case "/start":
                    return start(message)
                case "\U0001F4D1 Отправить новое сообщение(текст)":
                    return start(message)
                case _:
                    return func(message)
        return wrapper
    return decorator





@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == "\U0001F4D1 Отправить новое сообщение(текст)")
def start(message):
    if message.text == "/start":
        bot.send_message(message.from_user.id, """Привет. Это бот для отправки сообщений в канал""", reply_markup=hide_keyboard())
    bot.send_message(message.from_user.id, """Напиши сообщение в формате <b>1INCH 13.03.2024 4Ч Bybit spot</b>""", parse_mode='HTML', reply_markup=hide_keyboard())
    bot.register_next_step_handler(message, check_message)


@check_command_or_menu()
def check_message(message):
    buf_user = {}
    global send_messages
    print(send_messages)
    if message.from_user.username:
        buf_user["telegram_nick"] = f"@{message.from_user.username}"
    else:
        buf_user["telegram_nick"] = f"@{message.from_user.id}"
    okey, buf_user["message"] = utils.validate_message(message.text)
    if not okey:
        bot.send_message(message.from_user.id, f"""{buf_user["message"]}""", reply_markup=hide_keyboard())
        bot.send_message(message.from_user.id, """<b>Подсказка:</b>
Формат сообщения: <b>1INCH 13.03.2024 4Ч Bybit spot</b>
<b>1INCH</b> - название монеты, максимально 15 символов
<b>13.03.2024</b> - дата в формате дд.мм.(гг)гг, дд/мм/(гг)гг
<b>4Ч</b> - Тайминг. Выбор из 1Ч, 4Ч, 1Д
<b>Bybit</b> - биржа. Выбор из Bybit, Binance
<b>spot</b> - тип. Выбор из spot, futures""",
                         parse_mode='HTML', reply_markup=hide_keyboard())
        bot.register_next_step_handler(message, check_message)
    else:
        check, send_messages = utils.not_in_messages(buf_user["message"], send_messages)
        if check:
            bot.send_message(message.from_user.id, f"""Спасибо за сообщение!""", reply_markup=get_main_keyboard())
            bot.send_message(group_id, f"""#ЦС #{buf_user["message"]} (спасибо {buf_user["telegram_nick"]})""", parse_mode='HTML')
            send_messages.append({"time": datetime.datetime.now(), "message": buf_user["message"]})
        else:
            bot.send_message(message.from_user.id, f"""Кто-то уже отправил такое сообщение""", reply_markup=get_main_keyboard())

@check_command_or_menu()
@bot.message_handler(func=lambda message: True)
def check_all_messages(message):
    buf_user = {}
    global send_messages
    print(send_messages)
    if message.from_user.username:
        buf_user["telegram_nick"] = f"@{message.from_user.username}"
    else:
        buf_user["telegram_nick"] = f"@{message.from_user.id}"
    okey, buf_user["message"] = utils.validate_message(message.text)
    if not okey:
        bot.send_message(message.from_user.id, f"""{buf_user["message"]}""", reply_markup=hide_keyboard())
        bot.send_message(message.from_user.id, """<b>Подсказка:<b>
Формат сообщения: 1INCH 13.03.2024 4Ч Bybit spot
1INCH - название монеты, максимально 15 символов
13.03.2024 - дата в формате дд.мм.гг, дд.мм.гггг, дд/мм/гг, дд/мм/гггг
4Ч - Тайминг. Выбор из 1Ч, 4Ч, 1Д
Bybit - биржа. Выбор из Bybit, Binance
spot - тип. Выбор из spot, futures""",
                         parse_mode='HTML', reply_markup=hide_keyboard())
        bot.register_next_step_handler(message, check_message)
    else:
        check, send_messages = utils.not_in_messages(buf_user["message"], send_messages)
        if check:
            bot.send_message(message.from_user.id, f"""Спасибо за сообщение!""", reply_markup=get_main_keyboard())
            bot.send_message(group_id, f"""#ЦС #{buf_user["message"]} (спасибо {buf_user["telegram_nick"]})""",
                             parse_mode='HTML')
            send_messages.append({"time": datetime.datetime.now(), "message": buf_user["message"]})
        else:
            bot.send_message(message.from_user.id, f"""Кто-то уже отправил такое сообщение""",
                             reply_markup=get_main_keyboard())

def fetch_last_message_except_one():
    token = TOKEN
    response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
    data = response.json()
    if data["ok"]:
        if data["result"]:
            latest_update = data["result"][-1]
            bot.process_new_updates([telebot.types.Update.de_json(latest_update)])



def main():
    # schedule.every().day.at("00:00").do(clear_users)
    log.info("Starting bot")
    while True:
        schedule.run_pending()
        time.sleep(1)



if __name__ == "__main__":
    log.info("Starting bot")
    fetch_last_message_except_one()
    Thread(target=main).start()
    while True:
        try:
            bot.infinity_polling(none_stop=True)
        except Exception as e:
            log.error(f"bot error, {e}")
            time.sleep(5)
