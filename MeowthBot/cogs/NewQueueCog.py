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

        if "GOOGLE_OAUTH_JSON" in os.environ:
            self.sheet = gclient.open("InHouseData").worksheet("Meowth_Queue")
        elif os.path.isfile("InHouseTest.json"):
            self.sheet = gclient.open("InHouseDataTest").worksheet("Test_Queue")
        
        self.queue = self.sheet.get_all_values()[0]
        print(self.queue)

    @commands.command(aliases=["join"])
    async def add(self, ctx):
        """ Add yourself to the queue! """
        
    
    @commands.command(aliases=["forcejoin","fjoin", "fadd"])
    async def forceadd(self, ctx, member: discord.Member):
        """ Force another user to join the queue with an @ """
        
    
    @commands.command(name="ready", aliases=["go"])
    async def _ready(self, ctx, num=""):
        """ If everyone is ready to game, this command will ping them! """
        
    
    @commands.command(aliases=["leave", "drop"])
    async def remove(self, ctx):
        """ Remove yourself from the queue """
        
    
    @commands.command(aliases=["forcedrop","forceleave","fremove","fdrop","fleave"])
    async def forceremove(self, ctx, member: discord.Member):
        """ Force another user to drop from the queue with an @ """
        
    
    @commands.command(name="queue", aliases=["lobby", "q"])
    async def _queue(self, ctx):
        """ See who's up next! """
        
    
    @commands.command(aliases=["qtime","settime"])
    async def queuetime(self, ctx, *, _time):
        """ Set gaming time """
        self.qtime = _time
        await ctx.invoke(self._queue)

    @commands.command(name="next")
    async def _next(self, ctx, num=1):
        """ Call the next member in the queue """


    @is_approved()
    @commands.command()
    @commands.has_permissions(manage_roles=True, ban_members=True)
    async def clear(self, ctx):
        """ Clears the queue (ADMIN ONLY) """
        self.queue = []
        self.qtime = "None set yet"
        await ctx.send("Queue has been cleared")

    @commands.command()
    async def leggo(self, ctx, *, _time = "None set yet"):
        """ Tries to get a game ready """
        self.qtime = _time
        await ctx.send("Time for some 10 mens! Join the lobby @here")
        