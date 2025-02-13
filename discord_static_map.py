import networkx as nx
import matplotlib.pyplot as plt
import disnake

# Function to fetch server data dynamically
def fetch_discord_server_data(guild):
    graph_data = {}
    for channel in guild.channels:
        if isinstance(channel, disnake.TextChannel):
            threads = [thread.name for thread in channel.threads]
            graph_data[channel.name] = threads
    return graph_data

# Function to shorten names to avoid overlaps
def shorten_name(name, max_length=15):
    return name if len(name) <= max_length else name[:max_length] + "..."

# Function to generate the Discord map
def generate_discord_map(graph_data, output_file="server_map.png"):
    # Create a directed graph
    G = nx.DiGraph()

    # Add nodes and edges
    for channel, threads in graph_data.items():
        G.add_node(channel, type='channel', color='lightblue', size=2000)
        for thread in threads:
            shortened_thread = shorten_name(thread)
            G.add_node(shortened_thread, type='thread', color='lightgreen', size=1000)
            G.add_edge(channel, shortened_thread)

    # Extract attributes for styling
    node_colors = [data['color'] for _, data in G.nodes(data=True)]
    node_sizes = [data['size'] for _, data in G.nodes(data=True)]

    # Draw the graph
    plt.figure(figsize=(16, 12))

    # Use a shell layout for better spatial distribution
    pos = nx.shell_layout(G)

    # Draw nodes and edges
    nx.draw(
        G, pos,
        with_labels=True,
        labels={node: shorten_name(node) for node in G.nodes()},
        node_size=node_sizes,
        node_color=node_colors,
        font_size=8,
        font_color='black',
        edge_color='gray',
        alpha=0.8
    )

    # Set title and save the map
    plt.title("Discord Server Map", fontsize=16)
    plt.savefig(output_file)
    plt.show()

async def generate_map(inter: disnake.ApplicationCommandInteraction):
    await inter.response.defer()

    # Fetch graph data
    graph_data = fetch_discord_server_data(inter.guild)

    # Generate and save the map
    generate_discord_map(graph_data)

    await inter.followup.send(file=disnake.File("server_map.png"))
