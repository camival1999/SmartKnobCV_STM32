/**
 * button.cpp — Multi-Button Input Handler
 *
 * Implements debounced button detection using ButtonState struct.
 * Currently manages one button (USER_BTN) for mode cycling.
 *
 * To add a second button:
 *   1. Define pin in config.h:  #define BTN2_PIN PA5
 *   2. Declare in button.h:     extern ButtonState btn2;
 *   3. Define here:             ButtonState btn2;
 *   4. Init in setup():         initButton(btn2, BTN2_PIN);
 *   5. Check in loop():         if (checkButtonPress(btn2)) { ... }
 */

#include "button.h"
#include "config.h"
#include "comms.h"

// ======================== Global Button Instance ========================
ButtonState userBtn;

// ======================== Init ========================
void initButton(ButtonState& btn, uint8_t pin) {
  btn.pin = pin;
  btn.lastState = HIGH;       // Pull-up: idle = HIGH
  btn.lastPressMs = 0;
  pinMode(pin, INPUT);
}

// ======================== Debounced Press Detection ========================
bool checkButtonPress(ButtonState& btn) {
  bool current = digitalRead(btn.pin);
  bool pressed = false;

  // Detect falling edge (HIGH → LOW) with debounce
  if (current == LOW && btn.lastState == HIGH) {
    if (millis() - btn.lastPressMs > DEBOUNCE_MS) {
      btn.lastPressMs = millis();
      pressed = true;
    }
  }

  btn.lastState = current;
  return pressed;
}

// ======================== Button Action ========================
void handleButtonAction() {
  if (currentMode == MODE_POSITION) {
    // Exit position mode, return to previous
    motor.controller = MotionControlType::torque;
    currentMode = previousMode;
    Serial.println(F("Exited position mode"));
  } else {
    toggleMode();
  }
}

// ======================== Toggle Mode ========================
void toggleMode() {
  // Cycle: HAPTIC → INERTIA → SPRING → BOUNDED → HAPTIC
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
