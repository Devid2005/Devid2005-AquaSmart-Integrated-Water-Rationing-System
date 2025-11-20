// ====== PINES DE CONTROL (Motores y Sensores) ======
const int MOTOR1_PIN = 10;
const int MOTOR2_PIN = 13;
const int TRIG = 9;
const int ECHO = 8;
const int TEMP_PIN = A1;

// ====== PINES DE LEDs INDICADORES ======
const int LED_AZUL_PIN  = 7; 
const int LED_ROJO_PIN  = 11; 
const int LED_VERDE_PIN = 12; 

// ====== PARAMETROS DE MOTORES Y AMBIENTE ======
float V1_obj_ml = 0;
float V2_obj_ml = 0;
float Q1_ml_s   = 45.0;  // caudal nominal motor 1
float Q2_ml_s   = 30.0;  // caudal nominal motor 2

const float TEMP_TRIGGER = 30.0;
const float K_FACTOR = 0.05;
const long THRESHOLD_CM = 5;

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

  long dur = pulseIn(ECHO, HIGH, 30000); // duración en microsegundos
  long dist = dur / 58.0;  // conversión a cm
  return dist;
}


// ====== FUNCIONES DE CONTROL ======
void motoresOff() {
  digitalWrite(MOTOR1_PIN, LOW);
  digitalWrite(MOTOR2_PIN, LOW);
}

void apagarLEDsDeEstado() {
  digitalWrite(LED_ROJO_PIN, LOW);
  digitalWrite(LED_VERDE_PIN, LOW);
  digitalWrite(LED_AZUL_PIN, LOW);
}

// ====== PROGRAMA PRINCIPAL ======
void setup() {
  Serial.begin(9600);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(MOTOR1_PIN, OUTPUT);
  pinMode(MOTOR2_PIN, OUTPUT);

  pinMode(LED_AZUL_PIN, OUTPUT);
  pinMode(LED_ROJO_PIN, OUTPUT);
  pinMode(LED_VERDE_PIN, OUTPUT);

  apagarLEDsDeEstado();
  motoresOff();

  Serial.println(">>> Sistema de Riego listo.");
}

void loop() {
  if (Serial.available() > 0) {
    String linea = Serial.readStringUntil('\n'); 
    linea.trim();

    if (linea.length() > 0) {
      int idx1 = linea.indexOf(',');
      int idx2 = linea.indexOf(',', idx1 + 1);

      int dia = linea.substring(0, idx1).toInt();
      V1_obj_ml = linea.substring(idx1 + 1, idx2).toFloat();
      V2_obj_ml = linea.substring(idx2 + 1).toFloat();

      Serial.print(">>> Datos recibidos: Dia ");
      Serial.print(dia);
      Serial.print(" | Motor1=");
      Serial.print(V1_obj_ml);
      Serial.print(" ml | Motor2=");
      Serial.print(V2_obj_ml);
      Serial.println(" ml");

      ejecutarRiegoDia(dia);
    }
  }
}

// ====== FUNCION DE RIEGO POR DIA ======
void ejecutarRiegoDia(int dia) {
  float vol1_total = 0;
  float vol2_total = 0;

  apagarLEDsDeEstado();
  Serial.print(">>> INICIO DIA ");
  Serial.println(dia);

  // Chequeo inicial de agua
  long dist_inicial = leerDistanciaCM();
  if (dist_inicial > THRESHOLD_CM) {
    motoresOff();
    digitalWrite(LED_VERDE_PIN, HIGH);
    Serial.print(">>> PARADA DIA ");
    Serial.println(dia);
    return;
  }

  digitalWrite(MOTOR1_PIN, HIGH);
  digitalWrite(MOTOR2_PIN, HIGH);
  digitalWrite(LED_AZUL_PIN, HIGH);

  while (vol1_total < V1_obj_ml || vol2_total < V2_obj_ml) {
    long dist = leerDistanciaCM();
    if (dist > THRESHOLD_CM) {
      motoresOff();
      digitalWrite(LED_AZUL_PIN, LOW);
      digitalWrite(LED_VERDE_PIN, HIGH);
      Serial.print(">>> PARADA DIA ");
      Serial.println(dia);
      return;
    }

    float T = leerTemperaturaLM35();
    if (T > TEMP_TRIGGER) digitalWrite(LED_ROJO_PIN, HIGH);
    else digitalWrite(LED_ROJO_PIN, LOW);

    float factorTemp = (T > TEMP_TRIGGER) ? (1.0 + K_FACTOR * (T - TEMP_TRIGGER)) : 1.0;

    float Q1_adj = Q1_ml_s * factorTemp;
    float Q2_adj = Q2_ml_s * factorTemp;

    // Incremento de volumenes
    if (vol1_total < V1_obj_ml) vol1_total += Q1_adj;
    if (vol2_total < V2_obj_ml) vol2_total += Q2_adj;

    // Corrección si pasa el objetivo
    if (vol1_total >= V1_obj_ml) {
      digitalWrite(MOTOR1_PIN, LOW);
      vol1_total = V1_obj_ml;
    }
    if (vol2_total >= V2_obj_ml) {
      digitalWrite(MOTOR2_PIN, LOW);
      vol2_total = V2_obj_ml;
    }

    // Si ambos motores ya se apagaron → salir
    if (digitalRead(MOTOR1_PIN) == LOW && digitalRead(MOTOR2_PIN) == LOW) break;

    // Estado en vivo
    Serial.print("Temp: "); Serial.print(T,1); Serial.println(" °C");
    Serial.print("Dist: "); Serial.print(dist); Serial.println(" cm");
    Serial.print("M1: "); Serial.print(vol1_total, 0); Serial.print(" ml ");
    Serial.print("M2: "); Serial.print(vol2_total, 0); Serial.println(" ml");
    Serial.println("-----");

    delay(1000);
  }

  motoresOff();
  apagarLEDsDeEstado();
  Serial.print(">>> DIA ");
  Serial.print(dia);
  Serial.println(" COMPLETADO");
}
