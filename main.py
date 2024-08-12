# requests library is used to send HTTP requests in python
import concurrent.futures.process
import threading
import time

# Import Pandas library to create a dataframe
import pandas as pd

from utils import get_links, get_odds, find_arbitage_bets, calculate_stake_return, get_urls

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

start_time = time.time()

links = get_urls('https://www.betexplorer.com', 'football')

url_retrieval = ['https://www.betexplorer.com/football/england/premier-league/'
                 'https://www.betexplorer.com/football/england/championship/',
                 'https://www.betexplorer.com/football/england/league-one/',
                 'https://www.betexplorer.com/football/england/league-two/',
                 'https://www.betexplorer.com/football/england/national-league/']

bookmakers = ["Betsson", "888sport", "UniBet", "betway"]

# links = []
# for url in url_retrieval:
#     found_url = get_links(url)
#     links.append(found_url)
#
# print(links)

global compiled_odds
global times
times = []
compiled_odds = pd.DataFrame()
writing_lock = threading.Lock()

def find_odds(link, name):
    global compiled_odds
    link = "https://www.betexplorer.com" + link
    odds = get_odds(link, name)
    if odds.empty:
        return
    with writing_lock:
        compiled_odds = pd.concat([compiled_odds, odds])

        end = time.perf_counter()
        times.append(end)


executor = concurrent.futures.ThreadPoolExecutor(10)
futures = [executor.submit(find_odds, link, name) for link, name in links]
for future in concurrent.futures.as_completed(futures):
    diffs = []
    if len(times) <= 1:
        continue
    for i in range(len(times) - 1):
        diffs.append(times[i + 1] - times[i])

    avg_time = sum(diffs) / len(diffs)
    remaining = len(links) - len(times)
    s_left = remaining * avg_time
    minutes, seconds = divmod(s_left, 60)
    minutes = int(minutes)
    seconds = int(seconds)
    print(f"Time left: {minutes}:{seconds:02}")

# for league in links:
# for link, name in links:
#     start = time.perf_counter()
#
#     link = "https://www.betexplorer.com" + link
#     odds = get_odds(link, name)
#     if odds.empty:
#         continue
#     compiled_odds = pd.concat([compiled_odds, odds])
#
#     end = time.perf_counter() - start
#     times.append(end)
#     avg_time = sum(times) / len(times)
#     links_left -= 1
#     s_left = links_left * avg_time
#     minutes, seconds = divmod(s_left, 60)
#     minutes = int(minutes)
#     seconds = int(seconds)
#     print(f"Time left: {minutes}:{seconds:02}")

# print(compiled_odds)


arbitrage_bets = find_arbitage_bets(compiled_odds, bookmakers)
print("----------------------- ARBITRAGE BETS -----------------------")
print(arbitrage_bets)

print("----------------------- STAKE & RETURN -----------------------")

stake = float(input("How much to put at stake?"))

stake_return = calculate_stake_return(arbitrage_bets, stake)
print(stake_return.sort_values('Home Return', ascending=False))

minutes, seconds = divmod(time.time() - start_time, 60)
minutes = int(minutes)
seconds = int(seconds)

print(f"Calculations completed in {minutes}:{seconds:02}")
