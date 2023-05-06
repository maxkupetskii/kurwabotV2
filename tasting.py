from dataclasses import dataclass, field
from telegram import User, InlineKeyboardButton, InlineKeyboardMarkup
import random
from strings import Strings
from actions import Action


@dataclass
class Tasting:
    current_message_id: int | None
    people: int = 0
    users: dict[int, User] = field(default_factory=lambda: {})
    initiated_user: User | None = None
    shuffled_ids: list[int] = field(default_factory=list)

    def clear(self):
        self.current_message_id = None
        self.people = 0
        self.users.clear()

    def add(self, user: User):
        if user.id not in self.users.keys():
            self.users[user.id] = user

    def remove(self, user: User):
        if user.id in self.users.keys():
            del self.users[user.id]

    def generate_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(Strings.KEYBOARD_TITLE, callback_data=Action.ROLL.value)],
            [
                InlineKeyboardButton(Strings.KEYBOARD_MINUS, callback_data=Action.MINUS.value),
                InlineKeyboardButton(Strings.KEYBOARD_PEOPLE.format(self.people), callback_data=Action.NUM.value),
                InlineKeyboardButton(Strings.KEYBOARD_PLUS, callback_data=Action.PLUS.value)
            ],
            [InlineKeyboardButton(Strings.KEYBOARD_ADD, callback_data=Action.ADD_ME.value)]
        ]
        if len(self.users) > 0:
            for user_id, user in self.users.items():
                # use last_name if username is not present
                last = f'(@{user.username})' if user.username else user.last_name
                single_user = [
                    InlineKeyboardButton(f'{user.first_name} {last}', callback_data=Action.NAME.value),
                    InlineKeyboardButton(Strings.KEYBOARD_REMOVE,
                                         callback_data=f'{Action.REMOVE_ME.value} id:{user_id}'),
                ]
                keyboard.append(single_user)
        return InlineKeyboardMarkup(keyboard)

    def roll(self, initiated_user):
        self.initiated_user = initiated_user
        all_ids = list(self.users.keys())
        random.shuffle(all_ids)
        self.shuffled_ids = all_ids

    def winners_message(self) -> str:
        def get_user_info(num: int, user_id: int) -> str:
            user = self.users.get(user_id)
            user_string = f'{num + 1}) {user.full_name}'
            if user.username:
                user_string += f' (@{user.username})'
            user_string += "\n"
            return user_string

        winners = f'{Strings.TITLE}\n\n'
        winners += f'{Strings.WINNERS}\n'
        for counter, shuffle_id in enumerate(self.shuffled_ids):
            if counter < self.people:
                winners += get_user_info(counter, shuffle_id)
            elif counter == self.people:
                winners += f'{Strings.WAITING_LIST}\n'
                winners += get_user_info(counter, shuffle_id)
            else:
                winners += get_user_info(counter, shuffle_id)
        return winners
