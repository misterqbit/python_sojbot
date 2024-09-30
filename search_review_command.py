import disnake
from disnake.ext import commands
import mysql.connector
from mysql.connector import Error
from config import DB_host, DB_username, DB_password, DB_name

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_host,
            user=DB_username,
            password=DB_password,
            database=DB_name,
            charset= 'utf8mb4',  # Specify the charset
            collation= 'utf8mb4_general_ci',  # Specify a compatible collation
            connection_timeout=10  # Set a reasonable timeout value
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Platform: {e}")
        return None

async def review_search(ctx, keywords: str):
    db = create_db_connection()
    if not db:
        await ctx.send("Could not connect to the database.")
        return
    
    cursor = db.cursor()
    try:
        # Split the input string into individual keywords
        keywords_list = keywords.split()

        # Construct the query to search for each keyword in column 2 and retrieve corresponding result from column 9
        query = "SELECT `COL 9` FROM `soj___all_reviews` WHERE "
        query += " AND ".join(["`COL 2` LIKE %s"] * len(keywords_list))

        # Execute the constructed query
        cursor.execute(query, [('%' + keyword + '%') for keyword in keywords_list])
        results = cursor.fetchall()

        # Check if any results were found
        if results:
            # If more than 10 results, limit to 10
            if len(results) > 10:
                results = results[:10]
                await ctx.send(f"Trop de résultats. Essayez d'ajuster votre recherche.")

            # Construct a message with the results
            message = f"Les résultats pour les mots-clef '{', '.join(keywords_list)}' sont:\n"
            for result in results:
                # Replace spaces with %20
                formatted_result = result[0].replace(" ", "%20")
                message += f"- {formatted_result}\n"

            # Send the message
            await ctx.send(message)
        else:
            await ctx.send(f"Aucun résultat trouvé pour les mots-clef '{', '.join(keywords_list)}'")
    except Error as e:
        await ctx.send(f"An error occurred: {e}")
    finally:
        cursor.close()
        db.close()
