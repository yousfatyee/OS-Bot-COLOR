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


class OSRSWoodcutter(OSRSBot):
    def __init__(self):
        bot_title = "Woodcutter"
        description = (
            "This bot power-chops wood. Position your character near some trees, tag them, and press Play.\nTHIS SCRIPT IS AN EXAMPLE, DO NOT USE LONGTERM."
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

            # 2% chance to drop logs early
            #if rd.random_chance(probability=0.02):
                #self.__burn_logs(api_m)

            # If inventory is full, drop logs
            if api_m.get_is_inv_full():
                self.__burn_logs(api_m)

            # If our mouse isn't hovering over a tree, and we can't find another tree...
            if not self.__move_mouse_to_nearest_tree():
                if not self.mouseover_text(contains="Chop", color=clr.OFF_WHITE) :
                    failed_searches += 1
                    if failed_searches % 10 == 0:
                        self.log_msg("Searching for trees...")
                    if failed_searches > 70:
                        # If we've been searching for a whole minute...
                        self.__logout("No tagged trees found. Logging out.")
                    time.sleep(1)
                    continue
            failed_searches = 0  # If code got here, a tree was found

            # Click if the mouseover text assures us we're clicking a tree
            if not self.mouseover_text(contains="Chop", color=clr.OFF_WHITE):
                continue
            
            self.mouse.click()
            time.sleep(3.5)

            # While the player is chopping (or moving), wait
            probability = 0.10
            while not api_m.get_is_player_idle():
                # Every second there is a chance to move the mouse to the next tree, lessen the chance as time goes on
                if rd.random_chance(probability):
                    self.__move_mouse_to_nearest_tree(next_nearest=True)
                    probability /= 5
                RuneLiteBot.pick_up_loot(self,self.loot)
                time.sleep(1)

            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()

    def __move_mouse_to_nearest_tree(self, next_nearest=False):
        """
        Locates the nearest tree and moves the mouse to it. This code is used multiple times in this script,
        so it's been abstracted into a function.
        Args:
            next_nearest: If True, will move the mouse to the second nearest tree. If False, will move the mouse to the
                          nearest tree.
            mouseSpeed: The speed at which the mouse will move to the tree. See mouse.py for options.
        Returns:
            True if success, False otherwise.
        """
        trees = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)
        tree = None
        if not trees:
            return False
        # If we are looking for the next nearest tree, we need to make sure trees has at least 2 elements
        if next_nearest and len(trees) < 2:
            return False
        trees = sorted(trees, key=RuneLiteObject.distance_from_rect_center)
        tree = trees[1] if next_nearest else trees[0]
        if next_nearest:
            self.mouse.move_to(tree.random_point(), mouseSpeed="slow", knotsCount=2)
        else:
            self.mouse.move_to(tree.random_point())
        return True
    
    def __bank_log(self,api_m: MorgHTTPSocket):
        retry = random.randint(0,5)
        done = False
        while(not done):
            keyboard.press_and_release("escape")
            time.sleep(random.randint(600,940)/1000)
            bank_depost = self.get_all_tagged_in_rect(self.win.game_view, clr.BLUE)[0]
            if not bank_depost:
                self.__logout("cant locate bank desposit")
            self.mouse.move_to(bank_depost.random_point(), mouseSpeed="slow", knotsCount=2)
            self.mouse.click()
            while not (val := search_img_in_rect(BOT_IMAGES.joinpath("bank","bankdeposit.png"),self.win.game_view)):
                time.sleep(0.1)
                retry += 1
                if retry >= 10:
                    retry = random.randint(0,5)
                    continue
            if not val:
                continue
            
            while not (bank_all := search_img_in_rect(BOT_IMAGES.joinpath("bank","bankall.png"),self.win.game_view)) and not api_m.get_is_player_idle():
                time.sleep(0.1)
                retry += 1
                if retry >= 10:
                    retry = random.randint(0,5)
                    continue
            if not bank_all:
                continue
            self.log_msg("Deposting...")
            self.mouse.move_to(bank_all.random_point())
            self.mouse.click()
            time.sleep(random.randint(600,940)/1000)
            slots = api_m.get_inv_item_indices(ids.logs)
            if len(slots) == 0 :
                done = True
                break
        self.log_msg("closing desposit")
        keyboard.press_and_release("escape")
        return None
    
    def __fletch_log(self, api_m: MorgHTTPSocket):
                        
        knife = api_m.get_inv_item_indices(ids.KNIFE)
        slots = api_m.get_inv_item_indices(ids.logs)
        if len(slots) == 0 :
            self.log_msg("NO LOGS TO FLETCH...")
            return None
        
        
        while (1):
            retry = 0 
            self.mouse.move_to(self.win.inventory_slots[knife[0]].random_point())
            if not self.mouseover_text(contains="Use", color=clr.OFF_WHITE):
                self.log_msg("cant find 'USE' text...")
                continue
            self.mouse.click()

            #get first 4
            slots = slots[:4]
            rand_log =random.choice(range(len(slots)))
            slot = self.win.inventory_slots[slots[rand_log]]
            self.mouse.move_to(slot.random_point())
            if not self.mouseover_text(contains="Use", color=clr.OFF_WHITE):
                self.log_msg("cant find 'USE' text...")
                continue
            self.mouse.click()
            time.sleep(random.randint(550,850)/1000)
            #path = BOT_IMAGES.joinpath("chatbox","fletching1.png")
            while not (val := search_img_in_rect(BOT_IMAGES.joinpath("chatbox","fletching1.png"),self.win.chat)):
                time.sleep(random.randint(100,300)/1000)
                retry += 1
                if retry == 5:
                    break
                
            if not val:
                continue
            
            pag.press("space")
            
            while not api_m.get_is_player_idle():
                time.sleep(0.05)
            
            slots = api_m.get_inv_item_indices(ids.logs)
            if len(slots) == 0 :
                self.log_msg("NO LOGS TO FLETCH...")   
                break
        
        return None             

    def __burn_logs(self, api_m: MorgHTTPSocket):
        start_tile = self.get_all_tagged_in_rect(self.win.game_view, clr.BLUE)
        tile = None
        if not start_tile:
            return False
        tile_ind = random.choice(range(len(start_tile)))
        tile = start_tile[tile_ind]
        tile_start = tile.random_point()
        self.mouse.move_to(tile_start, mouseSpeed="slow", knotsCount=2)
        
        if not self.mouseover_text(contains="Walk here", color=clr.OFF_WHITE):
            return False
        self.mouse.click()
        while not api_m.get_is_player_idle():
            self.log_msg("walking to spot")
            time.sleep(0.1)
                
        tinder_box = api_m.get_inv_item_indices(ids.TINDERBOX)
        
        while(1):
            slots = api_m.get_inv_item_indices(ids.logs)
            if len(slots) == 0 :
                break
            for i, slot in enumerate(self.win.inventory_slots):
                if i not in slots:
                    continue
                self.mouse.move_to(self.win.inventory_slots[tinder_box[0]].random_point())
                self.mouse.click()
                self.mouse.move_to(slot.random_point())
                self.mouse.click()
                while not api_m.get_is_player_idle():
                    time.sleep(0.05)
                if "You can't light a" in api_m.get_latest_chat_message() and api_m.get_is_player_idle():
                    while(True):
                        start_tile = self.get_all_tagged_in_rect(self.win.game_view, clr.BLUE)
                        if not start_tile:
                            return False
                        ntile_ind = random.choice(range(len(start_tile)))
                        #next_tile = random.choice(start_tile)
                        if  ntile_ind != tile_ind:
                            tile_ind = ntile_ind
                            tile = start_tile[tile_ind]
                            tile_start = tile.random_point()
                            self.mouse.move_to(tile_start, mouseSpeed="slow", knotsCount=2)
                            self.log_msg("walking to next spot")
                            if not self.mouseover_text(contains="Walk here", color=clr.OFF_WHITE):
                                continue
                            self.mouse.click()
                            while not api_m.get_is_player_idle():
                                time.sleep(0.1)
                            break
                
            while not api_m.get_is_player_idle():
                time.sleep(0.1)
        self.log_msg("no more logs to burn...")
        return None            
        
        
        
        

    def __drop_logs(self, api_m: StatusSocket):
        """
        Private function for dropping logs. This code is used in multiple places, so it's been abstracted.
        Since we made the `api` and `logs` variables assigned to `self`, we can access them from this function.
        """
        slots = api_m.get_inv_item_indices(ids.logs)
        self.drop(slots)
        self.logs += len(slots)
        self.log_msg(f"Logs cut: ~{self.logs}")
        time.sleep(1)
   
        
        