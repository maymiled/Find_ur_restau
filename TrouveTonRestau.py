import streamlit as st
import pandas as pd
import requests
from dataclasses import dataclass, asdict
from math import radians, sin, cos, sqrt, atan2

# --- Initialisation des arrondissements ---
arrondissements = [
    (48.8610, 2.3361, 763),    # 1er
    (48.8683, 2.3431, 561),    # 2e
    (48.8635, 2.3610, 610),    # 3e
    (48.8555, 2.3572, 714),    # 4e
]

@dataclass
class Item:
    Nom: str | None
    Adresse: str | None
    Note: float | None
    Chien: bool | None
    Musique: bool | None
    Terasse: bool | None
    Vegetarien: bool | None
    MenuEnfant: bool | None
    Prix: str | None
    Latitude: float
    Longitude: float

PRICE_MAPPING = {
    "PRICE_LEVEL_INEXPENSIVE": 1,  
    "PRICE_LEVEL_MODERATE": 2,    
    "PRICE_LEVEL_EXPENSIVE": 3,   
    "PRICE_LEVEL_VERY_EXPENSIVE": 4  
}

# --- Fonctions pour le calcul et les requêtes ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    a = sin(delta_phi / 2)**2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def normalize_continuous(value, min_value, max_value):
    return (value - min_value) / (max_value - min_value) if max_value != min_value else 0

def normalize_boolean(value):
    return 1 if value else 0

def calculate_score(restaurant, user_preferences, min_values, max_values, user_lat, user_lon):
    score = 0
    distance = haversine(user_lat, user_lon, restaurant['Latitude'], restaurant['Longitude'])
    score += (1 / (1 + distance)) * user_preferences['distance']
    score += normalize_continuous(restaurant['Note'], min_values['Note'], max_values['Note']) * user_preferences['Note']
    prix_value = PRICE_MAPPING.get(restaurant['Prix'], 0)
    score += normalize_continuous(prix_value, min_values['Prix'], max_values['Prix']) * user_preferences['Prix']
    boolean_criteria = ['Chien', 'Musique', 'Terasse', 'Vegetarien', 'MenuEnfant']
    for criterion in boolean_criteria:
        score += normalize_boolean(restaurant[criterion]) * user_preferences[criterion]
    return score

def run_api(lat, lng, rad):
    payload = {
        "includedTypes": ["restaurant", "french_restaurant", "italian_restaurant"],
        "excludedTypes": ["cafe", "fast_food_restaurant", "bar"],
        "locationRestriction": {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": rad}}
    }
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": "AIzaSyCgJpgA1IPL0azUj4phMzWnl5C8vU5oRBA",
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.allowsDogs,places.location"
    }
    response = requests.post("https://places.googleapis.com/v1/places:searchNearby", json=payload, headers=headers)
    return response.json()

def parse_json(data):
    places = data.get("places", [])
    for place in places:
        try:
            yield asdict(
                Item(
                    Nom=place.get("displayName", {}).get("text", "Inconnu"),
                    Adresse=place.get("formattedAddress", "Non renseignée"),
                    Note=place.get("rating", 0.0),
                    Chien=place.get("allowsDogs", False),
                    Musique=place.get("liveMusic", False),
                    Terasse=place.get("outdoorSeating", False),
                    Vegetarien=place.get("servesVegetarianFood", False),
                    MenuEnfant=place.get("menuForChildren", False),
                    Prix=place.get("priceLevel", "PRICE_LEVEL_INEXPENSIVE"),
                    Latitude=place.get("location", {}).get("latitude", 0.0),
                    Longitude=place.get("location", {}).get("longitude", 0.0),
                )
            )
        except Exception as e:
            st.error(f"Erreur lors du parsing des données : {e}")

# --- Interface Streamlit ---
st.title("🔍 Recherche des Meilleurs Restaurants à Paris")

# Entrée des préférences utilisateur
st.sidebar.header("Préférences")
distance_weight = st.sidebar.slider("Importance de la distance", 1, 5, 3)
note_weight = st.sidebar.slider("Importance de la note", 1, 5, 3)
prix_weight = st.sidebar.slider("Importance du prix", 1, 5, 3)
chien_weight = st.sidebar.slider("Restaurants acceptant les chiens", 1, 5, 1)
musique_weight = st.sidebar.slider("Musique sur place", 1, 5, 1)
terasse_weight = st.sidebar.slider("Présence de terrasse", 1, 5, 2)
vegetarien_weight = st.sidebar.slider("Options végétariennes", 1, 5, 2)
menu_enfant_weight = st.sidebar.slider("Menu pour enfants", 1, 5, 1)

user_preferences = {
    'distance': distance_weight,
    'Note': note_weight,
    'Prix': prix_weight,
    'Chien': chien_weight,
    'Musique': musique_weight,
    'Terasse': terasse_weight,
    'Vegetarien': vegetarien_weight,
    'MenuEnfant': menu_enfant_weight,
}

user_lat = st.sidebar.number_input("Latitude de votre position", value=48.8566)
user_lon = st.sidebar.number_input("Longitude de votre position", value=2.3522)

if st.button("Rechercher"):
    min_values = {'Note': 0, 'Prix': 1}
    max_values = {'Note': 5, 'Prix': 4}
    global_df = pd.DataFrame(columns=["Nom", "Adresse", "Note", "Score"])

    for lat, lon, rad in arrondissements:
        data = run_api(lat, lon, rad)

        leads = parse_json(data)
        for lead in leads:
            score = calculate_score(lead, user_preferences, min_values, max_values, user_lat, user_lon)
            lead["Score"] = score
            st.write(f"Restaurant : {lead['Nom']}, Score : {score}")
            global_df = pd.concat([global_df, pd.DataFrame([lead])], ignore_index=True)

    if not global_df.empty:
        global_df['Score'] = pd.to_numeric(global_df['Score'], errors='coerce')
        global_df = global_df.dropna(subset=['Score'])
        top_5_restaurants = global_df.nlargest(5, 'Score')
    else:
        st.warning("Aucun restaurant trouvé avec les critères actuels.")
        top_5_restaurants = pd.DataFrame(columns=["Nom", "Adresse", "Note", "Score"])

    st.write("Top 5 Restaurants :", top_5_restaurants)
    st.download_button("Télécharger les résultats", global_df.to_csv(index=False), "restaurants.csv")
