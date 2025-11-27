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


class OSRScraftmolten(OSRSBot):
    def __init__(self):
        self.clay = None
        self.options_set = True
        bot_title = "feltch yew longs"
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
        yewlogs = 'Yew_logs'
        while time.time() - start_time < end_time:
            if api_m.get_is_player_idle(2):
                if api_m.get_if_item_in_inv(ids.MOLTEN_GLASS):
                    self.__craft_glass(api_m)
                    continue
                
                if api_m.get_is_inv_full:
                    bankchest = self.get_all_tagged_in_rect(self.win.game_view,clr.DARK_ORANGE2)
                    if not bankchest:
                        continue
                    self.mouse.move_to(bankchest[0].random_point(),mouseSpeed='medium')
                    bank = self.open_bank_orange()
                    if not bank:
                        continue
                    time.sleep(0.6)
                    self.deposit_glass()
                    self.withdraw_from_bank([f'{moltenglass}_bank'])
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
    def __craft_glass(self,api_m:MorgHTTPSocket):
        pipe = api_m.get_inv_item_indices(ids.GLASSBLOWING_PIPE)
        if not pipe:
            self.__logout("no knife located")
        self.mouse.move_to(self.win.inventory_slots[pipe[0]].random_point(),mouseSpeed='fast')
        self.mouse.click()
        glass = api_m.get_inv_item_indices(ids.MOLTEN_GLASS)
        if  glass: 
            self.mouse.move_to(self.win.inventory_slots[glass[0]].random_point(),mouseSpeed='fast')
        self.mouse.click()
        time.sleep(1.2)
        keyboard.press_and_release("7")
        
        
    

    def deposit_glass(self):
        self.mouse.move_to(self.win.inventory_slots[random.randint(1,7)].random_point(),mouseSpeed='fast')
        self.mouse.click()        
     
        
        
    