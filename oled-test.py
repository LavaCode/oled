##############################################################
#
# author: KASPER
# code: OLED TIMER - test code (first run)
#
# -- YOU ARE NOT ALLOWED TO USE W/O PERMISSION FROM AUTHOR -- 
#
# contact: kasperz@2heads.com
#
##############################################################

#!/usr/bin/env python3

import board
import busio
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont

i2c = busio.I2C(board.SDA, board.SCL)
oled = SSD1306_I2C(128, 64, i2c, addr=0x3d)

oled.fill(0)
oled.show()

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image) 
draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=0)

font_size = 14
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(font_path, font_size)
text = "First test"

bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox [1]

x = (oled.width - text_width) // 2
y = (oled.height - text_height) // 2

draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
draw.text((x, y), text, font=font, fill=255)

oled.image(image)
oled.show()