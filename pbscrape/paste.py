import os
import time
import re
import requests
import bs4
import sys
boiler_path = "\\".join(sys.argv[0].split("\\")[:-2])
sys.path.append(boiler_path)
import PyBoiler

def request_wrap(CFG: dict, href: str = "") -> bs4.BeautifulSoup:
    """
    A wrap for making a request and handling any unsatisfying error codes. \n
    Returns either a BeautifulSoup (parsed) object or None, depending on how the request went.
    """
    fatal_errors = {
        403:"Blocked from pastebin",
        503:"Pastebin under protection"
    }
    url = CFG["BASE_URL"] + href

    #print(f"\n[{url}] Fetching")
    r = requests.get(url, headers=CFG["HEADERS"])
    time.sleep(int(CFG["sleep_s"])) # Attempt to avoid getting banned from pastebin by limiting requests/h

    if r.status_code == 200:
        return bs4.BeautifulSoup(r.content, "lxml")
    elif r.status_code in fatal_errors.keys():
        PyBoiler.Log(fatal_errors[r.status_code]).to_larva()
        PyBoiler.Log("Sleeping for 30m").to_larva()
        time.sleep(30*60)
    elif r.status_code == 404:
        #print(f"[{url}] Paste expired")
        pass
    else:
        PyBoiler.Log(f"[{url}] Unknown error: {r.status_code}").to_larva()

    return None

class paste:
    """ Class for working with a parsed pastebin response/bs4 object. """
    def __init__(self, CFG: dict, href: str, parsed: bs4.BeautifulSoup, module_path: str):
        self.module_path = module_path
        self.url = CFG["BASE_URL"] + href
        self.CFG = CFG
        self.parsed = parsed
        code_buttons = parsed.find("div", {"id":"code_buttons"})
        self.public = (code_buttons != None) # Evaluates to true if public paste
        self.keywords = []
        if self.public:
            self.type = code_buttons.find("a", {"class":"buttonsm"}).text
            if self.type == "raw":
                self.size = code_buttons.text
                container = parsed.find("ol", {"class":"text"})
                if container != None:
                    self.text_block = "\n".join([e.text for e in container.findAll("div")])
                    self.text_block_lowercase = self.text_block.lower()
                    for kw in CFG["KEYWORDS"]:
                        if kw in self.text_block_lowercase:
                            self.keywords.append(kw)

    def store(self):
        """ Stores the paste into a text file. """
        # Assign directory
        path = time.strftime(self.module_path + f"\\matches\\{self.CFG['version']}\\%Y\\%B\\%d\\") # example: "matches\\v3\\2018\\6\\2\\"
        if os.path.exists(path):
            path += f"{len([name for name in os.listdir(path)]) + 1}.txt" # one-up
        else:
            os.makedirs(path)
            path += "1.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{self.url}\n")
            f.write(f"{time.strftime('%H:%M:%S')}\n")
            f.write(f"{'; '.join(self.keywords)}\n\n")
            f.write(self.text_block)

    def regex(self):
        for line in self.text_block.split("\n"):
            if re.search(r"\w+@\w+\.\w+:\w+", line): # email@domain.top-level-domain:password
                return True
        return False
            
    def scan(self) -> str:
        """
        Scans the bs4 object to see if it is a potential match for mail:password combos. \n
        On successful match, calls \n
            self.store() \n
        Always returns a string that sums up the result.
        """
        # 1. Must not be a private paste
        # (althought this is checked in main.py, by the time the actual request is made,
        # the paste might have been edited)
        if not self.public:
            return f"[{self.url}] Private paste"
        # 2. Must be of text type
        if self.type != "raw":
            return f"[{self.url}] Not of text type"
        # 3. Must not be >= 1 mb in size. (regex checking would take fucking forever)
        if "KB" not in self.size:
            return f"[{self.url}] Too large in size"
        # 4. One of the KEYWORDS must be in text block
        if not len(self.keywords):
            return f"[{self.url}] Missing keyword(s)"
        # 5. Must pass regex check
        if not self.regex():
            return f"[{self.url}] Didn't pass regex check"
        # Match
        self.store()
        return f"[{self.url}] MATCH"