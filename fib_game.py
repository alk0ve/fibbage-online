import logging # should be configured elsewhere


class FibGame(object):
    def __init__(self):
        self.POST_HANDLERS = {
            'host': self.handle_POST_host,
            'join': self.handle_POST_join,
            'list_players': self.handle_POST_list_players,
            'start': self.handle_POST_start,
            'get_game_state': self.handle_POST_get_game_state,
            'get_current_question': self.handle_POST_get_current_question,
            'fib': self.handle_POST_fib,
            'get_current_answers': self.handle_POST_get_current_answers,
            'submit_answer': self.handle_POST_submit_answer,
            'get_round_results': self.handle_POST_get_round_results,
        }


    def handle_POST_host(self, data):
        return {"handle_POST_host": 'is a stub'}


    def handle_POST_join(self, data):
        return {"handle_POST_join": 'is a stub'}


    def handle_POST_list_players(self, data):
        return {"handle_POST_list_players": 'is a stub'}


    def handle_POST_start(self, data):
        return {"handle_POST_start": 'is a stub'}


    def handle_POST_get_game_state(self, data):
        return {"handle_POST_get_game_state": 'is a stub'}


    def handle_POST_get_current_question(self, data):
        return {"handle_POST_get_current_question": 'is a stub'}


    def handle_POST_fib(self, data):
        return {"handle_POST_fib": 'is a stub'}


    def handle_POST_get_current_answers(self, data):
        return {"handle_POST_get_current_answers": 'is a stub'}


    def handle_POST_submit_answer(self, data):
        return {"handle_POST_submit_answer": 'is a stub'}


    def handle_POST_get_round_results(self, data):
        return {"handle_POST_get_round_results": 'is a stub'}


