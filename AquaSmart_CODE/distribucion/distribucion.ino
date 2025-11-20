// =====================================================
//  Arduino - Riego Diario con Joystick y Control Doble
// =====================================================

// ====== PINES DE CONTROL ======
const int MOTOR1_PIN = 10;
const int MOTOR2_PIN = 13;
const int TRIG = 9;
const int ECHO = 8;
const int TEMP_PIN = A1;
const int JOY_SW = 2;

// ====== LEDS ======
const int LED_AZUL_PIN  = 7; 
const int LED_ROJO_PIN  = 11; 
const int LED_VERDE_PIN = 12; 

// ====== PARÁMETROS ======
float Q1_ml_s = 45.0;   // Caudal motor 1 (ml/s)
float Q2_ml_s = 30.0;   // Caudal motor 2 (ml/s)
const float TEMP_TRIGGER = 30.0;
const float K_FACTOR = 0.05;
const long THRESHOLD_CM = 5;  // distancia mínima

bool lastButton = HIGH;

// ====== FUNCIONES DE SENSORES ======
float leerTemperaturaLM35() {
  int lectura = analogRead(TEMP_PIN);
  float volt = (5.0 / 1024.0) * lectura;
  return volt * 100.0;
}

long leerDistanciaCM() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long dur = pulseIn(ECHO, HIGH, 30000);
  return dur / 58.0;  // Conversión a cm
}

// ====== FUNCIONES DE CONTROL ======
void motoresOff() {
  digitalWrite(MOTOR1_PIN, LOW);
  digitalWrite(MOTOR2_PIN, LOW);
}

void apagarLEDs() {
  digitalWrite(LED_ROJO_PIN, LOW);
  digitalWrite(LED_VERDE_PIN, LOW);
  digitalWrite(LED_AZUL_PIN, LOW);
}

// ====== SETUP ======
void setup() {
  Serial.begin(9600);
  pinMode(JOY_SW, INPUT_PULLUP);
  pinMode(MOTOR1_PIN, OUTPUT);
  pinMode(MOTOR2_PIN, OUTPUT);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(LED_AZUL_PIN, OUTPUT);
  pinMode(LED_ROJO_PIN, OUTPUT);
  pinMode(LED_VERDE_PIN, OUTPUT);

  apagarLEDs();
  motoresOff();

  Serial.println(">>> Modo riego listo. Presiona joystick para avanzar los días.");
}

// ====== LOOP ======
void loop() {
  bool currentButton = digitalRead(JOY_SW);

  // Detectar presión del joystick
  if (lastButton == HIGH && currentButton == LOW) {
    Serial.println("CLICK");
  }
  lastButton = currentButton;

  // Escuchar volúmenes desde Python
  if (Serial.available() > 0) {
    String linea = Serial.readStringUntil('\n');
    linea.trim();

    if (linea.length() > 0) {
      int idx1 = linea.indexOf(',');
      int idx2 = linea.indexOf(',', idx1 + 1);

      int dia = linea.substring(0, idx1).toInt();
      float V1_obj_ml = linea.substring(idx1 + 1, idx2).toFloat();
      float V2_obj_ml = linea.substring(idx2 + 1).toFloat();

      Serial.print(">>> Día "); Serial.print(dia);
      Serial.print(" recibido | M1="); Serial.print(V1_obj_ml);
      Serial.print(" ml | M2="); Serial.print(V2_obj_ml); Serial.println(" ml");

      ejecutarRiegoDia(dia, V1_obj_ml, V2_obj_ml);
    }
  }

  delay(100);
}

// ====== EJECUTAR RIEGO POR DÍA ======
void ejecutarRiegoDia(int dia, float V1_obj_ml, float V2_obj_ml) {
  float vol1_total = 0;
  float vol2_total = 0;

  apagarLEDs();
  digitalWrite(LED_AZUL_PIN, HIGH);
  digitalWrite(MOTOR1_PIN, HIGH);
  digitalWrite(MOTOR2_PIN, HIGH);

  Serial.print(">>> Iniciando riego día "); Serial.println(dia);

  while (vol1_total < V1_obj_ml || vol2_total < V2_obj_ml) {
    long dist = leerDistanciaCM();
    float T = leerTemperaturaLM35();

    if (T > TEMP_TRIGGER) digitalWrite(LED_ROJO_PIN, HIGH);
    else digitalWrite(LED_ROJO_PIN, LOW);

    float factor = (T > TEMP_TRIGGER) ? (1.0 + K_FACTOR * (T - TEMP_TRIGGER)) : 1.0;
    float Q1_adj = Q1_ml_s * factor;
    float Q2_adj = Q2_ml_s * factor;

    if (vol1_total < V1_obj_ml) vol1_total += Q1_adj;
    if (vol2_total < V2_obj_ml) vol2_total += Q2_adj;

    if (vol1_total >= V1_obj_ml) digitalWrite(MOTOR1_PIN, LOW);
    if (vol2_total >= V2_obj_ml) digitalWrite(MOTOR2_PIN, LOW);

    if (dist > THRESHOLD_CM) {
      motoresOff();
      digitalWrite(LED_VERDE_PIN, HIGH);
      Serial.println(">>> Parada por nivel de agua.");
      break;
    }

    Serial.print("Temp: "); Serial.print(T,1); Serial.print("°C | ");
    Serial.print("Dist: "); Serial.print(dist); Serial.print(" cm | ");
    Serial.print("M1: "); Serial.print(vol1_total); Serial.print("/");
    Serial.print(V1_obj_ml); Serial.print(" | M2: ");
    Serial.print(vol2_total); Serial.print("/"); Serial.println(V2_obj_ml);
    delay(1000);
  }

  motoresOff();
  apagarLEDs();
  digitalWrite(LED_VERDE_PIN, HIGH);
  Serial.print(">>> Día "); Serial.print(dia); Serial.println(" completado.\n");
}
