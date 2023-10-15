import requests
import json
import os
import discord
import re
import sys

# Constants
DATA_FOLDER = 'data'
MAPPER_FILE = 'mappers.json'
file_name = 'data_v2.json'
OUTPUT_FILE = 'final_output_data.json'

# Function to send Discord alerts
def send_discord_alert(final_data):
    
    # Define your intents
    intents = discord.Intents.default()
    intents.typing = False  # Disable typing event (optional)
    
    # Initialize a Discord client
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'Logged in as {client.user.name} ({client.user.id})')

        channel_name = 'general'  # Replace with your desired channel name
        guild = discord.utils.get(client.guilds, name='TestServer')  # Replace with your server's name
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        
        total_seats = []
        split_json_lists = []
        try:
            # Extract data from final_data
            event_title = final_data.get("Event Title")
            event_date = final_data.get("Event Date")
            location = final_data.get("Location")
            address = location.get("address")
            addressLocality = address.get("addressLocality")
            addressRegion = address.get("addressRegion")
            total_seats_tmp = final_data.get("seat_details")
            total_seats = [{'price': item['price'], 'seat_number': item['shape_name']} for item in total_seats_tmp]
            chunk_size = 20
            # this is because discord only allows 1024 characters !
            split_json_lists = [total_seats[i:i + chunk_size] for i in range(0, len(total_seats), chunk_size)]
            seat_types_restocked = final_data.get("seat_types_restocked")
        except Exception as e:
            print(f"Error extracting data: {e}")
            pass

        if channel:
            # Create and send the Discord embed
            embed = discord.Embed(
                title=f'Restock Alert For {event_title}, {event_date}, AT {addressLocality} {addressRegion} | TicketMaster',
                description=f'{len(total_seats)} Seats have been Restocked',
                color=discord.Color.blue()
            )
            
            # Add seat details to the embed
            for i in split_json_lists:
                embed.add_field(name="Seat Details", value=json.dumps(i), inline=False)

            embed.add_field(name="Seat Type Restocked", value=str(seat_types_restocked), inline=False)

            await channel.send(embed=embed)
            
            sys.exit()

    # Start the bot with your token
    client.run('MTE2MTM2ODIyNzE1OTQ5NDczNg.GhiZiq.QOi_s1WzehI_7-bxtLoE4wCkvEvK1vU3e7kDOk')

# Create a mapper file
def create_mapper_file(URL1, URL3, cookies_price, headers_price):
    if os.path.exists(os.path.join(DATA_FOLDER, MAPPER_FILE)):
        print("Mapper file already exists. Skipping creation.")
        return

    print("Creating Mapper file...")
    
    # Fetch and process data from URL1
    response = requests.get(URL1, headers=headers_price)
    data = response.json()
    pages = data.get("pages")
    segments = pages[0]['segments']
    output_data = [{"id": segment["id"], "name": segment["name"]} for segment in segments]

    # Fetch and process data from URL3
    price_respone = requests.get(URL3, cookies=cookies_price, headers=headers_price)
    price_data = price_respone.text
    list2 = re.findall(r'\\\"shapes\\\":\[(.*?)\]', price_data)
    list1 = re.findall(r'\"listPriceRange\\\"\:\[{\\\"currency\\\"\:\\\"USD\\\",\\\"min\\\":(.*?),', price_data)
    result_dict = {}

    # Check if the lengths of both lists are the same
    if len(list1) == len(list2):
        for value, key in zip(list1, list2):
            match = re.search(r's_\d+', key)
            if match:
                s_number = match.group()
                result_dict[s_number] = value
    else:
        print("The lengths of the two lists are not the same.")

    # Create dictionaries based on 'id' values in output_data and merge with result_dict
    dict1_id_dict = {item['id']: item['name'] for item in output_data}
    merged_dict = [{'id': key, 'price': result_dict.get(key, None), 'name': dict1_id_dict.get(key, None)} for key in result_dict]

    # Save the mapper file
    output_file = os.path.join(DATA_FOLDER, MAPPER_FILE)
    with open(output_file, 'w') as json_file:
        json.dump(merged_dict, json_file, indent=4)
    print(f'Mapper file has been created at {output_file}')

# Fetch data from URLs and save to files
def fetch_and_save_data(URL2, HEADERS):
    try:
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
                'NATIVE': '%2Fnative%2Fconversion%2Fe.gif%3Fe%3DeyJ2IjoiMS4xMSIsImF2IjozNjcyMTQsImF0IjozMzg5LCJidCI6MCwiY20iOjczMjI4MiwiY2giOjI5NTg1LCJjayI6e30sImNyIjoyNjAzNzI1NTksImRpIjoiNGVkZWI2YzdjYThlNGQ0NmJmYzM3OTJlMTZlMDcwNTAiLCJkaiI6MCwiaWkiOiJjZWY0N2Y4OTY5Njk0YmJiOTcyN2IzYjRhZTk3MWZmMCIsImRtIjozLCJmYyI6NDM5Njk5MTQ3LCJmbCI6NDI5NzE1NTU1LCJpcCI6IjUyLjIyLjI0MS42MyIsImt3IjoiY2F0X2NvbmNlcnRzLGRtYS41MSxlbi11cyIsIm1rIjoiZG1hLjUxIiwibnciOjEwMDg1LCJwYyI6MSwib3AiOjEsImVjIjo0Ljg0MDkyNiwiZ20iOjAsImVwIjpudWxsLCJwciI6MTE2NTMzLCJydCI6MywicnMiOjUwMCwic2EiOiI1NSIsInNiIjoiaS0wMGNiMjAyMzMzY2FjYmUxOSIsInNwIjo4MDA5MDAsInN0Ijo5NzgzNDIsInVrIjoidWUxLTdmYjNlMThkNzk1ODQ4NTJhNzgwMWRiNmQ2NGIwNmEyIiwiem4iOjE3ODIzNCwidHMiOjE2OTcxNDA4MTA3OTksInBuIjoiaGVyb18xIiwiZ2MiOnRydWUsImdDIjp0cnVlLCJncyI6Im5vbmUiLCJkYyI6MSwidHoiOiJBbWVyaWNhL05ld19Zb3JrIiwiZXQiOjN9%26s%3DDqqNwPT-Hb2ESSM01nKSXqWO9sY',
                'azk': 'ue1-7fb3e18d79584852a7801db6d64b06a2',
                'azk-ss': 'true',
                'discovery_location': '%7B%22geoHash%22%3A%22tepg%22%2C%22latLong%22%3A%2217.500%2C78.610%22%7D',
                'reese84': '3:RYT+MtV1c0mA0F5edDOpoQ==:W5FXLeImQkim4S+TYLL8qinoaEQb7PAL1uAGFKIBuwiuilZsfmMq2CRVl8bQWi/cxKw0GC8fFXf5bDMfF4jCBejBYmZVecyunn7P5IEjSXp3J/xB9LqqIeYrDdjG+BzzhrYmCOZ8dlX9mhqOaRos2pKaQasHo5Fabxcl8lDb/U0VdlyJSDwj84N2jJ+bXaP4j530NQP4imneG7DIb1PqvAGlDZRaRmEfrNhAYKm3ECdww2NbOJe9D5DaoYVBpTuouJVSxN7OkxgJaIq+wyDCoJ9cYD75WXWPOckObrGAj4YxvHhOfs1J8PYgiYMZwrJpSAUvxEUn6bsO5qeOK9Y/FaU8k5lzw5zExy+UxL7CpYFHLPdqYuLyxiBZntcBVzEF7/wb/BhGlfyeQaVS7nQrJPMdyzjOmsocUKON/S0PZHoDdlc4jP9xECSnTIj0Y4zw7TH0tdqkFrL3i1YCuh5kbQ==:wqUhth3CUXY1bTSAXpGNnGUdsrtNOnaSXcdx8fS3bGc=',
                'tmsid': '0833bfc6-2ee4-419f-8983-f71ea1e3c73e',
                'tmdl': '0',
            }



        headers_price = {
            'authority': 'www.ticketmaster.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            # 'cookie': 'eps_sid=e7a6d93eee084b6bdbc09d42a92c2ddc6cd389b5; lightstep_guid%2Fco2.sdk=44434edb2e64a27f; lightstep_session_id=6d5d860e6b72d652; TMUO=west_SPb9YyInjChFYrizst3Dp16FHEq2kbVQg+YNNiTdhls=; lightstep_guid%2Fedp.app=2f33731c4a843833; LANGUAGE=en-us; SID=Bkjpd6KzC0kBVU6LUrE8Bd6SvqYaCOgkRz0LZRhFtfzMiBObMqHsO0F1ulqrSpxA17yK8JiQXBjeQGj3oMqi; BID=KyVkTn7E4X2ntuXoLoBmrlbfO7XRIUnsjA7L-4ILrOS9bzQmfjXvAx7Y6rVyGUUuwfNDgPUG3lXz1mw; mt.v=5.1480159744.1696928485846; tmff=; NDMA=200; ms_visitorid=5ea65d62-dd54-12c4-57b4-c81f00ee0fa2; NATIVE=%2Fnative%2Fconversion%2Fe.gif%3Fe%3DeyJ2IjoiMS4xMSIsImF2IjozNjcyMTQsImF0IjozMzg5LCJidCI6MCwiY20iOjczMjI4MiwiY2giOjI5NTg1LCJjayI6e30sImNyIjoyNjAzNzI1NTksImRpIjoiNGVkZWI2YzdjYThlNGQ0NmJmYzM3OTJlMTZlMDcwNTAiLCJkaiI6MCwiaWkiOiJjZWY0N2Y4OTY5Njk0YmJiOTcyN2IzYjRhZTk3MWZmMCIsImRtIjozLCJmYyI6NDM5Njk5MTQ3LCJmbCI6NDI5NzE1NTU1LCJpcCI6IjUyLjIyLjI0MS42MyIsImt3IjoiY2F0X2NvbmNlcnRzLGRtYS41MSxlbi11cyIsIm1rIjoiZG1hLjUxIiwibnciOjEwMDg1LCJwYyI6MSwib3AiOjEsImVjIjo0Ljg0MDkyNiwiZ20iOjAsImVwIjpudWxsLCJwciI6MTE2NTMzLCJydCI6MywicnMiOjUwMCwic2EiOiI1NSIsInNiIjoiaS0wMGNiMjAyMzMzY2FjYmUxOSIsInNwIjo4MDA5MDAsInN0Ijo5NzgzNDIsInVrIjoidWUxLTdmYjNlMThkNzk1ODQ4NTJhNzgwMWRiNmQ2NGIwNmEyIiwiem4iOjE3ODIzNCwidHMiOjE2OTcxNDA4MTA3OTksInBuIjoiaGVyb18xIiwiZ2MiOnRydWUsImdDIjp0cnVlLCJncyI6Im5vbmUiLCJkYyI6MSwidHoiOiJBbWVyaWNhL05ld19Zb3JrIiwiZXQiOjN9%26s%3DDqqNwPT-Hb2ESSM01nKSXqWO9sY; azk=ue1-7fb3e18d79584852a7801db6d64b06a2; azk-ss=true; discovery_location=%7B%22geoHash%22%3A%22tepg%22%2C%22latLong%22%3A%2217.500%2C78.610%22%7D; reese84=3:RYT+MtV1c0mA0F5edDOpoQ==:W5FXLeImQkim4S+TYLL8qinoaEQb7PAL1uAGFKIBuwiuilZsfmMq2CRVl8bQWi/cxKw0GC8fFXf5bDMfF4jCBejBYmZVecyunn7P5IEjSXp3J/xB9LqqIeYrDdjG+BzzhrYmCOZ8dlX9mhqOaRos2pKaQasHo5Fabxcl8lDb/U0VdlyJSDwj84N2jJ+bXaP4j530NQP4imneG7DIb1PqvAGlDZRaRmEfrNhAYKm3ECdww2NbOJe9D5DaoYVBpTuouJVSxN7OkxgJaIq+wyDCoJ9cYD75WXWPOckObrGAj4YxvHhOfs1J8PYgiYMZwrJpSAUvxEUn6bsO5qeOK9Y/FaU8k5lzw5zExy+UxL7CpYFHLPdqYuLyxiBZntcBVzEF7/wb/BhGlfyeQaVS7nQrJPMdyzjOmsocUKON/S0PZHoDdlc4jP9xECSnTIj0Y4zw7TH0tdqkFrL3i1YCuh5kbQ==:wqUhth3CUXY1bTSAXpGNnGUdsrtNOnaSXcdx8fS3bGc=; tmsid=0833bfc6-2ee4-419f-8983-f71ea1e3c73e; tmdl=0',
            'dnt': '1',
            'if-none-match': 'W/"11jo6cra1hl582x"',
            'referer': 'https://www.ticketmaster.com/travis-scott-tickets/artist/1788754',
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
        
        create_mapper_file(URL1, URL3, cookies_price, headers_price)
        fetch_and_save_data(URL2, HEADERS)

        data_v1 = load_json_file('data_v1.json')
        data_v2 = load_json_file('data_v2.json')
        mappers =  load_json_file('mappers.json')

        # Check for changes between data_v1 and data_v2
        changes = check_changes(data_v1, data_v2, mappers)

        if changes:
            changes_list.append(changes)
        
    if changes_list:
        # Notify Discord with the changes
        output_event_data = load_json_file("/Users/anillusion/Documents/neuronaio/event_data.json")
        output_event_data = (output_event_data)[0]
        unique_seat_types = list(set((entry["inventoryTypes"])[0] for entry in data_v2))
        output_event_data['seat_types_restocked'] = list(unique_seat_types)
        output_event_data['seat_details'] = (changes_list)[0]
        
        #Removing the old data file and just keeping the New File for the next Run        
        current_file_name = os.path.join(DATA_FOLDER, 'data_v2.json')
        new_file_name = os.path.join(DATA_FOLDER, 'data_v1.json')
        

        # Rename the file
        os.rename(current_file_name, new_file_name)
        
        
        #Sending Discord Alert
        send_discord_alert(output_event_data)
        

# Function to read event IDs from a file
def read_event_ids_from_file(filename):
    try:
        with open(filename, 'r') as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
        return []
    except Exception as e:
        print(f"An error occurred while reading event IDs from '{filename}': {e}")
        return []

# Function to compare two JSON files and find the changes
def check_changes(data_v1, data_v2, mappers):
    changes = []
    
    for item_v1 in data_v1:
        for item_v2 in data_v2:
            if item_v1['shapes'] == item_v2['shapes'] and item_v1['inventoryTypes'] == item_v2['inventoryTypes']:
                if item_v2['count'] > item_v1['count']:
                    # Find the corresponding shape in mappers.json
                    shape_id = item_v2['shapes'][0]
                    shape_info = next((x for x in mappers if x['id'] == shape_id), None)
                    changes.append({
                        "count": item_v2['count'],
                        "shape_name": item_v1['shapes'],
                        "price": shape_info['price']
                    })
                break
    return changes

if __name__ == "__main__":
    main()
