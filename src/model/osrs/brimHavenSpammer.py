import time
import random

import utilities.color as clr
from model.osrs.osrs_bot import OSRSBot
from utilities.geometry import RuneLiteObject


class OSRSRandomYellowClicker(OSRSBot):
    def __init__(self):
        bot_title = "yellow_clicker"
        description = "Randomly clicks yellow-tagged tiles every 0.6–1.8 seconds."
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 60  # default in minutes
        self.take_breaks = False

    def create_options(self):
        self.options_builder.add_slider_option(
            "running_time",
            "How long to run (minutes)?",
            1,
            500,
        )
        self.options_builder.add_checkbox_option(
            "take_breaks",
            "Take breaks?",
            [" "],
        )

    def save_options(self, options: dict):
        for option in options:
            if option == "running_time":
                self.running_time = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")
                print(
                    "Developer: ensure that the option keys are correct, "
                    "and that options are being unpacked correctly."
                )
                self.options_set = False
                return

        self.log_msg(f"Running time: {self.running_time} minutes.")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks.")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        start_time = time.time()
        end_time = self.running_time * 60

        self.log_msg("Starting yellow clicker...")
        self.log_msg("Make sure your yellow tags are visible in the game view.")

        while time.time() - start_time < end_time:
            # Optional random break
            if self.take_breaks and random.random() < 0.03:  # ~3% chance
                self.take_break(max_seconds=30, fancy=True)

            # Find all yellow-tagged objects in the game view
            yellow_objs = self.get_all_tagged_in_rect(self.win.game_view, clr.YELLOW)

            if yellow_objs:
                # Randomly choose one of the yellow objects
                yellow_objs = sorted(
                    yellow_objs, key=RuneLiteObject.distance_from_rect_center
                )
                target = random.choice(yellow_objs)

                # Move and click
                self.mouse.move_to(target.random_point())
                self.mouse.click()
            else:
                # If nothing is tagged yellow, small idle pause
                self.log_msg("No yellow tags found in game view.")
                time.sleep(0.5)

            # Random delay between clicks: 0.6–1.8s
            delay = random.uniform(0.6, 1.8)
            time.sleep(delay)

            # Progress bar
            self.update_progress((time.time() - start_time) / end_time)

        self.update_progress(1)
        self.__logout("Finished yellow clicking.")

    def __logout(self, msg: str):
        self.log_msg(msg)
        self.logout()
        self.stop()
