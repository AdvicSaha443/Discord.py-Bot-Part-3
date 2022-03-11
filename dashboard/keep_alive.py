import random
import json

from flask import Flask, request, redirect, render_template, jsonify
from dashboard.routes.discord_oauth import DiscordOauth
from zCommands.zzCommands import Levels, Economy, Dashboard
from threading import Thread
from replit import db

app = Flask(__name__)

codes = []
hm=[]
p=[]
tf=[]

room_available = ['room1', 'room2', 'room3', 'room4', 'room5', 'room6', 'room7', 'room8']

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET'])
def login():
  code = request.args.get('code')
  redirect = request.args.get('redirect')

  if code is None:
    userid = ""
  else:
    access_token = DiscordOauth.get_access_token(code)
    user_object = DiscordOauth.get_user(access_token)

    userid = user_object.get('id')

    with open("jsons/loggedUsers.json", "r") as f:
      data = json.load(f)

    if userid in data:
      pass
    else:
      data[str(userid)] = {}
      data[str(userid)]['avatar'] = user_object.get("avatar")
      data[str(userid)]['name'] = f"{user_object.get('username')}#{user_object.get('discriminator')}"

      with open("jsons/loggedUsers.json", "w") as f:
        json.dump(data, f)
    

  if redirect is None:
    redirect = ""
    
  return render_template('login.html', userid=userid, redirect=redirect)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    code = request.args.get('code')
    access_token = DiscordOauth.get_access_token(code)

    user_object = DiscordOauth.get_user(access_token)

    if user_object.get('banner_color') is None:
      user_banner_color = "#ffffff"
    else:
      user_banner_color = user_object.get('banner_color')

    
    print(user_object)

    user_bank_data = Economy.get_bank_data()[user_object.get('id')]['bank']+Economy.get_bank_data()[user_object.get('id')]['wallet']

    user_rank_card = Levels.make_user_rank_card_just_for_showing_them_lol(user_object.get('id'), f"https://cdn.discordapp.com/avatars/{user_object.get('id')}/{user_object.get('avatar')}.png", f"{user_object.get('username')}#{user_object.get('discriminator')}")

    return render_template('dashboard.html', user_banner_color=user_banner_color, user_id=user_object.get('id'), user_username=f"{user_object.get('username')}#{user_object.get('discriminator')}", user_profile=f"https://cdn.discordapp.com/avatars/{user_object.get('id')}/{user_object.get('avatar')}.png", user_bank_data=user_bank_data, user_rank_card=user_rank_card)

@app.route('/edit-rank-card')
def editrankcard():
  code = request.args.get('code')

  if code is None:
    return redirect('/login?redirect=editrankcard')
  else:
    access_token = DiscordOauth.get_access_token(code)
    user_object = DiscordOauth.get_user(access_token)

    user_rank_card = Levels.make_user_rank_card_just_for_showing_them_lol(user_object.get('id'), f"https://cdn.discordapp.com/avatars/{user_object.get('id')}/{user_object.get('avatar')}.png", f"{user_object.get('username')}#{user_object.get('discriminator')}")

    return render_template('editrankcard.html', user_id=user_object.get('id'), user_username=f"{user_object.get('username')}#{user_object.get('discriminator')}", user_profile=f"https://cdn.discordapp.com/avatars/{user_object.get('id')}/{user_object.get('avatar')}.png", userrankcard=user_rank_card)


@app.route("/errors/limit-exceeded")
def limit_error():
  return render_template('limit_error.html')
  
@app.route("/errors/gift-card-not-found")
def gift_card_not_found_error():
  return render_template('gift_card_error.html')

@app.route("/sbbotgiftcard")
def gift_card_before():
  gift_code = request.args.get("giftcode")
  reward_price_code = request.args.get("p")

  if len(room_available) == 0:
    return redirect('/errors/limit-exceeded')
  else:
    room = room_available[0]
    room_available.remove(room)

  try:
    gift_code_value = db[gift_code]
  except:
    return redirect('/errors/gift-card-not-found')
  
  del db[gift_code]
  db[str(room)]=str(gift_code_value)

  login_for_gift_url=DiscordOauth.get_login_url(gift_code, reward_price_code, room)
  return redirect(login_for_gift_url)

@app.route("/test.sbbotgiftcard")
def giftcard_test():
  gift_code = request.args.get("giftcode")
  print(gift_code)
  userid = request.args.get("userid")

  if userid is None:
    userid = ""
  
  return render_template("gift_card_test.html", gift_code = gift_code, userid = userid)

@app.route("/redeemcode")
def redeemcode():
  gift_code = request.args.get("gift_code")
  print(gift_code)
  user_id = request.args.get("userid")

  try:
    gift_code_value = db[str(gift_code)]
  except Exception as e:
    print(e)
    return redirect('/errors/gift-card-not-found')

  del db[gift_code]
  bal = Economy.update_bank_using_id(str(user_id), int(gift_code_value), mode="bank")
  return render_template("giftcard.html", balance=bal, money_won=gift_code_value)
  
@app.route('/sbbotgift')
def sbbot_gift():
  return redirect('/')

@app.route('/sbbotgift/<room>')
def gift_card_showing(room):
  try:
    reward_price = db[str(room)]
  except:
    return redirect('/errors/gift-card-not-found')

  c = request.args.get("code")
  access_token = DiscordOauth.get_access_token_custom(c, str(room))
  user_object = DiscordOauth.get_user(access_token)
  user_id = user_object.get('id')

  room_available.append(str(room))
  del db[str(room)]

  bal = Economy.update_bank_using_id(str(user_id), int(reward_price), mode="bank")
  return render_template("giftcard.html", balance=bal, money_won=reward_price, username=f"{user_object.get('username')}#{user_object.get('discriminator')}")


@app.route("/generate_code")
def show_code():
  value = request.args.get("w")
  code = Dashboard.generate_new_key(10)
  db[code]=value
  gift_website = f"https://a.advic.repl.co/test.sbbotgiftcard?giftcode={code}"
  return gift_website
  
def create_gift_codes():
  for i in range(0, 100):
    code = Dashboard.generate_new_key(65)
    codes.append(code)

@app.route('/just_random_thing')
def kinda_home():
  return render_template('bot_stuff.html')

@app.route('/just_random_thing/clear_data_base_data/<sure>')
def clear_data_base_data(sure: str):
  if sure == 'sure':
    counter = 0
    for value in db:
      del db[str(value)]
      counter+=1

    return f"Removed"
  else:
    return redirect('/')

@app.route('/create_embed')
def create_embed_start():
  return render_template('embed_form.html')

@app.route('/create_embed/end', methods=["POST"])
def create_embed_end():
  embed_title = request.form.get("embed_title")
  embed_message = request.form.get("embed_message")
  embed_color = request.form.get("embed_color")
  channel_id = request.form.get("channel_id")
  field1 = request.form.get("field1")
  field2 = request.form.get("field2")
  field3 = request.form.get("field3")
  field4 = request.form.get("field4")
  field5 = request.form.get("field5")
  field6 = request.form.get("field6")
  field7 = request.form.get("field7")
  field8 = request.form.get("field8")

  #response = Dashboard.send_embed(embed_title, embed_message, embed_color, channel_id)
  data_raw=f"{embed_title}£{embed_message}£{embed_color}£{channel_id}£embed"
  data=f"{embed_title}£{embed_message}£{embed_color}£{channel_id}£embed£{field1}£{field2}£{field3}£{field4}£{field5}£{field6}£{field7}£{field8}"
  tf.append(data)
  return data

@app.route('/send_message')
def send_embed_start():
  return render_template('message_form.html')

@app.route('/send_message/end', methods=["POST"])
def send_message_end():
  embed_title = request.form.get("embed_title")
  channel_id = request.form.get("channel_id")

  #response = Dashboard.send_embed(embed_title, embed_message, embed_color, channel_id)
  data_raw=f"{embed_title}£skip£skip£{channel_id}£msg"
  data=f"{embed_title}£skip£skip£{channel_id}£msg"
  tf.append(data)
  return data

@app.route('/send_private_message')
def send_private_message_start():
  return render_template('private_message_form.html')

@app.route('/send_private_message/end', methods=["POST"])
def send_private_message_end():
  embed_title = request.form.get("embed_title")
  embed_message = request.form.get("embed_message")
  embed_color = request.form.get("embed_color")
  user_id = request.form.get("user_id")

  #response = Dashboard.send_embed(embed_title, embed_message, embed_color, channel_id)
  data_raw=f"{embed_title}£{embed_message}£{embed_color}£{channel_id}£embed"
  data=f"{embed_title}£{embed_message}£{embed_color}£{user_id}£private_embed"
  tf.append(data)
  return data

def send_private_message():
  return render_template('private_message_form.html')

@app.route("/just_random_thing/requests")
def requests_feed():
  try:
    if tf[0] is None:
      return "NONE"
    else:
      return tf[0]
  except:
    return "NONE"

@app.route("/get_rank_card")
async def get_user_rank_card():
  user_id = request.args.get("user_id")
  avatar = request.args.get("avatar")
  username = request.args.get("username")

  user_rank_card = await Levels.make_user_rank_card_just_for_showing_them_lol(user_id, username, avatar)

  return render_template('renderRankCard.html', user_rank_card = user_rank_card)


@app.route("/just_random_thing/clear_request")
def clear_request():
  try:
    del tf[0]
  except:
    pass
  return "DONE"

@app.route('/create_embed')
def embed_redirect():
  return redirect('/create_embed/start')

@app.route('/send_message')
def message_redirect():
  return redirect('/just_random_thing/send_message/start')

@app.route('/just_random_thing/login')
def login_direct():
  type = request.args.get("redirect")

  if type == "DClogin":
    return redirect(DiscordOauth.login_url)

@app.route("/make_user_rank_card")
async def make_user_rank_card_1():
  user_id = request.args.get("user_id")
  background_image = request.args.get("background")
  blend = request.args.get("blend")
  bar_color = request.args.get("bar_color")
  text_color = request.args.get("text_color")
  normal = request.args.get("normal")
  has_all_value = request.args.get("has_all_value")

  if has_all_value == "false":
    return "doesn't has all value #0"
  else:
    with open("jsons/loggedUsers.json", "r") as f:
      data = json.load(f)

    try:
      if str(user_id) in data:
        avatar = data[str(user_id)]['avatar']
        username = data[str(user_id)]['name']
      else:
        return "you're not logged in"
    except:
      return "user not logged in #1"

    if normal == "true":
      card = await Dashboard.make_user_rank_card(userid=user_id, username=username, avatar=avatar, normal=False)
    else:
      card = await Dashboard.make_user_rank_card(userid=user_id, username=username, avatar=avatar, card=background_image, blend=blend, text_color=text_color, bar_color=bar_color)

      return card
  


create_gift_codes()
def run():  
  app.run(host='0.0.0.0',port=8080) 

def keep_alive():
    t = Thread(target=run)
    t.start()