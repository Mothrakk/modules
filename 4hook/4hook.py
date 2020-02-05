import sys
import requests
import bs4
import os
boiler_path = "\\".join(sys.argv[0].split("\\")[:-2])
sys.path.append(boiler_path)
import PyBoiler

REFRESH_RATE = 200
BASE = "https://boards.4chan.org"

tick_count = 0
my = PyBoiler.Boilerplate()

def work():
    path_tracking = my.module_path + "\\tracking.txt"
    path_seen = my.module_path + "\\already_seen.log"
    path_archive = my.module_path + "\\archive.log"
    if os.path.exists(path_tracking):
        with open(path_tracking, "r") as fptr:
            tracked_boards = set(fptr.read().strip().split("\n"))
        if os.path.exists(path_seen):
            with open(path_seen, "r") as fptr:
                seen_IDs = set(fptr.read().strip().split("\n"))
        else:
            seen_IDs = set()
        for board in tracked_boards:
            response = requests.get(BASE + board, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})
            parsed = bs4.BeautifulSoup(response.content, "lxml")
            threads = parsed.findAll("div", {"class":"thread"})
            for t in threads:
                is_sticky = t.find("img", {"class":"stickyIcon retina"}) is not None
                if is_sticky:
                    ID = t.find("span", {"class":"postNum desktop"}).findAll("a")[1].text.strip()
                    if ID not in seen_IDs:
                        seen_IDs.add(ID)
                        thread_url = BASE + board + t.find("a", {"class":"replylink"})["href"]
                        thread_subject = t.find("span", {"class":"subject"}).text.strip()
                        PyBoiler.Log(f"New sticky on {board}: {thread_subject} {thread_url}").to_larva()
                        with open(path_archive, "a") as fptr:
                            fptr.write(f"{ID}\n{thread_subject}\n{thread_url}\n\n")
        with open(path_seen, "w") as fptr:
            fptr.write("\n".join(seen_IDs))

while PyBoiler.tick(1):
    if not tick_count % REFRESH_RATE:
        tick_count = 0
        work()
    tick_count += 1
