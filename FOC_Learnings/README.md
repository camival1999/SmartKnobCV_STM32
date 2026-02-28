# FOC Learnings

Structured learning resources for STM32, SimpleFOC, and Field-Oriented Control theory.

## Overview

This branch contains the educational side of the SmartKnob project — a structured learning path progressing from zero STM32 experience to advanced FOC motor control and haptic feedback.

## Contents

| File | Purpose |
|------|---------|
| [stm32_smart_knob_learning_path.md](stm32_smart_knob_learning_path.md) | Complete learning path: phases, milestones, theory, and resources |
| [firmware_iterations/](firmware_iterations/) | Historical firmware versions from each development milestone |

## Firmware Iterations

Backup snapshots of `main.cpp` at key development milestones:

| File | Milestone |
|------|-----------|
| `main_firstSSIWorking.bak` | First successful MT6701 SSI sensor readout |
| `main_AngleControl.bak` | Angle position control with PID |
| `main_FullControl.bak` | Full SimpleFOC control with Commander interface |
| `main_backup_complex.bak` | Complex multi-feature development snapshot |

## Learning Path Structure

The learning path is organized into phases:

| Phase | Topic | Status |
|-------|-------|--------|
| **Phase 1** | PlatformIO + STM32Duino environment | Completed |
| **Phase 2** | SimpleFOC open-loop (no encoder) | Completed |
| **Phase 3** | Closed-loop with MT6701 encoder | Completed |
| **Phase 4+** | Advanced: current control, sensorless, HFI | Planned |
