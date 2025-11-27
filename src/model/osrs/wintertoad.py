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
    
class OSRSwintertoad(OSRSBot):
    def __init__(self):
        bot_title = "wintertoad"
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
            
            if api_m.get_winterdt_active() and state == STATE.IDLE and api_m.get_is_player_idle():
                if api_m.get_winterdt_health() <= 10:
                    if api_m.get_if_item_in_inv(ids.BRUMA_ROOT) or api_m.get_if_item_in_inv(ids.BRUMA_KINDLING):
                        state = STATE.FEEDING
                else:
                    if api_m.get_is_inv_full():
                        if api_m.get_if_item_in_inv(ids.BRUMA_ROOT):
                            state = STATE.FLETCHING
                        else:
                            state = STATE.FEEDING
                    else:
                        state = STATE.CHOPPING
                        
            if not api_m.get_winterdt_active():
                if  self.__get_total_sips(api_m) < 3:
                    # make potion
                    state = STATE.HERB
                    
            if api_m.get_winterdt_warmth() <= 60: 
                # drink potion.
                ind = self.__get_potion_index(api_m)
                if ind:
                    self.mouse.move_to(self.win.inventory_slots[ind[0]].random_point(),mouseSpeed='fast')
                    self.mouse.click()
                else :
                    # make potion
                    state = STATE.HERB
                                    
            if state == STATE.FEEDING:
                if not api_m.get_winterdt_active() :
                    state = STATE.IDLE
                    continue 
                if not api_m.get_is_player_idle(1.7) and api_m.get_animation() not in [2846,1248]:
                    self.log_msg("player is not idle not chopping/fletching, with ID =  " + str(api_m.get_animation()) )
                    continue
                    # 832
                if not (api_m.get_if_item_in_inv(ids.BRUMA_ROOT) or api_m.get_if_item_in_inv(ids.BRUMA_KINDLING)):                    
                    state = STATE.IDLE
                    continue
                self.select_color(clr.BLUE,['Feed','brazier','Brazier','Light'],api_m)

            if state == STATE.FLETCHING:
                #self.log_msg("current wintertoad hp: "+ str(api_m.get_winterdt_health()))
                if api_m.get_winterdt_health() < 12:
                    state = STATE.FEEDING
                    continue
                if not api_m.get_winterdt_active():
                    state = STATE.IDLE
                    continue
                if not api_m.get_if_item_in_inv(ids.BRUMA_ROOT):
                    state = STATE.FEEDING
                    continue
                if not api_m.get_is_player_idle(0.2):
                    continue
                self.__fletch_roots(api_m)
                
            if state == STATE.CHOPPING:
                #self.log_msg("current wintertoad hp: "+ str(api_m.get_winterdt_health()))
                if api_m.get_winterdt_health() < 13:
                    state = STATE.FEEDING
                    continue
                if not api_m.get_winterdt_active():
                    state = STATE.IDLE
                    continue
                if api_m.get_is_inv_full():
                    state = STATE.FLETCHING
                    continue 
                #if api_m.get_animation_id() != 2846:
                if not api_m.get_is_player_idle(0.1):
                    continue
                #self.__activate_spec()
                self.select_color(clr.YELLOW,['Chop','Bruma','roots'],api_m)
                time.sleep(0.2)

            if state == STATE.HERB:
                self.__make_pot(api_m)
                state = STATE.IDLE
                continue
            
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")
    def __fletch_roots(self,api_m=MorgHTTPSocket):
        knife = api_m.get_inv_item_indices(ids.KNIFE)
        if not (roots := api_m.get_inv_item_indices(ids.BRUMA_ROOT)) :
            return
        self.mouse.move_to(self.win.inventory_slots[knife[0]].random_point(),mouseSpeed='fast')
        self.mouse.click()
        if not (roots := api_m.get_inv_item_indices(ids.BRUMA_ROOT)) :
            self.mouse.click()
            return
        self.mouse.move_to(self.win.inventory_slots[roots[0]].random_point(),mouseSpeed='fastest')
        self.mouse.click()
        time.sleep(2.5)
    
    
    def __activate_spec(self):
        spec_energy = self.get_special_energy()
        if spec_energy >= 100:
            self.mouse.move_to(self.win.spec_orb.random_point())
            self.mouse.click()
            
    def __make_pot(self,api_m=MorgHTTPSocket):
        self.select_color(clr.PINK,['Pick','Sprouting','Roots'],api_m)
        while len(api_m.get_inv_item_indices(ids.BRUMA_HERB)) < 3:
            time.sleep(0.2)
        herb = api_m.get_inv_item_indices(ids.BRUMA_HERB)
        for i in range(len(herb)):
            self.select_color2(clr.RED,['Take','concoction'],api_m)
            time.sleep(0.5)
            while not api_m.get_is_player_idle():
                time.sleep(0.1)
        self.mouse.move_to(self.win.inventory_slots[herb[-1]].random_point(),mouseSpeed='fastest')
        self.mouse.click()
        time.sleep(0.1)
        self.mouse.move_to(self.win.inventory_slots[api_m.get_inv_item_indices(ids.REJUVENATION_POTION_UNF)[0]].random_point(),mouseSpeed='fastest')
        self.mouse.click()
        time.sleep(0.1)
        while not api_m.get_is_player_idle(2):
            time.sleep(0.1)
        
    def __get_potion_index(self,api_m=MorgHTTPSocket):
        for i in [ids.REJUVENATION_POTION_1 , ids.REJUVENATION_POTION_2 , ids.REJUVENATION_POTION_3 , ids.REJUVENATION_POTION_4]:
            if (id := api_m.get_inv_item_indices(i)):    
                return id
        return None            
        
    def __get_total_sips(self,api_m=MorgHTTPSocket):
        total = 0
        for i in [ids.REJUVENATION_POTION_1 , ids.REJUVENATION_POTION_2 , ids.REJUVENATION_POTION_3 , ids.REJUVENATION_POTION_4]:
            total += len(api_m.get_inv_item_indices(i)) * (i+1)
        return total
    def __round_is_complete(self,api_m=MorgHTTPSocket):
        if self.chatbox_text_BLACK_first_line(contains="Your subdued") or self.chatbox_text_BLACK_first_line(contains="owned an additional"):
            return True
        return False
    
    def __game_is_active(self,api_m=MorgHTTPSocket):
        game_active = imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("wintertoad", "wintertoad_start.png"),self.win.game_view)
        if game_active:
            return True
        return False
        
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
   
        
        