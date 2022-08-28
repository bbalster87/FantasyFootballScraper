import csv
import os
import re

import requests
from bs4 import BeautifulSoup


def save_csv(website, position, tier_list):
    """
    Saves dictionary to a CSV file

    args:
      website: str: Name of the website tier list was pulled from
      position: str: Player position for the tier list
      tier_list: dict: Should be Tier: list of players
    """
    filename = f"{website}_{position}.csv"
    print(f"Writing {filename}")
    with open(f"output/{filename}", "w") as fh:
        writer = csv.writer(fh)

        # Writes the header row
        writer.writerow(["Tier", "Player"])
        for tier, players in tier_list.items():

            # Write a row for each player
            for player in players:
                writer.writerow([tier, player.strip()])


def fix_shitty_cbs_formatting(tier_split):
    """
    Fixes inconsistent tier naming on CBS website

    args:
      tier_split: list: Tier name split on spaces

    return: str: Tier list number or original tier list name
    """
    word_tiers = {
        "First": "1",
        "Second": "2",
        "Third": "3",
        "Fourth": "4",
        "Fifth": "5",
    }
    for word, number in word_tiers.items():
        if tier_split[0] == word:
            return number
    return " ".join(tier_split)


def pull_CBS():
    """
    Pulls down fantasy tier lists from CBS sports, extracts the rankings, and then saves them into CSV files
    """
    # They store each position on a unique URL
    websites = {
        "QB": "https://www.cbssports.com/fantasy/football/news/2022-fantasy-football-rankings-quarterback-tiers-update-plus-dave-richards-positional-draft-prep-strategy/",
        "WR": "https://www.cbssports.com/fantasy/football/news/2022-fantasy-football-rankings-wide-receiver-tiers-update-plus-dave-richards-positional-draft-prep-strategy/",
        "RB": "https://www.cbssports.com/fantasy/football/news/2022-fantasy-football-rankings-running-back-tiers-update-plus-dave-richards-positional-draft-prep-strategy/",
        "TE": "https://www.cbssports.com/fantasy/football/news/2022-fantasy-football-rankings-tight-end-tiers-update-plus-dave-richards-positional-draft-prep-strategy/",
    }

    for position, url in websites.items():
        tier_list = {}
        # GETs the website and converts the HTML to soup format
        html_data = requests.get(url)
        soup = BeautifulSoup(html_data.content, "html.parser")

        # CBS stores tier rankings in tables with a table-player-tiers class
        player_tables = soup.find_all(class_="table-player-tiers")
        for player_table in player_tables:
            # Table title is the tier
            tier = player_table.find(class_="ArticleContentHeader-title").text
            players = []

            # --Long is the full player name stored in an anchor tag
            for player in player_table.find_all(class_="CellPlayerName--long"):
                players.append(player.find("a").text)
            try:
                # Most tiers are "Tier #" so this pulls those
                tier_list[int(tier.split(" ")[1])] = players
            except IndexError:
                # Some tires are single words so this catches that
                tier_list[tier.upper()] = players
            except ValueError:
                # This catches the other formats that they use in their tier names
                tier_list[fix_shitty_cbs_formatting(tier.split(" "))] = players

        # Saves each position in its own CSV
        save_csv("CBS", position, tier_list)


def pull_wash_post():
    """
    Pulls down fantasy tier lists from Washington Post, extracts the rankings, and then saves them into CSV files
    """
    url = (
        "https://www.washingtonpost.com/sports/2022/08/24/fantasy-football-draft-tiers/"
    )
    # GETs the website and converts the HTML to soup format
    html_data = requests.get(url)
    soup = BeautifulSoup(html_data.content, "html.parser")
    players = False
    tier = ""

    # Position we want to extract from the website
    positions = ["TE", "WR", "RB", "QB"]
    tier_list = {}

    # Everything on the webiste is housed in article-body divs
    for part in soup.find_all(class_="article-body"):
        if players:
            # Search to weed out advertisements
            if re.search(", ", part.text):
                tier_list[tier] = (
                    part.text.replace(",", " ").replace("’", "'").split(";")
                )
                players = False

        # Search to header line with Tier in it
        if re.search("Tier", part.text):
            tier = part.text.split(" ")[1]
            if tier_list.get(tier):
                save_csv("WashingtonPost", positions.pop(), tier_list)
                tier_list = {}
            players = True
    save_csv("WashingtonPost", positions.pop(), tier_list)


def pull_fantasy_nerds():
    """
    Pulls down fantasy tier lists from Fantasy Nerds, extracts the rankings, and then saves them into CSV files
    """
    url = "https://www.fantasynerds.com/nfl/tiers/std/export"
    # GETs the CSV file from the website
    response = requests.get(url)
    master_file = "output/fantasy_nerds_master.csv"
    tier_lists = {"QB": {}, "RB": {}, "WR": {}, "TE": {}, "K": {}, "DEF": {}}

    # Saves the master file pulled down
    open(master_file, "wb").write(response.content)

    # Breaks the master file into positional rankings
    with open(master_file, "r") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if tier_lists[row["Position"]].get(row["Tier"]):
                tier_lists[row["Position"]][row["Tier"]].append(
                    f"{row['Player']} {row['Team']}"
                )
            else:
                tier_lists[row["Position"]][row["Tier"]] = [
                    f"{row['Player']} {row['Team']}"
                ]

    # Saves each position
    for position, tier_list in tier_lists.items():
        save_csv("FantasyNerds", position, tier_list)

    # Removes the original master file
    os.remove(master_file)


def build_master_position_file():
    """
    Combines each positional tier ranking per website into a master tier list for each position
    """
    output_dir = "output/"
    all_files = os.listdir(output_dir)

    # List out different positions we care about
    positions = {
        "QB": re.compile(r".*_QB\.csv"),
        "RB": re.compile(r".*_RB\.csv"),
        "TE": re.compile(r".*_TE\.csv"),
        "WR": re.compile(r".*_WR\.csv"),
    }
    for position, r in positions.items():
        master_position = {}

        # Grabs the correct files for each position
        for idv_file in filter(r.match, all_files):
            website = idv_file.split("_")[0]
            with open(output_dir + idv_file, "r") as fh:
                reader = csv.DictReader(fh)

                # Build out a master dict from all sources
                for row in reader:
                    name_parts = row["Player"].split(" ")
                    player_name = name_parts[0] + " " + name_parts[1]
                    if master_position.get(player_name):
                        master_position[player_name][website] = row["Tier"]
                    else:
                        master_position[player_name] = {website: row["Tier"]}

        with open("master/" + position + ".csv", "w") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                ["Player", "CBS", "Fantasy Nerds", "Washington Post", "Average"]
            )

            for player, tiers in master_position.items():
                # Get the average tier ranking across sources
                try:
                    cbs = int(tiers.get("CBS", 10))
                except ValueError:
                    cbs = tiers.get("CBS")

                nerds = int(tiers.get("FantasyNerds", 10))
                wash = int(tiers.get("WashingtonPost", 10))

                # CBS has text for some tiers so we exclude it here
                try:
                    avg = round((cbs + nerds + wash) / 3, 2)
                except TypeError:
                    avg = round((nerds + wash) / 2 + 0.1, 2)  # lower ranking slightly

                # Writes the master position file
                writer.writerow(
                    [
                        player,
                        tiers.get("CBS"),
                        tiers.get("FantasyNerds"),
                        tiers.get("WashingtonPost"),
                        avg,
                    ]
                )


def main():
    pull_CBS()
    pull_wash_post()
    pull_fantasy_nerds()
    build_master_position_file()


if __name__ == "__main__":
    main()
