import os
import requests
import pandas as pd
import telebot
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# 
bot = telebot.TeleBot("API")

# 
currency = None

# 
last_usage_times = {}

def fetch_binance_data(symbol, interval, limit):
    # URL 
    url = f"https://api.binance.com/api/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()

    #  DataFrame
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])

    # 
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

    return df

def save_to_csv(df, file_path):
    #  CSV
    df.to_csv(file_path)
    return file_path

def generate_currency_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    btn_ada = telebot.types.InlineKeyboardButton('ADA Data', callback_data='ada')
    btn_btc = telebot.types.InlineKeyboardButton('BTC Data', callback_data='btc')
    btn_eth = telebot.types.InlineKeyboardButton('ETH Data', callback_data='eth')
    markup.add(btn_ada, btn_btc, btn_eth)
    return markup

def generate_time_frame_markup():
    markup = telebot.types.InlineKeyboardMarkup()

    btn_1h = telebot.types.InlineKeyboardButton('1 hour', callback_data='1h')
    btn_4h = telebot.types.InlineKeyboardButton('4 hours', callback_data='4h')
    btn_1d = telebot.types.InlineKeyboardButton('1 day', callback_data='1d')
    markup.add(btn_1h, btn_4h, btn_1d)
    return markup

def plot_chart(data):
    x = np.arange(len(data))
    y = data

    plt.plot(x, y)
    plt.title('')
    plt.xlabel('')
    plt.ylabel('')


    image_path = 'chart_temp.png'
    plt.savefig(image_path)

    return image_path

def send_chart_image(chat_id, image_path):
    with open(image_path, 'rb') as chart:
        bot.send_photo(chat_id, chart)

def record_last_usage(user_id):
    last_usage_times[user_id] = datetime.now()

def check_daily_usage(user_id):
    if user_id not in last_usage_times:
        return True
    last_usage = last_usage_times[user_id]
    today = datetime.now().date()
    return last_usage.date() != today

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Welcome to Binance Data Bot! Click below to choose a currency:", reply_markup=generate_currency_markup())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global currency

    def process_currency_choice(currency_choice):
    
        global currency
        currency = currency_choice.upper()
        bot.send_message(call.message.chat.id, f"You chose {currency}. Now select a time frame.", reply_markup=generate_time_frame_markup())

    def process_time_frame(time_frame, user_id):
        interval = call.data
        bot.send_message(call.message.chat.id, f"You chose {time_frame}. Processing your request...")

       
        df = fetch_binance_data(currency + "USDT", interval, limit=1000)
        data_to_plot = df['close'].values

     
        image_path = plot_chart(data_to_plot)

   
        send_chart_image(call.message.chat.id, image_path)

        os.remove(image_path)  
        record_last_usage(user_id)

    if call.data in ['ada', 'btc', 'eth']:
        if check_daily_usage(call.from_user.id):
            process_currency_choice(call.data)
        else:
            bot.send_message(call.message.chat.id, "Sorry, you've already used the bot today.")
    elif call.data in ['1h', '4h', '1d']:
        if currency:
            if check_daily_usage(call.from_user.id):
                process_time_frame(call.data, call.from_user.id)
            else:
                bot.send_message(call.message.chat.id, "Sorry, you've already used the bot today.")
        else:
            bot.send_message(call.message.chat.id, "Please choose a currency first.")


bot.polling()
