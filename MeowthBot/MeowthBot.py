import discord
import os
import random

from discord.ext import commands, tasks

from cogs.MeowthCog import Meowth
from cogs.QueueCog import Queue

intents = discord.Intents.default()
intents.members = True
# Change this to whatever prefix you'd like
prefixes = ["!", "."]
# Instantiate our bot
bot = commands.Bot(command_prefix=prefixes,
                    case_insensitive=True,
                    intents=intents
                    )

@bot.event
async def on_ready():
    print(bot.user.name)
    print(bot.user.id)
    # Disabling, as the bot experienced a lot of resets lately.
    # channel = bot.get_channel(656313087707840523)
    # await channel.send('Bot has been reset.')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.upper() == "W":
        await message.add_reaction("\U0001F1FC")
    elif message.content.upper() == "L":
        await message.add_reaction("\U0001F1F1")
    elif message.content.upper() == "F":
        await message.add_reaction("\U0001F1EB")
    else:
        await bot.process_commands(message)

# queue_emojis = [join_id, drop_id]
queue_emojis = [668410201099206680,668410288667885568]

@bot.event
async def on_raw_reaction_add(reaction):
    if reaction.user_id == bot.user.id:
        return

    if not (reaction.emoji.id in queue_emojis):
        return
    
    guild = await bot.fetch_guild(reaction.guild_id)
    user = await guild.fetch_member(reaction.user_id)
    channel = bot.get_channel(reaction.channel_id)
    message = await channel.fetch_message(reaction.message_id)
    ctx = await bot.get_context(message)

    if reaction.emoji.id == 668410201099206680:
        await ctx.invoke(bot.get_command("forceadd"),user)
        return
    elif reaction.emoji.id == 668410288667885568:
        await ctx.invoke(bot.get_command("forceremove"),user)
        return

token = None

if "BOT_KEY" in os.environ:
    token = os.environ["BOT_KEY"]
    print("Using environment var for key")
elif os.path.isfile("key"):
    print("Using file for key")
    with open("key", "r") as f:
        token = f.read().strip().strip("\n")

# Add in our cogs
bot.add_cog(Meowth(bot))
bot.add_cog(Queue(bot))

if token is not None:
    bot.run(token)
else:
    print("Failed to find token in `key` file or `BOT_KEY` environment variable")
