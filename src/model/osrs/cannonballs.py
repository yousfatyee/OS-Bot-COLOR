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


class OSRSCannonballs(OSRSBot):
    def __init__(self):
        self.clay = None
        self.options_set = True
        bot_title = "cannon balls"
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
        while time.time() - start_time < end_time:
            if not api_m.get_if_item_in_inv(ids.STEEL_BAR):
                self.refresh_energy(api_m)
                self.open_bank()
                self.withdraw_from_bank( ['Steel_bar_bank'])
            if api_m.get_is_player_idle(2) and api_m.get_if_item_in_inv(ids.STEEL_BAR):   
                self.select_color(clr.RED,['Smelt'],api_m)
                time.sleep(random.randint(11,14)/2)
                keyboard.press_and_release("Space")
            
            #while api_m.get_if_item_in_inv(ids.STEEL_BAR):
            #    time.sleep(0.6)
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()

    

    def refresh_energy(self, api_m):
        if api_m.get_run_energy() > 5000:
            self.toggle_run(True)
            #self.withdraw_from_bank(self, [f'Stamina_potion_bank'], False)
            #while not (stamina := search_img_in_rect(BOT_IMAGES.joinpath("items", 'Stamina_potion.png'), self.win.control_panel)):
            #    time.sleep(0.1)
            #self.mouse.move_to(stamina.random_point(), mouseSpeed='fastest')
            #keyboard.press('shift')
            #self.mouse.click()
            #keyboard.release('shift')

    