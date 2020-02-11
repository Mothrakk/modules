import random
import os
import json
from typing import List, Dict, Tuple

SIMPLIFICATIONS = (
    (1_000_000 * 1000, "B"),
    (1_000_000, "M")
)

def simplify_number(n: int) -> str:
    for scale, postfix in SIMPLIFICATIONS:
        r = n / scale
        if r >= 1:
            return f"{round(r, 2)}{postfix}"
    n = str(n)
    if len(n) == 5:
        return n[:2] + "," + n[2:]
    if len(n) == 6:
        return n[:3] + "," + n[3:]
    return n

def loot_to_str(loot: List["Drop"]) -> List[str]:
    compiled_loot = dict()
    total_gp = 0

    for i in loot:
        q, p = i.get_quantity_and_price()
        total_gp += p
        if i.name not in compiled_loot:
            compiled_loot[i.name] = {
                "price": p,
                "quantity": q,
                "type": i.type
            }
        else:
            compiled_loot[i.name]["price"] += p
            compiled_loot[i.name]["quantity"] += q

    out = list()
    
    for TYPE, type_data in Drop.TYPES.items():
        filtered_items = [i for i in compiled_loot if compiled_loot[i]["type"] == TYPE]
        if len(filtered_items):
            filtered_items = sorted(filtered_items, key=lambda i: compiled_loot[i]["price"], reverse=True)
            msg = []

            out.append(f"{type_data['name']} {type_data['emoji']}")
            msg.append("```")
            
            for i in filtered_items:
                msg.append(f"{compiled_loot[i]['quantity']}x {i} {simplify_number(compiled_loot[i]['price'])} gp")

            msg.append("```")
            out.append("\n".join(msg))
    
    working_i = 0
    while len(out) > 1 and working_i < (len(out) - 1):
        if len(out[working_i]) + len(out[working_i + 1]) <= 1999:
            out[working_i] += "\n" + out.pop(working_i + 1)
        else:
            working_i += 1
        
    out[-1] += f"\nKokku {simplify_number(total_gp)} gp :moneybag:"
    return out

class Chance:
    def __init__(self, rarity: str):
        if rarity == "Always":
            self.a = self.b = 1
        else:
            rarity = rarity.split(";")[0]
            self.a, self.b = rarity.replace(",", "").split("/")
            self.a = int(self.a)
            if len(frac := self.b.split(".")) > 1:
                self.a *= 10 ** len(frac[1])
                self.b = int("".join(frac))
            else:
                self.b = int(self.b)
    
    def roll(self) -> bool:
        return random.randint(1, self.b) <= self.a

class Drop:
    HERB = 0
    EQUIPMENT = 1
    SEED = 2
    RUNE = 3
    OTHER = 4
    GEMS = 5
    UNSORTED = -1
    TYPES = {
        EQUIPMENT: {
            "emoji": ":crossed_swords:",
            "name": "Varustus"
        },
        HERB: {
            "emoji": ":herb:",
            "name": "Ganja"
        },
        SEED: {
            "emoji": ":seedling:",
            "name": "Seeme"
        },
        RUNE: {
            "emoji": ":congratulations:",
            "name": "Rune"
        },
        GEMS: {
            "emoji": ":gem:",
            "name": "Kivid"
        },
        OTHER: {
            "emoji": ":bone:",
            "name": "Muu"
        },
        UNSORTED: {
            "emoji": ":grey_question:",
            "name": "Sorteerimata"
        }
    }

    def __init__(self, name: str, chance: Chance, price: str, quantity: str):
        self.name = name
        self.chance = chance
        if price == "Not sold":
            self.price = 0
        else:
            self.price = price.replace(",", "").replace("–", "-")
        self.quantity = quantity.replace(",", "").replace("\xa0(noted)", "").replace("–", "-")
        self.decide_type()

    def decide_type(self) -> None:
        if "Grimy" in self.name:
            self.type = Drop.HERB
        elif "rune" in self.name:
            self.type = Drop.RUNE
        elif "seed" in self.name:
            self.type = Drop.SEED
        elif "Uncut" in self.name:
            self.type = Drop.GEMS
        elif any(x in self.name for x in (
                "axe",
                "helm",
                "spear",
                "shield",
                "warhammer",
                "staff",
                "chainbody",
                "d'hide",
                "mask",
                "javelin",
                "arrow",
                "dagger",
                "longsword",
                "bolt",
                "Ensouled",
                "bow"
                )):
            self.type = Drop.EQUIPMENT
        elif any(x in self.name for x in (
                "logs",
                "bone",
                "ore",
                "Clue",
                "Coins",
                "Coal",
                "bar",
                "hammer",
                "Bone"
                )):
            self.type = Drop.OTHER
        else:
            self.type = Drop.UNSORTED

    def roll(self) -> bool:
        return self.chance.roll()

    def get_quantity_and_price(self) -> Tuple[int, int]:
        if "-" not in self.quantity:
            return int(self.quantity), int(self.price)
        a, b = (int(x) for x in self.quantity.split("-"))
        count = random.randint(a, b)
        price_of_one = int(self.price.split("-")[0]) // a
        return count, count * price_of_one

class DropTable:
    def __init__(self, drop_table: List[Drop]):
        self.drop_table = drop_table
    
    def simulate(self, times: int) -> List[Drop]:
        loot = list()
        while times:
            for drop in self.drop_table:
                if drop.roll():
                    loot.append(drop)
            times -= 1
        return loot

class LootSimManager:
    MAX_ALLOWED = 20_000

    def __init__(self, data_path: str):
        self.simulatable = dict()
        for fname in (x for x in os.listdir(data_path) if x.split(".")[1] == "json"):
            monster = fname.split(".")[0]
            with open("\\".join([data_path, fname]), "r") as fptr:
                json_data = json.load(fptr)
            drops = [
                Drop(
                    item["name"],
                    Chance(item["rarity"]),
                    item["price"],
                    item["quantity"]
                ) for item in json_data
            ]
            self.simulatable[monster] = DropTable(drops)

    def handle(self, message) -> List[str]:
        spl = [x for x in message.content.lower().split(" ") if x]
        if len(spl) > 2:
            k = " ".join(spl[1:-1])
            if k in self.simulatable:
                if spl[-1].isnumeric():
                    times = int(spl[-1])
                    if 1 <= times <= LootSimManager.MAX_ALLOWED:
                        if times > 1:
                            out = [f"{k.capitalize()} {times} korda\n"]
                        else:
                            out = [f"{k.capitalize()} {times} kord\n"]
                        loot = self.simulatable[k].simulate(times)
                        out += loot_to_str(loot)
                        return out
        return [f"lootsim ({' | '.join(self.simulatable)}) (1 <= kogus <= {LootSimManager.MAX_ALLOWED})"]
