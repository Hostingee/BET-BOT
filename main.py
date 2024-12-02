import os
import re
import asyncio
from telethon import events, TelegramClient
from telethon.tl.types import PhotoStrippedSize
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, ContextTypes, CommandHandler, filters
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment Variables
API_ID = int(os.getenv("API_ID", "2282111"))
API_HASH = os.getenv("API_HASH", "da58a1841a16c352a2a999171bbabcad")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7357384521:AAEELUVDMZzdrBlEaphntKxWB9zM9hl7yyk")
BOT_USERNAME = os.getenv("BOT_USERNAME", "@hexaguess420_bot")
CHAT_IDS = [-1002450653337, -1002329043138]

# Directories
TEMP_CACHE_DIR = "BET BOT/cache"
FINAL_CACHE_DIR = "cache"
os.makedirs(TEMP_CACHE_DIR, exist_ok=True)
os.makedirs(FINAL_CACHE_DIR, exist_ok=True)

# Initialize Telethon Client
guess_solver = TelegramClient("temp", API_ID, API_HASH)

# Initialize Telegram Bot API Application
telegram_app = Application.builder().token(BOT_TOKEN).build()


def sanitize_filename(name):
    """Remove invalid characters from filenames."""
    return re.sub(r'[<>:"/\\|?*]', '', name)


async def delete_message_later(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int = 10):
    """Deletes a message after a specified delay."""
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Deleted message {message_id} in chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to delete message {message_id}: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command in bot's DM."""
    if update.message.chat.type == "private":  # Ensure it's in a private chat (DM)
        await update.message.reply_text(
            text="🌟 Welcome to the Pokémon Guessing Bot! 🌟\n\n"
                 "🎮 Join the game and have fun!\n\n"
                 "👉 Click here to join the group: [Join Now](https://t.me/+ikG7sJXB9toyZGRl)",
            parse_mode="markdown"
        )


@guess_solver.on(events.NewMessage(from_users=572621020, chats=tuple(CHAT_IDS), incoming=True))
async def guesser(event):
    """Handles Pokémon guessing game messages."""
    correct_name = None

    if event.message.photo:
        for size in event.message.photo.sizes:
            if isinstance(size, PhotoStrippedSize):
                size = str(size)

            for file in os.listdir(FINAL_CACHE_DIR):
                with open(f"{FINAL_CACHE_DIR}/{file}", "rb") as f:
                    file_content = f.read()
                    if file_content == size.encode("utf-8"):
                        correct_name = file.split(".txt")[0]
                        break

            if correct_name:
                message_text = f"🌟 **Who's That Pokémon?** 🌟\n\n1️⃣ {correct_name}\n\n📝 Pick your guess and type it below!"
                await guess_solver.send_message(
                    BOT_USERNAME, f"GroupID: {event.chat_id}\n{message_text}", parse_mode="markdown"
                )
            break

        temp_cache_path = f"{TEMP_CACHE_DIR}/cache.txt"
        with open(temp_cache_path, "wb") as file:
            file.write(size.encode("utf-8"))
        logger.info(f"Stripped size saved temporarily in {temp_cache_path}")
    else:
        logger.warning("No photo found in the message.")


async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwards Pokémon guessing messages to the appropriate group."""
    if update.message.chat_id == update.effective_user.id:
        match = re.search(r"GroupID: (-\d+)", update.message.text)
        if match:
            group_chat_id = int(match.group(1))  # Extract Group ID
            message_text = re.sub(r"GroupID: -\d+\n", "", update.message.text)
            correct_option = re.search(r"1️⃣ (.+)", message_text)

            if correct_option:
                correct_answer = correct_option.group(1)
                keyboard = [
                    [KeyboardButton(correct_answer)],[KeyboardButton("/guess")]
                    
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

                try:
                    sent_message = await context.bot.send_message(
                        chat_id=group_chat_id,
                        text="🌟 **Who's That Pokémon?** 🌟\n\n📝 Type your guess or tap below:",
                        reply_markup=reply_markup,
                        parse_mode="markdown"
                    )
                    logger.info(f"Message successfully sent to group {group_chat_id}.")
                    asyncio.create_task(delete_message_later(context, group_chat_id, sent_message.message_id))
                except Exception as e:
                    logger.error(f"Error sending message to group {group_chat_id}: {e}")
            else:
                logger.warning("Correct answer not found in the message text.")
        else:
            logger.warning("Group ID not found in the message text.")


@guess_solver.on(events.NewMessage(from_users=572621020, pattern="The pokemon was ", chats=tuple(CHAT_IDS)))
async def cache_pokemon(event):
    """Caches the Pokémon name with its stripped size."""
    pokemon_name = ((event.message.text).split("The pokemon was ")[1]).split(" ")[0]
    sanitized_name = sanitize_filename(pokemon_name)

    temp_cache_path = f"{TEMP_CACHE_DIR}/cache.txt"
    final_cache_path = f"{FINAL_CACHE_DIR}/{sanitized_name}.txt"

    try:
        with open(temp_cache_path, "rb") as inf:
            file_content = inf.read()
            with open(final_cache_path, "wb") as file:
                file.write(file_content)
        os.remove(temp_cache_path)
        logger.info(f"Pokémon '{sanitized_name}' cached successfully in {final_cache_path}.")
    except Exception as e:
        logger.error(f"Error caching Pokémon: {e}")


async def start_telethon_client():
    """Start the Telethon client with retry logic."""
    while True:
        try:
            await guess_solver.start()
            logger.info("Telethon client started. Listening for messages...")
            break
        except Exception as e:
            logger.error(f"Telethon client connection failed: {e}")
            await asyncio.sleep(5)


async def start_telegram_bot():
    """Start the Telegram bot with retry logic."""
    while True:
        try:
            await telegram_app.initialize()
            logger.info("Telegram Bot Application initialized.")
            await telegram_app.start()
            logger.info("Telegram Bot Application started.")
            break
        except Exception as e:
            logger.error(f"Telegram bot connection failed: {e}")
            await asyncio.sleep(5)


async def health_check(request):
    """Health check endpoint."""
    return web.Response(text="OK", status=200)



async def main():
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

    task_telethon = asyncio.create_task(start_telethon_client())
    task_bot = asyncio.create_task(start_telegram_bot())
    await asyncio.gather(guess_solver.run_until_disconnected(), telegram_app.updater.start_polling())


if __name__ == "__main__":
    asyncio.run(main())
