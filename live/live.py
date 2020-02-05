import sys
import requests
import json
import os
import subprocess
boiler_path = "\\".join(sys.argv[0].split("\\")[:-2])
sys.path.append(boiler_path)
import PyBoiler

REFRESH_RATE = 60
ticks = REFRESH_RATE - 1
my = PyBoiler.Boilerplate()

with open(f"{my.module_path}\\client_id.txt", "r") as fptr:
    client_id = fptr.read().strip()
with open(f"{my.module_path}\\tracking.txt", "r") as fptr:
    tracking = set(fptr.read().strip().split("\n"))

custom_headers = {'Client-ID':client_id}
query = "https://api.twitch.tv/helix/streams?" + "&".join([f"user_login={x}" for x in tracking])

last_tick_online = set()
while PyBoiler.tick(1):
    ticks = (ticks + 1) % REFRESH_RATE
    if not ticks:
        response = requests.get(query, headers=custom_headers)
        parsed = json.loads(response.content)
        d = dict()
        for streamer_data in parsed["data"]:
            d[streamer_data["user_name"]] = streamer_data
        
        now_online = set(d)
        new_online = set.difference(now_online, last_tick_online)
        for name in new_online:
            PyBoiler.Log("-----"*2).to_larva()
            PyBoiler.Log(f"{name} online").to_larva()
            PyBoiler.Log(f"Title: {d[name]['title']}").to_larva()
            PyBoiler.Log(f"https://www.twitch.tv/{name}").to_larva()
            PyBoiler.Log("-----"*2).to_larva()
        last_tick_online = now_online

    for line in my.read_from_larva():
        subprocess.run(f"start https://www.twitch.tv/{line}", shell=True)