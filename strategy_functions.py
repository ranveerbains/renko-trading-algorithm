
def api(access_token):
    import pandas as pd
    import numpy as  np
    import pytz

    import matplotlib.pyplot as plt

    from apscheduler.schedulers.blocking import BlockingScheduler 
    # ^u need a scheduler to schedule how often you want to probe the market

    import json
    from oandapyV20 import API
    import oandapyV20.endpoints.orders as orders
    from oandapyV20.contrib.requests import LimitOrderRequest
    from oanda_candles import Pair, Gran, CandleCollector, CandleClient
    from oandapyV20.contrib.requests import TakeProfitDetails, StopLossDetails


    client = CandleClient(access_token, real=False)

    collector = client.get_collector(Pair.EUR_USD, Gran.M5)
    candles = collector.grab(500) #grabbing 5min candles from the past 10000

    data = {
        'Unixtime': np.array([candle.time for candle in candles]),
        'Open': np.array([float(str(candle.bid.o)) for candle in candles]),
        'High': np.array([float(str(candle.bid.h)) for candle in candles]),
        'Low': np.array([float(str(candle.bid.l)) for candle in candles]),
        'Close': np.array([float(str(candle.bid.c)) for candle in candles])
    }

    ohlc = pd.DataFrame(data)

    ohlc['Previous Close'] = ohlc['Close'].shift(1)
    ohlc['Date'] = pd.to_datetime(ohlc['Unixtime'], unit='s')

    ohlc['Date'] = ohlc['Date'].dt.tz_localize(pytz.utc).dt.tz_convert('Asia/Singapore')
    # ohlc['Time_gmt8'] = ohlc['Date'].dt.strftime('%H:%M:%S')
    ohlc = ohlc.iloc[1:].reset_index(drop = True) #removes the first candle because there is no previous close data
    return ohlc

    
def bricksize(dataframe, n):
    import pandas as pd
    import talib
    atr = talib.ATR(dataframe['High'], dataframe['Low'], dataframe['Close'], timeperiod=n)
    bricks = round(atr.iloc[-1], 4)
    return float(bricks)


def df_to_renko(data, bricksize):
    #using stocktrends package
    from stocktrends import Renko
    
    if 'level_0' in data.columns:
        data = data.drop('level_0', axis=1)  
    data.reset_index(inplace=True)
    data.columns = [i.lower() for i in data.columns]
    df = Renko(data) #Call renko function and pass dataframe
    df.brick_size = bricksize #Assign brick size
    renko_df = df.get_ohlc_data()#Convert to renko and pass to renko_df
    new_column_names = {'date':'Date','open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'uptrend': 'Uptrend'}
    renko_df = renko_df.rename(columns=new_column_names)    
    return renko_df

def trade_signal(latest_divergence, renko_ohlc):
    signal = 'nil'
    if not latest_divergence.empty : 
        endindex = latest_divergence['EndIndex']
        divergence_type = latest_divergence['Type']
        
        def is_current_price_higher(endindex,renko_ohlc):
            endindex_close = renko_ohlc.iloc[endindex]['Close']
            current_price = renko_ohlc.iloc[-1]['Close']
            return endindex_close < current_price

        def is_current_price_lower(endindex,renko_ohlc):
            endindex_close = renko_ohlc.iloc[endindex]['Close']
            current_price = renko_ohlc.iloc[-1]['Close']
            return endindex_close > current_price

        def is_within_last_2_candles(endindex,dataframe):
            last_2nd_index_df = len(dataframe)-2
            return endindex>=last_2nd_index_df

        if is_within_last_2_candles(endindex,renko_ohlc):
            if divergence_type == 0:
                if renko_ohlc.iloc[endindex]['Uptrend'] == False: #check to see if divergence candle is red
                    if is_current_price_higher(endindex,renko_ohlc):  #check to see if current candle is green
                        signal = 'long'
            if divergence_type == 1:
                if renko_ohlc.iloc[endindex]['Uptrend'] == True: #check to see if divergence candle is green
                    if is_current_price_lower(endindex,renko_ohlc):  #check to see if current candle is red
                        signal = 'short'
    return signal

def calculate_unit_size(account_size, exchange_rate, stop_loss_price, risk_percentage,leverage):
        risk_amount = account_size * risk_percentage/100
        pip_value = 0.0001  # Assuming a pip value of 0.0001 for most pairs
        leverage = 20
        # Calculate the stop loss distance in pips
        stop_loss_distance = round((abs(exchange_rate - stop_loss_price) / pip_value),5)
        # Calculate the unit size
        #lot size = (risk/sl*pipvalue)
        #unit size = lost size *100,000
        risk_per_pip = (risk_amount/stop_loss_distance)
        lot_size = round(risk_per_pip/10,2)
        unit_size = round(lot_size*100000)
        return unit_size

def trade_values(signal,renko_ohlc, bricks,account_size, risk_percentage,rr,latest_divergence,leverage):
    last_candle = renko_ohlc.iloc[-1]
    trade_values ={}

    if signal == 'nil': #if signal not nil, there will be divergence
        return trade_values
    
    endindex = latest_divergence['EndIndex']

    if signal == 'long':
        exchange_rate = round(last_candle['Close'],5)
        stop_loss_price = round(renko_ohlc.iloc[endindex]['Low'] - (bricks) ,5)
        take_profit_price = round(exchange_rate + abs(exchange_rate-stop_loss_price)*rr,5)
        partial_price = round(exchange_rate + abs(exchange_rate-stop_loss_price)*(rr*0.5),5)
        if take_profit_price>exchange_rate>stop_loss_price:
            trade_values['signal'] = signal
            trade_values['units'] = calculate_unit_size(account_size, exchange_rate, stop_loss_price, risk_percentage,leverage) 
            trade_values['stop loss'] = stop_loss_price 
            trade_values['exchange rate'] = exchange_rate  
            trade_values['take profit'] = take_profit_price
            trade_values['partial'] = partial_price 
            pip_value = 0.0001
            stop_loss_pips = round(abs(exchange_rate - stop_loss_price)/pip_value)
            if stop_loss_pips >20:
                trade_values = {}

    if signal == 'short':
        exchange_rate = round(last_candle['Close'],5)
        stop_loss_price = round(renko_ohlc.iloc[endindex]['High'] + (bricks) ,5)
        take_profit_price = round(exchange_rate - abs(exchange_rate-stop_loss_price)*rr,5)
        partial_price = round(exchange_rate - abs(exchange_rate-stop_loss_price)*(rr*0.5),5)
        if take_profit_price<exchange_rate<stop_loss_price:
            trade_values['signal'] = signal
            trade_values['units'] = calculate_unit_size(account_size, exchange_rate, stop_loss_price, risk_percentage,leverage) 
            trade_values['stop loss'] = stop_loss_price  
            trade_values['exchange rate'] = exchange_rate 
            trade_values['take profit'] = take_profit_price 
            trade_values['partial'] = partial_price
            pip_value = 0.0001
            stop_loss_pips = round(abs(exchange_rate - stop_loss_price)/pip_value)
            if stop_loss_pips >20:
                trade_values = {}
            
    return trade_values

def final_job(ohlc,
    atr_length, momentum_period,rsi_period,
    min_candle_distance,rsi_oversold,rsi_overbought,
    account_size, risk_percentage, rr
    ):
    import renko_booker_class as rb
    ohlc = api()
    bricks = bricksize(ohlc,atr_length)
    renko_ohlc = df_to_renko(ohlc,bricks)
    divergence_indicator = rb.RobBookerKnoxvilleDivergence() #class
    divergence_indicator.Initialize() #method
    latest_divergence = divergence_indicator.Calculate(renko_ohlc, momentum_period, rsi_period, min_candle_distance, rsi_oversold, rsi_overbought)
    signal = trade_signal(latest_divergence,renko_ohlc)
    trade_value = trade_values(signal,renko_ohlc,bricks, account_size, risk_percentage,rr,latest_divergence)
    return trade_value


