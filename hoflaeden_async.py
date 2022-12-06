import asyncio
import time
import aiohttp
import requests
import re
from selectolax.parser import HTMLParser
from extruct.jsonld import JsonLdExtractor
import pandas as pd


BASE_URL = "https://hofladen.info"
FIRST_PAGE = 1


def get_last_page() -> int:
    """Ausgehend von der first_page_url wird im Quelltext der Link zur letzten seite gesucht,
       geparst und die Zahl als Integer für eine weitere Verwendung zurückgegeben.

    Returns:
        last_page (int): Die letzte Seite, die noch Informationen zu Hofläden enthält.
    """

    first_page_url = "https://hofladen.info/regionale-produkte"
    res = requests.get(first_page_url).text
    html = HTMLParser(res)
    last_page = int(re.findall("(\d+)", html.css("li.page-last > a")[0].attributes["href"])[0])

    return last_page


def build_links_to_pages(start: int, ende: int) -> list:
    """Diese Funktion bildet n Links im Bereich start:ende. Diese Links bilden die Grundlage für das spätere
       Scraping der Detailinformationen zu den Hofläden.

    Args:
        start (int): Die Seitennummer der ersten zu parsenden Seite mit Verlinkungen auf Hofläden.
                     Am besten übergibt man hier die Konstante FIRST_PAGE.

        ende (int): Die Seitennummer der letzten zu parsenden Seite mit Verlinkungen auf Hofläden.
                    Am besten übergibt man hier den int Wert, der mit get_last_page() ermittelt wurde.

    Returns:
        lst (list): Eine Liste die n Links zur weiteren Verwendung erhält.
    """
    lst = []
    for i in range(start, ende + 1):
        url = f"https://hofladen.info/regionale-produkte?page={i}"
        lst.append(url)

    return lst


async def scrape_detail_links(url: str):
    """Hier werden in asynchron die Links aus der Liste verarbeitet, die in der Funktion build_links_to_pages()
       gebildet wurden.
       Das "Ergebnis" sind wiederum Links, die an die globale Liste detail_links angehängt werden.
       Diese Links sind die Links für jeden Hofladen, also sogenannte Detailinformationen.

    Args:
        url (str): ein einzelner Link aus der Liste links_to_pages.
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=True) as resp:
            body = await resp.text()
            html = HTMLParser(body)

            for node in html.css(".sp13"):
                detail_link = BASE_URL + node.attributes["href"]
                detail_links.append(detail_link)


async def append_detail_infos(data):
    """Diese Funktion extrahiert die relevanten Werte zu den hoflaeden aus dem JSON sowie den Link,
       der im dadata objekt mitgegeben wurde und packt sie in die liste my_detail_lst.
       Am schluss jeder iteration, wird die my_detail_lst, an die global definierte liste detail_infos angehangen.
       Die globale verschachtelte liste detail_infos erleichtert später die erstellung eines pandas df.

    Args:
        data (list): die zwei elementige Liste aus der async Funktion scrape_detail_infos()
    """
    my_detail_lst = []
    my_detail_lst.append(data[0]["name"])  # name
    my_detail_lst.append(data[0]["address"]["streetAddress"])  # str
    my_detail_lst.append(data[0]["address"]["postalCode"])  # plz
    my_detail_lst.append(data[0]["address"]["addressLocality"])  # ort
    my_detail_lst.append(data[0]["address"]["addressRegion"])  # bundesland
    my_detail_lst.append(data[0]["address"]["addressCountry"])  # land
    my_detail_lst.append(data[0]["geo"]["latitude"])  # breitengrad
    my_detail_lst.append(data[0]["geo"]["longitude"])  # längengrad
    my_detail_lst.append(data[1])  # url

    detail_infos.append(my_detail_lst)


async def scrape_detail_infos(detail_link: str):
    """Diese Funktion arbeiten mit den Detaillinks aus der Funktion scrape_detail_links() bzw. verarbeitet
       die Links aus der globalen Liste detail_links. Der übergebene Detail Link wird
       mithilfe von aiohttp get und der extruct library geparsed um die relevanten Daten zu verarbeiten.
       Die relevanten Daten stehen als Detailinformationen in einem JSON-LD (JSON Linked Data) Format im Quelltext.
       Im letzten Schritt dieser Funktion wird ein List objekt bestehend aus zwei Elementen an die Funktion
       append_detail_infos() übergeben. data[0] besteht aus dem json
       und data[1] aus der url des gerade verarbeiteten hofladens.

    Args:
        detail_link (str):
    """
    async with aiohttp.ClientSession() as session_detailinfos:
        async with session_detailinfos.get(detail_link, allow_redirects=True) as res_d:
            body_d = await res_d.text()
            # print(res_d.status)  # for debugging
            # print(body_d)  # for debugging
            # print(res_d.url)  # for debugging
            data = JsonLdExtractor().extract(body_d)
            data.append(str(res_d.url))
            await append_detail_infos(data)


async def main() -> None:
    """Die Funtktion main() bildet die steuernde Hülle für den syncr und async Code.

    """
    start_time = time.perf_counter()

    global detail_links, detail_infos
    detail_links, detail_infos = [], []

    tasks = []
    tasks_detail_infos = []
    # extrahiere die letzte zu iterierende Seite
    last_page = get_last_page()

    # scrape detail links
    links_to_pages = build_links_to_pages(FIRST_PAGE, last_page)
    for link in links_to_pages:
        task = asyncio.create_task(scrape_detail_links(link))
        tasks.append(task)

    print("Saving the output of extracted information.")
    await asyncio.gather(*tasks)


    # scrape detail infos
    for detail_url in detail_links:
        task_detail_infos = asyncio.create_task(scrape_detail_infos(detail_url))
        tasks_detail_infos.append(task_detail_infos)

    await asyncio.gather(*tasks_detail_infos, return_exceptions=True)
    pd.DataFrame(detail_infos,
                 columns=["name",
                          "streetAddress",
                          "postalCode",
                          "addressLocality",
                          "addressRegion",
                          "addressCountry",
                          "geo_latitude",
                          "geo_longitude",
                          "url"]).to_csv("data/hoflaeden_detail_infos.csv",
                                         index=False,
                                         sep=";")

    time_difference = time.perf_counter() - start_time
    print(f"Scraping time: {time_difference} seconds.")


asyncio.run(main())  # erst mit dieser zeile wird der vorher definierte code ausgeführt
