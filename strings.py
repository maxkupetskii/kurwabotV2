from dataclasses import dataclass


@dataclass(frozen=True)
class Strings:
    TITLE = '🍷Wine tasting roulette!🍷'
    RESTRICTED = 'юзер {} не шмог'
    KEYBOARD_TITLE = 'Choose winners!🎲'
    KEYBOARD_MINUS = '(-)'
    KEYBOARD_PEOPLE = '{}'
    KEYBOARD_PLUS = '(+)'
    KEYBOARD_ADD = 'Add me!🍇'
    KEYBOARD_REMOVE = '⛔'
    REPLY_DELETE = 'Стираём всех!'
    REPLY_CANCEL = 'Не'
    REPLY_TITLE_DELETE = 'Дега уже создана, херим?'
    REPLY_0_PEOPLE = 'Мест 0, тыкай плюсики!'
    REPLY_0_USERS = 'Людей нема, надо ждать!'
    REPLY_START = 'Стартуём!'
    REPLY_TITLE_ROLL = 'Вращаем барабан?'
    WINNERS = 'The winners are:'
    WAITING_LIST = 'Waiting list:'
