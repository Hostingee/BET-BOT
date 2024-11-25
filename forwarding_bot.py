from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, ContextTypes, filters
import logging
import re
import asyncio

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7357384521:AAE3oiVuRsJ92_REDYnH49f1zJdVYKLy0hE"

# Dictionary to store the message IDs of bot messages
bot_messages = {}

async def delete_message_later(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay: int = 10):
    """Deletes a message after a specified delay."""
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Deleted message {message_id} in chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to delete message {message_id}: {e}")

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forwards Pokémon guessing messages to the appropriate group."""
    if update.message.chat_id == update.effective_user.id:  # Message from private chat
        # Extract the group ID from the message text
        match = re.search(r"GroupID: (-\d+)", update.message.text)
        if match:
            group_chat_id = int(match.group(1))  # Extract group ID

            # Extract Pokémon options from the message
            message_text = re.sub(r"GroupID: -\d+\n", "", update.message.text)
            options = re.findall(r"\d️⃣ (.+)", message_text)  # Extract options

            if options and len(options) == 3:
                # Create a reply keyboard with Pokémon options and /guess button
                keyboard = [
                    [KeyboardButton(options[0]), KeyboardButton(options[1])],
                    [KeyboardButton(options[2]), KeyboardButton("/guess")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

                # Forward the message with reply keyboard to the appropriate group
                sent_message = await context.bot.send_message(
                    chat_id=group_chat_id,
                    text="🌟 **Who's That Pokémon?",
                    reply_markup=reply_markup,
                    parse_mode="markdown"
                )

                # Schedule message deletion
                asyncio.create_task(delete_message_later(context, group_chat_id, sent_message.message_id))

            else:
                logger.warning("Options not properly extracted from message.")
        else:
            logger.warning("Group ID not found in the message text.")

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles user guesses for the Pokémon guessing game."""
    chat_id = update.message.chat_id  # Group chat ID
    user_message = update.message.text.strip()  # User's guess or command

    if user_message == "/guess":
        # Handle regenerating new Pokémon options (mocking for now)
        new_options = ["Bulbasaur", "Charmander", "Squirtle"]
        keyboard = [
            [KeyboardButton(new_options[0]), KeyboardButton(new_options[1])],
            [KeyboardButton(new_options[2]), KeyboardButton("/guess")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        sent_message = await context.bot.send_message(
            chat_id=chat_id,
            text="🌟 **Wait:",
            reply_markup=reply_markup,
            parse_mode="markdown"
        )

        # Schedule message deletion
        asyncio.create_task(delete_message_later(context, chat_id, sent_message.message_id))
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎉 {update.message.from_user.first_name} guessed: {user_message}!",
            parse_mode="markdown"
        )

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Add handler to forward messages from private chat
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

    # Add handler for guesses and commands
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^(?!GroupID).*"), handle_guess))

    application.run_polling()

if __name__ == "__main__":
    main()
