# Interface PyQt de la cordeuse DMS SP55

Première reconstruction cliquable de l’interface de commande. Cette version fonctionne en **mode simulation** et ne communique pas encore avec l’Arduino Mega.

## Fonctions présentes

- écran principal de commande ;
- réglage de la tension par pas de 0,5 kg ;
- choix du pré-étirage, de la surtension de nœud et de la vitesse ;
- simulation d’un cycle de tirage ;
- jauge et afficheur numérique ;
- compteur de cordes tirées ;
- écrans Réglages et Diagnostic ;
- interface redimensionnable.

## Installation

Depuis le dossier `interface_pyqt` :

```bash
python -m venv .venv
```

Sous Windows :

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Sous Linux ou macOS :

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Portée de cette version

L’apparence constitue une base fonctionnelle destinée à être rapprochée progressivement de chaque écran du logiciel SP55 d’origine. Les actions machine sont simulées. Le futur module série sera isolé de l’interface afin de ne pas modifier les écrans lors de l’intégration de l’Arduino Mega.
