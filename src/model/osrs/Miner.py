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


class OSRSMiner(OSRSBot):
    def __init__(self):
        bot_title = "Miner"
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

        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        while time.time() - start_time < end_time:
            # 5% chance to take a break between tree searches
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=30, fancy=True)           

            if (not api_m.get_if_item_in_inv(ids.WATERSKIN1)) and (not api_m.get_if_item_in_inv(ids.WATERSKIN2)) and (not api_m.get_if_item_in_inv(ids.WATERSKIN3)) and (not api_m.get_if_item_in_inv(ids.WATERSKIN4)):
                self.__logout("No more water skins logging out")
            
            if api_m.get_if_item_in_inv(ids.WATERSKIN0):
                self.__drop_water_skins(api_m)
                
            if api_m.get_is_inv_full() and rd.random_chance(probability=0.90):
                slots1 = api_m.get_inv_item_indices(ids.SANDSTONE_1KG)
                slots2 = api_m.get_inv_item_indices(ids.SANDSTONE_2KG)
                slots = slots1+slots2
                self.drop(slots)
                time.sleep(1)   
                
            # If inventory is full, drop logs
            while api_m.get_is_inv_full() :     
                #if api_m.get_run_energy() > 30:
                #    self.toggle_run(True)                                                               
                if  self.__move_to_grinder() and api_m.get_is_player_idle():
                    if not self.mouseover_text(contains="Deposit", color=clr.OFF_WHITE):
                        continue
                    self.mouse.click()
                    while api_m.get_is_player_idle(1):
                        time.sleep(0.6*random.randint(1,2))
                elif not self.__move_to_further_tile():
                    self.__logout("cant locate grinder")
                self.mouse.click()
                time.sleep(2.5)
            
            

            # If our mouse isn't hovering over a tree, and we can't find another tree...
            if not self.__move_mouse_to_nearest_rock(False,True):
                if not self.__move_to_further_tile():
                    self.__logout("cant locate grinder")
                elif api_m.get_is_player_idle():
                    self.mouse.click()
                    time.sleep(1.5)
                if not self.mouseover_text(contains="Mine", color=clr.OFF_WHITE) :
                    failed_searches += 1
                    if failed_searches % 10 == 0:
                        self.log_msg("Searching for rocks...")
                    if failed_searches > 70:
                        # If we've been searching for a whole minute...
                        self.__logout("No tagged rocks found. Logging out.")
                    time.sleep(1)
                    continue
            failed_searches = 0  # If code got here, a tree was found

            # Click if the mouseover text assures us we're clicking a tree
            if api_m.get_is_player_idle() and self.__move_mouse_to_nearest_rock():
                if not self.mouseover_text(contains="Mine", color=clr.OFF_WHITE):
                    continue
                self.mouse.click()
            time.sleep(0.6*random.randint(1,2))

            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
        
    def __move_to_further_tile(self):
        tiles = self.get_all_tagged_in_rect(self.win.game_view, clr.GREEN)
        tile = None
        if not tiles:
            return False
        tiles = sorted(tiles, key=RuneLiteObject.distance_from_rect_center)
        tile = tiles[len(tiles)-1] 
        self.mouse.move_to(tile.random_point())
        return True
    
    def __move_to_grinder(self):
        grinder = self.get_all_tagged_in_rect(self.win.game_view, clr.RED)
        if not grinder:
            return False
        self.mouse.move_to(grinder[0].random_point(), mouseSpeed="slow", knotsCount=2)
        return True
            
    def __move_mouse_to_nearest_rock(self, next_nearest=False, dontMove=False):
        """
        Locates the nearest rock and moves the mouse to it. This code is used multiple times in this script,
        so it's been abstracted into a function.
        Args:
            next_nearest: If True, will move the mouse to the second nearest rock. If False, will move the mouse to the
                          nearest rock.
            mouseSpeed: The speed at which the mouse will move to the rock. See mouse.py for options.
        Returns:
            True if success, False otherwise.
        """
        rocks1 = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)
        rocks2 = self.get_all_tagged_in_rect(self.win.game_view, clr.CYAN)
        rocks = rocks1 + rocks2
        rock = None
        if not rocks:
            rocks = self.get_all_tagged_in_rect(self.win.game_view, clr.WHITE)
            if not rocks:
                return False
        # If we are looking for the next nearest rock, we need to make sure rocks has at least 2 elements
        if next_nearest and len(rocks) < 2:
            return False
        rocks = sorted(rocks, key=RuneLiteObject.distance_from_rect_center)
        rock = rocks[1] if next_nearest else rocks[0]
        if not dontMove:
            if next_nearest:
                self.mouse.move_to(rock.random_point(), mouseSpeed="slow", knotsCount=2)
            else:
                self.mouse.move_to(rock.random_point())
        return True            
        
    def __drop_water_skins(self, api_m: StatusSocket):
        """
        Private function for dropping logs. This code is used in multiple places, so it's been abstracted.
        Since we made the `api` and `logs` variables assigned to `self`, we can access them from this function.
        """
        slots = api_m.get_inv_item_indices(ids.WATERSKIN0)
        self.drop(slots)
        time.sleep(1)
   
        
        