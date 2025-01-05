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


class OSRSMakepot(OSRSBot):
    def __init__(self):
        self.clay = None
        self.options_set = True
        bot_title = "make potion"
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
        
        watervial = 'Vial_of_water'
        
        
        kwuarm = 'Kwuarm_potion_(unf)'
        irit = 'Irit_potion_(unf)'
        iritleaf = 'Irit_leaf'
        eyeofnewt = 'Eye_of_newt'
        
        limpwurt = 'Limpwurt_root'
        # energy
        avantoe='Avantoe'
        fungus='Mort_myre_fungus'
        avantoeUnf ='Avantoe_potion_(unf)'
        
        # SUPER DEF 
        cadantine='Cadantine'
        whiteBerries='White_berries'
        cadantineUnf='Cadantine_potion_(unf)'
        
        # super restore
        snapdragon='Snapdragon'
        redSpiderEggs='Red_spiders'
        snapdragonUnf='Snapdragon_potion_(unf)'
        
        # sarabrews 
        toadflax='Toadflax'
        crushedNest='Crushed_nest'
        toadflaxUnf='Toadflax_potion_(unf)'
        
        #prayer pot
        ranarr='Ranarr_weed'
        snapeGrass='Snape_grass'
        ranarrUnf='Ranarr_potion_(unf)'
        
        #crushing
        crush = False
        birdNest='Bird_nest'
        
        
        while time.time() - start_time < end_time:
            if api_m.get_is_player_idle(2):
                
                if crush == True:
                    #self.log_msg(api_m.get_if_item_in_inv(ids.BIRD_NEST_5075))
                    while len(api_m.get_inv_item_indices(ids.BIRD_NEST_5075)) >= 3:
                        #randomSlot = random.randint(27)
                        self.mouse.move_to(self.win.inventory_slots[27].random_point(),mouseSpeed='fastest')
                        self.mouse.click()
                        #randomSlot = random.randint(26)
                        self.mouse.move_to(self.win.inventory_slots[26].random_point(),mouseSpeed='fastest')
                        self.mouse.click()
                        time.sleep(0.1)
                    self.log_msg('2 or less left')    
                    time.sleep(1)
                    if not (deposit := self.open_bank_orange()):
                        continue
                    self.mouse.move_to(deposit.random_point(),mouseSpeed='fast')
                    self.mouse.click()
                    self.withdraw_from_bank([f'{birdNest}_bank'])
                    #self.withdraw_from_bank([f'{redSpiderEggs}_bank'])
                    time.sleep(0.2)    
                else:
                    if  api_m.get_if_item_in_inv(ids.RANARR_POTION_UNF) and api_m.get_if_item_in_inv(ids.SNAPE_GRASS):
                        randomSlot = random.randint(12,13) 
                        self.mouse.move_to(self.win.inventory_slots[13].random_point(),mouseSpeed='fast') 
                        self.mouse.click()   
                        randomSlot = random.randint(14,18)         
                        self.mouse.move_to(self.win.inventory_slots[randomSlot].random_point(),mouseSpeed='fast')   
                        self.mouse.click()      
                        time.sleep(0.9) 
                        keyboard.press_and_release("space") 
                        time.sleep(0.9)
                    else:                
                        if not (deposit := self.open_bank_orange()):
                            continue
                        self.mouse.move_to(deposit.random_point(),mouseSpeed='fast')
                        self.mouse.click()

                        self.withdraw_from_bank([f'{snapeGrass}_bank'],False)
                        self.withdraw_from_bank([f'{ranarrUnf}_bank'])
                        time.sleep(0.2)
                
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
    
        
    

    def deposit_glass(self):
        self.mouse.move_to(self.win.inventory_slots[random.randint(1,7)].random_point(),mouseSpeed='fast')
        self.mouse.click()        
     
        
        
    