import random

from telegram.ext import Updater
updater = Updater(token='183271930:AAGYn-3WiGIQU50i9uH99hRhOQQBQMfH9Wc')
dispatcher = updater.dispatcher
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
level=logging.INFO)

def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Hello! Send /help to get a list of commands!")

from telegram.ext import CommandHandler
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()

def echo(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=update.message.text)

from telegram.ext import MessageHandler, Filters
echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

# ================================ Damage calculators

def checkstab(attack_type, attacker_type):
    if attack_type == attacker_type:
        return 1.5
    else:
        return 1

def checktypeadv(att_type, def_type):
    return 1 #TO DO: Add types

def modifiercalc(STAB, typeadv, criticalstage, otherbonus):
#    STAB = checkstab() #TO DO: ADD THIS and remove STAB from required arguments
#    typeadv = checktypeadv #TO DO: ditto ^
    if criticalstage == 0:
        criticalrate = 16
    elif criticalstage == 1:
        criticalrate = 8
    elif criticalstage == 2:
        criticalrate = 2
    else:
        criticalrate = 1
    if random.randint(1, criticalrate) == 1: #higher rate is worse (denominator)
        criticalbonus = 1.5
    else:
        criticalbonus = 1
    prerandom = STAB * typeadv * criticalbonus * otherbonus #get subtotal before randomising to include "1"
    return random.uniform(0.85 * prerandom, 1 * prerandom) #this guarantees sometimes it will get max


def damage(level, attack, defense, baseatk, modifier):
    return (((2 * level + 10)/250.0) * (attack / defense) * baseatk + 2) * modifier #TO DO: round down
