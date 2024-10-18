import random
import time

import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from model.runelite_bot import BotStatus
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from utilities.geometry import RuneLiteObject


class OSRSBarbFisher(OSRSBot):
    def __init__(self):
        self.options_set = True
        bot_title = "Barbarian Fisher"
        description = (
            "This bot power-fish. Position your character near some trees, tag them, and press Play.\nTHIS SCRIPT IS AN EXAMPLE, DO NOT USE LONGTERM."
        )
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 180
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

        # self.log_msg("Selecting inventory...")
        # self.mouse.move_to(self.win.cp_tabs[3].random_point())
        # self.mouse.click()
        self.logs = 0

        # Main loop
        start_time = time.time()
        end_time = self.running_time * 60
        while time.time() - start_time < end_time:
            # 5% chance to take a break between tree searches
            if rd.random_chance(probability=0.05) and self.take_breaks:
                self.take_break(max_seconds=30, fancy=True)

            # 2% chance to drop logs early
            if rd.random_chance(probability=0.02):
                self.__drop_fish(api_m)

            # If inventory is full, drop logs
            #if api_m.get_is_inv_full():
            #    self.__drop_fish(api_m)

            # If our mouse isn't hovering over a tree, and we can't find another tree...
            if not self.mouseover_text(contains="Net", color=clr.OFF_WHITE) and not self.__move_mouse_to_nearest_spot():
                failed_searches += 1
                if failed_searches % 10 == 0:
                    self.log_msg("Searching for fishing spots...")
                if failed_searches > 60:
                    # If we've been searching for a whole minute...
                    self.__logout("No tagged fishing spots found. Logging out.")
                time.sleep(1)
                continue
            failed_searches = 0  # If code got here, a tree was found

            # Click if the mouseover text assures us we're clicking a tree
            if not self.mouseover_text(contains="Net", color=clr.OFF_WHITE):
                continue
            self.mouse.click()
            time.sleep(5)

            # While the player is chopping (or moving), wait
            probability = 0.10
            while not api_m.get_is_player_idle():
                # Every second there is a chance to move the mouse to the next tree, lessen the chance as time goes on
                if rd.random_chance(probability):
                    self.__move_mouse_to_nearest_spot(next_nearest=True)
                    probability /= 2
                time.sleep(1)

            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()

    def __move_mouse_to_nearest_spot(self, next_nearest=False):
        """
        Locates the nearest tree and moves the mouse to it. This code is used multiple times in this script,
        so it's been abstracted into a function.
        Args:
            next_nearest: If True, will move the mouse to the second nearest tree. If False, will move the mouse to the
                          nearest tree.
            mouseSpeed: The speed at which the mouse will move to the tree. See mouse.py for options.
        Returns:
            True if success, False otherwise.
        """
        fishing_spots = self.get_all_tagged_in_rect(self.win.game_view, clr.CYAN)
        fishing_spot = None
        if not fishing_spots:
            return False
        # If we are looking for the next nearest tree, we need to make sure trees has at least 2 elements
        if next_nearest and len(fishing_spots) < 2:
            return False
        fishing_spots = sorted(fishing_spots, key=RuneLiteObject.distance_from_rect_center)
        try:
            fishing_spot = fishing_spots[0] # if next_nearest else fishing_spots[1]
        except IndexError:
            self.log_msg("Can't find fishing spot")
            return False
        if next_nearest:
            self.mouse.move_to(fishing_spot.random_point(), mouseSpeed="slow", knotsCount=2)
        else:
            self.mouse.move_to(fishing_spot.random_point())
        return True

    def __drop_fish(self, api_m: StatusSocket):
        """
        Private function for dropping logs. This code is used in multiple places, so it's been abstracted.
        Since we made the `api` and `logs` variables assigned to `self`, we can access them from this function.
        """
        slots_trout = api_m.get_inv_item_indices(ids.LEAPING_TROUT)
        slots_salmon = api_m.get_inv_item_indices(ids.LEAPING_SALMON)
        slots_sturgeon = api_m.get_inv_item_indices(ids.LEAPING_STURGEON)
        slots = slots_trout + slots_salmon + slots_sturgeon
        time.sleep(random.randint(4, 9))
        if rd.random_chance(probability=0.75) and self.take_breaks:
            self.take_break(max_seconds=30, fancy=True)
        if rd.random_chance(probability=0.05) and self.take_breaks:
            self.take_break(max_seconds=60, fancy=True)
        self.drop(slots)
        self.logs += len(slots)
        self.log_msg(f"Fish fished: ~{self.logs}")
        time.sleep(1)
