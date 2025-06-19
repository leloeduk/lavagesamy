#!/usr/bin/env bash
# Exit immédiatement en cas d'erreur
set -o errexit

# Met à jour pip
pip install --upgrade pip  

# Installe les dépendances
pip install -r requirements.txt  

# Collecte les fichiers statiques (Django)
python manage.py collectstatic --no-input  

# Applique les migrations
python manage.py migrate  
