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
        self.crush = False
        self.crush_withdraw = "Bird_nest"
        self.make_unf_potions = False
        self.potion_type = "Prayer potion"
        self.primary_withdraw = "Ranarr_potion_(unf)"
        self.secondary_withdraw = "Snape_grass"

    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])
        self.options_builder.add_checkbox_option("crush", "Crush mode?", [" "])
        self.options_builder.add_text_edit_option("crush_withdraw", "Crush withdraw name:", "Bird_nest")
        self.options_builder.add_checkbox_option("make_unf_potions", "Make unfinished potions?", [" "])
        self.options_builder.add_dropdown_option("potion_type", "Potion type:", [
            "Prayer potion",
            "Energy potion",
            "Super defense",
            "Super restore",
            "Saradomin brew",
            "Strength potion"
        ])
        self.options_builder.add_text_edit_option("primary_withdraw", "Primary withdraw name:", "Ranarr_potion_(unf)")
        self.options_builder.add_text_edit_option("secondary_withdraw", "Secondary withdraw name:", "Snape_grass")

    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            elif option == "crush":
                self.crush = options[option] != []
            elif option == "crush_withdraw":
                self.crush_withdraw = options[option]
            elif option == "make_unf_potions":
                self.make_unf_potions = options[option] != []
            elif option == "potion_type":
                self.potion_type = options[option]
                # Auto-set primary and secondary based on potion type and mode
                if self.make_unf_potions:
                    # For making unf potions: primary = herb/weed, secondary = Vial_of_water
                    unf_potion_mapping = {
                        "Prayer potion": ("Ranarr_weed", "Vial_of_water"),
                        "Energy potion": ("Avantoe", "Vial_of_water"),
                        "Super defense": ("Cadantine", "Vial_of_water"),
                        "Super restore": ("Snapdragon", "Vial_of_water"),
                        "Saradomin brew": ("Toadflax", "Vial_of_water"),
                        "Strength potion": ("Kwuarm", "Vial_of_water")
                    }
                    if self.potion_type in unf_potion_mapping:
                        self.primary_withdraw, self.secondary_withdraw = unf_potion_mapping[self.potion_type]
                else:
                    # For making finished potions: primary = unf potion, secondary = ingredient
                    potion_mapping = {
                        "Prayer potion": ("Ranarr_potion_(unf)", "Snape_grass"),
                        "Energy potion": ("Avantoe_potion_(unf)", "Mort_myre_fungus"),
                        "Super defense": ("Cadantine_potion_(unf)", "White_berries"),
                        "Super restore": ("Snapdragon_potion_(unf)", "Red_spiders"),
                        "Saradomin brew": ("Toadflax_potion_(unf)", "Crushed_nest"),
                        "Strength potion": ("Kwuarm_potion_(unf)", "Limpwurt_root")
                    }
                    if self.potion_type in potion_mapping:
                        self.primary_withdraw, self.secondary_withdraw = potion_mapping[self.potion_type]
            elif option == "primary_withdraw":
                self.primary_withdraw = options[option]
            elif option == "secondary_withdraw":
                self.secondary_withdraw = options[option]
        
        # Re-apply potion type mapping ONLY if user didn't manually edit primary/secondary
        # This ensures auto-configuration works, but manual edits take precedence
        manual_override = "primary_withdraw" in options or "secondary_withdraw" in options
        if not manual_override and ("make_unf_potions" in options or "potion_type" in options):
            if self.make_unf_potions:
                unf_potion_mapping = {
                    "Prayer potion": ("Ranarr_weed", "Vial_of_water"),
                    "Energy potion": ("Avantoe", "Vial_of_water"),
                    "Super defense": ("Cadantine", "Vial_of_water"),
                    "Super restore": ("Snapdragon", "Vial_of_water"),
                    "Saradomin brew": ("Toadflax", "Vial_of_water"),
                    "Strength potion": ("Kwuarm", "Vial_of_water")
                }
                if self.potion_type in unf_potion_mapping:
                    self.primary_withdraw, self.secondary_withdraw = unf_potion_mapping[self.potion_type]
            else:
                potion_mapping = {
                    "Prayer potion": ("Ranarr_potion_(unf)", "Snape_grass"),
                    "Energy potion": ("Avantoe_potion_(unf)", "Mort_myre_fungus"),
                    "Super defense": ("Cadantine_potion_(unf)", "White_berries"),
                    "Super restore": ("Snapdragon_potion_(unf)", "Red_spiders"),
                    "Saradomin brew": ("Toadflax_potion_(unf)", "Crushed_nest"),
                    "Strength potion": ("Kwuarm_potion_(unf)", "Limpwurt_root")
                }
                if self.potion_type in potion_mapping:
                    self.primary_withdraw, self.secondary_withdraw = potion_mapping[self.potion_type]
            
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks.")
        self.log_msg(f"Crush mode: {'enabled' if self.crush else 'disabled'}")
        self.log_msg(f"Crush withdraw: {self.crush_withdraw}")
        self.log_msg(f"Make unf potions: {'enabled' if self.make_unf_potions else 'disabled'}")
        self.log_msg(f"Potion type: {self.potion_type}")
        self.log_msg(f"Primary withdraw: {self.primary_withdraw}")
        self.log_msg(f"Secondary withdraw: {self.secondary_withdraw}")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        # Setup API
        api_m = MorgHTTPSocket()
        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        
        watervial = 'Vial_of_water'
        
        kwuarm = 'Kwuarm'
        
        irit = 'Irit_potion_(unf)'
        iritleaf = 'Irit_leaf'
        eyeofnewt = 'Eye_of_newt'
        
        # super strength 
        kwuarmUnf = 'Kwuarm_potion_(unf)'
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
        birdNest='Bird_nest'
        
        
        while time.time() - start_time < end_time:
            if api_m.get_is_player_idle(2):
                
                if self.crush == True:
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
                    self.withdraw_from_bank([f'{self.crush_withdraw}_bank'])
                    #self.withdraw_from_bank([f'{redSpiderEggs}_bank'])
                    time.sleep(0.2)    
                else:
                    # Create mapping for item ID checks based on potion type and mode
                    item_id_mapping = {
                        "Prayer potion": {
                            "unf": (ids.RANARR_POTION_UNF, ids.SNAPE_GRASS),
                            "make_unf": (ids.RANARR_WEED, ids.VIAL_OF_WATER)
                        },
                        "Energy potion": {
                            "unf": (ids.AVANTOE_POTION_UNF, ids.MORT_MYRE_FUNGUS),
                            "make_unf": (ids.AVANTOE, ids.VIAL_OF_WATER)
                        },
                        "Super defense": {
                            "unf": (ids.CADANTINE_POTION_UNF, ids.WHITE_BERRIES),
                            "make_unf": (ids.CADANTINE, ids.VIAL_OF_WATER)
                        },
                        "Super restore": {
                            "unf": (ids.SNAPDRAGON_POTION_UNF, ids.RED_SPIDERS_EGGS),
                            "make_unf": (ids.SNAPDRAGON, ids.VIAL_OF_WATER)
                        },
                        "Saradomin brew": {
                            "unf": (ids.TOADFLAX_POTION_UNF, ids.CRUSHED_NEST),
                            "make_unf": (ids.TOADFLAX, ids.VIAL_OF_WATER)
                        },
                        "Strength potion": {
                            "unf": (ids.KWUARM_POTION_UNF, ids.LIMPWURT_ROOT),
                            "make_unf": (ids.KWUARM, ids.VIAL_OF_WATER)
                        }
                    }
                    
                    # Get the appropriate item IDs based on mode
                    mode_key = "make_unf" if self.make_unf_potions else "unf"
                    if self.potion_type in item_id_mapping and mode_key in item_id_mapping[self.potion_type]:
                        primary_id, secondary_id = item_id_mapping[self.potion_type][mode_key]
                        has_items = api_m.get_if_item_in_inv(primary_id) and api_m.get_if_item_in_inv(secondary_id)
                    else:
                        # Fallback: use default check (for backward compatibility)
                        has_items = api_m.get_if_item_in_inv(ids.RANARR_POTION_UNF) and api_m.get_if_item_in_inv(ids.SNAPE_GRASS)
                    
                    if has_items:
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

                        self.withdraw_from_bank([f'{self.secondary_withdraw}_bank'],False)
                        self.withdraw_from_bank([f'{self.primary_withdraw}_bank'])
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
     
        
        
    