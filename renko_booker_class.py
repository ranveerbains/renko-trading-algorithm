import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import talib
from enum import Enum
        
class DivergenceType(Enum):
    Up = 0
    Down = 1

class Divergence:
    def __init__(self):
        self.StartIndex = 0
        self.EndIndex = 0
        self.Type = None
        
class RobBookerKnoxvilleDivergence:
    def __init__(self):
        self._upDivergenceColor = '#00FF00'  # Green color
        self._downDivergenceColor = '#FF0000'  # Red color
        self._momentumOscillator = None
        self._relativeStrengthIndex = None

    def Initialize(self):
        self._upDivergenceColor = self.GetColor(self._upDivergenceColor)
        self._downDivergenceColor = self.GetColor(self._downDivergenceColor)

    def Calculate(self, data, momentum_period, rsi_period, min_distance, rsi_oversold, rsi_overbought):
        latest_divergence = pd.Series()
        close_prices = data['Close'].values.astype(np.float64)  # use only the close prices
        divergence_df = pd.DataFrame(columns=['StartIndex', 'EndIndex', 'Type'])  # Create an empty DataFrame to store divergences
        self._momentumOscillator = talib.MOM(close_prices, timeperiod=momentum_period)
        self._relativeStrengthIndex = talib.RSI(close_prices, timeperiod=rsi_period)

        for index in range(len(close_prices)):
            if index <= momentum_period:
                continue
            divergences = self.GetDivergence(self._momentumOscillator, index, momentum_period, min_distance)
            for divergence in divergences:
                if (divergence.Type == DivergenceType.Up and self._relativeStrengthIndex[index] > rsi_oversold) or \
                        (divergence.Type == DivergenceType.Down and self._relativeStrengthIndex[index] < rsi_overbought):
                    continue
                # self.PlotDivergence(divergence, close_prices)
            # Store the divergence in the divergenceDataFrame
            #Cannot pass thru as an argument as changes made to df in method will stay in method
            # Store the divergence
                divergence_df = self.StoreDivergence(divergence, divergence_df)  
             # Store the latest divergence
        if not divergence_df.empty:
            if len(divergence_df)>1:
                latest_divergence = divergence_df.iloc[-1].copy() #rerturn object
            else:
                latest_divergence = divergence_df.iloc[0].copy()#return object
                      
        # plt.show()  # Moved to outside the loop
        return latest_divergence
    
    def StoreDivergence(self, divergence, divergence_df):
        new_row = {
            'StartIndex': divergence.StartIndex,
            'EndIndex': divergence.EndIndex,
            'Type': divergence.Type.value
        }
        divergence_df = pd.concat([divergence_df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
        return divergence_df

    def PlotDivergence(self, divergence, close_prices):
        color = self._upDivergenceColor if divergence.Type == DivergenceType.Up else self._downDivergenceColor
        #plotting the divergence
        plt.plot([divergence.StartIndex, divergence.EndIndex], [close_prices[divergence.StartIndex], close_prices[divergence.EndIndex]], color=color)
        
    def GetDivergence(self, series, index, periods, min_distance):
        result = []
        for i in range(index - min_distance, index - periods, -1):
            isDiverged = False
            if series[i] != series[index]:
                isDiverged = True
            if not isDiverged:
                continue
            #ensure that there is one element before calling the max() funciton
            range_start = i - min_distance + 1
            range_end = index
            if range_start < 0:
                 range_start = 0
                # continue
            if range_start < range_end:
                isHigherHigh = series[i] >= max(series[range_start:range_end])
                isLowerLow = series[i] <= min(series[range_start:range_end])  
            #original code
            # isHigherHigh = series[i] >= max(series[i - min_distance + 1:index])
            # isLowerLow = series[i] <= min(series[i - min_distance + 1:index])
            if series[i] < series[index] and isLowerLow:
                divergence = Divergence()
                divergence.StartIndex = i
                divergence.EndIndex = index
                divergence.Type = DivergenceType.Up
                result.append(divergence)
            elif series[i] > series[index] and isHigherHigh:
                divergence = Divergence()
                divergence.StartIndex = i
                divergence.EndIndex = index
                divergence.Type = DivergenceType.Down
                result.append(divergence)
        return result

    def GetColor(self, colorString, alpha=1.0):
    # Parse the color string and return the corresponding RGBA color tuple
        colorString = colorString.lstrip('#')
        r, g, b = tuple(int(colorString[i:i+2], 16) for i in (0, 2, 4))
        return (r / 255, g / 255, b / 255, alpha)