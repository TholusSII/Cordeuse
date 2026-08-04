#include "EntreesSorties.h"
#include "PID_v1.h"
#include "LiquidCrystal.h"
#include "Keypad.h"
#include "digitalWriteFast.h"
#include "HX711.h"
#include "TimerOne.h"


#define Baudrate 115200

#define MEASURESCourant 100
//---------------------------------------------------------------------------------------------
//                               Clavier + écran
//---------------------------------------------------------------------------------------------

const byte ROWS = 4; //four rows
const byte COLS = 5; //five columns
char keys[ROWS][COLS] = {
  {'.','7','8','9','L'},
  {'+','4','5','6','T'},
  {'-','1','2','3','.'},
  {'.','V','0','.','.'}
};
byte rowPins[ROWS] =  {LINE1, LINE2, LINE3, LINE4};//connect to the column pinouts of the keypad
byte colPins[COLS] = {COL1, COL2, COL3, COL4, COL5}; //connect to the row pinouts of the keypad

//const byte ROWS = 5; //four rows
//const byte COLS = 4; //five columns les colonnes sont pilotés 
//char keys[ROWS][COLS] = {
//  {'.','+','-','.'},
//  {'7','4','1','V'},
//  {'8','5','2','0'},
//  {'9','6','3','.'},
//  {'L','T','.','.'}
//};

//byte rowPins[ROWS] =   {COL1, COL2, COL3, COL4, COL5};//connect to the column pinouts of the keypad
//byte colPins[COLS] = {LINE1, LINE2, LINE3, LINE4};//connect to the row pinouts of the keypad

Keypad keypad = Keypad( makeKeymap(keys), rowPins, colPins, ROWS, COLS );
// Définition des broches RS, E, et Data (DB4 à DB7)
LiquidCrystal lcd(AFFRS,AFFRW, AFFE, AFFDB4, AFFDB5, AFFDB6, AFFDB7);  

//---------------------------------------------------------------------------------------------
//                               Capteurs
//---------------------------------------------------------------------------------------------


HX711 CaptHX711;


//---------------------------------------------------------------------------------------------
//                               PID
//---------------------------------------------------------------------------------------------

//Define Variables we'll be connecting to
double Setpoint, Input, Output;

//Define the aggressive and conservative Tuning Parameters
double aggKp=4, aggKi=0.2, aggKd=1;
double consKp=1, consKi=0.05, consKd=0.25;

//Specify the links and initial tuning parameters
PID myPID(&Input, &Output, &Setpoint, consKp, consKi, consKd, DIRECT);



//---------------------------------------------------------------------------------------------
//                               Variables
//---------------------------------------------------------------------------------------------
bool bTraction = false;
bool bFinCoursMaxi = false;
bool bFinCoursMini = false;

int mCourantMoteur = 0;
int mPosition = 0;
int mCordePot = 0;




/************************************************************/





//---------------------------------------------------------------------------------------------
//                               Setup
//---------------------------------------------------------------------------------------------

void setup() {
  Serial.begin(Baudrate) ;
  delay(2000);
  Serial.println("Démarrage du programme de la Cordeuse version TL");
  initPins();
  initCapteurEffort();
  initEcranLCD();
  initClavier();
  initPID();
  Timer1.initialize(150000);
  Timer1.attachInterrupt(lectureEntrees); // lectureEntrees to run every 0.15 seconds


 

  
delay(500);

}




//---------------------------------------------------------------------------------------------
//                               Loop
//---------------------------------------------------------------------------------------------
void loop() {

 /* 24/12/25 : 
  *  BPTra FCMaxi FC Mini : OK, attention il faut les pull_ups pour que ça fonctionne
  *  Clavier OK, gérer le rebond c'est tout
  *  LCD OK
  *  LED clavier OK
  *  Moteur OK
  *  Mesure potard OK, A CALIBRER
  *  Capteur Effort OK, mesure négative, A CALIBRER
  *  Manque test sur  : capteur courant, capteur vitesse (ou position???, du coup peut-être à recabler sur une entrée analogique A5)
  *  GERER UN TIMER POUR faire les E/S, FAIRE PID de l'asserivssement, VERIFIER LE LOGICIEL DE MESURE
  *  
  */
//lectureEntrees();

//testEcranLCD();
//testEntrees();
//testCapteurEffort();
testMoteur();
//testCapteurVitesse();
//testCapteurCourant();
//testClavier();
//testTension(10);
//testLEDs();
//testMiseTension();


}



//---------------------------------------------------------------------------------------------
//                               Programmes d'initialisation
//---------------------------------------------------------------------------------------------


void initClavier()
{

    for (byte r=0; r<ROWS; r++) {
     pinMode(rowPins[r],INPUT_PULLUP);
    }

    
  // bitMap stores ALL the keys that are being pressed.
  for (byte c=0; c<COLS; c++) {
         Serial.print(colPins[c]); Serial.print(", ");

    pinMode(colPins[c],OUTPUT);
  }
     Serial.println("clavier Init fait");

}


void initPins()
{

 TCCR5B = TCCR5B & B11111000 | B00000001;  // for PWM frequency of 31372.55 Hz on pin 46
// = TCCR5B & B11111000 | B00000010;  // for PWM frequency of  3921.16 Hz
 pinMode(MLI, OUTPUT);
 pinMode(SENS, OUTPUT);
    
 pinMode(CaptCordePot, INPUT);
 pinMode(AlimCordePot, OUTPUT);

  pinMode(FinCoursMaxi, INPUT_PULLUP);
  pinMode(FinCoursMini, INPUT_PULLUP);
  pinMode(BPTraction, INPUT_PULLUP);
  pinMode(LEDPlus, OUTPUT);
  pinMode(23, OUTPUT);//ALIM LEDS CLAVIER
  digitalWrite(23,LOW); //LED ETEINTES

  pinMode(LEDMoins, OUTPUT);

  pinMode(AFFCONTRASTE,OUTPUT);

  analogWrite(AFFCONTRASTE,50);
  pinMode(CaptPosition, INPUT);

  pinMode(CaptCordePot, INPUT);
  pinMode(AlimCordePot, OUTPUT);
  digitalWrite(AlimCordePot,HIGH);
  pinMode(CaptEffortDATA, INPUT);
  pinMode(CaptEffortCLK, OUTPUT);

  digitalWrite(SENS,LOW);
  delay(500);
}

void initEcranLCD()
{
//timerLCD.begin(GestionLCD, 10); 

  lcd.begin(16, 2);
  // Print a message to the LCD.
  lcd.print("hello!");
  // set up the LCD's number of rows and columns: 
  //lcd.begin(16, 2);
  // Print a message to the LCD.
 // lcd.print("hello, world!");

lcd.clear();

}

void initPID()
{

  
}


void initCapteurEffort()
{
Serial.println("HX711 Demo");

  Serial.println("Initializing the CaptHX711");

  // Initialize library with data output pin, clock input pin and gain factor.
  // Channel selection is made by passing the appropriate gain:
  // - With a gain factor of 64 or 128, channel A is selected
  // - With a gain factor of 32, channel B is selected
  // By omitting the gain factor parameter, the library
  // default "128" (Channel A) is used here.
  CaptHX711.begin(CaptEffortDATA, CaptEffortCLK);

  Serial.println("Before setting up the CaptHX711:");
  Serial.print("read: \t\t");
  Serial.println(CaptHX711.read());      // print a raw reading from the ADC

  Serial.print("read average: \t\t");
  Serial.println(CaptHX711.read_average(20));   // print the average of 20 readings from the ADC

  Serial.print("get value: \t\t");
  Serial.println(CaptHX711.get_value(5));   // print the average of 5 readings from the ADC minus the tare weight (not set yet)

  Serial.print("get units: \t\t");
  Serial.println(CaptHX711.get_units(5), 1);  // print the average of 5 readings from the ADC minus tare weight (not set) divided
            // by the CaptHX711 parameter (not set yet)

  CaptHX711.set_scale(2280.f);                      // this value is obtained by calibrating the CaptHX711 with known weights; see the README for details
  CaptHX711.tare();               // reset the CaptHX711 to 0

  Serial.println("After setting up the CaptHX711:");

  Serial.print("read: \t\t");
  Serial.println(CaptHX711.read());                 // print a raw reading from the ADC

  Serial.print("read average: \t\t");
  Serial.println(CaptHX711.read_average(20));       // print the average of 20 readings from the ADC

  Serial.print("get value: \t\t");
  Serial.println(CaptHX711.get_value(5));   // print the average of 5 readings from the ADC minus the tare weight, set with tare()

  Serial.print("get units: \t\t");
  Serial.println(CaptHX711.get_units(5), 1);        // print the average of 5 readings from the ADC minus tare weight, divided
            // by the CaptHX711 parameter set with set_CaptHX711

  Serial.println("Readings:");



}

//---------------------------------------------------------------------------------------------
//                               Programmes de base
//---------------------------------------------------------------------------------------------
void lectureEntrees()
{

if(digitalRead(BPTraction))
  {
    if(bTraction) bTraction= false;
    else bTraction= true;
  }



mCourantMoteur = analogRead(CaptCourant);
mPosition = analogRead(CaptPosition);
mCordePot = analogRead(CaptCordePot);


bFinCoursMaxi = not(digitalRead(FinCoursMaxi));
bFinCoursMini = not(digitalRead(FinCoursMini));

if(bFinCoursMaxi) digitalWrite(SENS,HIGH);
if(bFinCoursMini) digitalWrite(SENS,LOW);


}


//---------------------------------------------------------------------------------------------
//                               Programmes de test
//---------------------------------------------------------------------------------------------
void testEcranLCD()
{

    lcd.setCursor(0, 0); //ligne du bas
//  // print the number of seconds since reset:
//  lcd.print(millis() / 1000);
  lcd.print("Bonne annee");
  lcd.setCursor(0, 1); //ligne du haut
//  // print the number of seconds since reset:
//  lcd.print(millis() / 1000);
  lcd.print("Matthieu");
  
    // set the cursor to column 0, line 1
//  // (note: line 1 is the second row, since counting begins with 0):
  //lcd.setCursor(0, 1);
//  // print the number of seconds since reset:
 // lcd.print(millis()/1000);
}

void testClavier()
{

  // bitMap stores ALL the keys that are being pressed.
  for (byte c=0; c<COLS; c++) {
    digitalWrite(colPins[c], LOW); // Begin column pulse output.
//  delayMicroseconds(1000);
    for (byte r=0; r<ROWS; r++) {
       //Serial.println(rowPins[r]);
        if(!digitalRead(rowPins[r])) 
        {
        //   Serial.print(r);Serial.print(" , ");Serial.print(c);Serial.print(" -> ");
          Serial.print("r=");Serial.print(r);Serial.print(", c=");Serial.print(c);Serial.print(", char=");Serial.println(keys[r][c]);              
          digitalWrite(colPins[c], HIGH); // Begin column pulse output.
        }
    }
   digitalWrite(colPins[c], HIGH); // Begin column pulse output.

  }
 // delay(100);
        
}

void testLEDs()
{
digitalWrite(23,HIGH); //LED ALLUMEES

delay(500);

digitalWrite(LEDMoins,HIGH);
digitalWrite(LEDPlus,HIGH);

delay(500);
digitalWrite(LEDMoins,LOW);
digitalWrite(LEDPlus,LOW);

}

void testTension(float tensionCorde)
{

int pwm = (int)(tensionCorde *7);
if(pwm > 255) pwm=255;




analogWrite(MLI,150);

digitalWrite(SENS,LOW);
delay(1000);

digitalWrite(SENS,HIGH);
delay(1000);
analogWrite(MLI,0);
delay(2000);


  
}


void testMoteur()
{
      //Fin CourseMaxi c'et le capteur à droite quand on regarde la cordeuse, celui qui est pèrs des poulies
      // Il est à "1" lorsqu'il n'est pas activé
//   if(FinCoursMaxi) digitalWrite(SENS,HIGH);
// if(FinCoursMini) digitalWrite(SENS,LOW);

// analogWrite(MLI,150);

// digitalWrite(SENS,LOW);
// delay(1000);

// digitalWrite(SENS,HIGH);
// delay(1000);
// analogWrite(MLI,0);
// delay(2000);
digitalWrite(SENS,LOW);
//Serial.print("LOW, FinCMaxi =");Serial.print(digitalRead(FinCoursMaxi)); Serial.print("FinCMini =");Serial.println(FinCoursMini); 
bool EtatFinCMaxi = digitalRead(FinCoursMaxi);
bool EtatFinCMini = digitalRead(FinCoursMini);

while(digitalRead(FinCoursMaxi))
{
analogWrite(MLI,150);
Serial.print(digitalRead(FinCoursMaxi)); 
}
Serial.println("Arrivé en fin de course maxi");

analogWrite(MLI,0);
digitalWrite(SENS,HIGH);
delay(1000);
Serial.println("Départ dans l'autre sens !");


while(digitalRead(FinCoursMini) )
{
analogWrite(MLI,150);
}
//Serial.print("HIGHafter, FinCMaxi =");Serial.print(EtatFinCMaxi); Serial.print("FinCMini =");Serial.println(EtatFinCMini); 
Serial.println("Arrivé en fin de course mini");

digitalWrite(SENS,LOW);
delay(1000);


}

void testMiseTension()
{
    if(bTraction)
    {
     digitalWrite(SENS,LOW);
     while(bTraction and FinCoursMaxi) analogWrite(MLI,150);

     digitalWrite(SENS,HIGH);
     while(FinCoursMini) analogWrite(MLI,150);
    analogWrite(MLI,0);
    digitalWrite(SENS,LOW);

    }
  
}


void testBO()
{
    if(bTraction)
    {
     digitalWrite(SENS,LOW);
     while(bTraction and FinCoursMaxi) analogWrite(MLI,150);

     digitalWrite(SENS,HIGH);
     while(FinCoursMini) analogWrite(MLI,150);
    analogWrite(MLI,0);
    digitalWrite(SENS,LOW);

    }
  
}



void testCapteurVitesse()
{
  
}

void testCapteurCourant()
{
  
}
void testEntrees()
{
  Serial.print("FCMaxi = ");Serial.print(digitalRead(FinCoursMaxi));
  Serial.print(" , FCMini = ");Serial.print(digitalRead(FinCoursMini));
  Serial.print(" , BPTra = ");Serial.println(digitalRead(BPTraction));
  Serial.print(" AnalogRead = ");Serial.println(analogRead(CaptCordePot));

  
}

void testCapteurEffort()
{

  Serial.print("one reading:\t");
  Serial.print(CaptHX711.get_units(), 1);
  Serial.print("\t| average:\t");
  Serial.println(CaptHX711.get_units(10), 1);

  CaptHX711.power_down();             // put the ADC in sleep mode
  delay(100);
  CaptHX711.power_up();

}

//---------------------------------------------------------------------------------------------
//                               PID
//---------------------------------------------------------------------------------------------

//    Input = analogRead(PIN_INPUT);
//  myPID.Compute();
//  analogWrite(PIN_OUTPUT, Output);




//---------------------------------------------------------------------------------------------
//                               Fonctions
//---------------------------------------------------------------------------------------------
/*
 * ' Asser.BAS
'**********************************************************************
' Prg principal d' Asservissement SP55
'
'   - Acquisition BO ou BF
'   - Acquisition  coeff Kp, Ki, Kd
'   - Calcul des coeff du correcteur en BF
'   - Entrée consigne de tension corde en BF
'   - Attente départ cycle par appui sur le bouton traction (SwTRA)
'   - Asservissement tant que le contact de fin de course arrière n'est pas atteint
'     ou qu'il n'y a pas un deuxième appui sur le bouton traction 
'   - Quand il n'y a plus d'asservissement : Retour en position avant du chariot
'     et attente de nouveau de départ cycle 
'***********************************************************************
'  
' version 2 26/11/2003
'==================================================
'======================
' 01/12/03 JMA Mise au point
' 03/12/03 JMA  Mise au point
' 05/12/03 JMA  Mise au point: changer Ti et Td en Ki et Kd refonte du  
'       correcteur
'
'==================================================
'=======================

#include "startsp5.bas" 
asm option c

' Initialisations générales
DDRA  = $F8         'Bits 3 à 7 du port A en sortie
DDRG.0 = 1      'Bit 0 du port G en sortie led verte CB
DDRG.1 = 1      'Bit 1 du port G en sortie led rouge CB
DDRG.2 = 1      'Bit 2 du port G en sortie sens moteur
DDRG.3 = 1      'Bit 3 du port G en sortie PWM moteur
DDRD = $3C      ' Bits 2 à 5 du port D en sortie  
OPTIONS.7 = 0     ' CAN off

' Flags pour interruptions du PWM moteur
PACTL.2 = 1      'valide OC5 si zéro (marche moteur)
TMSK1.3 = 1      'valide OC5 si un (Autorise IT sur OC5) 
TMSK1.7 = 1      'valide OC1 si un (Autorise IT sur OC1)
OC1M.3 = 1       'active PA3 pour OC1
OC1D.3 = 0       'niveau du signal de sortie pour OC1
TCTL1.1 = 1      'permet set et reset par OC5
                   
' Interruptions Horloge temps réel    
TMSK2.6 = 0      ' arrêt RTI timer 
PACTL.0 = 0      ' rapport de division 2e13 comme E = 3Mhz (12Mhz/4) ==> 
PACTL.1 = 0  ' Période = 333ns*2e13 # 2.725 ms

'Période signal PWM
periode = 18784  ' 12MHz => 18784 * 333ns = 6.255 ms de periode
limite = 16905   ' PWM min/max = 90% de la période

'Déclarations et Initialisations 
byte init_val() = $30,$30,$2E,$30

mes = 0
consr = 0     'Pour Boucle ouverte ou debut
xn=0        'Initialisation des mémoires
xn1=0
xn2=0
yn1=0
led = $10
compteurte=0

' Programme principal   
'******************************************
' Avertissement
'******************************************
  Aff_Led($FF)      ' eteindre les leds du clavier
  lcd_init()      ' initialiser l'afficheur
  cls()       ' effacer l'afficheur
  Appui= 0
        cursor(1,1)     ' positionner le curseur
        envoi_data ($80+$0+0,$0)
        print "Pour validation"         ' Affichage
  envoi_data ($80+$40+0,$0)
  print "    Touche V"    ' Affichage 
        do  until Appui=`V`     ' Si Touche V  finir
           Appui = GetKey()   ' attendre un appui sur une touche
        loop
        tempo_ms(200)
'******************************************
' Boucle ouverte ou fermee ?
'******************************************
  Aff_Led($FF)      ' eteindre les leds du clavier
  lcd_init()      ' initialiser l'afficheur
  cls()       ' effacer l'afficheur
  Appui= 0
        cursor(1,1)     ' positionner le curseur
        envoi_data ($80+$0+0,$0)
        print "Choix boucle :"          ' Affichage
  envoi_data ($80+$40+0,$0)
  print "Ouv:0  Fermee:V"   ' Affichage 
        do  until Appui=`V` or Appui=`0`  ' Si Touche V ou 0: finir
           Appui = GetKey()   ' attendre un appui sur une touche
        loop
        if Appui = `0` then boucle = 0  ' Coeff boucle ouverte
        if Appui=`V` then boucle = 1    ' Coeff boucle fermee : voir SP RTI
        tempo_ms(200)
             
'******************************************
' Saisie des donnees
'******************************************
'------------------------------------------
' Acquisition de Kp
'------------------------------------------
       if boucle = 1 then
    Aff_Led($FF)      ' eteindre les leds du clavier
    for m=0 to 3      ' initialiser la variable val() avec les 
    val(m)=init_val(m)  ' valeurs de la constante init_val()
    next m
    lcd_init()      ' initialiser l'afficheur
    cls()       ' effacer l'afficheur
    cursor(1,1)     ' positionner le curseur
          envoi_data ($80+$0+0,$0)
          print "Coeff Cor Proportionnel" 'Affichage
    Appui= 0                      'Remise à zero de la case tampon clavier
          envoi_data ($80+$40+0,$0)
    print "KP     ="    'Affichage
    for m=0 to 3  
    putchar(val(m))
    next m
    do until Appui=`V`        ' Si Touche V : finir
       cursor(12,2)               ' positionner le curseur
       cursor_on(1)   ' allumer le curseur
       Appui = GetKey()   ' attendre un appui sur une touche
       if Appui != 0 and Appui !=`V` then affiche()  
          loop
          cursor_on(0)      ' éteindre le curseur
          kkpp0 = val(0)-48             ' chiffre des dizaines de Kp
          kkpp1 = val(1)-48             ' chiffre des unites de Kp
          kkpp3 = val(3)-48             ' chiffre des dixiemes de Kp
          tempo_ms(200)

      else 
         kkpp0 = 0                      ' si boucle ouverte : Kp = 1
          ' (Voir par la suite si on ne peut
          ' pas utilser KP pour définir l'amplitude
          ' du signal en boucle ouverte ?)
         kkpp1 = 1                     
         kkpp3 = 0                 
      end if
'------------------------------------------
' Acquisition de Ki
'------------------------------------------
      if boucle = 1 then
  Aff_Led($FF)      ' eteindre les leds du clavier
  lcd_init()      ' initialiser l'afficheur
  cls()       ' effacer l'afficheur
        envoi_data ($80+$0+0,$0)
        print "Coeff Cor Integral"  ' si Cor integrale : saisie du coef
        val(0)=$30                      ' initialiser les valeurs affichees
        val(1)=$30
        val(2)=$2E
        val(3)=$30
  Appui= 0
        envoi_data ($80+$40+0,$0)
        print "KI     ="    ' Affichage
  for m=0 to 3  
    putchar(val(m))
    next m 
'             print "  s"                ' KI sans dimension
        do until Appui=`V`  ' Si Touche V : finir
    cursor(12,2)            ' positionner le curseur
    cursor_on(1)    ' allumer le curseur
    Appui = GetKey()  ' attendre un appui sur une touche
    if Appui != 0 and Appui !=`V` then affiche()   
        loop
  cursor_on(0)    ' éteindre le curseur

        tempsi0= val(0)-48         ' chiffre des dizaines de Ki
        tempsi1= val(1)-48         ' chiffre des unites de Ki
        tempsi3= val(3)-48         ' chiffre des dixiemes de Ki
        tempo_ms(200)
  
     end if

'------------------------------------------
' Acquisition de Kd
'------------------------------------------

      if boucle = 1 then
         Aff_Led($FF)     ' eteindre les leds du clavier
   for m=0 to 3       ' initialiser la variable val() avec les 
    val(m)=init_val(m)  ' valeurs de la constante init_val()
   next m
   lcd_init()     ' initialiser l'afficheur
   cls()        ' effacer l'afficheur
   Appui= 0
         cursor(1,1)      ' positionner le curseur
         envoi_data ($80+$0+0,$0)
         print "Coef Cor derive"  ' Affichage
   Appui= 0
         envoi_data ($80+$40+0,$0)
   print "KD     ="   ' Affichage
   for m=0 to 3   
    putchar(val(m))
     next m
'         print "  s"                    ' Affichage KD sans dimension
         do until Appui=`V`       ' Si Touche V : finir
     cursor(12,2)                 ' positionner le curseur
           cursor_on(1)     ' allumer le curseur
     Appui = GetKey()   ' attendre un appui sur une touche
     if Appui != 0 and Appui !=`V` then affiche()  
         loop
   cursor_on(0)     ' éteindre le curseur

         tempsd0= val(0)-48             ' chiffre des dizaines de Kd
         tempsd1= val(1)-48             ' chiffre des unites de Kd
         tempsd3= val(3)-48             ' chiffre des dixiemes de Kd
         tempo_ms(200)

      end if

'*********************************************
' Calcul des coefficients du correcteur
'*********************************************

  te10=2                           ' Te mesuree est de 200ms
  '=========================
'=>      ' Te à changer (Te mesuree ancienne version)

        kpint10=100*kkpp0 + 10*kkpp1 +kkpp3
        kiint10=100*tempsi0 + 10*tempsi1 +tempsi3
        kdint10=100*tempsd0 + 10*tempsd1 +tempsd3
        koef1=kdint10 
        if koef1<0 then koef1=0
        koef2= kiint10 
        if koef2<0 then koef2=0
        if koef2 = 1 then koef2=2
  koef2 = koef2/2
        koef3=kpint10
  a10=koef1+koef2+koef3
  b10=-koef1+koef2
  c10=koef1


'**********************************************
' Entree de la tension corde de consigne
'**********************************************
  Aff_Led($FF)      ' eteindre les leds du clavier
  for m=0 to 3      ' initialiser la variable val() avec les 
    val(m)=init_val(m)  ' valeurs de la constante init_val()
  next m
  lcd_init()      ' initialiser l'afficheur
  cls()       ' effacer l'afficheur
  Appui= 0
        cursor(1,1)     ' positionner le curseur
        envoi_data ($80+$0+0,$0)
        print "Consigne"          ' Affichage
  Appui= 0
        envoi_data ($80+$40+0,$0)
  print "Tension="    ' Affichage
  for m=0 to 3  
    putchar(val(m))
    next m 
  print " daN"                    ' Affichage
        do until Appui=`V`          ' Si Touche V : finir
    cursor(12,2)                  ' positionner le curseur
    cursor_on(1)      ' allumer le curseur
          Appui = GetKey()    ' attendre un appui sur une touche
    if Appui != 0 and Appui !=`V` then affiche()   
        loop
  cursor_on(0)      ' éteindre le curseur
        tens0 = val(0)-48               ' Chiffre des dizaines de daN
        tens1 = val(1)-48               ' Chiffre des unites de daN
        tens3 = val(3)-48               ' Chiffre des dixiemes de daN
  conse=100*tens0 + 10*tens1 + tens3
  if conse > 300 then     'Limitation consigne à 30 daN
     conse=300
     lcd_init()     ' initialiser l'afficheur
     cls()        ' effacer l'afficheur
           cursor(1,1)      ' positionner le curseur
           print "Consigne max"         ' Affichage
           envoi_data ($80+$40+0,$0)
     print "Tension=30.0 daN"   ' Affichage
     tempo_ms (3000)    ' Laisser afficher 3 secondes
  end if

        tempo_ms(200)
        if  boucle = 0 then  
      lcd_init()      ' initialiser l'afficheur
      cls()                       ' effacer l'afficheur
            cursor(1,1) 
            print "Boucle ouverte"
  end if
        if boucle = 1 then
 Aff_Led($FF)
  lcd_init()      ' initialiser l'afficheur
  cls()                           ' effacer l'afficheur
  cursor(1,1)     ' positionner le curseur
  print " KP    KI    KD"           'Coeff de correction
  envoi_data ($80+$40+0,$0)
        print kkpp0 
  print kkpp1 
        print "."
        print kkpp3                        
  print "  "        
  print tempsi0 
  print tempsi1 
        print "."
        print tempsi3                        
  print "  " 
        print tempsd0 
  print tempsd1 
        print "."
        print tempsd3                
  end if  

'******************************************************************
' Bouble principale d'asservissement
'******************************************************************
   do
  do  
  loop until PORTA.0 = 0          ' attente départ cycle SWTRA

  do  
  loop until PORTA.0 = 1          ' attente relachement bouton SWTRA

'-------------------------------------------------------------------
'  Asservissement
'-------------------------------------------------------------------


  consigne_PWM = 0    'Init consigne
  PACTL.2 = 0     'Marche moteur
  Fcalculcons  = 1    'Lancer tout de suite 1er calcul
  TFLG2.6 = 0     'autorisation IT RTI
  TMSK2.6 = 1     'Départ horloge temps réel
  compteurte = 1      'Init compteurte

  if boucle = 1 then

'   Boucle d'asservissement Fermée           
'--------------------------------------
       
  do 
         
          if Fcalculcons=1 then

      Fcalculcons = 0     ' Pour ne pas recommencer un deuxième calcul
          ' Avant la fin de décompte des IT RTI
   
      'Calcul consigne_PWM
      '-------------------

            force = can(0)-30           ' le CAN indique 30 corde non tendue
      consr = force*6/5           ' consr en 1/10 N
      xn = 10*conse - consr ' conse en N
            xn=xn/10
      i1 = somme(xn1,xn)
      i2 = produit(koef2,i1)
      yn = somme (i2,yn1)     'yn = koef2*(xn + xn1) + yn1

      i1 = produit(a10,xn)
      i2 = produit(b10,xn1)
      i3 = somme(i1,i2)
      consigne = somme (i3,yn1)   'consigne = yn1 + a10*xn + b10*xn1 
            'Calcul du nombre à envoyer pour fixer le rapport cyclique
            ' Formule : 1878*(tension en N)/100

            consigne = somme (consigne,consigne) 'Consigne*2 au lieu de 0,1878
             ' Evite une multiplication
            consigne_PWM = consigne

      ' Enregistrer les valeurs précédentes pour echantillonnage suivant
      yn1 = yn
      xn1 = xn

      ' Affichage force mesurée et consigne PWM
      '-----------------------
'            lcd_init()     ' initialiser l'afficheur
'     cls()                       ' effacer l'afficheur
'           cursor(1,1) 
'            print consr
'       envoi_data ($80+$40+0,$0)
'            print consigne 
     end if     ' de if Fcalculcons=1
     
        loop until PORTA.2 = 0 or PORTA.0 = 0   'attente fin de course max ou 
            '        Réappui sur SWTRA
        
  else          ' de if boucle = 1

'   Boucle d'asservissement Ouverte           
'--------------------------------------
          
  do 
          
          if Fcalculcons=1 then

      Fcalculcons = 0     ' Pour ne pas recommencer un deuxième calcul
          ' Avant la fin de décompte des IT RTI
      ' Mesure de la force exercée
      '---------------------------
            force = can(0)-30           ' le CAN indique 30 corde non tendue
      consr = force*12/10         ' consr en 1/10 de Newton

   
      'Calcul consigne_PWM
      '-------------------
            'Calcul du nombre à envoyer pour fixer le rapport cyclique
            ' Formule : 1878*(tension en N)/100
            'conse = 1878*tens0+188*tens1+19*tens3
            
            consigne=conse*19
            consigne_PWM = consigne
      
            
        
     end if       ' de if Fcalculcons=1
     
        loop until PORTA.2 = 0 or PORTA.0 = 0   'attente fin de course max ou 
          '        Réappui sur SWTRA  
  
  end if          ' de if boucle = 1 then else

'-------------------------------------------------------------------
' Retour en position avant
'-------------------------------------------------------------------
          
        consigne_PWM = -15000    ' vitesse retour
  
        do
        loop until PORTA.1 = 0  ' attente fin de course min SWMI
        
  
  consigne_PWM = 2000     ' inversion rotation pour freinage
  tempo_ms (10)   ' Ajouter tempo pour permettre au moteur de freiner 
        consigne_PWM = 0  
        
        PACTL.2 = 1         ' arrêt moteur
        PORTA.3 = 0           ' en arrêt le bit 3 du port A doit etre à 0
  
  
  
  loop
        
       
#include "driver.bas" 
 swi

'**************************************************************  
' fonction d'affichage 
'***************************************************************
function affiche()      
byte n
  val(0) = val(1)     ' décalage vers la gauche 
  val(1) = val(3)
  val(3) = Appui
  cursor(9,2)     ' positionner le curseur
  for n=0 to 3      ' affichage des valeurs
    putchar(val(n))
  next n
        
end function

'**************************************************************  
' fonction curseur(x,y):
' ' positionne le curseur en x,y sur le Lcd
'    x de 1 à 16 : les colonnes
'    y de 1 à 2 : les lignes    
'***************************************************************

function cursor(x,y)  
byte line       
  if y=1 then line=$0 else line=$40
  envoi_data($80+line+(x-1),0)
end function  
'**************************************************************  
' fonction curseur on(On_Off):
' On_Off = 0 éteint le curseur
' On_Off = 1 allume le curseur  
'***************************************************************

function cursor_on(On_Off)     

if On_Off != 0 then envoi_data(%00001110,0)   else envoi_data(%00001100,0)        

end function

'*****************************************************************
' Fonction produit (k,x)
' Fait le produit de k*x en testant le débordement. S'il y a débordement
' la valeur maximum +32767 ou minimum -32768 est affecté au résultat
'
' K doit être absolument positif !!!
'
'*************************************************************************

function produit(k,x)
int prod

prod = k*x
if x > 0 then 
  if prod < 0 then prod = 32767
else
  if prod > 0 then prod = -32768
end if

return prod
end function

'*****************************************************************
' Fonction somme (x,y)
' Fait la somme de x+y en testant le débordement. S'il y a débordement
' la valeur maximum +32767 ou minimum -32768 est affecté au résultat
'
'*************************************************************************

function somme(x,y)
int s

s = x+y
if x > 0 then 
   if y > 0 and s < 0 then s = 32767
else
   if y < 0 and s > 0 then s = -32768
end if

return s
end function

'*************************************************************************
'SP interruption RTI
' Cadence le raffraichissement de la consigne moteur :
'   si compteurte> Nb IT désiré --> flag raffraichissement à 1
'           et compteurte=1
'   
'**************************************************************************

interrupt function Timer at $FFF0
        TFLG2.6 = 1     'reautoriser IT

  compteurte = compteurte+1
  if compteurte > 25 then   'Ici 10 est le nombre d'IT désiré
     compteurte=1
     Fcalculcons=1    'Autoriser rafraichisement consigne
  end if
  
end function
        


*/
