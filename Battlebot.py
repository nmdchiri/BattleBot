import random
import logging
import json
import os
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler

updater = Updater(token='183271930:AAGYn-3WiGIQU50i9uH99hRhOQQBQMfH9Wc')
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# TODO: JESUS CHRIST THIS CODE IS A MESS, REORGANISE EVERYTHING

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


# ================================ Profile handling


def has_profile(user_id):
    user_path = "Users/" + user_id + ".json"
    if os.path.isfile(user_path):
        return True
    else:
        return False


def create_profile(user_id: str, username=""):  # Also may work as a reset
    user_path = "Users/" + str(user_id) + ".json"
    player_dict = {
        "user_id": user_id,
        "status": {
            "username": username,
            "wins": 0,
            "losses": 0,
            "money": 5000,
            "in_battle": "",
        },
        "inventory": [],
        "party": []
    }
    with open(user_path, "w") as outfile:  # 'w' to create file if it doesn't exist
        json.dump(player_dict, outfile)


def start(bot, update):  # Callback for /start
    user_id = str(update.message.from_user.id)
    username = str(update.message.from_user.username)
    if not has_profile(user_id=user_id):  # Only creates file IF there is NO file already
        create_profile(user_id=user_id, username=username)
    bot.sendMessage(chat_id=update.message.chat_id, text='Hello! Send "/help" to get a list of commands!')


def set_username(bot, update, args):  # Callback for /username
    user_id = str(update.message.from_user.id)
    user_path = "Users/" + user_id + ".json"
    custom_username = ' '.join(args)  # Makes argument list into a single string
    if has_profile(user_id=user_id):  # Checks if user has profile file already
        with open(user_path, 'r+') as outfile:  # If so, opens file and only edits username
            player_dict = json.load(outfile)
            player_dict["status"]["username"] = custom_username
            json.dump(player_dict, outfile)  # Is this necessary?
    else:
        create_profile(user_id=user_id, username=custom_username)  # Otherwise, creates profile with custom username
    bot.sendMessage(chat_id=update.message.chat_id, text='Username set to "' + custom_username + '"!')


# ================================ Battle hosting and joining

def is_in_battle(user_id: str):  # Checks if user is in active battle
    user_path = "Users/" + str(user_id) + ".json"
    with open(user_path, 'r') as infile:
        user_dict = json.load(infile)
    if not user_dict["status"]["in_battle"]:
        return False
    else:
        return True

    # battle_path = "Battles/" + host_id + ".json"  # TODO: Delete this code when sure it isn't needed
    # if os.path.isfile(battle_path):  # TODO: Check if two files agree, else delete guest
    #     with open(battle_path, 'r') as infile:
    #         battle_dict = json.load(infile)
    #         if battle_dict["guest"]:  # If guest is not null, then user must be battling
    #             return True
    #         else:  # If guest is still empty, user must be waiting for friend to join
    #             return False
    # else:  # If file does not exist, then user has not hosted or joined battle
    #     return False


def host_battle(bot, update):  # Callback for /battle and host_battle_handler
    host_id = str(update.message.from_user.id)
    battle_path = "Battles/" + host_id + ".json"
    host_path = "Users/" + host_id + ".json"
    if not has_profile(user_id=host_id):
        create_profile(user_id=host_id, username=update.message.from_user.username)
    battle_dict = {
        "host": host_id,
        "guest": ""
    }
    if is_in_battle(user_id=host_id):  # If user is in active battle
        bot.sendMessage(chat_id=update.message.chat_id, text='You are already in battle!')
    else:  # If user is NOT in active battle
        with open(battle_path, 'w+') as outfile:
            json.dump(battle_dict, outfile)
        with open(host_path, 'r+') as outfile:
            user_dict = json.load(outfile)
            user_dict["in_battle"] = host_id
        bot.sendMessage(chat_id=update.message.chat_id, text='Done! Tell your friend to send "/join '
                                                             + host_id + '" to join the battle!')


def join_battle(bot, update, args: list):  # Callback for /join and join_battle_handler
    guest_id = str(update.message.from_user.id)
    battle_path = "Battles/" + " ".join(args) + ".json"
    host_path = "Users/" + " ".join(args) + ".json"
    if not has_profile(user_id=guest_id):
        create_profile(user_id=guest_id, username=update.message.from_user.username)
    guest_battle_path = "Battles/" + str(guest_id) + ".json"
    if not args:  # User did not provide host_id as args
        bot.sendMessage(chat_id=update.message.chat_id, text='You must add the number after "/join "!')
    elif is_in_battle(guest_battle_path):  # User provided host_id but user is in battle
        bot.sendMessage(chat_id=update.message.chat_id, text='You are already in battle!')
    elif is_in_battle(host_path):  # User provided host_id but host is in battle
        bot.sendMessage(chat_id=update.message.chat_id, text='That user is already in battle!')
    elif not os.path.isfile(battle_path):  # User provided wrong host_id
        bot.sendMessage(chat_id=update.message.chat_id, text='That user is not ready to battle!')
    else:  # User provided host_id and is not in battle
        host_id = " ".join(args)
        host_battle_path = "Battles/" + str(host_id) + ".json"
        battle_dict = {
            "host": host_id,
            "guest": guest_id,
            "host_active_pokemon": "",
            "guest_active_pokemon": ""
        }
        with open(guest_battle_path, "w+") as outfile:
            json.dump(battle_dict, outfile)
        with open(host_battle_path, "w+") as outfile:
            json.dump(battle_dict, outfile)
        bot.sendMessage(chat_id=update.message.chat_id, text='Successfully joined the battle! Send out your Pokémon by '
                                                             'sending "/go" followed by a space and the name of the '
                                                             'Pokémon you want to choose!')


# ================================ Battle processing


def user_is_host(user_id):
    battle_path = "Battles/" + user_id + ".json"
    with open(battle_path, "r") as infile:
        user_battle_dict = json.load(infile)
    if user_battle_dict["host"] == user_id:
        return True
    else:
        return False


def pokemon_out(user_id):
    battle_path = "Battles/" + user_id + ".json"
    with open(battle_path, "r") as infile:
        user_battle_dict = json.load(infile)
    host_battle_path = "Battles/" + user_battle_dict["host"] + ".json"  # This only matters if user is guest
    with open(host_battle_path, "r") as infile:
        host_battle_dict = json.load(infile)  # Now we can be sure this is the host battle file
    if user_is_host(user_id) and host_battle_dict["host_active_pokemon"]:
        return True
    elif (not user_is_host(user_id)) and host_battle_dict["guest_active_pokemon"]:
        return True
    else:
        return False


# def end_battle(user_id):
#     pass  # TODO: Delete files and halve money of loser after finishing


def send_pokemon(bot, update, args: list):  # Callback for /go and send_pokemon_handler
    pokemon = " ".join(args)
    user_id = str(update.message.from_user.id)
    battle_path = "Battles/" + user_id + ".json"
    if not is_in_battle(battle_path):
        bot.sendMessage(chat_id=update.message.chat_id, text='You are not in battle!')
    elif not pokemon:  # User sent no arguments
        bot.sendMessage(chat_id=update.message.chat_id, text='You have to write a name after "/go "!'
                                                             '(e.g.: "/go Bulbasaur)')
    elif pokemon_out(user_id):  # "is_in_battle" being True also made sure user has a battle file
        bot.sendMessage(chat_id=update.message.chat_id, text='You already have a Pokémon out!')
    else:  # User is in battle and has NO Pokémon out
        bot.sendMessage(chat_id=update.message.chat_id, text='Go, {}!').format(pokemon)


# ================================ Damage calculators


def check_stab(attack_type, attacker_type):
    if attack_type == attacker_type:
        return 1.5
    else:
        return 1


# def check_type_adv(att_type, def_type):
#     return 1  # TODO: Add types


def modifier_calc(stab, type_adv, critical_stage, other_bonus):
    # STAB = check_stab()  # TODO: ADD THIS and remove STAB from required arguments
    # type_adv = check_type_adv()  # TODO: ditto ^
    if critical_stage == 0:
        critical_rate = 16
    elif critical_stage == 1:
        critical_rate = 8
    elif critical_stage == 2:
        critical_rate = 2
    else:
        critical_rate = 1
    if random.randint(1, critical_rate) == 1:  # higher rate is worse (denominator)
        critical_bonus = 1.5
    else:
        critical_bonus = 1
    pre_random = stab * type_adv * critical_bonus * other_bonus  # get subtotal before randomising to include "1"
    return random.uniform(0.85 * pre_random, 1 * pre_random)  # this guarantees sometimes it will get max


def damage(level, attack, defense, base_atk, modifier):  # TODO: Add modifier function
    return (((2 * level + 10) / 250.0) * (attack / defense) * base_atk + 2) * modifier  # TODO: round down


# ================================ Handlers


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

username_handler = CommandHandler('username', set_username, pass_args=True)
dispatcher.add_handler(username_handler)

host_battle_handler = CommandHandler('battle', host_battle)
dispatcher.add_handler(host_battle_handler)

join_battle_handler = CommandHandler('battle', join_battle)
dispatcher.add_handler(join_battle_handler)


def echo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=update.message.text)


echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()


def inline_caps(bot, update):
    query = update.inline_query.query
    if not query:
        return
    results = list()
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper()),
            description='This is a description'
        )
    )
    bot.answerInlineQuery(update.inline_query.id, results)


inline_caps_handler = InlineQueryHandler(inline_caps)
dispatcher.add_handler(inline_caps_handler)
