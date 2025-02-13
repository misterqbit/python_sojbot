import disnake
import matplotlib.pyplot as plt
import pandas as pd
import io


async def plot_duration_over_time(interaction: disnake.ApplicationCommandInteraction, data: pd.DataFrame, start_season: int, end_season: int):
    # Filter the data based on start and end seasons
    filtered_data = data[(data['saison'] >= start_season) & (data['saison'] <= end_season)]
    
    # Use .loc to avoid SettingWithCopyWarning
    filtered_data.loc[:, 'duree'] = pd.to_timedelta(filtered_data['duree']).dt.total_seconds() / 60
    
    # Calculate the mean duration and standard deviation by season
    duration_stats = filtered_data.groupby('saison')['duree'].agg(['mean', 'std']).reset_index()

    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.errorbar(duration_stats['saison'], duration_stats['mean'], yerr=duration_stats['std'], fmt='o', capsize=5, color='skyblue', label='Durée moyenne')
    plt.title("Durée moyenne des épisodes par saison", fontsize=16)
    plt.xlabel("Saison", fontsize=12)
    plt.ylabel("Durée moyenne (minutes)", fontsize=12)
    plt.xticks(duration_stats['saison'])
    plt.grid(axis='y', linestyle='--')
    plt.legend()

    # Save the plot to a buffer
    buf = io.BytesIO()  # Ensure you're using io.BytesIO() here
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Send the plot to Discord
    await interaction.send(file=disnake.File(buf, 'duree_des_episodes.png'))

    # Close the plot to free memory
    plt.close()


async def plot_episodes_per_chroniqueur(interaction, data, start_season, end_season):
    # Filter data for the specified seasons
    filtered_data = data[(data['saison'] >= start_season) & (data['saison'] <= end_season)]

    # Ensure chroniqueurs are split by comma
    filtered_data.loc[:, 'statschroniqueurs'] = filtered_data['statschroniqueurs'].str.split(',')

    # Explode the list of chroniqueurs into separate rows
    exploded_data = filtered_data.explode('statschroniqueurs')

    # Group by chroniqueur and count episodes, limit to top 15
    episodes_per_chroniqueur = (
        exploded_data.groupby('statschroniqueurs')['episode']
        .count()
        .nlargest(15)  # Top 15 chroniqueurs
        .sort_values(ascending=False)
    )

    # Plotting the data
    plt.figure(figsize=(10, 6))
    episodes_per_chroniqueur.plot(kind='bar', color='skyblue')
    plt.title(f"Top 15 Chroniqueureuses par Nbre d'épisodes (de la saison {start_season} à la {end_season})")
    plt.xlabel('Chroniqueureuses')
    plt.ylabel("Nombre d'Épisodes")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    # Save the plot to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Send the plot in Discord
    await interaction.send(file=disnake.File(buf, 'episodes_per_chroniqueur.png'))


async def plot_episodes_per_month(interaction, data, start_season, end_season):
    # Filter data for the specified seasons
    filtered_data = data[(data['saison'] >= start_season) & (data['saison'] <= end_season)]

    # Ensure the 'date' column is a datetime object
    filtered_data['date'] = pd.to_datetime(filtered_data['date'])

    # Extract the month from the 'date' column (1 for January, 12 for December)
    filtered_data.loc[:, 'month'] = filtered_data['date'].dt.month  # Use .loc to avoid the warning

    # Group by month and count episodes
    episodes_per_month = filtered_data.groupby('month')['episode'].count()

    # Sort by month number for better visualization
    episodes_per_month = episodes_per_month.sort_index()

    # Plotting the data
    plt.figure(figsize=(10, 6))
    episodes_per_month.plot(kind='bar', color='lightgreen')
    plt.title(f"Nbre d'Épisodes par Mois (de la saison {start_season} à la {end_season})")
    plt.xlabel('Mois')
    plt.ylabel("Nombre d'Épisodes")
    plt.xticks(ticks=range(12), labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], rotation=45)
    plt.tight_layout()

    # Save the plot to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Send the plot in Discord
    await interaction.send(file=disnake.File(buf, 'episodes_per_month.png'))
