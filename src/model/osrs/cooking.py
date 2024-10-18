import time

import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
import pyautogui as pag
import keyboard
from model.osrs.osrs_bot import OSRSBot
from model.runelite_bot import BotStatus
from model.runelite_bot import RuneLiteBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from utilities.geometry import RuneLiteObject
import random
from utilities.imagesearch import search_img_in_rect, BOT_IMAGES


class OSRSCooker(OSRSBot):
    def __init__(self):
        bot_title = "Cooking"
        description = (
            "This bot power-Mines wood. Position your character near some trees, tag them, and press Play.\nTHIS SCRIPT IS AN EXAMPLE, DO NOT USE LONGTERM."
        )
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 1
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
        failed_searches = 0
        flag = True
        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        
        rawKaram='Raw_karambwan'
        
        while time.time() - start_time < end_time:
            # 5% chance to take a break between tree searches
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=120, fancy=True)   
            #if api_m.get_run_energy() > 5000:
            #    self.toggle_run(True)            
            if api_m.get_is_player_idle(2):
                if  api_m.get_if_item_in_inv(ids.RAW_KARAMBWAN):
                    self.select_color2(clr.CYAN,'Cook',api_m)
                    time.sleep(0.8)
                    keyboard.press_and_release("1")
                    time.sleep(0.1)
                else:                
                    if not (deposit := self.open_bank_orange()):
                        continue
                    self.mouse.move_to(deposit.random_point(),mouseSpeed='fast')
                    self.mouse.click()
                    #self.withdraw_from_bank([f'{crushedNest}_bank'],False)
                    self.withdraw_from_bank([f'{rawKaram}_bank'])
                    time.sleep(0.2)
            i=0
            while not api_m.get_is_player_idle(2):
                if i ==0:
                    self.log_msg('player is not idle.',overwrite=True)
                    i = 1
                    time.sleep(.8)
                    continue
                elif i == 1:
                    self.log_msg('player is not idle..',overwrite=True)
                    i=2
                    time.sleep(.8)
                    continue
                else:
                    self.log_msg('player is not idle...',overwrite=True)
                    i=0
                    time.sleep(.8)
                    continue

            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
        
    