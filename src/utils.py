from typing import Tuple
import math
import numpy as np
import pandas as pd

def sumproduct(bid_chg_A: float, 
               bid_chg_B: float, 
               weight_A: float, 
               weight_B: float, 
               direction_A_text: str, 
               direction_B_text: str) -> float:
    if direction_A_text == "Long" and direction_B_text == "Long":
        return bid_chg_A*weight_A + bid_chg_B*weight_B
    elif direction_A_text == "Long" and direction_B_text == "Short":
        return bid_chg_A*weight_A - bid_chg_B*weight_B
    elif direction_A_text == "Short" and direction_B_text == "Long":
        return -bid_chg_A*weight_A + bid_chg_B*weight_B
    elif direction_A_text == "Short" and direction_B_text == "Short":
        return -bid_chg_A*weight_A - bid_chg_B*weight_B

def get_daily_historical_var_df(amount_entry: float, 
                     var_historical: float, 
                     account: float,
                     days: int = 6) -> pd.DataFrame:
    daily_var_list = []
    var_daily = amount_entry * var_historical
    for i in range(1,days):
        port_daily = var_daily*math.sqrt(i)
        max_loss_daily = port_daily/account*100
        daily_var_list.append({
            "Day": i,
            "PORT": f"$ {port_daily:,.2f}",
            "Max Loss % Equity": f"{max_loss_daily:.0f} %",
        })
    daily_var_df = pd.DataFrame(daily_var_list)
    return daily_var_df

def get_W_SD_info(given_pairs: str, 
                  w_sd_df: pd.DataFrame) -> Tuple[float, float, float, float, float]:
    sd_A = w_sd_df.loc[w_sd_df['Currency Portfolio'] == given_pairs]['SD_A'].values[0]
    sd_B = w_sd_df.loc[w_sd_df['Currency Portfolio'] == given_pairs]['SD_B'].values[0]
    correl = w_sd_df.loc[w_sd_df['Currency Portfolio'] == given_pairs]['Correl'].values[0]
    weight_A = w_sd_df.loc[w_sd_df['Currency Portfolio'] == given_pairs]['Weight_A'].values[0]
    weight_B = w_sd_df.loc[w_sd_df['Currency Portfolio'] == given_pairs]['Weight_B'].values[0]
    sd_portfolio = w_sd_df.loc[w_sd_df['Currency Portfolio'] == given_pairs]['SD_Portfolio'].values[0]

    return (sd_A, sd_B, correl, weight_A, weight_B, sd_portfolio)

def get_normal_var(given_pairs_df: pd.DataFrame,
                   pair: str,
                   direction: str,
                   quantile_percent: int) -> float:
    if direction == "Long" and quantile_percent == 95:
        quantile = 0.05
    elif direction == "Long" and quantile_percent == 99:
        quantile = 0.01
    elif direction == "Short" and quantile_percent == 95:
        quantile = 0.95
    elif direction == "Short" and quantile_percent == 99:
        quantile = 0.99

    var_pairA = given_pairs_df[f"{pair} Bid%Chg"].quantile(quantile)
    return var_pairA

def get_var_portfolio(var_A: float, var_B: float, correl: float) -> float:
    var_port = math.sqrt(var_A**2 + var_B**2 + 2*var_A*var_B*correl)
    return -var_port if var_port >=0 else var_port

def get_daily_normal_var_df(amount_entry: float, 
                            pair_A: str,
                            pair_B: str,
                            direction_A_text: str,
                            direction_B_text: str,
                            weight_A: float,
                            weight_B: float,
                            correl: float,
                            var_pair_A: float,
                            var_pair_B: float,
                            account: float,
                            days: int = 6) -> pd.DataFrame:
    if direction_A_text == "Long":
        var_pair_A_daily = amount_entry*var_pair_A*weight_A
    else:
        var_pair_A_daily = amount_entry*var_pair_A*(-weight_A)
    if direction_B_text == "Long":
        var_pair_B_daily = amount_entry*var_pair_B*weight_B
    else:
        var_pair_B_daily = amount_entry*var_pair_B*(-weight_B)

    var_port_daily = get_var_portfolio(var_pair_A_daily, var_pair_B_daily, correl)

    daily_var_list = []

    for i in range(1,days):
        var_pair_A_day_i = var_pair_A_daily*math.sqrt(i)
        var_pair_B_day_i = var_pair_B_daily*math.sqrt(i)
        var_port_day_i = var_port_daily*math.sqrt(i)

        max_loss_daily = var_port_day_i/account*100
        daily_var_list.append({
            "Day": i,
            f"{pair_A}": f"$ {var_pair_A_day_i:,.2f}",
            f"{pair_B}": f"$ {var_pair_B_day_i:,.2f}",
            "PORT": f"$ {var_port_day_i:,.2f}",
            "Max Loss % Equity": f"{max_loss_daily:.0f} %",
        })
    daily_var_df = pd.DataFrame(daily_var_list)
    return daily_var_df