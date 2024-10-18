import random
import time

import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.imagesearch as imsearch
import pyautogui as pag
import utilities.ocr as ocr
from model.osrs.osrs_bot import OSRSBot
from utilities.api.morg_http_client import MorgHTTPSocket

from model.osrs.rc.Location import get_location, Location

POUCH_SIZE = 40


class OSRSGOTR(OSRSBot):
    def __init__(self):
        self.game_has_ended = False
        self.compass_change = False
        self.options_set = None
        bot_title = "GOTR"
        description = ("Pouch first slot \n varrock armor second slot")
        super().__init__(bot_title=bot_title, description=description)
        # Set option variables below (initial value is only used during UI-less testing)
        self.running_time = 1
        self.start_time = 0
        self.location = None
        self.colossal_pouch = None
        self.altar = None

    def create_options(self):
        self.options_builder.add_slider_option("running_time", "How long to run (minutes)?", 1, 40)

    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return
        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        # Setup APIs
        api_m = MorgHTTPSocket()

        # Main loop
        
        
        while  self.start_time < self.running_time:
            self.first_sequence(api_m)
            self.normal_sequence(api_m)

            

        self.update_progress(1)
        self.log_msg("Finished.")
        self.stop()

    def update_pouch(self, update_value):
        self.colossal_pouch += update_value
        if self.colossal_pouch > 40:
            self.colossal_pouch = 40
        if self.colossal_pouch < 0:
            self.colossal_pouch = 0

    def wait_for_update_location(self, goal_location):
        self.log_msg(f'Location: {get_location()}')

        while get_location() != goal_location:
            time.sleep(0.3)
        self.location = goal_location
        self.log_msg(f'Destination: {get_location()}')

    # Full sequences
    def first_sequence(self, api_m: MorgHTTPSocket):
        self.log_msg("\t\t\t\t\t\t\t\tFirst sequence")
        self.colossal_pouch = 0
        self.game_has_ended = False
        self.location = get_location()
        self.guardian_remains(api_m)
        #self.activate_spec()
        while (api_m.get_inv_item_stack_amount(ids.GUARDIAN_FRAGMENTS) < 290):
            self.is_guardian_defeated(api_m)
            time.sleep(0.2)
        if api_m.get_if_item_in_inv(ids.ROBE_TOP_OF_THE_EYE):
            self.mouse.move_to(self.win.inventory_slots[1].random_point(), mouseSpeed='fastest')
            self.mouse.click()
        self.select_color2(clr.RED, 'Climb', api_m)
        self.wait_for_update_location(Location.MAIN_AREA)
        self.return_to_start(api_m)
        time.sleep(1)
        self.portal_sequence(api_m, True)

    def normal_sequence(self, api_m: MorgHTTPSocket):
        self.log_msg("\t\t\t\t\t\t\t\tGather sequence") 
        if not api_m.get_is_inv_full():
            self.get_essence_workbench(api_m)
        self.power_up_guardian(api_m)
        self.choose_guardian(api_m)
        self.click_altar(api_m)
        self.deposit_runes(api_m)
        return self.normal_sequence(api_m)

    def portal_sequence(self, api_m: MorgHTTPSocket, wait):
        self.log_msg("\t\t\t\t\t\t\t\tPortal sequence")
        self.blue_portal_sequence(api_m, wait)
        self.power_up_guardian(api_m)
        self.choose_guardian(api_m)
        self.click_altar(api_m)
        self.deposit_runes(api_m)
        self.log_msg("\t\t\t\t\t\t\t\tReturning to normal sequence")
        return self.normal_sequence(api_m)

    def power_up_guardian(self, api_m: MorgHTTPSocket):
        if api_m.get_if_item_in_inv([ids.CATALYTIC_GUARDIAN_STONE, ids.ELEMENTAL_GUARDIAN_STONE]):
            power_up = self.get_nearest_tag(clr.DARKER_YELLOW)
            while not power_up:
                self.log_msg('looking for guardian')
                power_up = self.get_nearest_tag(clr.DARKER_YELLOW)
                self.is_guardian_defeated(api_m)
                time.sleep(1)
            try:
                self.log_msg("Powering up the guardian..")
                self.mouse.move_to(power_up.random_point())
                self.mouse.click()
                api_m.wait_til_gained_xp("Runecraft", 7)
                pag.press('space')  # In case the game ends before we get to deposit the last batch
                self.is_guardian_defeated(api_m)
            except AttributeError:
                return

    def deposit_runes(self, api_m: MorgHTTPSocket):
        self.is_guardian_defeated(api_m)
        if api_m.get_if_item_in_inv(
                [ids.AIR_RUNE, ids.WATER_RUNE, ids.EARTH_RUNE, ids.FIRE_RUNE, ids.MIND_RUNE, ids.BODY_RUNE, ids.CHAOS_RUNE, ids.COSMIC_RUNE, ids.DEATH_RUNE, ids.NATURE_RUNE,
                 ids.BLOOD_RUNE, ids.LAW_RUNE, ids.BLOOD_RUNE]):
            self.log_msg("Heading to deposit runes")
            self.find_deposit(api_m)
            counter = 0
            while not self.chatbox_text_BLACK_first_line(contains=f"You deposit all of your runes into the pool"):
                if self.chatbox_text_BLACK(contains="You have no runes to deposit into the pool"):
                    self.log_msg("You had no runes to deposit")
                    break
                self.log_msg("Looking for successful deposit message")
                self.is_guardian_defeated(api_m)
                counter += 1
                time.sleep(1)
                if counter == 8:
                    self.log_msg("Counter reached 15, returning to get_essence_workbench function")
                    return self.normal_sequence(api_m)
            time.sleep(0.2)
        self.is_portal_active(api_m)

    def click_altar(self, api_m: MorgHTTPSocket):
        self.wait_for_update_location(Location.ALTAR)
        if self.game_has_ended:
            self.orange_portal(api_m)
            return
        self.log_msg(f"Successfully entered the {self.altar} altar room!!")
        if self.compass_change:
            self.set_compass_north()
            self.compass_change = False
        while not self.get_nearest_tag(clr.GREEN):
            time.sleep(0.3)
        self.is_guardian_defeated(api_m)
        if self.altar in ['fire', 'mind']:
            while not (red_path := self.get_nearest_tag(clr.RED)):
                time.sleep(0.3)
            self.mouse.move_to(red_path.random_point(), mouseSpeed='fast')
            self.mouse.click()
            time.sleep(random.randint(2000, 2300) / 1000)
        while not (altar := self.get_nearest_tag(clr.GREEN)):
            time.sleep(0.3)

        if altar:
            self.log_msg("Crafting first set of essence..")
            self.select_color2(clr.GREEN, 'Craft', api_m)
            api_m.wait_til_gained_xp("Runecraft", 10)
            self.log_msg("Crafting first set of essence..")
            #while not self.mouseover_text(contains="Craft", color=clr.OFF_WHITE):
            #    altar = self.get_nearest_tag(clr.GREEN)
            #    self.mouse.move_to(altar.random_point(), mouseSpeed='fast')
            #    time.sleep(0.2)
            #self.mouse.click()
        #api_m.wait_til_gained_xp("Runecraft", 10)
        self.empty_pouches()
        if altar:
            self.log_msg("Crafting first set of essence..")
            self.select_color2(clr.GREEN, 'Craft', api_m)
            api_m.wait_til_gained_xp("Runecraft", 10)
            self.log_msg("Crafting first set of essence..")
        #api_m.wait_til_gained_xp("Runecraft", 3)
        self.empty_pouches()
        if altar:
            self.log_msg("Crafting first set of essence..")
            self.select_color2(clr.GREEN, 'Craft', api_m)
            api_m.wait_til_gained_xp("Runecraft", 10)
            self.log_msg("Crafting first set of essence..")
        time.sleep(1.5)  # Gives enough time to let your charact

        if self.altar in ['fire', 'law']:
            if red_path := self.get_nearest_tag(clr.RED):
                self.mouse.move_to(red_path.random_point(), mouseSpeed='fast')
                self.mouse.click()
                time.sleep(random.randint(3000, 3500) / 1000)
        self.select_color2(clr.ORANGE, "Use", api_m)
        self.wait_for_update_location(Location.MAIN_AREA)
        self.altar = None
        self.log_msg("Heading back to main area..")

    def fill_pouches(self, api_m: MorgHTTPSocket):
        self.mouse.move_to(self.win.inventory_slots[0].random_point(), mouseSpeed='fastest')  # small pouch
        self.mouse.click()
        #self.mouse.move_to(self.win.inventory_slots[1].random_point(), mouseSpeed='fastest')  # medium pouch
        #self.mouse.click()
        #self.mouse.move_to(self.win.inventory_slots[2].random_point(), mouseSpeed='fastest')  # large pouch
        #self.mouse.click()

    def blue_portal_sequence(self, api_m: MorgHTTPSocket, wait):
        self.log_msg("\t\t\t\t\t\t\t\tBlue portal sequence")
        # Loop to locate blue portal
        self.is_guardian_defeated(api_m)
        portal = self.get_nearest_tag(clr.CYAN)
        if wait:
            self.log_msg("Waiting for portal to appear.")
            # Constantly check for blue portal to spawn
            counter = 0
            while not portal:
                portal = self.get_nearest_tag(clr.CYAN)
                #self.activate_spec()
                self.is_guardian_defeated(api_m)
                counter += 1
                time.sleep(1)
                if counter == 3:
                    return self.normal_sequence(api_m)
        while not self.mouseover_text(contains="Enter", color=[clr.OFF_WHITE, clr.OFF_CYAN]):
            if portal := self.get_nearest_tag(clr.CYAN):
                self.mouse.move_to(portal.random_point())
        # This sequence is for the blue portal that spawns on the east side
        if self.chatbox_text_RED(contains='A portal to the huge guardian fragment mine has opened to the east!') or self.mouseover_text(contains="EnterGuardian"):
            self.mouse.right_click()
            if enter_text := ocr.find_text("Enter Portal", self.win.game_view, ocr.BOLD_12, [clr.WHITE, clr.CYAN]):
                self.mouse.move_to(enter_text[0].random_point(), knotsCount=0)
        self.mouse.click()
        self.log_msg("Heading to huge guardian remains")
        # Counter sequence to break us out of this if we get stuck
        self.check_chatbox_blue_portal(api_m, 2)
        # Mine huge guardian essence
        while not self.get_nearest_tag(clr.RED):
            time.sleep(0.7)
        # Check if inventory is full
        if api_m.get_if_item_in_inv(ids.VARROCK_ARMOUR_1):
            self.mouse.move_to(self.win.inventory_slots[1].random_point(), mouseSpeed='fastest')
            self.mouse.click()
        remains = self.get_nearest_tag(clr.RED)
        self.mouse.move_to(remains.random_point(), mouseSpeed='fast')
        time.sleep(0.5)
        self.mouse.click()
        while not self.chatbox_text_QUEST(contains="Your inventory is too full to hold any more guardian essence"):
            self.is_guardian_defeated(api_m)
            time.sleep(1)
        self.fill_pouches(api_m)
        time.sleep(0.5)
        remains = self.get_nearest_tag(clr.RED)
        self.mouse.move_to(remains.random_point(), mouseSpeed='fast')
        time.sleep(0.5)
        self.mouse.click()
        while not self.chatbox_text_QUEST(contains="Your inventory is too full to hold any more guardian essence"):
            self.is_guardian_defeated(api_m)
            time.sleep(1)
        self.fill_pouches(api_m)
        time.sleep(1)
        remains = self.get_nearest_tag(clr.RED)
        self.mouse.move_to(remains.random_point(), mouseSpeed='fast')
        time.sleep(0.5)
        self.mouse.click()
        while not self.chatbox_text_QUEST(contains="Your inventory is too full to hold any more guardian essence"):
            self.is_guardian_defeated(api_m)
            time.sleep(1)
        if api_m.get_if_item_in_inv(ids.ROBE_TOP_OF_THE_EYE):
            self.mouse.move_to(self.win.inventory_slots[1].random_point(), mouseSpeed='fastest')
            self.mouse.click()

        self.select_color2(clr.CYAN, 'Enter', api_m)
        self.log_msg("Returning to main area...")
        time.sleep(3)
        self.check_chatbox_blue_portal(api_m, 1)
        time.sleep(2)

    def choose_altar(self):
        pillar_images = ['blood','death','fire',  'earth','water', 'air',  'nature',  'law',  'chaos', 'body','cosmic', 'mind']#

        colors = {
            'law': clr.LIGHT_PURPLE,
            'fire': clr.PINK,
            'chaos': clr.LIGHT_BROWN,
            'nature': clr.DARKER_GREEN_50,
            'mind': clr.DARK_ORANGE,
            'earth': clr.PURPLE,
            'cosmic': clr.LIGHT_RED,
            'body': clr.LIGHT_CYAN,
            'water': clr.BLUE,
            'air': clr.DARK_YELLOW,
            'death': clr.HIGH_PINK,
            'blood': clr.LIGHT_GREEN
        }

        for altar_name in pillar_images:
            pillar = imsearch.search_img_in_rect(imsearch.BOT_IMAGES.joinpath("gotr_image", f'gotr_{altar_name}.png'), self.win.game_view)
            if pillar:
                if not self.get_nearest_tag(colors[altar_name]):
                    self.compass_change = True
                    self.set_compass_east()
                    time.sleep(random.randint(2500, 3000) / 1000)
                    if not self.get_nearest_tag(colors[altar_name]):
                        continue
                self.altar = altar_name
                return altar_name, colors[altar_name]
        return None

    def choose_guardian(self, api_m: MorgHTTPSocket):
        self.is_guardian_defeated(api_m)
        self.log_msg("Picking a guardian..")
        chosen_altar = None
        while not chosen_altar:
            try:
                chosen_altar, tag_color = self.choose_altar()
            except TypeError:  # slow load
                continue
        if chosen_altar:
            self.go_to_altar(api_m, chosen_altar, tag_color)

    def go_to_altar(self, api_m: MorgHTTPSocket, chosen_altar: str, tag_color):
        self.is_guardian_defeated(api_m)
        self.log_msg(f"Going to {chosen_altar} altar")
        try:
            self.select_color2(tag_color, 'Enter', api_m)
        except (AttributeError, KeyError):
            self.log_msg(f"Could not locate {chosen_altar} pillar")
            return self.choose_guardian(api_m)

        self.is_guardian_defeated(api_m)
        while get_location() != Location.ALTAR:
            self.is_guardian_defeated(api_m)
            time.sleep(1)
            if self.chatbox_text_QUEST(contains="The Guardian is dormant. Its energy might return soon."):
                pag.press('space')
                self.log_msg("Altar was dormant. Trying again")
                self.choose_guardian(api_m)
                break

    # Mini-sequences
    def get_essence_workbench(self, api_m: MorgHTTPSocket):
        self.check_chatbox_guardian_fragment()
        self.is_guardian_defeated(api_m)
        self.log_msg("Waiting until inventory is full..")
        self.work_at_bench(api_m)
        api_m.wait_til_gained_xp("Crafting", 5)
        self.workbench_is_inv_full(api_m)
        pag.press('space')
        self.fill_pouches(api_m)
        self.log_msg("Waiting until inventory is full #2..")
        self.work_at_bench(api_m)
        self.workbench_is_inv_full(api_m)
        pag.press('space')
        self.fill_pouches(api_m)
        time.sleep(1)
        self.log_msg("Waiting until inventory is full #3..")
        self.work_at_bench(api_m)
        while not self.chatbox_text_QUEST(contains="Your inventory is too full to hold any more essence"):
            self.is_guardian_defeated(api_m)
            if self.chatbox_text_BLACK_first_line(contains="You have no more guardian fragments to combine"):
                break
            time.sleep(1)
        pag.press('space')

    def is_portal_active(self, api_m: MorgHTTPSocket):
        if self.get_nearest_tag(clr.CYAN) and api_m.get_inv_item_stack_amount(ids.GUARDIAN_FRAGMENTS) > 50:
            return self.portal_sequence(api_m, False)

    def workbench_is_inv_full(self, api_m: MorgHTTPSocket):
        while not self.chatbox_text_QUEST(contains="Your inventory is too full to hold any more essence"):
            self.is_portal_active(api_m)
            if self.chatbox_text_GREEN(contains="The Great Guardian"):
                self.power_up_guardian(api_m)
                break
            self.is_guardian_defeated(api_m)
            if self.chatbox_text_BLACK_first_line(contains="You have no more guardian fragments to combine"):
                break
            time.sleep(1)

    def huge_guardian_remains_is_inv_full(self, api_m):
        while not self.chatbox_text_QUEST(contains="Your inventory is too full to hold any more guardian essence"):
            self.is_guardian_defeated(api_m)
            time.sleep(1)

    def is_guardian_active(self):
        while not self.chatbox_text_RED(contains="The rift becomes active!"):
            self.log_msg("Waiting for new game to start..")
            time.sleep(1)

    def is_guardian_defeated(self, api_m : MorgHTTPSocket):
        
        game_ended_img = imsearch.BOT_IMAGES.joinpath("gotr_image", "game_ended.png")
        if self.chatbox_text_GREEN(contains="The Great Guardian") or self.chatbox_text_RED(contains="defeated") or imsearch.search_img_in_rect(game_ended_img, self.win.game_view):
            self.log_msg("Game has ended.")
            self.game_has_ended = True
            self.start_time += 1
            self.update_progress(self.start_time/self.running_time)
            if self.compass_change:
                self.compass_change = False
                self.set_compass_north()
            
            guardian = imsearch.BOT_IMAGES.joinpath("gotr_image", "gotr_guardian.png")
            while not imsearch.search_img_in_rect(guardian, self.win.game_view):
                time.sleep(1)
            while not api_m.get_is_player_idle(1):
                time.sleep(0.5)
            time.sleep(0.5)                
            self.location = get_location()
            #self.repair_pouches(api_m)
            if self.start_time >= self.running_time:
                return self.main_loop()    
            match self.location:
                case Location.MAIN_AREA:
                    self. return_to_start(api_m)
                case Location.LEFT_AREA:
                    self.blue_portal(api_m)
                    time.sleep(5)
                case Location.RIGHT_AREA:
                    return self.main_loop()
                case Location.ALTAR:
                    self.orange_portal(api_m)
                    time.sleep(5)
                case _:
                    self.return_to_start(api_m)
            self.wait_for_update_location(Location.MAIN_AREA)
            self.top_rubble(api_m)
            time.sleep(1)
            self.is_guardian_active()
            #self.repair_pouches(api_m)
            return self.main_loop()

    def check_chatbox_guardian_fragment(self):
        while self.chatbox_text_QUEST("You'll need at least one guardian fragment to craft guardian essence."):
            time.sleep(1)
            pag.press('space')

    def check_chatbox_blue_portal(self, api_m: MorgHTTPSocket, location):
        portal_active = imsearch.BOT_IMAGES.joinpath("gotr_image", "gotr_portal.png")
        guardian = imsearch.BOT_IMAGES.joinpath("gotr_image", "gotr_guardian.png")

        self.log_msg("Moving to 'another part of the temple' after clicking blue portal")
        while imsearch.search_img_in_rect(guardian, self.win.game_view) and imsearch.search_img_in_rect(portal_active, self.win.game_view):
            if get_location() != location:
                time.sleep(1)
            else:
                while not imsearch.search_img_in_rect(guardian, self.win.game_view):
                    time.sleep(1)
                self.location = location
                return
        if imsearch.search_img_in_rect(guardian, self.win.game_view) and not imsearch.search_img_in_rect(portal_active, self.win.game_view):
            return self.normal_sequence(api_m)

    # Smaller functions
    def activate_spec(self):
        spec_energy = self.get_special_energy()
        if spec_energy >= 100:
            self.mouse.move_to(self.win.spec_orb.random_point())
            self.mouse.click()

    def empty_pouches(self):
        pag.keyDown('shift')
        self.mouse.move_to(self.win.inventory_slots[0].random_point(), mouseSpeed='fastest')  # small(colisial) pouch 
        self.mouse.click()
        #self.mouse.move_to(self.win.inventory_slots[1].random_point(), mouseSpeed='fastest')  # medium pouch
        #self.mouse.click()
        #self.mouse.move_to(self.win.inventory_slots[2].random_point(), mouseSpeed='fastest')  # large pouch
        #self.mouse.click()
        pag.keyUp('shift')

    def find_deposit(self, api_m):
        while not self.get_nearest_tag(clr.DARK_BLUE):
            time.sleep(0.1)
        self.is_portal_active(api_m)
        self.select_color2(clr.DARK_BLUE, 'Deposit', api_m)

    def work_at_bench(self, api_m):
        self.log_msg("Converting fragments to essence..")
        self.select_color2(clr.DARK_PURPLE, 'Work', api_m)

    def guardian_remains(self, api_m: MorgHTTPSocket):
        if get_location() != Location.RIGHT_AREA:
            self.top_rubble(api_m)
            self.is_guardian_defeated(api_m)
        self.is_guardian_active()
        self.log_msg("Mining guardian fragments")
        if api_m.get_if_item_in_inv(ids.VARROCK_ARMOUR_1):
            self.mouse.move_to(self.win.inventory_slots[1].random_point(), mouseSpeed='fastest')
            self.mouse.click()
        remains = self.get_nearest_tag(clr.YELLOW)
        self.mouse.move_to(remains.random_point(), mouseSpeed='fast')
        time.sleep(0.5)
        self.mouse.click()
        api_m.wait_til_gained_xp('Mining', 10)
        self.is_guardian_defeated(api_m)

    def return_to_start(self, api_m):
        if self.location == Location.LEFT_AREA:
            self.blue_portal(api_m)
            time.sleep(2)
        self.power_up_guardian(api_m)
        time.sleep(2)
        if return_to_start := self.get_nearest_tag(clr.DARKER_GREEN):
            self.mouse.move_to(return_to_start.random_point())
            self.mouse.click()
        time.sleep(2)

    def orange_portal(self, api_m):
        if red_path := self.get_nearest_tag(clr.RED):
            self.mouse.move_to(red_path.random_point(), mouseSpeed='fast')
            self.mouse.click()
            time.sleep(random.randint(2000, 2300) / 1000)
        self.select_color2(clr.ORANGE, 'Use', api_m)
        self.log_msg("Heading back to main area..")
        self.wait_for_update_location(Location.MAIN_AREA)

    def blue_portal(self, api_m):
        if self.get_nearest_tag(clr.CYAN):
            self.select_color2(clr.CYAN, 'Enter', api_m)
            self.wait_for_update_location(Location.LEFT_AREA)

    def  top_rubble(self, api_m):
        portal_active = imsearch.BOT_IMAGES.joinpath("gotr_image", "gotr_portal.png")
        while imsearch.search_img_in_rect(portal_active, self.win.game_view) or self.get_nearest_tag(clr.CYAN):
            time.sleep(1)
        walk = imsearch.BOT_IMAGES.joinpath("gotr_image", "walk.png")
        while not (next_rubble := imsearch.search_img_in_rect(walk, self.win.game_view)):
            time.sleep(1)
        self.mouse.move_to(next_rubble.random_point(), mouseSpeed='fast')
        self.mouse.click()
        
        time.sleep(random.randint(7000, 9000) / 1000)
        self.pink_rock()
        time.sleep(random.randint(2000, 3000) / 1000)
        if 'I can' in api_m.get_latest_chat_message():
            self.pink_rock()
        time.sleep(10)
        self.repair_pouches(api_m)
        


    def pink_rock(self):
        pink_rock_image = imsearch.BOT_IMAGES.joinpath("gotr_image", "pink_rock.png")
        while not self.mouseover_text(contains="Climb", color=clr.OFF_WHITE):
            if rock_found := imsearch.search_img_in_rect(pink_rock_image, self.win.game_view):
                self.mouse.move_to(rock_found.random_point(), mouseSpeed='fast')
            time.sleep(0.7)
        self.mouse.click()
        

    def repair_pouches(self, api_m: MorgHTTPSocket):
        if api_m.get_if_item_in_inv(ids.MEDIUM_POUCH_5511) or api_m.get_if_item_in_inv(ids.LARGE_POUCH_5513) or api_m.get_if_item_in_inv(ids.GIANT_POUCH_5515) or api_m.get_if_item_in_inv(ids.COLOSSAL_POUCH_26786):
            spellbook_tab = self.win.cp_tabs[6]
            self.mouse.move_to(spellbook_tab.random_point())
            self.mouse.click()
            npc_contact_img = imsearch.BOT_IMAGES.joinpath("gotr_image", "npc_contact_on.png")
            npc_contact = imsearch.search_img_in_rect(npc_contact_img, self.win.control_panel)
            self.mouse.move_to(npc_contact.random_point())
            self.mouse.right_click()
            time.sleep(0.3)
            if enter_text := ocr.find_text("Dark Mage NPC Contact", self.win.control_panel, ocr.BOLD_12, [clr.WHITE, clr.GREEN]):
                self.mouse.move_to(enter_text[0].random_point(), knotsCount=0)
            self.mouse.click()
            time.sleep(1)
            api_m.wait_til_gained_xp('Magic', 10)
            pag.press('space')
            time.sleep(1)
            pag.press('2')
            time.sleep(1)
            pag.press('space')
            time.sleep(1)
            self.mouse.move_to(self.win.cp_tabs[3].random_point())
            self.mouse.click()
            time.sleep(2)
            self.mouse.move_to(self.win.inventory_slots[1].random_point(), mouseSpeed='fastest')
            self.mouse.click()
            time.sleep(1)