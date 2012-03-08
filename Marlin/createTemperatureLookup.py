#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Thermistor Value Lookup Table Generator

Generates lookup to temperature values for use with the Marlin RepRap
firmware.

Usage: python createTemperatureLookup.py [options]

The quantities below refer to the following circuit,

     Vref ──────┐
                │
                R2
                │
                ├────────┬──── Vout
                │        │
               Rth       R1
                │        │
                │        │
               GND      GND

We assume the common thermistor parameterization of T₀, R₀ and beta where,

  R(T) = R₀ * exp(beta * (1/T - 1/T₀))
  
"""

from math import *

class Thermistor:
    "Class to do the thermistor maths"
    def __init__(self, r0, t0, beta, r1, r2):
        self.r0 = r0                        # stated resistance, e.g. 10K
        self.t0 = t0 + 273.15               # temperature at stated resistance, e.g. 25C
        self.beta = beta                    # stated beta, e.g. 3500
        self.vadc = 5.0                     # ADC reference
        self.vcc = 5.0                      # supply voltage to potential divider
        self.k = r0 * exp(-beta / self.t0)   # constant part of calculation

        if r1 > 0:
            self.vs = r1 * self.vcc / (r1 + r2) # effective bias voltage
            self.rs = r1 * r2 / (r1 + r2)       # effective bias impedance
        else:
            self.vs = self.vcc                   # effective bias voltage
            self.rs = r2                         # effective bias impedance

    def temp(self,adc):
        "Convert ADC reading into a temperature in Celcius"
        v = adc * self.vadc / 1024          # convert the 10 bit ADC value to a voltage
        r = self.rs * v / (self.vs - v)     # resistance of thermistor
        return (self.beta / log(r / self.k)) - 273.15        # temperature

    def setting(self, t):
        "Convert a temperature into a ADC value"
        r = self.r0 * exp(self.beta * (1 / (t + 273.15) - 1 / self.t0)) # resistance of the thermistor
        v = self.vs * r / (self.rs + r)     # the voltage at the potential divider
        return round(v / self.vadc * 1024)  # the ADC reading

def main():
    import sys
    from argparse import ArgumentParser
    import argparse
    parser = ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                            description=__doc__)
    parser.add_argument('--r0', type=float, required=True,
                        help='Resistance of thermistor at T0 in ohms')
    parser.add_argument('--t0', type=float, default=25,
                        help='T0 parameter of thermistor in Celcius')
    parser.add_argument('--beta', type=float, required=True,
                        help='Beta parameter of thermistor')
    parser.add_argument('--r1', type=float, default=None,
                        help='Value of the optional low-side resistor in ohms')
    parser.add_argument('--r2', type=float, required=True,
                        help='Value of the high-side resistor in ohms')
    parser.add_argument('--num-temps', '-n', type=int, default=20,
                        help='Number of temperature points to generate')
    parser.add_argument('--max-adc', type=int, default=1023,
                        help='Maximum ADC value if R1 is used')
    parser.add_argument('--name', type=str,
                        help='Produce output as array with given name')
    args = parser.parse_args()
    
    max_adc = args.max_adc
    if args.r1 is not None:
        max_adc = int(1023 * r1 / (r1 + r2));
        
    t = Thermistor(args.r0, args.t0, args.beta, args.r1, args.r2)

    increment = int(max_adc/(args.num_temps-1));
    adcs = range(1, max_adc, increment);

    print "// Thermistor lookup table for RepRap Temperature Sensor Boards (http://make.rrrf.org/ts)"
    print "// Made with createTemperatureLookup.py (http://svn.reprap.org/trunk/reprap/firmware/Arduino/utilities/createTemperatureLookup.py)"
    print "// ", sys.argv
    
    if args.name is not None:
        print "const short %s[][2] PROGMEM = {" % args.name

    for n,adc in enumerate(adcs):
        print "   {%4d*OVERSAMPLENR, %4d}%s" % (adc, int(t.temp(adc)), '' if n==len(adcs) else ',')
            
    if args.name is not None:
        print "};"
    
def usage():
    print __doc__

if __name__ == "__main__":
    main()
