#this code won't work for wavelink version - 1.0.0 and above

import asyncio
import datetime as dt
import random
import time
import re
import os
import json
import typing as t
import aiohttp
import discord
import subprocess
import wavelink

from discord.colour import Color
from discord.ext import commands
from wavelink.errors import BuildTrackError
from threading import Thread
from enum import Enum

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
LYRICS_URL = "https://some-random-api.ml/lyrics?title="
HZ_BANDS = (20, 40, 63, 100, 150, 250, 400, 450, 630, 1000, 1600, 2500, 4000, 10000, 16000)
TIME_REGEX = r"([0-9]{1,2})[:ms](([0-9]{1,2})s?)?"
connection_status="not-connected"
OPTIONS = {
    "1️⃣": 0,
    "2⃣": 1,
    "3⃣": 2,
    "4⃣": 3,
    "5⃣": 4,
}

current_playing_text_channel = []


class AlreadyConnectedToChannel(commands.CommandError):
    pass


class NoVoiceChannel(commands.CommandError):
    pass


class QueueIsEmpty(commands.CommandError):
    pass


class NoTracksFound(commands.CommandError):
    pass


class PlayerIsAlreadyPaused(commands.CommandError):
    pass


class NoMoreTracks(commands.CommandError):
    pass


class NoPreviousTracks(commands.CommandError):
    pass


class InvalidRepeatMode(commands.CommandError):
    pass


class VolumeTooLow(commands.CommandError):
    pass


class VolumeTooHigh(commands.CommandError):
    pass


class MaxVolume(commands.CommandError):
    pass


class MinVolume(commands.CommandError):
    pass


class NoLyricsFound(commands.CommandError):
    pass


class InvalidEQPreset(commands.CommandError):
    pass


class NonExistentEQBand(commands.CommandError):
    pass


class EQGainOutOfBounds(commands.CommandError):
    pass


class InvalidTimeString(commands.CommandError):
    pass


class RepeatMode(Enum):
    NONE = 0
    ONE = 1
    ALL = 2


class Queue:
    def __init__(self):
        self._queue = []
        self.position = 0
        self.repeat_mode = RepeatMode.NONE

    @property
    def is_empty(self):
        return not self._queue

    @property
    def first_track(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[0]

    @property
    def current_track(self):
        if not self._queue:
            raise QueueIsEmpty

        if self.position <= len(self._queue) - 1:
            return self._queue[self.position]

    @property
    def upcoming(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[self.position + 1:]

    @property
    def history(self):
        if not self._queue:
            raise QueueIsEmpty

        return self._queue[:self.position]

    @property
    def length(self):
        return len(self._queue)

    def add(self, *args):
        self._queue.extend(args)

    def get_next_track(self):
        if not self._queue:
            raise QueueIsEmpty

        self.position += 1

        if self.position < 0:
            return None
        elif self.position > len(self._queue) - 1:
            if self.repeat_mode == RepeatMode.ALL:
                self.position = 0
            else:
                return None

        return self._queue[self.position]

    def shuffle(self):
        if not self._queue:
            raise QueueIsEmpty

        upcoming = self.upcoming
        random.shuffle(upcoming)
        self._queue = self._queue[:self.position + 1]
        self._queue.extend(upcoming)

    def set_repeat_mode(self, mode):
        if mode == "none":
            self.repeat_mode = RepeatMode.NONE
        elif mode == "track" or mode == "t":
            self.repeat_mode = RepeatMode.ONE
        elif mode == "queue" or mode == "q":
            self.repeat_mode = RepeatMode.ALL

    def empty(self):
        self._queue.clear()
        self.position = 0


class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = Queue()
        self.eq_levels = [0.] * 15

    async def connect(self, ctx, channel=None):
        if self.is_connected:
            raise AlreadyConnectedToChannel

        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            raise NoVoiceChannel

        await super().connect(channel.id)
        return channel

    async def teardown(self):
      try:
        await self.destroy()
      except KeyError:
        pass

    async def add_tracks(self, ctx, tracks):
        if not tracks:
            await ctx.send("No Tracks Found")

        if isinstance(tracks, wavelink.TrackPlaylist):
            self.queue.add(*tracks.tracks)
        elif len(tracks) == 1:
            self.queue.add(tracks[0])
            mbed = discord.Embed(
              title=f"Added {tracks[0].title} to the queue",
              color = discord.Color.teal()
            )
            await ctx.send(embed=mbed)
        else:
            if (track := await self.choose_track(ctx, tracks)) is not None:
                self.queue.add(track)
                mbed = discord.Embed(
                  title=f"Added {tracks[0].title} to the queue",
                  color = discord.Color.teal()
                )
                await ctx.send(embed=mbed)

        if not self.is_playing and not self.queue.is_empty:
            await self.start_playback()

    async def choose_track(self, ctx, tracks):
        def _check(r, u):
            return (
                r.emoji in OPTIONS.keys()
                and u == ctx.author
                and r.message.id == msg.id
            )

        embed = discord.Embed(
            title="Choose a song",
            description=(
                "\n".join(
                    f"**{i+1}.** {t.title} ({t.length//60000}:{str(t.length%60).zfill(2)})"
                    for i, t in enumerate(tracks[:5])
                )
            ),
            colour=ctx.author.colour,
            timestamp=dt.datetime.utcnow()
        )
        embed.set_author(name="Query Results")
        embed.set_footer(text=f"Invoked by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        msg = await ctx.send(embed=embed)
        for emoji in list(OPTIONS.keys())[:min(len(tracks), len(OPTIONS))]:
            await msg.add_reaction(emoji)

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=_check)
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.message.delete()
        else:
            await msg.delete()
            return tracks[OPTIONS[reaction.emoji]]

    async def start_playback(self):
        await self.play(self.queue.current_track)

    async def advance(self):
        try:
            if (track := self.queue.get_next_track()) is not None:
                
                await self.play(track)
                return track
        except QueueIsEmpty:
            pass

    async def repeat_track(self):
        await self.play(self.queue.current_track)


class Music(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, bot):
        self.bot = bot
        print("Starting Lavalink")
        def connection():
          os.system("java -jar Lavalink.jar")
        connection_status = "connecting"
        Thread(target = connection).start()
        time.sleep(58)
        print("Loaded Lavalink")
        self.wavelink = wavelink.Client(bot=bot)
        self.bot.loop.create_task(self.start_nodes())
        print(connection_status)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot]:
                await self.get_player(member.guild).teardown()

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        connection_status = "connected"
        print(f" Wavelink node `{node.identifier}` ready.")

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    @wavelink.WavelinkMixin.listener("on_track_exception")
    async def on_player_stop(self, node, payload):
        if payload.player.queue.repeat_mode == RepeatMode.ONE:
            await payload.player.repeat_track()
        else:
            await payload.player.advance()

    @wavelink.WavelinkMixin.listener("on_track_end")
    async def on_player_stop_np(self, node, payload):
        if payload.player.queue.repeat_mode == RepeatMode.ONE:
            await payload.player.repeat_track()
        else:
            track = await payload.player.advance()

            if track is None:
              return
            else:

              channelid = current_playing_text_channel[0]
              channel = self.bot.get_channel(int(channelid))

              mbed = discord.Embed(
                title=f"Now Playing {track}",
                color = discord.Color.teal()
              )

              await channel.send(embed=mbed)

            

    async def cog_check(self, ctx):
        if isinstance(ctx.channel, discord.DMChannel):
            await ctx.send("Music commands are not available in DMs.")
            return False

        return True

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        nodes = {
            "MAIN": {
                "host": "127.0.0.1",
                "port": 2333,
                "rest_uri": "http://127.0.0.1:2333",
                "password": "youshallnotpass",
                "identifier": "MAIN",
                "region": "asia",
            }
        }

        for node in nodes.values():
            await self.wavelink.initiate_node(**node)

    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    @commands.command(name="connect_to_lavalink", aliases=["ctl"])
    async def connect_to_lavalink(self, ctx):
      self.bot.loop.create_task(self.start_nodes())
      await ctx.send("Bot should be connected to Lavalink Now")

    @commands.command(name="connect", aliases=["join", "summon"])
    async def connect_command(self, ctx, *, channel: t.Optional[discord.VoiceChannel]):
        player = self.get_player(ctx)
        channel = await player.connect(ctx, channel)
        mbed = discord.Embed(
          title=f"Connected To {channel.name}",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="disconnect", aliases=["leave"])
    async def disconnect_command(self, ctx):
        player = self.get_player(ctx)
        await player.teardown()
        mbed = discord.Embed(
          title=f"Disconnected",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="play", aliases=["yt", "search"])
    async def play_command(self, ctx, *, query: t.Optional[str]):
        player = self.get_player(ctx)

        if len(current_playing_text_channel) == 0:
          pass
        else:
          del current_playing_text_channel[0]
        
        current_playing_text_channel.append(ctx.channel.id)
        if not player.is_connected:
            await player.connect(ctx)

        if query is None:
            if player.queue.is_empty:
                raise QueueIsEmpty

            await player.set_pause(False)
            mbed = discord.Embed(
              title=f"Playback Resumed",
              color = discord.Color.teal()
            )
            await ctx.send(embed=mbed)

        else:
            query = query.strip("<>")
            if not re.match(URL_REGEX, query):
                query = f"ytsearch:{query}"

            await player.add_tracks(ctx, await self.wavelink.get_tracks(query))

    @commands.command(name="pause")
    async def pause_command(self, ctx):
        player = self.get_player(ctx)

        if player.is_paused:
            raise PlayerIsAlreadyPaused

        await player.set_pause(True)

        mbed = discord.Embed(
          title=f"Playback Paused",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="stop")
    async def stop_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.empty()
        await player.stop()

        mbed = discord.Embed(
          title=f"Playback Stopped",
          description="Queue Also Got Reset",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="next", aliases=["skip"])
    async def next_command(self, ctx):
        player = self.get_player(ctx)

        if not player.queue.upcoming:
            raise NoMoreTracks

        await player.stop()

        mbed = discord.Embed(
          title=f"Playing Next Track In Queue",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="previous", aliases=["pre"])
    async def previous_command(self, ctx):
        player = self.get_player(ctx)

        if not player.queue.history:
            raise NoPreviousTracks

        player.queue.position -= 2
        await player.stop()

        mbed = discord.Embed(
          title=f"Playing Previous Track In The Queue",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="shuffle")
    async def shuffle_command(self, ctx):
        player = self.get_player(ctx)
        player.queue.shuffle()

        mbed = discord.Embed(
          title=f"Queue Shuffled",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="repeat", aliases=["loop"])
    async def repeat_command(self, ctx, mode=None):
      if mode is None:
        emojis_list = ["🇹", "🇶", "❌"]

        mbed = discord.Embed(
          title="Select Repeat Mode: ",
          color=discord.Color.teal()
        )
        mbed.add_field(name="Put The Current Track In Repeat Mode: ", value="🇹", inline=False)
        mbed.add_field(name="Put The Queue In Repeat Mode: ", value="🇶", inline=False)
        mbed.add_field(name="Remove Repeat Mode: ", value="❌", inline=False)

        msg = await ctx.send(embed=mbed)

        for emoji in emojis_list:
          await msg.add_reaction(emoji)

        emojis_dict = {
          "🇶": "queue",
          "🇹": "track",
          "❌": "none"
        }

        def _check(r, u):
          return (
              str(r.emoji) in emojis_list
              and u == ctx.author
              and r.message.id == msg.id
          )

        try:
          reaction, _ = await self.bot.wait_for("reaction_add", timeout=20.0, check=_check)
        except asyncio.TimeoutError:
          pass
        else:
          reaction_type = emojis_dict.get(str(reaction.emoji))
          player = self.get_player(ctx)
          
          if reaction_type == "track":
            player.queue.set_repeat_mode("track")

            mbed1 = discord.Embed(title="The Repeat mode is now in **Current Track**", color=discord.Color.teal())
            await ctx.send(embed=mbed1)
          elif reaction_type == "queue":
            player.queue.set_repeat_mode("queue")

            mbed2 = discord.Embed(title="The Repeat mode is now in **Queue**", color=discord.Color.teal())
            await ctx.send(embed = mbed2)
          else:
            player.queue.set_repeat_mode("none")

            mbed3 = discord.Embed(title="The Repeat mode is now in **None**", color=discord.Color.teal())
            await ctx.send(embed=mbed3)

        return
        
      else:
        if mode not in ("none", "q", "t", "queue", "track"):
          emojis_list = ["🇹", "🇶", "❌"]

          mbed = discord.Embed(
            title="Select Repeat Mode: ",
            color=discord.Color.teal()
          )
          mbed.add_field(name="Put The Current Track In Repeat Mode: ", value="🇹", inline=False)
          mbed.add_field(name="Put The Queue In Repeat Mode: ", value="🇶", inline=False)
          mbed.add_field(name="Remove Repeat Mode: ", value="❌", inline=False)
  
          msg = await ctx.send(embed=mbed)
  
          for emoji in emojis_list:
            await msg.add_reaction(emoji)
  
          emojis_dict = {
            "🇶": "queue",
            "🇹": "track",
            "❌": "none"
          }
  
          def _check(r, u):
            return (
                str(r.emoji) in emojis_list
                and u == ctx.author
                and r.message.id == msg.id
            )
  
          try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=20.0, check=_check)
          except asyncio.TimeoutError:
            pass
          else:
            reaction_type = emojis_dict.get(str(reaction.emoji))
            player = self.get_player(ctx)
            
            if reaction_type == "track":
              player.queue.set_repeat_mode("track")
  
              mbed1 = discord.Embed(title="The Repeat mode is now in **Current Track**", color=discord.Color.teal())
              await ctx.send(embed=mbed1)
            elif reaction_type == "queue":
              player.queue.set_repeat_mode("queue")
  
              mbed2 = discord.Embed(title="The Repeat mode is now in **Queue**", color=discord.Color.teal())
              await ctx.send(embed = mbed2)
            else:
              player.queue.set_repeat_mode("none")
  
              mbed3 = discord.Embed(title="The Repeat mode is now in **None**", color=discord.Color.teal())
              await ctx.send(embed=mbed3)

          return
  
        player = self.get_player(ctx)
        player.queue.set_repeat_mode(mode)
        if mode == "q":
          mode = "queue"
        elif mode == "t":
          mode = "Current Track"
  
        mbed = discord.Embed(
          title=f"The Repeat Mode Has Been Set To {mode}",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="queue")
    async def queue_command(self, ctx, show: t.Optional[int] = 10):
      player = self.get_player(ctx)

      if player.queue.is_empty:
          raise QueueIsEmpty

      embed = discord.Embed(
          title="Queue",
          description=f"Showing up to next {show} tracks",
          colour=ctx.author.colour,
          timestamp=dt.datetime.utcnow()
      )
      embed.set_author(name="Query Results")
      embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
      embed.add_field(
          name="Currently playing",
          value=getattr(player.queue.current_track, "title", "No tracks currently playing."),
          inline=False
      )
      if upcoming := player.queue.upcoming:
          embed.add_field(
              name="Next up",
              value="\n".join(t.title for t in upcoming[:show]),
              inline=False
          )

      msg = await ctx.send(embed=embed)
      
      emojis_list = ["◀️", "▶️"]
      emojis_dict = {
        "◀️": "back",
        "▶️": "next"
      }

      for emoji in emojis_list:
        await msg.add_reaction(emoji)

      pages = int(len(upcoming)/10)
      current_page = 0
      showing = 10

      def _check(r, u):
        return(
          str(r.emoji) in emojis_list
          and u == ctx.author
          and r.message.id == msg.id
        )
        
      for i in range(pages):
        try:
          reaction, _ = await self.bot.wait_for("reaction_add", timeout=10.0, check=_check)
        except asyncio.TimeoutError:
          break
        else:
          reaction_type = emojis_dict.get(str(reaction.emoji))

          ## other code for changing the page
          if reaction_type == "back" and current_page == 0:
            continue
          elif reaction_type == "back" and not current_page == 0:
            ## add code here for going back

            new_embed = discord.Embed(
              title="Queue",
              description=f"Showing up to next {showing-10} tracks",
              colour=ctx.author.colour,
              timestamp=dt.datetime.utcnow()
            )
            new_embed.set_author(name="Query Results")
            new_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            new_embed.add_field(
              name="Next up",
              value="\n".join(t.title for t in upcoming[(showing-10):showing]),
              inline=False
            )

            showing=-10
            current_page=-1
          elif reaction_type == "next" and current_page == pages:
            continue
          elif reaction_type == "next" and not current_page == pages:
            new_embed = discord.Embed(
              title="Queue",
              description=f"Showing up to next {showing+10} tracks",
              colour=ctx.author.colour,
              timestamp=dt.datetime.utcnow()
            )
            new_embed.set_author(name="Query Results")
            new_embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
            new_embed.add_field(
              name="Next up",
              value="\n".join(t.title for t in upcoming[showing:(showing+10)]),
              inline=False
            )
            msg.edit(embed = new_embed)
            showing+=10
            current_page+=1


    @commands.group(name="volume", aliases=["vol"], invoke_without_command=True)
    async def volume_group(self, ctx, volume: int):
        player = self.get_player(ctx)

        if volume < 0:
            raise VolumeTooLow

        if volume > 150:
            raise VolumeTooHigh

        await player.set_volume(volume)

        mbed = discord.Embed(
          title=f"Volume Has Been Set To {volume:,}%",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @volume_group.command(name="up")
    async def volume_up_command(self, ctx):
        player = self.get_player(ctx)

        if player.volume == 150:
            raise MaxVolume

        await player.set_volume(value := min(player.volume + 10, 150))
        await ctx.send(f"Volume set to {value:,}%")

    @volume_group.command(name="down")
    async def volume_down_command(self, ctx):
        player = self.get_player(ctx)

        if player.volume == 0:
            raise MinVolume

        await player.set_volume(value := max(0, player.volume - 10))
        await ctx.send(f"Volume set to {value:,}%")

    @commands.command(name="lyrics")
    async def lyrics_command(self, ctx, name: t.Optional[str]):
        player = self.get_player(ctx)
        name = name or player.queue.current_track.title

        async with ctx.typing():
            async with aiohttp.request("GET", LYRICS_URL + name, headers={}) as r:
                if not 200 <= r.status <= 299:
                    raise NoLyricsFound

                data = await r.json()

                if len(data["lyrics"]) > 2000:
                    return await ctx.send(f"<{data['links']['genius']}>")

                embed = discord.Embed(
                    title=data["title"],
                    description=data["lyrics"],
                    colour=discord.Color.teal(),
                    timestamp=dt.datetime.utcnow(),
                )
                embed.set_thumbnail(url=data["thumbnail"]["genius"])
                embed.set_author(name=data["author"])
                await ctx.send(embed=embed)

    @commands.command(name="eq")
    async def eq_command(self, ctx, preset: str):
        player = self.get_player(ctx)

        eq = getattr(wavelink.eqs.Equalizer, preset, None)
        if not eq:
            raise InvalidEQPreset

        await player.set_eq(eq())
        await ctx.send(f"Equaliser adjusted to the {preset} preset.")

    @commands.command(name="adveq", aliases=["aeq"])
    async def adveq_command(self, ctx, band: int, gain: float):
        player = self.get_player(ctx)

        if not 1 <= band <= 15 and band not in HZ_BANDS:
            raise NonExistentEQBand

        if band > 15:
            band = HZ_BANDS.index(band) + 1

        if abs(gain) > 10:
            raise EQGainOutOfBounds

        player.eq_levels[band - 1] = gain / 10
        eq = wavelink.eqs.Equalizer(levels=[(i, gain) for i, gain in enumerate(player.eq_levels)])
        await player.set_eq(eq)
        await ctx.send("Equaliser adjusted.")

    @commands.command(name="playing", aliases=["np", "now", "nowplaying"])
    async def playing_command(self, ctx):
        player = self.get_player(ctx)

        if not player.is_playing:
            raise PlayerIsAlreadyPaused

        embed = discord.Embed(
            title="Now playing",
            colour=discord.Color.teal(),
            timestamp=dt.datetime.utcnow(),
        )
        embed.set_author(name="Playback Information")
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
        embed.add_field(name="Track title", value=player.queue.current_track.title, inline=False)
        embed.add_field(name="Artist", value=player.queue.current_track.author, inline=False)

        position = divmod(player.position, 60000)
        length = divmod(player.queue.current_track.length, 60000)
        embed.add_field(
            name="Position",
            value=f"{int(position[0])}:{round(position[1]/1000):02}/{int(length[0])}:{round(length[1]/1000):02}",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="skipto", aliases=["playindex"])
    async def skipto_command(self, ctx, index: int):
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        if not 0 <= index <= player.queue.length:
            raise NoMoreTracks

        player.queue.position = index - 2
        await player.stop()

        mbed = discord.Embed(
          title=f"Playing Track In Position {index}",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="restart")
    async def restart_command(self, ctx):
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        await player.seek(0)

        mbed = discord.Embed(
          title=f"Retarted Track",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="seek")
    async def seek_command(self, ctx, position: str):
        player = self.get_player(ctx)

        if player.queue.is_empty:
            raise QueueIsEmpty

        if not (match := re.match(TIME_REGEX, position)):
            raise InvalidTimeString

        if match.group(3):
            secs = (int(match.group(1)) * 60) + (int(match.group(3)))
        else:
            secs = int(match.group(1))

        await player.seek(secs * 1000)

        mbed = discord.Embed(
          title=f"Seeked To {position}",
          color = discord.Color.teal()
        )
        await ctx.send(embed=mbed)

    @commands.command(name="save_playlist")
    async def save_playlist(self, ctx, playlist = None, playlist_name = None):
      if playlist is None:
        await ctx.send("Please Provide A Youtube Playlist Link")
        return
      elif playlist_name is None:
        await ctx.send("Please Provide A Name For Your Playlist")
        return
      else:
        with open("jsons/playlist.json", "r") as f:
          data = json.load(f)
        
        if str(ctx.author.id) in data:
          await ctx.send("You already have one playlist saved \n If you want to replace the playlist link then use ?change_playlist command with new playlist link")
          return
        else:
          data[str(ctx.author.id)] = {}
          data[str(ctx.author.id)]['playlist_name'] = playlist_name
          data[str(ctx.author.id)]['playlist_link'] = playlist

          with open("jsons/playlist.json", "w") as f:
            json.dump(data, f)

          await ctx.send("Your playlist was saved \n *make sure that your playlist is public or unlisted*")

    @commands.command(name="change_playlist")
    async def change_playlist(self, ctx, playlist = None, playlist_name = None):
      if playlist is None:
        await ctx.send("Please Provide Your New Youtube Playlist Link")
        return
      elif playlist_name is None:
        await ctx.send("Please Provite Your New Youtube Playlist Name")
        return
      else:
        with open("jsons/playlist.json", "r") as f:
          data = json.load(f)

        try:
          del data[str(ctx.author.id)]
        except:
          pass
        
        data[str(ctx.author.id)] = {}
        data[str(ctx.author.id)]['playlist_name'] = playlist_name
        data[str(ctx.author.id)]['playlist_link'] = playlist

        with open("jsons/playlist.json", "w") as f:
          json.dump(data, f)

        await ctx.send("Your playlist was changed")

    @commands.command(name="get_playlist", aliases=["gp"])
    async def get_playlist(self, ctx, userr: t.Optional[discord.Member]):
      member = userr or ctx.author

      with open("jsons/playlist.json", "r") as f:
        data = json.load(f)

      if str(member.id) in data:
        mbed = discord.Embed(
          title = f"**{member.name}'s Youtube Playlist**",
          color = discord.Color.teal()
        )
        fields = [("Playlist Name: ", f"{data[str(member.id)]['playlist_name']}", True),
        ("Playlist Link: ", f"{data[str(member.id)]['playlist_link']}", True),
        ("React With ▶️ To Queue This Playlist", "You have 20 Seconds", False),
        ("React With 🔂 To Queue And Shuffle This Playlist", "You Have 20 Seconds", False)]
        
        for name, value, inline in fields:
          mbed.add_field(name=name, value=value, inline=inline)

        mbed.set_footer(text="Bot Not Playing Music? Your Playlist Must Be Public Or Unlisted", icon_url="https://cdn.discordapp.com/attachments/822717749725757460/874358230199992360/unknown.png")
        
        msg = await ctx.send(embed=mbed)

        emojis_list = ["▶️", "🔂"]
        emojis_dict = {
          "▶️": "queue",
          "🔂": "shuffle"
        }

        for emoji in emojis_list:
          await msg.add_reaction(emoji)

        def _check(r, u):
          return (
              str(r.emoji) in emojis_list
              and u == ctx.author
              and r.message.id == msg.id
          )

        try:
          reaction, _ = await self.bot.wait_for("reaction_add", timeout=20.0, check=_check)
        except asyncio.TimeoutError:
          pass
        else:
          reaction_type = emojis_dict.get(str(reaction.emoji))

          if reaction_type == "queue":
            query = str(data[str(member.id)]['playlist_link'])

            player = self.get_player(ctx)

            if len(current_playing_text_channel) == 0:
              pass
            else:
              del current_playing_text_channel[0]
            
            current_playing_text_channel.append(ctx.channel.id)
            if not player.is_connected:
                await player.connect(ctx)

            if query is None:
                if player.queue.is_empty:
                    raise QueueIsEmpty

                await player.set_pause(False)
                mbed = discord.Embed(
                  title=f"Playback Resumed",
                  color = discord.Color.teal()
                )
                await ctx.send(embed=mbed)

            else:
                query = query.strip("<>")
                if not re.match(URL_REGEX, query):
                    query = f"ytsearch:{query}"

                await player.add_tracks(ctx, await self.wavelink.get_tracks(query))
          else:
            query = str(data[str(member.id)]['playlist_link'])

            player = self.get_player(ctx)

            if len(current_playing_text_channel) == 0:
              pass
            else:
              del current_playing_text_channel[0]
            
            current_playing_text_channel.append(ctx.channel.id)
            if not player.is_connected:
                await player.connect(ctx)

            if query is None:
                if player.queue.is_empty:
                    raise QueueIsEmpty

                await player.set_pause(False)
                mbed = discord.Embed(
                  title=f"Playback Resumed",
                  color = discord.Color.teal()
                )
                await ctx.send(embed=mbed)

            else:
                query = query.strip("<>")
                if not re.match(URL_REGEX, query):
                    query = f"ytsearch:{query}"

                await player.add_tracks(ctx, await self.wavelink.get_tracks(query))
                player.queue.shuffle()

                if not player.queue.upcoming:
                  raise NoMoreTracks

                await player.stop()

      else:
        await ctx.send(f"{member.name} Don't Have Any playlist saved")

    #ERRORS


    @connect_command.error
    async def connect_command_error(self, ctx, exc):
        if isinstance(exc, AlreadyConnectedToChannel):
            mbed = discord.Embed(
              title=f"Already connected to a voice channel",
              color = discord.Color.teal()
            )
            await ctx.send(embed=mbed)
        elif isinstance(exc, NoVoiceChannel):
            mbed = discord.Embed(
               title=f"No suitable voice channel was provided",
               color = discord.Color.teal()
            )
            await ctx.send(embed=mbed)

    @play_command.error
    async def play_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("No songs to play as the queue is empty.")
        elif isinstance(exc, NoVoiceChannel):
            await ctx.send("No suitable voice channel was provided.")
    
    @pause_command.error
    async def pause_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("Already paused.")

    @next_command.error
    async def next_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("This could not be executed as the queue is currently empty.")
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("There are no more tracks in the queue.")

    @previous_command.error
    async def previous_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("This could not be executed as the queue is currently empty.")
        elif isinstance(exc, NoPreviousTracks):
            await ctx.send("There are no previous tracks in the queue.")

    @shuffle_command.error
    async def shuffle_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue could not be shuffled as it is currently empty.")
    
    @queue_command.error
    async def queue_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("The queue is currently empty.")
    
    @volume_group.error
    async def volume_group_error(self, ctx, exc):
        if isinstance(exc, VolumeTooLow):
            await ctx.send("The volume must be 0% or above.")
        elif isinstance(exc, VolumeTooHigh):
            await ctx.send("The volume must be 150% or below.")

    @volume_up_command.error
    async def volume_up_command_error(self, ctx, exc):
        if isinstance(exc, MaxVolume):
            await ctx.send("The player is already at max volume.")

    @volume_down_command.error
    async def volume_down_command_error(self, ctx, exc):
        if isinstance(exc, MinVolume):
            await ctx.send("The player is already at min volume.")
    
    @lyrics_command.error
    async def lyrics_command_error(self, ctx, exc):
        if isinstance(exc, NoLyricsFound):
            await ctx.send("No lyrics could be found.")
    
    @eq_command.error
    async def eq_command_error(self, ctx, exc):
        if isinstance(exc, InvalidEQPreset):
            await ctx.send("The EQ preset must be either 'flat', 'boost', 'metal', or 'piano'.")
    
    @adveq_command.error
    async def adveq_command_error(self, ctx, exc):
        if isinstance(exc, NonExistentEQBand):
            await ctx.send(
                "This is a 15 band equaliser -- the band number should be between 1 and 15, or one of the following "
                "frequencies: " + ", ".join(str(b) for b in HZ_BANDS)
            )
        elif isinstance(exc, EQGainOutOfBounds):
            await ctx.send("The EQ gain for any band should be between 10 dB and -10 dB.")
    
    @playing_command.error
    async def playing_command_error(self, ctx, exc):
        if isinstance(exc, PlayerIsAlreadyPaused):
            await ctx.send("There is no track currently playing.")

    @skipto_command.error
    async def skipto_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("There are no tracks in the queue")
        elif isinstance(exc, NoMoreTracks):
            await ctx.send("That index is out of the bounds of the queue")

    @restart_command.error
    async def restart_command_error(self, ctx, exc):
        if isinstance(exc, QueueIsEmpty):
            await ctx.send("There are no tracks in the queue")

    

def setup(bot):
    bot.add_cog(Music(bot))
