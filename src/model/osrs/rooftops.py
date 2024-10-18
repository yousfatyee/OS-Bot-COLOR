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

from utilities import ocr
from utilities.geometry import Rectangle
from utilities.imagesearch import search_img_in_rect, BOT_IMAGES


def count_marks(inventory):
    for item in inventory:
        if item.get('id', 0) == 11849:
            return item.get('quantity', 0)


class OSRSAgility(OSRSBot):
    def __init__(self):
        self.amount_of_marks = 0
        self.laps = None
        self.options_set = True
        bot_title = "Canifis Agility"
        description = (
            "Agility + marks"
        )
        super().__init__(bot_title=bot_title, description=description)
        self.laps_run = 240
        self.total_laps = 0
        self.total_marks = 0
        self.fails = 0
        self.take_breaks = True

    def create_options(self):
        self.options_builder.add_slider_option("laps_run", "How long to run (laps)?", 1, 500)
        self.options_builder.add_checkbox_option("take_breaks", "Take breaks?", [" "])

    def save_options(self, options: dict):
        for option in options:
            if option == "laps_run":
                self.laps_run = options[option]
            elif option == "take_breaks":
                self.take_breaks = options[option] != []
            else:
                self.log_msg(f"Unknown option: {option}")
                print("Developer: ensure that the option keys are correct, and that options are being unpacked correctly.")
                self.options_set = False
                return
        self.log_msg(f"Running laps: {self.laps_run}.")
        self.log_msg(f"Bot will{' ' if self.take_breaks else ' not '}take breaks.")
        self.log_msg("Options set successfully.")
        self.options_set = True

    def main_loop(self):
        # Setup API
        api_m = MorgHTTPSocket()

        self.laps = 0
        self.amount_of_marks = count_marks(api_m.get_inv())
        self.total_laps = 0
        obstacles = {
            (2726,3485,0): {
                'text': ["Climb", "Wall"],
                'yellow_step': False,
                'mark': True,
                'color': clr.YELLOW
            },
            (2729, 3491, 3): {
                'text': ["Jump", "Gap"],
                'yellow_step': False,
                'mark': True,
                'color': clr.ORANGE
            },
            (2713, 3494, 2): {
                'text': ["Cross", "Tightrope"],
                'yellow_step': True,
                'mark': True,
                'color': clr.DARK_BLUE
            },
            (2710, 3480, 2): {
                'text': ["Jump", "Gap"],
                'yellow_step': False,
                'mark': True,
                'color': clr.LIGHT_RED
            },
            (2712, 3472, 3): {
                'text': ["Jump", "Gap"],
                'yellow_step': False,
                'mark': True,
                'color': clr.DARK_ORANGE
            },
            (2713, 3472, 3): {
                'text': ["Jump", "Gap"],
                'yellow_step': False,
                'mark': True,
                'color': clr.DARK_ORANGE
            },
            (2711, 3472, 3): {
                'text': ["Jump", "Gap"],
                'yellow_step': False,
                'mark': True,
                'color': clr.DARK_ORANGE
            },
            (2710, 3472, 3): {
                'text': ["Jump", "Gap"],
                'yellow_step': False,
                'mark': True,
                'color': clr.DARK_ORANGE
            },
            (2714, 3472, 3): {
                'text': ["Jump", "Gap"],
                'yellow_step': False,
                'mark': True,
                'color': clr.DARK_ORANGE
            },
            (2702, 3465, 2): {
                'text': ["Jump", "Gap"],
                'yellow_step': False,
                'mark': True,
                'color': clr.DARK_GREEN
            },
        }
        # Main loop
        #keyboard.press_and_release("F6") #open magic book
        last_message = api_m.get_latest_chat_message()
        keyboard.press_and_release("f6")
        while self.total_laps < self.laps_run:
            if rd.random_chance(probability=0.02) and self.take_breaks:
                self.take_break(max_seconds=10, fancy=True)

            new_message = api_m.get_latest_chat_message()
            if 'Your Seers' in new_message and new_message != last_message:
                last_message = new_message
                self.total_laps += 1
                self.log_msg(f"Laps: {self.total_laps}, Marks: {self.total_marks}, Fails: {self.fails}")
                self.update_progress(self.total_laps/self.laps_run)
                #self.__cast_tele()
            try:
                self.obstacle(obstacles[api_m.get_player_position()], api_m)
                #if not self.obstacle(obstacles[api_m.get_player_position()], api_m):
                    #self.obstacle(obstacles[(3510, 3485, 0)], api_m)
            except KeyError:
                if not self.obstacle(obstacles[(2726,3485,0)], api_m):
                    self.__cast_tele()
                    continue

        self.update_progress(1)
        self.__logout("Finished.")

    def __logout(self, msg):
        self.log_msg(msg)
        self.logout()
        self.stop()

    def pick_up_mark(self):
        if ocr.find_text("Mark of grace", self.win.game_view, ocr.PLAIN_11, [clr.GROUND_PURPLE]):
            while not self.mouseover_text(contains=['Take'], color=[clr.OFF_WHITE]):
                enter_text = ocr.find_text("of", self.win.game_view, ocr.PLAIN_11, [clr.GROUND_PURPLE])
                self.mouse.move_to(enter_text[0].random_point(), mouseSpeed='fastest')
                time.sleep(0.2)
            self.mouse.click()
            return True
        return False
    def __cast_tele(self):
        tele = search_img_in_rect(BOT_IMAGES.joinpath("spellbooks").joinpath("normal","Camelot_teleport.png"),self.win.control_panel)
        if tele:
            self.mouse.move_to(tele.random_point(),mouseSpeed='fast')
            self.mouse.click()
        time.sleep(2.6)
        
        
    def obstacle(self, step, api_m: MorgHTTPSocket):
        #if step['yellow_step']:
        #    if yellow_step := self.get_nearest_tag(clr.YELLOW):
        #        self.mouse.move_to(yellow_step.random_point(), mouseSpeed='fastest')
        #        self.mouse.click()
        #        time.sleep(random.randint(2500, 3500) / 1000)

        #if step['mark']:
        #    if self.pick_up_mark():
        #        self.total_marks += 1
        #        self.log_msg(f"Marks collected: ~{self.total_marks}")
        #        attempt = 0
        #        while self.amount_of_marks == count_marks(api_m.get_inv()):
        #            attempt += 1
        #            time.sleep(1)
        #            if attempt == 20:
        #                break
        #        self.amount_of_marks = count_marks(api_m.get_inv())

        #time.sleep(0.7)
        #if self.alch:
        #    rand = random.randint(0,4)
        #    for i in range(rand):
         
        search_val = ocr.find_text("Mark of grace", self.win.game_view, ocr.PLAIN_11, [clr.GROUND_PURPLE])
        retries = 0   
        #self.highAlch(api_m)
        pickup = False
        moved = False    
        while not self.mouseover_text(contains=step['text'], color=[clr.OFF_WHITE, clr.OFF_CYAN]):
            if retries >= 10:
                break
            if nearest := self.get_all_tagged_in_rect(self.win.game_view, step['color']):
                if (not pickup) and search_val:
                    enter_text = ocr.find_text("of", self.win.game_view, ocr.PLAIN_11, [clr.GROUND_PURPLE])
                    if len(enter_text):
                        enter_text[0].set_rectangle_reference(self.win.game_view)
                        d1 = 1
                        d2 = 2
                        #if step['yellow_step']:
                        #    d1 = enter_text[0].distance_from_center()
                        #    d2 = nearest[0].distance_from_rect_center()
                        if d1 < d2:
                            if (pickup:= self.pick_up_mark()):
                                self.total_marks += 1
                                self.log_msg(f"Marks collected: ~{self.total_marks}")
                                attempt = 0
                                while self.amount_of_marks == count_marks(api_m.get_inv()):
                                    attempt += 1
                                    time.sleep(1)
                                    if attempt == 20:
                                        break
                                self.amount_of_marks = count_marks(api_m.get_inv())
                                      
                self.mouse.move_to(nearest[0].random_point(), mouseSpeed='fast')
                time.sleep(0.1)
                if self.mouseover_text(contains=step['text'], color=[clr.OFF_WHITE, clr.OFF_CYAN]):
                    if not self.mouse.click(check_red_click=True):
                        continue
                    #if rd.random_chance(probability=0.89):
                        #moved = True
                        #self.mouse.move_to(self.win.spellbook_normal[34].random_point(),mouseSpeed='medium')
                        #if not self.mouseover_text(contains="Cast",color=clr.OFF_WHITE):
                        #    keyboard.press_and_release("F6") 
                        #    time.sleep(0.2)
                        #self.mouse.click()  
                        #yewlong = api_m.get_inv_item_indices(ids.YEW_LONGBOW_NOTED)
                        #self.mouse.move_to(self.win.inventory_slots[yewlong[0]].random_point(), mouseSpeed='fast')
                    break
            retries += 1
        

        #self.log_msg(f'Clicking color {str(step["color"])}')
        if not api_m.wait_til_gained_xp('Agility', 10):
            self.obstacle(step, api_m)
        if moved:
            self.mouse.click()            
        if api_m.get_player_position()[2] == 0 and api_m.get_player_position() != (3510, 3485, 0):
            self.__cast_tele()
            #while not self.get_nearest_tag(clr.YELLOW):
            #    if enter_text := self.get_all_tagged_in_rect(self.win.game_view, clr.RED):
            #        self.fails += 1
            #        self.mouse.move_to(enter_text[0].random_point(), mouseSpeed='fastest')
            #        time.sleep(0.2)
            #        self.mouse.click()
            #        time.sleep(random.randint(3500, 4500) / 1000)
            #return False        
        time.sleep(random.randint(850, 933) / 1000)
        return True

    def highAlch(self,api_m: MorgHTTPSocket):
        #alch_pic = BOT_IMAGES.joinpath("spellbooks").joinpath("normal","high_alch1.png")
        keyboard.press_and_release("F6")
        self.mouse.move_to(self.win.spellbook_normal[34].random_point())
        self.mouse.click()
        time.sleep(0.6)
        yewlong = api_m.get_inv_item_indices(ids.YEW_LONGBOW_NOTED)
        self.mouse.move_to(self.win.inventory_slots[yewlong[0]].random_point(), mouseSpeed='fastest')
        self.mouse.click()
        time.sleep(0.3)
        return True
