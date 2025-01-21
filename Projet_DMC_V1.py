import requests

import pandas as pd

from dataclasses import dataclass, asdict

from math import radians, sin, cos, sqrt, atan2


# Tableau d'arrondissements (latitude, longitude, rayon)

arrondissements = [

(48.8610, 2.3361, 763), # 1er

(48.8683, 2.3431, 561), # 2e

(48.8635, 2.3610, 610), # 3e

(48.8555, 2.3572, 714), # 4e

(48.8443, 2.3503, 899), # 5e

(48.8508, 2.3322, 827), # 6e

(48.8704, 2.3161, 1111), # 8e

(48.8754, 2.3575, 959), # 10e

(48.8579, 2.3802, 1081), # 11e

(48.8380, 2.4008, 2279), # 12e

(48.8270, 2.3563, 1509), # 13e

(48.8324, 2.3236, 1337), # 14e

(48.8410, 2.2988, 1645), # 15e

(48.8628, 2.2699, 2283), # 16e

(48.8864, 2.3204, 1343), # 17e

(48.8924, 2.3444, 1383), # 18e

(48.8848, 2.3770, 1470), # 19e

(48.8638, 2.3983, 1380), # 20e

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

"PRICE_LEVEL_INEXPENSIVE": 1, # Prix peu élevé

"PRICE_LEVEL_MODERATE": 2, # Prix modéré

"PRICE_LEVEL_EXPENSIVE": 3, # Prix élevé

"PRICE_LEVEL_VERY_EXPENSIVE": 4 # Prix très élevé, si applicable

}



# Fonction pour calculer la distance Haversine entre deux points (en kilomètres)

def haversine(lat1, lon1, lat2, lon2):

R = 6371 # Rayon de la Terre en km

phi1 = radians(lat1)

phi2 = radians(lat2)

delta_phi = radians(lat2 - lat1)

delta_lambda = radians(lon2 - lon1)


a = sin(delta_phi / 2)**2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2)**2

c = 2 * atan2(sqrt(a), sqrt(1 - a))

return R * c # Retourne la distance en kilomètres


# Fonction pour normaliser les critères continus

def normalize_continuous(value, min_value, max_value):

return (value - min_value) / (max_value - min_value) if max_value != min_value else 0


# Fonction pour normaliser les critères inverses

def normalize_inverse(value, min_value, max_value):

return 1 - ((value - min_value) / (max_value - min_value)) if max_value != min_value else 0


# Fonction pour normaliser les critères booléens

def normalize_boolean(value):

return 1 if value else 0


# Fonction pour calculer le score d'un restaurant

def calculate_score(restaurant, user_preferences, min_values, max_values, user_lat, user_lon):

score = 0

# Calcul de la distance

distance = haversine(user_lat, user_lon, restaurant['Latitude'], restaurant['Longitude'])

score += (1 / (1 + distance)) * user_preferences['Distance']


# Normalisation des critères continus (Note, etc.)

score += normalize_continuous(restaurant['Note'], min_values['Note'], max_values['Note']) * user_preferences['Note']


# Récupérer la valeur numérique du prix à partir du mapping

prix_value = PRICE_MAPPING.get(restaurant['Prix'], 0) # Valeur par défaut : 0 si clé non trouvée


# Calcul du score pour le prix

score += normalize_continuous(prix_value, min_values['Prix'], max_values['Prix']) * user_preferences['Prix']


# Normalisation des critères booléens (Chien, Musique, Terrasse, etc.)

boolean_criteria = ['Chien', 'Musique', 'Terasse', 'Vegetarien', 'MenuEnfant']

for criterion in boolean_criteria:

score += normalize_boolean(restaurant[criterion]) * user_preferences[criterion]


return score



# Fonction pour obtenir les données de l'API

def run_api(lat, lng, rad):

payload_1 = {

"includedTypes": [

"restaurant", "french_restaurant", "italian_restaurant", "japanese_restaurant",

"greek_restaurant", "indian_restaurant", "mexican_restaurant"

],

"excludedTypes": ["cafe", "fast_food_restaurant", "bar"],

"languageCode": "fr",

"maxResultCount": 10,

"locationRestriction": {

"circle": {

"center": {

"latitude": lat,

"longitude": lng,

},

"radius": rad,

}

},

}

headers = {

"Content-Type": "application/json",

"X-Goog-Api-Key": "AIzaSyCgJpgA1IPL0azUj4phMzWnl5C8vU5oRBA",

"X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.allowsDogs,places.liveMusic,places.outdoorSeating,places.servesVegetarianFood,places.menuForChildren,places.priceLevel,places.location",

}


r = requests.post("https://places.googleapis.com/v1/places:searchNearby", json=payload_1, headers=headers)

data = r.json()

return data


# Fonction pour analyser les données JSON

def parse_json(data):

places = data.get("places", [])

for place in places:

yield asdict(

Item(

Nom=place.get("displayName", {}).get("text"),

Adresse=place["formattedAddress"],

Note=place.get("rating", 0),

Chien=place.get("allowsDogs", False),

Musique=place.get("liveMusic", False),

Terasse=place.get("outdoorSeating", False),

Vegetarien=place.get("servesVegetarianFood", False),

MenuEnfant=place.get("menuForChildren", False),

Prix=place.get("priceLevel", 0), # On suppose que le prix est normalisé entre 0 et 4

Latitude=place["location"]["latitude"],

Longitude=place["location"]["longitude"],

)

)


# Fonction pour demander à l'utilisateur ses préférences

def get_user_preferences():

print("Veuillez indiquer l'ordre de priorité des critères en entrant un nombre entre 1 (peu important) et 5 (très important).")

preferences = {}

preferences['Distance'] = int(input("Priorité pour la distance (1-5): "))

preferences['Note'] = int(input("Priorité pour la note (1-5): "))

preferences['Prix'] = int(input("Priorité pour le prix (1-5): "))

preferences['Chien'] = int(input("Priorité pour les chiens (1-5): "))

preferences['Musique'] = int(input("Priorité pour la musique (1-5): "))

preferences['Terasse'] = int(input("Priorité pour la terrasse (1-5): "))

preferences['Vegetarien'] = int(input("Priorité pour le végétarien (1-5): "))

preferences['MenuEnfant'] = int(input("Priorité pour le menu enfant (1-5): "))


# Convertir en scores normalisés (plus la priorité est élevée, plus le poids est grand)

max_priority = max(preferences.values())

for key in preferences:

preferences[key] = preferences[key] / max_priority


return preferences


# Fonction principale

def main():

# Demander à l'utilisateur de saisir ses préférences

user_preferences = get_user_preferences()


user_lat = 48.870137048255145 # Latitude de l'utilisateur (Paris, exemple)

user_lon = 2.273619029474809 # Longitude de l'utilisateur (Paris, exemple)


# Valeurs minimales et maximales des critères (à définir selon les restaurants)

min_values = {

'Note': 0, # Minimum pour la note

'Prix': 1, # Prix minimum (PRICE_LEVEL_INEXPENSIVE)

}


max_values = {

'Note': 5, # Maximum pour la note

'Prix': 4, # Prix maximum (PRICE_LEVEL_VERY_EXPENSIVE)

}


# Initialisation du DataFrame global pour stocker les résultats

global_df = pd.DataFrame(columns=["Nom", "Adresse", "Note", "Chien", "Musique", "Terasse", "Vegetarien", "MenuEnfant", "Prix", "Score"])


for element in arrondissements:

# Récupérer les données de l'API pour un arrondissement spécifique

data = run_api(element[0], element[1], element[2])


# Parser les données récupérées

leads = parse_json(data)


# Calculer le score pour chaque restaurant

for lead in leads:

# Calculer le score du restaurant

score = calculate_score(lead, user_preferences, min_values, max_values, user_lat, user_lon)

lead["Score"] = score


# Ajouter les données du restaurant et son score au DataFrame global

global_df = pd.concat([global_df, pd.DataFrame([lead])], ignore_index=True)


# Supprimer les doublons basés sur le nom et l'adresse

global_df = global_df.drop_duplicates(subset=["Nom", "Adresse"], keep="first")


# Trier les restaurants par score décroissant et sélectionner les 5 meilleurs

top_5_restaurants = global_df.nlargest(5, 'Score')


# Afficher les informations des 5 meilleurs restaurants avec un affichage épuré

print("¥n" + "=" * 40)

print(" 🏆 TOP 5 RESTAURANTS 🏆")

print("=" * 40)

for i, (_, restaurant) in enumerate(top_5_restaurants.iterrows(), start=1):

print(f"¥n[{i}] {restaurant['Nom']}")

print("-" * 40)

print(f"📍 Adresse : {restaurant['Adresse']}")

print(f"⭐ Note : {restaurant['Note']:.1f}")

print(f"💰 Prix : {restaurant['Prix']} ({'Abordable' if restaurant['Prix'] == 1 else 'Modéré' if restaurant['Prix'] == 2 else 'Élevé' if restaurant['Prix'] == 3 else 'Très Élevé'})")

print(f"🐶 Chien admis : {'Oui' if restaurant['Chien'] else 'Non'}")

print(f"🎶 Musique : {'Oui' if restaurant['Musique'] else 'Non'}")

print(f"☀️ Terrasse : {'Oui' if restaurant['Terasse'] else 'Non'}")

print(f"🌱 Végétarien : {'Oui' if restaurant['Vegetarien'] else 'Non'}")

print(f"👶 Menu Enfant : {'Oui' if restaurant['MenuEnfant'] else 'Non'}")

print(f"🏅 Score : {restaurant['Score']:.2f}")

print("-" * 40)


print("¥nLes résultats ont été enregistrés dans le fichier restaurant_scores.xlsx")

print("=" * 40)


# Sauvegarder tout dans un fichier Excel après la boucle

global_df.to_excel(r"/Users/giulianodarwish/Documents/Decisions_Multicriteres/API_Google_Maps.xlsx", index=False)


if __name__ == "__main__":

main()
