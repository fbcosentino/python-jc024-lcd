"""
Library to deal with JC024_V02 SunStudio LCD and similar, from Python (via serial port).

:Author: Fernando Cosentino
    https://github.com/fbcosentino/python-jc024-lcd
"""

import serial
import time



class SunLCD:
    """This class represents one LCD object. Create one instance per display."""

    #Vertical orientation
    VERTICAL = 0
    #Horizontal orientation
    HORIZONTAL = 1
    
    COLOR_BLACK = 0
    COLOR_RED = 1
    COLOR_GREEN = 2
    COLOR_BLUE = 3
    COLOR_YELLOW = 4
    COLOR_CYAN = 5
    COLOR_MAGENTA = 6
    COLOR_GRAY = 7
    COLOR_LIGHT_GRAY = 8
    COLOR_BROWN = 9
    COLOR_DARK_GREEN = 10
    COLOR_DARK_BLUE = 11
    COLOR_DARK_YELLOW = 12
    COLOR_ORANGE = 13
    COLOR_LIGHT_RED = 14
    COLOR_WHITE = 15

    def __init__(self, port = '/dev/ttyUSB0', width=240, height=320):
        """Creates one instance for one display.
        
        :param port: Serial port (default '/dev/ttyUSB0')
        """
        self.ser = serial.Serial(port, 115200, timeout=1)
        self.ok = False
        self.response_body = ""
        self._buf = ""
        self.cursor = [0,0]
        self.img_list = []
        self.img_offset = 2097152 
        self.font_list = []
        
        # these are used to calculate font line wrap
        self.current_orientation = self.VERTICAL
        self.standard_width = width
        self.standard_height = height

        self.ser.write("\r\n") # flush in case some garbage was already sent
        if self.Reset():
            self.Background(self.COLOR_BLACK)
        


    # ========================================================================
    # SERIAL PROCESSING METHODS
    # ========================================================================
            
    def ReadBack(self):
        """
        Called internally. Reads the response from the LCD and acts accordingly.
        
        :returns: True if response received, None otherwise.
        """
        responses = []
        while self.ser.inWaiting() > 0:
            c = self.ser.read(1)
            if (ord(c) == 10):
                responses.append(self._buf.strip())
                self._buf = ""
            else:
                self._buf += c
                
        if len(responses) == 0:
            return None
            
        for response in responses:
            if response == 'OK':
                self.ok = True
            self.response_body = response
                
        return True
        
    def send_serial(self, cmd):
        """
        Sends a command over the serial port, and waits for any answer.
        
        :param cmd: The command to be sent, without newlines.
        :returns: True on response, False on timeout.
        """
        self.ok = False
        self.response_body = ""
        self.ser.write(cmd+"\r\n")
        i = 10
        while i > 0:
            time.sleep(0.1)
            i -= 1
            res = self.ReadBack()
            if res is not None:
                return True
        return False
        
        
        
    # ========================================================================
    # INTERNAL LCD METHODS
    # ========================================================================
    
    
    def Reset(self):
        """Resets the LCD.
        
        :returns: True on success, False otherwise."""
        res = self.send_serial("RESET")
        return res
        
    def Version(self):
        """Prints version info on the display."""
        res = self.send_serial("VER")
        return res
        
    def Baudrate(self, baudrate):
        """Changes the baudrate. BE CAREFUL: THIS IS PERMANENT IN FLASH!
        
        :param baudrate: The new baudrate. Both the display and this object will be modified.
        :returns: True on success, False otherwise. But always fails...
        """
        res = self.send_serial("BPS("+str(baudrate)+")")
        self.ser.close()
        self.ser.baudrate = baudrate
        self.ser.open()
        return res
        
    def Clear(self, color = 0):
        """
        Clears the screen to a specified color.
        
        :param color: Screen color (default black).
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("CLR("+str(color)+")")
        return res
    
        
    def On(self, on_off):
        """Turns the LCD ON and OFF.
        
        :param on: If False or 0, will turn LCD OFF. Anything else will turn ON.
        :returns: True on success, False otherwise.
        """
        if (on_off is False) or (on_off == 0):
            res = self.send_serial("LCDON(0)")
        else:
            res = self.send_serial("LCDON(1)")
        return res
        
    def RawImage(self, address, position, size, transparent = 0):
        """
        Displays an image from the internal memory.
        
        :param address: Address from memory (starts at 2097152)
        :param position: A tuple (X,Y)
        :param size: A tuple (W,H)
        :param transparent: 0 - not transparent. 1 - transparent (transparent color is white)
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("FSIMG("+str(address)+","+str(position[0])+","+str(position[1])+","+str(size[0])+","+str(size[1])+","+str(transparent)+")")
        return res
    
    
    
    
    # TODO: FS_DLOAD
    
    def Orientation(self, orientation):
        """Sets the orientation. 1 means horizontal, 0 means vertical.
        You can also use instance.HORIZONTAL and instance.VERTICAL.
        
        :param orientation: 1 is horizontal, 0 is vertical. 
        :returns: True on success, False otherwise.
        """
        if (orientation == 0):
            self.current_orientation = orientation
            res = self.send_serial("DIR(0)")
        elif (orientation == 1):
            self.current_orientation = orientation
            res = self.send_serial("DIR(1)")
        else:
            res = False
        return res
    
    
    def Brightness(self, level):
        """Sets the backlight brightness.
        
        :param level: Intensity in the range 0.0 - 1.0
        :returns: True on success, False otherwise.
        """
        try:
            bl_val = int( (1.0 - float(level))*255 ) 
        except:
            return False
        if bl_val < 0:
            bl_val = 0
        if bl_val > 255:
            bl_val = 255
        res = self.send_serial("BL("+str(bl_val)+")")
        return res
    
    def Point(self, location, color = 15):
        """
        Prints a point (pixel).
        
        :param location: A touple (X,Y)
        :param color: Point color (default white).
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("PS("+str(location[0])+","+str(location[1])+","+str(color)+")")
        return res

    def Line(self, origin, destination, color = 15):
        """
        Prints a line.
        
        :param origin: A touple (X,Y)
        :param destination: A touple (X,Y)
        :param color: Point color (default white).
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("PL("+ str(origin[0])+","+str(origin[1]) + "," + str(destination[0])+","+str(destination[1]) + ","+str(color)+")")
        return res
    
    def HollowBox(self, top_left, bottom_right, color = 15):
        """
        Prints a hollow box.
        
        :param top_left: A touple (X,Y)
        :param bottom_right: A touple (X,Y)
        :param color: Point color (default white).
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("BOX("+ str(top_left[0])+","+str(top_left[1]) + "," + str(bottom_right[0])+","+str(bottom_right[1]) + ","+str(color)+")")
        return res
    
    def FilledBox(self, top_left, bottom_right, color = 15):
        """
        Prints a filled box.
        
        :param top_left: A touple (X,Y)
        :param bottom_right: A touple (X,Y)
        :param color: Point color (default white).
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("BOXF("+ str(top_left[0])+","+str(top_left[1]) + "," + str(bottom_right[0])+","+str(bottom_right[1]) + ","+str(color)+")")
        return res
    
    def HollowCircle(self, center, radius, color = 15):
        """
        Prints a hollow circle.
        
        :param center: A touple (X,Y)
        :param radius: The radius
        :param color: Point color (default white).
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("CIR("+ str(center[0])+","+str(center[1]) + "," + str(radius) + ","+str(color)+")")
        return res
    
    def FilledCircle(self, center, radius, color = 15):
        """
        Prints a filled circle.
        
        :param center: A touple (X,Y)
        :param radius: The radius
        :param color: Point color (default white).
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("CIRF("+ str(center[0])+","+str(center[1]) + "," + str(radius) + ","+str(color)+")")
        return res
    
    def Background(self, color):
        """Sets background color for text.
        
        :param color: Color number (you can use one of the color names instance.COLOR_xxxx)
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("SBC("+str(color)+")")
        return res
    
    def TextSmall(self, location, text, color = 15):
        """
        Prints text with font 16.
        
        :param location: A touple (X,Y)
        :param text: Text to be printed
        :param color: Text color (default white). Current background color will be used.
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("DCV16("+str(location[0])+","+str(location[1])+",'"+str(text)+"',"+str(color)+")")
        return res
    
    def TextMedium(self, location, text, color = 15):
        """
        Prints text with font 24.
        
        :param location: A touple (X,Y)
        :param text: Text to be printed
        :param color: Text color (default white). Current background color will be used.
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("DCV24("+str(location[0])+","+str(location[1])+",'"+str(text)+"',"+str(color)+")")
        return res
    
    def TextLarge(self, location, text, color = 15):
        """
        Prints text with font 32.
        
        :param location: A touple (X,Y)
        :param text: Text to be printed
        :param color: Text color (default white). Current background color will be used.
        :returns: True on success, False otherwise.
        """
        res = self.send_serial("DCV32("+str(location[0])+","+str(location[1])+",'"+str(text)+"',"+str(color)+")")
        return res

    
    
    
    
    
    # ========================================================================
    # OBJECT-LEVEL METHODS
    # ========================================================================
    
    def MoveTo(self, position):
        """
        Sets the location of the internal cursor, without drawing anything.
        
        :param position: A tuple (X,Y)
        :returns: True on success, False otherwise.
        """
        if (isinstance(position, tuple) or isinstance(position, list)) and (len(position) == 2):
            # do not assign directly to avoid changing type
            # or replacing the list variable with a pointer
            self.cursor[0] = position[0]
            self.cursor[1] = position[1]
            return True
        else:
            return False
            
    def LineTo(self, position, color = 15):
        """
        Draws a line from the current internal cursor to the position specified,
        and moves the cursor to that position.
        
        :param position: A tuple (X,Y)
        :param color: Line color (default white).
        :returns: True on success, False otherwise.
        """
        if (isinstance(position, tuple) or isinstance(position, list)) and (len(position) == 2):
            if self.Line(self.cursor, position, color) is False:
                return False
            return self.MoveTo(position)
    
    
    def ListImage(self, size):
        """
        Adds image information into a list
        
        :param size: A tuple (W,H)
        :returns: The image ID
        """
        byte_len = size[0]*size[1]*2
        self.img_list.append([self.img_offset,size])
        self.img_offset += byte_len
        return len(self.img_list)-1
        
        
    # 
    def ListFont(self, char_size, char_list = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"):
        """
        Adds information over a list of monospaced character images.
        They must be present in the flash memory sequentially in the same order.
        
        :param char_size: A tuple (W,H)
        :param char_list: A string containing the chars in the same order as 
            they appear in the map. Defaults to ASCII char range 0x20 - 0x7E
        :returns: Font ID
        """
        this_font = {}
        i = 0
        cl_len = len(char_list)
        last_i = cl_len-1
        # create the font map
        for c in char_list:
            this_font[c] = self.ListImage(char_size)
        # add the font to the font list
        self.font_list.append(this_font)
        return len(self.font_list)-1
                
                
    def ShowImage(self, image_id, position, transparent=0):
        """
        Shows an image from te listed images (ListImage())
        
        :param image_id: The ID returned by ListImage()
        :param position: A tuple (X,Y)
        :returns: True on success, False otherwise.
        """
        if image_id > (len(self.img_list)-1):
            return False
            
        img_info = self.img_list[image_id]
        return self.RawImage(img_info[0], position, img_info[1], transparent)
        
    def TextFont(self, font_id, position, text, transparent=0):
        """
        Prints text using image fonts.
        
        :param font_id: The font ID given by ListFont
        :param position: A tuple (X,Y)
        :param text: The text to print. If a character is not
            found in the font, it is ignored.
        :param transparent: If 1, text will be rendered transparent.
        :returns: True on success, False otherwise.
        """
        if font_id > (len(self.font_list)-1):
            return False
        this_font = self.font_list[font_id]
        # this_font[ 'char' ] = Image ID
        # self.img_list[ Image ID ][1] = (W,H)
        
        x = position[0]
        y = position[1]
        
        if self.current_orientation == self.HORIZONTAL:
            lcd_w = self.standard_height
            lcd_h = self.standard_width
        else:
            lcd_w = self.standard_width
            lcd_h = self.standard_height
        
        
        # we have to flush every 16 chars to avoid buffer overflow in the lcd
        i = 0 
        send_str = ""
        for c in text:
            if c in this_font:
                # Prints the char
                char_img_id = this_font[c]
                img_info = self.img_list[char_img_id]
                char_size = img_info[1]
                # below is deprecated: stack several instructions into one string instead
                #self.ShowImage(char_img_id, (x,y), transparent) 
                
                # FSIMG(addr,x,y,w,h,mode)
                send_str += "FSIMG("+str(img_info[0])+","+str(x)+","+str(y)+","+str(char_size[0])+","+str(char_size[1])+","+str(transparent)+");"

                
                # Moves the cursor
                x += char_size[0]
                # line wrap?
                if x >= (lcd_w - char_size[0]):
                    x = 0
                    y += char_size[1]
                    # screen wrap?
                    if y >= (lcd_h - char_size[1]):
                        y = 0
                
                # if buffered 16 chars, send them and reset counter and buffer
                i += 1
                if i >= 16:
                    res = self.send_serial(send_str)
                    if res is False:
                        return False
                    send_str = ""
                    i = 0
            
        if len(send_str) > 0:
            res = self.send_serial(send_str)
            return res
        else:
            return True

            