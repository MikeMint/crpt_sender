import re
import yaml
import telebot
import requests
import datetime
import schedule
import time
from telebot import types
from journal import logger
from functools import wraps
from threading import Thread

log = logger("main")
with open('config.yaml', 'r') as stream:
    try:
        config = yaml.safe_load(stream)
        TOKEN = config['telegram']['token']
        group_id = config['telegram']['group_id']
    except yaml.YAMLError as exc:
        log.error(exc)
        exit()


bot = telebot.TeleBot(TOKEN)

buf_user = None  # Define a global variable to store user data temporarily
global send_messages
send_messages = []
global user

def check_command_or_menu(bot):
    def decorator(func):
        @wraps(func)
        def wrapper(message):
            match message.text:
                case "/start":
                    return start(message)
                case "\U0001F4D1 Отправить новое сообщение":
                    return start(message)
                case _:
                    return func(message)
        return wrapper
    return decorator


def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, one_time_keyboard=False)
    button_send = types.KeyboardButton("\U0001F4D1 Отправить новое сообщение")
    # button_show = types.KeyboardButton("\U0001F4F0 Показать последние")
    markup.add(button_send)
    return markup

def hide_keyboard():
    markup = types.ReplyKeyboardRemove(selective=False)
    return markup


def check_and_convert_string(input_str, dict_to_check):
    # Convert input string to lowercase
    lower_input = input_str.lower()

    # Check if the lowercase input string is in the lowercase versions of dict values
    if lower_input in [val.lower() for val in dict_to_check]:
        # Modify the input string to the corresponding uppercase value
        input_str = [val for val in dict_to_check if val.lower() == lower_input][0]
        return True, input_str
    else:
        return False, None

def validate_message(message):
    buf = message.split(" ")
    # Checking if the first part contains digits and letters less than 15 symbols
    if not re.match("^[a-zA-Z0-9]{1,15}$", buf[0]):
        return False, "Неправильно введено название монеты, попробуй еще раз"
    # Checking if the second part is datetime object like %d.%m.%Y
    try:
        datetime.datetime.strptime(buf[1], '%d.%m.%Y')
    except Exception as e:
        log.error(f"Error while parsing date, {e}")
        return False, "Неправильно введена дата, попробуй еще раз"
    # Checking if the 3,4,5 parts is in dicts
    length_values = ["1Ч", "4Ч", "1Д"]
    found, buf[2] = check_and_convert_string(input_str=buf[2], dict_to_check=length_values)
    if not found:
        return False, f"Неправильно введена длительность, не попадает в {length_values}, попробуй еще раз"

    length_values = ["Bybit", "Binance"]
    found, buf[3] = check_and_convert_string(input_str=buf[3], dict_to_check=length_values)
    if not found:
        return False, f"Неправильно введена биржа, не попадает в {length_values}, попробуй еще раз"

    length_values = ["spot", "futures"]
    found, buf[4] = check_and_convert_string(input_str=buf[4], dict_to_check=length_values)
    if not found:
        return False, f"Неправильно введен тип, не попадает в {length_values}, попробуй еще раз"
    return True, " ".join(buf)

def not_in_messages(message, send_messages):
    send_messages = [send_msg for send_msg in send_messages
                     if (datetime.datetime.now() - send_msg["time"]) < datetime.timedelta(minutes=10)]

    if message.lower() not in [send_msg["message"].lower() for send_msg in send_messages]:
        return True, send_messages
    else:
        return False, send_messages


@bot.message_handler(commands=['start'])
@bot.message_handler(func=lambda message: message.text == "\U0001F4D1 Отправить новое сообщение")
def start(message):
    if message.text == "/start":
        bot.send_message(message.from_user.id, """Привет. Это бот для отправки сообщений в канал""", reply_markup=hide_keyboard())
    bot.send_message(message.from_user.id, """Напиши сообщение в формате <b>1INCH 13.03.2024 4Ч Bybit spot</b>""", parse_mode='HTML', reply_markup=hide_keyboard())
    bot.register_next_step_handler(message, check_message)


@check_command_or_menu(bot)
def check_message(message):
    buf_user = {}
    global send_messages
    print(send_messages)
    if message.from_user.username:
        buf_user["telegram_nick"] = f"@{message.from_user.username}"
    else:
        buf_user["telegram_nick"] = f"@{message.from_user.id}"
    okey, buf_user["message"] = validate_message(message.text)
    if not okey:
        bot.send_message(message.from_user.id, f"""{buf_user["message"]}""", reply_markup=hide_keyboard())
        bot.register_next_step_handler(message, check_message)
    else:
        check, send_messages = not_in_messages(buf_user["message"], send_messages)
        if check:
            bot.send_message(message.from_user.id, f"""Спасибо за сообщение!""", reply_markup=get_main_keyboard())
            bot.send_message(group_id, f"""#ЦС #{buf_user["message"]} (спасибо {buf_user["telegram_nick"]})""", parse_mode='HTML')
            send_messages.append({"time": datetime.datetime.now(), "message": buf_user["message"]})
        else:
            bot.send_message(message.from_user.id, f"""Кто-то уже отправил такое сообщение""", reply_markup=get_main_keyboard())

@check_command_or_menu(bot)
@bot.message_handler(func=lambda message: True)
def check_all_messages(message):
    buf_user = {}
    global send_messages
    print(send_messages)
    if message.from_user.username:
        buf_user["telegram_nick"] = f"@{message.from_user.username}"
    else:
        buf_user["telegram_nick"] = f"@{message.from_user.id}"
    okey, buf_user["message"] = validate_message(message.text)
    if not okey:
        bot.send_message(message.from_user.id, f"""{buf_user["message"]}""", reply_markup=hide_keyboard())
        bot.register_next_step_handler(message, check_message)
    else:
        check, send_messages = not_in_messages(buf_user["message"], send_messages)
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

def clear_users():
    global users
    log.info("Cleaning users")
    users = {}
    log.info(users)

def main():
    schedule.every().day.at("00:00").do(clear_users)
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
