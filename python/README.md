# Interface Python de la cordeuse DMS SP55

Le dossier `python` se trouve directement à la racine du dépôt **Cordeuse**.

## Lancement sous Windows

Double-cliquer sur :

```text
lancer_cordeuse.bat
```

Au premier lancement, le script crée un environnement virtuel `.venv`, installe PySide6 puis ouvre l’interface.

## Contenu

- `main.py` : point d’entrée ;
- `classic.py` : chargement de l’interface graphique ;
- `requirements.txt` : dépendances Python ;
- `lancer_cordeuse.bat` : installation et lancement automatique.

La communication série avec l’Arduino Mega n’est pas encore intégrée.
