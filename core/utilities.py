# NOTE: deprecated code.
#  I'm leaving it here simply as a blueprint to build in the future better
#  visualization tools for debugging

import math
import numpy as np
import time


def cell_check_inboard(x, y):
    ''' Given coordinates (x, y), expressed wrt to the exagonal base (where
    two unitary sides 30 degrees apart are taken as a base of the lattice), it
    returns True if the point lies on the board, False otherwise
    
    >>> call_check_inboard(0, 0) -> True
    (0, 0) is the center of the board

    >>> call_check_inboard(8, -4) -> True
    this is the top-right corner.

    >>> call_check_inboard(6, -6) -> False
    outside of the board.
    '''
    return (
        (x >= -4 and y >= -4 and x+y <= 4) or 
        (x <= 4 and y <= 4 and x+y >= -4)
    )

HOLES_SET = {
    (x-8,y-8) for x, y in np.ndindex(17, 17) if cell_check_inboard(x-8,y-8)
}


class State:
    def __init__(self):
        ''' game state

        self.pieces:    list of game pieces
        '''
        self.pieces = []
        self.next_player = None

    def clear(self):
        self.pieces = []

    def new_game(self, players_number: int):
        '''set the board for a new game with given number of players
        '''
        assert (players_number in (2, 3, 4, 6)), f"\
            games with {players_number} players are unsuppported"


        # Set next player to be player 1
        self.next_player = 1

        # Setup the board
        #  Currently only two players are supported cause I'm lazy
        if players_number != 2:
            raise NotImplementedError("only 2 players game are provided")


    def _move(self, xf, yf, xt, yt):
        for p in self.pieces:
            if (p.x, p.y) == (xf, yf):
                p.x = xt 
                p.y = yt
                break



class Screen:
    def __init__(self, s):
        '''s is a game state that has to be printed
        '''
        self.s = s
        self.tiles = {
            "out" : " ",
            "empty" : "\u001b[2m.\u001b[0m",
            1 : "\u001b[31mo\u001b[0m",
            2 : "\u001b[34;1mo\u001b[0m",
        }   

    def screen_to_piece(x, y):
        ''' screen coordinates to board coordinates.
        Note: y is flipped
        '''
        return ((-y+x)/2, (-y-x)/2)

    def piece_to_screen(x, y):
        return (12 + y - x, 8 -(y + x))

    def _show_board_char(self, x, y):
        if (x,y) in HOLES_SET:
            return self.tiles["empty"]
        else:
            return self.tiles["out"]

    def show(self):
        T = [[
                self._show_board_char(*Screen.screen_to_piece(x, y))
                for x in range(-12, 13)
            ]
            for y in range(-8, 9)
        ]

        for p in s.pieces:
            x, y = Screen.piece_to_screen(p.x, p.y)
            T[y][x] = self.tiles[p.team]

        print("\n".join("".join(c for c in line) for line in T))

#test_print_cell()

s = State()
s.new_game(2)
screen = Screen(s)



# time test
A = [i for i in range(100)]
B = {i for i in range(100)}
t1 = time.time()
for i in range(100000):
    for j in range(100):
        out = (i + j)%100
        A[j] = (i+j)%100
t2 = time.time()
print(t2 - t1)

t1 = time.time()
for i in range(100000):
    for j in range(100):
        B.remove((i+j)%100)
        B.add((i+j)%100)
t2 = time.time()
print(t2 - t1)











while True:
    print("")
    screen.show()
    print("")
    print(f"P1 inv = {s.stat(1)}\nP2 inv = {s.stat(2)}")
    move = input("next move? ")
    move = move.replace(",", " ").replace("  ", " ").split(" ")
    move = [int(x) for x in move]
    print(move)
    s._move(*move)
