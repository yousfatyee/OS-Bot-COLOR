import random
import time
import keyboard
from enum import Enum
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


class STATE(Enum):
    """State machine states for glass smithing bot"""
    IDLE = 0
    BANKING = 1
    WALKING_TO_FURNACE = 2
    SMELTING = 3
    WAITING_FOR_SMELT = 4
    ERROR = 5


class OSRSGlassSmither(OSRSBot):
    def __init__(self):
        self.clay = None
        self.options_set = True
        bot_title = "glass smither"
        description = (
            "edgevile glass smither"
        )
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 240
        self.take_breaks = True
        self.state = STATE.IDLE
        self.error_count = 0
        self.max_errors = 5

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
        self.state = STATE.IDLE
        
        while time.time() - start_time < end_time:
            # Handle breaks
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=120, fancy=True)
            
            # State machine
            if self.state == STATE.IDLE:
                self._handle_idle_state(api_m)
            elif self.state == STATE.BANKING:
                self._handle_banking_state(api_m)
            elif self.state == STATE.WALKING_TO_FURNACE:
                self._handle_walking_to_furnace_state(api_m)
            elif self.state == STATE.SMELTING:
                self._handle_smelting_state(api_m)
            elif self.state == STATE.WAITING_FOR_SMELT:
                self._handle_waiting_for_smelt_state(api_m)
            elif self.state == STATE.ERROR:
                self._handle_error_state(api_m)
            
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def _handle_idle_state(self, api_m: MorgHTTPSocket):
        """Determine next action based on current situation"""
        has_soda_ash = api_m.get_if_item_in_inv(ids.SODA_ASH)
        has_sand = api_m.get_if_item_in_inv(ids.BUCKET_OF_SAND)
        
        # Check if we have both materials
        if has_soda_ash and has_sand:
            # Skip idle check - just go to furnace immediately if we have materials
            # The idle check was causing delays. We'll check idle state in walking_to_furnace if needed.
            self.log_msg("Materials ready, moving to furnace...")
            self.state = STATE.WALKING_TO_FURNACE
        else:
            # Missing materials, need to bank
            self.log_msg("Missing materials, going to bank...")
            self.state = STATE.BANKING

    def _handle_banking_state(self, api_m: MorgHTTPSocket):
        """Handle banking: deposit all, withdraw materials"""
        # Refresh energy if needed
        self.refresh_energy(api_m)
        
        # Open bank
        self.open_bank()
        
        # Deposit all items
        self._deposit_all_items(api_m)
        
        # Withdraw soda ash (keep bank open)
        self.withdraw_from_bank(['Soda_ash_bank'], close=False)
        
        # Withdraw bucket of sand (close bank)
        self.withdraw_from_bank(['Bucket_of_sand_bank'], close=True)
        
        
        # Check if we have materials and go directly to furnace if ready
        if api_m.get_if_item_in_inv(ids.SODA_ASH) and api_m.get_if_item_in_inv(ids.BUCKET_OF_SAND):
            self.log_msg("Banking complete, going to furnace...")
            self.state = STATE.WALKING_TO_FURNACE
        else:
            self.state = STATE.IDLE

    def _handle_walking_to_furnace_state(self, api_m: MorgHTTPSocket):
        """Walk to furnace and interact with it"""
        # Check if we still have materials
        if not (api_m.get_if_item_in_inv(ids.SODA_ASH) and api_m.get_if_item_in_inv(ids.BUCKET_OF_SAND)):
            self.log_msg("Lost materials, going back to bank...")
            self.state = STATE.BANKING
            return
        
        # Find and click furnace (RED tagged object)
        self.log_msg("Looking for furnace...")
        furnace_found = False
        timeout = 0
        max_timeout = 50  # 5 seconds max
        
        while not (furnace := self.get_nearest_tag(clr.RED)) and timeout < max_timeout:
            time.sleep(0.1)
            timeout += 1
        
        if not furnace:
            self.log_msg("Could not find furnace! Make sure it's visible and tagged RED.")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE
            return
                
        # Move to furnace and wait for correct mouseover text
        self.mouse.move_to(furnace.random_point(), mouseSpeed='fastest')
        timeout = 0
        while not self.mouseover_text(contains=['Smelt'], color=[clr.OFF_WHITE, clr.OFF_CYAN]) and timeout < 25:
            if furnace := self.get_nearest_tag(clr.RED):
                self.mouse.move_to(furnace.random_point(), mouseSpeed='fastest')
            time.sleep(0.2)
            timeout += 1
        
        if timeout >= 25:
            self.log_msg("Could not get 'Smelt' option on furnace")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE
            return
        
        # Click furnace
        if not self.mouse.click(check_red_click=True):
            self.log_msg("Failed to click furnace, retrying...")
            self.state = STATE.WALKING_TO_FURNACE
            return
        
        # Wait for smelting interface to open
        time.sleep(random.randint(600, 900) / 1000)
        self.state = STATE.SMELTING

    def _handle_smelting_state(self, api_m: MorgHTTPSocket):
        """Start smelting by pressing Space"""
        # Check if smelting interface is open (check for "Make" text or similar)
        # For now, just press space after a short delay
        time.sleep(random.randint(5000, 5500) / 1000)
        keyboard.press_and_release("Space")
        
        
        self.log_msg("Started smelting...")
        self.state = STATE.WAITING_FOR_SMELT

    def _handle_waiting_for_smelt_state(self, api_m: MorgHTTPSocket):
        """Wait for entire inventory smelting to complete"""
        # Wait until all materials are consumed (entire inventory smelted)
        has_soda_ash = api_m.get_if_item_in_inv(ids.SODA_ASH)
        has_sand = api_m.get_if_item_in_inv(ids.BUCKET_OF_SAND)
        
        if not has_soda_ash and not has_sand:
            # All materials consumed - entire inventory smelted
            self.log_msg("Entire inventory smelting completed!")
            time.sleep(random.randint(500, 800) / 1000)
            self.error_count = 0  # Reset error count on success
            self.state = STATE.IDLE
        else:
            # Still smelting, wait a bit more
            time.sleep(0.3)

    def _handle_error_state(self, api_m: MorgHTTPSocket):
        """Handle error state - log and stop"""
        self.log_msg("Too many errors encountered. Stopping bot.")
        self.__logout("Stopped due to errors.")

    def _deposit_all_items(self, api_m: MorgHTTPSocket) -> bool:
        """Deposit all items in inventory. Returns True if successful."""
        retry = 0
        max_retries = 50
        
        # Wait for bank interface to be fully open
        while not (bank_all := search_img_in_rect(BOT_IMAGES.joinpath("bank", "bankall.png"), self.win.game_view)):
            time.sleep(0.1)
            retry += 1
            if retry >= max_retries:
                self.log_msg("Timeout waiting for bank deposit button")
                return False
        
        # Click deposit all button
        self.log_msg("Depositing all items...")
        self.mouse.move_to(bank_all.random_point())
        self.mouse.click()
        time.sleep(random.randint(600, 940) / 1000)
        
        # Verify items were deposited (inventory should be mostly empty)
        time.sleep(0.3)
        return True

    def refresh_energy(self, api_m: MorgHTTPSocket):
        """Refresh run energy if needed"""
        if api_m.get_run_energy() > 5000:
            self.toggle_run(True)
            # Optional: Use stamina potion if available
            # self.withdraw_from_bank([f'Stamina_potion_bank'], False)
            # while not (stamina := search_img_in_rect(BOT_IMAGES.joinpath("items", 'Stamina_potion.png'), self.win.control_panel)):
            #     time.sleep(0.1)
            # self.mouse.move_to(stamina.random_point(), mouseSpeed='fastest')
            # keyboard.press('shift')
            # self.mouse.click()
            # keyboard.release('shift')

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()

    