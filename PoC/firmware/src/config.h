/**
 * config.h — SmartKnob Hardware & Parameter Configuration
 *
 * Single source of truth for:
 *   - Pin definitions
 *   - Hardware object externs
 *   - Mode enum
 *   - Compile-time constants (organized by module)
 *   - Runtime parameter externs (defaults in config.cpp)
 *
 * All mutable parameter variables are declared extern here
 * and defined with their default values in config.cpp.
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <SimpleFOC.h>
#include "SimpleFOCDrivers.h"
#include "encoders/MT6701/MagneticSensorMT6701SSI.h"

// ======================== Pin Definitions ========================
#define SENSOR_CS PB6
#define USER_BTN  PC13
#define PWM_A     PB10
#define PWM_B     PC7
#define PWM_C     PB4
#define DRIVER_EN PA9
#define CURRENT_A PA0
#define CURRENT_B PA4

// ======================== Hardware Constants ========================
const int    MOTOR_POLE_PAIRS       = 7;
const float  SUPPLY_VOLTAGE         = 12.0f;
const float  CURRENT_SENSE_GAIN     = 185.0f;   // mV/A (ACS712-05B)
const float  VOLTAGE_LIMIT          = 8.0f;      // Max motor voltage (V)
const float  VOLTAGE_SENSOR_ALIGN   = 5.0f;      // Alignment voltage (V)
const float  VELOCITY_LPF_TF        = 0.03f;     // Velocity low-pass filter time constant
const float  POS_PID_P              = 50.0f;     // Position PID defaults
const float  POS_PID_I              = 0.0f;
const float  POS_PID_D              = 0.3f;
const float  DEFAULT_VELOCITY_LIMIT  = 40.0f;     // rad/s max during seek

// ======================== Hardware Objects (extern) ========================
extern MagneticSensorMT6701SSI sensor;
extern BLDCMotor motor;
extern BLDCDriver3PWM driver;
extern InlineCurrentSense current_sense;
extern Commander command;

// ======================== Mode Enum ========================
enum HapticMode {
  MODE_HAPTIC,
  MODE_INERTIA,
  MODE_SPRING,
  MODE_BOUNDED,
  MODE_POSITION
};

extern HapticMode currentMode;
extern HapticMode previousMode;

// ============================================================
//  COMPILE-TIME CONSTANTS (organized by module)
// ============================================================

// --- Button ---
const unsigned long DEBOUNCE_MS = 200;  // Min ms between accepted presses

// --- Position Seek ---
const unsigned long SEEK_SETTLE_MS  = 200;    // Hold at target before returning
const unsigned long SEEK_TIMEOUT_MS = 10000;  // 10 second timeout

// --- Reporting defaults ---
const float DEFAULT_REPORT_INTERVAL_MS  = 20.0f;   // Position report throttle
const float DEFAULT_REPORT_THRESHOLD_DEG = 0.5f;   // Min change to report
const float INERTIA_REPORT_INTERVAL_MS  = 10.0f;   // Faster reporting for inertia mode

// ============================================================
//  RUNTIME PARAMETERS (extern — defaults in config.cpp)
// ============================================================

// --- Haptic mode (detents) ---
extern int   detent_count;       // Default: 36 (detents per 360°)
extern float detent_strength;    // Default: 1.5 V (snap strength)

// --- Inertia mode (virtual flywheel) ---
extern float virtual_inertia;    // Default: 5.0 (mass feel)
extern float inertia_damping;    // Default: 1.0 (drag)
extern float inertia_friction;   // Default: 0.2 (static friction)
extern float coupling_K;         // Default: 40.0 (spring stiffness)

// --- Spring mode (centered return) ---
extern float spring_center;      // Default: 0.0 rad (center position)
extern float spring_stiffness;   // Default: 10.0 V/rad (spring constant)
extern float spring_damping;     // Default: 0.1 (velocity damping)

// --- Bounded mode (detents with walls) ---
extern float bound_min;          // Default: -60° (lower bound, rad)
extern float bound_max;          // Default: +60° (upper bound, rad)
extern float wall_strength;      // Default: 20.0 V/rad
extern float wall_damping;       // Default: 2.0 V·s/rad

// --- Position Reporting (runtime-adjustable) ---
extern float last_reported_angle;
extern unsigned long last_report_us;
extern float report_interval_ms;
extern float report_threshold_deg;

// --- Position Seek (runtime state) ---
extern float seek_tolerance_rad;
extern unsigned long seek_settle_start;
extern unsigned long seek_start_time;

// ======================== Helper Functions ========================

/**
 * Get current motor angle in degrees.
 * Uses motor.shaft_angle for consistency with SimpleFOC's internal state.
 */
inline float getCurrentAngleDeg() {
  return motor.shaft_angle * 180.0f / _PI;
}

#endif // CONFIG_H
