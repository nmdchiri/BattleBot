import random
import logging
import os
import json
import jsonpickle

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

# ================================ Battle and profile classes


class Pokemon(object):
    def __init__(self, id):
        self.id = id
    
    nickname = ""
    name = ""
    held_items = ""
    abilities = ""
    moves = []
    types = []


class Profile(object):
    def __init__(self, user_id, username, money):
        self.user_id = user_id
        self.username = username
        self.money = money
    
    party = []
    inventory = []
    wins = 0
    losses = 0
    in_battle = ""
    battle_against = ""
    active_pokemon = ""
    command = ""  # TODO: Should be able to take an object "Move" or similar


class Battle(object):
    def __init__(self, host, guest):
        self.host = host
        self.guest = guest
    turn = 0
    
    def do_turn(self):  # TODO: Add speed checking to see who goes first, etc
        self.turn += 1
        
    def take_command(self, host_command="", guest_command=""):  # TODO: Add some kind of confirmation
        if host_command:
            self.host.command = host_command
        if guest_command:
            self.guest.command = guest_command
        if self.host.command and self.guest.command:
            do_turn()

    def end_battle(self, winner_id, loser_id):
        if winner_id == host.user_id:
            winner = host
            loser = guest
        else:
            winner = guest
            loser = host
        winner.money += loser.money - loser.money // 2
        loser.money = loser.money // 2

    def surrender(self, user_id):
        if self.host.user_id == user_id:  # If user who surrenders is host
            winner_id = self.guest.user_id  # Then guest is the winner
        else:  # If user who surrenders is not host
            winner_id = self.host.user_id  # Then host is the winner
        end_battle(winner_id=winner_id, loser_id=user_id)


# ================================ Profile handling


def get_profile(user_id):
    user_path = "Users/" + user_id + ".json"
    with open(user_path, "r") as infile:
        profile = jsonpickle.decode(infile.read())
    return profile


def get_battle(host_id):
    battle_path = "Battles/" + host_id + ".json"
    with open(battle_path, "r") as infile:
        battle = jsonpickle.decode(infile.read())
    return battle


def save_profile(user_id, profile):  # TODO: Complete this
    user_path = "Users/" + user_id + ".json"
    with open(user_path, "w") as outfile:
        outfile.write(jsonpickle.encode(profile))


def save_battle(host_id, battle):  # TODO: Complete this
    user_path = "Battles/" + host_id + ".json"
    with open(host_path, "w") as outfile:
        outfile.write(jsonpickle.encode(battle))


def get_profile_dict(user_id):  # TODO: Delete
    user_path = "Users/" + user_id + ".json"
    with open(user_path, "r") as infile:
        user_dict = json.load(infile)
    return user_dict


def get_battle_dict(host_id):
    battle_path = "Battle/" + host_id + ".json"
    with open(battle_path, "r") as infile:
        battle_dict = json.load(infile)
    return battle_dict


def has_profile(user_id):
    user_path = "Users/{}.json".format(str(user_id))
    if os.path.isfile(user_path):
        return True
    else:
        return False


def create_profile(user_id: str, username=""):  # Also may work as a reset
    user_path = "Users/{}.json".format(str(user_id))
    profile = Profile(user_id=user_id, username=username, money=5000)
    pickled_profile = jsonpickle.encode(profile)
    with open(user_path, "w") as outfile:  # 'w' to create file if it doesn't exist
        outfile.write(pickled_profile)


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
        with open(user_path, 'r+') as infile:  # If so, opens file and only edits username
            profile = jsonpickle.decode(infile.read())
        profile.username = custom_username
        with open(user_path, 'w+') as outfile:
            outfile.write(jsonpickle.encode(profile))
    else:
        create_profile(user_id=user_id, username=custom_username)  # Otherwise, creates profile with custom username
    bot.sendMessage(chat_id=update.message.chat_id, text='Username set to "' + custom_username + '"!')


# ================================ Battle hosting and joining

def is_in_battle(user_id: str):  # Checks if user is in active battle
    user_path = "Users/{}.json".format(str(user_id))
    with open(user_path, 'r') as infile:
        profile = jsonpickle.decode(infile.read())
    if profile.battle_against:  # Only if active battle
        return True
    else:  # Both being waiting for your friend to join or not hosting any battle will return False
        return False


def host_battle(bot, update):  # Callback for /battle and host_battle_handler
    host_id = str(update.message.from_user.id)
    host_path = "Users/" + host_id + ".json"
    if not has_profile(user_id=host_id):  # Makes sure user has profile
        create_profile(user_id=host_id, username=update.message.from_user.username)
    if is_in_battle(user_id=host_id):  # If user is in active battle
        bot.sendMessage(chat_id=update.message.chat_id, text='You are already in battle!')
    else:  # If user is NOT in active battle
        with open(host_path, 'r+') as infile:
            profile = jsonpickle.decode(infile.read())
            profile.in_battle = host_id
        with open(host_path, 'w+') as outfile:
            outfile.write(jsonpickle.encode(profile))
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
        with open(host_path, "r") as infile:  # We open the host's user file
            host_profile = jsonpickle.decode(infile.read())
        host_profile.battle_against = guest_id  # We set the guest_id as the host's foe
        with open(host_path, "w") as outfile:  # We overwrite the host's user file
            outfile.write(jsonpickle.encode(host_profile))
        with open(guest_path, "r") as infile:  # We now open the guest's user file
            guest_profile = jsonpickle.decode(infile.read())
        guest_profile.in_battle = host_id
        guest_profile.battle_against = host_id  # We set the host_id as the guest's foe
        with open(guest_path, "w") as outfile:  # We overwrite the guest's user file
            outfile.write(jsonpickle.encode(guest_profile))
        battle = jsonpickle.encode(Battle(host=host_profile, guest=guest_profile))
        with open(battle_path, 'w') as outfile:
            outfile.write(battle)
        bot.sendMessage(chat_id=update.message.chat_id, text='Successfully joined the battle! Send out your Pokémon by '
                                                             'sending "/go" followed by a space and the name of the '
                                                             'Pokémon you want to choose!')


def cancel_battle(user_id):  # TODO: Should add 1 loss if aborts when already in battle, nothing if waiting
    pass


# ================================ Battle processing


def user_is_host(user_id):
    user_path = "Users/" + user_id + ".json"
    with open(user_path, "r") as infile:
        user_dict = json.load(infile)
    battle_path = "Battles/" + user_dict["status"]["in_battle"] + ".json"
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
    if user_is_host(user_id=user_id) and battle_dict["host_active_pokemon"]:
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
    user_dict = get_profile_dict(user_id=user_id)
    host_id = user_dict["status"]["in_battle"]
    battle_dict = get_battle_dict(host_id=host_id)
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
        if user_is_host(user_id=user_id):
            battle_dict["host_active_pokemon"] = pokemon
        else:
            battle_dict["guest_active_pokemon"] = pokemon
        bot.sendMessage(chat_id=update.message.chat_id, text='{} sent out {}!'.format(user_dict["status"]["username"],
                                                                                      pokemon))


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
