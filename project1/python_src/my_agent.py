import random
from agent import RandomAgent
from environment import Environment
from negamax import NegaMax

BLACK, WHITE, EMPTY = "B", "W", " "

class MyAgent(RandomAgent):
    def __init__(self):
        self.role = None
        self.play_clock = None
        self.my_turn = False
        self.width = 0
        self.height = 0
        self.env = None
        self.last_move = None
        self.game_terminated = False

    # start() is called once before you have to select the first action. Use it to initialize the agent.
    # role is either "white" or "black" and play_clock is the number of seconds after which nextAction must return.
    def start(self, role, width, height, play_clock):
        self.game_terminated = False
        self.play_clock = play_clock
        self.role = role
        self.my_turn = role != 'white'
        # we will flip my_turn on every call to next_action, so we need to start with False in case
        #  our action is the first
        self.width = width
        self.height = height
        self.env = Environment(width=width, height=height, role=role)

    def next_action(self, last_action):
        if last_action:
            if self.my_turn and self.role == 'white' or not self.my_turn and self.role != 'white':
                last_player = 'white'
            else:
                last_player = 'black'
            print("%s moved from %s to %s" % (last_player, str(last_action[0:2]), str(last_action[2:4])))
            x1, y1, x2, y2 = last_action
            if self.last_move != (x1-1, y1-1, x2-1, y2-1) and self.my_turn:
                print("Error! Our last move was not expected. "
                      "Probably we timed out or did an illegal move")
                exit(0)
            # Simulate move of opponent
            self.env.move(self.env.current_state, (x1-1, y1-1, x2-1, y2-1))
        else:
            print("first move!")

        # update turn (above that line it myTurn is still for the previous state)
        self.my_turn = not self.my_turn
        if self.my_turn:
            x1, y1, x2, y2 = self.get_best_move()
            self.last_move = (x1, y1, x2, y2)
            return "(move " + " ".join(map(str, [x1+1, y1+1, x2+1, y2+1])) + ")"
        else:
            return "noop"

    def get_best_move(self):
        """Compute the best possible move according to the NegaMax algorithm."""
        return NegaMax(self.env, self.role, self.play_clock).run()

    def cleanup(self, last_move):
        self.game_terminated = True
        print("cleanup called")
        return