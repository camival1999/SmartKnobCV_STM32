/**
 * haptics.h — Haptic Torque Computation
 *
 * Declares the four torque computation functions:
 *   computeHapticTorque()  — Sine-based virtual detents
 *   computeInertiaTorque() — Virtual flywheel with coupling spring
 *   computeSpringTorque()  — Hooke's law centered return
 *   computeBoundedTorque() — Detents within walled range
 *
 * Inertia state variables (virt_pos, virt_vel, prev_time_us) live here
 * because they are only used by computeInertiaTorque().
 */

#ifndef HAPTICS_H
#define HAPTICS_H

// ======================== Inertia State ========================
// These are internal to haptics but need extern for resetInertiaState()
extern float virt_pos;
extern float virt_vel;
extern unsigned long prev_time_us;

// ======================== Torque Functions ========================
float computeHapticTorque();
float computeInertiaTorque();
float computeSpringTorque();
float computeBoundedTorque();

/**
 * Reset inertia virtual flywheel state to current motor position.
 * Call when entering inertia mode or returning to it from position seek.
 */
void resetInertiaState();

#endif // HAPTICS_H
