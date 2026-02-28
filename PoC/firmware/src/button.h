/**
 * button.h — Multi-Button Input Handler
 *
 * Uses a ButtonState struct to track per-button state.
 * Currently one button (USER_BTN on PC13), but the struct-based
 * design makes adding more buttons trivial.
 *
 * Usage:
 *   ButtonState userBtn;
 *   initButton(userBtn, USER_BTN);          // in setup()
 *   if (checkButtonPress(userBtn)) { ... }  // in loop()
 */

#ifndef BUTTON_H
#define BUTTON_H

#include <Arduino.h>

// DEBOUNCE_MS is defined in config.h

// ======================== ButtonState Struct ========================
struct ButtonState {
  uint8_t       pin;            // GPIO pin number
  bool          lastState;      // Previous digitalRead value
  unsigned long lastPressMs;    // Timestamp of last accepted press
};

// ======================== Functions ========================

/**
 * Initialize a button: set pin as INPUT, initialize state.
 * @param btn  ButtonState struct to initialize
 * @param pin  GPIO pin (e.g., USER_BTN / PC13)
 */
void initButton(ButtonState& btn, uint8_t pin);

/**
 * Check if a button was just pressed (falling edge, debounced).
 * Call once per loop iteration. Returns true on a new press event.
 * @param btn  ButtonState struct to check and update
 * @return     true if a new debounced press was detected
 */
bool checkButtonPress(ButtonState& btn);

/**
 * Handle button press action: cycle modes or exit position mode.
 * Contains the mode-switching logic previously in loop().
 */
void handleButtonAction();

/**
 * Cycle through haptic modes: HAPTIC → INERTIA → SPRING → BOUNDED → HAPTIC
 */
void toggleMode();

// ======================== Global Button Instance ========================
extern ButtonState userBtn;

#endif // BUTTON_H
