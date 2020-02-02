import requests
import bs4
from typing import Dict

SHITRS_SKILL_LOOKUP = {0: 'Overall', 1: 'Attack', 2: 'Defence', 3: 'Strength',
    4: 'Constitution', 5: 'Ranged', 6: 'Prayer', 7: 'Magic',
    8: 'Cooking', 9: 'Woodcutting', 10: 'Fletching', 11: 'Fishing',
    12: 'Firemaking', 13: 'Crafting', 14: 'Smithing', 15: 'Mining',
    16: 'Herblore', 17: 'Agility', 18: 'Thieving', 19: 'Slayer',
    20: 'Farming', 21: 'Runecrafting', 22: 'Hunter', 23: 'Construction',
    24: 'Summoning', 25: 'Dungeoneering', 26: 'Divination', 27: 'Invention'}

def osrs(players: Dict[str, str]) -> Dict[str, Dict[str, int]]:
    completed_data = dict()
    for name, url in players.items():
        response = requests.get(url)
        parsed = bs4.BeautifulSoup(response.content, "lxml")
        player_data = dict()
        main = parsed.find("div", {"id":"contentHiscores"})
        rows = main.find_all("tr")[3:27]
        for r in rows:
            skill = r.find("a").text.strip()
            rank, level, xp = [int(x.text.strip().replace(",", "")) for x in r.find_all("td")[2:]]
            player_data[skill] = {
                "rank": rank,
                "level": level,
                "xp": xp
            }
        completed_data[name] = player_data
    return completed_data

def shitrs(players: Dict[str, str]) -> Dict[str, Dict[str, int]]:
    completed_data = dict()
    for name, url in players.items():
        response = requests.get(url)
        parsed = bs4.BeautifulSoup(response.content, "lxml")
        player_data = dict()
        main = parsed.find("table", {"class":"headerBgLeft"})
        rows = main.find("tbody").find_all("tr")
        for i, r in enumerate(rows):
            rank, xp, level = [a.text.strip().replace(",", "") for a in r.find_all("a")]
            if rank != "--":
                rank = int(rank)
                xp = int(xp)
                level = int(level)
            player_data[SHITRS_SKILL_LOOKUP[i]] = {
                "rank": rank,
                "xp": xp,
                "level": level
            }
        completed_data[name] = player_data
    return completed_data

