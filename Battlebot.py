import logging
import os
import random

try:
    import simplejson as json
except ImportError:
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


# ================================ Profile handling


def get_profile(user_id):
    user_path = "Users/{}.json".format(user_id)
    with open(user_path, "r") as infile:
        profile = jsonpickle.decode(infile.read())
    return profile


def get_battle(host_id):
    battle_path = "Battles/{}.json".format(host_id)
    with open(battle_path, "r") as infile:
        battle = jsonpickle.decode(infile.read())
    return battle


def save_profile(user_id, profile):
    user_path = "Users/{}.json".format(user_id)
    with open(user_path, "w") as outfile:
        outfile.write(jsonpickle.encode(profile))


def save_battle(host_id, battle):
    battle_path = "Battles/{}.json".format(host_id)
    with open(battle_path, "w") as outfile:
        outfile.write(jsonpickle.encode(battle))


def delete_battle(host_id):
    battle_path = "Battles/{}.json".format(host_id)
    os.remove(battle_path)


def has_profile(user_id):
    user_path = "Users/{}.json".format(user_id)
    if os.path.isfile(user_path):
        return True
    else:
        return False


# ================================ Battle and profile classes


class Pokemon(object):
    def __init__(self, poke_id):
        self.id = poke_id
    
    nickname = ""
    name = ""
    held_items = ""
    abilities = ""
    moves = []
    types = []


class Profile(object):
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.money = 5000
        self.wins = 0
        self.losses = 0

    party = []
    inventory = []
    in_battle = ""
    battle_against = ""
    command = ""  # TODO: Should be able to take an object "Move" or similar


class Battle(object):
    def __init__(self, host_id, guest_id):
        self.host_id = host_id  # TODO: Change this so that it can be pickled, flatten?
        self.guest_id = guest_id
        self.turn = 0
    
    def do_turn(self, host, guest):  # TODO: Add speed checking to see who goes first, etc
        self.turn += 1
        return = []
        
    def take_command(self, host_command="", guest_command=""):
        host = get_profile(user_id=host_id)
        guest = get_profile(user_id=guest_id)
        if host_command:
            host.command = host_command
            save_profile(user_id=self.host_id, profile=host)
        if guest_command:
            guest.command = guest_command
            save_profile(user_id=self.guest_id, profile=guest)
        if host.command and guest.command:
            return self.do_turn(host=host, guest=guest)
        elif host.command and not guest.command:
            return ["{} is ready!", "Waiting for {}!"]

    def end_battle(self, winner_id):
        if winner_id == self.host.user_id:
            winner = self.host
            loser = self.guest
        else:
            winner = self.guest
            loser = self.host
        winner.money += loser.money - loser.money // 2
        loser.money = loser.money // 2
        save_profile(user_id=winner.user_id, profile=winner)
        save_profile(user_id=loser.user_id, profile=loser)
        delete_battle(host_id=self.host.user_id)

    def surrender(self, user_id):
        if self.host.user_id == user_id:  # If user who surrenders is host
            winner_id = self.guest.user_id  # Then guest is the winner
        else:  # If user who surrenders is not host
            winner_id = self.host.user_id  # Then host is the winner
        self.end_battle(winner_id=winner_id)


# ================================ Profile callback functions


def create_profile(user_id: str, username=""):  # Also may work as a reset
    user_path = "Users/{}.json".format(str(user_id))
    profile = Profile(user_id=user_id, username=username)
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
    custom_username = ' '.join(args)  # Makes argument list into a single string
    if has_profile(user_id=user_id):  # Checks if user has profile file already
        profile = get_profile(user_id=user_id)  # If so, opens file and only edits username
        profile.username = custom_username
        save_profile(user_id=user_id, profile=profile)
    else:
        create_profile(user_id=user_id, username=custom_username)  # Otherwise, creates profile with custom username
    bot.sendMessage(chat_id=update.message.chat_id, text='Username set to "' + custom_username + '"!')


# ================================ Battle hosting and joining

def is_in_battle(user_id: str):  # Checks if user is in active battle
    profile = get_profile(user_id=user_id)
    if profile.battle_against:  # Only if active battle
        return True
    else:  # Both being waiting for your friend to join or not hosting any battle will return False
        return False


def host_battle(bot, update):  # Callback for /battle and host_battle_handler
    user_id = str(update.message.from_user.id)
    if not has_profile(user_id=user_id):  # Makes sure user has profile
        create_profile(user_id=user_id, username=update.message.from_user.username)
    if is_in_battle(user_id=user_id):  # If user is in active battle
        bot.sendMessage(chat_id=update.message.chat_id, text='You are already in battle!')
    else:  # If user is NOT in active battle
        profile = get_profile(user_id=user_id)
        profile.in_battle = user_id
        save_profile(user_id=user_id, profile=profile)
        bot.sendMessage(chat_id=update.message.chat_id, text='Done! Tell your friend to send "/join '
                                                             + user_id + '" to join the battle!')


def join_battle(bot, update, args: list):  # Callback for /join and join_battle_handler
    user_id = str(update.message.from_user.id)
    host_id = " ".join(args)
    host_path = "Users/{}.json".format(host_id)
    if not has_profile(user_id=user_id):  # Makes sure user has profile
        create_profile(user_id=user_id, username=update.message.from_user.username)
    if not args:  # User did not provide host_id as args
        bot.sendMessage(chat_id=update.message.chat_id, text='You must add the number after "/join "!')
    elif not os.path.isfile(host_path):  # User provided wrong or non-existent host_id
        bot.sendMessage(chat_id=update.message.chat_id, text='That user is not ready to battle!')
    elif host_id == user_id:  # User provided their own user_id
        bot.sendMessage(chat_id=update.message.chat_id, text='You cannot battle yourself!')
    elif is_in_battle(user_id=user_id):  # User provided host_id but user is in battle
        bot.sendMessage(chat_id=update.message.chat_id, text='You are already in battle!')
    elif is_in_battle(user_id=host_id):  # User provided host_id but host is in battle
        bot.sendMessage(chat_id=update.message.chat_id, text='That user is already in battle!')
    elif not get_profile(user_id=host_id).in_battle:  # User provided host_id but host is not hosting battle
        bot.sendMessage(chat_id=update.message.chat_id, text='That user is not willing to battle!')
    else:  # User provided host_id and is not in active battle
        host_profile = get_profile(user_id=host_id)  # Opens the host's profile
        host_profile.battle_against = user_id  # Sets the user_id as the host's foe
        save_profile(user_id=host_id, profile=host_profile)  # Overwrites the host's profile

        guest_profile = get_profile(user_id=user_id)  # Opens the guest's user file
        guest_profile.in_battle = host_id  # Updates the profile with the battle's host_id
        guest_profile.battle_against = host_id  # Sets the host_id as the guest's foe
        save_profile(user_id=user_id, profile=guest_profile)  # Overwrites the guest's user file

        battle = jsonpickle.encode(Battle(host_id=host_profile, guest_id=guest_profile))  # Creates battle object
        save_battle(host_id=host_id, battle=battle)
        bot.sendMessage(chat_id=update.message.chat_id, text='Successfully joined the battle! Send out your Pokémon by '
                                                             'sending "/go" followed by a space and the name of the '
                                                             'Pokémon you want to choose!')


def abort_battle(bot, update, args):  # TODO: Should add 1 loss if aborts when already in battle, nothing if waiting
    user_id = update.message.from_user.id 
    if not has_profile(user_id=user_id):
        create_profile(user_id=user_id)
    profile = get_profile(user_id=user_id)
    if is_in_battle(user_id=user_id) and args == profile.in_battle:  # In active battle and sent "confirmation code"
        battle = get_battle(host_id=profile.in_battle)
        battle.end_battle(winner_id=profile.battle_against)
        bot.sendMessage(chat_id=update.message.chat_id, text='{} surrendered!'.format(profile.username))
    elif is_in_battle(user_id=user_id) and args != profile.in_battle:  # In active battle but sent wrong code
        bot.sendMessage(chat_id=update.message.chat_id, text='You mistyped the code after "/abort "!')
    elif is_in_battle(user_id) and not args:  # If in active battle and no arguments, sends "confirmation code"
        bot.sendMessage(chat_id=update.message.chat_id, text='If you really want to surrender, '
                                                             'send "/abort {}"'.format(profile.in_battle))
    elif not is_in_battle(user_id=user_id) and profile.in_battle:  # Hosting battle but not actively battling
        profile.in_battle = ""
        save_profile(user_id=user_id, profile=profile)
        bot.sendMessage(chat_id=update.message.chat_id, text='You are now no longer hosting a battle!')
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text='You are not yet hosting or fighting any battle!')


# ================================ Battle processing


def user_is_host(user_id):
    profile = get_profile(user_id=user_id)
    host_id = profile.in_battle
    battle = get_battle(host_id=host_id)
    if battle.host.user_id == user_id:
        return True
    else:
        return False


def pokemon_out(user_id):
    profile = get_profile(user_id=user_id)
    host_id = profile.in_battle
    battle = get_battle(host_id=host_id)
    if user_is_host(user_id=user_id) and battle.host_active_pokemon:
        return True
    elif (not user_is_host(user_id)) and battle.guest_active_pokemon:
        return True
    else:
        return False


def send_pokemon(bot, update, args: list):  # Callback for /go and
    user_id = str(update.message.from_user.id)
    if not has_profile(user_id=user_id):  # Makes sure user has user file
        create_profile(user_id=user_id, username=update.message.from_user.username)
    pokemon = " ".join(args)
    profile = get_profile(user_id=user_id)
    if not is_in_battle(user_id):
        bot.sendMessage(chat_id=update.message.chat_id, text='You are not in battle!')
    elif not pokemon:  # User sent no arguments
        bot.sendMessage(chat_id=update.message.chat_id, text='You have to write a name after "/go "!'
                                                             '(e.g.: "/go Bulbasaur)')
    elif pokemon_out(user_id):  # "is_in_battle" being True also made sure user has a "battle_against"
        bot.sendMessage(chat_id=update.message.chat_id, text='You already have a Pokémon out!')
    else:  # User is in battle and has NO Pokémon out
        host_id = profile.in_battle
        battle = get_battle(host_id=host_id)
        if user_is_host(user_id=user_id):
            battle.host_active_pokemon = pokemon
        else:
            battle.guest_active_pokemon = pokemon
        save_battle(host_id=host_id, battle=battle)
        bot.sendMessage(chat_id=update.message.chat_id, text='{} sent out {}!'.format(profile.username, pokemon))


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

abort_battle_handler = CommandHandler('abort', abort_battle, pass_args=True)
dispatcher.add_handler(abort_battle_handler)


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
