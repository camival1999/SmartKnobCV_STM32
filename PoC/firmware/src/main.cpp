/**
 * SmartKnob STM32 — Main Entry Point
 *
 * Hardware object instantiation, setup(), and loop() only.
 * All logic is delegated to modules:
 *   config.h/cpp — Pin definitions, mode enum, parameter defaults
 *   haptics      — Torque computation (4 models)
 *   comms        — Serial commands, position reporting, Commander
 *   button       — Debounced multi-button input
 *
 * Serial Protocol:
 *   PC → STM32: Single-letter commands (H, I, C, O, S, D, etc.)
 *   STM32 → PC: "A:<cmd>" acks, "P<angle>" position updates
 *
 * Hardware:
 *   MCU:     Nucleo L452RE (STM32L452RET6)
 *   Sensor:  MT6701 magnetic encoder via SSI
 *   Driver:  SimpleFOCShield V3.2
 */

#include "config.h"
#include "haptics.h"
#include "comms.h"
#include "button.h"

// ======================== Hardware Object Definitions ========================
// These are declared extern in config.h, defined here because they need
// constructor arguments. All tunable parameters live in config.cpp.
MagneticSensorMT6701SSI sensor(SENSOR_CS);
BLDCMotor motor = BLDCMotor(MOTOR_POLE_PAIRS);
BLDCDriver3PWM driver = BLDCDriver3PWM(PWM_A, PWM_B, PWM_C, DRIVER_EN);
InlineCurrentSense current_sense = InlineCurrentSense(CURRENT_SENSE_GAIN, CURRENT_A, CURRENT_B);
Commander command = Commander(Serial);

// ======================== Setup ========================
void setup() {
  Serial.begin(115200);
  delay(1000);
  SimpleFOCDebug::enable(&Serial);

  // Button
  initButton(userBtn, USER_BTN);

  // Sensor
  sensor.init();
  motor.linkSensor(&sensor);

  // Driver
  driver.voltage_power_supply = SUPPLY_VOLTAGE;
  driver.init();
  motor.linkDriver(&driver);

  // Current sense
  current_sense.linkDriver(&driver);
  current_sense.init();
  motor.linkCurrentSense(&current_sense);

  // Motor config
  motor.controller = MotionControlType::torque;
  motor.voltage_limit = VOLTAGE_LIMIT;
  motor.voltage_sensor_align = VOLTAGE_SENSOR_ALIGN;
  motor.LPF_velocity.Tf = VELOCITY_LPF_TF;

  // Angle controller (for position seek mode)
  motor.P_angle.P = POS_PID_P;
  motor.P_angle.I = POS_PID_I;
  motor.P_angle.D = POS_PID_D;
  motor.velocity_limit = DEFAULT_VELOCITY_LIMIT;

  // Init motor
  motor.useMonitoring(Serial);
  motor.monitor_downsample = 0;
  motor.init();
  motor.initFOC();
  motor.target = 0;

  // Commander
  setupCommander();
  printBanner();

  _delay(500);
}

// ======================== Loop ========================
void loop() {
  motor.loopFOC();

  // Button
  if (checkButtonPress(userBtn)) {
    handleButtonAction();
  }

  // Mode dispatch
  if (currentMode == MODE_POSITION) {
    // SimpleFOC handles position control internally
    motor.move(motor.target);

    // Check if we've reached target position
    float pos_error = fabs(motor.shaft_angle - motor.target);
    bool timeout = (millis() - seek_start_time) > SEEK_TIMEOUT_MS;

    if (pos_error < seek_tolerance_rad || timeout) {
      if (seek_settle_start == 0) {
        seek_settle_start = millis();
        if (timeout) {
          Serial.print(F("Seek timeout, error=")); Serial.println(pos_error * 180.0f / _PI, 1);
        }
      } else if (millis() - seek_settle_start > SEEK_SETTLE_MS) {
        // Settled at target — return to previous mode
        motor.controller = MotionControlType::torque;
        currentMode = previousMode;
        seek_settle_start = 0;
        Serial.println(F("A:SEEK_DONE"));
        Serial.print(F("Final position: ")); Serial.print(getCurrentAngleDeg(), 1);
        Serial.print(F(", returning to "));
        const char* modeNames[] = {"HAPTIC", "INERTIA", "SPRING", "BOUNDED"};
        Serial.println(modeNames[previousMode]);
        if (previousMode == MODE_INERTIA) {
          resetInertiaState();
        }
      }
    } else {
      seek_settle_start = 0;
    }
  } else {
    // Compute torque based on haptic mode
    float voltage;
    switch (currentMode) {
      case MODE_HAPTIC:  voltage = computeHapticTorque();  break;
      case MODE_INERTIA: voltage = computeInertiaTorque(); break;
      case MODE_SPRING:  voltage = computeSpringTorque();  break;
      case MODE_BOUNDED: voltage = computeBoundedTorque(); break;
      default:           voltage = 0;
    }

    voltage = constrain(voltage, -motor.voltage_limit, motor.voltage_limit);
    motor.move(voltage);
  }

  reportPosition();
  command.run();
}
