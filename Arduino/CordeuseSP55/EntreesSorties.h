/*
Cablage connecteur clavier, le 1 repéré à gauche en bas, fenêtre clavier vers le haut
________________________________________________________________________________
|                                                                               |
|                                                                               |
|                                                                               |
|                                                                               |
|                                                                               |
|_______________________________________________________________________________|

20. . . . . . . . . . 11
  . . . . . . . . . .
  1                 10

HE20 -> Arduino
2     -> 8 //CLA1 COL1 + -
3     -> 7 //CLA2 COL2 7 4 1 V
4     -> 6 //CLA3 COL3 8 5 2 0
5     -> 5 //CLA4 COL4 9 6 3
6     -> 4 //CLA5 COL5  L T

9     -> 3 //LEDMONOIS PD3
1O    -> 23 METTRE A +5
12     -> 9 //LEDPLUS PD4
16    -> 10 //LINE1 PD1 789L
17    -> 11 // LINE2 PD3 +456T
18    -> 12  //LINE3 PD4 -123 
19    -> 13 //LINE4 //PD5 VO


Leds sont avec pull down dont on pilote la masse avec le uC

Pin DB25  Couleur Câble Utilité Cordeuse  E/S Teensy
1 Noir    GND 
2 Marron    GND 
3 Rouge   IRQ 24
4 Orange  DIN courant SPI + LED « -« + DB5 afficheur + Ligne 2 Clavier  PD3 12
5 Jaune Ligne 4 clavier + Afficheur DB7 PD5 28
6 Vert  Clock bascules Afficheur  PA6 – PWM 29
7 Bleu  Clock bascules Clavier + CS courant SPI PA4 – PWM - CS  10 (PWM, CS0) 
8 Violet  Non connecté  PA1 NC
9 Gris  Mesure de l’effort, analogique  PA0 - ANALOG  37 (A18)
10  Blanc Fin de course minimum SWMI  26
11  Rose  Colonne 1 Clavier CLA1  25
12  Vert pastel Colonne 2 Clavier CLA2  3
13  Noir Blanc  Colonne 4 clavier CLA4  9
14  Marron Blanc    GND GND
15  Rouge Blanc   GND GND
16  Orange Blanc  Ligne 1 Clavier + Afficheur DB4 +  DOUT courant SPI PD2 11
17  Vert Blanc  Ligne 3 Clavier + Afficheur DB6 + LED « + » + CLK PI Courant  PD4 13
18  Bleu Blanc  Sens Moteur PA7 33
19  Violet Blanc  Clock bascules LEDs PA5 – PWM 30
20  Rouge Noir  MLI Moteur  PA3– PWM  36
21  Orange Noir   PA2 NC
22  Jaune Noir  BP demande traction SWTRA 35
23  Vert Noir Fin de course Maxi  SWMA  7
24  Gris Noir Colonne 3 clavier CLA3  6
25    Rose Noir Colonne 5 clavier CLA5  38
 

E/S cablage :
A pour Arduino, C pour Cordeuse

*/

//---------------------------------------------------------------------------------------------
//                               Clavier
//---------------------------------------------------------------------------------------------
/*
A
colonnes : 
1(+,-):9C8A
2(741V):8C71
3(8520):7C6A
4(963):6C5A
5(LT):5C4A

lignes:
1(789L):16C10A
2(+456T):17C11A
3(-123):18C12A
4(V0):19C13A
 * 
 */
#define COL1 2  // CLA1
#define COL2 29  // CLA2
#define COL3 6  // CLA3
#define COL4 5  // CLA4
#define COL5 4  //CLA5

#define LINE1 10  //PD2
#define LINE2 11  // PD3
#define LINE3 12  //PD4
#define LINE4 13  //PD5

//---------------------------------------------------------------------------------------------
//                               Afficheur
//---------------------------------------------------------------------------------------------
//Cablage Afficheur de 1 à ...
//Masse, VDD, Contraste (V0), RS, RW, E, D0 à D7,
// Définition des broches RS, E, et Data (DB4 à DB7)
//LiquidCrystal lcd(AFFRS,AFFRW, AFFE, AFFDB4, AFFDB5, AFFDB6, AFFDB7);
#define AFFRS 14  //PD3
#define AFFRW 15  //PD4
#define AFFE 16   //PD5

#define AFFDB4 17  //PD2
#define AFFDB5 18  //PD3
#define AFFDB6 19  //PD4
#define AFFDB7 20  //PD5

#define AFFRS 14  //PD3
#define AFFRW 15  //PD4
#define AFFE 16   //PD5

#define AFFDB4 17  //PD2
#define AFFDB5 18  //PD3
#define AFFDB6 19  //PD4
#define AFFDB7 20  //PD5






#define AFFCONTRASTE 45

// Remarque : Attention DB4 afficheur et R/W sur la même pin,
// sans doute il faut désactiver l'horloge de l'afficheur quand
// on envoie les données sur l'afficheur

//---------------------------------------------------------------------------------------------
//                               Moteur
//---------------------------------------------------------------------------------------------
//moteur : dir 47 PWM 46

#define MLI 46   //PA3
#define SENS 47  //PA7

//---------------------------------------------------------------------------------------------
//                               Capteur
//---------------------------------------------------------------------------------------------

//DATA 24, CLOCK 25 : capteur d'effort
//Potentiometre A0, A3
//44 capteur de vitesse
//45 BP commande cordage
//0, 1,2,3, 4,5,6,7, 8, 9, 22, 23, 24, 25, 28,29, 33 34, 35, 36, 37, 38, 39  4.482 kHz

/*
capteur courant moteur A8
potentiometre rouge A0
potentiometre bleu A3
capteur d'effort DATA 24
CLK 25



capteur fin de course vert 33
capteur fin de course marron 32

capteur vitesse 44
bouton poussoir cordeuse 45

*/
//Captuer d'effort

#define CaptCordePot A0    //ou A3?
#define AlimCordePot A3    //ou A0?
#define CaptEffortDATA 24  //DATA HX711
#define CaptEffortCLK 27   //CLK HX711

#define FinCoursMaxi 33  //SWMA : Fin de cours, Maxi vert?
#define FinCoursMini 32  //SWMi : Fin de course mini, marron?
#define BPTraction 49    //SWTRA : BP de demande de traction

//Mesure du courant
#define CaptCourant A8  //PA4 : Patte 1 (CS barre / SHDN) du TL1298

//Capteur Vitesse

#define CaptPosition A5  //Capteur Vitesse courroie


//---------------------------------------------------------------------------------------------
//                               LEDS
//---------------------------------------------------------------------------------------------
/*
 *  * clavier 
masse 1
LED - : 2C3A
LED + : 12C9
*/

#define LEDMoins 3  //PD3 : Led moins
#define LEDPlus 9   //PD4 : led +
