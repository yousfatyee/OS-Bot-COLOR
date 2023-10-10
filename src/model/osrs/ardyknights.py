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


class OSRSTheiving(OSRSBot):
    def __init__(self):
        bot_title = "Theiving"
        description = (
            "Ardy Knights Theiving"
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

    def main_loop(self):
        # Setup API
        api_m = MorgHTTPSocket()
        #api_m = StatusSocket()

        #self.log_msg("Selecting inventory...")
        #self.mouse.move_to(self.win.cp_tabs[3].random_point())
        #self.mouse.click()

        self.logs = 0
        failed_searches = 0
        food =[ids.TUNA,ids.SALMON]
        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        banked = False
        while time.time() - start_time < end_time:
            # 5% chance to take a break between tree searches
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=30, fancy=True)    
            
            if api_m.get_inv_item_stack_amount(ids.COIN_POUCH_22531) > 10:
                coin_pouch = api_m.get_inv_item_indices(ids.COIN_POUCH_22531)
                if coin_pouch:     
                    self.mouse.move_to(self.win.inventory_slots[coin_pouch[0]].random_point(),mouseSpeed="fast")
                    self.mouse.click()
            
            slots = api_m.get_inv_item_indices(food)
            if len(slots) == 0:
                if not self.__move_to_closest_bank():
                    self.__logout("cant locate bank")
                if self.mouseover_text(contains="Bank",color=clr.OFF_WHITE):
                    self.mouse.click()
                    banked = True
                time.sleep(3)                                    
                fish = self.get_all_tagged_in_rect(self.win.game_view,clr.CYAN)
                if not fish:
                    self.__logout("cant find green tagged")
                self.mouse.move_to(fish[0].random_point(),mouseSpeed="medium")
                if self.mouseover_text(contains="Withdraw-",color=clr.OFF_WHITE):
                    self.mouse.click()
                if banked:
                    keyboard.press_and_release("escape")
                    time.sleep(1)    
            cur_hp = api_m.get_hitpoints()      
                          
            while cur_hp[1]-cur_hp[0] > 10 and len(slots) != 0:
                #keyboard.press_and_release("escape")
                self.mouse.move_to(self.win.inventory_slots[slots[0]].random_point(),mouseSpeed="fast")
                self.mouse.click()
                slots = api_m.get_inv_item_indices(food)
                cur_hp = api_m.get_hitpoints()
                
            ardy_knight = self.get_all_tagged_in_rect(self.win.game_view,clr.BLUE)
            time.sleep(0.4)
            if not ardy_knight:
                keyboard.press_and_release("2")
                banked = True
            ardy_knight = self.get_all_tagged_in_rect(self.win.game_view,clr.BLUE)
            if ardy_knight:
                self.mouse.move_to(ardy_knight[0].random_point(),mouseSpeed="fast")
                if self.mouseover_text(contains="Pickpocket", color=clr.OFF_WHITE):
                    self.mouse.click()
                    if banked and api_m.wait_til_gained_xp('Thieving', 10):
                        keyboard.press_and_release("1")
                        banked = False
                
            while self.mouseover_text(contains="Pickpocket", color=clr.OFF_WHITE):
                if  api_m.get_inv_item_stack_amount(ids.COIN_POUCH_22531) > 51:
                    break
                if  api_m.get_hitpoints()[0] < 30:
                    break
                self.mouse.click()
                time.sleep(0.1)
                #time.sleep(0.6)      

            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
        
    
    def __move_to_closest_bank(self):
        keyboard.press_and_release("2")
        time.sleep(0.3)
        keyboard.press_and_release("escape")
        time.sleep(0.6)
        bank = self.get_all_tagged_in_rect(self.win.game_view,clr.PINK)
        if not bank:
            return False
        bank = sorted(bank,key=RuneLiteObject.distance_from_rect_center)
        self.mouse.move_to(bank[0].random_point(),mouseSpeed="medium", knotsCount=2)
        return True
            
        
        