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

from utilities.imagesearch import search_img_in_rect, BOT_IMAGES


class OSRSBuyIronOre(OSRSBot):
    def __init__(self):
        self.clay = None
        self.options_set = True
        bot_title = "buyiron"
        description = (
            "edgevile cannon balls"
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
        filled = False
        if not api_m.get_if_item_in_inv(ids.COINS_995):
            self.__logout("No Coins")
        while time.time() - start_time < end_time:
            self.refresh_energy(api_m)
            keyboard.press_and_release("Escape")
            if api_m.get_if_item_in_inv(ids.COINS_995) and not api_m.get_is_inv_full():
                if not filled:
                    self.select_color(clr.DARK_ORANGE,['Trade'],api_m)
                    self.__buy_ore('Coal')
                    if len(api_m.get_inv()) > 2:
                        keyboard.press_and_release("Escape")
                        self.use_coal_bag(api_m,False)
                        filled = True
                if filled:
                    self.select_color(clr.DARK_ORANGE,['Trade'],api_m)
                self.__buy_ore('Iron_ore')
                keyboard.press_and_release("Escape")
                time.sleep(0.5)
                if not api_m.get_is_inv_full():
                    keyboard.press_and_release("0")
                    time.sleep(9)
                    continue    
            if api_m.get_is_inv_full():
                keyboard.press_and_release("Escape")
                self.open_bank()
                self.deposit('Iron_ore')
                if filled:
                    self.use_coal_bag(api_m,True)
                    filled = False
                keyboard.press_and_release("Escape")
                    
            
            #while api_m.get_if_item_in_inv(ids.STEEL_BAR):
            #    time.sleep(0.6)
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
        
    def use_coal_bag(self, api_m, bank_open):
        found_bag = search_img_in_rect(BOT_IMAGES.joinpath("items", 'Coal_bag.png'), self.win.control_panel)
        self.mouse.move_to(found_bag.random_point(), mouseSpeed='fastest')
        if bank_open:
            keyboard.press('shift')
        time.sleep(random.randint(100, 200) / 1000)
        self.mouse.click()
        if bank_open:
            keyboard.release('shift')
        if not bank_open:
            return
        timer = 0
        while 'The coal bag is now empty' not in api_m.get_latest_chat_message():
            time.sleep(0.6)
            timer += 1
            if timer > 8:
                self.use_coal_bag(api_m, bank_open)

    def deposit(self, bar):
        if found_bar := search_img_in_rect(BOT_IMAGES.joinpath("items", f'{bar}.png'), self.win.control_panel):
            self.mouse.move_to(found_bar.random_point(), mouseSpeed='fastest')
            self.mouse.click()
            time.sleep(1)
            
    def __buy_ore(self,ore):
        retries=0
        while not (ores := search_img_in_rect(BOT_IMAGES.joinpath("bank", f'{ore}_bank.png'), self.win.game_view)):
            time.sleep(0.5)
            retries += 1
            if retries > 50:
                return False
        self.mouse.move_to(ores.random_point(),mouseSpeed="fast")
        keyboard.press("Shift")
        self.mouse.click()
        time.sleep(1)
        keyboard.release("Shift")
        return True
            

    def refresh_energy(self, api_m):
        if api_m.get_run_energy() > 8000:
            self.toggle_run(True)
            #self.withdraw_from_bank(self, [f'Stamina_potion_bank'], False)
            #while not (stamina := search_img_in_rect(BOT_IMAGES.joinpath("items", 'Stamina_potion.png'), self.win.control_panel)):
            #    time.sleep(0.1)
            #self.mouse.move_to(stamina.random_point(), mouseSpeed='fastest')
            #keyboard.press('shift')
            #self.mouse.click()
time.sleep(1)
            #keyboard.release('shift')

    