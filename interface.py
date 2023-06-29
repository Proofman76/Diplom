# импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import VkTools

from data_store import DataStore
from data_store import engine
# отправка сообщений


class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.offset = 50
        self.data_store = DataStore(engine)

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )

# обработка событий / получение сообщений

    def event_handler(self):
        for event in self.longpoll.listen():

            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.params['relation'] = 6  # в активном поиске
                    self.event_greeting(event.user_id)
                    if not self.params['city']:
                        self.event_city_input(event.user_id)
                    elif not self.params['sex']:
                        self.event_sex_input(event.user_id)
                    elif not self.params['year']:
                        self.event_year_input(event.user_id)

                elif event.text.lower() == 'поиск' or event.text.lower() == 'далее':
                    '''Логика для поиска анкет'''
                    self.message_send(
                        event.user_id, 'Идет поиск...')
                    if self.worksheets:
                        worksheet = self.worksheets.pop()
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                    else:
                        self.worksheets = self.vk_tools.search_worksheet(self.params, self.offset)
                        worksheet = self.worksheets.pop()
                        self.offset += 50

                    '''првоерка анкеты в бд в соотвествие с event.user_id'''
                    while self.data_store.check_user(event.user_id, worksheet["id"]) is True:
                        worksheet = self.worksheets.pop()

                    '''добавление анкеты в бд в соотвествие с event.user_id'''
                    if self.data_store.check_user(event.user_id, worksheet["id"]) is False:
                        self.data_store.add_user(event.user_id, worksheet["id"])

                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'

                        self.message_send(
                            event.user_id,
                            f'Имя: {worksheet["name"]}. Страница: vk.com/id{worksheet["id"]}',
                            attachment=photo_string
                        )

                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, 'До новых встреч')
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда')

    def event_greeting(self, user_id):
        self.message_send(user_id, f'Привет, {self.params["name"]}!')

    def event_city_input(self, user_id):
        self.message_send(user_id, 'Введите название вашего города проживания:')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.params['city'] = event.text
                break
        if self.params['city']:
            self.message_send(user_id, 'ОК')

    def event_sex_input(self, user_id):
        self.message_send(user_id, 'Введите ваш пол м - мужской, ж - женский:')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.params['sex'] = 2 if event.text == 'м' else 1
                break
        if self.params['sex']:
            self.message_send(user_id, 'ОК')

    def event_year_input(self, user_id):
        self.message_send(user_id, 'Введите ваш возраст:')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.params['year'] = event.text
                break
        if self.params['year']:
            self.message_send(user_id, 'ОК')


if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()