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


class OSRSsuperglass(OSRSBot):
    def __init__(self):
        self.clay = None
        self.options_set = True
        bot_title = "super glass make"
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
        filled = False
        if not api_m.get_if_item_in_inv(ids.COINS_995):
            self.__logout("No Coins")
        while time.time() - start_time < end_time:
            self.open_bank()
            self.withdraw_from_bank("Giant_seaweed_bank")
            self.withdraw_from_bank("Giant_seaweed_bank")
            keyboard.press("Shift")
            self.withdraw_from_bank("Bucket_of_sand_bank")
            keyboard.release("Shift")
            self.__cast_superglass()
            api_m.wait_til_gained_xp('Crafting',10)
            self.__bank_molten_glass()           
                
            
            
                    
            
            #while api_m.get_if_item_in_inv(ids.STEEL_BAR):
            #    time.sleep(0.6)
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
    
    def __cast_superglass(self):
        superglass_str = BOT_IMAGES.joinpath("spellbooks").joinpath("lunar","superglass_spell.png")
        superglass = search_img_in_rect(superglass_str,self.win.control_panel)
        if not superglass:
            keyboard.press_and_release("F6")
            superglass = search_img_in_rect(superglass_str,self.win.control_panel)
            if not superglass:
                return False
        self.mouse.move_to(superglass.random_point(),mouseSpeed='fast')
        self.mouse.click()
        return True
        
    def __bank_molten_glass(self,api_m: MorgHTTPSocket):
        retry = random.randint(0,5)
        done = False
        while(api_m.get_if_item_in_inv(ids.MOLTEN_GLASS)):
            keyboard.press_and_release("escape")
            time.sleep(random.randint(600,940)/1000)
            while not (val := search_img_in_rect(BOT_IMAGES.joinpath("bank","bankdeposit.png"),self.win.game_view)):
                time.sleep(0.1)
                if api_m.get_is_inv_empty() :
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
        
        
    