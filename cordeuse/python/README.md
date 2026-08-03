# Interface Python de la cordeuse DMS SP55

Cette première reconstruction reproduit un pupitre graphique cliquable en PySide6. Elle fonctionne actuellement en mode simulation ; la communication USB avec l’Arduino Mega sera ajoutée séparément.

## Contenu

- `main.py` : point d’entrée ;
- `classic.py` : interface graphique 1024 × 768 ;
- `requirements.txt` : dépendances Python ;
- `lancer_cordeuse.bat` : installation et lancement automatique sous Windows.

## Lancement sous Windows

Double-cliquer sur `lancer_cordeuse.bat`.

Au premier lancement, le script crée un environnement virtuel `.venv`, installe PySide6 puis ouvre l’interface.

## Lancement manuel

```powershell
cd cordeuse\python
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## État actuel

- réglage de la tension ;
- pré-étirage, nœud et vitesse ;
- simulation du cycle de tirage ;
- navigation vers les réglages et le diagnostic ;
- arrêt d’urgence simulé.
