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
            "battle_against": "",
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
    if user_dict["status"]["in_battle"] and user_dict["status"]["battle_against"]:  # Only if active battle
        return True
    else:  # Both being waiting for your friend to join or not hosting any battle will return False
        return False


def host_battle(bot, update):  # Callback for /battle and host_battle_handler
    host_id = str(update.message.from_user.id)
    battle_path = "Battles/" + host_id + ".json"
    host_path = "Users/" + host_id + ".json"
    if not has_profile(user_id=host_id):  # Makes sure user has profile
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
        with open(host_path, 'r+') as infile:
            user_dict = json.load(infile)
            user_dict["status"]["in_battle"] = host_id
        with open(host_path, 'w+') as outfile:
            json.dump(user_dict, outfile)
        bot.sendMessage(chat_id=update.message.chat_id, text='Done! Tell your friend to send "/join '
                                                             + host_id + '" to join the battle!')


def join_battle(bot, update, args: list):  # Callback for /join and join_battle_handler
    guest_id = str(update.message.from_user.id)
    guest_path = "Users/" + guest_id + ".json"
    host_id = " ".join(args)
    host_path = "Users/" + host_id + ".json"
    battle_path = "Battles/" + host_id + ".json"
    if not has_profile(user_id=guest_id):  # Makes sure user has user file
        create_profile(user_id=guest_id, username=update.message.from_user.username)
    if not args:  # User did not provide host_id as args
        bot.sendMessage(chat_id=update.message.chat_id, text='You must add the number after "/join "!')
    elif not os.path.isfile(battle_path):  # User provided wrong or non-existent host_id
        bot.sendMessage(chat_id=update.message.chat_id, text='That user is not ready to battle!')
    elif host_id == guest_id:  # User provided their own user_id
        bot.sendMessage(chat_id=update.message.chat_id, text='You cannot battle yourself!')
    elif is_in_battle(user_id=guest_id):  # User provided host_id but user is in battle
        bot.sendMessage(chat_id=update.message.chat_id, text='You are already in battle!')
    elif is_in_battle(user_id=host_id):  # User provided host_id but host is in battle
        bot.sendMessage(chat_id=update.message.chat_id, text='That user is already in battle!')
    else:  # User provided host_id and is not in active battle
        battle_dict = {
            "host": host_id,
            "guest": guest_id,
            "host_active_pokemon": "",
            "guest_active_pokemon": "",
            "turn": 0
        }
        with open(battle_path, "w+") as outfile:  # We overwrite the battle file with the new data
            json.dump(battle_dict, outfile)
        with open(host_path, "r") as infile:  # We open the host's user file
            host_dict = json.load(infile)
        host_dict["status"]["battle_against"] = guest_id  # We set the guest_id as the host's foe
        with open(host_path, "w") as outfile:  # We overwrite the host's user file
            json.dump(host_dict, outfile)
        with open(guest_path, "r") as infile:  # We now open the guest's user file
            guest_dict = json.load(infile)
        guest_dict["status"]["battle_against"] = host_id  # We set the host_id as the guest's foe
        with open(guest_path, "w") as outfile:  # We overwrite the guest's user file
            json.dump(guest_dict, outfile)
        bot.sendMessage(chat_id=update.message.chat_id, text='Successfully joined the battle! Send out your Pokémon by '
                                                             'sending "/go" followed by a space and the name of the '
                                                             'Pokémon you want to choose!')


def cancel_battle(user_id):  # TODO: Should add 1 loss if aborts when already in battle, nothing if waiting
    pass


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
    user_path = "Users/" + user_id + ".json"
    with open(user_path, "r") as infile:
        user_dict = json.load(infile)
    battle_path = "Battles/" + user_dict["status"]["in_battle"] + ".json"
    with open(battle_path, "r") as infile:
        battle_dict = json.load(infile)
    if user_is_host(user_id) and battle_dict["host_active_pokemon"]:
        return True
    elif (not user_is_host(user_id)) and battle_dict["guest_active_pokemon"]:
        return True
    else:
        return False


def end_battle(winner_id, battle_path):  # TODO: Delete files and halve money of loser after finishing
    winner_path = "Users/" + str(winner_id) + ".json"
    with open(winner_path, 'r+') as infile:
        winner_dict = json.load(infile)
    loser_id = winner_dict["status"]["battle_against"]
    loser_path = "Users/" + str(loser_id) + ".json"
    os.remove(battle_path)
    winner_dict["status"]["in_battle"] = ""
    winner_dict["status"]["battle_against"] = ""
    winner_dict["status"]["wins"] = +1
    with open(winner_path, 'w+') as outfile:
        json.dump(winner_dict, outfile)
    with open(loser_path, 'r+') as infile:
        loser_dict = json.load(infile)
    loser_dict["status"]["in_battle"] = ""
    loser_dict["status"]["battle_against"] = ""
    loser_dict["status"]["losses"] = +1


def send_pokemon(bot, update, args: list):  # Callback for /go and send_pokemon_handler
    pokemon = " ".join(args)
    user_id = str(update.message.from_user.id)
    if not has_profile(user_id=user_id):  # Makes sure user has user file
        create_profile(user_id=user_id, username=update.message.from_user.username)
    if not is_in_battle(user_id):
        bot.sendMessage(chat_id=update.message.chat_id, text='You are not in battle!')
    elif not pokemon:  # User sent no arguments
        bot.sendMessage(chat_id=update.message.chat_id, text='You have to write a name after "/go "!'
                                                             '(e.g.: "/go Bulbasaur)')
    elif pokemon_out(user_id):  # "is_in_battle" being True also made sure user has a "battle_against"
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

join_battle_handler = CommandHandler('join', join_battle, pass_args=True)
dispatcher.add_handler(join_battle_handler)

send_pokemon_handler = CommandHandler('go', send_pokemon, pass_args=True)
dispatcher.add_handler(send_pokemon_handler)


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
