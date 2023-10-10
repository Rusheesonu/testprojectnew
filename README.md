
# Event Ticket Monitor Readme

Overview
This Python script is designed to monitor changes in event ticket availability and send alerts to a Discord webhook when new tickets become available for specified events. It fetches data from Ticketmaster's APIs, compares it with previous data, and generates a report of changes.

Prerequisites
Before using this script, ensure you have the following:

Python installed (version 3.6 or higher)
Required Python libraries (requests, json) installed
Event IDs listed in a text file (event_ids.txt) to specify which events to monitor
Discord webhook URL to send alerts to Discord
