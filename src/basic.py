#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple PoC to confirm the details of the datasheet; configure the probe and poll it.
Comments below indicate where the datasheet and observations differ.
"""


import minimalmodbus
import structlog

log = structlog.get_logger(__name__)

# Change as needed
PORT = "/dev/ttyUSB0"

# Defaults from the datasheet
BAUDRATE = 9600
SENSOR_ADDR = 0x01
# Most of this comes from page 2/3 of the datasheet
##
# This is the actual address of the device
# So odd that first address isn't the actual value but whatever...
DEV_ADDR_REGISTER = 0x00

# What speed is the device running at?
DEV_BAUD_RATE_REGISTER = 0x01
# 0: 1200 baud
# 1: 2400 baud
# 2: 4800 baud
# 3: 9600 baud
# 4: 19200 baud
# 5: 38400 baud
# 6: 57600 baud
# 7: 115200 baud

# What unit does the measurement come in?
DEV_MEASUREMENT_UNIT_REGISTER = 0x02
# 0: unit not shown
# 1: cmH2O
# 2: mmH20
# 3: MPa
# for Pascal/KiloPascal: also displays the temp in C in top right corner
# 4: Pa
# 5: Kpa
# Datasheet SAYS `ma` but I think they mean Mpa
# In any case, writing value 6 here clears the display just as if I had written 0.
# This might be a limitation of my device since it's only rated for 0-10 Kpa
# 6: ma

# Number of decimal places in the measurement
DEV_PRESSURE_VALUE_PRECISION_REGISTER = 0x03
# 0: 0 decimal places (NNNN)
# 1: 1 decimal places (NNN.N)
# 2: 2 decimal places (NN.NN)
# 3: 3 decimal places (N.NNN)

# The actual pressure value that the sensor is reading
DEV_PRESSURE_VALUE_REGISTER = 0x04
# will be between -32768 and 32767 (16 bits)

# The datasheet isn't clear on what these registers are for.
# Reading between the lines a bit, these are used to calibrate the sensor for custom offsets?
# It could also be this is how the sensor pressure range is set?
##
# This is the "zero" value of the sensor?!
DEV_PRESSURE_ZERO_VALUE_REGISTER = 0x05
# will be between -32768 and 32767 (16 bits)

# Transmitter range is full point?!?
DEV_PRESSURE_FULL_VALUE_REGISTER = 0x06
# will be between -32768 and 32767 (16 bits)


def main():
    """Configure and then poll the sensor."""
    log.error("Starting basic.py")
    # Debug = True to get the raw bytes; makes it easier to match up to datasheet for verification
    instrument = minimalmodbus.Instrument(PORT, SENSOR_ADDR, debug=True)

    if instrument.serial is None:
        log.error("Serial is None")
        return

    instrument.serial.baudrate = BAUDRATE
    instrument.serial.timeout = 1

    instrument.clear_buffers_before_each_transaction = True

    # Should be 1
    address = instrument.read_register(DEV_ADDR_REGISTER)
    log.info("Readings:", address=address)

    # Should be 3 -> 9600 baud
    speed = instrument.read_register(DEV_BAUD_RATE_REGISTER)
    log.info("Readings:", speed=speed)

    # Should be 1 meaning 1 decimal place

    value = instrument.read_register(
        DEV_PRESSURE_VALUE_REGISTER, number_of_decimals=1, signed=True
    )
    log.info("Readings:", value=value)

    #
    zero = instrument.read_register(DEV_PRESSURE_ZERO_VALUE_REGISTER)
    log.info("Readings:", zero=zero)

    full = instrument.read_register(DEV_PRESSURE_FULL_VALUE_REGISTER)
    log.info("Readings:", full=full)

    unit = instrument.read_register(DEV_MEASUREMENT_UNIT_REGISTER)
    log.info("Readings:", unit=unit)

    # We want to measure in pascals
    instrument.write_register(DEV_MEASUREMENT_UNIT_REGISTER, value=4)

    # With 2 decimal places of precision (default is 1)
    instrument.write_register(DEV_PRESSURE_VALUE_PRECISION_REGISTER, value=2)

    unit = instrument.read_register(DEV_MEASUREMENT_UNIT_REGISTER)
    precision = instrument.read_register(DEV_PRESSURE_VALUE_PRECISION_REGISTER)
    value = instrument.read_register(
        DEV_PRESSURE_VALUE_REGISTER, number_of_decimals=2, signed=True
    )
    log.info("Measure:", value=value, unit=unit, precision=precision)


if __name__ == "__main__":
    main()
