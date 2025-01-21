import requests

import pandas as pd

from dataclasses import dataclass, asdict

from math import radians, sin, cos, sqrt, atan2

import tkinter as tk

from tkinter import ttk, messagebox


# Tableau d'arrondissements (latitude, longitude, rayon)

arrondissements = [

(48.8610, 2.3361, 763), # 1er

(48.8683, 2.3431, 561), # 2e

(48.8635, 2.3610, 610), # 3e

(48.8555, 2.3572, 714), # 4e

(48.8443, 2.3503, 899), # 5e

(48.8508, 2.3322, 827), # 6e

(48.8559, 2.3126, 1141), # 7e

(48.8704, 2.3161, 1111), # 8e

(48.8762, 2.3371, 833), # 9e

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

Distance: float | None # Ajout du champ Distance



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

def parse_json(data, user_lat, user_long):

places = data.get("places", [])

for place in places:

# Coordonnées du lieu

place_lat = place["location"]["latitude"]

place_long = place["location"]["longitude"]


# Calcul de la distance avec l'utilisateur

distance = haversine(user_lat, user_long, place_lat, place_long)


yield asdict(

Item(

Nom=place.get("displayName", {}).get("text"),

Adresse=place["formattedAddress"],

Note=float(place.get("rating", 0)), # Convertir en float

Chien=bool(place.get("allowsDogs", False)),

Musique=bool(place.get("liveMusic", False)),

Terasse=bool(place.get("outdoorSeating", False)),

Vegetarien=bool(place.get("servesVegetarianFood", False)),

MenuEnfant=bool(place.get("menuForChildren", False)),

Prix=PRICE_MAPPING.get(place.get("priceLevel", ""), 0), # Convertir le prix en entier

Latitude=place_lat,

Longitude=place_long,

Distance=distance # Ajout de la distance

)

)


# Fonction pour calculer les seuils d'indifférence, de préférence et de veto

def calculate_thresholds(importance, k_indifference, k_preference, max_importance, max_critere):

thresholds = {}

for critere, imp in importance.items():

thresholds[critere] = {

"q": (1 / imp) * k_indifference, # Seuil d'indifférence

"p": (imp / max_importance) * k_preference, # Seuil de préférence

"v": (1 - (imp / max_importance)) * max_critere[critere] # Seuil de veto

}

return thresholds


# Fonction pour demander à l'utilisateur d'entrer ses préférences

def get_user_preferences():

print("Veuillez entrer vos notes pour chaque critère (de 1 à 5) :")

criteria = ["Note", "Prix", "Distance", "Chien", "Musique", "Terasse", "Vegetarien", "MenuEnfant"]

user_preferences = {}


for critere in criteria:

while True:

try:

note = int(input(f"{critere} (1 - Pas important, 5 - Très important) : "))

if 1 <= note <= 5:

user_preferences[critere] = note

break

else:

print("Veuillez entrer un nombre entre 1 et 5.")

except ValueError:

print("Veuillez entrer un nombre valide.")

return user_preferences


# Fonction pour normaliser les pondérations par rapport à la somme des notes

def normalize_weights(user_preferences):

total_importance = sum(user_preferences.values())

return {k: v / total_importance for k, v in user_preferences.items()}


# Fonction pour construire la matrice de concordance partielle

def build_concordance_matrix(df, weights, thresholds):

n = len(df)

concordance_matrix = [[0] * n for _ in range(n)]


for i in range(n):

for j in range(n):

if i != j:

concordance = 0

for critere in thresholds:

diff = df.iloc[i][critere] - df.iloc[j][critere]

if diff >= -thresholds[critere]["q"]: # Totalement en faveur

cj = 1

elif diff <= -thresholds[critere]["p"]: # Pas du tout en faveur

cj = 0

else: # Partiellement en faveur

cj = (thresholds[critere]["p"] + diff) / (thresholds[critere]["p"] - thresholds[critere]["q"])


concordance += weights[critere] * cj

concordance_matrix[i][j] = concordance

return concordance_matrix


# Fonction pour construire la matrice de discordance partielle

def build_discordance_matrix(df, thresholds):

n = len(df)

discordance_matrix = [[0] * n for _ in range(n)]


for i in range(n):

for j in range(n):

if i != j:

discordance = 0

for critere in thresholds:

diff = df.iloc[j][critere] - df.iloc[i][critere]

if diff <= thresholds[critere]["v"]: # Pas du tout en opposition

dj = 0

elif diff > thresholds[critere]["v"]: # Opposition totale

dj = 1

else: # Opposition partielle

dj = (diff - thresholds[critere]["p"]) / (thresholds[critere]["v"] - thresholds[critere]["p"])


discordance = max(discordance, dj) # Prendre le maximum sur tous les critères

discordance_matrix[i][j] = discordance

return discordance_matrix


# Fonction pour construire la matrice de crédibilité

def build_credibility_matrix(concordance_matrix, discordance_matrix):

n = len(concordance_matrix)

credibility_matrix = [[0] * n for _ in range(n)]


for i in range(n):

for j in range(n):

if i == j:

# L'indice de crédibilité entre un élément et lui-même est 1

credibility_matrix[i][j] = 1

else:

credibility_matrix[i][j] = concordance_matrix[i][j] * (1 - discordance_matrix[i][j])

return credibility_matrix



# Fonction pour déterminer les restaurants dans le noyau (non surclassés par d'autres)

def find_core_restaurants(df, credibility_matrix, s=0.9):

"""

Retourne uniquement les restaurants dans le noyau, c'est-à-dire ceux qui ne sont

surclassés par personne.

"""

n = len(df)

core_restaurants = []


for i in range(n):

is_in_core = True

for j in range(n):

if i != j and credibility_matrix[j][i] >= s: # Vérifie si j surclasse i

is_in_core = False

break

if is_in_core:

core_restaurants.append(i) # Ajoute l'index du restaurant au noyau

return core_restaurants


# Fonction pour déterminer les restaurants qui surclassent tous les autres, en excluant ceux du noyau

def check_core_dominance(df, credibility_matrix, core_restaurants, s=0.9):

"""

Retourne les restaurants qui surclassent tous les autres, mais uniquement si ces derniers

ne sont pas dans le noyau.

"""

n = len(df)

dominant_restaurants = []


for i in range(n):

if i not in core_restaurants: # Ignorer les restaurants déjà dans le noyau

is_dominant = True

for j in range(n):

if j not in core_restaurants and i != j and credibility_matrix[i][j] < s:

is_dominant = False

break

if is_dominant:

dominant_restaurants.append(i) # Ajouter au groupe des dominants

return dominant_restaurants


class RestaurantApp:

def __init__(self, root):

self.root = root

self.root.title("Sélecteur de Restaurant")

self.root.geometry("1100x800") # Taille agrandie de la fenêtre

self.root.configure(bg="#2e2e2e") # Couleur de fond sombre


# Initialisation des préférences utilisateur

self.criteria = ["Note", "Prix", "Distance", "Chien", "Musique", "Terasse", "Vegetarien", "MenuEnfant"]

self.user_preferences = {crit: tk.IntVar(value=3) for crit in self.criteria}


# Titre de l'application

tk.Label(root, text="Sélecteur de Restaurant", font=("Arial", 20, "bold"), bg="#2e2e2e", fg="#f1f1f1").pack(pady=10)


# Cadre des critères

frame = tk.Frame(root, bg="#3a3a3a", padx=10, pady=10, relief=tk.RIDGE, borderwidth=2)

frame.pack(pady=10)


tk.Label(frame, text="Entrez vos préférences", font=("Arial", 14, "bold"), bg="#3a3a3a", fg="#ffffff").grid(row=0, column=0, columnspan=2, pady=(0, 10))


for crit in self.criteria:

tk.Label(frame, text=crit, width=15, anchor="w", bg="#3a3a3a", fg="#d9d9d9", font=("Arial", 12)).grid(row=self.criteria.index(crit) + 1, column=0, padx=5, pady=5)

tk.Scale(frame, from_=1, to=5, orient="horizontal", variable=self.user_preferences[crit], bg="#4e4e4e", highlightthickness=0, fg="#ffffff", troughcolor="#616161").grid(row=self.criteria.index(crit) + 1, column=1, padx=5, pady=5)


# Bouton pour lancer l'algorithme

tk.Button(root, text="Rechercher", command=self.run_algorithm, font=("Arial", 14, "bold"), bg="#4caf50", fg="white", relief=tk.RAISED, padx=10, pady=5).pack(pady=20)


# Résumé des résultats

self.summary_label = tk.Label(root, text="", font=("Arial", 12), bg="#2e2e2e", fg="#d9d9d9")

self.summary_label.pack(pady=5)


# Cadre des résultats

self.result_frame = tk.Frame(root, bg="#2e2e2e", padx=10, pady=10)

self.result_frame.pack(fill="both", expand=True)


self.tree = None


def run_algorithm(self):

# Récupération des préférences utilisateur

preferences = {crit: self.user_preferences[crit].get() for crit in self.criteria}


# Normalisation des poids

weights = normalize_weights(preferences)


# Exemple de valeurs maximales des critères

max_critere = {

"Note": 5,

"Prix": 4,

"Distance": 10,

"Chien": 1,

"Musique": 1,

"Terasse": 1,

"Vegetarien": 1,

"MenuEnfant": 1

}


# Calcul des seuils

thresholds = calculate_thresholds(preferences, 0.05, 0.3, max(preferences.values()), max_critere)


# Récupération des données pour les arrondissements

all_data = []

for lat, lng, rad in arrondissements:

data = run_api(lat, lng, rad)

if "places" in data and len(data["places"]) > 0:

parsed_data = list(parse_json(data, 48.8566, 2.3522)) # Exemple : Paris

all_data.extend(parsed_data)


# Transformation en DataFrame

if not all_data:

messagebox.showinfo("Résultat", "Aucun restaurant trouvé.")

return


global_df = pd.DataFrame(all_data)


# Nettoyage et conversion des colonnes

bool_columns = ["Chien", "Musique", "Terasse", "Vegetarien", "MenuEnfant"]

for col in bool_columns:

global_df[col] = global_df[col].astype(int)


numeric_columns = ["Note", "Prix", "Distance"]

for col in numeric_columns:

global_df[col] = pd.to_numeric(global_df[col], errors="coerce")


global_df.dropna(inplace=True)


if global_df.empty:

messagebox.showinfo("Résultat", "Aucun restaurant valide trouvé après nettoyage.")

return


# Matrices de concordance, discordance et crédibilité

concordance_matrix = build_concordance_matrix(global_df, weights, thresholds)

discordance_matrix = build_discordance_matrix(global_df, thresholds)

credibility_matrix = build_credibility_matrix(concordance_matrix, discordance_matrix)


# Trouver les restaurants dans le noyau

core_restaurants = find_core_restaurants(global_df, credibility_matrix, s=0.9)


# Résumé des résultats

total_restaurants = len(global_df)

core_count = len(core_restaurants)

self.summary_label.config(text=f"Restaurants trouvés : {total_restaurants} | Dans le noyau : {core_count}")


# Affichage des résultats

self.show_results(global_df, core_restaurants)


def show_results(self, global_df, core_restaurants):

# Supprimer les widgets existants dans le cadre des résultats

for widget in self.result_frame.winfo_children():

widget.destroy()


# Initialiser l'arbre (Treeview)

self.tree = ttk.Treeview(self.result_frame, columns=list(global_df.columns), show="headings", style="Dark.Treeview")

self.tree.pack(side="left", fill="both", expand=True)


# Définir les colonnes et leurs en-têtes

for col in global_df.columns:

self.tree.heading(col, text=col, anchor="center")

self.tree.column(col, width=150) # Ajuster la largeur des colonnes pour plus de lisibilité


# Ajouter les résultats au tableau

for index in core_restaurants:

row_values = list(global_df.iloc[index])

if "Note" in global_df.columns:

row_values[global_df.columns.get_loc("Note")] = f"★ {row_values[global_df.columns.get_loc('Note')]} ★"

self.tree.insert("", "end", values=row_values)


# Ajouter une barre de défilement

scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.tree.yview)

scrollbar.pack(side="right", fill="y")

self.tree.configure(yscrollcommand=scrollbar.set)


# Application de style pour le tableau

style = ttk.Style()

style.configure("Dark.Treeview", font=("Arial", 10), rowheight=20, background="#424242", fieldbackground="#2e2e2e", foreground="#f1f1f1")

style.map("Dark.Treeview", background=[("selected", "#4caf50")], foreground=[("selected", "white")])

style.configure("Dark.Treeview.Heading", font=("Arial", 12, "bold"), background="#616161", foreground="white")




# Fonction principale mise à jour

def main():

# Coordonnées de l'utilisateur (par exemple, Paris)

user_lat, user_long = 48.8566, 2.3522


# Récupération des préférences utilisateur

user_preferences = get_user_preferences()


# Calcul des pondérations normalisées

weights = normalize_weights(user_preferences)


# Exemple de valeurs maximales des critères (utilisé pour les seuils)

max_critere = {

"Note": 5,

"Prix": 4,

"Distance": 10,

"Chien": 1,

"Musique": 1,

"Terasse": 1,

"Vegetarien": 1,

"MenuEnfant": 1

}


# Calcul des seuils

thresholds = calculate_thresholds(user_preferences, 0.05, 0.3, max(user_preferences.values()), max_critere)


# Fusion des données des arrondissements en une seule DataFrame

all_data = [] # Liste pour stocker les données de chaque arrondissement


for lat, lng, rad in arrondissements:

# Appel de l'API pour récupérer les restaurants

data = run_api(lat, lng, rad)


# Vérifiez que les données ne sont pas vides et analysez-les

if "places" in data and len(data["places"]) > 0:

parsed_data = list(parse_json(data, user_lat, user_long))

all_dat

lse:

print(f"Aucun restaurant trouvé pour l'arrondissement à ({lat}, {lng}).")


# Transformer la liste de résultats en un DataFrame

global_df = pd.DataFrame(all_data)


# Vérifiez si le DataFrame est vide après la collecte des données

if global_df.empty:

print("Aucun restaurant trouvé après la collecte des données.")

return


# Conversion des colonnes booléennes en numériques (1 ou 0)

bool_columns = ["Chien", "Musique", "Terasse", "Vegetarien", "MenuEnfant"]

for col in bool_columns:

if col in global_df.columns:

global_df[col] = global_df[col].astype(int)


# Conversion des colonnes nécessaires en numériques

numeric_columns = ["Note", "Prix", "Distance"]

for col in numeric_columns:

if col in global_df.columns:

global_df[col] = pd.to_numeric(global_df[col], errors="coerce")


# Si la colonne 'Distance' n'existe pas (par exemple, problème de parsing), calculez-la

if "Distance" not in global_df.columns:

global_df["Distance"] = global_df.apply(

lambda row: haversine(user_lat, user_long, row["Latitude"], row["Longitude"]), axis=1

)


# Supprimer les lignes avec des valeurs manquantes

global_df.dropna(inplace=True)


# Vérifiez à nouveau si le DataFrame est vide après le nettoyage

if global_df.empty:

print("Aucun restaurant valide trouvé après le nettoyage des données.")

return



# Conversion des colonnes booléennes en numériques

bool_columns = ["Chien", "Musique", "Terasse", "Vegetarien", "MenuEnfant"]

for col in bool_columns:

global_df[col] = global_df[col].astype(int)


# Conversion des colonnes nécessaires en numériques

for col in ["Note", "Prix", "Distance", "Chien", "Musique", "Terasse", "Vegetarien", "MenuEnfant"]:

global_df[col] = pd.to_numeric(global_df[col], errors="coerce")


# Construction des matrices de concordance et discordance

concordance_matrix = build_concordance_matrix(global_df, weights, thresholds)

discordance_matrix = build_discordance_matrix(global_df, thresholds)


# Construction de la matrice de crédibilité

credibility_matrix = build_credibility_matrix(concordance_matrix, discordance_matrix)


print("¥nMatrice de crédibilité :")

print(pd.DataFrame(credibility_matrix, columns=global_df["Nom"], index=global_df["Nom"]))


# Trouver les restaurants dans le noyau

core_restaurants = find_core_restaurants(global_df, credibility_matrix, s=0.9)

print("¥nRestaurants dans le noyau (non surclassés par d'autres) :")

if core_restaurants:

for index in core_restaurants:

print(global_df.iloc[index]["Nom"])

else:

print("Aucun restaurant dans le noyau.")


# Vérification des restaurants qui surclassent tous les autres, en excluant ceux dans le noyau

core_dominant = check_core_dominance(global_df, credibility_matrix, core_restaurants, s=0.9)

print("¥nRestaurants qui surclassent tous les autres (en excluant ceux du noyau) :")

if core_dominant:

for index in core_dominant:

print(global_df.iloc[index]["Nom"])

else:

print("Aucun restaurant ne surclasse tous les autres.")


if __name__ == "__main__":

root = tk.Tk()

app = RestaurantApp(root)

root.mainloop()