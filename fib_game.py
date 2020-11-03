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

# Fibbage adds fibs if there are only two or three players,
# so there is a minimum of 3 fibs + 1 answer displayed for each
# player, but each player doesn't see his own answer, so you
# need a total of at least 4 fibs 
MIN_ANSWERS = 4

# types of fibs - user-created or automatic suggestions
FIB_USER_CREATED, FIB_SUGGESTION = list(range(2))

# field names in .jet/JSON files
JET_SUGGESTIONS = 'Suggestions'
JET_QUESTION_AUDIO = 'QuestionAudio'
JET_CORRECT_TEXT = 'CorrectText'


RETURN_CODES_TO_NAMES = {POST_REPLY: "POST_REPLY",
                         POST_REDIRECT: "POST_REDIRECT",
                         POST_VALIDATION_ERROR: "POST_VALIDATION_ERROR",
                         POST_INTERNAL_ERROR: "POST_INTERNAL_ERROR",
                         POST_ENDPOINT_NOT_FOUND: "POST_ENDPOINT_NOT_FOUND"}

# returns a random hex ID string
def random_hex_id(len_bytes=4):
    format_str = "%%0%dx" % (len_bytes * 2)
    return (format_str % random.randrange(2 ** (8 * len_bytes))).upper()


def process_question_json(question_json):
    question_fields = question_json['fields']

    for question_field in question_fields:
        if question_field['n'] == JET_SUGGESTIONS and 'v' in question_field:
            question_json[JET_SUGGESTIONS] = question_field['v'].split(',')
        elif question_field['n'] == JET_CORRECT_TEXT and 'v' in question_field:
            question_json[JET_CORRECT_TEXT] = question_field['v']
        elif question_field['n'] == JET_QUESTION_AUDIO and 'v' in question_field:
            question_json[JET_QUESTION_AUDIO] = question_field['v']

    return question_json


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

        self.GET_HANDLERS = {
            'question_audio': self.handle_GET_question_audio,
            'answer_audio': self.handle_GET_answer_audio
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
        self.question_jsons = []
        self.question_folders = []
        
        # hex ID to (answer, answer type)
        self.current_round_answers = {}

    # return either an absolute path, or None
    def handle_GET(self, get_path):
        if get_path not in self.GET_HANDLERS:
            return None
        
        try:
            # post_handler() should return a tuple of (type, data)
            return self.GET_HANDLERS[get_path](get_path)
        except:
            traceback.print_exc()
            return None

    
    def handle_GET_question_audio(self, _):
        if self.state != GAME_FIBBING:
            return None
        
        if JET_QUESTION_AUDIO not in self.question_jsons[self.current_round]:
            return None

        audio_file_name = self.question_jsons[self.current_round][JET_QUESTION_AUDIO] + '.ogg'
        # print(os.path.join(self.question_folders[self.current_round], audio_file_name))
        return os.path.join(self.question_folders[self.current_round], audio_file_name)


    def handle_GET_answer_audio(self, _):
        # TODO check state
        # TODO add answer audio file name extraction to process_question_json()
        # TODO extract answer audio file name, if present in JSON, otherwise return None
        return None


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

        for question_folder in self.question_folders:
            with open(os.path.join(question_folder, "data.jet"), 'r') as f:
                self.question_jsons.append(process_question_json(json.load(f)))

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
        question_json = self.question_jsons[self.current_round]
        
        question_json['timer_length'] = self.timer_length

        return POST_REPLY, question_json


    def pad_with_fibs(self):
        # add more auto-fibs until there's enough, but
        # keep in mind that the others might be auto-fibs as well

        auto_suggestion_count = sum(map(lambda x: x[1] == FIB_SUGGESTION, self.current_round_answers.values()))
        suggestions = self.question_jsons[self.current_round][JET_SUGGESTIONS]

        if ((MIN_ANSWERS - len(self.current_round_answers.values())) < (len(suggestions) - auto_suggestion_count)):
            # if we're here this means there are enough suggestions
            while len(self.current_round_answers) < MIN_ANSWERS:
                new_suggestion = random.sample(self.question_jsons[self.current_round][JET_SUGGESTIONS], 1)
                answers = map(lambda x:x[0], self.current_round_answers.values())

                while new_suggestion in answers:
                    new_suggestion = random.sample(self.question_jsons[self.current_round][JET_SUGGESTIONS], 1)
                
                # insert using new random hex IDs (since the fib is automatic this shouldn't matter)
                new_hex_id = random_hex_id()
                while new_hex_id in self.current_round_answers:
                    new_hex_id = random_hex_id()
                self.current_round_answers[new_hex_id] = (new_suggestion, FIB_SUGGESTION)


    def handle_POST_fib(self, data):
        if data['id'] in self.current_round_answers:
            # ignore any answer after the first one
            return
        
        self.current_round_answers[data['id']] = (data['fib'], int(data['fib_type']))

        if len(self.current_round_answers) == len(self.players):
            # all answers accepted

            if len(self.current_round_answers) < MIN_ANSWERS:
                self.pad_with_fibs()
            
            self.state = GAME_CHOOSING

        return POST_REPLY, {}


    def handle_POST_get_current_answers(self, data):
        return POST_REPLY, {"handle_POST_get_current_answers": 'is a stub'}


    def handle_POST_submit_answer(self, data):
        return POST_REPLY, {"handle_POST_submit_answer": 'is a stub'}


    def handle_POST_get_round_results(self, data):
        return POST_REPLY, {"handle_POST_get_round_results": 'is a stub'}


