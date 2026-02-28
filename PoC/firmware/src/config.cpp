/**
 * config.cpp — Parameter Default Values
 *
 * Defines all runtime-adjustable parameters declared extern in config.h.
 * This is the single place to change default values.
 *
 * Hardware objects (motor, driver, sensor, etc.) are defined in main.cpp
 * because they require constructor arguments tied to pin definitions.
 */

#include "config.h"

// ======================== Mode State ========================
HapticMode currentMode  = MODE_HAPTIC;
HapticMode previousMode = MODE_HAPTIC;

// ======================== Haptic Mode Defaults ========================
int   detent_count    = 36;      // detents per 360°
float detent_strength = 1.5f;    // snap strength (V)

// ======================== Inertia Mode Defaults ========================
float virtual_inertia  = 5.0f;   // mass feel
float inertia_damping  = 1.0f;   // drag
float inertia_friction = 0.2f;   // static friction
float coupling_K       = 40.0f;  // spring stiffness

// ======================== Spring Mode Defaults ========================
float spring_center    = 0.0f;   // center position (rad)
float spring_stiffness = 10.0f;  // spring constant (V/rad)
float spring_damping   = 0.1f;   // velocity damping

// ======================== Bounded Mode Defaults ========================
float bound_min     = -60.0f * _PI / 180.0f;  // lower bound (rad) = -60°
float bound_max     = +60.0f * _PI / 180.0f;  // upper bound (rad) = +60°
float wall_strength = 20.0f;                   // wall spring constant (V/rad)
float wall_damping  = 2.0f;                    // wall damping (V·s/rad)

// ======================== Position Reporting ========================
float last_reported_angle  = 0.0f;
unsigned long last_report_us = 0;
float report_interval_ms   = DEFAULT_REPORT_INTERVAL_MS;
float report_threshold_deg = DEFAULT_REPORT_THRESHOLD_DEG;

// ======================== Position Seek ========================
float seek_tolerance_rad      = 0.06f;   // ~3.4° — relaxed for reliable completion
unsigned long seek_settle_start = 0;
unsigned long seek_start_time   = 0;
