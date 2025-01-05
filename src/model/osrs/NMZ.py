import random
import re
import time

import utilities.api.item_ids as ids
import utilities.color as clr
import utilities.random_util as rd
from model.osrs.osrs_bot import OSRSBot
from model.runelite_bot import BotStatus
from utilities.api.morg_http_client import MorgHTTPSocket
from utilities.api.status_socket import StatusSocket
from utilities.geometry import RuneLiteObject


class OSRSNMZ(OSRSBot):
    def __init__(self):
        self.options_set = True
        bot_title = "NMZ"
        description = (
            "Maintain 1 hp + overload"
        )
        super().__init__(bot_title=bot_title, description=description)
        self.running_time = 180
        self.take_breaks = True
        self.overload_timer = 0

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

        pattern = ' \d+ '

        overload_list = [ids.OVERLOAD_1, ids.OVERLOAD_2, ids.OVERLOAD_3, ids.OVERLOAD_4]
        absorption_list = [ids.ABSORPTION_1, ids.ABSORPTION_2, ids.ABSORPTION_3, ids.ABSORPTION_4]
        while True:
            try:
                if (not api_m.get_is_in_combat()) and api_m.get_is_player_idle():
                    if (object_found := self.get_nearest_tag(clr.PINK)):
                        self.mouse.move_to(object_found.random_point(), mouseSpeed='fast')
                        time.sleep(0.8)
                        self.mouse.click()
                        time.sleep()
                current_hp = api_m.get_hitpoints()[0]
                if current_hp > 50:
                    self.drink(overload_list, api_m)
                    self.drink(absorption_list, api_m)
                    self.overload_timer = time.time() + 300
                    if 'You can only drink' in api_m.get_latest_chat_message():
                        time.sleep(random.randint(6000, 8000) / 1000)
                        self.__logout('finito')
                    time.sleep(random.randint(6000, 8000) / 1000)
                if 10 > current_hp > 1:
                    if abs(time.time() - self.overload_timer) < 5:
                        continue
                    if self.mouseover_text(contains="Feel", color=clr.OFF_WHITE):
                        time.sleep(random.randint(132, 322) / 1000)
                        self.mouse.click()
                    else:
                        if orb := api_m.get_inv_item_indices(ids.LOCATOR_ORB)[0]:
                            self.mouse.move_to(self.win.inventory_slots[orb].random_point())
                            time.sleep(random.randint(132, 322) / 1000)
                            if self.mouseover_text(contains="Feel", color=clr.OFF_WHITE):
                                self.mouse.click()
                if 'You now' in (message := api_m.get_latest_chat_message()):
                    if int(re.search(pattern, message).group().strip()) < 100:
                        self.drink(absorption_list, api_m)

                elif 'You wake up' in api_m.get_latest_chat_message():
                    time.sleep(random.randint(6000, 8000) / 1000)
                    self.__logout('finito')
            except:
                continue

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()

    def drink(self, potions, api_m):
        for pot in potions:
            if pot_found := api_m.get_inv_item_indices(pot):
                self.mouse.move_to(self.win.inventory_slots[pot_found[0]].random_point())
                time.sleep(random.randint(132, 322) / 1000)
                if self.mouseover_text(contains="Drink", color=clr.OFF_WHITE):
                    self.mouse.click()
                    return
        return