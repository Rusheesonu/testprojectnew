import requests
import json
import time
import os

# Constants
DATA_FOLDER = 'data'
MAPPER_FILE = 'mappers.json'
file_name = 'data_v2' + '.json'
OUTPUT_FILE = 'final_output_data.json'
webhook_url = "https://discord.com/api/webhooks/1161306474014842941/0ixkJWR54wgrT2hqppNqoUlqKPE-tNpC_FuBnSuioUFJgUMjBGF3vfplE2XPM_PdeE-O"


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
def send_discord_alert(event_name, data_to_send):
    # Define the message content
    message = {
        "content": f"Event Restocked: {event_name}, {data_to_send}"
    }

    try:
        # Send a POST request to the Discord webhook
        response = requests.post(
            webhook_url,
            data=json.dumps(message),
            headers={'Content-Type': 'application/json'}
        )

        # Check if the request was successful
        if response.status_code == 204:
            print("Alert sent to Discord.")
        else:
            print("Failed to send alert to Discord. Status code:", response.status_code)
    except Exception as e:
        print("An error occurred:", str(e))
        
def create_mapper_file(URL1, HEADERS):
    if os.path.exists(os.path.join(DATA_FOLDER, MAPPER_FILE)):
        print("Mapper file already exists. Skipping creation.")
        return

    print("Creating Mapper file...")
    
    response = requests.get(URL1, headers=HEADERS)
    data = response.json()
    pages = data.get("pages")
    segments = pages[0]['segments']

    output_data = [{"id": segment["id"], "name": segment["name"]} for segment in segments]

    output_file = os.path.join(DATA_FOLDER, MAPPER_FILE)

    with open(output_file, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f'Mapper file has been created at {output_file}')

# Fetch data from URLs and save to files
def fetch_and_save_data(URL1, URL2, HEADERS):
    try:
        # Fetch data from URL1
        response = requests.get(URL1, headers=HEADERS)
        data = response.json()
        pages = data.get("pages")
        segments = pages[0]['segments']

        output_data = [{"id": segment["id"], "name": segment["name"]} for segment in segments]

        output_file = os.path.join(DATA_FOLDER, MAPPER_FILE)

        with open(output_file, 'w') as json_file:
            json.dump(output_data, json_file, indent=4)

        print(f'Mapper file has been created at {output_file}')
    except Exception as e:
        print(f"An error occurred while fetching data from URL1: {e}")

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

        create_mapper_file(URL1, HEADERS)
        fetch_and_save_data(URL1, URL2, HEADERS)

        data1 = load_json_file('data_v1.json')
        data2 = load_json_file('data_v2.json')
        mappers_data = load_json_file(MAPPER_FILE)

        id_to_name = {item['id']: item['name'] for item in mappers_data}

        for record2 in data2:
            matching_record = next(
                (record1 for record1 in data1 if record1["shapes"] == record2["shapes"] and record1["inventoryTypes"] == record2["inventoryTypes"]),
                None,
            )
            if matching_record is not None and record2["count"] > matching_record["count"]:
                shape_id = record2["shapes"][0]
                name = id_to_name.get(shape_id, "Name not found")
                print("Count in file 2 is greater for Shape:", shape_id)
                print("Name from mappers:", name)
            
                # Append changes to the list
                changes_list.append({"id": event_id, "count": record2["count"], "name": name})

    # Save the changes to a JSON file
    with open(OUTPUT_FILE, 'w') as json_file:
        json.dump(changes_list, json_file, indent=4)
        
    with open("final_output_data.json", "r") as file1:
        json1 = json.load(file1)

    with open("event_data.json", "r") as file2:
        json2 = json.load(file2)

    json1_map = {entry["id"]: entry for entry in json1}

    # Create a list to store the merged data
    merged_data = []

    # Iterate through JSON 2 data and merge with JSON 1 data
    for entry in json2:
        tmp_id = entry.get("Event ID")
        if tmp_id in json1_map:
            merged_entry = entry.copy()
            merged_entry["new_seats"] = [json1_entry["name"] for json1_entry in json1 if json1_entry["id"] == tmp_id]
            merged_data.append(merged_entry)

    # Print the merged data
    data_to_send = (json.dumps(merged_data, indent=4))


    print(data_to_send)
    
    event_name = "New Tickets Available"  # Replace with the actual event name
    
    if data_to_send != []:
        send_discord_alert(event_name, data_to_send)
    else:
        print("No Changes")

    # Removing the old data file and just keeping the New File for the next Run        
    current_file_name = os.path.join(DATA_FOLDER, 'data_v2.json')
    new_file_name = os.path.join(DATA_FOLDER, 'data_v1.json')

    # Rename the file
    os.rename(current_file_name, new_file_name)

if __name__ == "__main__":
    main()
