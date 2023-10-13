import requests
import json
import time
import os
import discord
import re

# Constants
DATA_FOLDER = 'data'
MAPPER_FILE = 'mappers.json'
file_name = 'data_v2' + '.json'
OUTPUT_FILE = 'final_output_data.json'


# Read event IDs from a text file
def read_event_ids_from_file(file_path):
    try:
        with open(file_path, 'r') as id_file:
            return [line.strip() for line in id_file.readlines()]
    except FileNotFoundError:
        print("Event ID file not found.")
        return []
    except Exception as e:
        print(f"An error occurred while reading event IDs: {e}")
        return []

# Function to send Discord alerts
def send_discord_alert(final_data):

    # Define your intents
    intents = discord.Intents.default()
    intents.typing = False  # Disable typing event (optional)

    # Initialize a Discord client with intents
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'Logged in as {client.user.name} ({client.user.id})')

        # Get the channel where you want to send the embed
        channel_name = 'general'  # Replace with the desired channel name
        guild = discord.utils.get(client.guilds, name='TestServer')  # Replace with your server's name
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        
        try :
            tmp_title = (final_data.get("Event Title"))
            tmp_date = (final_data.get("Event Date"))
            tmp_location_tmp = (final_data.get("Location"))
            address = tmp_location_tmp.get("address")
            addressLocality = (address.get("addressLocality"))
            addressRegion = (address.get("addressRegion"))
            total_seats_tmp = ((final_data.get("seat_details")))[0]
            total_seats = []
            for item in total_seats_tmp:
                new_item = {
                    'price': item['price'],
                    'seat_number': item['shape_name']
                }
                total_seats.append(new_item)
            print("123113")
            print(len(total_seats))
            chunk_size = 20
            split_json_lists = [total_seats[i:i + chunk_size] for i in range(0, len(total_seats), chunk_size)]

            seat_types_restocked = final_data.get("seat_types_restocked")
        except Exception as e:
            print(str(e))
            pass

        if channel:
            # Create an embed for the custom message
            embed = discord.Embed(
                title=f'Restock Alert For {tmp_title} , {tmp_date} , AT {addressLocality} {addressRegion} | TicketMaster',
                description=f'{len(total_seats)} Seats have been Restocked',
                color=discord.Color.blue()  # You can customize the color
            )

            # Add fields or other customization to the embed as needed
            for i in split_json_lists:
                embed.add_field(name="Seat Details", value=f'{i}', inline=False)
            
            embed.add_field(name="Seat Type Restocked", value= f'{seat_types_restocked}', inline=False)

            # Send the embed
            await channel.send(embed=embed)
            
            
        #     # Logout (close) the bot
        #     await client.close()
        # else:
        #     print(f"Could not find a suitable channel to send the message in {guild.name}")

    # Start the bot with your token

    client.run('ADD YOUR TOKEN')
        
def create_mapper_file(URL1,URL3, cookies_price , headers_price):
    if os.path.exists(os.path.join(DATA_FOLDER, MAPPER_FILE)):
        print("Mapper file already exists. Skipping creation.")
        return

    print("Creating Mapper file...")
    
    response = requests.get(URL1, headers=headers_price)
    data = response.json()
    pages = data.get("pages")
    segments = pages[0]['segments']

    output_data = [{"id": segment["id"], "name": segment["name"]} for segment in segments]
            
    price_respone = requests.get(URL3,cookies=cookies_price ,headers=headers_price)
    #print("price_response", price_respone)
    price_data = price_respone.text
    
    list2 = re.findall(r'\\\"shapes\\\":\[(.*?)\]', price_data)  # Getting Price Keys

    list1 = re.findall(r'\"listPriceRange\\\"\:\[{\\\"currency\\\"\:\\\"USD\\\",\\\"min\\\":(.*?),', price_data) # Getting Price Values
        
        
    # Check if the lengths of both lists are the same
    if len(list1) == len(list2):
        result_dict = {}

        for value, key in zip(list1, list2):
            # Extract "s_number" from the value using a regular expression
            match = re.search(r's_\d+', key)
            if match:
                s_number = match.group()
                result_dict[s_number] = value

        #print(result_dict)
    else:
        print("The lengths of the two lists are not the same.")
                
    # Create a dictionary based on the 'id' values in dict1
    dict1_id_dict = {item['id']: item['name'] for item in output_data}

    # Merge the dictionaries based on keys from dict2
    merged_dict = [{'id': key, 'price': result_dict[key], 'name': dict1_id_dict.get(key, None)} for key in result_dict]


    output_file = os.path.join(DATA_FOLDER, MAPPER_FILE)

    with open(output_file, 'w') as json_file:
        json.dump(merged_dict, json_file, indent=4)

    print(f'Mapper file has been created at {output_file}')

# Fetch data from URLs and save to files
def fetch_and_save_data(URL2, HEADERS):
    try:
        # Fetch data from URL2
        response = requests.get(URL2, headers=HEADERS)
        data = response.json()
        temp_data = data.get("facets")

        output_file = os.path.join(DATA_FOLDER, file_name)

        with open(output_file, 'w') as json_file:
            json.dump(temp_data, json_file, indent=4)

        print(f'Data has been written to {output_file}')
    except Exception as e:
        print(f"An error occurred while fetching data from URL2: {e}")

# Load JSON data from a file
def load_json_file(filename):
    try:
        with open(os.path.join(DATA_FOLDER, filename), 'r') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return []
    except Exception as e:
        print(f"An error occurred while loading JSON file '{filename}': {e}")
        return []

def main():
    id_list = read_event_ids_from_file('event_ids.txt')
    
    if not id_list:
        print("No event IDs found in the input file.")
        return
    
    changes_list = []  # To store changes

    for event_id in id_list:
        URL1 = f'https://mapsapi.tmol.io/maps/geometry/3/event/{event_id}/placeDetailNoKeys?useHostGrids=true&app=PRD2663_EDP_NA&sectionLevel=true&systemId=HOST'
        URL2 = f'https://services.ticketmaster.com/api/ismds/event/{event_id}/facets?by=inventorytypes%20%2B%20shape&q=not(%27accessible%27)&show=places&qty=2&compress=places&apikey=b462oi7fic6pehcdkzony5bxhe&apisecret=pquzpfrfz7zd2ylvtz3w5dtyse&resaleChannelId=internal.ecommerce.consumer.desktop.web.browser.ticketmaster.us'
        URL3 = f'https://www.ticketmaster.com/event/{event_id}'
        
        HEADERS = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Cookie': 'eps_sid=e7a6d93eee084b6bdbc09d42a92c2ddc6cd389b5; TMUO=west_SPb9YyInjChFYrizst3Dp16FHEq2kbVQg+YNNiTdhls=; LANGUAGE=en-us; SID=Bkjpd6KzC0kBVU6LUrE8Bd6SvqYaCOgkRz0LZRhFtfzMiBObMqHsO0F1ulqrSpxA17yK8JiQXBjeQGj3oMqi; BID=KyVkTn7E4X2ntuXoLoBmrlbfO7XRIUnsjA7L-4ILrOS9bzQmfjXvAx7Y6rVyGUUuwfNDgPUG3lXz1mw; mt.v=5.1480159744.1696928485846; NDMA=200; reese84=3:3ngTSIN4U/+mgdApq36yQw==:nL7tzTb5/t5Jce6OK2MKYhp18VL1hiJxynuKq6JJLIkZHR2ORHehCSSyvb8EbpSARQxVdBHtG9S8uYKGoZJt31jeahTxgYyS0qwRGx9wfYN9jBemxQ7cXlF31lItWfvkUmvW3bnVb308toDZQcM9yfZth4WW/gsJGrc1ikIQtG2sTZWJ0BF2CSgbmnupMV+TsYR6LFJ4fsOlo3YO0WJdmHy/d3et97aM/1HtwxnXRNoOCPq3VTXwHSa6cCG4WZc2z19RFIr06gSljk8jCxA8pYkMORMsNg6yc93RS73jaaujkonBBYhwzu+u1D7coGPBpUyTQcYchz7pprFb56bAK2t9uZTyUbdmmxjXHXAc0LO/uV3kNYiuFJz0w07ryCEX4Dsh8lJoREr1jD6bQ2jz0hj6q0Q9lm35Ar3WDtJgFXW3IRP0/XWHdmpJd6v59HIomYKswQ80gco1APZk4GYuyM7iQ0VqJgbRuyaVTyC2L9dHh1uMeNo0Iva34eFy1xdTHjpuaGiR8WkOvv4FersBYw==:NdqlBp0vasIoIweHWZzZLDduGHIcZGlDSACkURThcjw=',
            'DNT': '1',
            'If-Modified-Since': 'Tue, 10 Oct 2023 11:37:06 GMT',
            'If-None-Match': 'W/"08dca40938caea2ee259cdf5176993b10"',
            'Origin': 'https://www.ticketmaster.com',
            'Referer': 'https://www.ticketmaster.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'TMPS-Correlation-Id': '6d5f81e3-ec51-4e95-ab34-a64104fdbfc7',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="117", "Not;A=Brand";v="8"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
            # ... add other headers here ...
        }
        
        cookies_price  = {
                'eps_sid': 'e7a6d93eee084b6bdbc09d42a92c2ddc6cd389b5',
                'lightstep_guid%2Fco2.sdk': '44434edb2e64a27f',
                'lightstep_session_id': '6d5d860e6b72d652',
                'TMUO': 'west_SPb9YyInjChFYrizst3Dp16FHEq2kbVQg+YNNiTdhls=',
                'lightstep_guid%2Fedp.app': '2f33731c4a843833',
                'LANGUAGE': 'en-us',
                'SID': 'Bkjpd6KzC0kBVU6LUrE8Bd6SvqYaCOgkRz0LZRhFtfzMiBObMqHsO0F1ulqrSpxA17yK8JiQXBjeQGj3oMqi',
                'BID': 'KyVkTn7E4X2ntuXoLoBmrlbfO7XRIUnsjA7L-4ILrOS9bzQmfjXvAx7Y6rVyGUUuwfNDgPUG3lXz1mw',
                'mt.v': '5.1480159744.1696928485846',
                'tmff': '',
                'NDMA': '200',
                'ms_visitorid': '5ea65d62-dd54-12c4-57b4-c81f00ee0fa2',
                'tmsid': 'ed4dc411-995e-4947-b4da-59b35d9059b3',
                'NATIVE': '%2Fnative%2Fconversion%2Fe.gif%3Fe%3DeyJ2IjoiMS4xMSIsImF2IjozNjcyMTQsImF0IjozMzg5LCJidCI6MCwiY20iOjczMjI4MiwiY2giOjI5NTg1LCJjayI6e30sImNyIjoyNjAzNzI1NTksImRpIjoiNGVkZWI2YzdjYThlNGQ0NmJmYzM3OTJlMTZlMDcwNTAiLCJkaiI6MCwiaWkiOiJjZWY0N2Y4OTY5Njk0YmJiOTcyN2IzYjRhZTk3MWZmMCIsImRtIjozLCJmYyI6NDM5Njk5MTQ3LCJmbCI6NDI5NzE1NTU1LCJpcCI6IjUyLjIyLjI0MS42MyIsImt3IjoiY2F0X2NvbmNlcnRzLGRtYS41MSxlbi11cyIsIm1rIjoiZG1hLjUxIiwibnciOjEwMDg1LCJwYyI6MSwib3AiOjEsImVjIjo0Ljg0MDkyNiwiZ20iOjAsImVwIjpudWxsLCJwciI6MTE2NTMzLCJydCI6MywicnMiOjUwMCwic2EiOiI1NSIsInNiIjoiaS0wMGNiMjAyMzMzY2FjYmUxOSIsInNwIjo4MDA5MDAsInN0Ijo5NzgzNDIsInVrIjoidWUxLTdmYjNlMThkNzk1ODQ4NTJhNzgwMWRiNmQ2NGIwNmEyIiwiem4iOjE3ODIzNCwidHMiOjE2OTcxNDA4MTA3OTksInBuIjoiaGVyb18xIiwiZ2MiOnRydWUsImdDIjp0cnVlLCJncyI6Im5vbmUiLCJkYyI6MSwidHoiOiJBbWVyaWNhL05ld19Zb3JrIiwiZXQiOjN9%26s%3DDqqNwPT-Hb2ESSM01nKSXqWO9sY',
                'azk': 'ue1-7fb3e18d79584852a7801db6d64b06a2',
                'azk-ss': 'true',
                'reese84': '3:fJW/pXs2oSTzV0eJUgGWjw==:W8tEbIphIWu+VZ3W9S4NSmk43rSVDUkVDticTI+2pICy0HzNqp1cNpH0vKFadmBWzP5NoQnQKHI5tPoTp1eD69Y7XDbLycXrCZ6fAbakFIgQ5jiYoN+a5eOdjBM3bPWMPV3OcaRvG3bEme3efGmhd/Bp3KBw80pJMK5snRX1zs9MMLTnM5v0pK85pyI9bq33KnOZF1KXWow8amdTU2vo+NxPsx0G+v/JZc5cL+mnrisqankpUR7NMFy7KyoUKvanQM9ZU8MnNvddpQfD8KmyBD94SBFt3ZXo0fkP5SrSxRRNtRT9/pI5mvN7PMiipC5TlWAsFvIhXZkDLHjdSd4k8UXlnV/pSix+MwhCaETbmMxgY3k59VwYIL0yo8Szq7IRe8/6j9sZjEua3zubp/9FAKvV0hDw1I3lNAY67g3ggMo6l/Or+vt9pJ2J3uZWeau5dTBRO8MxIBZ3wNXryO9mqSd/8JZkFTDyYrKr/NRhx6UBWDsbD0OoCT/Yfl2qrF0UL44SsxSla1f1jN539G9rLA==:I4ZEsksh07NLdQxHlz8HwylbspakmctuPXAiFw2c7Rk=',
            }

        headers_price = {
            'authority': 'www.ticketmaster.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            # 'cookie': 'eps_sid=e7a6d93eee084b6bdbc09d42a92c2ddc6cd389b5; lightstep_guid%2Fco2.sdk=44434edb2e64a27f; lightstep_session_id=6d5d860e6b72d652; TMUO=west_SPb9YyInjChFYrizst3Dp16FHEq2kbVQg+YNNiTdhls=; lightstep_guid%2Fedp.app=2f33731c4a843833; LANGUAGE=en-us; SID=Bkjpd6KzC0kBVU6LUrE8Bd6SvqYaCOgkRz0LZRhFtfzMiBObMqHsO0F1ulqrSpxA17yK8JiQXBjeQGj3oMqi; BID=KyVkTn7E4X2ntuXoLoBmrlbfO7XRIUnsjA7L-4ILrOS9bzQmfjXvAx7Y6rVyGUUuwfNDgPUG3lXz1mw; mt.v=5.1480159744.1696928485846; tmff=; NDMA=200; ms_visitorid=5ea65d62-dd54-12c4-57b4-c81f00ee0fa2; tmsid=ed4dc411-995e-4947-b4da-59b35d9059b3; NATIVE=%2Fnative%2Fconversion%2Fe.gif%3Fe%3DeyJ2IjoiMS4xMSIsImF2IjozNjcyMTQsImF0IjozMzg5LCJidCI6MCwiY20iOjczMjI4MiwiY2giOjI5NTg1LCJjayI6e30sImNyIjoyNjAzNzI1NTksImRpIjoiNGVkZWI2YzdjYThlNGQ0NmJmYzM3OTJlMTZlMDcwNTAiLCJkaiI6MCwiaWkiOiJjZWY0N2Y4OTY5Njk0YmJiOTcyN2IzYjRhZTk3MWZmMCIsImRtIjozLCJmYyI6NDM5Njk5MTQ3LCJmbCI6NDI5NzE1NTU1LCJpcCI6IjUyLjIyLjI0MS42MyIsImt3IjoiY2F0X2NvbmNlcnRzLGRtYS41MSxlbi11cyIsIm1rIjoiZG1hLjUxIiwibnciOjEwMDg1LCJwYyI6MSwib3AiOjEsImVjIjo0Ljg0MDkyNiwiZ20iOjAsImVwIjpudWxsLCJwciI6MTE2NTMzLCJydCI6MywicnMiOjUwMCwic2EiOiI1NSIsInNiIjoiaS0wMGNiMjAyMzMzY2FjYmUxOSIsInNwIjo4MDA5MDAsInN0Ijo5NzgzNDIsInVrIjoidWUxLTdmYjNlMThkNzk1ODQ4NTJhNzgwMWRiNmQ2NGIwNmEyIiwiem4iOjE3ODIzNCwidHMiOjE2OTcxNDA4MTA3OTksInBuIjoiaGVyb18xIiwiZ2MiOnRydWUsImdDIjp0cnVlLCJncyI6Im5vbmUiLCJkYyI6MSwidHoiOiJBbWVyaWNhL05ld19Zb3JrIiwiZXQiOjN9%26s%3DDqqNwPT-Hb2ESSM01nKSXqWO9sY; azk=ue1-7fb3e18d79584852a7801db6d64b06a2; azk-ss=true; reese84=3:0DvzWGOHQGBJ/l3FHe3O+Q==:OYj3QTY8DddHLK6YugsapVwbb5fNIGvnAP3ukZU0kQMhxTfavf/OFXYFyllHjq4VSKQHatbObMSUAbgkZplDvkBEXmqZ9HlZ/Dv2yxyU2GGAoRtfqoolnP+XypgQrdWIezRsEfLf3SRKohyiYPjkr1wQ2lgRv/RC0xiKLv2jedMB8HNgqGoKZp8o0+nk6Vr4GgoH5qZqfqAeIeznMyhZD/WeaqeJ7eRaTHk7FuJ8Lj7KDNUz+n6HiUXPzpPrucmqIPuEHKXLMzZHDyU0SiZT8C7KbuEGj1UgIl/9hOgi2A38MHjB0WsWNkLrp+hx+OfCnLxQfO83Evd0m6gNMKnDoIMKRMW8tRK9Mxq0G+kspMNtDiI6u8zqJbKKpHrP+mstqyeCMK3CYjgwKUCn7tJB+s9zymzmF9BSacjEKISxUM3uCUa1zWNJImljwPF7WWKD3JYcE0NzL1ylWl9bIdrjpg==:PpFvLh2IGD6jZAIm6FWboRCkYXZBXMKRD3JJRfvJoIo=',
            'dnt': '1',
            'if-none-match': 'W/"yc9ifas2ht5hsp"',
            'referer': 'https://www.ticketmaster.com/travis-scott-utopia-tour-presents-circus-raleigh-north-carolina-10-14-2023/event/2D005F1FA3013F69',
            'sec-ch-ua': '"Chromium";v="117", "Not;A=Brand";v="8"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        }

        create_mapper_file(URL1,URL3, cookies_price , headers_price)
        fetch_and_save_data(URL2, HEADERS)

        
        
        data_v1 = load_json_file('data_v1.json')
        data_v2 = load_json_file('data_v2.json')
        mappers = load_json_file(MAPPER_FILE)

        changes_list = []

        # Iterate through data_v2 and compare with data_v1
        for item_v2 in data_v2:
            for item_v1 in data_v1:
                if (
                    item_v2['inventoryTypes'] == item_v1['inventoryTypes']
                    and item_v2['shapes'] == item_v1['shapes']
                ):
                    if item_v2['count'] > item_v1['count']:
                        shape_id = item_v2['shapes'][0]
                        # Find the corresponding shape in mappers.json
                        shape_info = next((x for x in mappers if x['id'] == shape_id), None)
                        if shape_info:
                            price = shape_info['price']
                            shape_name = shape_info['name']
                            id = shape_id  # Add id as it is
                            seat_type = item_v2['inventoryTypes']
                            
                            # Create a dictionary with price, shape, and id
                            changes_list.append({'id': id, 'price': price, 'seat_type': seat_type, 'shape_name': shape_name})
                            
    # Save the changes to a JSON file
    with open(OUTPUT_FILE, 'w') as json_file:
        json.dump(changes_list, json_file, indent=4)
        
    with open("final_output_data.json", "r") as file1:
        json1 = json.load(file1)
        print(json1)

    with open("event_data.json", "r") as file2:
        json2 = json.load(file2)
        json2 = json2[0]

    # Extract unique seat_type values from JSON 1
    unique_seat_types = list(set((entry["seat_type"])[0] for entry in json1))
    
    print(unique_seat_types)

    # Create a new list called 'seat_details' in json_2
    json2['seat_details'] = [json1]
    json2['seat_types_restocked'] = str(unique_seat_types)

    final_data = json2
    
    send_discord_alert(final_data)

    #Removing the old data file and just keeping the New File for the next Run        
    current_file_name = os.path.join(DATA_FOLDER, 'data_v2.json')
    new_file_name = os.path.join(DATA_FOLDER, 'data_v1.json')

    # Rename the file
    os.rename(current_file_name, new_file_name)

if __name__ == "__main__":
    main()
