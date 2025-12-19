import time
from enum import Enum
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
from utilities.geometry import RuneLiteObject
import random
from utilities.imagesearch import search_img_in_rect, BOT_IMAGES


class STATE(Enum):
    """State machine states for mining bot"""
    IDLE = 0
    WAITING_FOR_IDLE = 1
    DROPPING_WATER_SKINS = 2
    DEPOSITING_AT_GRINDER = 3
    MOVING_TO_TILE = 4
    FINDING_ROCK = 5
    MINING = 6
    ERROR = 7


class OSRSMiner(OSRSBot):
    def __init__(self):
        bot_title = "Miner"
        description = (
            "This bot power-mines rocks. Position your character near some rocks, tag them (PINK/CYAN/WHITE), "
            "tag the grinder (RED), and tag movement tiles (GREEN), then press Play.\nTHIS SCRIPT IS AN EXAMPLE, DO NOT USE LONGTERM."
        )
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 1
        self.take_breaks = False
        self.state = STATE.IDLE
        self.error_count = 0
        self.max_errors = 5
        self.failed_searches = 0
        self.max_failed_searches = 70
    
    def _get_random_mouse_speed(self):
        """Returns a random mouse speed with higher probability for fast/fastest"""
        # Weighted random: 40% fastest, 35% fast, 15% medium, 7% slow, 3% slowest
        rand = random.random()
        if rand < 0.40:
            return "fastest"
        elif rand < 0.75:
            return "fast"
        elif rand < 0.90:
            return "medium"
        elif rand < 0.97:
            return "slow"
        else:
            return "slowest"

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
                self.take_break(max_seconds=30, fancy=True)
            
            # State machine
            if self.state == STATE.IDLE:
                self._handle_idle_state(api_m)
            elif self.state == STATE.WAITING_FOR_IDLE:
                self._handle_waiting_for_idle_state(api_m)
            elif self.state == STATE.DROPPING_WATER_SKINS:
                self._handle_dropping_water_skins_state(api_m)
            elif self.state == STATE.DEPOSITING_AT_GRINDER:
                self._handle_depositing_at_grinder_state(api_m)
            elif self.state == STATE.MOVING_TO_TILE:
                self._handle_moving_to_tile_state(api_m)
            elif self.state == STATE.FINDING_ROCK:
                self._handle_finding_rock_state(api_m)
            elif self.state == STATE.MINING:
                self._handle_mining_state(api_m)
            elif self.state == STATE.ERROR:
                self._handle_error_state(api_m)
            
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def _handle_idle_state(self, api_m: MorgHTTPSocket):
        """Determine next action based on current situation"""
        # Check for water skins to drop
        if api_m.get_if_item_in_inv(ids.WATERSKIN0):
            self.log_msg("Dropping water skins...")
            self.state = STATE.DROPPING_WATER_SKINS
            return
        
        # Check if inventory is full - need to deposit at grinder
        if api_m.get_is_inv_full():
            self.log_msg("Inventory full, going to grinder...")
            self.state = STATE.DEPOSITING_AT_GRINDER
            return
        
        # Skip blocking idle check - go directly to finding rock
        # The idle check was causing delays. We'll check idle state in mining if needed.
        self.state = STATE.FINDING_ROCK

    def _handle_waiting_for_idle_state(self, api_m: MorgHTTPSocket):
        """Wait for player to become idle with timeout"""
        timeout = 0
        max_timeout = 100  # 10 seconds max (0.1s * 100)
        
        while not api_m.get_is_player_idle() and timeout < max_timeout:
            time.sleep(0.1)
            timeout += 1
        
        if timeout >= max_timeout:
            self.log_msg("Timeout waiting for player to become idle")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE
        else:
            self.state = STATE.IDLE

    def _handle_dropping_water_skins_state(self, api_m: MorgHTTPSocket):
        """Drop water skins from inventory"""
        if not self._drop_water_skins(api_m):
            self.log_msg("Failed to drop water skins")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE
        else:
            self.error_count = 0
            self.state = STATE.IDLE

    def _handle_depositing_at_grinder_state(self, api_m: MorgHTTPSocket):
        """Deposit items at the grinder"""
        # Use shorter poll time for idle check
        if not api_m.get_is_player_idle(0.5):
            # Player still doing something, wait briefly
            time.sleep(0.2)
            return
        
        # Find grinder (RED tagged)
        if not self._move_to_grinder():
            self.log_msg("Could not find grinder, trying to move to tile...")
            self.state = STATE.MOVING_TO_TILE
            return
        
        # Reduced delay for faster movement
        time.sleep(random.randint(150, 250) / 1000)
        
        # Verify we're over the grinder with correct text
        if not self.mouseover_text(contains="Deposit", color=clr.OFF_WHITE):
            self.log_msg("Not over grinder, retrying...")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.DEPOSITING_AT_GRINDER
            return
        
        # Click to deposit
        self.log_msg("Depositing at grinder...")
        self.mouse.click()
        
        # Wait for deposit to complete
        timeout = 0
        max_timeout = 50
        while not api_m.get_is_player_idle() and timeout < max_timeout:
            time.sleep(0.1)
            timeout += 1
        
        if timeout >= max_timeout:
            self.log_msg("Timeout waiting for deposit to complete")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.IDLE
        else:
            self.log_msg("Deposit completed!")
            self.error_count = 0
            self.state = STATE.IDLE

    def _handle_moving_to_tile_state(self, api_m: MorgHTTPSocket):
        """Move to a further tile to reposition"""
        if not self._move_to_further_tile():
            self.log_msg("Could not find movement tile")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                # Try to find rocks anyway
                self.state = STATE.FINDING_ROCK
            return
        
        # Click the tile to move
        self.log_msg("Moving to tile...")
        self.mouse.click()
        time.sleep(random.randint(800, 1200) / 1000)  # Reduced from 1500-2000ms
        
        # Wait for movement to complete (optimized with shorter poll)
        timeout = 0
        max_timeout = 30  # Reduced from 50
        while not api_m.get_is_player_idle(0.3) and timeout < max_timeout:
            time.sleep(0.1)
            timeout += 1
        
        self.error_count = 0
        self.state = STATE.FINDING_ROCK

    def _handle_finding_rock_state(self, api_m: MorgHTTPSocket):
        """Find and move mouse to nearest rock"""
        # Try to find nearest rock
        if not self._move_mouse_to_nearest_rock(dontMove=False):
            # No rocks found, try moving to a tile
            self.log_msg("No rocks found, trying to reposition...")
            self.failed_searches += 1
            
            if self.failed_searches % 10 == 0:
                self.log_msg("Searching for rocks...")
            
            if self.failed_searches > self.max_failed_searches:
                self.__logout("No tagged rocks found after many attempts. Logging out.")
                return
            
            self.state = STATE.MOVING_TO_TILE
            return
        
        # Reduced delay for faster movement
        time.sleep(random.randint(100, 200) / 1000)
        
        # Verify we're over a rock with correct text (quick check)
        if not self.mouseover_text(contains="Mine", color=clr.OFF_WHITE):
            self.log_msg("Not over rock, retrying...")
            self.failed_searches += 1
            if self.failed_searches > self.max_failed_searches:
                self.__logout("No tagged rocks found. Logging out.")
                return
            self.state = STATE.FINDING_ROCK
            return
        
        # Reset failed searches on success
        self.failed_searches = 0
        self.state = STATE.MINING

    def _handle_mining_state(self, api_m: MorgHTTPSocket):
        """Click on rock to start mining"""
        # Use shorter poll time for idle check
        if not api_m.get_is_player_idle(0.5):
            # Player still doing something, wait briefly
            time.sleep(0.2)
            return
        
        # Verify we're still over a rock
        if not self.mouseover_text(contains="Mine", color=clr.OFF_WHITE):
            self.log_msg("Lost rock, finding new one...")
            self.state = STATE.FINDING_ROCK
            return
        
        # Click to mine
        self.log_msg("Mining rock...")
        self.mouse.click()
        time.sleep(random.randint(600, 1200) / 1000)
        
        # Wait for mining to start
        timeout = 0
        max_timeout = 20
        while api_m.get_is_player_idle() and timeout < max_timeout:
            time.sleep(0.1)
            timeout += 1
        
        if timeout >= max_timeout:
            self.log_msg("Mining didn't start, retrying...")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                self.state = STATE.ERROR
            else:
                self.state = STATE.FINDING_ROCK
        else:
            self.error_count = 0
            # Mining started, wait for it to complete
            self.state = STATE.WAITING_FOR_IDLE

    def _handle_error_state(self, api_m: MorgHTTPSocket):
        """Handle error state - log and stop"""
        self.log_msg("Too many errors encountered. Stopping bot.")
        self.__logout("Stopped due to errors.")

    def _move_to_further_tile(self) -> bool:
        """Move to the furthest tile (GREEN tagged). Returns True if successful."""
        tiles = self.get_all_tagged_in_rect(self.win.game_view, clr.GREEN)
        if not tiles:
            return False
        tiles = sorted(tiles, key=RuneLiteObject.distance_from_rect_center)
        tile = tiles[-1]  # Get furthest tile (last in sorted list)
        self.mouse.move_to(tile.random_point(), mouseSpeed=self._get_random_mouse_speed())
        return True
    
    def _move_to_grinder(self) -> bool:
        """Move mouse to grinder (RED tagged). Returns True if successful."""
        grinder = self.get_all_tagged_in_rect(self.win.game_view, clr.RED)
        if not grinder:
            return False
        self.mouse.move_to(grinder[0].random_point(), mouseSpeed=self._get_random_mouse_speed(), knotsCount=1)
        return True
            
    def _move_mouse_to_nearest_rock(self, next_nearest=False, dontMove=False) -> bool:
        """
        Locates the nearest rock and moves the mouse to it.
        Args:
            next_nearest: If True, will move the mouse to the second nearest rock.
            dontMove: If True, only finds the rock but doesn't move mouse.
        Returns:
            True if success, False otherwise.
        """
        rocks1 = self.get_all_tagged_in_rect(self.win.game_view, clr.PINK)
        rocks2 = self.get_all_tagged_in_rect(self.win.game_view, clr.CYAN)
        rocks = rocks1 + rocks2
        
        if not rocks:
            rocks = self.get_all_tagged_in_rect(self.win.game_view, clr.WHITE)
            if not rocks:
                return False
        
        # If we are looking for the next nearest rock, we need to make sure rocks has at least 2 elements
        if next_nearest and len(rocks) < 2:
            return False
        
        rocks = sorted(rocks, key=RuneLiteObject.distance_from_rect_center)
        rock = rocks[1] if next_nearest else rocks[0]
        
        if not dontMove:
            speed = self._get_random_mouse_speed()
            if next_nearest:
                self.mouse.move_to(rock.random_point(), mouseSpeed=speed, knotsCount=1)
            else:
                self.mouse.move_to(rock.random_point(), mouseSpeed=speed)
        
        return True
            
    def _drop_water_skins(self, api_m: MorgHTTPSocket) -> bool:
        """
        Drop water skins from inventory.
        Returns True if successful, False otherwise.
        """
        try:
            slots = api_m.get_inv_item_indices(ids.WATERSKIN0)
            if not slots:
                return True  # No water skins to drop, consider success
            self.drop(slots)
            time.sleep(random.randint(800, 1200) / 1000)
            return True
        except Exception as e:
            self.log_msg(f"Error dropping water skins: {e}")
            return False

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()
