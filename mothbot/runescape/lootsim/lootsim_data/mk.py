import json
import requests
import bs4

RELEVANT_CLASS = "wikitable sortable filterable item-drops autosort=4,a"
URL = "https://oldschool.runescape.wiki/w/Lizardman_shaman"

response = requests.get(URL)
parsed = bs4.BeautifulSoup(response.content, "lxml")

data = list()
tables = parsed.find_all("table", {"class":RELEVANT_CLASS})


for table in tables:
    for row in table.find_all("tr")[1:]:
        columns = row.find_all("td")
        d = {
            "name": columns[1].find("a").text.strip(),
            "quantity": columns[2].text.strip(),
            "price": row.find("td", {"class":"ge-column"}).text.strip()
        }
        rarity = columns[3].find("span")
        try:
            d["rarity"] = rarity["data-drop-oneover"].strip()
        except KeyError:
            d["rarity"] = rarity.text.strip()
        data.append(d)

json.dump(data, open("lizardman shaman.json", "w"))
