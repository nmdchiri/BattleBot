import random
import logging
import json
import os
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

updater = Updater(token='183271930:AAGYn-3WiGIQU50i9uH99hRhOQQBQMfH9Wc')
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# ================================ Model dictionaries

"""
pokemon_dict = {
    "id": 1,
    "name": "bulbasaur",
    "held_items": {},
    "abilities": "",
    "moves": []
    "types": [
        {
            "slot": 2,
            "type": {
                "url": "https://pokeapi.co/api/v2/type/4/",
                "name": "poison"
                }
            },
        {
            "slot": 1,
            "type": {
                "url": "https://pokeapi.co/api/v2/type/12/",
                "name": "grass"
                }
            }
        ]
"""

status_dict = {
    "username": "",
    "wins": 0,
    "losses": 0,
    "money": 5000
}


def create_player(user_id, username):
    player_dict = {
        "user_id": user_id,
        "status": {
            "username": username,
            "wins": 0,
            "losses": 0,
            "money": 5000
        },
        "inventory": [],
        "party": []
    }
    return player_dict


# ================================ Profile handling

def create_profile(user_id, username):
    with open("Users/" + str(user_id)+'.json','w') as outfile:
        json.dump(create_player(user_id, username), outfile)


# ================================ Damage calculators


def check_stab(attack_type, attacker_type):
    if attack_type == attacker_type:
        return 1.5
    else:
        return 1


def checktypeadv(att_type, def_type):
    return 1  # TODO: Add types


def modifiercalc(STAB, typeadv, critical_stage, other_bonus):
    # STAB = check_stab()  # TODO: ADD THIS and remove STAB from required arguments
    # typeadv = checktypeadv  # TODO: ditto ^
    if critical_stage == 0:
        critical_rate = 16
    elif critical_stage == 1:
        critical_rate = 8
    elif critical_stage == 2:
        critical_rate = 2
    else:
        critical_rate = 1
    if random.randint(1, critical_rate) == 1:  # higher rate is worse (denominator)
        criticalbonus = 1.5
    else:
        criticalbonus = 1
    prerandom = STAB * typeadv * criticalbonus * other_bonus  # get subtotal before randomising to include "1"
    return random.uniform(0.85 * prerandom, 1 * prerandom)  # this guarantees sometimes it will get max


def damage(level, attack, defense, baseatk, modifier):
    return (((2 * level + 10) / 250.0) * (attack / defense) * baseatk + 2) * modifier  # TODO: round down


"""
#how to make a file
test_file = open("testfile.txt", "w+")

test_file.write("Testing if this works")
test_file.close()
"""


# ================================ Handlers


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Hello! Send /help to get a list of commands!")
    create_profile(update.message.from_user.id, update.message.from_user.username)


def set_username(bot, update, args):
    username = ' '.join(args)
    bot.sendMessage(chat_id=update.message.chat_id, text='Username set to "' + username + '"!')
    user_id = update.message.from_user.id
    file_path = "Users/" + str(user_id)
    if os.path.isfile(file_path):
        player_dict = json.load(file_path)
        player_dict["status"]["username"] = username
        json.dump(player_dict, file_path)
    else:
        create_profile(user_id, username)  # TODO: check if already has profile


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

username_handler = CommandHandler('username', set_username, pass_args=True)
dispatcher.add_handler(username_handler)


def echo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=update.message.text)


echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()
