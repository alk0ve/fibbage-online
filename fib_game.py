import os
import random
import logging # should be configured elsewhere
import traceback
import json
import glob

# game states
GAME_PREPARING = 'preparing'
GAME_FIBBING = 'fibbing'
GAME_CHOOSING = 'choosing'
GAME_DISPLAYING = 'displaying'

# POST handler return codes
(POST_REPLY, POST_REDIRECT, POST_VALIDATION_ERROR, POST_INTERNAL_ERROR,
 POST_ENDPOINT_NOT_FOUND) = list(range(5))

# types of fibs - user-created or automatic suggestions
FIB_USER_CREATED, FIB_SUGGESTION = list(range(2))

RETURN_CODES_TO_NAMES = {POST_REPLY: "POST_REPLY",
                         POST_REDIRECT: "POST_REDIRECT",
                         POST_VALIDATION_ERROR: "POST_VALIDATION_ERROR",
                         POST_INTERNAL_ERROR: "POST_INTERNAL_ERROR",
                         POST_ENDPOINT_NOT_FOUND: "POST_ENDPOINT_NOT_FOUND"}

# returns a random hex ID string
def random_hex_id(len_bytes=4):
    format_str = "%%0%dx" % (len_bytes * 2)
    return (format_str % random.randrange(2 ** (8 * len_bytes))).upper()


class FibGame(object):
    def __init__(self, fib_content_path):
        # each entry is a pair of (validation, handler),
        # where validation is a list of either names or
        # tuples of (name, type)
        self.POST_HANDLERS = {
            'host': (['name', ('rounds', int), ('timer', int)], self.handle_POST_host),
            'join': (['name'], self.handle_POST_join),
            'list_players': ([], self.handle_POST_list_players),
            'start': (['id'], self.handle_POST_start),
            'get_game_state': ([], self.handle_POST_get_game_state),
            'get_current_question': ([], self.handle_POST_get_current_question),
            'fib': (['id', 'fib', ('fib_type', int)], self.handle_POST_fib),
            'get_current_answers': ([], self.handle_POST_get_current_answers),
            'submit_answer': ([], self.handle_POST_submit_answer),
            'get_round_results': ([], self.handle_POST_get_round_results)
        }

        self.fib_content_path = fib_content_path

        self.reset_state()


    def reset_state(self):
        # hex ID to name (and this includes the host)
        self.players = {}

        self.state = GAME_PREPARING
        self.host_id = None
        self.num_rounds = None
        self.current_round = 0
        self.timer_length = None
        self.question_folders = []
        
        # hex ID to (answer, answer type)
        self.current_round_answers = {}


    def handle_POST(self, post_path, json_data):
        post_path = post_path.lstrip('/')

        # find the endpoint
        if post_path not in self.POST_HANDLERS:
            return POST_ENDPOINT_NOT_FOUND, "POST endpoint not found"
        
        post_validation, post_handler = self.POST_HANDLERS[post_path]

        # validate data
        for validation_entry in post_validation:
            if type(validation_entry) == str:
                # name
                if validation_entry not in json_data:
                    return POST_VALIDATION_ERROR, "entry %s not found" % validation_entry
            elif type(validation_entry) == tuple:
                # name + type
                entry_name, entry_type = validation_entry
                if entry_name not in json_data:
                    return POST_VALIDATION_ERROR, "entry %s not found" % entry_name
                try:
                    json_data[entry_name] = entry_type(json_data[entry_name])
                except:
                    traceback.print_exc()
                    return POST_VALIDATION_ERROR, "entry %s is not of type %s" % (entry_name, str(entry_type))
            else:
                raise Exception("Unexpected type (%s) of validation entry %s" % (str(type(validation_entry)),
                        str(validation_entry)))

        try:
            # post_handler() should return a tuple of (type, data)
            return post_handler(json_data)
        except:
            traceback.print_exc()
            return POST_INTERNAL_ERROR, "Exception caught while handling POST to %s" % post_path



    def handle_POST_host(self, data):
        self.reset_state()

        self.host_id = random_hex_id()
        self.players[self.host_id] = data['name']
        
        self.num_rounds = int(data['rounds'])
        self.timer_length = int(data['timer'])

        # TODO choose a Final Fibbage question as well
        question_folders = glob.glob(os.path.join(self.fib_content_path, 'fibbageshortie', '*'))
        self.question_folders = random.sample(question_folders, self.num_rounds)

        return POST_REDIRECT, ('host_wait#%s' % self.host_id)


    def handle_POST_join(self, data):
        player_name = data["name"]
        player_id = random_hex_id()

        # make sure the random ID is not taken
        while player_id in self.players:
            player_id = random_hex_id()
        
        self.players[player_id] = player_name

        return POST_REDIRECT, ('join_wait#%s' % player_id)


    def handle_POST_list_players(self, data):
        return POST_REPLY, list(self.players.values())


    def handle_POST_start(self, data):
        if data['id'] != self.host_id:
            return POST_VALIDATION_ERROR, "Non-host tried to start the game"
        
        self.state = GAME_FIBBING

        return POST_REDIRECT, ('question#%s' % data['id'])


    def handle_POST_get_game_state(self, data):
        return POST_REPLY, self.state


    def handle_POST_get_current_question(self, data):
        with open(os.path.join(self.question_folders[self.current_round], "data.jet"), 'r') as f:
            question_json = json.load(f)
        
        question_json['timer_length'] = self.timer_length

        return POST_REPLY, question_json


    def handle_POST_fib(self, data):
        self.current_round_answers[data['id']] = (data['fib'], int(data['fib_type']))

        return POST_REPLY, {}


    def handle_POST_get_current_answers(self, data):
        return POST_REPLY, {"handle_POST_get_current_answers": 'is a stub'}


    def handle_POST_submit_answer(self, data):
        return POST_REPLY, {"handle_POST_submit_answer": 'is a stub'}


    def handle_POST_get_round_results(self, data):
        return POST_REPLY, {"handle_POST_get_round_results": 'is a stub'}


