import time

import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
import utilities.imagesearch as imsearch
import pyautogui as pag
import keyboard
import utilities.ocr as ocr
from model.osrs.osrs_bot import OSRSBot
from model.runelite_bot import BotStatus
from model.runelite_bot import RuneLiteBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from utilities.geometry import RuneLiteObject
import random
from utilities.imagesearch import search_img_in_rect, BOT_IMAGES
from enum import Enum

class STATE(Enum):
    IDLE = 0
    CHOPPING = 1
    FEEDING = 2
    FLETCHING = 3
    HERB = 4
    
class OSRSSlayer(OSRSBot):
    def __init__(self):
        bot_title = "SLAYER"
        self.randomized_point = 0
        description = (
            "wintertoad, need to have "
        )
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 120
        self.take_breaks = False

    
    
    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])

    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks.")
        self.log_msg("Options set successfully.")
        self.options_set = True
        self.loot = ["Bird nest","Bird nest (seeds)","Bird nest (ring)","Bird nest (egg)","Clue nest (medium)","Clue nest (hard)","Clue nest (elite)","Clue nest (easy)"]

    def main_loop(self):
        # Setup API
        api_m = MorgHTTPSocket()
        #api_m = StatusSocket()

        #self.log_msg("Selecting inventory...")
        #self.mouse.move_to(self.win.cp_tabs[3].random_point())
        #self.mouse.click()

        self.logs = 0
        logs = 'Maple_logs'
        failed_searches = 0
        flag = True
        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        state = STATE.IDLE
        
        while time.time() - start_time < end_time:
            # 5% chance to take a break between tree searches
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=30, fancy=True)   
            
            self.randomized_point = self.win.prayer_orb.random_point()
            if api_m.get_is_in_combat():
                self.__prayer_flick(True)
                while api_m.get_is_in_combat():
                    self.log_msg("still in combat!")
                    self.__prayer_flick()
                self.log_msg("not any more in combat!")
                self.__prayer_flick(True)
            
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")
        
    def __prayer_flick(self,turnOn = False):
        self.mouse.move_to(self.randomized_point,mouseSpeed='fast')
        self.mouse.click()
        if turnOn == False:
            time.sleep(0.1)
            self.mouse.click()    
            time.sleep(0.4)
    
    def __activate_spec(self):
        spec_energy = self.get_special_energy()
        if spec_energy >= 100:
            self.mouse.move_to(self.win.spec_orb.random_point())
            self.mouse.click()
            
        
    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
        
    