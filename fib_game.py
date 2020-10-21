import random
import logging # should be configured elsewhere
import traceback

# game states
GAME_PREPARING = 'preparing'
GAME_FIBBING = 'fibbing'
GAME_CHOOSING = 'choosing'
GAME_DISPLAYING = 'displaying'

# POST handler return codes
(
 POST_REPLY, POST_REDIRECT, POST_VALIDATION_ERROR, POST_INTERNAL_ERROR,
 POST_ENDPOINT_NOT_FOUND
) = list(range(5))

RETURN_CODES_TO_NAMES = {POST_REPLY: "POST_REPLY",
                         POST_REDIRECT: "POST_REDIRECT",
                         POST_VALIDATION_ERROR: "POST_VALIDATION_ERROR",
                         POST_INTERNAL_ERROR: "POST_INTERNAL_ERROR",
                         POST_ENDPOINT_NOT_FOUND: "POST_ENDPOINT_NOT_FOUND"}


def random_hex_id(len_bytes=4):
    format_str = "%%0%dx" % (len_bytes * 2)
    return (format_str % random.randrange(2 ** (8 * len_bytes))).upper()


class FibGame(object):
    def __init__(self):
        # each entry is a pair of (validation, handler),
        # where validation is a list of either names or
        # tuples of (name, type)
        self.POST_HANDLERS = {
            'host': (['name', ('rounds', int), ('timer', int)], self.handle_POST_host),
            'join': ([], self.handle_POST_join),
            'list_players': ([], self.handle_POST_list_players),
            'start': ([], self.handle_POST_start),
            'get_game_state': ([], self.handle_POST_get_game_state),
            'get_current_question': ([], self.handle_POST_get_current_question),
            'fib': ([], self.handle_POST_fib),
            'get_current_answers': ([], self.handle_POST_get_current_answers),
            'submit_answer': ([], self.handle_POST_submit_answer),
            'get_round_results': ([], self.handle_POST_get_round_results)
        }
        self.state = GAME_PREPARING
        # hex ID to name (and this includes the host)
        self.players = {}
        self.host_id = None
        self.num_rounds = None
        self.timer_length = None


    def handle_POST(self, post_path, json_data):
        post_path = post_path.lstrip('/')

        # find the endpoint
        if post_path not in self.POST_HANDLERS:
            return POST_ENDPOINT_NOT_FOUND, "POST endpoint not found"
        
        post_validation, post_handler = self.POST_HANDLERS[post_path]

        # validate data
        data_valid = True
        error_message = ""

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
        self.host_id = random_hex_id()
        self.players[self.host_id] = data['name']
        self.num_rounds = int(data['rounds'])
        self.timer_length = int(data['timer'])

        return POST_REDIRECT, 'host_wait'


    def handle_POST_join(self, data):
        return POST_REPLY, {"handle_POST_join": 'is a stub'}


    def handle_POST_list_players(self, data):
        return POST_REPLY, {"handle_POST_list_players": 'is a stub'}


    def handle_POST_start(self, data):
        return POST_REPLY, {"handle_POST_start": 'is a stub'}


    def handle_POST_get_game_state(self, data):
        return POST_REPLY, {"handle_POST_get_game_state": 'is a stub'}


    def handle_POST_get_current_question(self, data):
        return POST_REPLY, {"handle_POST_get_current_question": 'is a stub'}


    def handle_POST_fib(self, data):
        return POST_REPLY, {"handle_POST_fib": 'is a stub'}


    def handle_POST_get_current_answers(self, data):
        return POST_REPLY, {"handle_POST_get_current_answers": 'is a stub'}


    def handle_POST_submit_answer(self, data):
        return POST_REPLY, {"handle_POST_submit_answer": 'is a stub'}


    def handle_POST_get_round_results(self, data):
        return POST_REPLY, {"handle_POST_get_round_results": 'is a stub'}


