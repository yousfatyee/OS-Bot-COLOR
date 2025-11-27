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


class OSRSMotherLode(OSRSBot):
    def __init__(self):
        bot_title = "MotherLode"
        description = (
            "MotherLode."
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
        mined = 0
        banked = 0
        number_of_deposit = 3
        flag = True
        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        while time.time() - start_time < end_time:
            # 5% chance to take a break between tree searches
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=30, fancy=True)           
            
            
            loc = api_m.get_player_position()
            if api_m.get_is_inv_full()  and loc[1] >= 5675:# still in mining area
                self.log_msg("Inventory is full")
                #if  5671 <= loc[1] and loc[1] >=5673: # might be blocked 
                if loc[1] > 5676:
                    self.log_msg("Inventory is full going down")
                    if self.__get_nearest_between_two_colors(clr.CYAN,clr.RED): 
                        if self.mouseover_text(contains=["Mine","Climb"],color=clr.OFF_WHITE):
                            self.mouse.click()
                else:
                    if self.__move_to_closest_color(clr.CYAN):
                        if self.mouseover_text(contains="Climb",color=clr.OFF_WHITE):
                            self.mouse.click()
                #time.sleep(.6*random.randint(4,5))
            elif (api_m.get_is_inv_full() or (banked > 0 and  len(api_m.get_inv()) > 1 )) and  loc[1] < 5675: # main area
                self.log_msg(f"Inventory is full in main area! banked = {banked}")
                if api_m.get_if_item_in_inv(ids.PAYDIRT):
                    self.log_msg("depositing in hopper!")
                    self.__move_to_color(clr.GREEN)
                    if self.mouseover_text(contains="Deposit",color=clr.OFF_WHITE):
                        self.mouse.click()
                        mined += 1
                    self.log_msg(f"total mined inventories = {mined}")   
                else:
                    self.__move_to_color(clr.DARK_ORANGE)
                if self.mouseover_text(contains="Deposit",color=clr.OFF_WHITE):
                    self.mouse.click()
                    #while api_m.get_is_player_idle():
                        #time.sleep(.6*random.randint(2,3))
                if not api_m.get_if_item_in_inv(ids.PAYDIRT):
                    self.__bank_ores(api_m)
                    self.log_msg("banked successfully!!")
                    banked += 1
                    time.sleep(0.6)
                    
                    # if not (deposit := self.open_bank_orange()):
                    #     continue
                    # self.mouse.move_to(deposit.random_point(),mouseSpeed='fast')
                    # self.mouse.click()
                    # keyboard.press_and_release('esc')
                    # banked += 1
                    # self.log_msg(f"total banked inventories = {banked}") 
                    
                    
                        
             
            
                        
            if not api_m.get_is_inv_full():
                if (sack := self.get_all_tagged_in_rect(self.win.game_view,clr.WHITE)) and mined == number_of_deposit and banked != mined: # need to bank ores
                    self.log_msg("looting the sack")
                    self.mouse.move_to(sack[0].random_point(),mouseSpeed="fast")
                    if self.mouseover_text(contains="Search",color=clr.OFF_WHITE):
                        self.mouse.click()
                        #if api_m.wait_til_gained_xp('Mining',10) > 0:
                               
                elif mined < number_of_deposit :
                    self.log_msg(f"mining still... {mined}")
                    loc = api_m.get_player_position()
                    if loc[1] < 5675: # main area
                        if self.__move_to_closest_color(clr.CYAN):
                            
                            if self.mouseover_text(contains="Climb",color=clr.OFF_WHITE):
                                self.mouse.click()
                                #time.sleep(.6*random.randint(5,6))
                    elif loc[1] >= 5675: #mine :)
                        if self.__get_nearest_between_two_colors(clr.PINK,clr.RED):
                            if self.mouseover_text(contains="Mine",color=clr.OFF_WHITE):
                                self.mouse.click()
            while not api_m.get_is_player_idle(2):
                time.sleep(0.1)
            
            if banked == mined:
                banked = 0
                mined = 0
            #if api_m.get_is_inv_full() and api_m.get_if_item_in_inv(ids.PAYDIRT):
            #    loc = api_m.get_player_position()
            #    if loc[0] >= 3765: # still in mining area
            #        if  5671 <= loc[1] and loc[1] >=5673: # might be blocked 
            #            if self.__get_nearest_between_two_colors(clr.CYAN,clr.RED):
            #                if self.mouseover_text(contains=["Mine","Enter"],color=clr.OFF_WHITE):
            #                    self.mouse.click()
            #        else:
            #            if self.__move_to_color(clr.CYAN):
            #                if self.mouseover_text(contains="Enter",color=clr.OFF_WHITE):
            #                    self.mouse.click()
            #        time.sleep(.6*random.randint(4,5))
            #    elif loc[0] <= 3759: # main area
            #        if self.__move_to_color(clr.GREEN):
            #            if self.mouseover_text(contains="Deposit",color=clr.OFF_WHITE):
            #                self.mouse.click()
            #        time.sleep(.6*random.randint(4,5))
            #elif api_m.get_is_inv_full():

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
    def __move_to_color(self,clr):
        obj = self.get_all_tagged_in_rect(self.win.game_view,clr)
        if not obj:
            return False
        self.mouse.move_to(obj[0].random_point(),mouseSpeed="medium")
        return True
    
    def __move_to_closest_color(self,clr):
        obj = self.get_all_tagged_in_rect(self.win.game_view,clr)
        if not obj:
            return False
        obj = sorted(obj,key=RuneLiteObject.distance_from_rect_center)
        self.mouse.move_to(obj[0].random_point(),mouseSpeed="fastest")
        return True
    
    def __get_nearest_between_two_colors(self,clr1,clr2): # mine either a block or vine if have access.
        nxt_mine = self.get_all_tagged_in_rect(self.win.game_view,clr1) + self.get_all_tagged_in_rect(self.win.game_view,clr2)
        if not nxt_mine:
            return False
        nxt_mine = sorted(nxt_mine,key=RuneLiteObject.distance_from_rect_center)
        if not nxt_mine[0]:
            return False
        self.mouse.move_to(nxt_mine[0].random_point(),mouseSpeed="fast")
        return True
        
    def __bank_ores(self,api_m: MorgHTTPSocket):
        retry = random.randint(0,5)
        done = False
        while( len(api_m.get_inv()) > 1):
            keyboard.press_and_release("escape")
            time.sleep(random.randint(600,940)/1000)
            while not (val := search_img_in_rect(BOT_IMAGES.joinpath("bank","bankdeposit.png"),self.win.game_view)):
                time.sleep(0.1)
                if len(api_m.get_inv()) <= 1 :
                    break
            if not val:
                continue
            
            while not (bank_all := search_img_in_rect(BOT_IMAGES.joinpath("bank","bankall.png"),self.win.game_view)) and not api_m.get_is_player_idle():
                time.sleep(0.1)
                if api_m.get_is_inv_empty() :
                    break
            if not bank_all:
                continue
            self.log_msg("Deposting...")
            self.mouse.move_to(bank_all.random_point())
            self.mouse.click()
            time.sleep(random.randint(600,940)/1000)
        self.log_msg("closing desposit")
        keyboard.press_and_release("escape")
        return None
            
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
        
   
        
        