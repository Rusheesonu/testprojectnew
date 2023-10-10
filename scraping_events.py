import requests
import re
import json

def extract_event_data_to_json(event_ids, output_file):
    event_data_list = []

    for event_id in event_ids:
        try:
            # Construct the URL for the event ID
            url = f'https://proxy.scrapeops.io/v1/?api_key=267de23e-a363-4c82-96c9-d5863d4f3ef3&url=https://www.ticketmaster.com/event/{event_id}&render_js=true&bypass=perimeterx'

            # Send an HTTP GET request to the URL
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception if the request was not successful
            
            # Decode the response content to a string
            page_content = response.text
            
            # Use regular expressions to find JSON data within script tags
            json_matches = re.findall(r'<script type="application/ld\+json" data-bdd="([^"]+)">(.*?)</script>', page_content)

            for json_key, json_data in json_matches:
                try:
                    parsed_data = json.loads(json_data)
                    event_title = parsed_data.get("name")
                    event_date = parsed_data.get("startDate")
                    location = parsed_data.get("location")
                    image = parsed_data.get("image")
                    event_url = parsed_data.get("url")
                    
                    event_info = {
                        "Event ID": event_id,  # Include Event ID in the dictionary
                        "Event Title": event_title,
                        "Event Date": event_date,
                        "Location": location,
                        "Image URL": image,
                        "Event URL": event_url
                    }
                    event_data_list.append(event_info)
                except json.JSONDecodeError:
                    print(f"Invalid JSON for event ID {event_id}, JSON key: {json_key}\n")
        except requests.exceptions.RequestException as e:
            print(f"Request failed for event ID {event_id}: {e}")
        except Exception as e:
            print(f"An error occurred for event ID {event_id}: {e}")

    # Write the extracted event data to a JSON file
    if event_data_list:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(event_data_list, json_file, ensure_ascii=False, indent=4)
            print(f'Data has been written to {output_file}')
    else:
        print("No valid event data to write.")

if __name__ == "__main__":
    try:
        # Read event IDs from a text file
        with open('event_ids.txt', 'r') as id_file:
            event_ids = [line.strip() for line in id_file.readlines()]

        if event_ids:
            output_file = 'event_data.json'
            extract_event_data_to_json(event_ids, output_file)
        else:
            print("No event IDs found in the input file.")
    except FileNotFoundError:
        print("Input file 'event_ids.txt' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
