from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater, MessageHandler, CommandHandler, RegexHandler, CallbackQueryHandler
import config_private as config
from urllib.request import urlopen
import hashlib
import logging
import pickle
import os.path
import string
import random
import time
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

HELPTEXT='''
Type /newPack to start a new Pack
'''

dataFile="data.pkl"
data = {}
data["admin_id"] = -1
data["chat_state"] = {}

admin_token=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
def save_obj(obj, name ):
    with open(name, 'w+b') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
        
def load_obj(name ):
    with open(name, 'rb') as f:
        return pickle.load(f)

def saveData():
    save_obj(data, dataFile)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="I'm a bot, please talk to me!")

def recieve(bot, update, chat_data):
    message = update.message
    chat_id = message.chat.id

    
    if not ("state" in chat_data)  or chat_data["state"]=="none":
        message.reply_text("No command active.\n"+HELPTEXT)
        return
    
    if chat_data["state"]=="add GIF":
        if message.document:
            if message.document.mime_type=="video/mp4":
                message.reply_text("Added to your Pack.\n_Send another one to continue, type _/finish_ to save and publish your pack, or type _/cancel_ to abort creation_",parse_mode=ParseMode.MARKDOWN)
            else:
                message.reply_text("Please add only GIFs to *GIF*-Packs",parse_mode=ParseMode.MARKDOWN)
    else:
        if  chat_data["state"]=="add Description":
            print()
            

def newPack(bot, update, chat_data):
    if not ("state" in chat_data) or chat_data["state"]=="none":
        chat_data["state"]="add GIFs"
        
def admin(bot, update, job_queue):
    global data
    global admin_token
    chat_id=update.message.chat_id
    if data["admin_id"]==-1:
        if update.message.text==("admin verify "+admin_token):
            data["admin_id"]=update.message.chat_id
            update.message.reply_text("Success, you are now `ADMIN`\n\nI am at your command.",parse_mode=ParseMode.MARKDOWN)
            return
    if data["admin_id"]==chat_id:
        update.message.reply_text("Hello `ADMIN`!",parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text("Nice try but you are not `ADMIN`!\nThis incident will be reportet!",parse_mode=ParseMode.MARKDOWN)

def test(bot, update):
    
    keyboard = [[InlineKeyboardButton("Option 1", callback_data='1'),
                 InlineKeyboardButton("Option 2", callback_data='2')],

                [InlineKeyboardButton("Option 3", callback_data='3')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)

    print(update)

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))

    
def main():

    updater = Updater(config.token)
    # Get the dispatcher to register handlers
    
    dp = updater.dispatcher

    # on different commands - answer in Telegram

    dp.add_handler(CommandHandler("start", start))
    
    dp.add_handler(CommandHandler("newPack",
                                  newPack,
                                  pass_chat_data=True))
    dp.add_handler(MessageHandler(Filters.all,
                                  recieve,
                                  pass_chat_data=True))

    
    # log all errors
    dp.add_error_handler(error)
    print("Loading data")
    if os.path.isfile(dataFile):
        global data
        data=load_obj(dataFile)
        print("done")
    else:
        print("No data-file found. Once any settigns are made, one will be created")
    if data["admin_id"] == -1:
        global admin_token
        print("CRITICAL WARNING: No Admin-Chat is set,\n"+
              "   to verify as Admin, please send \"admin verify "+admin_token+"\" to the Bot\n"+
              "   The first one to send this, will be the Admin\n"+
              "   If somehow anyone but you gets admin, delete data.pkl")
    # Start the Bot
    updater.start_polling()
    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()





if __name__ == '__main__':
    
    main()
#start_handler = CommandHandler('start', start)
#dispatcher.add_handler(start_handler)
#updater.start_polling()