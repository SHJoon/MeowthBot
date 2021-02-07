import asyncio
import discord
from discord.ext import commands

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tempfile import NamedTemporaryFile
from functools import wraps
import os

creds = None
gclient = None
google_oauth_json = None

if "GOOGLE_OAUTH_JSON" in os.environ:
    google_oauth_json = os.environ["GOOGLE_OAUTH_JSON"]
elif os.path.isfile("InHouseTest.json"):
    print("Grabbed local json file for test spreadsheet.")
    with open("InHouseTest.json", "r") as f:
        google_oauth_json = f.read()

f = NamedTemporaryFile(mode="w+", delete=False)
f.write(google_oauth_json)
f.flush()

scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    
creds = ServiceAccountCredentials.from_json_keyfile_name(
        f.name, scope
    )

gclient = gspread.authorize(creds)

def retry_authorize(exceptions, tries=4):
    def deco_retry(f):
        @wraps(f)
        async def f_retry(*args, **kwargs):
            mtries = tries
            while mtries > 1:
                try:
                    return await f(*args, **kwargs)
                except exceptions as e:
                    msg = f"{e}, Reauthorizing and retrying ..."
                    gclient.login()
                    print(msg)
                    mtries -= 1
            return await f(*args, **kwargs)

        return f_retry

    return deco_retry

class QueueCog(commands.Cog):
    def __init__(self, bot):
        self.qtoggle = True
        self.qtime = "None set yet"
        self.queuemsg = None
        self.readynum = 0

        self.creds = creds
        self.gclient = gclient
        self.lock = asyncio.Lock()
        self.alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        if "GOOGLE_OAUTH_JSON" in os.environ:
            self.sheet = gclient.open("InHouseData").worksheet("Meowth_Queue")
        elif os.path.isfile("InHouseTest.json"):
            self.sheet = gclient.open("InHouseDataTest").worksheet("Test_Queue")
        
        self.queue = [int(member_id) for member_id in self.sheet.get_all_values()[0]]
        print(self.queue)
    
    async def update_sheet(self, ctx):
        if len(self.queue) == 0:
            self.sheet.clear()
            return
        
        col_alpha = self.alphabet[len(self.queue) - 1]
        
        sheet_a1_range = f'A1:{col_alpha}1'
        cell_list = self.sheet.range(sheet_a1_range)

    @commands.command(name="queue", aliases=["lobby", "q"])
    async def _queue(self, ctx):
        """ View the queue! """
        # Try to delete previous queue message
        if self.queuemsg is not None:
            try:
                await self.queuemsg.delete()
            except Exception:
                pass
        
        # Build our queue message
        await self.update_sheet(ctx)
        msg = f"**Gaming time**: {self.qtime}\n"
        if len(self.queue) == 0:
            msg += f"Queue is empty."
        else:
            for place, member_id in enumerate(self.queue):
                member = discord.utils.get(ctx.guild.members, id=int(member_id))
                name = member.nick if member.nick else member.name
                msg += f"**#{place+1}** : {name}\n"
        
        # Build our embed
        embed = discord.Embed(description=msg, colour=discord.Colour.blue())
        embed.set_footer(text="Join the queue with !add / Leave the queue with !leave")
        self.queuemsg = await ctx.send(embed=embed)

        # Add reaction for join/drop
        await self.queuemsg.add_reaction("<:join:668410201099206680>")
        await self.queuemsg.add_reaction("<:drop:668410288667885568>")
        
        # Attempt to delete user message if possible
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(aliases=["join", "fadd", "forceadd", "fjoin", "forcejoin"])
    @retry_authorize(gspread.exceptions.APIError)
    async def add(self, ctx, member: discord.Member=None):
        """ Add yourself or another person to the queue! """
        # Check if user is adding themselves or another person
        if member is not None:
            member_id = member.id
        else:
            member_id = ctx.message.author.id
        
        # Check if member is already in queue or not
        if member_id not in self.queue:
            self.queue.append(member_id)
        elif member is not None:
            await ctx.send(f"{member.nick} is already in queue!")
        else:
            await ctx.send(f"You are already in queue!")
        
        # Repost the queue
        await ctx.invoke(self._queue)
    
    @commands.command(aliases=["leave", "drop", "fdrop", "fremove", "fleave",
        "forcedrop", "forceremove", "forceleave"])
    @retry_authorize(gspread.exceptions.APIError)
    async def remove(self, ctx, member: discord.Member=None):
        """ Remove yourself from the queue """
        # Check if user is removing themselves or another person
        if member is not None:
            member_id = member.id
        else:
            member_id = ctx.message.author.id
        
        # Check if member is already in queue or not
        if member_id in self.queue:
            self.queue.remove(member_id)
        elif member is not None:
            await ctx.send(f"{member.name} was not in the queue!")
        else:
            await ctx.send(f"You were not in the queue!")
        
        # Repost the queue
        await ctx.invoke(self._queue)

    @commands.command(name="ready", aliases=["go"])
    @retry_authorize(gspread.exceptions.APIError)
    async def _ready(self, ctx, num:int=-1):
        """ If everyone is ready to game, this command will ping them! """
        if num == -1:
            self.readynum = len(self.queue)
        else:
            self.readynum = num
        
        if len(self.queue) < self.readynum:
            await ctx.send("Not enough people in the lobby...")
        else:
            msg = ""
            for i in range(self.readynum):
                member = discord.utils.get(ctx.guild.members, id=self.queue[0])
                msg += member.mention
                self.queue.pop(0)
            await ctx.send(msg)
        
        await ctx.invoke(self._queue)
    
    @commands.command(aliases=["qtime","settime"])
    async def queuetime(self, ctx, *, _time):
        """ Set gaming time """
        self.qtime = _time
        await ctx.invoke(self._queue)

    @commands.command(name="next")
    @retry_authorize(gspread.exceptions.APIError)
    async def _next(self, ctx, num=1):
        """ Call the next member in the queue """
        for _ in range(num):
            if len(self.queue) == 0:
                await ctx.send("No one left in the queue :(")
                return
            member = discord.utils.get(ctx.guild.members, id=self.queue[0])
            await ctx.send(f"You are up **{member.mention}**! Have fun!")
            self.queue.pop(0)

    @commands.command()
    @commands.has_permissions(manage_roles=True, ban_members=True)
    @retry_authorize(gspread.exceptions.APIError)
    async def clear(self, ctx):
        """ Clears the queue (ADMIN ONLY) """
        self.queue.clear()
        self.qtime = "None set yet"
        await ctx.send("Queue has been cleared")
        await ctx.invoke(self._queue)

    @commands.command()
    async def leggo(self, ctx, *, _time = "None set yet"):
        """ Tries to get a game ready """
        self.qtime = _time
        await ctx.send("Gaming time! Join the lobby @here")
