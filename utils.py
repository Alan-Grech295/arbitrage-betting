# requests library is used to send HTTP requests in python
import time
from typing import Union, Literal

import requests

# BeautifulSoup library is used for web scraping purposes to pull the data out of HTML and XML files
from bs4 import BeautifulSoup

# Import Pandas library to create a dataframe
import pandas as pd

# Import webdriver from selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_urls(base_link: str, sport: Literal["football", "basketball", "tennis", "baseball"]) -> list[str]:
    driver = webdriver.Chrome()
    driver.get(base_link + f"/{sport}/next")
    wait = WebDriverWait(driver, 30)

    if sport == "football":
        visibility = (By.ID, "nr-ko-all")
    else:
        visibility = (By.CLASS_NAME, "table-main only12 js-nrbanner-t")

    try:
        wait.until(EC.visibility_of_element_located(visibility))
        html = driver.page_source
        link_soup = BeautifulSoup(html, 'html.parser')
    except:
        return []
    driver.quit()

    if sport == "football":
        table = link_soup.find('div', attrs={'id': "nr-ko-all"})
        a_tags = table.find_all('a', attrs={"data-live-cell": 'matchlink'})

        links = []
        for tags in a_tags:
            if not tags["href"].startswith("/"):
                continue

            finished = tags.find_all('div', attrs={"class": 'table-main__finishedResults'})
            # live = tags.find_all('div', attrs={"class": 'table-table-main__liveResults'})
            if len(finished) > 0:
                continue

            spans = tags.find_all('p')
            names_string = ' - '.join([name.text for name in spans])
            links.append([tags['href'], names_string])
    else:
        table = link_soup.find('table', attrs={'class': "table-main only12 js-nrbanner-t"})
        a_tags = table.select("a:not(.table-main__tournament)")

        links = []
        for tags in a_tags:
            if not tags["href"].startswith("/"):
                continue
            spans = tags.find_all('span')
            names_string = ' - '.join([name.text for name in spans])
            links.append([tags['href'], names_string])

    return links


def get_links(url_retrieval):
    """
    This script retrieves the HTML content of a web page and extracts links from a specific table using BeautifulSoup.

    The URL of the page to scrape is defined in the variable 'url_retrieval'.
    The script sends an HTTP request to the URL and checks the status code of the response.
    If the status code is 200, the request was successful and a message is printed.
    Otherwise, an error message is printed with the status code.

    The HTML content of the page is parsed using BeautifulSoup.
    The script finds a specific table in the HTML and extracts the links from it.
    The links are stored in a list of lists, where each inner list contains the link URL and a string representing the names associated with the link.

    The extracted links are printed at the end of the script.
    """
    response = requests.get(url_retrieval)

    if response.status_code == 200:
        print("HTTP request successful.")
    else:
        print("Failed to send HTTP request. Status code: ", response.status_code)

    link_soup = BeautifulSoup(response.text, 'html.parser')

    table = link_soup.find('table', attrs={'class': "table-main table-main--leaguefixtures h-mb15"})
    a_tags = table.find_all('a', attrs={'class': "in-match"})

    links = []
    for tags in a_tags:
        spans = tags.find_all('span')
        names_string = ' - '.join([name.text for name in spans])
        links.append([tags['href'], names_string])
    return (links)


def get_odds(link, name):
    """
    Retrieves the odds data from a given link.

    Parameters:
    link (str): The URL of the match page.

    Returns:
    pandas.DataFrame: A DataFrame containing the extracted odds data.
    """

    driver = webdriver.Chrome()
    driver.get(link)
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(EC.visibility_of_element_located((By.ID, "odds-content-2")))
        html = driver.page_source
        odds_soup = BeautifulSoup(html, 'html.parser')
    except:
        return pd.DataFrame()
    driver.quit()

    table = odds_soup.find('div', attrs={'id': "odds-content-2"})
    table = table.find('table', attrs={'class': "table-main sortable oddsComparison__table best-odds-0"})
    if (table == None):
        return pd.DataFrame()
    rows = table.find_all('tr')

    data = []

    for row in rows:
        cols = row.find_all('td')
        ct = 0
        bet = []
        for element in cols:
            if ct == 0:
                bookmaker = element.find('a', attrs={'class': "in-bookmaker-logo-link"})
                if bookmaker != None:
                    bet.append(bookmaker.text)
            if ct > 3:
                stake = element.find('span', attrs={'class': "table-main__detail-odds--hasarchive"})
                if stake != None:
                    if stake.text != ' ':
                        bet.append(stake.text)
            ct = ct + 1

        if len(bet) == 4:
            bet.insert(0, name)
            bet.insert(1, link)
            data.append(bet)

    odds_df = pd.DataFrame(data, columns=['Game', 'Link', 'Bookmaker', 'hw', 'D', 'aw'])

    return odds_df


def find_arbitage_bets(df, bookmakers: Union[list[str], None]):
    """
    Finds arbitrage bets based on the given dataframe.

    Args:
        df (pandas.DataFrame): The dataframe containing the odds for each game.

    Returns:
        list: A list of arbitrage bets, where each bet is represented as [game, bookmaker, odds, lay_odds].
    """
    arb_bets = []
    matches = df.Game.unique()

    bookmakers = [x.lower() for x in bookmakers] if bookmakers else None

    for match in matches:
        odds = df.loc[df['Game'] == match]
        x = 0
        while x < odds.shape[0]:
            if bookmakers and odds.loc[x, 'Bookmaker'].lower() not in bookmakers:
                x += 1
                continue
            winning = float(odds.loc[x, 'hw'])
            d = 0
            while d < odds.shape[0]:
                if bookmakers and odds.loc[d, 'Bookmaker'].lower() not in bookmakers:
                    d += 1
                    continue
                draw = float(odds.loc[d, 'D'])
                l = 0
                while l < odds.shape[0]:
                    if bookmakers and odds.loc[l, 'Bookmaker'].lower() not in bookmakers:
                        l += 1
                        continue
                    loss = float(odds.loc[l, 'aw'])
                    total_implied_probability = 1 / winning + 1 / draw + 1 / loss
                    if total_implied_probability < 1:
                        arb_bets.append([match, odds.loc[x, 'Link'], winning, odds.loc[x, 'Bookmaker'], draw, odds.loc[d, 'Bookmaker'], loss,
                                         odds.loc[l, 'Bookmaker'], total_implied_probability])
                    l = l + 1
                d = d + 1
            x = x + 1
    return pd.DataFrame(arb_bets, columns=['Game', 'Link', 'Home Win Odds', 'Home Win Bookmaker', 'Draw Odds', 'Draw Bookmaker',
                                           'Loss Odds', 'Loss Bookmaker', 'Total Implied Probability'])


def calculate_stake_return(odds, stake) -> pd.DataFrame:
    """
    Calculates the stake return for each game based on the provided odds and stake.

    Args:
        odds (DataFrame): A DataFrame containing the odds for each game.
        stake (float): The stake amount.

    Returns:
        DataFrame: A DataFrame containing the stake return for each game, including various stake-related metrics.
    """
    ret_list = []
    for index, row in odds.iterrows():
        win_implied_probability = 1 / float(row['Home Win Odds'])
        draw_implied_probability = 1 / float(row['Draw Odds'])
        away_implied_probability = 1 / float(row['Loss Odds'])

        home_stake = (win_implied_probability / row['Total Implied Probability']) * stake
        draw_stake = (draw_implied_probability / row['Total Implied Probability']) * stake
        away_stake = (away_implied_probability / row['Total Implied Probability']) * stake

        total_stake = home_stake + draw_stake + away_stake

        home_return = home_stake * float(row['Home Win Odds'])
        draw_return = draw_stake * float(row['Draw Odds'])
        away_return = away_stake * float(row['Loss Odds'])

        home_bookmaker = row['Home Win Bookmaker']
        draw_bookmaker = row['Draw Bookmaker']
        loss_bookmaker = row['Loss Bookmaker']

        ret_list.append(
            [row['Game'], row['Link'], home_stake, draw_stake, away_stake, total_stake, home_return, draw_return, away_return,
             home_bookmaker, draw_bookmaker, loss_bookmaker])

    return pd.DataFrame(ret_list,
                        columns=['Game', 'Link', 'Home Stake', 'Draw Stake', 'Loss Stake', 'Total Stake', 'Home Return',
                                 'Draw Return', 'Away Return', 'Home Bookmaker', 'Draw Bookmaker', 'Loss Bookmaker'])
