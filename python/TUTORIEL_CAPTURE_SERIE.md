# Tutoriel — capturer les échanges série de l'ancien logiciel SP55

## Objectif

Observer exactement ce que l'ancien logiciel envoie quand on clique sur :

```text
Mesures → Initialiser
```

Le principe est d'intercaler un proxy Python entre l'ancien logiciel et la carte.

```text
Ancien SP55 → COM10 ↔ COM11 → proxy Python → COM3 → carte
Carte → COM3 → proxy Python → COM11 ↔ COM10 → ancien SP55
```

Dans cet exemple :

- `COM3` est le vrai port de la carte ;
- `COM10` et `COM11` forment une paire de ports virtuels ;
- l'ancien logiciel utilise `COM10` ;
- le proxy ouvre `COM11` et `COM3`.

## 1. Identifier le port physique de la carte

1. Branche la carte ou la cordeuse.
2. Ouvre le **Gestionnaire de périphériques** Windows.
3. Déplie **Ports (COM et LPT)**.
4. Note le port qui apparaît, par exemple `COM3`.
5. Débranche puis rebranche la carte pour confirmer que c'est bien ce port.

Ne laisse pas le moniteur série Arduino ou un autre logiciel ouvert sur ce port.

## 2. Installer une paire de ports COM virtuels

Installe `com0com` ou un logiciel équivalent de ports série virtuels.

Crée une paire reliée, par exemple :

```text
COM10 ↔ COM11
```

Choisis des numéros non utilisés dans le Gestionnaire de périphériques.

Après installation, les deux ports doivent apparaître dans Windows.

## 3. Configurer l'ancien logiciel SP55

Dans la configuration série de l'ancien logiciel, remplace le port physique par :

```text
COM10
```

L'ancien logiciel ne doit plus ouvrir directement `COM3`.

## 4. Installer les dépendances Python

Depuis le dossier `Cordeuse\python`, lance d'abord :

```text
lancer_cordeuse.bat
```

Cela crée normalement `.venv` et installe PySide6 ainsi que pyserial.

Au besoin, dans un terminal ouvert dans le dossier `python` :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 5. Lancer le proxy

Double-clique sur :

```text
lancer_proxy_serie.bat
```

Dans la fenêtre :

1. mets `COM11` dans **Port virtuel** ;
2. mets `COM3` dans **Port physique carte** ;
3. choisis la vitesse ; commence par `9600` si elle est inconnue ;
4. clique sur **Démarrer la capture**.

Le journal doit afficher :

```text
Pont actif : COM11 ↔ COM3 à 9600 bauds
```

## 6. Déclencher la commande à observer

1. Laisse le proxy actif.
2. Lance l'ancien logiciel SP55.
3. Vérifie qu'il utilise `COM10`.
4. Clique sur :

```text
Mesures → Initialiser
```

Le proxy affiche alors les données dans les deux sens.

Exemple :

```text
[20:43:12.154] ANCIEN SP55 → CARTE
ASCII : INIT\r\n
HEX   : 49 4E 49 54 0D 0A

[20:43:12.168] CARTE → ANCIEN SP55
ASCII : OK\r\n
HEX   : 4F 4B 0D 0A
```

Même si l'ASCII est illisible, la ligne `HEX` reste exploitable.

## 7. Enregistrer le résultat

Clique sur **Enregistrer le journal** et sauvegarde le fichier `.txt`.

Conserve au minimum :

- la capture au démarrage ;
- la capture après **Initialiser** ;
- la vitesse utilisée ;
- les numéros des ports ;
- tout message d'erreur éventuel.

## Si rien ne s'affiche

Vérifie dans cet ordre :

1. l'ancien logiciel utilise bien `COM10` ;
2. le proxy utilise bien l'autre côté de la paire, `COM11` ;
3. le port physique est bien celui de la carte ;
4. aucun autre logiciel n'occupe le port physique ;
5. la vitesse est correcte ;
6. les ports virtuels sont réellement reliés ;
7. l'ancien logiciel ne nécessite pas de contrôle de flux matériel.

Teste ensuite les vitesses courantes :

```text
9600
19200
38400
57600
115200
```

## Attention électrique

Ce tutoriel ne modifie pas le câblage physique. Si une analyse matérielle devient nécessaire, il faudra d'abord déterminer si la liaison est en TTL, RS-232 ou RS-485 avant de brancher un analyseur logique ou un adaptateur.
