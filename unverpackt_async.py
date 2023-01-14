import asyncio
import json
import time
import aiohttp
import pandas as pd
import requests


def scrape_store_ids() -> list:
    """Funktion iteriert durch die definierte Base-Url und extrahiert die IDs.

    Returns:
        list: eine liste von strings die später zu scrapenden ids der unverpackt läden repräsentiert
    """

    base_url = "https://api.unverpackt-verband.de/map"

    req = requests.get(base_url)
    base_df = pd.json_normalize(req.json())
    base_df = base_df.astype({"id": "str"})
    id_list = base_df["id"].values.tolist()

    return id_list


async def append_store_details(store: json) -> None:
    """Diese Funktion wandelt die json über einen pandas df in einen dict um
       und hängt diese an die globable detail_infos list an.
       Der Weg über einen dict wurde an dieser Stelle bewusst gewählt,
       da er die künftige Weiterverarbeitung erleichtert.
       Manche Datensätze haben nur 11 Datenfelder, andere 12.
       Beispiel für 11: https://api.unverpackt-verband.de/map/info/1545
       Beispiel für 12: https://api.unverpackt-verband.de/map/info/1551

    Args:
        store (json): die json response die in scrape_store_details() erhalten wird
    """
    # detail_infos.append(pd.json_normalize(store).values.tolist()[0])
    detail_infos.append(pd.json_normalize(store).to_dict("records")[0])


async def scrape_store_details(id: str) -> None:
    """Diese Funktion baut aus der übergebenen store id einen vollständigen Link.
       Mit diesem Link lassen sich aus der API mittells async get() die Detailinfos
       zu den einzelnen Unverpackt Läden abrufen.

    Args:
        id (str): Die IDs aus der id_list, die mittels scrape_store_ids() ermittelt wurden.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.unverpackt-verband.de/map/info/{id}", allow_redirects=True) as resp:
            data = await resp.json()
            await append_store_details(data)


async def main() -> None:
    """Hier wird die Logik des teilweise synchronen und teilweise asynchronen Ablaufs gesteuert.

    Systematischer Programmablauf:


    """
    start_time = time.perf_counter()
    global detail_infos, id_list  # globale definition, damit diese listen für andere funktionen verfügbar sind
    detail_infos = []

    id_list = scrape_store_ids()
    # print(id_list[:10]) für präsentation

    tasks = []

    # scrape asynchron detailinformationen zu den einzelnen unverpackt läden
    for id in id_list:
        task = asyncio.create_task(scrape_store_details(id))
        tasks.append(task)
    # print(tasks[:2]) # für visualisierung auf powerpoint

    print("Saving the output of extracted information.")

    # await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.gather(*tasks)

    # print(detail_infos[:1]) für visulaisierung auf ppt

    time_difference = time.perf_counter() - start_time
    print(f"Scraping time: {time_difference} seconds.")
    print(f"Länge id list: {len(id_list)}")
    print(f"Länge detail infos: {len(detail_infos)}")

    # die  verschachtelte liste detail_infos wird in einen pandas df umgewandelt und als .csv datei exportiert
    # es werden nur ausgewählte spalten exportiert
    pd.DataFrame.from_dict(detail_infos).to_csv("data/unverpackt_detail_infos.csv",
                                                index=False,
                                                sep=";",
                                                columns=["id",
                                                         "name",
                                                         "type",
                                                         "address",
                                                         "websiteUrl",
                                                         "lat",
                                                         "lng"])


asyncio.run(main())     # führt die übergebene Coroutine aus
                        # und kümmert sich um die Verwaltung der Asyncio-Ereignisschleife,
                        # den Abschluss der asynchronen Generatoren und das Schließen des Threadpools
