import locale
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy import distance

# locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

# Streamlit Kontrolleinstellung
st.set_page_config(layout="wide", page_title="PKI - Interaktive Karte zu Unverpackt- und Hofläden",
                   menu_items={
                       "About": f"PKI - Interaktive Karten App\n"
                       f"contact: [Daniel Owona](mailto:daniel.owona@outlook.de)"
                   })

# adresse entgegennehmen
adresse = st.text_input(f"\nBitte gib deine Adresse im Format\n'Straße Nr, PLZ Ort' an:\n",
                        value="Frauenstuhlweg 31, 58644 Iserlohn")
geolocator = Nominatim(user_agent="pki_interaktive_karte")
location = geolocator.geocode(adresse)
location_tpl = (location.latitude, location.longitude)
#st.write(f"Deine Adresse wurde in folgende Komponenten aufgelöst")
#st.write(f"Breitengrad: {location_tpl[0]}")
#st.write(f"Längengrad: {location_tpl[1]}")

# Funktionen
@st.experimental_memo
def grab_df1():
    # importieren des dfs für die hoflaeden
    df1 = pd.read_csv("data/hoflaeden_detail_infos.csv", sep=";")

    # aufbereiten: zeilen löschen bei denen der breiten- oder längengrad leer ist
    # so bekommen wir keine probleme bei der distanzberechnung
    df1.dropna(subset=["geo_latitude", "geo_longitude"], inplace=True)

    return df1


@st.experimental_memo
def grab_df2():
    # erstellen des dfs für die unverpackt läden
    df2 = pd.read_csv("data/unverpackt_detail_infos.csv", sep=";")

    # aufbereiten: zeilen löschen bei denen der breiten- oder längengrad leer ist
    # so bekommen wir keine probleme bei der distanzberechnung
    df2.dropna(subset=["lat", "lng"], inplace=True)
    df2.rename(columns={"lat": "geo_latitude", "lng": "geo_longitude"}, inplace=True)
    # fillna
    df2["websiteUrl"].fillna("", inplace=True)
    # Ersetze alle Werte in der Spalte "websiteUrl", die entweder "x" oder "-" sind, durch einen leeren String
    df2['websiteUrl'] = df2['websiteUrl'].where(df2['websiteUrl'].str.match(r'^[^x-]*$'), '')
    # umbenennen der Spaltennamen
    df2.rename(columns={"Distanz_in_KM":"Distanz (km)",
                        "id":"ID",
                        "name":"Name",
                        "type":"Mitgliedsstatus/Mitgliedsart",
                        "address": "Adresse",
                        "websiteUrl": "Website"},
              inplace=True)

    return df2


l1 = grab_df1()
l2 = grab_df2()
df1 = l1.copy()
df2 = l2.copy()

# Mapping
def zeichne_map_kombiniert(df1, df2, geo_latitude, geo_longitude, radiusKM):
    m = folium.Map(location=[geo_latitude, geo_longitude], zoom_start=12)
    # plotten von hoflaeden
    for index, location_info in df1.iterrows():
        pop = """<b>Hofladen</b></br>
        {}""".format(location_info["name"])
        folium.Marker([location_info["geo_latitude"], location_info["geo_longitude"]],
                      popup=pop,
                      icon=folium.Icon(color="red")
                      ).add_to(m)

    # plotten von unverpackt läden
    for index, location_info in df2.iterrows():
        address = location_info["address"]
        pop = """<b>Unverpackt Läden</b></br>
                {}""".format(location_info["address"])
        folium.Marker([location_info["geo_latitude"], location_info["geo_longitude"]],
                      popup=pop,
                      icon=folium.Icon(color="blue")
                      ).add_to(m)

        # Plot Radius
    folium.Circle(
        radius=radiusKM*1000,
        location=[geo_latitude, geo_longitude],
        popup="{} m radius".format(radiusKM),
        color="crimson",
        fill=False).add_to(m)

    return m

def zeichne_map_hoflaeden(df1, geo_latitude, geo_longitude, radiusKM):
    m = folium.Map(location=[geo_latitude, geo_longitude], zoom_start=12)
    # plotten von hoflaeden
    for index, location_info in df1.iterrows():
        pop = """<b>Hofladen</b></br>
        {}""".format(location_info["name"])
        folium.Marker([location_info["geo_latitude"], location_info["geo_longitude"]],
                      popup=pop,
                      icon=folium.Icon(color="red")
                      ).add_to(m)

        # Plot Radius
    folium.Circle(
        radius=radiusKM*1000,
        location=[geo_latitude, geo_longitude],
        popup="{} m radius".format(radiusKM),
        color="crimson",
        fill=False).add_to(m)

    return m

def zeichne_map_unverpackt(df2, geo_latitude, geo_longitude, radiusKM):
    m = folium.Map(location=[geo_latitude, geo_longitude], zoom_start=12)

    # plotten von unverpackt läden
    for index, location_info in df2.iterrows():
        address = location_info["address"]
        pop = """<b>Unverpackt Läden</b></br>
                {}""".format(location_info["address"])
        folium.Marker([location_info["geo_latitude"], location_info["geo_longitude"]],
                      popup=pop,
                      icon=folium.Icon(color="blue")
                      ).add_to(m)

        # Plot Radius
    folium.Circle(
        radius=radiusKM*1000,
        location=[geo_latitude, geo_longitude],
        popup="{} m radius".format(radiusKM),
        color="crimson",
        fill=False).add_to(m)

    return m

# Streamlit App
st.title("PKI - Interaktive Karten - Hofläden & Unverpacktläden")

st.header("Finde den nächsten passenden Laden")
typ = st.radio("Suche dir aus, was du angezeigt bekommen möchtest", ("Hofläden", "Unverpacktläden", "Alle"))
# radius = st.number_input("Trage einen Radius ein (in Metern)", value=25000, step=1000)
radius = st.number_input("Trage einen Radius ein (in KM)", value=25, step=1)

# distanz für beide df berechnen
df1["Distanz_in_KM"] = df1.apply(lambda x: distance.distance(location_tpl,
                                                             (x["geo_latitude"], x["geo_longitude"])
                                                             ).km,
                                 axis=1)
df2["Distanz_in_KM"] = df2.apply(lambda x: distance.distance(location_tpl,
                                                             (x["geo_latitude"], x["geo_longitude"])
                                                             ).km,
                                 axis=1)

# wir nutzen pandas um die DFs nach der aufsteigend Distanz von unserer Location zu sortieren
df1.sort_values("Distanz_in_KM", inplace=True)
df2.sort_values("Distanz_in_KM", inplace=True)

# aufbereitung
spalten_df1 = ['Distanz_in_KM'] + list(df1.columns[0:-1])
df1 = df1[spalten_df1]
spalten_df2 = ['Distanz_in_KM'] + list(df2.columns[0:-1])
df2 = df2[spalten_df2]


# radiusKM = radius/1000
radiusKM = radius

hoflaeden_im_radius = df1[df1["Distanz_in_KM"] <= radiusKM]
hoflaeden_im_radius = hoflaeden_im_radius.style.format(subset=["Distanz_in_KM"], formatter="{:.2f}")
unverpackt_im_radius = df2[df2["Distanz_in_KM"] <= radiusKM]
unverpackt_im_radius = unverpackt_im_radius.style.format(subset=["Distanz_in_KM"], formatter="{:.2f}")

if typ == "Hofläden":
    st.write("Hofläden innerhalb des Radius:")
    st.write(hoflaeden_im_radius)
    st.write("Rote Marker sind Hofläden.")
    # call to render Folium map in Streamlit
    m = zeichne_map_hoflaeden(df1, location_tpl[0], location_tpl[1], radius)
    st_data = st_folium(m, width=800)
    st.header("Alle Hofläden Locations mit Detailinformationen")
    st.dataframe(df1)

elif typ == "Unverpacktläden":
    st.write("Unverpackt Läden innerhalb des Radius:")
    st.write(unverpackt_im_radius)
    st.write("Blaue Marker sind Hofläden.")
    # call to render Folium map in Streamlit
    m = zeichne_map_unverpackt(df2, location_tpl[0], location_tpl[1], radius)
    st_data = st_folium(m, width=800)
    st.header("Alle Unverpackt Läden Locations mit Detailinformationen")
    st.dataframe(df2)
elif typ == "Alle":
    st.write("Hofläden und Unverpackt Läden innerhalb des Radius:")
    st.write(hoflaeden_im_radius)
    st.write(unverpackt_im_radius)
    st.write("Rote Marker sind Hofläden und Blaue Marker sind Unverpackt Läden.")
    # call to render Folium map in Streamlit
    m = zeichne_map_kombiniert(df1, df2, location_tpl[0], location_tpl[1], radius)
    st_data = st_folium(m, width = 800)
    st.header("Alle Hofläden Locations mit Detailinformationen")
    st.dataframe(df1)
    st.header("Alle Unverpackt Läden Locations mit Detailinformationen")
    st.dataframe(df2)



        
