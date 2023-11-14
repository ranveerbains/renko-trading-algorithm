

def scheduled_job():
    import strategy_functions as sf
    import renko_booker_class as rb
    import json
    from oandapyV20 import API
    import oandapyV20.endpoints.orders as orders
    import oandapyV20.endpoints.trades as trades
    from oandapyV20.contrib.requests import MarketOrderRequest
    from oandapyV20.contrib.requests import TrailingStopLossOrderRequest
    from oandapyV20.contrib.requests import TakeProfitDetails, StopLossDetails
    import sys

    atr_length =  22
    rsi_period = 18
    momentum_period = 12
    min_candle_distance = 3
    rsi_oversold = 30
    rsi_overbought = 70
    account_size = 100000
    leverage = 20 # DO NOT CHANGE. OANDA HAS FIXED LEVERAGE OF 1:20
    risk_percentage = 0.9
    rr = 4 #RISK TO REWARD RATIO
    accountID = "xxx-xxx-xxxxxxxx-xxx"
    access_token= 'xxxxxxxxxxxxxxxxxxxxx'
    instrument = "EUR_USD"
    
    ohlc = sf.api(access_token)
    bricks = sf.bricksize(ohlc,atr_length)
    renko_ohlc = sf.df_to_renko(ohlc,bricks)
    divergence_indicator = rb.RobBookerKnoxvilleDivergence() #class
    divergence_indicator.Initialize() #method
    latest_divergence = divergence_indicator.Calculate(renko_ohlc, momentum_period, rsi_period, min_candle_distance, rsi_oversold, rsi_overbought)
    signal = sf.trade_signal(latest_divergence,renko_ohlc)
    trade_value = sf.trade_values(signal,renko_ohlc,bricks, account_size, risk_percentage,rr,latest_divergence,leverage)
    # tester: trade_value = {'signal': 'short', 'units': 160000, 'stop loss': 1.0581, 'exchange rate': 1.0561, 'take profit':1.0530, 'partial':1.0540}
    
    
    # executing orders if there is no running trade
    
    client = API(access_token=access_token)
    if len(trade_value) == 0:
        print ("no trade opportunities available")
        sys.stdout.flush()
        
        
    open_trades = trades.OpenTrades(accountID)
    client.request(open_trades)   
    open_trades_response = open_trades.response
    num_open_trades = len(open_trades_response["trades"])
    if num_open_trades >=0: 
        if num_open_trades == 0:
            if trade_value: 
                signal =  trade_value['signal']
                units = trade_value['units']
                stop_loss_price  = trade_value['stop loss']
                exchange_rate  = trade_value['exchange rate']
                take_profit_price = trade_value['take profit']
                partial_price = trade_value['partial'] 
                
                if signal == 'short':
                    # first order to full tp
                    shortmarketorder1 = MarketOrderRequest(
                        instrument=instrument,
                        units=-units*0.5,
                        takeProfitOnFill=TakeProfitDetails(price=take_profit_price).data,
                        stopLossOnFill=StopLossDetails(price=stop_loss_price).data
                    )
                    r1 = orders.OrderCreate(accountID, data=shortmarketorder1.data)
                    rv1 = client.request(r1)
                    print(json.dumps(rv1, indent = 4))
                    
                    # second order to partial tp
                    shortmarketorder2 = MarketOrderRequest(
                        instrument=instrument,
                        units=-units*0.5,
                        takeProfitOnFill=TakeProfitDetails(price=partial_price).data,
                        stopLossOnFill=StopLossDetails(price=stop_loss_price).data
                    )
                    r2 = orders.OrderCreate(accountID, data=shortmarketorder2.data)
                    rv2 = client.request(r2)
                    print(json.dumps(rv2, indent = 4))
                    print('x'*100)
                    print('x'*100)
                    print("short trades to full tp and partial tp initiated")
                    print('x'*100)
                    print('x'*100)
                    sys.stdout.flush()
                    
                    
                    
                    
                if signal == 'long':
                    # first order to full tp
                    longmarketorder1 = MarketOrderRequest(
                        instrument=instrument,
                        units=units*0.5,
                        takeProfitOnFill=TakeProfitDetails(price=take_profit_price).data,
                        stopLossOnFill=StopLossDetails(price=stop_loss_price).data
                    )
                    r3 = orders.OrderCreate(accountID, data=longmarketorder1.data)
                    rv3 = client.request(r3)
                    print(json.dumps(rv3, indent = 4))
                    
                    # second order to partial tp
                    longmarketorder2 = MarketOrderRequest(
                        instrument=instrument,
                        units=units*0.5,
                        takeProfitOnFill=TakeProfitDetails(price=partial_price).data,
                        stopLossOnFill=StopLossDetails(price=stop_loss_price).data
                    )
                    r4 = orders.OrderCreate(accountID, data=longmarketorder2.data)
                    rv4 = client.request(r4)
                    print(json.dumps(rv4, indent = 4))
                    print('x'*100)
                    print('x'*100)
                    print("long trades to full tp and partial tp initiated")
                    print('x'*100)
                    print('x'*100)
                    sys.stdout.flush()
                   
                    
                    
        # if the first tp has been hit, and only one running trade left, make sl to be on trade
        #change the distance of pips, maybe put 5-10 pip
        if num_open_trades ==1:
            most_recent_trade = open_trades_response["trades"][0]
            if "trailingStopLossOrder" not in most_recent_trade.keys(): #checks that the trade left running has no trailing stop, and adds a 10pip trailing stop
                trade_id = open_trades_response["trades"][0]["id"]
                trailing_stoploss_order = TrailingStopLossOrderRequest(tradeID = trade_id, distance=0.0010)
                r5 = orders.OrderCreate(accountID, data=trailing_stoploss_order.data)
                rv5 = client.request(r5)
                print(json.dumps(rv5, indent=4))
                print('x'*100)
                print('x'*100)
                print("one trade left, trailing stops initiated")
                print('x'*100)
                print('x'*100)
                sys.stdout.flush()
                
                
            else:
                print('x'*100)
                print('x'*100)
                print("trailing stops in place")
                print('x'*100)
                print('x'*100)
                sys.stdout.flush()
                
            
            


