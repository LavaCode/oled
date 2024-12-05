##############################################################
#
# author: KASPER
# code: OLED TIMER
#
# -- YOU ARE NOT ALLOWED TO USE W/O PERMISSION FROM AUTHOR -- 
#
# contact: kasperz@2heads.com
#
##############################################################

#!/usr/bin/env python3

import board
import busio
import threading
import json
import time
import socket
import netifaces
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont

i2c = busio.I2C(board.SCL, board.SDA)

#Set OLED address
oled = SSD1306_I2C(128, 64, i2c, addr=0x3d)
oled.fill(0)
oled.show()

image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image) 
draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=0)

timer_font_size = 40
msg_font_size = 20
label_font_size = 12
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font_timer_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

timer_font = ImageFont.truetype(font_timer_path, timer_font_size)
msg_font = ImageFont.truetype(font_path, msg_font_size)
label_font = ImageFont.truetype(font_path, label_font_size)

def get_ip_address(intf):
    try:
        ip_address = netifaces.ifaddresses(intf)[netifaces.AF_INET][0]
        print(f"Device IP address of {intf} is: {ip_address}")
        return ip_address
    except KeyError:
        print(f"No IP address found or seth for: {intf}")
        return None

#Set network interface
udp_ip = get_ip_address('eth0')

#Set desired UDP listening port#
udp_port = 12345

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True: 
    try: 
        sock.bind((udp_ip, udp_port))
        break
    except OSError as e:
        print("Error")
        time.sleep(5)

timer_running = False 
remaining_time = 0 
duration_file = "/home/galaxy/countdown_duration.json"
countdown_duration = 20  #Set a default duration
default_message = "Waiting..."

def show_fullscreen_message(msg): 
    background = Image.new('1', (128, 64), 'black')
    draw = ImageDraw.Draw(background)
    
    text_bbox = draw.textbbox((0, 0), msg, font=msg_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (oled.width - text_width) // 2
    y = (oled.height - text_height) // 2
    draw.text((x, y), msg, font=msg_font, fill=255)
    
    oled.image(background)
    oled.show()

def countdown_timer(): 
    global timer_running, remaining_time
    if not timer_running: 
        return
    
    for remaining_time in range(remaining_time, -1, -1): 
        minutes, seconds = divmod(remaining_time, 60)
        update_display(minutes, seconds)
        time.sleep(1)

        if remaining_time == 0:
            timer_running = False
            print("Timer finished!")
            show_fullscreen_message(default_message)
            break
        if not timer_running:
            break

def update_display(minutes, seconds): 
    background = Image.new("1", (128,64), 'black')
    draw = ImageDraw.Draw(background)

    time_display = f"{minutes:02}:{seconds:02}"
    label_text = "Time remaining:"

    #Label positioning
    label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_width = label_bbox[2] - label_bbox[0]
    label_height = label_bbox[3] - label_bbox[1]
    label_position = ((128 - label_width) // 2, 5)
    draw.text(label_position, label_text, font=label_font, fill=255)

    #Timer positioning
    timer_bbox = draw.textbbox((0, 0), time_display, font=timer_font)
    timer_width = timer_bbox[2] - timer_bbox[0]
    timer_height = timer_bbox[3] - timer_bbox[1]
    timer_position = ((128 - timer_width) // 2, 10 + label_height)
    draw.text(timer_position, time_display, font=timer_font, fill="white")

    oled.image(background)
    oled.show()

def handle_udp_commands():
    global timer_running, remaining_time, countdown_thread, countdown_duration
    while True:
        data, addr = sock.recvfrom(1024)
        command = data.decode("utf-8").strip()

        if command == "start":
            if not timer_running:
                timer_running = True
                remaining_time = countdown_duration
                sock.sendto(b"start_rcv", addr)
                countdown_thread = threading.Thread(target=countdown_timer)
                countdown_thread.start()
                print("Timer started")
            else:
                print("Timer already running.")
        elif command == "stop":
            if timer_running: 
                timer_running = False
                sock.sendto(b"stop_rcv", addr)
                print("Timer stopped")

                remaining_time = 0
                if countdown_thread is not None:
                    countdown_thread.join()
                show_fullscreen_message(default_message)
                oled.image(Image.new('1', (128,64), 'black'))
                oled.show()
        elif command.startswith("DUR!"):
            try:
                new_duration = int(command.split("!")[1])
                print(f"Value received: {new_duration} seconds")

                if new_duration < 3600 and new_duration > 0: 
                    countdown_duration = new_duration
                    save_countdown_duration()
                    sock.sendto(f"DUR!{new_duration}_rcv".encode("utf-8"), addr)
                    print(f"Countdown duration updated to {new_duration} seconds")
                else:
                    sock.sendto(f"DUR!INV!".encode("utf-8"), addr)
                    print("Invalid value received! Duration is invalid")
            except: 
                sock.sendto(f"DUR!INV!".encode("utf-8"), addr)
                print("Invalid value received! Data packet is invalid")
        else: 
            print("Timer is not running!")

def load_countdown_duration():
    global countdown_duration
    try:
        with open(duration_file, "r") as f:
            countdown_duration = json.load(f)["countdown_duration"]
            print(f"Loaded countdown duration from file: {countdown_duration} seconds")
    except (FileNotFoundError, json.JSONDecodeError): 
        print(f"No data - using default duration: {countdown_duration} seconds")
        save_countdown_duration()

def save_countdown_duration():
    with open(duration_file, "w") as f:
        json.dump({"countdown_duration": countdown_duration}, f)
        print(f"Countdown duration saved to file: {countdown_duration} seconds")

udp_thread = threading.Thread(target=handle_udp_commands)
udp_thread.daemon = True
udp_thread.start()

load_countdown_duration()
show_fullscreen_message(default_message)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting script")

##############################################################