import yaml

# Ouvrir le fichier YAML en mode lecture
with open("config.yaml", "r") as file:
    # Charger le contenu du fichier en tant que dictionnaire Python
    config = yaml.safe_load(file)

print(config)