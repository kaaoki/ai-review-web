import requests

url = "https://mfvrezrxkhzaobtnlnpa.supabase.co/rest/v1/reviews?select=id&limit=1"
headers = {
    "apikey": "sb_publishable_DBpeR7WWVb69hh5YvIQ6KA_wA3Y3bTq",
    "Authorization": "Bearer sb_publishable_DBpeR7WWVb69hh5YvIQ6KA_wA3Y3bTq",
}

r = requests.get(url, headers=headers)
print(r.status_code)
print(r.text)