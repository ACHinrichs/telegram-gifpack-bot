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
from enum import Enum




# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

HELPTEXT='''
Type /newPack to start a new Pack
'''
ERROR_MSG='''
Unfortunatly, there was an error.
Please try again Later.

If the error occurs often, please add a new Bugreport at the [Issuetracker](https://github.com/ACHinrichs/telegram-gifpack-bot/issues)
'''

dataFile="data.pkl"
data = {}
data["admin_id"] = -1
data["chat_state"] = {}
data["next_pack_id"] = 0

gifpacks = {}


admin_token=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

class InvalidIDException(Exception):
    """Exception raised for invalid Pack-IDs.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

class States(Enum):
    NONE=0
    NEW_PACK_NAME=1
    NEW_PACK_ADD_GIF=2
    NEW_PACK_ADD_TEXT=2

class Gif:
    def __init__(self, gif_id, thumb_id, text):
        self.gif_id=gif_id
        self.thumb_id=thumb_id
        self.text=text


class GifPack:
    gifs=[]
    name=""
    creator=-1
    pack_id=-1
    
    def __init__(self, name, creator, pack_id=-1, gifs=[]):
        self.gifs=gifs
        self.name=name
        self.creator=creator
        self.pack_id=pack_id
        
    def add_gif(self, gif, thumb, text):
        self.gifs.append(Gif(gif, thumb, text))

    def set_id(self, pack_id):
        self.pack_id=pack_id

        
    def set_name(self, name):
        self.name=name


class GifPackCollection:

    # pack_path: String the path, where to store the packs WITHOUT following /
    def __init__(self, pack_path):
        self.gif_packs={}
        self.pack_path=pack_path


    def add_pack(self, gif_pack):
        if not (gif_packs[gif_pack.pack_id]):
            self.gif_packs[gif_pack.pack_id]=gif_pack
            save_obj(self.gif_pack,self.pack_path+"/"+gif_pack.pack_id+".pkl")
        else:
            raise InvalidIDException("GifPackCollection.add_pack", "pack-id "+
                                     gif_pack.pack_id+" is already taken")

    def get_pack(self, pack_id):
        if (self.gif_packs[pack_id]):
            return self.gif_packs[pack_id]
        else:
            try:
                pack=load_obj(self.pack_path+"/"+pack_id+".pkl")
                self.gif_packs[pack_id]=pack
                return pack
            except Exception as e:
                alert(e)
                return None
                
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
    
    if chat_data["state"]==States.NEW_PACK_NAME:
        if message.text:
            chat_data["new_pack"]=GifPack(message.text, message.chat_id)
            message.reply_text("Ok, please send me the first Gif for your new pack _"+
                               chat_data["new_pack"].name+"_!",parse_mode=ParseMode.MARKDOWN)
            chat_data["state"]=States.NEW_PACK_ADD_GIF
        else:
            message.reply_text("Error, please add a Name first",
                               parse_mode=ParseMode.MARKDOWN)
    else:   
        if chat_data["state"]==States.NEW_PACK_ADD_GIF:
            if message.document:
                if message.document.mime_type=="video/mp4":
                    chat_data["new_gif"]=message.document.file_id
                    chat_data["new_thumb"]=message.document.thumb.file_id
                    message.reply_text("Marked to be appended to your Pack.\n"+
                                       "Send a description to add this gif to your pack\n"+
                                       "_Send another one to overwrite this one, "+
                                       "type _/finish_ to save and publish "+
                                       "your pack, or type _/cancel_ to abort creation_",
                                       parse_mode=ParseMode.MARKDOWN)
                    chat_data["state"]=States.NEW_PACK_ADD_TEXT
                else:
                    message.reply_text("Please add only GIFs to *GIF*-Packs",
                                       parse_mode=ParseMode.MARKDOWN)
            else:
                if chat_data["state"]==States.NEW_PACK_ADD_TEXT:
                    chat_data["new_pack"].add_gif(chat_data["new_gif"], chat_data["new_thumb"], message.text)
                    message.reply_text("Appended to your Pack.\n"+
                                       "_Send another one to continue, "+
                                       "type _/finish_ to save and publish "+
                                       "your pack, or type _/cancel_ to abort creation_",
                                       parse_mode=ParseMode.MARKDOWN)
                    chat_data["state"]=States.NEW_PACK_ADD_GIF
                        
def newPack(bot, update, chat_data):
    if not ("state" in chat_data) or chat_data["state"]==States.NONE:
        chat_data["state"]=States.NEW_PACK_NAME
        update.message.reply_text("Ok, we will create a new Gif-Pack.\n\n"+
                           "Please choose a name for your new pack\n\n"+
                           "_Type _/cancel_ to abort creation_",
                           parse_mode=ParseMode.MARKDOWN)

def abort(bot, update, chat_data):
    chat_data["state"]=States.NONE
    chat_data["new_pack"]=None
    update.message.reply_text("Packcreation Aborted",
                              parse_mode=ParseMode.MARKDOWN)


def finish(bot, update, chat_data):
    chat_data["state"]=States.NONE
    
    pack_id=data["next_pack_id"]
    data["next_pack_id"]=data["next_pack_id"]+1
    chat_data["new_pack"].set_id(pack_id)

    try:
        gifpacks[pack_id]=chat_data["new_pack"]
        chat_data["new_pack"]=None
        saveData()
        update.message.reply_text("Pack successfully saved! Aborted",
                                  parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        alert(e)
        update.message.reply_text(ERROR_MSG,
                                  parse_mode=ParseMode.MARKDOWN)
    
def admin(bot, update, chat_data):
    global data
    global admin_token
    chat_id=update.message.chat_id
    if data["admin_id"]==-1:
        if update.message.text==("admin verify "+admin_token):
            data["admin_id"]=update.message.chat_id
            update.message.reply_text("Success, you are now `ADMIN`\n\nI am at your command.",
                                      parse_mode=ParseMode.MARKDOWN)
            return
    if data["admin_id"]==chat_id:
        update.message.reply_text("Hello `ADMIN`!",parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text("Nice try but you are not `ADMIN`!\n\n"+
                                  "This incident will be reportet!",parse_mode=ParseMode.MARKDOWN)

def test(bot, update,chat_data):
    
    keyboard = [[InlineKeyboardButton("Option 1", callback_data='1'),
                 InlineKeyboardButton("Option 2", callback_data='2')],

                [InlineKeyboardButton("Option 3", callback_data='3')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Please choose:', reply_markup=reply_markup)

    print(update)

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def alert(msg):
    print(msg)
    
def main():

    updater = Updater(config.token)
    # Get the dispatcher to register handlers
    
    dp = updater.dispatcher

    # on different commands - answer in Telegram

    dp.add_handler(CommandHandler("start", start))
    
    dp.add_handler(CommandHandler("newPack",
                                  newPack,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("cancel",
                                  abort,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("finish",
                                  finish,
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
