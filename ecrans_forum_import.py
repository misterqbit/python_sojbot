import disnake
import asyncio
import re
from mysql.connector import Error
from db import get_db_connection


FORUM_ID = 16  
MAX_TOPICS_TO_PROCESS = 1500
CHANNEL_ID = 1333853515348447243  

def remove_nested_quotes(text):
    """Recursively removes all nested [quote] tags and their contents."""
    while re.search(r"\[quote[^\]]*\].*?\[/quote\]", text, flags=re.DOTALL):
        text = re.sub(r"\[quote[^\]]*\].*?\[/quote\]", "", text, flags=re.DOTALL).strip()
    return text

def process_bbcode(message):
    #print(f"Original message:\n{message}\n")  # Debug: Show the input message
    # Convert other BBCode formatting
    message = re.sub(r"\[b\](.*?)\[/b\]", r"**\1**", message, flags=re.DOTALL)
    message = re.sub(r"\[i\](.*?)\[/i\]", r"*\1*", message, flags=re.DOTALL)
    message = re.sub(r"\[u\](.*?)\[/u\]", r"__\1__", message, flags=re.DOTALL)
    message = re.sub(r"\[code\](.*?)\[/code\]", r"`\1`", message, flags=re.DOTALL)
    message = re.sub(r"\[size=.*?\](.*?)\[/size\]", r"\1", message, flags=re.DOTALL)
    message = re.sub(r"\[color=.*?\](.*?)\[/color\]", r"\1", message, flags=re.DOTALL)
    message = re.sub(r"\[list\](.*?)\[/list\]", r"\n\1\n", message, flags=re.DOTALL)  # Ensure lists have breaks
    message = re.sub(r"\[\*\](.*?)", r"- \1", message, flags=re.DOTALL)
    message = re.sub(r"\[url.*?\](.*?)\[/url\]", r"\1", message, flags=re.DOTALL)
    message = re.sub(r"\[img.*?\](.*?)\[/img\]", r"\1", message, flags=re.DOTALL)

    # Find text before the first `[quote]` block
    before_quote_match = re.match(r"^(.*?)\s*(?=\[quote)", message, flags=re.DOTALL)
    before_quote = before_quote_match.group(1).strip() if before_quote_match else ""
    if before_quote:
        message = message[len(before_quote):].lstrip()

    # Match the outermost quote block
    match = re.match(r"\[quote(?:=([^\]]+))?\](.*)", message, flags=re.DOTALL)
    
    if not match:
        #print("No quote detected. Returning original message.\n")  # Debug
        return message.strip()  # No quotes, return as is
    
    username, quoted_content = match.groups()
    #print(f"Detected username: {username}")  # Debug
    #print(f"Quoted content before cleanup:\n{quoted_content}\n")  # Debug
    quoted_content = "||```" + quoted_content

    # Remove all nested quotes and their content
    cleaned_content = remove_nested_quotes(quoted_content)
    
    # Ensure all remaining [/quote] tags are removed
    cleaned_content = re.sub(r"\[/quote\]", "```||", cleaned_content).strip()
    
    #print(f"Quoted content after removing nested quotes:\n{cleaned_content}\n")  # Debug

    # Format the response
    if before_quote :
        message = f"{before_quote}\n\nEn réponse à {username} :\n{cleaned_content}" if username else f"En réponse à :\n{cleaned_content}"
    else:
        message = f"En réponse à {username} :\n{cleaned_content}" if username else f"En réponse à :\n{cleaned_content}"

    return message.strip()

def split_message(message, max_length=1900):
    #"""Splits long messages to fit within Discord's 2000-character limit."""
    #parts = [message[i:i+max_length] for i in range(0, len(message), max_length)]
    #return [f">>> {part}" for part in parts]
    """Splits long messages into parts without cutting words."""
    if len(message) <= max_length:
        return [f">>> {message}"]

    parts = []
    paragraphs = message.split("\n")  
    current_part = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_length:  # New check for single long paragraph
            # Split it into chunks
            words = paragraph.split(" ")
            temp_part = ""
            for word in words:
                if len(temp_part) + len(word) + 1 > max_length:
                    parts.append(f">>> {temp_part.strip()}")
                    temp_part = word  # Start new chunk
                else:
                    temp_part += " " + word
            if temp_part:
                parts.append(f">>> {temp_part.strip()}")
        else:
            if len(current_part) + len(paragraph) + 1 > max_length:
                parts.append(f">>> {current_part.strip()}")
                current_part = paragraph
            else:
                current_part += "\n" + paragraph

    if current_part:
        parts.append(f">>> {current_part.strip()}")

    return parts


async def import_forum_data(bot):
    """Imports topics and messages from the MySQL database into Discord forum threads."""
    db = get_db_connection()
    if not db:
        return "Failed to connect to the database."

    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel or not isinstance(channel, disnake.ForumChannel):
            return "Invalid channel ID or channel is not a forum channel."

        existing_threads = {thread.name: thread for thread in channel.threads if thread is not None}


        cursor = db.cursor(dictionary=True)

        cursor.execute(
            f"SELECT id, subject, poster, posted "
            f"FROM ecrans_topics WHERE forum_id = {FORUM_ID} ORDER BY last_post ASC LIMIT {MAX_TOPICS_TO_PROCESS}"
        )
        topics = cursor.fetchall()

        if not topics:
            return "No topics found to process."
        thread_name = None
        NEW_MAX_TOPICS_TO_PROCESS = MAX_TOPICS_TO_PROCESS
        for topic in topics:
            thread_name = topic["subject"]
            if thread_name in existing_threads:
                thread_count = len(channel.threads)
                NEW_MAX_TOPICS_TO_PROCESS = NEW_MAX_TOPICS_TO_PROCESS + thread_count
            
        if NEW_MAX_TOPICS_TO_PROCESS > MAX_TOPICS_TO_PROCESS:
            cursor.execute(
            f"SELECT id, subject, poster, posted "
            f"FROM ecrans_topics WHERE forum_id = {FORUM_ID} ORDER BY last_post ASC LIMIT {NEW_MAX_TOPICS_TO_PROCESS}"
            )
            topics = cursor.fetchall()


        created_count = 0
        print(f"Loaded {len(topics)} topics.")

        for topic in topics:
            thread_name = topic["subject"]
            thread_starter = topic["poster"]
            posted_date = topic["posted"]

            if thread_name in existing_threads:
                print(f"Thread '{thread_name}' already exists, skipping creation.")
                continue
            else:
                # Create the thread and get the actual thread object
                thread_with_message = await channel.create_thread(
                    name=thread_name,
                    content=f"**Sujet créé par {thread_starter}**\nLe: <t:{posted_date}:f>"
                )
                thread = thread_with_message.thread  # Extract the actual thread

            created_count += 1

            # Fetch and post messages for this topic
            cursor.execute(
                "SELECT poster, message, posted "
                "FROM ecrans_posts WHERE topic_id = %s ORDER BY posted ASC",
                (topic["id"],),
            )
            messages = cursor.fetchall()

            for message in messages:
                poster = message["poster"]
                posted_timestamp = message["posted"]  
                content = process_bbcode(message["message"])  
                if not content:  
                    content = "(Message vide ou non supporté)"

                #formatted_content = "> " + content.replace("\n", "\n> ")
                #formatted_content = ">>> " + content
                message_parts = split_message(content)
                message_parts.insert(0, f"**{poster} a écrit le <t:{posted_timestamp}:f>:**\n")
                #message_parts[-1] += "\n\u200B"
                message_parts.append("\n\u200B")

                for i, part in enumerate(message_parts):
                    if i == len(message_parts) - 1:
                        part += "\n\n"       
                    try:
                        await thread.send(
                            content=f"{part}",
                            allowed_mentions=disnake.AllowedMentions.none()
                        )
                    except disnake.HTTPException as e:
                        print(f"Error sending message part: {e}")
                        print("Rejected message content:")
                        print(part)
                        
                await asyncio.sleep(1)  

        return f"Created {created_count} new threads and imported messages."

    except Error as e:
        error_message = f"🚨 Database error: {e}\nLast processed thread: '{thread_name if created_count > 0 else 'None'}'."
        print(error_message)  # Print in console

        # Send error message in the forum channel
        try:
            if channel:
                await channel.send(error_message)
        except Exception as discord_error:
            print(f"Failed to send error message to Discord: {discord_error}")

        return error_message

    finally:
        if db.is_connected():
            cursor.close()
            db.close()
