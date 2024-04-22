import disnake
from disnake.ext import commands
import mysql.connector
from config import DB_host, DB_username, DB_password, DB_name

# Connect to your MySQL database
db = mysql.connector.connect(
    host=DB_host,
    user=DB_username,
    password=DB_password,
    database=DB_name
)
cursor = db.cursor()

async def review_search(ctx, keywords: str):
    try:
        # Split the input string into individual keywords
        keywords = keywords.split()

        # Construct the query to search for each keyword in column 2 and retrieve corresponding result from column 9
        # Construct the query to search for each keyword in column 2 and retrieve corresponding result from column 9
        query = "SELECT `COL 9` FROM `soj___all_reviews` WHERE "
        query += " AND ".join(["`COL 2` LIKE %s"] * len(keywords))

        # Execute the constructed query
        cursor.execute(query, [('%' + keyword + '%') for keyword in keywords])
        results = cursor.fetchall()

        # Check if any results were found
        if results:
            # If more than 10 results, limit to 10
            if len(results) > 10:
                results = results[:10]
                # Inform the user about more results and suggest refining the query
                await ctx.send(f"Trop de résultats. Essayez d'ajuster votre recherche.")
            
            # Construct a message with the results
            message = f"Les résultats pour les mots-clef '{', '.join(keywords)}' sont:\n"
            for result in results:
                message += f"- {result[0]}\n"

            # Send the message
            await ctx.send(message)
        else:
            await ctx.send(f"Aucun résultat trouvé pour les mots-clef '{', '.join(keywords)}'")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
