#!/usr/bin/python3

from cmath import log
from discord.ext import commands
import discord
import Token
import logging
import re
import random
import math
import sqlite3
import os

"""
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
"""

""" 
class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message: discord.Message):
        if message.author == client.user:
            return

        print('Message from {0.author}: {0.content}'.format(message))
        assert isinstance(message.channel, discord.abc.Messageable)
        await message.channel.send("Hi")

client = MyClient()
client.run(Token.token) """

bot = commands.Bot("//", status=discord.Status.online, intents=discord.Intents.all())
bad_double_quotes = re.compile(r"[“”]")
bad_single_quotes = re.compile(r"[‘’]")

con = sqlite3.connect('MingoBot.db')
cur = con.cursor()

@bot.event
async def on_ready():
    print("Logged on as {0}!".format(bot.user))
    await bot.get_channel(357409958922551296).send("Logged on as {0}!".format(bot.user))

@bot.event
async def on_message(message: discord.Message):
    message.content = bad_double_quotes.sub('"', message.content)
    message.content = bad_single_quotes.sub('"', message.content)
    await bot.process_commands(message)

"""
@bot.event
async def on_message_delete(message: discord.Message):
    if (message.author == bot.user):
        await message.channel.send(message.content)
"""

@bot.command(name="eval")
@commands.is_owner()
async def _eval(ctx: commands.Context, *, arg: str):
    """mingo888 only: Wrapper for Python's eval()"""
    print("Evaluating...")
    await ctx.send(eval(arg, globals(), globals()))

@bot.command(name="exec")
@commands.is_owner()
async def _exec(ctx: commands.Context, *, arg: str):
    """mingo888 only: Wrapper for Python's exec()"""
    print("Executing...")
    exec(arg, globals(), globals())

@bot.command(name="flipcoin")
async def flipcoin(ctx: commands.Context):
    """Flips a coin"""
    print("Flipping coin...")
    if random.random() >= 0.998:
        await ctx.send("The coin landed on its side")
    else:
        await ctx.send(random.choice(["Heads", "Tails"]))

@bot.command(name="rolldice")
async def rolldice(ctx: commands.Context, num: int = 1):
    """Rolls up to 20 dice"""
    if num < 1:
        return
    if num > 20:
        num = 20
    print("Rolling dice...")
    rolls = [random.randint(1, 6) for _ in range(num)]
    message = ", ".join(map(str, rolls))
    if num > 1:
        message = message + "  (total of %d dice: %d)" % (num, sum(rolls))
    await ctx.send(message)

@bot.command(name="points")
async def points(ctx: commands.Context, user: discord.User = None):
    """Checks your MingoPoints or those of another user"""
    print("Checking points...")
    message = str(user) + " has "
    if user is None:
        user = ctx.author
        message = "You have "
    cur.execute("SELECT amount FROM points WHERE user = ?", (user.id,))
    amount = cur.fetchone()
    if not amount:
        message = message + "no MingoPoints"
    elif amount[0] == 1:
        message = message + "1 MingoPoint"
    else:
        message = message + str(amount[0]) + " MingoPoints"
    await ctx.send(message)

@bot.command(name="allpoints")
async def allpoints(ctx: commands.Context):
    """Displays a list of all MingoPoints in existence"""
    print("Checking all points...")
    cur.execute("SELECT * FROM points")
    message = ""
    for user, amount in cur:
        message = message + str(bot.get_user(user)) + " : " + str(amount) + "\n"
    await ctx.send(message)

@bot.command(name="pay")
async def pay(ctx: commands.Context, payee: discord.User, amount: int):
    """Makes a MingoPoint payment to another user"""
    if await forcepay(ctx, ctx.author, payee, amount):
        with open("MingoBot.log", "r+") as file:
            file.seek(0, 2)
            file.seek(file.tell() - len(os.linesep) - len(" (forced)"), 0)
            file.write("\n")
            file.truncate()

@bot.command(name="forcepay")
@commands.is_owner()
async def forcepay(ctx: commands.Context, payer: discord.User, payee: discord.User, amount: int):
    """mingo888 only: forces a MingoPoint transaction"""
    print("Paying...")
    if amount <= 0:
        await ctx.send("Amount must be greater than zero")
        return
    if payer == payee:
        await ctx.send("Payer and payee must be different")
        return
    if payee.bot:
        await ctx.send("Bots cannot receive MingoPoints")
        return
    cur.execute("UPDATE points SET amount = amount - ? WHERE user = ? RETURNING amount", (amount, payer.id))
    new_amount = cur.fetchone()
    if not new_amount:
        # payer not found in DB, so assume 0 MingoPoints
        if ctx.author is payer:
            await ctx.send("You do not have any MingoPoints")
        else:
            await ctx.send(str(payer) + " does not have any MingoPoints")
        return
    elif new_amount[0] == 0:
        cur.execute("DELETE FROM points WHERE user = ?", (payer.id,))
    cur.execute("INSERT INTO points VALUES (:payee, :amount) ON CONFLICT DO \
                UPDATE SET amount = amount + :amount WHERE user = :payee",
                {"payee": payee.id, "amount": amount})
    with open("MingoBot.log", "a") as file:
        file.write("%s paid %s %d MingoPoint" % (payer, payee, amount) + "s"[:amount^1] + " (forced)\n")
    con.commit()
    await ctx.send("Success")
    return True

@bot.command(name="log")
async def log(ctx: commands.Context, page: int = 1):
    """Displays the MingoPoint transaction log"""
    print("Displaying log...")
    with open("MingoBot.log", "r") as file:
        lines = file.readlines()[::-1]
        pages = math.ceil(len(lines) / 12)
        page = max(1, min(page, pages))
        message = "=== Displaying page %d of %d ===\n" % (page, pages)
        message += "".join(lines[(page - 1) * 12 : page * 12])
    await ctx.send(message)

@bot.command(name="achievements")
async def achievements(ctx: commands.Context, user: discord.User = None):
    """Checks your achievements or those of another user"""
    print("Checking achievements...")
    message = str(user) + " has "
    if user is None:
        user = ctx.author
        message = "You have "
    cur.execute("SELECT achievement FROM achievements WHERE user = ?", (user.id,))
    achievements = cur.fetchall()
    if not achievements:
        message = message + "no achievements"
    else:
        message = message + "these achievements:\n"
        for (achievement,) in achievements:
            message = message + achievement + "\n"
    await ctx.send(message)

@bot.command(name="allachievements")
async def allachievements(ctx: commands.Context):
    """Displays a list of all achievements"""
    print("Checking all achievements...")
    cur.execute("SELECT * FROM achievements")
    message = ""
    for user, achievement in cur:
        message = message + str(bot.get_user(user)) + " : " + achievement + "\n"
    await ctx.send(message)

@bot.command(name="award")
@commands.is_owner()
async def award(ctx: commands.Context, user: discord.User, achievement: str):
    """mingo888 only: awards an achievement"""
    print("Awarding achievement...")
    cur.execute("INSERT INTO achievements VALUES (?, ?)", (user.id, achievement))
    con.commit()
    await ctx.send("Success")

@bot.command(name="revoke")
@commands.is_owner()
async def revoke(ctx: commands.Context, user: discord.User, achievement: str):
    """mingo888 only: revokes an achievement"""
    print("Revoking achievement...")
    cur.execute("DELETE FROM achievements WHERE user = ? AND achievement = ? RETURNING user", (user.id, achievement))
    if len(cur.fetchall()) != 1:
        await ctx.send("Achievement not found")
        return
    con.commit()
    await ctx.send("Success")

@bot.command(name="changelog")
async def changelog(ctx: commands.Context):
    """Displays the changelog"""
    print("Displaying changelog...")
    with open("changelog.txt", "r") as file:
        await ctx.send(file.read())

@bot.command(name="send")
@commands.is_owner()
async def send(ctx: commands.Context, channel: discord.TextChannel, *, message: str):
    """mingo888 only: sends a message in the specified channel"""
    print("Sending message...")
    await channel.send(message)

@bot.command(name="read")
@commands.is_owner()
async def read(ctx: commands.Context, channel: discord.TextChannel):
    """mingo888 only: reads the last message of the specified channel"""
    print("Reading from channel...")
    message = channel.last_message
    if not message:
        message = await channel.fetch_message(channel.last_message_id)
    await ctx.send(str(message.author) + " said: " + message.content)

@bot.command(name="moveme")
async def moveme(ctx: commands.Context, channel: discord.VoiceChannel):
    """Moves you to the specified channel"""
    print("Moving user...")
    await ctx.author.move_to(channel)

@moveme.error
@read.error
@send.error
@changelog.error
@revoke.error
@award.error
@allachievements.error
@achievements.error
@forcepay.error
@pay.error
@allpoints.error
@points.error
@rolldice.error
@flipcoin.error
@_exec.error
@_eval.error
async def errors(ctx, error):
    con.rollback()
    if isinstance(error, commands.NotOwner):
        await ctx.send("ERROR: You are not mingo888")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("ERROR: Mising argument")
    elif isinstance(error, commands.UserNotFound):
        await ctx.send("ERROR: User not found")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send("ERROR: Channel not found")
    elif isinstance(error, commands.CommandInvokeError):
        if isinstance(error.original, sqlite3.IntegrityError):
            await ctx.send("ERROR: Insufficient MingoPoints")
        elif isinstance(error.original, sqlite3.OperationalError):
            await ctx.send("ERROR: SQL syntax")
        else:
            await ctx.send(error.original)
            raise error
    else:
        await ctx.send("ERROR: Unknown")
        raise error

bot.run(Token.token)
