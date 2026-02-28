/**
 * comms.cpp — Serial Communication & Commander
 *
 * Implements all serial command handlers, position reporting,
 * and Commander registration.
 */

#include "comms.h"
#include "config.h"
#include "haptics.h"

// ======================== Mode Commands ========================

void doHaptic(char* cmd) {
  motor.controller = MotionControlType::torque;
  currentMode = MODE_HAPTIC;
  report_interval_ms = DEFAULT_REPORT_INTERVAL_MS;
  Serial.println(F("A:H"));
  Serial.print(F("Mode: HAPTIC | Detents: ")); Serial.print(detent_count);
  Serial.print(F(" | Strength: ")); Serial.println(detent_strength);
}

void doInertia(char* cmd) {
  motor.controller = MotionControlType::torque;
  currentMode = MODE_INERTIA;
  report_interval_ms = INERTIA_REPORT_INTERVAL_MS;
  resetInertiaState();
  Serial.println(F("A:I"));
  Serial.print(F("Mode: INERTIA | J: ")); Serial.print(virtual_inertia);
  Serial.print(F(" | B: ")); Serial.print(inertia_damping);
  Serial.print(F(" | K: ")); Serial.println(coupling_K);
}

void doSpring(char* cmd) {
  motor.controller = MotionControlType::torque;
  currentMode = MODE_SPRING;
  report_interval_ms = DEFAULT_REPORT_INTERVAL_MS;
  spring_center = motor.shaft_angle;
  Serial.println(F("A:C"));
  Serial.print(F("Mode: SPRING | Center: ")); Serial.print(spring_center * 180.0f / _PI, 1);
  Serial.print(F(" deg | Stiffness: ")); Serial.print(spring_stiffness);
  Serial.print(F(" | Damping: ")); Serial.println(spring_damping);
}

void doBounded(char* cmd) {
  motor.controller = MotionControlType::torque;
  currentMode = MODE_BOUNDED;
  report_interval_ms = DEFAULT_REPORT_INTERVAL_MS;
  Serial.println(F("A:O"));
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

void doSpringStiffness(char* cmd) {
  command.scalar(&spring_stiffness, cmd);
  Serial.print(F("A:W")); Serial.println(spring_stiffness);
}

void doSpringCenter(char* cmd) {
  if (cmd == nullptr || strlen(cmd) == 0) {
    spring_center = motor.shaft_angle;
  } else {
    spring_center = atof(cmd) * _PI / 180.0f;
  }
  Serial.print(F("A:E")); Serial.println(spring_center * 180.0f / _PI, 1);
  Serial.print(F("Spring center set to: ")); Serial.print(spring_center * 180.0f / _PI, 1); Serial.println(F(" deg"));
}

void doSpringDamping(char* cmd) {
  command.scalar(&spring_damping, cmd);
  Serial.print(F("A:G")); Serial.println(spring_damping);
}

void doLowerBound(char* cmd) {
  if (cmd && strlen(cmd) > 0) {
    bound_min = atof(cmd) * _PI / 180.0f;
  }
  Serial.print(F("A:L")); Serial.println(bound_min * 180.0f / _PI, 1);
}

void doUpperBound(char* cmd) {
  if (cmd && strlen(cmd) > 0) {
    bound_max = atof(cmd) * _PI / 180.0f;
  }
  Serial.print(F("A:U")); Serial.println(bound_max * 180.0f / _PI, 1);
}

void doWallStrength(char* cmd) {
  command.scalar(&wall_strength, cmd);
  Serial.print(F("A:A")); Serial.println(wall_strength);
}

// ======================== Query/Action Commands ========================

void doQueryPosition(char* cmd) {
  Serial.print(F("P")); Serial.println(getCurrentAngleDeg(), 2);
}

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
  seek_settle_start = 0;
  seek_start_time = millis();

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

void doMotor(char* cmd) {
  if (cmd == nullptr || strlen(cmd) < 2) {
    Serial.print(F("PP=")); Serial.print(motor.P_angle.P, 2);
    Serial.print(F(" PI=")); Serial.print(motor.P_angle.I, 2);
    Serial.print(F(" PD=")); Serial.print(motor.P_angle.D, 2);
    Serial.print(F(" VL=")); Serial.println(motor.velocity_limit, 1);
    return;
  }

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
    command.motor(&motor, cmd);
  }
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

// ======================== Commander Setup ========================

void setupCommander() {
  command.add('H', doHaptic,         "haptic mode (detents)");
  command.add('I', doInertia,        "inertia mode");
  command.add('C', doSpring,         "spring mode (centered)");
  command.add('O', doBounded,        "bounded mode (detents+walls)");
  command.add('S', doDetentCount,    "detent count (2-360)");
  command.add('D', doDetentStrength, "detent strength (V)");
  command.add('B', doDamping,        "damping");
  command.add('F', doFriction,       "friction");
  command.add('J', doInertiaVal,     "virtual inertia");
  command.add('K', doCoupling,       "coupling stiffness");
  command.add('W', doSpringStiffness,"spring stiffness (V/rad)");
  command.add('E', doSpringCenter,   "spring center (deg or empty=current)");
  command.add('G', doSpringDamping,  "spring damping");
  command.add('L', doLowerBound,     "bounded lower limit (deg)");
  command.add('U', doUpperBound,     "bounded upper limit (deg)");
  command.add('A', doWallStrength,   "bounded wall strength (V/rad)");
  command.add('P', doQueryPosition,  "query position");
  command.add('Q', doQueryState,     "query state");
  command.add('Z', doSeekPosition,   "seek to position (degrees)");
  command.add('M', doMotor,          "motor config");
}

void printBanner() {
  Serial.println(F("=== SmartKnob Simple ==="));
  Serial.println(F("H = Haptic, I = Inertia, C = Spring"));
  Serial.println(F("S<n> = detent count, D<v> = strength"));
  Serial.println(F("J/B/F/K = inertia, W/E/G = spring params"));
  Serial.println(F("P = position, Q = state, Z<deg> = seek"));
  Serial.println();
}
