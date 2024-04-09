import os
import spotipy
import aiohttp
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
import logging

load_dotenv()

# Constants
BOT_USERNAME: Final = os.getenv("VALARIFY_BOT_USERNAME")

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# START COMMAND
async def start_cmd(update: Update, context):
    await update.message.reply_text("Welcome to the Valarify Bot!")

# FIND SEARCH ID OF SONGS
def search_id(name: str) -> str:
    client_credentials_manager = SpotifyClientCredentials(client_id=os.getenv("SPOTIFY_C_ID"), client_secret=os.getenv("SPOTIFY_C_SECRET"))
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    results = sp.search(q=name, type='track')

    if len(results['tracks']['items']) > 0:
        track_id = results['tracks']['items'][0]['id']
        logger.info("Track ID: %s", track_id)
        return track_id
    else:
        logger.info("Track not found.")
        return ""

# GET THE SONG DOWNLOAD URL BY API
async def get_data(id: str) -> str:
    try:
        url = f"{os.getenv('VALARIFY_API')}/{id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if "url" in data:
                        url = data["url"]
                        return f"Here is the download link: {url}"
                    else:
                        return "The URL is not available in the response."
                elif response.status == 404:
                    return "Track not found, it is added in the downloading queue and will be available shortly."
                else:
                    return "Failed to fetch data from API."
    except Exception as e:
        logger.error("An error occurred: %s", e)
        return f"An error occurred: {e}"

# HANDLE MESSAGE OF THE USER
async def handle_message(update: Update, context):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    logger.info("User (%s) in %s: '%s'", update.message.chat.id, message_type, text)

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            song_id: str = search_id(new_text)
            response: str = await get_data(song_id)
            logger.info('Bot: %s', response)
            await update.message.reply_text(response)
    else:
        song_id: str = search_id(text)
        response: str = await get_data(song_id)
        logger.info('Bot: %s', response)
        await update.message.reply_text(response)

# ERROR
async def error(update: Update, context):
    logger.error("Update %s caused error %s", update, context.error)

# MAIN
if __name__ == '__main__':
    TOKEN: Final = os.getenv("VALARIFY_BOT_TOKEN")

    logger.info("Bot is starting...")

    app = Application.builder().token(TOKEN).build()

    # COMMANDS
    app.add_handler(CommandHandler("start", start_cmd))

    # MESSAGES
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # ERROR
    app.add_error_handler(error)

    # POLLING
    logger.info("Polling...")
    app.run_polling(poll_interval=3)
