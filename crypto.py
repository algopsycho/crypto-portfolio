import pandas as pd
import numpy as np
import json
from bs4 import BeautifulSoup
import requests
import urllib.request



pd.set_option('display.max_rows', 55000)
pd.set_option('display.max_columns', 3)
pd.set_option('display.width', 1000)
L= []
crypto_portfolio=[]
crypto_names=[]
crypto_names_lower_joined=[]

url = 'https://api.coincap.io/v2/assets'
response = requests.get(url)

data = json.loads(BeautifulSoup(response.text, 'html.parser').prettify())


#all_coins_dict is a dictionary where the key images are a list of dictionaries
L= data['data']

for i in L: #each dictionary represents the information of a crypto
    if int(i['rank'])<=12: #choose the top 12 cryptos based off market cap
        crypto_portfolio.append(i['symbol'])
        crypto_names.append(i['id'])

print("Portfolio coins with the top 12 ranking :\n",crypto_portfolio)
print(crypto_names)
all_coins_df = pd.DataFrame(data)

#Loop thru all the coins in the portfolio & get their historical prices in the past 5 days.
combined_df = pd.DataFrame()
prices = []
time= []
newd ={}
lst = []
for coin in crypto_names:
    prices_time_list=[]
    dic_t = json.loads(BeautifulSoup(
            requests.get('https://api.coincap.io/v2/assets/' +coin+ '/history?interval=d1').content, "html.parser").prettify()) #this is where we use the lower case
    #print(dic_t)
    for i in dic_t['data']:
        #print(i)
        newd[i['time']]=i['priceUsd']
        prices.append(i['priceUsd'])
        time.append(i['time'])
    
    time.sort()
    for i in time:
        lst.append(newd[i])

    coindf = pd.DataFrame(list(zip(time, lst)), columns = ['time','price'] , dtype=float)
    coindf['coin'] = coin
    combined_df = combined_df.append(coindf, ignore_index=True)
    newd={}
    time =[]
    prices =[]
    lst =[]
    print('working...')



#Change the time formart
combined_df['time'] = pd.to_datetime(combined_df['time'],unit='ms',yearfirst=True)
#combined_df['time'] = [d.date() for d in combined_df['time']]
print(combined_df)
operational_df = combined_df.groupby(['time', 'coin'],as_index=False)[['price']].mean()
operational_df = operational_df.set_index('time')

pivoted_portfolio = operational_df.pivot(columns='coin')

# get covariance & returns of the coin - daily & for the period 

daily_returns = pivoted_portfolio.pct_change()
period_returns = daily_returns.mean()*5

daily_covariance = daily_returns.cov()
period_covariance = daily_covariance*5

p_returns, p_volatility, p_sharpe_ratio, p_coin_weights=([] for i in range(4))

# portfolio combinations to probe
number_of_cryptoassets = len(crypto_portfolio)
number_crypto_portfolios = 500000

# for each portoflio, get returns, risk and weights
for a_crypto_portfolio in range(number_crypto_portfolios):
    weights = np.random.random(number_of_cryptoassets)
    weights /= np.sum(weights)
    
    #print(weights)
    returns = np.dot(weights, period_returns)*100
    
    #print(weights)
    volatility = np.sqrt(np.dot(weights.T, np.dot(period_covariance, weights)))*100
   
    p_sharpe_ratio.append(returns/volatility)
    p_returns.append(returns)
    p_volatility.append(volatility)
    p_coin_weights.append(weights)

# a dictionary for Returns and Risk values of each portfolio
portfolio = {'volatility': p_volatility,
             'sharpe_ratio': p_sharpe_ratio , 'returns': p_returns} 

# extend original dictionary to accomodate each ticker and weight in the portfolio
for counter,symbol in enumerate(crypto_portfolio):
    portfolio[symbol+'-%'] = [Weight[counter] for Weight in p_coin_weights]

# make a nice dataframe of the extended dictionary
df = pd.DataFrame(portfolio)

order_cols = ['returns', 'volatility', 'sharpe_ratio']+[coin+'-%' for coin in crypto_portfolio]
df = df[order_cols]

sharpe_portfolio = df.loc[df['sharpe_ratio'] == df['sharpe_ratio'].max()]
min_variance_port = df.loc[df['volatility'] == df['volatility'].min()]
max_returns_port = df.loc[df['returns'] == df['returns'].max()]

print('****Portfolio allocations*****')
print(sharpe_portfolio.T)
