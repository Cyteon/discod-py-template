# This project is licensed under the terms of the GPL v3.0 license. Copyright 2024 Cyteon

import random
import discord
import aiohttp
import json
import requests
import io

from io import BytesIO
from discord.ui import Button, View

from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

from utils import Checks

class TicTacToeButton(Button):
    def __init__(self, x: int, y: int, player_x: discord.Member, player_o: discord.Member):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y
        self.player_x = player_x
        self.player_o = player_o

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if interaction.user != view.current_player:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        if self.label == "\u200b":
            self.label = "X" if view.current_player == self.player_x else "O"
            self.style = discord.ButtonStyle.danger if view.current_player == self.player_x else discord.ButtonStyle.primary
            self.disabled = True

            view.board[self.x][self.y] = 1 if view.current_player == self.player_x else -1
            view.current_player = self.player_o if view.current_player == self.player_x else self.player_x

            await interaction.response.edit_message(content=f"{view.current_player.mention}, your turn.", view=view)

            winner = view.check_winner()
            if winner:
                await interaction.followup.send(f"{winner.mention} wins!", ephemeral=False)
                view.stop()
            elif all(cell != 0 for row in view.board for cell in row):
                await interaction.followup.send("It's a tie!", ephemeral=False)
                view.stop()
        else:
            await interaction.response.send_message("This button is already clicked!", ephemeral=True)

class TicTacToeView(View):
    def __init__(self, player_x: discord.Member, player_o: discord.Member):
        super().__init__(timeout=None)
        self.player_x = player_x
        self.player_o = player_o
        self.current_player = player_x
        self.board = [[0 for _ in range(3)] for _ in range(3)]

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y, player_x, player_o))

    def check_winner(self):
        for row in self.board:
            if sum(row) == 3:
                return self.player_x
            elif sum(row) == -3:
                return self.player_o

        for col in range(3):
            if self.board[0][col] + self.board[1][col] + self.board[2][col] == 3:
                return self.player_x
            elif self.board[0][col] + self.board[1][col] + self.board[2][col] == -3:
                return self.player_o

        if self.board[0][0] + self.board[1][1] + self.board[2][2] == 3:
            return self.player_x
        elif self.board[0][0] + self.board[1][1] + self.board[2][2] == -3:
            return self.player_o

        if self.board[0][2] + self.board[1][1] + self.board[2][0] == 3:
            return self.player_x
        elif self.board[0][2] + self.board[1][1] + self.board[2][0] == -3:
            return self.player_o

        return None

class Fun(commands.Cog, name="🎉 Fun"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="http",
        description="Commands for http cat/dog/fish images.",
        usage="http <subcommand>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def http(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}http {cmd.name} - {cmd.description}" for cmd in self.http.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Http", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @http.command(
        name="cat",
        description="Get a cat image representing a http status code.",
        usage="http cat <code>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def cat(self, context: Context, code) -> None:
        await context.send(f"https://http.cat/{code}.jpg")

    @http.command(
        name="dog",
        description="Get a dog image representing a http status code.",
        usage="http dog <code>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def dog(self, context: Context, code) -> None:
        await context.send(f"https://http.dog/{code}.jpg")

    @http.command(
        name="fish",
        description="Get a fish image representing a http status code.",
        usage="http fish <code>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def fish(self, context: Context, code) -> None:
        await context.send(f"https://http.fish/{code}.jpg")

    @commands.hybrid_command( # TODO: fix this crap
        name="bored",
        description="Get an activity if you are bored"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def bored(self, context: Context) -> None:
        async with aiohttp.ClientSession() as session:
            url="https://bored-api.appbrewery.com/random"

            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.json()

                    embed = discord.Embed()

                    if "error" in data:
                        embed = discord.Embed(title=data["error"], color=discord.Color.brand_red())
                    else:
                        embed = discord.Embed(title=data["activity"], color=discord.Color.teal())

                        embed.add_field(name = "Type", value = data["type"].capitalize())
                        embed.add_field(name = "Participants", value = data["participants"])
                        embed.add_field(name = "Price", value = data["price"])

                    await context.send(embed=embed)
                elif r.status == 404:
                    embed = discord.Embed(title="No activities found", color=discord.Color.brand_red())

                    await context.send(embed=embed)
                else:
                    await context.send(f"BoredAPI is currently experiencing issues: Status " + str(r.status))

    @commands.hybrid_command(
        name="advice",
        description="Get some advice",
        usage="advice"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def advice(self, context: Context) -> None:
        async with aiohttp.ClientSession() as session:
            r = requests.get("https://api.adviceslip.com/advice")
            data = json.loads(r.text)

            await context.send(data["slip"]["advice"])

    @commands.hybrid_command(
        name="insult",
        description="Get an insult"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def insult(self, context: Context) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://evilinsult.com/generate_insult.php?lang=en&type=json") as r:
                if r.status == 200:
                    data = await r.json()

                    await context.send(data["insult"])

    @commands.hybrid_group(
        name="avatar",
        description="Commands for avatar manipulation",
        usage="avatar <subcommand>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def avatar(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}avatar {cmd.name} - {cmd.description}" for cmd in self.avatar.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Avatar", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @avatar.command(
        name="get",
        description="Get someone's avatar",
        usage="avatar get [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def get(self, context: Context, user: discord.User = None) -> None:
        if not user:
            user = context.author

        embed = discord.Embed(
            title=f"{user.name}'s Avatar",
            color=discord.Color.blurple()
        )

        embed.set_image(url=user.display_avatar.url)

        await context.send(embed=embed)

    @avatar.command(
        name="blur",
        description="Blur someone",
        usage="avatar blur [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def blur(self, context: Context, user: discord.User = None) -> None:
        if not user:
            user = context.author

        async with aiohttp.ClientSession() as session:
            img = await session.get(
                f"https://some-random-api.com/canvas/misc/blur?avatar={user.display_avatar.url}"
            )

            imageData = io.BytesIO(await img.read())
            await context.send(file=discord.File(imageData, "blur.png"))

    @avatar.command(
        name="pixelate",
        description="Pixelate someone",
        usage="avatar pixelate [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def pixelate(self, context: Context, user: discord.User = None) -> None:
        if not user:
            user = context.author

        async with aiohttp.ClientSession() as session:
            img = await session.get(
                f"https://some-random-api.com/canvas/misc/pixelate?avatar={user.display_avatar.url}"
            )

            imageData = io.BytesIO(await img.read())
            await context.send(file=discord.File(imageData, "pixelate.png"))

    @avatar.command(
        name="trigger",
        description="Trigger someone",
        usage="avatar trigger [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def trigger(self, context: Context, user: discord.User = None) -> None:
        if not user:
            user = context.author

        async with aiohttp.ClientSession() as session:
            img = await session.get(
                f"https://some-random-api.com/canvas/overlay/triggered?avatar={user.display_avatar.url}"
            )

            imageData = io.BytesIO(await img.read())
            await context.send(file=discord.File(imageData, "triggered.gif"))

    @avatar.command(
        name="jail",
        description="Put someone in jail",
        usage="avatar jail [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def jail(self, context: Context, user: discord.User = None) -> None:
        if not user:
            user = context.author

        async with aiohttp.ClientSession() as session:
            img = await session.get(
                f"https://some-random-api.com/canvas/overlay/jail?avatar={user.display_avatar.url}"
            )

            imageData = io.BytesIO(await img.read())
            await context.send(file=discord.File(imageData, "jail.png"))

    @avatar.command(
        name="wasted",
        description="Wasted",
        usage="avatar wasted [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def wasted(self, context: Context, user: discord.User = None) -> None:
        if not user:
            user = context.author

        async with aiohttp.ClientSession() as session:
            img = await session.get(
                f"https://some-random-api.com/canvas/overlay/wasted?avatar={user.display_avatar.url}"
            )

            imageData = io.BytesIO(await img.read())
            await context.send(file=discord.File(imageData, "wasted.png"))

    @avatar.command(
        name="passed",
        description="Passed",
        usage="avatar passed [optional: user]"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def passed(self, context: Context, user: discord.User = None) -> None:
        if not user:
            user = context.author

        async with aiohttp.ClientSession() as session:
            img = await session.get(
                f"https://some-random-api.com/canvas/overlay/passed?avatar={user.display_avatar.url}"
            )

            imageData = io.BytesIO(await img.read())
            await context.send(file=discord.File(imageData, "passed.png"))

    @commands.hybrid_group(
        name="random",
        description="Random image commands",
        usage="image random <subcommand>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def random(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}random {cmd.name} - {cmd.description}" for cmd in self.random.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Random", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @random.command(
        name="cat",
        description="Get a random cat image",
        usage="random cat"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def random_cat(self, context: Context) -> None:

        async with aiohttp.ClientSession() as session:
            data = await session.get(
                "https://some-random-api.com/animal/cat"
            )

            data = await data.json()

            await context.send(data["image"])

    @random.command(
        name="dog",
        description="Get a random dog image",
        usage="random dog"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def random_dog(self, context: Context) -> None:

        async with aiohttp.ClientSession() as session:
            data = await session.get(
                "https://some-random-api.com/animal/dog"
            )

            data = await data.json()

            await context.send(data["image"])

    @random.command(
        name="bird",
        description="Get a random bird image",
        usage="random bird"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def random_bird(self, context: Context) -> None:

        async with aiohttp.ClientSession() as session:
            data = await session.get(
                "https://some-random-api.com/animal/bird"
            )

            data = await data.json()

            await context.send(data["image"])

    @commands.hybrid_group(
        name="image",
        description="Commands for image creation",
        usage="image <subcommand>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def image(self, context: Context) -> None:
        prefix = await self.bot.get_prefix(context)

        cmds = "\n".join([f"{prefix}image {cmd.name} - {cmd.description}" for cmd in self.image.walk_commands()])

        embed = discord.Embed(
            title=f"Help: Image", description="List of available commands:", color=0xBEBEFE
        )
        embed.add_field(
            name="Commands", value=f"```{cmds}```", inline=False
        )

        await context.send(embed=embed)

    @image.command(
        name="youtube",
        description="Youtube comment",
        usage="image youtube <user> <text>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def youtube(self, context: Context, user: discord.User, *, text: str) -> None:
        if not user:
            user = context.author

        async with aiohttp.ClientSession() as session:
            img = await session.get(
                f"https://some-random-api.com/canvas/misc/youtube-comment?avatar={user.display_avatar.url}&username={user.display_name}&comment={text}"
            )

            imageData = io.BytesIO(await img.read())
            await context.send(file=discord.File(imageData, "youtube.png"))

    @image.command(
        name="tweet",
        description="Tweet",
        usage="image tweet <user> <text>"
    )
    @commands.check(Checks.is_not_blacklisted)
    async def tweet(self, context: Context, user: discord.User, *, tweet: str) -> None:
        async with aiohttp.ClientSession() as session:
            nick = user.nick if hasattr(user, 'nick') else user.display_name
            if nick == None:
                nick = user.display_name

            img = await session.get(
                f"https://some-random-api.com/canvas/misc/tweet?avatar={user.display_avatar.url}&username={user.global_name if not user.bot else user.display_name}&displayname={nick}&comment={tweet}&replies=-1"
            )

            imageData = io.BytesIO(await img.read())
            await context.send(file=discord.File(imageData, "tweet.png"))

    @commands.hybrid_command(
        name="ttt",
        aliases=["tictactoe"],
        description="Play a game of Tic-Tac-Toe",
        usage="ttt <opponent>"
    )
    @commands.check(Checks.is_not_blacklisted)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def tictactoe(self, context: Context, opponent: discord.User) -> None:
        """Start a game of Tic-Tac-Toe with the specified opponent."""

        if opponent == context.author:
            await context.send("You cannot play against yourself!")
            return

        if opponent.bot:
            await context.send("You cannot play against bots!")
            return

        await context.send(f"{context.author.mention} vs {opponent.mention}!", view=TicTacToeView(context.author, opponent))

# And then we finally add the cog to the bot so that it can load, unload, reload and use it's content.
async def setup(bot) -> None:
    await bot.add_cog(Fun(bot))
