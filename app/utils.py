import re
import datetime
from journal import logger

class Utils():
    def __init__(self):
        self.description = "Utils functions"
        self.log = logger("utils")

    def check_and_convert_string(self, input_str, dict_to_check):
        # Convert input string to lowercase
        lower_input = input_str.lower()

        # Check if the lowercase input string is in the lowercase versions of dict values
        if lower_input in [val.lower() for val in dict_to_check]:
            # Modify the input string to the corresponding uppercase value
            input_str = [val for val in dict_to_check if val.lower() == lower_input][0]
            return True, input_str
        else:
            return False, None

    def parse_date(self, date_string):
        date_formats = ['%d.%m.%Y', '%d.%m.%y', '%d/%m/%Y', '%d/%m/%y']
        for date_format in date_formats:
            try:
                datetime.datetime.strptime(date_string, date_format)
                return datetime.datetime.strptime(date_string, date_format).strftime('%d.%m.%Y')
            except ValueError:
                continue
        raise ValueError("Invalid date format")

    def validate_message(self,message):
        buf = message.split(" ")
        if len(buf) !=5:
            return False, "Неправильный формат сообщения, попробуй еще раз"
        # Checking if the first part contains digits and letters less than 15 symbols
        if not re.match("^[a-zA-Z0-9]{1,15}$", buf[0]):
            return False, "Неправильно введено название монеты, попробуй еще раз"
        # Checking if the second part is datetime object like %d.%m.%Y
        try:
            buf[1] = self.parse_date(buf[1])
        except ValueError as e:
            self.log.error(e)
            return False, f"Неправильно введена дата, попробуй еще раз"
        # Checking if the 3,4,5 parts is in dicts
        length_values = ["1Ч", "4Ч", "1Д"]
        found, buf[2] = self.check_and_convert_string(input_str=buf[2], dict_to_check=length_values)
        if not found:
            return False, f"Неправильно введена длительность, не попадает в {length_values}, попробуй еще раз"

        length_values = ["Bybit", "Binance"]
        found, buf[3] = self.check_and_convert_string(input_str=buf[3], dict_to_check=length_values)
        if not found:
            return False, f"Неправильно введена биржа, не попадает в {length_values}, попробуй еще раз"

        length_values = ["spot", "futures"]
        found, buf[4] = self.check_and_convert_string(input_str=buf[4], dict_to_check=length_values)
        if not found:
            return False, f"Неправильно введен тип, не попадает в {length_values}, попробуй еще раз"
        return True, " ".join(buf)

    def not_in_messages(self, message, send_messages):
        send_messages = [send_msg for send_msg in send_messages
                         if (datetime.datetime.now() - send_msg["time"]) < datetime.timedelta(minutes=10)]

        if message.lower() not in [send_msg["message"].lower() for send_msg in send_messages]:
            return True, send_messages
        else:
            return False, send_messages