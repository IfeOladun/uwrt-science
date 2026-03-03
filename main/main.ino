#include <Encoder.h>

/*
Motor
	Represents a single DC motor controlled by:
		- one PWM pin (speed control)
		- one direction pin
		- an optional quadrature encoder for position feedback
	The class supports rotating the motor by a specified 
	angle (in degrees)using encoder feedback.
*/

class Motor {
  private:
    int motorPwmPin;
    int motorDirPin;
    float encoderCPR;  // Encoder counts per full revolution of the motor shaft
    bool hasEncoder = false;
    Encoder* encoder = nullptr;  // Pointer to an Encoder object (null if no encoder is used)
    bool isStepper = false;
  public:
    /*
    init()
		Initializes the motor control pins and optionally sets up
		an encoder for position feedback.
		
		Parameters:
			pwmPin     - PWM pin connected to the motor driver
			dirPin     - Direction control pin
			setEncoder - Enable encoder support (default: false)
			encA       - Encoder channel A pin
			encB       - Encoder channel B pin
			cpr        - Encoder counts per revolution
      stepper    - Enable stepper motor support (default: false)
		
		If encoder parameters are invalid, the motor will operate
		without encoder feedback.
    */
    void init(int pwmPin, int dirPin, bool setEncoder = false, int encA = -1, int encB = -1, float cpr = -1.00, bool isStepper = false) {
        pinMode(dirPin, OUTPUT);
        pinMode(pwmPin, OUTPUT);
        if (setEncoder && encA > -1 && encB > -1 && cpr > -1) {
            encoder = new Encoder(encA, encB);
            encoderCPR = cpr;
            hasEncoder = setEncoder;
        }

        motorPwmPin = pwmPin;
        motorDirPin = dirPin;
    }

    void rotate(int dir, int speed) {
        digitalWrite(motorDirPin, dir ? HIGH : LOW);
        analogWrite(motorPwmPin, speed);
    }

    void stop() {
        digitalWrite(motorDirPin, 127);
        analogWrite(motorPwmPin, 0);
    }
    /*
    rotate_deg()
		Rotates the motor shaft by a specified angle (in degrees)
		using encoder feedback.
    
		Positive angle --> forward rotation
		Negative angle --> reverse rotation
		
		The motor runs at full PWM until the target encoder count
		is reached or a safety timeout occurs.
		
		Parameters:
    		angle - Desired rotation angle in degrees
    */
    void rotate_deg(float angle) {
        if (hasEncoder) {
            float targetCounts = (angle / 360) * encoderCPR;  // Convert desired angle to encoder counts
            (*encoder).write(0);

            if (angle >= 0) {  // Set motor direction based on sign of angle
                digitalWrite(motorDirPin, HIGH);
            } else {
                digitalWrite(motorDirPin, LOW);
            }

            targetCounts = abs(targetCounts);

            analogWrite(motorPwmPin, 127);

            while (abs((*encoder).read()) < targetCounts) {}  // Wait until desired encoder count is reached

            analogWrite(motorPwmPin, 0);  // Stop the motor
        }
    }
};

const int dir1 = 4;
const int pwm1 = 5;
const int dir2 = 7;
const int pwm2 = 6;
const int encA = 2;
const int encB = 3;

const float CPR = 341.2 * 4;  // counts per revolution of the motor; per motor basis check datasheet
String readFromSerial;

Motor motor1;
Motor motor2;

void setup() {
    Serial.begin(9600);
    motor1.init(pwm1, dir1);
    motor2.init(pwm2, dir2, true, encA, encB, CPR);
}

void loop() {
    // checking keyboard input
    if (Serial.available()) {
        String fromSerial = Serial.readString();
        fromSerial.trim();
        if (fromSerial.length() > 0) {
            if (fromSerial == "on") {
              motor1.rotate(0, 255);
              Serial.println("on");
            }
            else if (fromSerial == "off") {
              motor1.stop();
              Serial.println("off");
            }
            else if (fromSerial == "+") {
              motor2.rotate_deg(72);
              Serial.println("+");
            }
            else if (fromSerial == "-") {
              motor2.rotate_deg(-72);
              Serial.println("-");
            }
            fromSerial = "";
        }
    }

    // motor1.rotate(0, 255);
    // // motor2.rotate_deg(360);
    // delay(1000);
    // Serial.println("stopped");
    // motor1.stop();
    // delay(1000);
}