/**
 * SmartKnob STM32 — Simple 2-Mode Version
 *
 * Two working haptic modes:
 *   H  → Haptic Wheel  : virtual detents (infinite rotation)
 *   I  → Inertial Wheel : simulated rotational inertia
 *
 * Serial Protocol:
 *   Commands (PC → STM32):
 *     H             → Haptic mode (detents)
 *     I             → Inertia mode
 *     S<val>        → Detent count (2-360)
 *     D<val>        → Detent strength (voltage)
 *     J<val>        → Virtual inertia
 *     B<val>        → Damping
 *     F<val>        → Friction
 *     K<val>        → Coupling stiffness
 *     P             → Query position
 *     Q             → Query full state
 *
 *   Events (STM32 → PC):
 *     P<angle>      → Position update (degrees)
 *     A<cmd>        → Command acknowledged
 *
 * Hardware:
 *   MCU:     Nucleo L452RE (STM32L452RET6)
 *   Sensor:  MT6701 magnetic encoder via SSI
 *   Driver:  SimpleFOCShield V3.2
 */

#include <SimpleFOC.h>
#include "SimpleFOCDrivers.h"
#include "encoders/MT6701/MagneticSensorMT6701SSI.h"

// ======================== Hardware ========================
#define SENSOR_CS PB6
MagneticSensorMT6701SSI sensor(SENSOR_CS);
BLDCMotor motor = BLDCMotor(7);
BLDCDriver3PWM driver = BLDCDriver3PWM(PB10, PC7, PB4, PA9);
InlineCurrentSense current_sense = InlineCurrentSense(185.0f, PA0, PA4);

// ======================== Mode ========================
enum HapticMode { MODE_HAPTIC, MODE_INERTIA, MODE_SPRING, MODE_BOUNDED, MODE_POSITION };
HapticMode currentMode = MODE_HAPTIC;
HapticMode previousMode = MODE_HAPTIC;  // For returning after position seek

// ======================== Parameters ========================
// Haptic mode
int   detent_count    = 36;      // detents per 360°
float detent_strength = 1.5f;    // snap strength (V)

// Inertia mode
float virtual_inertia  = 5.0f;   // mass feel
float inertia_damping  = 1.0f;   // drag
float inertia_friction = 0.2f;   // static friction
float coupling_K       = 40.0f;  // spring stiffness

// Spring mode
float spring_center    = 0.0f;   // center position (rad)
float spring_stiffness = 10.0f;  // spring constant (V/rad)
float spring_damping   = 0.1f;   // velocity damping to prevent oscillation

// Bounded mode (detents with walls)
// Uses same detent_count and detent_strength as haptic mode
float bound_min          = -60.0f * _PI / 180.0f;  // lower bound (rad), default -60°
float bound_max          = +60.0f * _PI / 180.0f;  // upper bound (rad), default +60°
float wall_strength      = 20.0f;                   // wall spring constant (V/rad)
float wall_damping       = 2.0f;                    // wall damping to prevent overshoot (V*s/rad)

// Virtual flywheel state
float virt_pos = 0.0f;
float virt_vel = 0.0f;
unsigned long prev_time_us = 0;

// Position reporting
float last_reported_angle = 0.0f;
unsigned long last_report_us = 0;
float report_interval_ms = 20.0f;
float report_threshold_deg = 0.5f;

// Position seek
float seek_tolerance_rad = 0.06f;  // ~3.4 degrees - relaxed for reliable completion
unsigned long seek_settle_start = 0;
unsigned long seek_start_time = 0;
const unsigned long SEEK_SETTLE_MS = 200;  // Hold at target for 200ms before returning
const unsigned long SEEK_TIMEOUT_MS = 10000;  // 10 second timeout for long seeks

// User button
#define USER_BTN PC13
bool btn_last = HIGH;
unsigned long btn_last_ms = 0;

// ======================== Commander ========================
Commander command = Commander(Serial);

// ======================== Helpers ========================
float getCurrentAngleDeg() {
  // Use motor.shaft_angle (not sensor.getAngle) for consistency with SimpleFOC's angle controller
  return motor.shaft_angle * 180.0f / _PI;
}

// ======================== Mode Commands ========================
void doHaptic(char* cmd) {
  motor.controller = MotionControlType::torque;  // Ensure torque mode
  currentMode = MODE_HAPTIC;
  report_interval_ms = 20.0f;
  Serial.println(F("A:H"));
  Serial.print(F("Mode: HAPTIC | Detents: ")); Serial.print(detent_count);
  Serial.print(F(" | Strength: ")); Serial.println(detent_strength);
}

void doInertia(char* cmd) {
  motor.controller = MotionControlType::torque;  // Ensure torque mode
  currentMode = MODE_INERTIA;
  report_interval_ms = 10.0f;
  virt_pos = motor.shaft_angle;
  virt_vel = 0.0f;
  prev_time_us = micros();
  Serial.println(F("A:I"));
  Serial.print(F("Mode: INERTIA | J: ")); Serial.print(virtual_inertia);
  Serial.print(F(" | B: ")); Serial.print(inertia_damping);
  Serial.print(F(" | K: ")); Serial.println(coupling_K);
}

void doSpring(char* cmd) {
  motor.controller = MotionControlType::torque;  // Ensure torque mode
  currentMode = MODE_SPRING;
  report_interval_ms = 20.0f;
  // Set center at current position by default
  spring_center = motor.shaft_angle;
  Serial.println(F("A:C"));
  Serial.print(F("Mode: SPRING | Center: ")); Serial.print(spring_center * 180.0f / _PI, 1);
  Serial.print(F(" deg | Stiffness: ")); Serial.print(spring_stiffness);
  Serial.print(F(" | Damping: ")); Serial.println(spring_damping);
}

void doBounded(char* cmd) {
  motor.controller = MotionControlType::torque;  // Ensure torque mode
  currentMode = MODE_BOUNDED;
  report_interval_ms = 20.0f;
  Serial.println(F("A:O"));  // O for bOunded
  Serial.print(F("Mode: BOUNDED | Range: ")); 
  Serial.print(bound_min * 180.0f / _PI, 1); Serial.print(F(" to "));
  Serial.print(bound_max * 180.0f / _PI, 1); Serial.println(F(" deg"));
  Serial.print(F("  Detents: ")); Serial.print(detent_count);
  Serial.print(F(" | Strength: ")); Serial.print(detent_strength);
  Serial.print(F(" | Wall: ")); Serial.println(wall_strength);
  Serial.println(F("  (Uses same detent S/D as haptic mode)"));
}

// ======================== Parameter Commands ========================
void doDetentCount(char* cmd) {
  if (cmd && strlen(cmd) > 0) {
    detent_count = constrain(atoi(cmd), 2, 360);
  }
  Serial.print(F("A:S")); Serial.println(detent_count);
}

void doDetentStrength(char* cmd) {
  command.scalar(&detent_strength, cmd);
  Serial.print(F("A:D")); Serial.println(detent_strength);
}

void doDamping(char* cmd) {
  command.scalar(&inertia_damping, cmd);
  Serial.print(F("A:B")); Serial.println(inertia_damping);
}

void doFriction(char* cmd) {
  command.scalar(&inertia_friction, cmd);
  Serial.print(F("A:F")); Serial.println(inertia_friction);
}

void doInertiaVal(char* cmd) {
  command.scalar(&virtual_inertia, cmd);
  Serial.print(F("A:J")); Serial.println(virtual_inertia);
}

void doCoupling(char* cmd) {
  command.scalar(&coupling_K, cmd);
  Serial.print(F("A:K")); Serial.println(coupling_K);
}

// Spring parameter: set stiffness
void doSpringStiffness(char* cmd) {
  command.scalar(&spring_stiffness, cmd);
  Serial.print(F("A:W")); Serial.println(spring_stiffness);
}

// Spring parameter: set center position (degrees, or empty to use current)
void doSpringCenter(char* cmd) {
  if (cmd == nullptr || strlen(cmd) == 0) {
    // Set center to current position
    spring_center = motor.shaft_angle;
  } else {
    // Set center to specified angle
    spring_center = atof(cmd) * _PI / 180.0f;
  }
  Serial.print(F("A:E")); Serial.println(spring_center * 180.0f / _PI, 1);
  Serial.print(F("Spring center set to: ")); Serial.print(spring_center * 180.0f / _PI, 1); Serial.println(F(" deg"));
}

// Spring parameter: set damping
void doSpringDamping(char* cmd) {
  command.scalar(&spring_damping, cmd);
  Serial.print(F("A:G")); Serial.println(spring_damping);
}

// Bounded parameter: set lower bound (degrees)
void doLowerBound(char* cmd) {
  if (cmd && strlen(cmd) > 0) {
    bound_min = atof(cmd) * _PI / 180.0f;
  }
  Serial.print(F("A:L")); Serial.println(bound_min * 180.0f / _PI, 1);
}

// Bounded parameter: set upper bound (degrees)
void doUpperBound(char* cmd) {
  if (cmd && strlen(cmd) > 0) {
    bound_max = atof(cmd) * _PI / 180.0f;
  }
  Serial.print(F("A:U")); Serial.println(bound_max * 180.0f / _PI, 1);
}

// Bounded parameter: set wall strength
void doWallStrength(char* cmd) {
  command.scalar(&wall_strength, cmd);
  Serial.print(F("A:A")); Serial.println(wall_strength);
}

void doQueryPosition(char* cmd) {
  Serial.print(F("P")); Serial.println(getCurrentAngleDeg(), 2);
}

// Move to position: Z<angle>
void doSeekPosition(char* cmd) {
  if (cmd == nullptr || strlen(cmd) == 0) {
    Serial.print(F("Position: ")); Serial.println(getCurrentAngleDeg(), 2);
    return;
  }
  float target_deg = atof(cmd);
  float target_rad = target_deg * _PI / 180.0f;
  
  // Save current mode and switch to position control
  if (currentMode != MODE_POSITION) {
    previousMode = currentMode;
  }
  currentMode = MODE_POSITION;
  seek_settle_start = 0;  // Reset settle timer
  seek_start_time = millis();  // Start timeout counter
  
  // Switch to SimpleFOC angle control
  motor.controller = MotionControlType::angle;
  motor.target = target_rad;
  
  Serial.print(F("A:Z")); Serial.println(target_deg, 1);
  Serial.print(F("Seeking to: ")); Serial.print(target_deg); Serial.println(F(" deg"));
}

void doQueryState(char* cmd) {
  const char* modeNames[] = {"HAPTIC", "INERTIA", "SPRING", "BOUNDED", "POSITION"};
  Serial.println(F("=== State ==="));
  Serial.print(F("Mode: ")); Serial.println(modeNames[currentMode]);
  Serial.print(F("Position: ")); Serial.print(getCurrentAngleDeg(), 2); Serial.println(F(" deg"));
  Serial.print(F("Detent count: ")); Serial.println(detent_count);
  Serial.print(F("Detent strength: ")); Serial.println(detent_strength);
  Serial.print(F("Inertia: ")); Serial.println(virtual_inertia);
  Serial.print(F("Damping: ")); Serial.println(inertia_damping);
  Serial.print(F("Friction: ")); Serial.println(inertia_friction);
  Serial.print(F("Coupling K: ")); Serial.println(coupling_K);
  Serial.print(F("Spring center: ")); Serial.print(spring_center * 180.0f / _PI, 1); Serial.println(F(" deg"));
  Serial.print(F("Spring stiffness: ")); Serial.println(spring_stiffness);
  Serial.print(F("Spring damping: ")); Serial.println(spring_damping);
  Serial.print(F("Pos PID: P=")); Serial.print(motor.P_angle.P);
  Serial.print(F(" I=")); Serial.print(motor.P_angle.I);
  Serial.print(F(" D=")); Serial.println(motor.P_angle.D);
  Serial.print(F("Velocity limit: ")); Serial.println(motor.velocity_limit);
}

// Motor config: M<subcmd><value>
// MPP<val> = Position P gain
// MPI<val> = Position I gain
// MPD<val> = Position D gain
// MVL<val> = Velocity limit
void doMotor(char* cmd) {
  if (cmd == nullptr || strlen(cmd) < 2) {
    // No subcommand - show current PID values
    Serial.print(F("PP=")); Serial.print(motor.P_angle.P, 2);
    Serial.print(F(" PI=")); Serial.print(motor.P_angle.I, 2);
    Serial.print(F(" PD=")); Serial.print(motor.P_angle.D, 2);
    Serial.print(F(" VL=")); Serial.println(motor.velocity_limit, 1);
    return;
  }
  
  // Parse subcommand (first 2 chars)
  char sub[3] = {cmd[0], cmd[1], '\0'};
  float val = atof(cmd + 2);
  
  if (strcmp(sub, "PP") == 0) {
    motor.P_angle.P = val;
    Serial.print(F("A:MPP")); Serial.println(val, 2);
  } else if (strcmp(sub, "PI") == 0) {
    motor.P_angle.I = val;
    Serial.print(F("A:MPI")); Serial.println(val, 2);
  } else if (strcmp(sub, "PD") == 0) {
    motor.P_angle.D = val;
    Serial.print(F("A:MPD")); Serial.println(val, 2);
  } else if (strcmp(sub, "VL") == 0) {
    motor.velocity_limit = val;
    Serial.print(F("A:MVL")); Serial.println(val, 1);
  } else {
    // Pass to SimpleFOC's built-in motor commander
    command.motor(&motor, cmd);
  }
}

// ======================== Setup ========================
void setup() {
  Serial.begin(115200);
  delay(1000);
  SimpleFOCDebug::enable(&Serial);

  pinMode(USER_BTN, INPUT);

  // Sensor
  sensor.init();
  motor.linkSensor(&sensor);

  // Driver
  driver.voltage_power_supply = 12;
  driver.init();
  motor.linkDriver(&driver);

  // Current sense
  current_sense.linkDriver(&driver);
  current_sense.init();
  motor.linkCurrentSense(&current_sense);

  // Motor config
  motor.controller = MotionControlType::torque;
  motor.voltage_limit = 8;
  motor.voltage_sensor_align = 5;
  motor.LPF_velocity.Tf = 0.03f;
  
  // Angle controller config (for position mode)
  motor.P_angle.P = 50.0f;
  motor.P_angle.I = 0.0f;
  motor.P_angle.D = 0.3f;
  motor.velocity_limit = 40.0f;  // rad/s max speed during seek

  // Init
  motor.useMonitoring(Serial);
  motor.monitor_downsample = 0;
  motor.init();
  motor.initFOC();
  motor.target = 0;

  // Commands
  command.add('H', doHaptic,        "haptic mode (detents)");
  command.add('I', doInertia,       "inertia mode");
  command.add('C', doSpring,        "spring mode (centered)");
  command.add('O', doBounded,       "bounded mode (detents+walls)");
  command.add('S', doDetentCount,   "detent count (2-360)");
  command.add('D', doDetentStrength,"detent strength (V)");
  command.add('B', doDamping,       "damping");
  command.add('F', doFriction,      "friction");
  command.add('J', doInertiaVal,    "virtual inertia");
  command.add('K', doCoupling,      "coupling stiffness");
  command.add('W', doSpringStiffness, "spring stiffness (V/rad)");
  command.add('E', doSpringCenter,  "spring center (deg or empty=current)");
  command.add('G', doSpringDamping, "spring damping");
  command.add('L', doLowerBound,    "bounded lower limit (deg)");
  command.add('U', doUpperBound,    "bounded upper limit (deg)");
  command.add('A', doWallStrength,  "bounded wall strength (V/rad)");
  command.add('P', doQueryPosition, "query position");
  command.add('Q', doQueryState,    "query state");
  command.add('Z', doSeekPosition,  "seek to position (degrees)");
  command.add('M', doMotor,         "motor config");

  Serial.println(F("=== SmartKnob Simple ==="));
  Serial.println(F("H = Haptic, I = Inertia, C = Spring"));
  Serial.println(F("S<n> = detent count, D<v> = strength"));
  Serial.println(F("J/B/F/K = inertia, W/E/G = spring params"));
  Serial.println(F("P = position, Q = state, Z<deg> = seek"));
  Serial.println();

  _delay(500);
}

// ======================== Haptic Torque ========================
float computeHapticTorque() {
  float angle_rad = motor.shaft_angle;  // Use shaft_angle for consistency
  float phase = (float)detent_count * angle_rad;
  return detent_strength * -sin(phase);
}

// ======================== Inertia Torque ========================
float computeInertiaTorque() {
  float actual_pos = motor.shaft_angle;

  unsigned long now_us = micros();
  float dt = (now_us - prev_time_us) * 1e-6f;
  prev_time_us = now_us;
  if (dt <= 0.0f || dt > 0.1f) dt = 0.001f;

  float pos_error = actual_pos - virt_pos;
  float accel = (coupling_K * pos_error - inertia_damping * virt_vel) / virtual_inertia;

  if (inertia_friction > 0.0f) {
    if (virt_vel > 0.0f)      accel -= inertia_friction;
    else if (virt_vel < 0.0f) accel += inertia_friction;
  }

  virt_vel += accel * dt;
  virt_pos += virt_vel * dt;

  return -coupling_K * pos_error;
}

// ======================== Spring Torque ========================
// Hooke's Law: F = -k * x, plus velocity damping to prevent oscillation
float computeSpringTorque() {
  float displacement = motor.shaft_angle - spring_center;  // How far from center (rad)
  
  // Spring force: pulls back toward center
  float torque = -spring_stiffness * displacement;
  
  // Velocity damping: opposes motion to prevent oscillation
  torque -= spring_damping * motor.shaft_velocity;
  
  return torque;
}

// ======================== Bounded Torque ========================
// Detents distributed within a bounded range, with hard walls at limits
float computeBoundedTorque() {
  float pos = motor.shaft_angle;
  float vel = motor.shaft_velocity;
  float torque = 0.0f;
  float buffer_rad = 2.0f * _PI / 180.0f;  // 2 degree buffer before hitting wall
  
  // Check if we're outside the bounds - apply wall force with damping
  if (pos < bound_min-buffer_rad) {
    // Below minimum - push back up (positive torque)
    float overflow = (bound_min+buffer_rad*5) - pos;
    torque = wall_strength * overflow - wall_damping * vel;
  } else if (pos > bound_max+buffer_rad) {
    // Above maximum - push back down (negative torque)
    float overflow = pos - (bound_max-buffer_rad*5);
    torque = -wall_strength * overflow - wall_damping * vel;
  } else {
    // Within bounds - apply detent haptics (using same params as haptic mode)
    float range = bound_max - bound_min;
    float normalized = (pos - bound_min) / range;  // 0 to 1 within bounds
    // Phase: goes through (detent_count-1) full cycles from min to max
    // This puts detents at: min, min+range/(n-1), min+2*range/(n-1), ..., max
    float phase = normalized * (float)(detent_count - 1) * 2.0f * _PI;
    torque = detent_strength * -sin(phase);
  }
  
  return torque;
}

// ======================== Position Reporting ========================
void reportPosition() {
  unsigned long now_us = micros();
  float elapsed_ms = (now_us - last_report_us) / 1000.0f;
  
  if (elapsed_ms < report_interval_ms) return;
  
  float current_angle = getCurrentAngleDeg();
  float delta = current_angle - last_reported_angle;
  
  if (fabs(delta) >= report_threshold_deg) {
    Serial.print(F("P")); Serial.println(current_angle, 2);
    last_reported_angle = current_angle;
    last_report_us = now_us;
  }
}

// ======================== Toggle Mode (Button) ========================
void toggleMode() {
  // Cycle: HAPTIC -> INERTIA -> SPRING -> BOUNDED -> HAPTIC
  switch (currentMode) {
    case MODE_HAPTIC:
      doInertia(nullptr);
      break;
    case MODE_INERTIA:
      doSpring(nullptr);
      break;
    case MODE_SPRING:
      doBounded(nullptr);
      break;
    case MODE_BOUNDED:
    default:
      doHaptic(nullptr);
      break;
  }
}

// ======================== Loop ========================
void loop() {
  motor.loopFOC();

  // Button toggle (only between haptic/inertia, exits position mode)
  bool btn_now = digitalRead(USER_BTN);
  if (btn_now == LOW && btn_last == HIGH && (millis() - btn_last_ms > 200)) {
    btn_last_ms = millis();
    if (currentMode == MODE_POSITION) {
      // Exit position mode, return to previous
      motor.controller = MotionControlType::torque;
      currentMode = previousMode;
      Serial.println(F("Exited position mode"));
    } else {
      toggleMode();
    }
  }
  btn_last = btn_now;

  // Handle modes
  if (currentMode == MODE_POSITION) {
    // SimpleFOC handles position control internally
    motor.move(motor.target);
    
    // Check if we've reached target position
    float pos_error = fabs(motor.shaft_angle - motor.target);
    bool timeout = (millis() - seek_start_time) > SEEK_TIMEOUT_MS;
    
    if (pos_error < seek_tolerance_rad || timeout) {
      if (seek_settle_start == 0) {
        seek_settle_start = millis();  // Start settle timer
        if (timeout) {
          Serial.print(F("Seek timeout, error=")); Serial.println(pos_error * 180.0f / _PI, 1);
        }
      } else if (millis() - seek_settle_start > SEEK_SETTLE_MS) {
        // Settled at target (or timed out) - return to previous mode
        motor.controller = MotionControlType::torque;
        currentMode = previousMode;
        seek_settle_start = 0;
        Serial.println(F("A:SEEK_DONE"));
        Serial.print(F("Final position: ")); Serial.print(getCurrentAngleDeg(), 1);
        Serial.print(F(", returning to "));
        const char* modeNames[] = {"HAPTIC", "INERTIA", "SPRING", "BOUNDED"};
        Serial.println(modeNames[previousMode]);
        // Re-init inertia state if returning to inertia mode
        if (previousMode == MODE_INERTIA) {
          virt_pos = motor.shaft_angle;
          virt_vel = 0.0f;
          prev_time_us = micros();
        }
      }
    } else {
      seek_settle_start = 0;  // Reset if we drifted away
    }
  } else {
    // Compute torque based on haptic mode
    float voltage;
    switch (currentMode) {
      case MODE_HAPTIC:
        voltage = computeHapticTorque();
        break;
      case MODE_INERTIA:
        voltage = computeInertiaTorque();
        break;
      case MODE_SPRING:
        voltage = computeSpringTorque();
        break;
      case MODE_BOUNDED:
        voltage = computeBoundedTorque();
        break;
      default:
        voltage = 0;
    }

    // Clamp and apply
    voltage = constrain(voltage, -motor.voltage_limit, motor.voltage_limit);
    motor.move(voltage);
  }

  // Position reporting
  reportPosition();

  // Process serial commands
  command.run();
}
