//For the Pressure Sensing


#include "MAX6675.h"
#include "HX710.h"


const int Tslc = 5;//temperature select pin
const int Tclk = 6;//temperature clock pin
const int Tdat = 7;//temperature data pin




MAX6675 thermoCouple(Tslc, Tdat, Tclk);


uint32_t start, stop;
float temp = 0;
//Pressure
const int Pdat = 4;
const int Pclk = 3;
HX710 ps;


// int heat = 9;//output for the heater relay


// int prson = 10;//input for the vacuum to work
// int vacc = 0;//variable for the vacuum
// int motor = 11;//output for the motor to turn on (L298N)
// int motorspeed = A0;//the motor speed is controlled by PWM signals in (L298N)
// int solenoid = 12;//output for the solenoid to turn on (L298N)


// int data;
void setup()
{


  
  Serial.begin(115200);
  // Temperature


  SPI.begin();


  thermoCouple.begin();
  thermoCouple.setSPIspeed(4000000);
  thermoCouple.setOffset(1);
  int status = thermoCouple.read();
  if (status != 0) Serial.println(status);
  temp = thermoCouple.getTemperature();


  //Pressure
   ps.initialize( Pclk , Pdat );
}




void loop()
{
  pinMode(8, OUTPUT);
  pinMode(2, OUTPUT);
  pinMode(9, OUTPUT);
  analogWrite(9, 128);//Motor
  analogWrite(11, 100);//Solenoid
  //Pressure
    int32_t v1, v2, v3;
   
    while( !ps.isReady() );
    ps.readAndSelectNextData( HX710_OTHER_INPUT_40HZ );
    v1 = ps.getLastDifferentialInput();
   
    while( !ps.isReady() );
    ps.readAndSelectNextData( HX710_DIFFERENTIAL_INPUT_40HZ );
    v2 = ps.getLastOtherInput();
   
    while( !ps.isReady() );
    ps.readAndSelectNextData( HX710_DIFFERENTIAL_INPUT_10HZ );
    v3 = ps.getLastDifferentialInput();
   
//Temperature print
  start = micros();
  int status = thermoCouple.read();
  stop = micros();
  float newValue = thermoCouple.getTemperature();
  //  0.2 is low pass filter
  temp += 0.2 * (newValue - temp);
  //  temp = newValue;


  Serial.print("Temp: ");
  Serial.print(temp-3);
 
  Serial.print( "\t Pressure: ");


//Pressure print
  Serial.print(v1/96000);
  //  Serial.print(stop - start);
  Serial.println();


  delay(200);


//Control Motor
if(analogRead(A4)>128){
  digitalWrite(8, HIGH);//Turn the motor and solenoid both on
  Serial.println("Vacuum ON\t");
}


if(analogRead(A4)<128){
  digitalWrite(8, LOW);//Turn the motor and solenoid both off
  Serial.println("Vacuum OFF\t");
}


//Control heater
if(temp<190){
    digitalWrite(2, HIGH);//Turn the heater on
    Serial.println("Heater ON");
  }
  else{
    digitalWrite(2, LOW);//Turn the heater off
    Serial.println("Heater OFF");
  }


}
