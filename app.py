from pathlib import Path
import math

import streamlit as st
import numpy as np
import pandas as pd
from src import (sumproduct, get_daily_historical_var_df, get_W_SD_info, 
                 get_normal_var, get_daily_normal_var_df)

### Constant
LEVERAGE = 500

### Read Data
bid_change_path = Path("data/bid_change.csv")
w_sd_path = Path("data/W_SD.csv")
bid_change_df = pd.read_csv(bid_change_path)
w_sd_df = pd.read_csv(w_sd_path)
list_of_ccy = [ccy[:6] for ccy in list(bid_change_df.columns)[1:]]
wsd_pairs = w_sd_df['Currency Portfolio'].to_list()

st.title("VaR Calculation")

### Get User Inputs

hide_streamlit_menu = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>

"""
st.markdown(hide_streamlit_menu, unsafe_allow_html=True) 

account = st.sidebar.number_input("Account $$$:")
position = st.sidebar.number_input("Position %:")
method = st.sidebar.selectbox(
    "Method:",
    ("Historical", "Normal Distribution"),
    index=0
)

pair_A = st.sidebar.selectbox("Currency Pair A:", list_of_ccy, index=0)
direction_A_text = st.sidebar.selectbox(
    "Direction for Pair A:",
    ("Long", "Short"),
    index=0
)

pair_B = st.sidebar.selectbox("Currency Pair B:", list_of_ccy, index=1)
direction_B_text = st.sidebar.selectbox(
    "Direction for Pair B:",
    ("Long", "Short"),
    index=0
)

if pair_A == pair_B:
    st.error("Please choose 2 different pairs.")
    st.stop()

if account <= 0:
    st.error("Account should be greater than 0.")
    st.stop()

### Calculation

# direction_A = 1 if direction_A_text == "Long" else -1
# direction_B = 1 if direction_B_text == "Short" else -1

given_pairs = f"{pair_A}, {pair_B}"
if given_pairs not in wsd_pairs:
    given_pairs = f"{pair_B}, {pair_A}"

sd_A, sd_B, correl, weight_A, weight_B, sd_portfolio = get_W_SD_info(given_pairs, w_sd_df)

given_pairs_df = bid_change_df[[f"{pair_A} Bid%Chg", f"{pair_B} Bid%Chg"]]
direction_column = f"{direction_A_text} {direction_B_text}"
given_pairs_df[direction_column] = given_pairs_df.apply(lambda row: sumproduct(row[f"{pair_A} Bid%Chg"],
                                                                               row[f"{pair_B} Bid%Chg"],
                                                                               weight_A,
                                                                               weight_B,
                                                                               direction_A_text,
                                                                               direction_B_text), axis=1)

margin_amount = account*position/100
amount_entry = margin_amount*LEVERAGE

var_standalone_95_A = amount_entry*sd_A*1.645
var_standalone_99_A = amount_entry*sd_A*2.326

var_standalone_95_B = amount_entry*sd_B*1.645
var_standalone_99_B = amount_entry*sd_B*2.326

## Historical
var_95_historical = given_pairs_df[direction_column].quantile(0.05)
var_99_historical = given_pairs_df[direction_column].quantile(0.01)
daily_var_95_historical_df = get_daily_historical_var_df(amount_entry, 
                                                         var_95_historical, 
                                                         account)
daily_var_99_historical_df = get_daily_historical_var_df(amount_entry, 
                                                          var_99_historical, 
                                                          account)

## Normal
var_95_pair_A = get_normal_var(given_pairs_df, 
                               pair_A, 
                               direction_A_text, 
                               quantile_percent=95)
var_95_pair_B = get_normal_var(given_pairs_df, 
                               pair_B, 
                               direction_B_text, 
                               quantile_percent=95)
var_99_pair_A = get_normal_var(given_pairs_df, 
                               pair_A, 
                               direction_A_text, 
                               quantile_percent=99)
var_99_pair_B = get_normal_var(given_pairs_df, 
                               pair_B, 
                               direction_B_text, 
                               quantile_percent=99)
daily_var_95_normal_df = get_daily_normal_var_df(amount_entry,
                                                 pair_A,
                                                 pair_B,
                                                 direction_A_text,
                                                 direction_B_text,
                                                 weight_A,
                                                 weight_B,
                                                 correl,
                                                 var_95_pair_A,
                                                 var_95_pair_B,
                                                 account)
daily_var_99_normal_df = get_daily_normal_var_df(amount_entry,
                                                 pair_A,
                                                 pair_B,
                                                 direction_A_text,
                                                 direction_B_text,
                                                 weight_A,
                                                 weight_B,
                                                 correl,
                                                 var_99_pair_A,
                                                 var_99_pair_B,
                                                 account)

### Output to UI
  
col1, col2 = st.columns([1, 1])
with col1:
    st.write(f"Account: $ **{account:,}**")
    st.write(f"Position: **{position:.2f}** %")

with col2:
    st.write(f"Margin Amount: $ **{margin_amount:,}**")
    st.write(f"Amount Entry: $ **{amount_entry:,}**")


col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.write("**Info**")
    st.write("Daily Volatility (SD)")
    st.write(f"Weight **{direction_A_text} - {direction_B_text}**")
    st.write("VaR standalone 95%")
    st.write("VaR standalone 99%")

with col2:
    st.write(f"**{direction_A_text} {pair_A}**")
    st.write(f"{sd_A*100:.4f} %")
    st.write(f"{weight_A*100:.2f} %")
    st.write(f"$ {var_standalone_95_A:,.2f}")
    st.write(f"$ {var_standalone_99_A:,.2f}")

with col3:
    st.write(f"**{direction_B_text} {pair_B}**")
    st.write(f"{sd_B*100:.4f} %")
    st.write(f"{weight_B*100:.2f} %")
    st.write(f"$ {var_standalone_95_B:,.2f}")
    st.write(f"$ {var_standalone_99_B:,.2f}")
st.write(f"Correlation of 2 pairs: {correl*100:.2f} %")

st.header(f"Historical VaR")
with st.expander("See results"):
    st.write("**VaR 95%**")
    st.write(daily_var_95_historical_df.assign(hack='').set_index('hack'))
    st.write("**VaR 99%**")
    st.write(daily_var_99_historical_df.assign(hack='').set_index('hack'))

st.header(f"Normal Distribution VaR")
with st.expander("See results"):
    st.write("**VaR 95%**")
    st.write(daily_var_95_normal_df.assign(hack='').set_index('hack'))
    st.write("**VaR 99%**")
    st.write(daily_var_99_normal_df.assign(hack='').set_index('hack'))