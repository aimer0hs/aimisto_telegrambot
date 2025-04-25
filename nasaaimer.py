
from html import escape
from uuid import uuid4
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.constants import ParseMode
from telegram.ext import InlineQueryHandler, ConversationHandler
import logging
import requests
from telegram import ForceReply, Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ChosenInlineResultHandler
import os
from dotenv import load_dotenv
import wikipedia
import random

load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def make_url(url):
    result = url.replace(" ", "%20")
    return result 

def wikipedia_search(query, senteces=2):
    try:
        return wikipedia.summary(query, sentences=senteces)
    except:
        return 'No Available Data On Wikipedia.'

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"""Hi {user.mention_html()}! 
I'm a Aimer Astro Bot, I can do these things:
        
    /pod : I will send you the picture of the day from NASA
    
    /LMP : I will send you a random picture of (latest mars photos) pack including the photo date, rover and main camera
    
    /HMP : How many people are in space right now? know their name and their place

    /search : I will search for you through nasa and wikipedia information
    
    /cancel : I will say goodbye!
    """,
    )


async def picture_of_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    api_key = os.getenv('api_key')
    api_url = "https://api.nasa.gov/planetary/apod"
    response = requests.get(api_url , params={'api_key': api_key})
    resp = response.json()
    explaination = resp['explanation']
    url = resp['url']
    title = resp['title']
    await update.message.reply_photo(photo=url, caption=title)
    await update.message.reply_text(explaination)

async def nasa_image_and_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    utext = update.message.text
    api_url = "https://images-api.nasa.gov/search"
    response = requests.get(api_url , params={'q': utext})
    resp = response.json()
    best_resault = resp['collection']['items']
    await update.message.reply_text(best_resault)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye!", reply_markup=ReplyKeyboardRemove()
    )

async def how_many_people_are_in_space_right_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    resp = requests.get('http://api.open-notify.org/astros.json').json()
    output = f'There are {resp["number"]} in the space: \n \n'
    for astronaut in resp['people']:
        output += f'    {astronaut["name"]} At {astronaut["craft"]} \n'

    await update.message.reply_text(output)


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the inline query. This is run when you type: @botusername <query>"""
    query = update.inline_query.query

    if not query:  # empty query should not be handled
        return
    
async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text('tell me the space object you wanna know about')
    return 0

async def search_nasa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    utext = update.message.text

    api_url = "https://images-api.nasa.gov/search"
    response = requests.get(api_url , params={'q': utext})
    resp = response.json()
    best_results = resp['collection']['items'][0:20]
    results = 'please choose a subject for more info'
    for result_index in range(len(best_results)):

        results += f'{result_index + 1}. {best_results[result_index]["data"][0]["title"]} \n \n'

    context.user_data["results"] = best_results
    print(results)
    await update.message.reply_text(results)
    return 1

async def choose_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    utext = int(update.message.text)
    chosen_title = context.user_data["results"][utext]["data"][0]["title"]
    await update.message.reply_photo(context.user_data["results"][utext]['links'][0]['href'])
    await update.message.reply_text(wikipedia_search(chosen_title))
    return 1

async def latest_mars_photos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = requests.get('https://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/latest_photos?api_key=DEMO_KEY')
    resp = response.json()['latest_photos']
    chosen_mars_photo = random.choice(resp)
    caption = f"Rover: {chosen_mars_photo['rover']['name']} \n Taken At: {chosen_mars_photo['earth_date']} \n Camera: {chosen_mars_photo['rover']['cameras'][0]['full_name']}"
    await update.message.reply_photo(chosen_mars_photo['img_src'], caption=caption)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    telegram_token = os.getenv('telegram_token')
    application = Application.builder().token(telegram_token).build()

    conv_handler = ConversationHandler(
    entry_points=[CommandHandler("search", search_start)],
    states={
            0: [MessageHandler(filters.TEXT, search_nasa)],
            1: [MessageHandler(filters.Regex("^\d+$"), choose_result)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("LMP", latest_mars_photos))
    application.add_handler(CommandHandler("HMP", how_many_people_are_in_space_right_now))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("pod", picture_of_day))
    application.add_handler(CommandHandler("nasavidimg", nasa_image_and_video))
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()