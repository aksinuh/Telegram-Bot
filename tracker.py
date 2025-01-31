import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_crypto_compare_client(api_key):
    return {"api_key": api_key}

def get_crypto_price(client, symbol):
    api_key = client["api_key"]
    base_symbol = symbol[:-4]  # Əgər symbol həmişə 4 simvolla bitirsə
    url = f"https://min-api.cryptocompare.com/data/price?fsym={base_symbol}&tsyms=USD"
    headers = {"Authorization": f"Apikey {api_key}"}

    # Yenidən cəhd parametrləri
    retry_strategy = Retry(
        total=3,  # Maksimum 3 cəhd
        backoff_factor=1,  # Cəhdlər arasında gözləmə müddəti
        status_forcelist=[500, 502, 503, 504]  # Bu status kodları üçün yenidən cəhd et
    )

    # Session yaradın və yenidən cəhd mexanizmini əlavə edin
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    try:
        # Sorğunu göndərin
        response = session.get(url, headers=headers, timeout=30)  # Zaman aşımını 30 saniyəyə çıxarın
        response.raise_for_status()  # HTTP xətalarını yoxlayın
        data = response.json()
        return data.get("USD")
    except requests.exceptions.RequestException as e:
        raise Exception(f"API Error: {e}")