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
import utilities.ocr as ocr
from utilities.geometry import RuneLiteObject
import random
from utilities.imagesearch import search_img_in_rect, BOT_IMAGES


class OSRSplankMake(OSRSBot):
    def __init__(self):
        bot_title = "plank make"
        description = (
            "this bot will teleport to home, uses butler to create planks"
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
        flag = True
        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        
        teakLogs='Teak_logs'
        teleToHouse='Teleport_to_house'
        
        
        
        loc = 0
        while time.time() - start_time < end_time:
            # 5% chance to take a break between tree searches
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=120, fancy=True)   
            
            if loc == 0:
                if not api_m.get_if_item_in_inv([ids.COINS_995,ids.LAW_RUNE,ids.CRAFTING_CAPET]):
                    self.__logout("make sure coins,law_runes or cape is in inv!")
                if not api_m.get_if_item_in_inv(ids.TEAK_LOGS):
                    self.open_bank_orange()
                    self.withdraw_from_bank([f'{teakLogs}_bank'])
                    time.sleep(random.randint(7,10)/10)
                keyboard.press_and_release('F6')
                timer = 0
                while not (tele := search_img_in_rect(BOT_IMAGES.joinpath("spellbooks").joinpath("normal", f'{teleToHouse}.png'),self.win.control_panel) ):
                    timer += 1
                    time.sleep(1)
                    if timer == 25:
                        keyboard.press_and_release('F6')
                    if timer == 50:
                        self.__logout("failed to find teleport to house!")
                self.mouse.move_to(tele.random_point(),mouseSpeed='fast')
                timer = 0
                while not self.mouseover_text(contains=["Cast"], color=clr.OFF_WHITE) and not self.mouse.move_to(tele.random_point(), mouseSpeed='fastest'):
                    timer += 1
                    time.sleep(1)
                    if timer == 50:
                        self.__logout("cannot validate teleport!")
                self.mouse.click()
                if api_m.wait_til_gained_xp('Magic',5) > 0:
                    loc = 1
                    
                if loc == 1:
                    time.sleep(4)
                    failed = 0  
                    while api_m.get_if_item_in_inv(ids.TEAK_LOGS):
                        if not (servant := self.get_all_tagged_in_rect(self.win.game_view,clr.CYAN)):
                            self.__call_servant()
                        else:
                            self.mouse.move_to(servant[0].random_point(),mouseSpeed='fastest')
                            timer = 0
                            time.sleep(0.8)
                            while not self.mouseover_text(contains=["Talk-to"], color=clr.OFF_WHITE) and not self.mouse.move_to(servant[0].random_point(), mouseSpeed='fastest'):
                                timer += 1
                                time.sleep(1)
                                if timer == 2:
                                    self.__call_servant()
                                    break
                            if timer != 2:
                                self.mouse.click()
                        timer = 1                                                          
                        while  not ( res1 := ocr.find_text("Take to sawmill:", self.win.chat, ocr.QUILL_8, clr.BLACK) )  :
                            timer += 1
                            time.sleep(1)
                            if timer % 10 == 0:
                                self.log_msg('Cant validate text!')
                                self.__call_servant()
                            if timer == 50:
                                failed = 1
                        if failed == 0:
                            time.sleep(1)
                            keyboard.press_and_release('1')
                            time.sleep(0.8)
                            keyboard.press_and_release('space')
                            time.sleep(0.8)
                            keyboard.press_and_release('1')                            
                            time.sleep(0.8)
                            keyboard.press_and_release('space')
                            time.sleep(1.3)
                    if failed == 0:
                        keyboard.press_and_release('escape')
                        time.sleep(0.8)
                        self.mouse.move_to(self.win.inventory_slots[api_m.get_inv_item_indices(ids.CRAFTING_CAPET)[0]].random_point(),mouseSpeed='fast')
                        time.sleep(0.7)
                        timer = 0
                        while not self.mouseover_text(contains=["Teleport"], color=clr.OFF_WHITE) and not self.mouse.move_to(self.win.inventory_slots[api_m.get_inv_item_indices(ids.CRAFTING_CAPET)[0]].random_point(),mouseSpeed='fast'):
                            timer +=1 
                            time.sleep(1)
                            if timer == 5:
                                keyboard.press_and_release('escape')
                            if timer == 25:
                                self.__logout("failed to teleport back :(")
                        self.mouse.click()
                        loc = 0
                         
                                                   
                        
            
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

        
    def __call_servant(self):
        callServant='call_servant'
        houseOpt='house_options'
        self.mouse.move_to(self.win.cp_tabs[11].random_point(),mouseSpeed='fast')
        time.sleep(3)
        self.mouse.click()
        timer = 0
        while not (Settings := search_img_in_rect(BOT_IMAGES.joinpath("ui_templates", f'{houseOpt}.png'),self.win.control_panel) ):
            timer +=1
            time.sleep(.7)
            if timer == 50:
                self.__logout("cannot find settings")
        time.sleep(0.7)         
        timer = 0
        while not self.mouseover_text(contains=["View House"], color=clr.OFF_WHITE) and not self.mouse.move_to(Settings.random_point(), mouseSpeed='fastest'):
            timer +=1
            time.sleep(.7)
            if timer == 50:
                self.__logout("cannot validate settings!")
        time.sleep(0.7)
        self.mouse.click()
        time.sleep(1.5)
        if self.mouseover_text(contains=["Call"], color=clr.OFF_WHITE):
            self.mouse.click()
        else:            
            timer = 0
            while not (callServ := search_img_in_rect(BOT_IMAGES.joinpath("ui_templates", f'{callServant}.png'),self.win.control_panel)):
                timer +=1
                time.sleep(.7)
                if timer == 50:
                    self.__logout("cannot find call servant")
            timer = 0
            time.sleep(0.7)                
            while not self.mouseover_text(contains=["Call Servant"], color=clr.OFF_WHITE) and not self.mouse.move_to(callServ.random_point(), mouseSpeed='fastest'):
                timer +=1
                time.sleep(.7)
                if timer == 50:
                    self.__logout("cannot validate call servant!")                
            time.sleep(0.9)
            self.mouse.click()
        
        
    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
        
    