import requests
import datetime
import time
import pandas as pd

SPOT_BASE_ENDPOINT = 'https://api.binance.com'
FUTURES_BASE_ENDPOINT = 'https://dapi.binance.com'


def get_futures_ticker():

    pairs = []

    response = requests.get(FUTURES_BASE_ENDPOINT + '/dapi/v1/ticker/price')

    for pair in response.json():

        expiration_date = pair['symbol'].split('_')[1]

        if expiration_date != 'PERP':

            expiration_timestamp = int(datetime.datetime.strptime(expiration_date, '%y%m%d').timestamp())
            
            if time.time() < expiration_timestamp: # Почему-то также получаем уже ликвидированные в сентябре пары, поэтому отсеиваем
                
                futures_symbol = {

                    'symbol': pair['ps'].split('USD')[0],
                    'full_symbol': pair['symbol'],
                    'futures_price': float(pair['price']),
                    'expiration_time': expiration_timestamp

                }

                pairs.append(futures_symbol)


    return pd.DataFrame(pairs)
            
            
def get_spot_ticker():

    pairs = []

    response = requests.get(SPOT_BASE_ENDPOINT + '/api/v3/ticker/price')
    
    for pair in response.json():

        if pair['symbol'][-4:] == 'USDT':
            
            spot_symbol = {

                'symbol': pair['symbol'].split('USDT')[0],
                'pair': pair['symbol'],
                'spot_price': float(pair['price'])

            }

            pairs.append(spot_symbol)

    return pd.DataFrame(pairs)

def main():

    futures_pairs = get_futures_ticker()
    spot_pairs = get_spot_ticker()

    contango_df = pd.merge(futures_pairs, spot_pairs, on='symbol')

    interest_rates_annulized = []

    for index, row in contango_df.iterrows():
        
        interest_rate = ((row['futures_price'] / row['spot_price']) - 1) * 100
        days_until_expiration = (row['expiration_time'] - time.time()) / 86400
        
        APY = interest_rate / days_until_expiration * 365
        interest_rates_annulized.append(APY)

    contango_df['interest_rate_annualized'] = interest_rates_annulized
    contango_df = contango_df.sort_values(by='interest_rate_annualized', ascending=False)
    contango_df = contango_df[['full_symbol', 'spot_price', 'futures_price', 'interest_rate_annualized']]
    contango_df.to_excel('contango.xlsx', index=False)


if __name__ == '__main__':
    main()