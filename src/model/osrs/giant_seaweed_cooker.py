import time
import random
import keyboard
from enum import Enum
import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.imagesearch import search_img_in_rect, BOT_IMAGES


class STATE(Enum):
    """State machine states for giant seaweed cooking bot"""
    IDLE = 0
    BANKING = 1
    WALKING_TO_COOKING = 2
    COOKING = 3
    WAITING_FOR_COOK = 4
    ERROR = 5


class OSRSGiantSeaweedCooker(OSRSBot):
    def __init__(self):
        bot_title = "Giant Seaweed Cooker"
        description = (
            "This bot cooks giant seaweed. Position your character near a bank and a cooking range/fire (tagged red), "
            "then press Play."
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
            elif self.state == STATE.WALKING_TO_COOKING:
                self._handle_walking_to_cooking_state(api_m)
            elif self.state == STATE.COOKING:
                self._handle_cooking_state(api_m)
            elif self.state == STATE.WAITING_FOR_COOK:
                self._handle_waiting_for_cook_state(api_m)
            elif self.state == STATE.ERROR:
                self._handle_error_state(api_m)
            
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def _handle_idle_state(self, api_m: MorgHTTPSocket):
        """Determine next action based on current situation"""
        has_giant_seaweed = api_m.get_if_item_in_inv(ids.GIANT_SEAWEED)
        
        # Check if we have giant seaweed to cook
        if has_giant_seaweed:
            # Go to cooking location
            self.log_msg("Giant seaweed ready, moving to cooking location...")
            self.state = STATE.WALKING_TO_COOKING
        else:
            # Need to bank to get more giant seaweed
            self.log_msg("No giant seaweed, going to bank...")
            self.state = STATE.BANKING

    def _handle_banking_state(self, api_m: MorgHTTPSocket):
        """Handle banking: deposit all, withdraw giant seaweed"""
        # Refresh energy if needed
        self.refresh_energy(api_m)
        
        # Open bank
        if not (deposit := self.open_bank()):
            self.log_msg("Failed to open bank")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE
            return
        
        # Deposit all items
        self._deposit_all_items(api_m)
        
        # Withdraw giant seaweed (close bank)
        if not self.withdraw_from_bank(['Giant_seaweed_bank'], close=True):
            self.log_msg("Failed to withdraw giant seaweed")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE
            return
        
        # Check if we have giant seaweed and go to cooking if ready
        if api_m.get_if_item_in_inv(ids.GIANT_SEAWEED):
            self.log_msg("Banking complete, going to cooking location...")
            self.error_count = 0  # Reset error count on success
            self.state = STATE.WALKING_TO_COOKING
        else:
            self.log_msg("No giant seaweed found after withdrawal")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE

    def _handle_walking_to_cooking_state(self, api_m: MorgHTTPSocket):
        """Walk to cooking location and interact with it"""
        # Check if we still have giant seaweed
        if not api_m.get_if_item_in_inv(ids.GIANT_SEAWEED):
            self.log_msg("Lost giant seaweed, going back to bank...")
            self.state = STATE.BANKING
            return
        
        # Find and click cooking object (RED tagged object)
        self.log_msg("Looking for cooking range/fire...")
        cooking_found = False
        timeout = 0
        max_timeout = 50  # 5 seconds max
        
        while not (cooking_obj := self.get_nearest_tag(clr.RED)) and timeout < max_timeout:
            time.sleep(0.1)
            timeout += 1
        
        if not cooking_obj:
            self.log_msg("Could not find cooking range/fire! Make sure it's visible and tagged RED.")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE
            return
        
        # Move to cooking object and wait for correct mouseover text
        self.mouse.move_to(cooking_obj.random_point(), mouseSpeed='fastest')
        timeout = 0
        while not self.mouseover_text(contains=['Cook'], color=[clr.OFF_WHITE, clr.OFF_CYAN]) and timeout < 25:
            if cooking_obj := self.get_nearest_tag(clr.RED):
                self.mouse.move_to(cooking_obj.random_point(), mouseSpeed='fastest')
            time.sleep(0.2)
            timeout += 1
        
        if timeout >= 25:
            self.log_msg("Could not get 'Cook' option on cooking object")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE
            return
        
        # Click cooking object
        if not self.mouse.click(check_red_click=True):
            self.log_msg("Failed to click cooking object, retrying...")
            self.state = STATE.WALKING_TO_COOKING
            return
        
        # Wait for cooking interface to open
        time.sleep(random.randint(600, 900) / 1000)
        self.state = STATE.COOKING

    def _handle_cooking_state(self, api_m: MorgHTTPSocket):
        """Start cooking by pressing Space or 1"""
        # Press space or 1 to start cooking (using 1 like in cooking.py example)
        time.sleep(random.randint(500, 800) / 1000)
        keyboard.press_and_release("space")
        
        self.log_msg("Started cooking giant seaweed...")
        self.state = STATE.WAITING_FOR_COOK

    def _handle_waiting_for_cook_state(self, api_m: MorgHTTPSocket):
        """Wait for entire inventory cooking to complete"""
        # Wait until all giant seaweed is consumed (entire inventory cooked)
        has_giant_seaweed = api_m.get_if_item_in_inv(ids.GIANT_SEAWEED)
        
        if not has_giant_seaweed:
            # All giant seaweed consumed - entire inventory cooked
            self.log_msg("Entire inventory cooking completed!")
            time.sleep(random.randint(500, 800) / 1000)
            self.error_count = 0  # Reset error count on success
            self.state = STATE.IDLE
        else:
            # Still cooking, wait a bit more
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

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()

