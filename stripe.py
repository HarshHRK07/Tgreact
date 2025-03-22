import requests
import json

# Map Stripe decline codes to user-friendly messages
DECLINE_MESSAGES = {
    "generic_decline": "Generic Decline",
    "insufficient_funds": " Insufficient Funds",
    "card_not_supported": " Card Not Supported",
    "expired_card": " Expired Card",
    "incorrect_cvc": "Incorrect CVC",
    "invalid_card_number": "Invalid Card Number",
    "card_decline_rate_limit_exceeded": "Rate Limit Exceeded",
    "authentication_required": "Authentication Required",
    "do_not_honor": "Do Not Honor",
    "lost_card": "Lost Card",
    "stolen_card": " Stolen Card",
    "pickup_card": " Pickup Card",
    "invalid_expiry_month": "Invalid Expiry Month",
    "invalid_expiry_year": " Invalid Expiry Year",
    "transaction_not_allowed": " Transaction Not Allowed",
    "card_velocity_exceeded": " Velocity Exceeded",
    "card_declined": " Card Declined (Contact Issuer)", 
    "invalid_account": "Invalid  Account",
}

def process_stripe_payment(card_number, exp_month, exp_year, cvv):
    try:
        # Step 1: Get payment details from Bloomerang API
        bloomerang_url = "https://api.bloomerang.co/v1/Widget/1396736"
        bloomerang_params = {'ApiKey': "pub_e4bd6000-6214-11ee-8019-0a4cd6191fc9"}
        bloomerang_payload = {
            "ServedSecurely": True,
            "FormUrl": "https://crm.bloomerang.co/HostedDonation?ApiKey=pub_e4bd6000-6214-11ee-8019-0a4cd6191fc9&WidgetId=1396736",
            "Logs": []
        }
        bloomerang_headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
            'Content-Type': "application/json",
            'sec-ch-ua-platform': "\"Android\"",
            'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            'sec-ch-ua-mobile': "?1",
            'origin': "https://crm.bloomerang.co",
            'sec-fetch-site': "same-site",
            'sec-fetch-mode': "cors",
            'sec-fetch-dest': "empty",
            'referer': "https://crm.bloomerang.co/",
            'accept-language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
            'priority': "u=1, i"
        }

        bloomerang_response = requests.post(bloomerang_url, params=bloomerang_params,
                                            data=json.dumps(bloomerang_payload), headers=bloomerang_headers)

        if bloomerang_response.status_code != 200:
            print(f"Bloomerang Error: {bloomerang_response.status_code} - {bloomerang_response.text}")
            return f"𝗘𝗿𝗿𝗼𝗿: 𝗕𝗹𝗼𝗼𝗺𝗲𝗿𝗮𝗻𝗴 𝗔𝗣𝗜 𝗳𝗮𝗶𝗹𝗲𝗱 𝘄𝗶𝘁𝗵 𝘀𝘁𝗮𝘁𝘂𝘀 {bloomerang_response.status_code}"

        bloomerang_data = bloomerang_response.json()
        payment_intent_id = bloomerang_data.get("PaymentElement", {}).get("PaymentIntentId")
        client_secret = bloomerang_data.get("PaymentElement", {}).get("ClientSecret")

        if not payment_intent_id or not client_secret:
            print("Bloomerang Response Missing Data:", bloomerang_data)
            return "𝗘𝗿𝗿𝗼𝗿: 𝗣𝗮𝘆𝗺𝗲𝗻𝘁𝗜𝗻𝘁𝗲𝗻𝘁𝗜𝗱 𝗼𝗿 𝗖𝗹𝗶𝗲𝗻𝘁𝗦𝗲𝗰𝗿𝗲𝘁 𝗺𝗶𝘀𝘀𝗶𝗻𝗴"

        # Step 2: Confirm payment using Stripe API
        stripe_url = f"https://api.stripe.com/v1/payment_intents/{payment_intent_id}/confirm"
        stripe_payload = {
            'return_url': "https://crm.bloomerang.co/HostedDonation?ApiKey=pub_e4bd6000-6214-11ee-8019-0a4cd6191fc9&WidgetId=1396736",
            'payment_method_data[billing_details][address][country]': "IN",
            'payment_method_data[type]': "card",
            'payment_method_data[card][number]': card_number,
            'payment_method_data[card][cvc]': cvv,
            'payment_method_data[card][exp_year]': exp_year,
            'payment_method_data[card][exp_month]': exp_month,
            'key': "pk_live_iZYXFefCkt380zu63aqUIo7y",
            'client_secret': client_secret
        }
        stripe_headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
            'Accept': "application/json",
            'sec-ch-ua-platform': "\"Android\"",
            'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            'sec-ch-ua-mobile': "?1",
            'origin': "https://js.stripe.com",
            'sec-fetch-site': "same-site",
            'sec-fetch-mode': "cors",
            'sec-fetch-dest': "empty",
            'referer': "https://js.stripe.com/"
        }

        stripe_response = requests.post(stripe_url, data=stripe_payload, headers=stripe_headers)
        print(f"Stripe Response: {stripe_response.status_code} - {stripe_response.text}")

        if stripe_response.status_code == 200:
            stripe_data = stripe_response.json()
            status = stripe_data.get('status')
            if status == 'succeeded':
                return "𝗖𝗵𝗮𝗿𝗴𝗲𝗱 $𝟭 ✅"
            elif status == 'requires_action':
                return "𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗿𝗲𝗾𝘂𝗶𝗿𝗲𝘀 𝗮𝗱𝗱𝗶𝘁𝗶𝗼𝗻𝗮𝗹 𝗮𝗰𝘁𝗶𝗼𝗻 (e.g., 3D Secure)"
            elif status == 'requires_payment_method':
                error = stripe_data.get('last_payment_error', {})
                decline_code = error.get('code', 'card_declined')  # Default to card_declined if no specific code
                decline_message = error.get('message', 'No additional info')
                print(f"Decline Details: Code={decline_code}, Message={decline_message}")
                return DECLINE_MESSAGES.get(decline_code, f"{decline_code} ({decline_message})")
            else:
                return f"𝗨𝗻𝗵𝗮𝗻𝗱𝗹𝗲𝗱 𝗽𝗮𝘆𝗺𝗲𝗻𝘁 𝘀𝘁𝗮𝘁𝘂𝘀: {status}"
        else:
            error_data = stripe_response.json().get('error', {})
            error_code = error_data.get('decline_code', 'unknown_error')
            error_message = error_data.get('message', 'No additional info')
            print(f"Stripe Error: Code={error_code}, Message={error_message}")
            return DECLINE_MESSAGES.get(error_code, f"{error_code} ({error_message})")

    except Exception as e:
        print(f"Stripe Payment Error: {str(e)}")
        return "𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱 𝘄𝗵𝗶𝗹𝗲 𝗽𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝘁𝗵𝗲 𝗰𝗮𝗿𝗱."