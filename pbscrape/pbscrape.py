import paste
import sys
boiler_path = "\\".join(sys.argv[0].split("\\")[:-2])
sys.path.append(boiler_path)
import PyBoiler

my = PyBoiler.Boilerplate()

# Setup constants
CFG = {
    "HEADERS":{
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
        },
    "BASE_URL":"https://pastebin.com"
}

with open(my.module_path + "\\docs\\config.txt", "r") as f:
    for line in f.read().split("\n"):
        key, value = line.split(":")
        CFG[key] = value

with open(my.module_path + "\\docs\\KEYWORDS.txt", "r") as f:
    CFG["KEYWORDS"] = f.read().split("\n")

def main():

    # Setup other variables
    already_visited = ["" for _ in range(int(CFG["already_visited_len"]))]
    x = 0 # iterator for the above

    # Initialization code
    refreshed = True
    current_page = paste.request_wrap(CFG)
    while current_page is None:
        current_page = paste.request_wrap(CFG)

    while True:
        if refreshed:
            refreshed = False
        else:
            # This is an edge-case if the last iteration, no good links were found and
            # the rightmost sidebar also did not get updated
            # This is basically re-initialization code to get updated latest pastes on the rightmost sidebar
            current_page = paste.request_wrap(CFG)
            while current_page is None:
                current_page = paste.request_wrap(CFG)
        # Seek out rightmost sidebar where the latest pastes are contained
        sidebar = current_page.find("div", {"id":"menu_2"})
        sidebar_elements = sidebar.findAll("li")
        # Seek out good links and work with them
        for s_e in sidebar_elements:
            href = s_e.find("a")["href"]
            description = s_e.find("span").text
            # Must be tagged as plain-text and must not have already been visited
            if "|" not in description and href not in already_visited:
                # Good link
                already_visited[x] = href
                x = (x + 1) % int(CFG["already_visited_len"])
                current_page = paste.request_wrap(CFG, href)
                if current_page != None:
                    try:
                        p = paste.paste(CFG, href, current_page, my.module_path)
                        result = p.scan()
                        if result.split(" ")[-1] == "MATCH":
                            PyBoiler.Log(f"{result} {'; '.join(p.keywords)}").to_larva()
                        #print(paste.scan())
                        refreshed = True
                    except:
                        PyBoiler.Log("Unknown parse error").to_larva()
                        #print("Unknown parse error")

while True:
    try:
        main()
    except AttributeError:
        PyBoiler.Log("Ignoring exception").to_larva()