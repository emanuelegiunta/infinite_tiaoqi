import unittest
from tiaoqi.core.gamestate import GameState

class TestGameState(unittest.TestCase):
    ''' API table:

    <DONE>  piece_add(x, y, kind)
    <DONE>  piece_remove(x, y)
    <DONE>  piece_remove_all(f)

    <DONE>  board_add(x, y)
    <DONE>  board_add_iter(iterator)
    <DONE>  board_remove(x, y)
    <DONE>  board_remove_all(f)

    <    >  player_add()
    <    >  player_pop()

    <    >  path(x, y)
    <    >  move(x1, y1, x2, y2)
    <    >  move_force(x1, y1, x2, y2)
    '''
    def setUp(self):
        self.gs = GameState()

    def test_board_add(self):
        # setup the board
        with self.subTest("single use"):
            assert self.gs.board == set()
            self.gs.board_add(0, 0)
            self.assertEqual(self.gs.board, {(0, 0)})

        # Adding replicated element should not do anything
        with self.subTest("adding replicated value"):
            assert self.gs.board == {(0, 0)}
            self.gs.board_add(0, 0)
            self.assertEqual(self.gs.board, {(0, 0)})

        # Negative Values Should be Accepted
        with self.subTest("adding negative values"):
            assert self.gs.board == {(0, 0)}
            self.gs.board_add(-1, 0)
            self.gs.board_add(0, -1)
            self.assertEqual(self.gs.board, {(0, 0), (-1, 0), (0, -1)})

        # Adding non-integer tuple should raise TypeError
        for p in [(0, 0.0), (0.0, 0), (0.0, 0.0)]:
            with self.subTest("float input type", point=p):
                self.assertRaises(TypeError, self.gs.board_add, *p)

    def test_board_add_iter(self):

        # Prepearing lists to add in board
        L = [
            [(0, 0), (1, 0)], 
            [(0, 0), (0, 1)], # Non empty intersection with the previous
            [(1, 0), (0, 1)], # Contained in the previous lists
            [(1, 1), (1, 1)], # The list contains replicated points
        ]

        # Initializing the expected state of the board
        S = set()

        # Adding simple lists with possibile overlaps
        for l in L:
            with self.subTest("adding list", used_list=l):
                self.gs.board_add_iter(l)
                S = S.union(set(l))
                self.assertEqual(self.gs.board, S)

        # Adding a generator should work too
        g = ((i, i) for i in range(2))
        with self.subTest("adding generator"):
            self.gs.board_add_iter(g)
            S = S.union(set(g))
            self.assertEqual(self.gs.board, S)

        # Adding a list with a single non-int-type raises TypeError
        # Note: the list should also not be changed (safe recovery)
        l = [(0, 0), (1, 0), (2, 0)]
        for p in [(1.0, 1), (1, 1.0), (1.0, 1.0)]:
            with self.subTest("non-int input", point=p):
                self.assertRaises(TypeError, self.gs.board_add_iter, l + [p])
                self.assertEqual(self.gs.board, S)

    def test_board_remove_all(self):
        
        # Testing default Value to be None
        with self.subTest("testing default"):
            # Add something on the board
            self.gs.board_add(0, 0)
            self.gs.board_remove_all()
            self.assertEqual(self.gs.board, set())

        # SETUP filters
        filters = [
            lambda x, y: True,      # Remove eveything.
            lambda x, y: x%2 == 1,  # Remove only entry with odd x
            lambda x, y: False,     # Remove nothing.
        ]

        # Removing from an empty set has no effect
        for i, f in enumerate(filters):
            with self.subTest("with empty board", case=i):
                # We don't update S, as we expect S to be empty in each case
                self.gs.board_remove_all(f)
                self.assertEqual(self.gs.board, set())

        # SETUP lists
        l = [(i, 0) for i in range(5)]
        
        # Removing from non-empty board
        for i, f in enumerate(filters):
            with self.subTest("with non-empty board", case=i):
                self.gs.board_add_iter(l)
                assert self.gs.board == set(l)
                self.gs.board_remove_all(f)
                self.assertEqual(self.gs.board, {p for p in l if not f(*p)})

        # SETUP - adding a piece on the board
        self.gs.board_remove_all()
        self.gs.board_add(0, 0)
        self.gs.board_add(1, 0)
        self.gs.piece_add(0, 0, "u")
        assert self.gs.board == {(0, 0), (1, 0)}
        assert self.gs.pieces == {(0, 0) : "u"}

        # Removing non-empty board with pieces on removed tiles -> ValueError
        # Note: The state should be unaltered
        #  default Case
        with self.subTest("with piece, default"):
            self.assertRaises(ValueError, self.gs.board_remove_all, None)
            self.assertEqual(self.gs.board, {(0, 0), (1, 0)})
            self.assertEqual(self.gs.pieces, {(0, 0) : "u"})

        #  non-default Case
        with self.subTest("with piece, filter, raise"):
            f = lambda x, y: True
            self.assertRaises(ValueError, self.gs.board_remove_all, f)
            self.assertEqual(self.gs.board, {(0, 0), (1, 0)})
            self.assertEqual(self.gs.pieces, {(0, 0) : "u"})

        # Removing non-empty board with pieces out of removed tiles
        with self.subTest("with piece, filter, pass"):
            f = lambda x, y: x == 1
            self.gs.board_remove_all(f)
            self.assertEqual(self.gs.board, {(0, 0)})
            self.assertEqual(self.gs.pieces, {(0, 0) : "u"})

    def test_board_remove(self):

        # Removing from empty board should do nothing
        with self.subTest("from empty"):
            self.gs.board_remove(-1, 1)
            self.assertEqual(self.gs.board, set())

        # Removing added elements
        with self.subTest("singleton"):
            self.gs.board_add(0, 0)
            self.gs.board_remove(0, 0)
            
            self.assertEqual(self.gs.board, set())

        # Removing a board tile with pieces on top raises ValueError
        with self.subTest("with piece on top"):
            self.gs.board_add(0, 0)
            self.gs.piece_add(0, 0, "u")
            self.assertRaises(ValueError, self.gs.board_remove, 0, 0)

    def test_piece_add(self):
        # SETUP board and players
        S = {(0, 0), (0, 1), (1, 0), (1, 1)}
        self.gs.board_add_iter(S)
        self.gs.player_add()
        assert self.gs.player_num == 1
        assert self.gs.board == S

        # Adding pieces for all kind
        #  Also testing gs.pieces return a dictionary decryption of the pieces
        D = {}
        for (x, y), kind in {(0, 0): "u", (0, 1): "j", (1, 0): "0"}.items():
            with self.subTest("adding piece", kind=kind):
                self.gs.piece_add(x, y, kind)
                D[(x, y)] = kind
                self.assertEqual(self.gs.pieces, D)

        # Adding pieces out of board raises ValueError
        with self.subTest("out of board"):
            self.assertRaises(ValueError, self.gs.piece_add, 2, 0, "u")

        # Adding pieces on occupied tiles raises ValueError
        #  Note: this still happens even if we are insering the same piece
        #  already placed on the board
        with self.subTest("adding occupied"):
            self.assertRaises(ValueError, self.gs.piece_add, 0, 0, "u")

        # Adding pieces with malformed kind raises ValueError
        for i in range(127):
            with self.subTest("malformed kind", i=i):
                # The only admissible kinds are "j", "u" and player numbers
                if chr(i) in ["j", "u", "0"]:
                    continue

                self.assertRaises(ValueError, self.gs.piece_add, 1, 1, chr(i))

    def test_piece_remove(self):
        # Setting up the board and a player
        S = {(0, 0), (1, 0), (0, 1), (1, 1)}
        self.gs.board_add_iter(S)
        self.gs.player_add()
        assert self.gs.player_num == 1
        assert self.gs.board == S

        # Removing pieces for all kind
        for (x, y), kind in {(0, 0): "u", (1, 0): "j", (0, 1): "0"}.items():
            with self.subTest("remove pieces", kind=kind):
                self.gs.piece_add(x, y, kind)
                assert self.gs.pieces == {(x, y): kind}
                self.gs.piece_remove(x, y)

                # Check that no piece is left, but board is untouched
                self.assertEqual(self.gs.pieces, {})
                self.assertEqual(self.gs.board, S)

        # Removing a piece where there is non raise no error
        with self.subTest("remove in empty position"):
            self.gs.piece_remove(0, 0)
            self.assertEqual(self.gs.pieces, {})

    def test_piece_remove_all(self):
        # SETUP board and player
        S = {(0, 0), (1, 0), (0, 1), (1, 1)}
        self.gs.board_add_iter(S)
        self.gs.player_add()
        self.gs.player_add()
        assert self.gs.player_num == 2
        assert self.gs.board == S
        assert self.gs.pieces == {}

        # SETUP filters
        filters = [
            lambda x, y, kind: True,        # Remove all
            lambda x, y, kind: y == 0,      # Remove all in the line y=0
            lambda x, y, kind: kind == "0", # Remove all piece of player 0
            lambda x, y, kind: False,       # Removes nothing
        ]

        # Removing from board with no pieces has no effect
        #  default case
        with self.subTest("no piece, default"):
            self.gs.piece_remove_all()
            # Pieces should be empty. The rest should be unaltered
            self.assertEqual(self.gs.pieces, {})
            self.assertEqual(self.gs.board, S)
            self.assertEqual(self.gs.player_num, 2)

        for i, f in enumerate(filters):
            with self.subTest("no piece, filter", case=i):
                self.gs.piece_remove_all(f)
                # pieces should be empty, the rest should be unaltered 
                self.assertEqual(self.gs.pieces, {})
                self.assertEqual(self.gs.board, S)
                self.assertEqual(self.gs.player_num, 2)

        # Only pieces satisfying f are removed when pieces are on board
        #  Default case
        with self.subTest("with pieces, default"):
            self.gs.piece_remove_all()
            self.gs.piece_add(0, 0, "u")
            self.gs.piece_add(0, 1, "j")
            self.gs.piece_add(1, 0, "0")
            self.gs.piece_add(1, 1, "1")
            assert self.gs.pieces == {(0, 0): "u", (0, 1): "j",
                (1, 0): "0", (1, 1): "1"}

            self.gs.piece_remove_all()
            self.assertEqual(self.gs.pieces, {})

        #  Filter case
        for i, f in enumerate(filters):
            with self.subTest("with pieces, filter", case=i):
                self.gs.piece_remove_all()
                self.gs.piece_add(0, 0, "u")
                self.gs.piece_add(0, 1, "j")
                self.gs.piece_add(1, 0, "0")
                self.gs.piece_add(1, 1, "1")
                D = {(0, 0): "u", (0, 1): "j", (1, 0): "0", (1, 1): "1"}
                assert self.gs.pieces == D

                self.gs.piece_remove_all(f)
                D = {(x, y): k for (x, y), k in D.items() if not f(x, y, k)}

                self.assertEqual(self.gs.pieces, D)
                self.assertEqual(self.gs.board, S)
                self.assertEqual(self.gs.player_num, 2)


