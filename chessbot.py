from serial import Serial
import numpy as np
import time

def connect_to_serial_port(ser):
    
    ser.close()
    ser = Serial('/dev/tty.usbmodem1411', 115200, xonxoff= True, timeout = None)

    for i in range(3):
        grbl_out = ser.readline() # Wait for grbl response with carriage return
        print grbl_out
    
    return ser

def move_absolute(ser, x, y, z, speed):
    
    # Generate G code and send it to the serial port
    g_code = 'G90 G01 X'+ str(x) + ' Y' + str(y) + ' Z' + str(z) + ' F' + str(speed)
    ser.write(g_code + '\r\n') # Send g-code block to grbl
    
    # Read 2 'OK' s from the serial port
    if not read_two_OKs(ser):
        return False
        
    # Poll to check if the move has been completed
    if not poll_until_idle(ser):
        return False

    return True

def move_relative(ser, x, y, z, speed):
    
    # Generate G code and send it to the serial port
    g_code = 'G91 G01 X'+ str(x) + ' Y' + str(y) + ' Z' + str(z) + ' F' + str(speed)
    ser.write(g_code + '\r\n') # Send g-code block to grbl
    
    # Read 2 'OK' s from the serial port
    if not read_two_OKs(ser):
        return False
        
    # Poll to check if the move has been completed
    if not poll_until_idle(ser):
        return False

    return True

def read_two_OKs(ser):
    
    for i in range(2):
        grbl_out = ser.readline().strip() # Wait for grbl response with carriage return
        
        if not ('ok' in grbl_out.lower()):
            print 'Could not read back 2 OKs after sending a G code line. Something is wrong.'
            return False
    
    return True
        
def poll_until_idle(ser):
    
    # Poll to check if the move has been completed
    while (True):
    
        ser.write('?\r\n')
        info_string = ser.readline() # Wait for grbl response with carriage return
        
        # Read 2 'OK' s from the serial port
        if not read_two_OKs(ser):
            return False
        
        split_info = info_string[1:-1].split(',')
        
        #print split_info[0]
        if 'Idle' in split_info[0]:
            #print 'Move completed.'
            return True
        
        time.sleep(0.1)
    
    return True
        
def go_home(ser):
    ser.write('$H\r\n')
    
    # Read 2 'OK' s from the serial port
    if not read_two_OKs(ser):
        return False

def get_current_work_position(ser):
    
    ser.write('?\r\n')
    info_string = ser.readline() # Wait for grbl response with carriage return
        
    # Read 2 'OK' s from the serial port
    if not read_two_OKs(ser):
        return False
        
    split_info = info_string[1:-1].split(',')
    
    x_val_temp = split_info[4]
    
    x = float(x_val_temp[5:])
    y = float(split_info[5])
    z = float(split_info[6])
    
    return x, y, z
    
def execute_move(move_str, ser):
    
    X_dict = {'1':128.17, '2':111.86, '3':95.55, '4':79.24, '5':62.93, '6':46.62, '7':30.31, '8':14.00}
    Y_dict = {'H':131.67, 'G':115.36, 'F':99.05, 'E':82.74, 'D':66.43, 'C':50.12, 'B':33.81, 'A':17.50}


    # Assuming no backlash
    y_start = Y_dict[move_str[0]]
    x_start = X_dict[move_str[1]]

    y_end   = Y_dict[move_str[2]]
    x_end   = X_dict[move_str[3]]
    
    # Fix backlash issue
    
    delta_y = 2.0*(y_end- y_start)/np.sqrt((y_end- y_start)*(y_end- y_start) + (x_end- x_start)*(x_end- x_start))
    delta_x = 2.0*(x_end- x_start)/np.sqrt((y_end- y_start)*(y_end- y_start) + (x_end- x_start)*(x_end- x_start))
   
    y_end = y_end + delta_y
    x_end = x_end + delta_x
    
    x_current, y_current, z_current = get_current_work_position(ser)
    
    if z_current<0:
        engage_delta = 15
    elif z_current>0:
        engage_delta = -15
    else :
        engage_delta = 0
    
    # Move to starting position
    move_absolute(ser, x_start, y_start+engage_delta, z_current, 1000)
    
    # Engage piece
    move_absolute(ser, x_start, y_start, 0, 1000)
    
    # Move to final position
    move_absolute(ser, x_end, y_end, 0, 1000)
    
    # Disengage piece
    if (y_end<75):
        move_relative(ser, 0,15,-1.5, 1000)
    else:
        move_relative(ser, 0,-15,1.5, 1000)
        
    print "Finished move ", move_str
    
    return 1
