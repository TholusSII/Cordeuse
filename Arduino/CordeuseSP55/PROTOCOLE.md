# Protocole série Arduino Mega — SP55

- Vitesse : 115200 bauds
- Encodage : ASCII
- Fin de trame : `\n`
- Une commande ou une mesure par ligne

## Commandes du logiciel

```text
HELLO?
GET;CAPS
GET;STATE
CMD;MODE=BO;KP=0.0000;KI=0.0000;KD=0.0000
CMD;MODE=BF;KP=1.0000;KI=0.0500;KD=0.2500
CMD;MODE=CONSTRUCTEUR;KP=0.0000;KI=0.0000;KD=0.0000
SET;SETPOINT=100;PWM=120
STREAM;ON=1;PERIOD=50
START
STOP
TARE
```

## Télémétrie

```text
MEAS;t=12345;mode=BF;state=TRACTION;effort=102.4;effort_raw=123456;current_raw=312;current=312;position_raw=621;position=621;corde_raw=488;corde=488;fc_min=0;fc_max=0;bp=1;pwm=137
```

Les grandeurs suffixées `_raw` sont toujours les valeurs brutes. Les autres utilisent les coefficients de calibration courants.

## Sécurité et cycle

- `BPTraction`, `FinCoursMini` et `FinCoursMaxi` utilisent un antirebond temporel de 35 ms.
- En traction, la fin de course maxi ou un nouvel appui sur `BPTraction` provoque le retour.
- Le retour s'arrête sur la fin de course mini, suivi d'une courte impulsion de freinage.
- Le mode `STOP` interdit un nouveau départ.
- Les valeurs PWM sont limitées à 0–255.

## Points restant à valider sur la machine

- polarité physique de `SENS` pour traction et retour ;
- valeur PWM de retour et valeur de freinage ;
- calibration HX711 ;
- conversion du capteur de courant ;
- nature exacte de `CaptPosition` : position ou vitesse ;
- conversion du potentiomètre de corde.
