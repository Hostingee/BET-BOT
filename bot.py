import os
import random
import re
import asyncio
from telethon import events, TelegramClient
from telethon.tl.types import PhotoStrippedSize
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, ContextTypes, filters
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
BOT_TOKEN = os.getenv("BOT_TOKEN", "7357384521:AAE3oiVuRsJ92_REDYnH49f1zJdVYKLy0hE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "@hexaguess420_bot")
CHAT_IDS = [-1002450653337]

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
                all_pokemon = [
                    file.split(".txt")[0] for file in os.listdir(FINAL_CACHE_DIR) if file.endswith(".txt")
                ]
                options = random.sample([name for name in all_pokemon if name != correct_name], 2)
                options.append(correct_name)
                random.shuffle(options)

                formatted_message = "\n".join(
                    f"{i + 1}️⃣ {option}" for i, option in enumerate(options)
                )
                message_text = f"🌟 **Who's That Pokémon?** 🌟\n\n{formatted_message}\n\n📝 Pick your guess and type it below!"
                await guess_solver.send_message(
                    BOT_USERNAME, f"GroupID: {event.chat_id}\n{message_text}", parse_mode="markdown"
                )
            break

        temp_cache_path = f"{TEMP_CACHE_DIR}/cache.txt"
        with open(temp_cache_path, "wb") as file:
            file.write(size.encode("utf-8"))
        print(f"Stripped size saved temporarily in {temp_cache_path}")
    else:
        print("No photo found in the message.")


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
        print(f"Pokémon '{sanitized_name}' cached successfully in {final_cache_path}.")
    except Exception as e:
        print(f"Error caching Pokémon: {e}")


async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwards Pokémon guessing messages to the appropriate group."""
    if update.message.chat_id == update.effective_user.id:
        match = re.search(r"GroupID: (-\d+)", update.message.text)
        if match:
            group_chat_id = int(match.group(1))
            message_text = re.sub(r"GroupID: -\d+\n", "", update.message.text)
            options = re.findall(r"\d️⃣ (.+)", message_text)

            if options and len(options) == 3:
                keyboard = [
                    [KeyboardButton(options[0]), KeyboardButton(options[1])],
                    [KeyboardButton(options[2]), KeyboardButton("/guess")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                sent_message = await context.bot.send_message(
                    chat_id=group_chat_id,
                    text="🌟 **Who's That Pokémon?**",
                    reply_markup=reply_markup,
                    parse_mode="markdown"
                )
                asyncio.create_task(delete_message_later(context, group_chat_id, sent_message.message_id))
            else:
                logger.warning("Options not properly extracted from message.")
        else:
            logger.warning("Group ID not found in the message text.")


telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))


async def main():
    await guess_solver.start()
    print("Telethon client started. Listening for messages...")
    await asyncio.gather(
        guess_solver.run_until_disconnected(),
        telegram_app.run_polling()
    )


if __name__ == "__main__":
    asyncio.run(main())
