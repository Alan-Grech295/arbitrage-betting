# requests library is used to send HTTP requests in python
import time

# Import Pandas library to create a dataframe
import pandas as pd

from utils import get_links, get_odds, find_arbitage_bets, calculate_stake_return, get_urls

pd.set_option('display.max_columns', 500)

start_time = time.time()

links = get_urls('https://www.betexplorer.com', 'football')

url_retrieval = ['https://www.betexplorer.com/football/england/premier-league/'
                 'https://www.betexplorer.com/football/england/championship/',
                 'https://www.betexplorer.com/football/england/league-one/',
                 'https://www.betexplorer.com/football/england/league-two/',
                 'https://www.betexplorer.com/football/england/national-league/']

bookmakers = ["bet365", "Betsson", "1xBet", "UniBet",
              "10x10bet", "Alphabet"]

# links = []
# for url in url_retrieval:
#     found_url = get_links(url)
#     links.append(found_url)
#
# print(links)


compiled_odds = pd.DataFrame()
times = []
# for league in links:
links_left = len(links)
for link, name in links:
    start = time.perf_counter()

    link = "https://www.betexplorer.com" + link
    odds = get_odds(link, name)
    if odds.empty:
        continue
    compiled_odds = pd.concat([compiled_odds, odds])

    end = time.perf_counter() - start
    times.append(end)
    avg_time = sum(times) / len(times)
    links_left -= 1
    s_left = links_left * avg_time
    minutes, seconds = divmod(s_left, 60)
    minutes = int(minutes)
    seconds = int(seconds)
    print(f"Time left: {minutes}:{seconds:02}")

# print(compiled_odds)


arbitrage_bets = find_arbitage_bets(compiled_odds, bookmakers)
print("----------------------- ARBITRAGE BETS -----------------------")
print(arbitrage_bets)

print("----------------------- STAKE & RETURN -----------------------")

stake_return = calculate_stake_return(arbitrage_bets, 100)
print(stake_return.sort_values('Home Return', ascending=False))

minutes, seconds = divmod(time.time() - start_time, 60)
minutes = int(minutes)
seconds = int(seconds)

print(f"Calculations completed in {minutes}:{seconds:02}")
