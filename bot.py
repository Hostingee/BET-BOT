import random
import os
import asyncio
import re
from telethon import events, TelegramClient
from telethon.tl.types import PhotoStrippedSize

# Telethon API credentials
api_id = 2282111
api_hash = 'da58a1841a16c352a2a999171bbabcad'
bot_username = "@hexaguess420_bot"  # Replace with your bot's username
guessSolver = TelegramClient('temp', api_id, api_hash)

# Chat IDs to monitor
chat_ids = [-1002450653337]

# Directories
temp_cache_dir = "BET BOT/cache"
final_cache_dir = "cache"
os.makedirs(temp_cache_dir, exist_ok=True)
os.makedirs(final_cache_dir, exist_ok=True)

def sanitize_filename(name):
    """Remove invalid characters from filenames."""
    return re.sub(r'[<>:"/\\|?*]', '', name)

@guessSolver.on(events.NewMessage(from_users=572621020, chats=tuple(chat_ids), incoming=True))
async def guesser(event):
    """Handles Pokémon guessing game messages."""
    correct_name = None

    # Check if the message contains a photo
    if event.message.photo:
        for size in event.message.photo.sizes:
            if isinstance(size, PhotoStrippedSize):
                size = str(size)

            # Match photo size with cached Pokémon
            for file in os.listdir(final_cache_dir):
                with open(f"{final_cache_dir}/{file}", "rb") as f:
                    file_content = f.read()
                    if file_content == size.encode("utf-8"):
                        correct_name = file.split(".txt")[0]
                        break

            if correct_name:
                # Generate random Pokémon options
                all_pokemon = [
                    file.split(".txt")[0] for file in os.listdir(final_cache_dir) if file.endswith(".txt")
                ]
                options = random.sample([name for name in all_pokemon if name != correct_name], 2)
                options.append(correct_name)
                random.shuffle(options)

                # Create the message text
                formatted_message = "\n".join(
                    f"{i + 1}️⃣ {option}" for i, option in enumerate(options)
                )
                message_text = f"🌟 **Who's That Pokémon?** 🌟\n\n{formatted_message}\n\n📝 Pick your guess and type it below!"

                # Include the originating group ID in the message
                await guessSolver.send_message(
                    bot_username, f"GroupID: {event.chat_id}\n{message_text}", parse_mode="markdown"
                )
            break

        # Save the stripped size temporarily in the `BET BOT/cache` directory
        temp_cache_path = f"{temp_cache_dir}/cache.txt"
        with open(temp_cache_path, "wb") as file:
            file.write(size.encode("utf-8"))
        print(f"Stripped size saved temporarily in {temp_cache_path}")
    else:
        print("No photo found in the message.")

@guessSolver.on(events.NewMessage(from_users=572621020, pattern="The pokemon was ", chats=tuple(chat_ids)))
async def cache_pokemon(event):
    """Caches the Pokémon name with its stripped size."""
    pokemon_name = ((event.message.text).split("The pokemon was ")[1]).split(" ")[0]
    sanitized_name = sanitize_filename(pokemon_name)

    temp_cache_path = f"{temp_cache_dir}/cache.txt"
    final_cache_path = f"{final_cache_dir}/{sanitized_name}.txt"

    try:
        # Move the stripped size from `BET BOT/cache` to the final `cache` directory
        with open(temp_cache_path, "rb") as inf:
            file_content = inf.read()
            with open(final_cache_path, "wb") as file:
                file.write(file_content)
        os.remove(temp_cache_path)
        print(f"Pokémon '{sanitized_name}' cached successfully in {final_cache_path}.")
    except Exception as e:
        print(f"Error caching Pokémon: {e}")

# Start the Telethon client
async def main():
    await guessSolver.start()
    print("Bot started. Listening for messages...")
    await guessSolver.run_until_disconnected()

asyncio.run(main())
