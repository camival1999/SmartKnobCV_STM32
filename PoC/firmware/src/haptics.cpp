/**
 * haptics.cpp — Haptic Torque Computation
 *
 * Implements four torque models:
 *   Haptic  — Sine-based virtual detents (infinite rotation)
 *   Inertia — Virtual flywheel coupled to motor via spring
 *   Spring  — Hooke's law with velocity damping
 *   Bounded — Detents distributed within walled range
 */

#include "haptics.h"
#include "config.h"

// ======================== Inertia State ========================
float virt_pos = 0.0f;
float virt_vel = 0.0f;
unsigned long prev_time_us = 0;

// ======================== Reset Inertia ========================
void resetInertiaState() {
  virt_pos = motor.shaft_angle;
  virt_vel = 0.0f;
  prev_time_us = micros();
}

// ======================== Haptic Torque ========================
float computeHapticTorque() {
  float angle_rad = motor.shaft_angle;
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
  float displacement = motor.shaft_angle - spring_center;

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
  if (pos < bound_min - buffer_rad) {
    float overflow = (bound_min + buffer_rad * 5) - pos;
    torque = wall_strength * overflow - wall_damping * vel;
  } else if (pos > bound_max + buffer_rad) {
    float overflow = pos - (bound_max - buffer_rad * 5);
    torque = -wall_strength * overflow - wall_damping * vel;
  } else {
    // Within bounds - apply detent haptics
    float range = bound_max - bound_min;
    float normalized = (pos - bound_min) / range;  // 0 to 1 within bounds
    float phase = normalized * (float)(detent_count - 1) * 2.0f * _PI;
    torque = detent_strength * -sin(phase);
  }

  return torque;
}
