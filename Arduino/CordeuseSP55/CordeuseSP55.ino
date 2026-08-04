#include "../EntreesSorties.h"
#include "../PID_v1.h"
#include "../HX711.h"
#include "../LiquidCrystal.h"
#include "../Keypad.h"

// Firmware de commande SP55 pour Arduino Mega.
// Protocole série ASCII à 115200 bauds, une trame par ligne.

static const unsigned long SERIAL_BAUD = 115200;
static const unsigned long CONTROL_PERIOD_MS = 20;
static const unsigned long DEFAULT_STREAM_PERIOD_MS = 50;
static const unsigned long DEBOUNCE_MS = 35;

static const int RETURN_PWM = 150;
static const int BRAKE_PWM = 35;
static const unsigned long BRAKE_TIME_MS = 30;

// Ces coefficients devront être remplacés par les valeurs issues de la calibration.
static float effortScale = 2280.0f;
static float currentScale = 1.0f;
static float positionScale = 1.0f;
static float cordPotScale = 1.0f;

// -----------------------------------------------------------------------------
// Clavier 4 x 5 et écran LCD 16 x 2 d'origine
// -----------------------------------------------------------------------------
const byte ROWS = 4;
const byte COLS = 5;
char keys[ROWS][COLS] = {
  {'.', '7', '8', '9', 'L'},
  {'+', '4', '5', '6', 'T'},
  {'-', '1', '2', '3', '.'},
  {'.', 'V', '0', '.', '.'}
};
byte rowPins[ROWS] = {LINE1, LINE2, LINE3, LINE4};
byte colPins[COLS] = {COL1, COL2, COL3, COL4, COL5};

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
LiquidCrystal lcd(AFFRS, AFFRW, AFFE, AFFDB4, AFFDB5, AFFDB6, AFFDB7);

class DebouncedInput {
 public:
  DebouncedInput(uint8_t pin, bool activeLow = true)
      : pin_(pin), activeLow_(activeLow) {}

  void begin() {
    pinMode(pin_, INPUT_PULLUP);
    raw_ = digitalRead(pin_);
    stable_ = raw_;
    changedAt_ = millis();
  }

  void update(unsigned long now) {
    bool value = digitalRead(pin_);
    if (value != raw_) {
      raw_ = value;
      changedAt_ = now;
    }
    if (value != stable_ && now - changedAt_ >= DEBOUNCE_MS) {
      previousStable_ = stable_;
      stable_ = value;
      rose_ = !isActive(previousStable_) && isActive(stable_);
      fell_ = isActive(previousStable_) && !isActive(stable_);
    } else {
      rose_ = false;
      fell_ = false;
    }
  }

  bool active() const { return isActive(stable_); }
  bool pressed() const { return rose_; }
  bool released() const { return fell_; }

 private:
  bool isActive(bool electrical) const { return activeLow_ ? !electrical : electrical; }
  uint8_t pin_;
  bool activeLow_;
  bool raw_ = HIGH;
  bool stable_ = HIGH;
  bool previousStable_ = HIGH;
  bool rose_ = false;
  bool fell_ = false;
  unsigned long changedAt_ = 0;
};

enum ControlMode : uint8_t { MODE_STOP, MODE_BO, MODE_BF, MODE_CONSTRUCTOR };
enum MachineState : uint8_t {
  STATE_IDLE,
  STATE_PULLING,
  STATE_RETURNING,
  STATE_BRAKING,
  STATE_FAULT
};

DebouncedInput endMax(FinCoursMaxi);
DebouncedInput endMin(FinCoursMini);
DebouncedInput pullButton(BPTraction);
HX711 loadCell;

double pidInput = 0.0;
double pidOutput = 0.0;
double pidSetpoint = 100.0;
double kp = 1.0, ki = 0.05, kd = 0.25;
PID forcePid(&pidInput, &pidOutput, &pidSetpoint, kp, ki, kd, DIRECT);

ControlMode controlMode = MODE_STOP;
MachineState machineState = STATE_IDLE;
int openLoopPwm = 120;
bool streaming = false;
unsigned long streamPeriodMs = DEFAULT_STREAM_PERIOD_MS;
unsigned long lastControlMs = 0;
unsigned long lastStreamMs = 0;
unsigned long brakeStartedMs = 0;

float effort = 0.0f;
long effortRaw = 0;
int currentRaw = 0;
int positionRaw = 0;
int cordPotRaw = 0;
int appliedPwm = 0;

char commandBuffer[180];
uint8_t commandLength = 0;

ControlMode lastDisplayedMode = MODE_STOP;
MachineState lastDisplayedState = STATE_FAULT;

const char *modeName(ControlMode mode) {
  switch (mode) {
    case MODE_BO: return "BO";
    case MODE_BF: return "BF";
    case MODE_CONSTRUCTOR: return "CONSTRUCTEUR";
    default: return "STOP";
  }
}

const char *stateName(MachineState state) {
  switch (state) {
    case STATE_PULLING: return "TRACTION";
    case STATE_RETURNING: return "RETOUR";
    case STATE_BRAKING: return "FREINAGE";
    case STATE_FAULT: return "DEFAUT";
    default: return "ATTENTE";
  }
}

const char *lcdModeName(ControlMode mode) {
  switch (mode) {
    case MODE_BO: return "Boucle ouverte";
    case MODE_BF: return "Boucle fermee";
    case MODE_CONSTRUCTOR: return "Constructeur";
    default: return "Mode arret";
  }
}

const char *lcdStateName(MachineState state) {
  switch (state) {
    case STATE_PULLING: return "Essai en cours";
    case STATE_RETURNING: return "Retour chariot";
    case STATE_BRAKING: return "Freinage";
    case STATE_FAULT: return "DEFAUT";
    default: return "Pret";
  }
}

void printLcdLine(uint8_t row, const char *text) {
  lcd.setCursor(0, row);
  uint8_t index = 0;
  while (text[index] != '\0' && index < 16) {
    lcd.print(text[index]);
    ++index;
  }
  while (index < 16) {
    lcd.print(' ');
    ++index;
  }
}

void refreshLcd(bool force = false) {
  if (!force && controlMode == lastDisplayedMode && machineState == lastDisplayedState) {
    return;
  }
  printLcdLine(0, lcdModeName(controlMode));
  printLcdLine(1, lcdStateName(machineState));
  lastDisplayedMode = controlMode;
  lastDisplayedState = machineState;
}

void showWelcome() {
  lcd.clear();
  printLcdLine(0, "Cordeuse SP55");
  printLcdLine(1, "Bienvenue");
  delay(1500);
  refreshLcd(true);
}

void stopMotor() {
  analogWrite(MLI, 0);
  appliedPwm = 0;
}

void driveMotor(bool pullingDirection, int pwm) {
  pwm = constrain(pwm, 0, 255);
  digitalWrite(SENS, pullingDirection ? HIGH : LOW);
  analogWrite(MLI, pwm);
  appliedPwm = pullingDirection ? pwm : -pwm;
}

void startPulling() {
  if (controlMode == MODE_STOP || endMax.active()) return;
  machineState = STATE_PULLING;
  refreshLcd();
  Serial.println(F("EVENT;TYPE=CYCLE_START"));
}

void startReturn() {
  stopMotor();
  if (endMin.active()) {
    machineState = STATE_IDLE;
    refreshLcd();
    Serial.println(F("EVENT;TYPE=CYCLE_END"));
    return;
  }
  machineState = STATE_RETURNING;
  refreshLcd();
  Serial.println(F("EVENT;TYPE=RETURN_START"));
}

void startBrake() {
  machineState = STATE_BRAKING;
  brakeStartedMs = millis();
  driveMotor(true, BRAKE_PWM);
  refreshLcd();
}

void readSensors() {
  currentRaw = analogRead(CaptCourant);
  positionRaw = analogRead(CaptPosition);
  cordPotRaw = analogRead(CaptCordePot);
  if (loadCell.is_ready()) {
    effortRaw = loadCell.read();
    effort = loadCell.get_units(1);
  }
  pidInput = effort;
}

void updateMachine(unsigned long now) {
  endMax.update(now);
  endMin.update(now);
  pullButton.update(now);

  if (pullButton.pressed()) {
    if (machineState == STATE_IDLE) startPulling();
    else if (machineState == STATE_PULLING) startReturn();
  }

  switch (machineState) {
    case STATE_IDLE:
      stopMotor();
      break;

    case STATE_PULLING:
      if (endMax.active()) {
        Serial.println(F("EVENT;TYPE=END_MAX"));
        startReturn();
        break;
      }
      if (controlMode == MODE_BF) {
        forcePid.Compute();
        driveMotor(true, (int)pidOutput);
      } else if (controlMode == MODE_BO || controlMode == MODE_CONSTRUCTOR) {
        driveMotor(true, openLoopPwm);
      } else {
        startReturn();
      }
      break;

    case STATE_RETURNING:
      if (endMin.active()) {
        Serial.println(F("EVENT;TYPE=END_MIN"));
        startBrake();
      } else {
        driveMotor(false, RETURN_PWM);
      }
      break;

    case STATE_BRAKING:
      if (now - brakeStartedMs >= BRAKE_TIME_MS) {
        stopMotor();
        machineState = STATE_IDLE;
        refreshLcd();
        Serial.println(F("EVENT;TYPE=CYCLE_END"));
      }
      break;

    case STATE_FAULT:
      stopMotor();
      break;
  }
}

void cycleLocalMode() {
  if (machineState != STATE_IDLE) return;
  if (controlMode == MODE_BO) controlMode = MODE_BF;
  else if (controlMode == MODE_BF) controlMode = MODE_CONSTRUCTOR;
  else controlMode = MODE_BO;
  refreshLcd();
  Serial.print(F("EVENT;TYPE=LOCAL_MODE;MODE="));
  Serial.println(modeName(controlMode));
}

void handleKeypad() {
  char key = keypad.getKey();
  if (!key) return;

  switch (key) {
    case 'L':
      cycleLocalMode();
      break;
    case 'V':
      if (machineState == STATE_IDLE) startPulling();
      else if (machineState == STATE_PULLING) startReturn();
      break;
    case 'T':
      if (machineState == STATE_IDLE) {
        printLcdLine(1, "Tare en cours");
        loadCell.tare(10);
        refreshLcd(true);
        Serial.println(F("EVENT;TYPE=TARE"));
      }
      break;
    case '+':
      pidSetpoint = min(300.0, pidSetpoint + 1.0);
      Serial.print(F("EVENT;TYPE=SETPOINT;VALUE="));
      Serial.println(pidSetpoint, 1);
      break;
    case '-':
      pidSetpoint = max(0.0, pidSetpoint - 1.0);
      Serial.print(F("EVENT;TYPE=SETPOINT;VALUE="));
      Serial.println(pidSetpoint, 1);
      break;
    default:
      break;
  }
}

void sendTelemetry(unsigned long now) {
  Serial.print(F("MEAS;t=")); Serial.print(now);
  Serial.print(F(";mode=")); Serial.print(modeName(controlMode));
  Serial.print(F(";state=")); Serial.print(stateName(machineState));
  Serial.print(F(";setpoint=")); Serial.print(pidSetpoint, 4);
  Serial.print(F(";effort=")); Serial.print(effort, 4);
  Serial.print(F(";effort_raw=")); Serial.print(effortRaw);
  Serial.print(F(";current_raw=")); Serial.print(currentRaw);
  Serial.print(F(";current=")); Serial.print(currentRaw * currentScale, 4);
  Serial.print(F(";position_raw=")); Serial.print(positionRaw);
  Serial.print(F(";position=")); Serial.print(positionRaw * positionScale, 4);
  Serial.print(F(";corde_raw=")); Serial.print(cordPotRaw);
  Serial.print(F(";corde=")); Serial.print(cordPotRaw * cordPotScale, 4);
  Serial.print(F(";fc_min=")); Serial.print(endMin.active() ? 1 : 0);
  Serial.print(F(";fc_max=")); Serial.print(endMax.active() ? 1 : 0);
  Serial.print(F(";bp=")); Serial.print(pullButton.active() ? 1 : 0);
  Serial.print(F(";pwm=")); Serial.println(appliedPwm);
}

float fieldFloat(const char *line, const char *name, float fallback) {
  char key[24];
  snprintf(key, sizeof(key), "%s=", name);
  const char *p = strstr(line, key);
  return p ? atof(p + strlen(key)) : fallback;
}

long fieldLong(const char *line, const char *name, long fallback) {
  char key[24];
  snprintf(key, sizeof(key), "%s=", name);
  const char *p = strstr(line, key);
  return p ? atol(p + strlen(key)) : fallback;
}

void acknowledge(const __FlashStringHelper *message) {
  Serial.print(F("ACK;"));
  Serial.println(message);
}

void handleCommand(char *line) {
  if (strcmp(line, "HELLO?") == 0) {
    Serial.println(F("HELLO;DEVICE=SP55_ARDUINO_MEGA;PROTO=1;BAUD=115200"));
    return;
  }
  if (strcmp(line, "GET;CAPS") == 0) {
    Serial.println(F("CAPS;MODES=STOP,BO,BF,CONSTRUCTEUR;MEAS=setpoint,effort,effort_raw,current,current_raw,position,position_raw,corde,corde_raw,fc_min,fc_max,bp,pwm"));
    return;
  }
  if (strcmp(line, "GET;STATE") == 0) {
    sendTelemetry(millis());
    return;
  }
  if (strcmp(line, "START") == 0) {
    startPulling(); acknowledge(F("START")); return;
  }
  if (strcmp(line, "STOP") == 0) {
    startReturn(); acknowledge(F("STOP")); return;
  }
  if (strcmp(line, "TARE") == 0) {
    printLcdLine(1, "Tare en cours");
    loadCell.tare(10);
    refreshLcd(true);
    acknowledge(F("TARE"));
    return;
  }
  if (strncmp(line, "STREAM;", 7) == 0) {
    streaming = fieldLong(line, "ON", streaming ? 1 : 0) != 0;
    streamPeriodMs = constrain(fieldLong(line, "PERIOD", streamPeriodMs), 20L, 2000L);
    acknowledge(F("STREAM"));
    return;
  }
  if (strncmp(line, "SET;", 4) == 0) {
    pidSetpoint = fieldFloat(line, "SETPOINT", pidSetpoint);
    openLoopPwm = constrain(fieldLong(line, "PWM", openLoopPwm), 0L, 255L);
    effortScale = fieldFloat(line, "EFFORT_SCALE", effortScale);
    currentScale = fieldFloat(line, "CURRENT_SCALE", currentScale);
    positionScale = fieldFloat(line, "POSITION_SCALE", positionScale);
    cordPotScale = fieldFloat(line, "CORDE_SCALE", cordPotScale);
    loadCell.set_scale(effortScale);
    acknowledge(F("SET"));
    return;
  }
  if (strncmp(line, "CMD;", 4) == 0) {
    if (strstr(line, "MODE=BF")) controlMode = MODE_BF;
    else if (strstr(line, "MODE=BO")) controlMode = MODE_BO;
    else if (strstr(line, "MODE=CONSTRUCTEUR")) controlMode = MODE_CONSTRUCTOR;
    else controlMode = MODE_STOP;

    kp = fieldFloat(line, "KP", kp);
    ki = fieldFloat(line, "KI", ki);
    kd = fieldFloat(line, "KD", kd);
    forcePid.SetTunings(kp, ki, kd);
    if (controlMode == MODE_STOP && machineState == STATE_PULLING) startReturn();
    refreshLcd();
    Serial.print(F("ACK;CMD;MODE=")); Serial.print(modeName(controlMode));
    Serial.print(F(";KP=")); Serial.print(kp, 4);
    Serial.print(F(";KI=")); Serial.print(ki, 4);
    Serial.print(F(";KD=")); Serial.println(kd, 4);
    return;
  }
  Serial.print(F("ERR;UNKNOWN_COMMAND;"));
  Serial.println(line);
}

void pollSerial() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      commandBuffer[commandLength] = '\0';
      if (commandLength) handleCommand(commandBuffer);
      commandLength = 0;
    } else if (commandLength < sizeof(commandBuffer) - 1) {
      commandBuffer[commandLength++] = c;
    } else {
      commandLength = 0;
      Serial.println(F("ERR;COMMAND_TOO_LONG"));
    }
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);

  pinMode(MLI, OUTPUT);
  pinMode(SENS, OUTPUT);
  pinMode(CaptCourant, INPUT);
  pinMode(CaptPosition, INPUT);
  pinMode(CaptCordePot, INPUT);
  pinMode(AlimCordePot, OUTPUT);
  digitalWrite(AlimCordePot, HIGH);
  stopMotor();

  pinMode(AFFCONTRASTE, OUTPUT);
  analogWrite(AFFCONTRASTE, 50);
  lcd.begin(16, 2);
  keypad.setDebounceTime(DEBOUNCE_MS);
  keypad.setHoldTime(500);

  endMax.begin();
  endMin.begin();
  pullButton.begin();

  loadCell.begin(CaptEffortDATA, CaptEffortCLK);
  loadCell.set_scale(effortScale);
  loadCell.tare(10);

  forcePid.SetOutputLimits(0, 255);
  forcePid.SetSampleTime(CONTROL_PERIOD_MS);
  forcePid.SetMode(AUTOMATIC);

  showWelcome();
  Serial.println(F("HELLO;DEVICE=SP55_ARDUINO_MEGA;PROTO=1;BAUD=115200"));
}

void loop() {
  unsigned long now = millis();
  pollSerial();
  handleKeypad();

  if (now - lastControlMs >= CONTROL_PERIOD_MS) {
    lastControlMs = now;
    readSensors();
    updateMachine(now);
    refreshLcd();
  }

  if (streaming && now - lastStreamMs >= streamPeriodMs) {
    lastStreamMs = now;
    sendTelemetry(now);
  }
}
