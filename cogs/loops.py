import discord
import requests
import asyncio
import json
import re
import os
import datetime

from discord.ext import commands, tasks

class Youtube(commands.Cog):
  def __init__(self, bot):
    self.client = bot

  @commands.Cog.listener()
  async def on_ready(self):
    print('Now Checking For Videos!')
    self.checkforvideo.start()

    
  @tasks.loop(seconds = 600)
  async def checkforvideo(self):
    data_raw = requests.get("https://a.advic.repl.co/just_random_thing/requests")
    data2 = data_raw.text

    if str(data2) == "NONE":
        pass
    else:
        nan = requests.get("https://a.advic.repl.co/just_random_thing/clear_request")
        try:
          data_splited = data2.split("£")
          if str(data_splited[4])=="embed":
            embed_title = data_splited[0]
            embed_message = data_splited[1]

            channel_id = data_splited[3]
            channel = self.client.get_channel(int(channel_id))

            embed_color = data_splited[2].split(",")
            mbed = discord.Embed(title=embed_title,
                                description=embed_message,
                                color=discord.Color.from_rgb(
                                    int(embed_color[0]), int(embed_color[1]),
                                    int(embed_color[2])))
            await channel.send(embed=mbed)
          elif str(data_splited[4])=="private_embed":
            embed_title = data_splited[0]
            embed_message = data_splited[1]

            user_id = data_splited[3]
            user = await self.client.fetch_user(int(user_id))

            embed_color = data_splited[2].split(",")
            mbed = discord.Embed(title=embed_title,
                                description=embed_message,
                                color=discord.Color.from_rgb(
                                    int(embed_color[0]), int(embed_color[1]),
                                    int(embed_color[2])))
            await user.send(embed=mbed)
          else:
            message = data_splited[0]

            channel_id = data_splited[3]
            channel = self.client.get_channel(int(channel_id))

            await channel.send(str(message))
            
        except Exception as e:
          print(e)

    now = datetime.datetime.now()
    curmonth = now.month
    curday = now.day
    curyear = now.year

    with open('jsons/birthday.json', 'r') as f:
      var = json.load(f)
      for member in var:
        if var[member]['month'] == curmonth:
          if var[member]['day'] == curday:
            if var[member]['wished'] == 0:
              channel = self.client.get_channel(878999525258330112)
              year = var[member]["year"]
              await channel.send(f"**Happy Birthday <@{member}>!** You're Now {curyear-year} Old!🎉🎊")
              var[member]['wished'] = 1
              with open("jsons/birthday.json", "w") as f:
                json.dump(var, f)
        else:
          if var[member]['wished'] == 1:
            var[member]['wished'] = 0
            with open('jsons/birthday.json', "w") as f:
              json.dump(var, f)

  @commands.command()
  async def run_loops_check(self, ctx):
    await ctx.message.delete()
    data_raw = requests.get("https://a.advic.repl.co/just_random_thing/requests")
    data2 = data_raw.text

    if str(data2) == "NONE":
        pass
    else:
        nan = requests.get("https://a.advic.repl.co/just_random_thing/clear_request")
        try:
          data_splited = data2.split("£")
          if str(data_splited[4])=="embed":
            embed_title = data_splited[0]
            embed_message = data_splited[1]
  
            channel_id = data_splited[3]
            channel = self.client.get_channel(int(channel_id))
  
            embed_color = data_splited[2].split(",")
            mbed = discord.Embed(title=embed_title,
                                description=embed_message,
                                color=discord.Color.from_rgb(
                                    int(embed_color[0]), int(embed_color[1]),
                                    int(embed_color[2])))
            try:
              if data_splited[5] is not None:
                try:
                  if data_splited[6] is not None:
                    try:
                      if data_splited[7] is not None:
                        try:
                          if data_splited[8] is not None:
                            try:
                              if data_splited[9] is not None:
                                try:
                                  if data_splited[10] is not None:
                                    try:
                                      if data_splited[11] is not None:
                                        try:
                                          if data_splited[12] is not None:
                                            print("this?")
                                            fields = [(str(data_splited[5]).split("]")[0], str(data_splited[5]).split("]")[1], False),
                                            (str(data_splited[6]).split("]")[0], str(data_splited[6]).split("]")[1], False),
                                            (str(data_splited[7]).split("]")[0], str(data_splited[7]).split("]")[1], False),
                                            (str(data_splited[8]).split("]")[0], str(data_splited[8]).split("]")[1], False),
                                            (str(data_splited[9]).split("]")[0], str(data_splited[9]).split("]")[1], False),
                                            (str(data_splited[10]).split("]")[0], str(data_splited[10]).split("]")[1], False),
                                            (str(data_splited[11]).split("]")[0], str(data_splited[11]).split("]")[1], False),
                                            (str(data_splited[12]).split("]")[0], str(data_splited[12]).split("]")[1], False)]
  
                                            for name, value, inline in fields:
                                              mbed.add_field(name=name, value=value, inline=inline)
                                        except:
                                          fields = [(str(data_splited[5]).split("]")[0], str(data_splited[5]).split("]")[1], False),
                                          (str(data_splited[6]).split("]")[0], str(data_splited[6]).split("]")[1], False),
                                          (str(data_splited[7]).split("]")[0], str(data_splited[7]).split("]")[1], False),
                                          (str(data_splited[8]).split("]")[0], str(data_splited[8]).split("]")[1], False),
                                          (str(data_splited[9]).split("]")[0], str(data_splited[9]).split("]")[1], False),
                                          (str(data_splited[10]).split("]")[0], str(data_splited[10]).split("]")[1], False),
                                          (str(data_splited[11]).split("]")[0], str(data_splited[11]).split("]")[1], False)]
  
                                          for name, value, inline in fields:
                                            mbed.add_field(name=name, value=value, inline=inline)
                                    except:
                                      fields = [(str(data_splited[5]).split("]")[0], str(data_splited[5]).split("]")[1], False),
                                      (str(data_splited[6]).split("]")[0], str(data_splited[6]).split("]")[1], False),
                                      (str(data_splited[7]).split("]")[0], str(data_splited[7]).split("]")[1], False),
                                      (str(data_splited[8]).split("]")[0], str(data_splited[8]).split("]")[1], False),
                                      (str(data_splited[9]).split("]")[0], str(data_splited[9]).split("]")[1], False),
                                      (str(data_splited[10]).split("]")[0], str(data_splited[10]).split("]")[1], False)]
  
                                      for name, value, inline in fields:
                                        mbed.add_field(name=name, value=value, inline=inline)
                                except:
                                  fields = [(str(data_splited[5]).split("]")[0], str(data_splited[5]).split("]")[1], False),
                                  (str(data_splited[6]).split("]")[0], str(data_splited[6]).split("]")[1], False),
                                  (str(data_splited[7]).split("]")[0], str(data_splited[7]).split("]")[1], False),
                                  (str(data_splited[8]).split("]")[0], str(data_splited[8]).split("]")[1], False),
                                  (str(data_splited[9]).split("]")[0], str(data_splited[9]).split("]")[1], False)]
  
                                  for name, value, inline in fields:
                                    mbed.add_field(name=name, value=value, inline=inline)
                            except:
                              fields = [(str(data_splited[5]).split("]")[0], str(data_splited[5]).split("]")[1], False),
                              (str(data_splited[6]).split("]")[0], str(data_splited[6]).split("]")[1], False),
                              (str(data_splited[7]).split("]")[0], str(data_splited[7]).split("]")[1], False),
                              (str(data_splited[8]).split("]")[0], str(data_splited[8]).split("]")[1], False)]
  
                              for name, value, inline in fields:
                                mbed.add_field(name=name, value=value, inline=inline)
                        except:
                          fields = [(str(data_splited[5]).split("]")[0], str(data_splited[5]).split("]")[1], False),
                          (str(data_splited[6]).split("]")[0], str(data_splited[6]).split("]")[1], False),
                          (str(data_splited[7]).split("]")[0], str(data_splited[7]).split("]")[1], False)]
  
                          for name, value, inline in fields:
                            mbed.add_field(name=name, value=value, inline=inline)
                    except:
                      fields = [(str(data_splited[5]).split("]")[0], str(data_splited[5]).split("]")[1], False),
                      (str(data_splited[6]).split("]")[0], str(data_splited[6]).split("]")[1], False)]
  
                      for name, value, inline in fields:
                        mbed.add_field(name=name, value=value, inline=inline)
                except:
                  fields = [(str(data_splited[5]).split("]")[0], str(data_splited[5]).split("]")[1], False)]
  
                  for name, value, inline in fields:
                    mbed.add_field(name=name, value=value, inline=inline)
            except Exception as e:
              print(e)
                                  
            await channel.send(embed=mbed)
          elif str(data_splited[4])=="private_embed":
            embed_title = data_splited[0]
            embed_message = data_splited[1]

            user_id = data_splited[3]
            user = await self.client.fetch_user(int(user_id))

            embed_color = data_splited[2].split(",")
            mbed = discord.Embed(title=embed_title,
                                description=embed_message,
                                color=discord.Color.from_rgb(
                                    int(embed_color[0]), int(embed_color[1]),
                                    int(embed_color[2])))
            await user.send(embed=mbed)
          else:
            message = data_splited[0]

            channel_id = data_splited[3]
            channel = self.client.get_channel(int(channel_id))

            await channel.send(str(message))
            
        except Exception as e:
          print(e)

    now = datetime.datetime.now()
    curmonth = now.month
    curday = now.day
    curyear = now.year

    with open('jsons/birthday.json', 'r') as f:
      var = json.load(f)
      for member in var:
        if var[member]['month'] == curmonth:
          if var[member]['day'] == curday:
            if var[member]['wished'] == 0:
              channel = self.client.get_channel(878999525258330112)
              year = var[member]["year"]
              await channel.send(f"**Happy Birthday <@{member}>!** You're Now {curyear-year} Old!🎉🎊")
              var[member]['wished'] = 1
              with open("jsons/birthday.json", "w") as f:
                json.dump(var, f)
        else:
          if var[member]['wished'] == 1:
            var[member]['wished'] = 0
            with open('jsons/birthday.json', "w") as f:
              json.dump(var, f)



  

def setup(client):
  client.add_cog(Youtube(client))
