import json
import scrapy

class TheCutSpider(scrapy.Spider):
    name = 'thecut'
    start_urls = ['https://api.thecut.co/v1/auth/token']

    def parse(self, response):
        headers = {
            "Authorization": "Basic YzgwMWE2NmEtNDJlMC00ZTZhLThiZTMtOTIwYzExNWY4NWJkOjU1NTM0MTFjLWIxNjMtNDYyNi1iYWU2LTk2YTczMjMzNzMyMQ==",
            "Auth-Client-Version": "1.25.1",
            "Device-Name": "Tm9raWEgQzMy",
            "Installation-Id": "17E229B5-41B7-4F4D-B44A-C76559665E54",
            "Device-Operating-System": "TIRAMISU (33)",
            "Device-Model": "Nokia Nokia C32",
            "Auth-Client-Name": "android-app",
            "Device-Fingerprint": "3a3f05ba6c66de6a",
            "Device-Platform": "android",
            "Signature": "v1 MTcwODMyNTg5NjpKSjltTUVSZjNmMXhtMUNLWHEzOHR1U0RUdDQxQmNpYTo4V09jZTUrS0dNa21ZR0doSGNmbmlxVlR1R0RFbmZIUkRSd1h0RXJua0FzPQ==",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "77",
            "Host": "api.thecut.co",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/4.11.0"
        }
        yield scrapy.Request(
            url='https://api.thecut.co/v1/auth/token',
            method='POST',
            headers=headers,
            body=json.dumps({
                'grant_type': 'password',
                'username': 'surgbc@gmail.com',
                'password': 'ca!kacut'
            }),
            callback=self.parse_access_token
        )

    def parse_access_token(self, response):
        data = json.loads(response.body)
        access_token = data.get('access_token')
        print(access_token)

        if access_token:
            self.logger.info(f"Access Token: {access_token}")
            json_filename = "boostedchatScrapper/spiders/helpers/jsons/town_coordinates.json"
            with open(json_filename, "r") as f:
                json_data = json.load(f)

            data = []
            for item, coords in json_data.items():
                location = coords.split(",")

                data.append({"name": item, "lat": location[0], "lon": location[1]})
                print(data)

            for entry in data:
                yield scrapy.Request(
                    url=f"https://api.thecut.co/v2/search/barbers?latitude={entry['lat']}&longitude={entry['lon']}&keywords=",
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Auth-Client-Version': '1.25.1',
                        'Device-Name': 'Tm9raWEgQzMy',
                        'Installation-Id': '17E229B5-41B7-4F4D-B44A-C76559665E54',
                        'Device-Operating-System': 'TIRAMISU (33)',
                        'Device-Model': 'Nokia Nokia C32',
                        'Auth-Client-Name': 'android-app',
                        'Device-Fingerprint': '3a3f05ba6c66de6a',
                        'Session-Id': 'f822af9b4e3a61e0d5b71eacbca9c5a686fba9d2b968792e729a6138f4fde7e8122528f7230406f75ed335f6b822c732',
                        'Device-Platform': 'android',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'User-Id': '65d2df444fd2435e639c4b43',
                        'Signature': 'v1 MTcwODMzNTg5NzprTFVKNmxjNFpiUzU4aXdUTFFsTENWQTFWNUlGSVFLMDpLQlhiand2bVpCeFppZmZieGFtYnd5bzh6aWp3c3FpSUU4ZHd6azViRHRrPQ=='
                    },
                    callback=self.parse_api_response
                )
        else:
            self.logger.error("Failed to get access token")

    def parse_api_response(self, response):
        data = json.loads(response.body)
        print(data)
        self.logger.info(data)
