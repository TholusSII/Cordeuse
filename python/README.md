# Interface Python de la cordeuse DMS SP55

Le dossier `python` se trouve directement à la racine du dépôt **Cordeuse**.

## Lancement sous Windows

Double-cliquer sur :

```text
lancer_cordeuse.bat
```

Au premier lancement, le script crée un environnement virtuel `.venv`, installe les dépendances puis ouvre l’interface.

## Contenu principal

- `main.py` : point d’entrée ;
- `app.py` : logique de chargement des fichiers `.mes` et ouverture des tracés ;
- `ui_choix_parametres.py` : interface modernisée de choix des paramètres ;
- `plot_window.py` : tracés PyQtGraph avec curseurs A et B ;
- `mes_reader.py` : lecture des fichiers de mesures SP55 ;
- `requirements.txt` : dépendances Python ;
- `lancer_cordeuse.bat` : installation et lancement automatique.

## Version modernisée

L’interface conserve l’organisation fonctionnelle du logiciel SP55 d’origine tout en adoptant un style plus proche de Windows 11 : police Segoe UI, panneaux clairs, boutons modernisés et fenêtre PyQtGraph harmonisée.

Cette version a été republiée sur `main` le 3 août 2026 afin de forcer une nouvelle synchronisation dans GitHub Desktop.

La communication série avec l’Arduino Mega n’est pas encore intégrée.
