/**
 * comms.h — Serial Communication & Commander
 *
 * Declares all serial command handlers (doXxx), position reporting,
 * and the Commander setup function.
 *
 * Protocol: ASCII text at 115200 baud, '\n'-terminated
 *   PC → STM32: Single-letter commands with optional value
 *   STM32 → PC: "A:<cmd>" acknowledgements, "P<angle>" position updates
 */

#ifndef COMMS_H
#define COMMS_H

// ======================== Mode Command Handlers ========================
void doHaptic(char* cmd);
void doInertia(char* cmd);
void doSpring(char* cmd);
void doBounded(char* cmd);

// ======================== Parameter Command Handlers ========================
void doDetentCount(char* cmd);
void doDetentStrength(char* cmd);
void doDamping(char* cmd);
void doFriction(char* cmd);
void doInertiaVal(char* cmd);
void doCoupling(char* cmd);
void doSpringStiffness(char* cmd);
void doSpringCenter(char* cmd);
void doSpringDamping(char* cmd);
void doLowerBound(char* cmd);
void doUpperBound(char* cmd);
void doWallStrength(char* cmd);

// ======================== Query/Action Handlers ========================
void doQueryPosition(char* cmd);
void doSeekPosition(char* cmd);
void doQueryState(char* cmd);
void doMotor(char* cmd);

// ======================== Position Reporting ========================
void reportPosition();

// ======================== Commander Setup ========================
/**
 * Register all commands with the Commander instance.
 * Call once from setup() after Commander is initialized.
 */
void setupCommander();

/**
 * Print the startup banner with available commands.
 */
void printBanner();

#endif // COMMS_H
