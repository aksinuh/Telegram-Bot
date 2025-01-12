import os
import requests

def create_crypto_compare_client(api_key):
    return {"api_key": api_key}

def get_crypto_price(client, symbol):
    api_key = client["api_key"]
    url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol[:-4]}&tsyms=USD"
    headers = {"Authorization": f"Apikey {api_key}"}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json().get("USD")
    else:
        raise Exception(f"API Error: {response.status_code}, {response.text}")