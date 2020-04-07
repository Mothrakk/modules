import json
import requests
import bs4
import os

from typing import Dict, Union, List

class StatEmojis:
    @staticmethod
    def get(name: str) -> str:
        return {
            "Overall": ":bar_chart:",
            "Attack": ":crossed_swords:",
            "Defence": ":shield:",
            "Strength": ":fist:",
            "Hitpoints": ":heart:",
            "Constitution": ":heart:",
            "Ranged": ":bow_and_arrow:",
            "Prayer": ":star:",
            "Magic": ":man_mage:",
            "Cooking": ":cooking:",
            "Woodcutting": ":axe:",
            "Fletching": ":dagger:",
            "Fishing": ":fishing_pole_and_fish:",
            "Firemaking": ":fire:",
            "Crafting": ":tools:",
            "Smithing": ":hammer:",
            "Mining": ":pick:",
            "Herblore": ":smoking:",
            "Agility": ":man_running_tone5:",
            "Thieving": ":man_detective_tone5:",
            "Slayer": ":skull_crossbones:",
            "Farming": ":seedling:",
            "Runecrafting": ":congratulations:",
            "Runecraft": ":congratulations:",
            "Hunter": ":rabbit2:",
            "Construction": ":moneybag: :fire:",
            "Summoning": ":ghost:",
            "Dungeoneering": ":mountain_snow:",
            "Divination": ":regional_indicator_g: :regional_indicator_a: :regional_indicator_y:",
            "Invention": ":wrench:"
        }[name]

class RunescapeType:
    OSRS = 0
    RS3 = 1
    def __init__(self, url: str):
        self.url = url
        self.type = RunescapeType.RS3 if "runemetrics" in url else RunescapeType.OSRS

class Stat:
    def __init__(self, name: str, rank: int, level: int, xp: int):
        self.name = name
        self.rank = rank
        self.level = level
        self.xp = xp

    def __lt__(self, other) -> bool:
        return self.level < other.level
    def __gt__(self, other) -> bool:
        return self.level > other.level
    def __ge__(self, other) -> bool:
        return self.level >= other.level
    def __le__(self, other) -> bool:
        return self.level <= other.level

    def build_delta_string(self, old: "Stat", username: str):
        out = [f"{username} sai leveli skillis {self.name}! {self.emoji}"]
        for p_name, self_p, old_p in zip( ("Level", "Rank", "XP"),
                                          (self.level, self.rank, self.xp),
                                          (old.level, old.rank, old.xp) ):
            out.append(f"{p_name}: {old_p} -> {self_p}")
        return "\n".join(out)

    @property
    def _dict(self) -> Dict[str, int]:
        return {
            "rank": self.rank,
            "level": self.level,
            "xp": self.xp
        }
    
    @property
    def emoji(self) -> str:
        return StatEmojis.get(self.name)

class StatCollection:
    def __init__(self, get_from: str = None):
        self.stats = dict()
        if get_from is not None:
            if get_from.startswith("http"):
                self.fetch(get_from)
            else:
                self.read(get_from)
    
    def __str__(self) -> str:
        return "\n\n".join(
            (str(stat) for stat in self.ordered)
        )

    def add(self, stat: Stat) -> None:
        self.stats[stat.name] = stat

    def fetch(self, url: str) -> None:
        response = requests.get(url)
        parsed = bs4.BeautifulSoup(response.content, "html.parser")
        table = parsed.find("div", {"id":"contentHiscores"})
        relevant_rows = table.findAll("tr")[3:27]
        for r in relevant_rows:
            columns = r.findAll("td")[1:]
            name = columns[0].text.strip()
            rank, level, xp = (int(c.text.replace(",", "")) for c in columns[1:])
            self.add(Stat(name, rank, level, xp))

    def read(self, path: str) -> None:
        if os.path.exists(path):
            with open(path, "r") as fptr:
                raw = json.load(fptr)
            for name, skill_data in raw.items():
                self.add(Stat(name, skill_data["rank"], skill_data["level"], skill_data["xp"]))

    def write(self, path: str) -> None:
        if "\\" in path:
            os.makedirs("\\".join(path.split("\\")[:-1]), exist_ok=True)
        with open(path, "w") as fptr:
            json.dump(self._dict, fptr)

    def get(self, stat_name: str = None) -> Union[dict, Stat]:
        if stat_name is None:
            return self.stats
        return self.stats[stat_name]

    def delta(self, other: "StatCollection") -> "StatCollection":
        d = StatCollection()
        other_stats = other.get()
        for stat_name, stat in self.stats.items():
            if stat_name in other_stats and stat > other_stats[stat_name]:
                d.add(stat)
        return d

    def build_delta_string(self, other: "StatCollection", username: str) -> str:
        out = list()
        for stat in self.ordered:
            s = stat.build_delta_string(other.get(stat.name), username)
            if stat.name != "Overall":
                out.append(s)
            else:
                overall_text = s
        out.append(overall_text)
        return "\n\n".join(out)

    @property
    def ordered(self) -> List[Stat]:
        return sorted(self.stats.values(), key=lambda stat: stat.name)

    @property
    def _dict(self) -> Dict[str, Dict[str, int]]:
        return {
            stat.name: stat._dict for stat in self.stats.values()
        }

    @property
    def empty(self) -> bool:
        return not len(self.stats)

class ActivityFeed:
    def __init__(self, get_from: str = None):
        self.activities = list()
        if get_from is not None:
            if get_from.startswith("http"):
                self.fetch(get_from)
            else:
                self.read(get_from)

    def add(self, activity: str) -> None:
        self.activities.append(activity)

    def fetch(self, url: str) -> None:
        response = requests.get(url)
        parsed = json.loads(response.content)
        self.activities = [parsed["activities"][i]["details"] for i in range(len(parsed["activities"]))]

    def read(self, path: str):
        if os.path.exists(path):
            with open(path, "r") as fptr:
                self.activities = fptr.read().strip().split("\n")

    def write(self, path: str):
        if "\\" in path:
            os.makedirs("\\".join(path.split("\\")[:-1]), exist_ok=True)
        with open(path, "w") as fptr:
            fptr.write("\n".join(self.activities))

    def difference(self, other: "ActivityFeed") -> "ActivityFeed":
        diff = ActivityFeed()
        for activity in self.activities:
            if activity not in other.activities:
                diff.add(activity)
        return diff

    def to_string(self, prefix: str) -> str:
        return "\n".join((f"{prefix}: {activity}" for activity in self.activities))

    def empty(self) -> bool:
        return not len(self.activities)
