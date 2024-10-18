import random
import time
import keyboard
import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from model.runelite_bot import BotStatus
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from utilities.geometry import RuneLiteObject
import pyautogui as pag
import random

from utilities.imagesearch import search_img_in_rect, BOT_IMAGES


class OSRSKarambwan(OSRSBot):
    def __init__(self):
        self.clay = None
        self.options_set = True
        bot_title = "fish karambwan"
        description = (
            "NA"
        )
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 240
        self.take_breaks = True

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
        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        moltenglass = 'Molten_glass'
        self.toggle_run(True)
        location = 0
        isFULL = 0
        while time.time() - start_time < end_time:
            if api_m.get_is_player_idle(2):
                
                # start at crafting guild
                if not api_m.get_if_item_in_inv([ids.RAW_KARAMBWANJI,ids.KARAMBWAN_VESSEL]):
                    self.__logout('KARAMWANJI/Vessil is missing')
                
                if location == 0:
                    ring = search_img_in_rect(BOT_IMAGES.joinpath("items", 'Slayer_ring_(eternal).png'), self.win.control_panel)
                    if not ring:
                        self.__logout('ring not found')

                    self.mouse.move_to(ring.random_point(),mouseSpeed='fast')
                    if not self.mouseover_text(contains="Rub", color=clr.OFF_WHITE):
                        continue
                    self.mouse.click()

                    time.sleep(1.7)
                    keyboard.press_and_release("1")
                    time.sleep(1.3)
                    keyboard.press_and_release("3")
                    location = 1                    
                    time.sleep(random.randint(3,4))
                
                if location == 1:
                    cave_enterance = self.get_all_tagged_in_rect(self.win.game_view,clr.RED)
                    if not cave_enterance:
                        continue
                    self.mouse.move_to(cave_enterance[0].random_point(),mouseSpeed='medium')
                    if not self.mouseover_text(contains="Enter", color=clr.OFF_WHITE):
                        continue
                    self.mouse.click()
                    time.sleep(3)
                    location = 2
                
                if location == 2:
                    fairy_ring = self.get_all_tagged_in_rect(self.win.game_view,clr.ORANGE)
                    if not fairy_ring:
                        continue
                    self.mouse.move_to(fairy_ring[0].random_point(),mouseSpeed='fast')
                    if not self.mouseover_text(contains="Last-destination", color=clr.OFF_WHITE):
                        continue
                    self.mouse.click()
                    time.sleep(3)
                    location = 3    
                
                if location == 3:
                    if not api_m.get_is_inv_full():
                        self.__fish_until_full(api_m)
                    else :
                        if isFULL < 2:
                            isFULL+=self.__barrel()
                            continue
                        #craftingCape = search_img_in_rect(BOT_IMAGES.joinpath("items", 'Crafting_cape.png'), self.win.control_panel)
                        craftingCape = api_m.get_inv_item_indices(ids.CRAFTING_CAPET)
                        if not craftingCape:
                            continue
                        self.mouse.move_to(self.win.inventory_slots[craftingCape[0]].random_point(),mouseSpeed='medium')
                        if not self.mouseover_text(contains="Teleport", color=clr.OFF_WHITE): 
                            continue
                        self.mouse.click()
                        time.sleep(2)
                        location = 0
                        self.open_bank_orange()
                        isFULL=self.__barrel(empty=True)
                        self.deposit_fish()
                        keyboard.press_and_release('escape')
                         
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
    
    
    def __barrel(self,empty=False):
        barrel = search_img_in_rect(BOT_IMAGES.joinpath("items", 'Fish_barrel.png'), self.win.control_panel)
        if not barrel:
            keyboard.press_and_release("escape")
            barrel = search_img_in_rect(BOT_IMAGES.joinpath("items", 'Fish_barrel.png'), self.win.control_panel)
            if not barrel:
                self.__logout('Cant find barrel')
        self.mouse.move_to(barrel.random_point(),mouseSpeed='fast')
        if not empty:
            if not self.mouseover_text(contains="Fill", color=clr.OFF_WHITE): 
                self.mouse.move_to(barrel.random_point(),mouseSpeed='fast')
            self.mouse.click()
            return 1
        if empty:
            if not self.mouseover_text(contains="Empty", color=clr.OFF_WHITE): 
                self.mouse.move_to(barrel.random_point(),mouseSpeed='fast')
            keyboard.press('shift')
            time.sleep(0.2)
            self.mouse.click()
            keyboard.release('shift')
            return 0
        
    def __fish_until_full(self,api_m:MorgHTTPSocket):
        retries = 0
        while(not api_m.get_is_inv_full()):
            if retries >= 200:
                self.__logout('Can\'t locate fishing spot')
            if api_m.get_is_player_idle():
                fishSpot = self.get_all_tagged_in_rect(self.win.game_view,clr.CYAN)
                if not fishSpot:
                    retries += 1
                    continue
                self.mouse.move_to(fishSpot[0].random_point(),mouseSpeed='fast')
                if not self.mouseover_text(contains=["Fish","Fishing","spot"], color=[clr.OFF_WHITE,clr.OFF_YELLOW]): 
                        continue
                self.mouse.click()
                time.sleep(7)

    def deposit_fish(self):
        self.mouse.move_to(self.win.inventory_slots[random.randint(4,7)].random_point(),mouseSpeed='fast')
        self.mouse.click()        
     
        
        
    