#include <Encoder.h>
#include <PID_v1.h>

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
    /*
    rotate()
      Sets the motor direction and speed.

      Parameters:
        dir   - Motor rotation direction.
          0 = reverse direction
          1 = forward direction

        speed - PWM speed value applied to the motor driver.
          Range: 0–255
          0   = motor stopped
          255 = maximum speed

      The function updates the motor driver's direction pin and
      outputs a PWM signal to control the motor speed.
    */
    void rotate(int dir, int speed) {
        digitalWrite(motorDirPin, dir ? HIGH : LOW);
        analogWrite(motorPwmPin, speed);
    }

    void stop() {
        digitalWrite(motorDirPin, 127);
        analogWrite(motorPwmPin, 0);
    }

    void starting_position() {
        if (hasEncoder) {
            long first = millis();
            long last = millis();

            float lastCount = (*encoder).read();
            rotate(1, 127);
            while (true) {
                if (millis() - last > 100) {
                    float currentCount = (*encoder).read();
                    if (abs(currentCount - lastCount) < 5) {
                        break;
                    } else if (millis() - first > 500) {
                        break;
                    }
                    last = millis();
                    lastCount = currentCount;
                }
            }
            stop();
            delay(250);
            (*encoder).write(0);
        }
    }

    void rotate_deg_pid(float angle) {
        if (hasEncoder) {
            double input;  // current angle
            double output;
            double setpoint = angle;  // target angle
            double kp = 1;
            double ki = 1.5;
            double kd = .1;

            PID pid(&input, &output, &setpoint, kp, ki, kd, DIRECT);
            pid.SetMode(AUTOMATIC);
            pid.SetOutputLimits(-255, 255);  // allows reverse
            long last = millis();
            while (true) {
                if (millis() - last >= 100) {
                    float encoderCounts = (*encoder).read();
                    input = (encoderCounts / encoderCPR) * 360;

                    pid.Compute();
                    Serial.println(output);
                    rotate(output > 0 ? 0 : 1, abs((int)output));
                    if (abs(input - setpoint) < 1.0) {
                        break;
                    }
                    last = millis();
                }
            }
            stop();
        }
    }
    void rotate_deg(float angle) {
        if (hasEncoder) {
            float target = angle;
            const int slowDownAngle = 50;
            const int maxSpeed = 40;
            const int minSpeed = 20;
            while (true) {
                float encoderCounts = (*encoder).read();
                float input = (encoderCounts / encoderCPR) * 360.0;

                float error = target - input;

                if (abs(error) < 5) {
                    break;
                }

                if (target == 0) {
                    starting_position();
                    return;
                }

                float dist = abs(error);
                int speed;
                if (dist > slowDownAngle) {
                    speed = maxSpeed;
                } else {
                    float ratio = dist / slowDownAngle;
                    speed = minSpeed + ratio * (maxSpeed - minSpeed);
                }
                rotate(error > 0 ? 0 : 1, speed);
            }
            stop();
        }
    }
    int get_degrees() {
        if (hasEncoder) {
            float counts = (*encoder).read();
            float angle = (counts / encoderCPR) * 360;
            return angle;
        }
    }
    float get_counts() {
        if (hasEncoder) {
            return (*encoder).read();
        }
    }
};


class Stepper_Motors {
  private:
    int stp_pin1;
    int dir_pin1;
    int stp_pin2;
    int dir_pin2;
  public:
    void init(int step_pin1, int direction_pin1, int step_pin2, int direction_pin2) {
        stp_pin1 = step_pin1;
        dir_pin1 = direction_pin1;
        stp_pin2 = step_pin2;
        dir_pin2 = direction_pin2;
        pinMode(stp_pin1, OUTPUT);
        pinMode(dir_pin1, OUTPUT);
        pinMode(stp_pin2, OUTPUT);
        pinMode(dir_pin2, OUTPUT);
    }

    void move_mm(int mils, int dir) {
        digitalWrite(dir_pin1, dir > 0 ? LOW : HIGH);  // 0/high is down, 1/low is up
        digitalWrite(dir_pin2, dir > 0 ? LOW : HIGH);
        for (int i = 0; i < mils * 50; i++) {  // ~ 1mm / 50 pulses
            digitalWrite(stp_pin1, HIGH);
            digitalWrite(stp_pin2, HIGH);
            delayMicroseconds(1000);
            digitalWrite(stp_pin1, LOW);
            digitalWrite(stp_pin2, LOW);
            delayMicroseconds(1000);
        }
    }
};

const int dir1 = 4;
const int pwm1 = 5;
const int dir2 = 7;
const int pwm2 = 6;
const int encA = 2;
const int encB = 3;
const int step1 = 8;
const int step_dir1 = 9;
const int step2 = 10;
const int step_dir2 = 11;

const float CPR = 341.2 * 4;  // counts per revolution of the motor; per motor basis check datasheet (341.2)

Motor motor1;
Motor motor2;
Stepper_Motors steppers;

void setup() {
    Serial.begin(9600);
    motor1.init(pwm1, dir1);
    motor2.init(pwm2, dir2, true, encA, encB, CPR);
    steppers.init(step1, step_dir1, step2, step_dir2);
}

void loop() {
    // checking keyboard input
    if (Serial.available()) {
        String fromSerial = Serial.readString();
        fromSerial.trim();
        Serial.println(fromSerial);
        if (fromSerial.length() > 0) {
            if (fromSerial == "on") {
                motor1.rotate(0, 127);
            } else if (fromSerial == "off") {
                motor1.stop();
            } else if (fromSerial == "reverse") {
                motor1.rotate(1, 255);
            } else if (fromSerial == "up") {
                steppers.move_mm(50, 1);
            } else if (fromSerial == "down") {
                steppers.move_mm(50, 0);
            } else if (fromSerial == "0") {
                motor2.rotate_deg(0);
            } else if (fromSerial == "1") {
                motor2.rotate_deg(72);
            } else if (fromSerial == "2") {
                motor2.rotate_deg(144);
            } else if (fromSerial == "3") {
                motor2.rotate_deg(216);
            } else if (fromSerial == "4") {
                motor2.rotate_deg(288);
            } else if (fromSerial == "reset") {
                motor2.starting_position();
            } else if (fromSerial == "p") {
                Serial.println(motor2.get_degrees());
            } else if (fromSerial == "c") {
                Serial.println(motor2.get_counts());
            }
            fromSerial = "";
        }
    }
}