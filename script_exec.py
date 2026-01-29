# Importation de ta nouvelle librairie 
from surf_scrap import extract_and_save

# Utilisation de la fonction avec une URL au choix [cite: 20, 21]
url_test = "https://www.surf-report.com/meteo-surf/lacanau-s1043.html"
destination = "donnees_surf.csv"

if __name__ == "__main__":
    extract_and_save(url_test, destination)