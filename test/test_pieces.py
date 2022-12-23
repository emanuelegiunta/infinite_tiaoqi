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

    <DONE>  paths(x, y)
    <DONE>  move(x1, y1, x2, y2)
    <DONE>  move_force(x1, y1, x2, y2)
    
    Internals: 
    <    >  _cache
    '''

    def setUp(self):
        self.gs = GameState()
        self.NEIGHBOURHOOD = ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), 
            (1, -1))

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

    def test_paths_error(self):
        # Empty Board
        with self.subTest("out of board, empty board"):
            self.assertRaises(ValueError, self.gs.paths, 0, 0)

        # Filled board
        with self.subTest("out of board, non-empty board"):
            self.gs.board_add_iter(self.NEIGHBOURHOOD)
            assert self.gs.board == set(self.NEIGHBOURHOOD)
            self.assertRaises(ValueError, self.gs.paths, 0, 0)

    def test_paths_empty(self):
        # SETUP board and player
        S = {(0, 0)}
        self.gs.board_add_iter(S)
        assert self.gs.board == S 
        assert self.gs.pieces == {}
        assert self.gs.player_num == 0

        P = {(0, 0): None}

        # No path if there is no available tile (with empty center)
        with self.subTest("no piece"):
            # P only has the "standing still" part of the path
            self.assertEqual(self.gs.paths(0, 0), P)

        # No path if there is no available tile (with empty center)
        with self.subTest("with piece"):
            self.gs.piece_add(0, 0, "j")
            assert self.gs.pieces == {(0, 0): "j"}

            self.assertEqual(self.gs.paths(0, 0), P)
            # TeadDown the piece
            self.gs.piece_remove(0, 0)
            assert self.gs.pieces == {}

        # SETUP add to board disconnected tiles at distance two
        #   `.` = empty spot (no tile),
        #   `o` = tile slot
        #
        #        o . o             
        #       . . . .            
        #      o . o . o            
        #       . . . .            
        #        o . o    
        #         
        S.union({(2*x, 2*y) for (x, y) in self.NEIGHBOURHOOD})
        self.gs.board_add_iter(S)

        assert self.gs.board == S
        assert self.gs.pieces == {}
        assert self.gs.player_num == 0

        # No path, with no pieces
        with self.subTest("no piece, far tiles"):
            self.assertEqual(self.gs.paths(0, 0), P)

        # No path, piece in the center
        with self.subTest("with piece, far tiles"):
            self.gs.piece_add(0, 0, "j")
            assert self.gs.pieces == {(0, 0): "j"}

            self.assertEqual(self.gs.paths(0, 0), P)
            # TearDown the piece
            self.gs.piece_remove(0, 0)
            assert self.gs.pieces == {}

    def test_paths_neighbouring(self):
        # SETUP board and pieces
        S = {(0, 0)}
        self.gs.board_add_iter(S)
        assert self.gs.board == S 
        assert self.gs.pieces == {}
        assert self.gs.player_num == 0

        # SETUP paths
        P = {(0, 0): None}

        # TEST: adding tiles in the neighbourhood progressively and check
        #  that path is correctly generated
        #
        # eg. at fourth iteration the state is
        #
        #          . .
        # board =   . .
        #            .
        for tile in self.NEIGHBOURHOOD:
            S.add(tile)
            P[tile] = (0, 0)

            # SETUP add the new tile
            self.gs.board_add(*tile)
            assert self.gs.board == S 
            assert self.gs.pieces == {}
            with self.subTest("partial neighbourhood", S=S):
                
                # No piece test
                self.assertEqual(self.gs.paths(0, 0), P) 

                # Piece test
                self.gs.piece_add(0, 0, "j")
                assert self.gs.pieces == {(0, 0): "j"}    
                self.assertEqual(self.gs.paths(0, 0), P)
                self.gs.piece_remove(0, 0)
                assert self.gs.pieces == {}

        # TEST: filling up tiles in the neighbourhood with pieces and check
        #  that path is correctly generated
        #
        # eg. at fourth iterarion the state is
        #
        #          u u
        # board = . . u
        #          . u
        #
        D = {}
        for tile in self.NEIGHBOURHOOD:
            D[tile] = "u"
            P.pop(tile)
            self.gs.piece_add(*tile, "u")
            assert self.gs.board == S 
            assert self.gs.pieces == D

            with self.subTest("filled neighbourhood", D=D):

                # No piece test
                self.assertEqual(self.gs.paths(0, 0), P)

                # Piece test
                self.gs.piece_add(0, 0, "j")
                D[(0, 0)] = "j"
                assert self.gs.pieces == D
                self.assertEqual(self.gs.paths(0, 0), P)
                self.gs.piece_remove(0, 0)
                D.pop((0, 0))
                assert self.gs.pieces == D

    def test_paths_no_cycles(self):
        # SETUP: radius 2 board
        #
        #           . . . 
        #          . o o . 
        # board = . o . o .
        #          . o o . 
        #           . . . 
        #
        # Note: we use this setup because no cycles are possibile, thus the
        #  paths tree is unique, so we can compare the output against the
        #  only possibile solution (as opposed to list all possibile solutions)
        S = {(0, 0)}
        S = {(x+dx, y+dy) for (x, y) in S for (dx, dy) in self.NEIGHBOURHOOD}
        S = {(x+dx, y+dy) for (x, y) in S for (dx, dy) in self.NEIGHBOURHOOD}
        self.gs.board_add_iter(S)
        for (x, y) in self.NEIGHBOURHOOD:
            self.gs.piece_add(x, y, "j")
        D = {p: "j" for p in self.NEIGHBOURHOOD}
        assert len(S) == 19
        assert self.gs.board == S 
        assert self.gs.pieces == {p: "j" for p in self.NEIGHBOURHOOD} 
        assert self.gs.player_num == 0

        # Test paths from (-1, 2)
        #
        #           . . . 
        #          . o o x 
        # board = . o . o .
        #          . o o . 
        #           . . . 
        #

        P = {(-1, 2): None, (0, 2): (-1, 2), (-2, 2): (-1, 2)}
        with self.subTest("p = (-1, 2)"):
            self.assertEqual(self.gs.paths(-1, 2), P)

        # Test paths from (0, 0)
        #
        #           . . . 
        #          . o o . 
        # board = . o x o .
        #          . o o . 
        #           . . . 
        #

        P = {(0, 0): None, (2, 0): (0, 0), (0, 2): (0, 0), (-2, 2): (0, 0),
             (-2, 0): (0, 0), (0, -2): (0, 0), (2, -2): (0, 0)}
        with self.subTest("p = (0, 0)"):
            self.assertEqual(self.gs.paths(0, 0), P)

        # Test paths from (2, 0)
        #
        #           x . . 
        #          . o o . 
        # board = . o . o .
        #          . o o . 
        #           . . . 
        #

        P = {(2, 0): None, (0, 0): (2, 0), (0, 2): (0, 0), (-2, 2): (0, 0),
             (-2, 0): (0, 0), (0, -2): (0, 0), (2, -2): (0, 0), (1, 1): (2, 0),
             (2, -1): (2, 0)}
        with self.subTest("p = (2, 0)"):
            self.assertEqual(self.gs.paths(2, 0), P)

        # Test paths from (1, -1)
        #
        #           . . . 
        #          . o o . 
        # board = . x . o .
        #          . o o . 
        #           . . . 
        #

        P = {(1, -1): None, (2, -1): (1, -1), (0, 0): (1, -1), 
             (1, -2): (1, -1), (2, -2): (1, -1), (1, 1): (1, -1), 
             (-1, -1): (1, -1)}
        with self.subTest("p = (1, -1)"):
            self.assertEqual(self.gs.paths(1, -1), P)

    def test_paths_cycles(self):
        # SETUP: radius 1 diamond
        #
        #           .          
        #          o o
        # board = . . .
        #          o o
        #           .
        # 
        S = {(x,y) for x in range(-1, 2) for y in range(-1, 2)}
        self.gs.board_add_iter(S)

        # SETUP: two lines of pieces
        l = ((1, 0), (0, 1), (-1, 0), (0, -1))
        for (x, y) in l:
            self.gs.piece_add(x, y, "j")
        D = {p: "j" for p in l}

        assert self.gs.board == S 
        assert self.gs.pieces == {p: "j" for p in l} 
        assert self.gs.player_num == 0

        # TEST: paths from (1, -1)
        #
        #           .
        #          o o
        # board = x . .
        #          o o
        #           .

        # P_base, part of the tree shared among all possibile paths
        P_base = {(1, -1): None, (0, 0): (1, -1), (1, 1): (1, -1), 
                  (-1, -1): (1, -1)}

        # P1, assuming (-1, 1) is reached from (1, 1)
        P1 = P_base.copy()
        P1[(-1, 1)] = (1, 1)

        # P2, assuming (-1, 1) is reached from (-1, -1)
        P2 = P_base.copy()
        P2[(-1, 1)] = (-1, -1)

        self.assertTrue(self.gs.paths(1, -1) in (P1, P2))

    def test_paths_unjumpable(self):
        # SETUP: 3 tiles line
        #
        #         . 
        # board =  u
        #           .
        #
        S = {(i, 0) for i in range(-1, 2)}
        self.gs.board_add_iter(S)
        self.gs.piece_add(0, 0, "u")

        assert self.gs.board == S
        assert self.gs.pieces == {(0, 0): "u"}
        assert self.gs.player_num == 0

        self.assertEqual(self.gs.paths(-1, 0), {(-1, 0): None})

    def test_move_errors(self):
        # SETUP: radius 1 ball
        #
        #          u j 
        # board = . . 0
        #          . 1
        #
        # u: unjump, j: jump, 0: player 0, 1: player 1

        S = {(0, 0)}.union(set(self.NEIGHBOURHOOD))
        self.gs.board_add_iter(S)
        self.gs.player_add(2)
        self.gs.piece_add(1, 0, "u")
        self.gs.piece_add(0, 1, "j")
        self.gs.piece_add(-1, 1, "0")
        self.gs.piece_add(-1, 0, "1")

        assert self.gs.board == S 
        assert self.gs.pieces == {(1, 0): "u", (0, 1): "j", (-1, 1): "0",
                                  (-1, 0): "1"}
        assert self.gs.player_num == 2

        # TEST: moving a tile not containing a `current round piece`
        # p = (1, 0) -> move an unjump
        # p = (0, 1) -> move a non-playing jump
        # p = (-1, 0) -> move a piece of a player in the wrong round
        #
        # Note: for all this piece (0, 0) is a valid destination
        for (x, y) in ((1, 0), (0, 1), (-1, 0)):
            with self.subTest("wrong piece", piece=self.gs.pieces[(x, y)]):
                self.assertRaises(ValueError, self.gs.move, x, y, 0, 0)

        # TEST: no path & move in place
        #
        # We iterate on all board point but the center since
        # from (-1, 1) the center is reacheable
        for (x, y) in S.difference({(0, 0)}):
            with self.subTest("no path", point=(x, y)):
                self.assertRaises(ValueError, self.gs.move, -1, 1, x, y)

    def test_move_3_players(self):
        # SETUP: radius 2 ball
        #
        #           . 0 . 
        #          . . 1 2 
        # board = . . 1 . .
        #          . 0 2 . 
        #           . . .  
        # 
        S = {(0, 0)}
        S = {(x+dx, y+dy) for (x, y) in S for (dx, dy) in self.NEIGHBOURHOOD}
        S = {(x+dx, y+dy) for (x, y) in S for (dx, dy) in self.NEIGHBOURHOOD}
        self.gs.board_add_iter(S)
        self.gs.player_add(3)
        self.gs.piece_add(1, 1, "0")
        self.gs.piece_add(0, -1, "0")
        self.gs.piece_add(0, 1, "1")
        self.gs.piece_add(0, 0, "1")
        self.gs.piece_add(-1, 2, "2")
        self.gs.piece_add(-1, 0, "2")

        D = {(1, 1): "0", (0, -1): "0",
            (0, 1): "1", (0, 0): "1",
            (-1, 2): "2", (-1, 0): "2",
        }

        assert len(S) == 19
        assert self.gs.board == S
        assert self.gs.pieces == D

        # STATUS after [player 0] : (1, 1) -> (-1, -1)
        #
        #           . . . 
        #          . . 1 2 
        # board = . . 1 . .
        #          . 0 2 . 
        #           . 0 . 
        # 
        with self.subTest("first move"):
            P = self.gs.move(1, 1, -1, -1)
            # Note: there are several paths leadind to (-1, -1) but this is the
            #       only one of length 2. Note the API ensures the returned
            #       path as to be the shortest.
            #
            self.assertEqual(tuple(P), ((1, 1), (-1, 1), (-1, -1)))
            # Check the round was correctly passed
            self.assertEqual(self.gs.player, 1)
            # Check pieces were correctly moved
            D.pop((1, 1))
            D[(-1, -1)] = "0"
            self.assertEqual(self.gs.pieces, D)

        # STATUS after [player 1] : (0, 0) -> (-2, 2)
        #
        #           . . . 
        #          . . 1 2 
        # board = . . 1 . .
        #          . 0 2 . 
        #           . 0 . 
        #
        with self.subTest("second move"):
            P = self.gs.move(0, 0, -2, 2)
            D.pop((0, 0))
            D[(-2, 2)] = "1"

            self.assertEqual(tuple(P), ((0, 0), (0, 2), (-2, 2)))
            self.assertEqual(self.gs.player, 2)
            self.assertEqual(self.gs.pieces, D)

        # STATUS after [player 1] : (-1, 0) -> (-1, 1)
        #
        #           . . . 
        #          . . 1 2 
        # board = . . 1 2 .
        #          . 0 . . 
        #           . 0 . 
        #
        with self.subTest("third move"):
            P = self.gs.move(-1, 0, -1, 1)
            D.pop((-1, 0))
            D[(-1, 1)] = "2"

            self.assertEqual(tuple(P), ((-1, 0), (-1, 1)))
            # Since we have two players, the player counter should wrap to 0
            self.assertEqual(self.gs.player, 0)
            self.assertEqual(self.gs.pieces, D)

    def test_move_force_errors(self):
        # SETUP four tiles board
        S = {(0, 0), (1, 0), (2, 0), (3, 0)}
        self.gs.board_add_iter(S)
        self.gs.piece_add(0, 0, "j")
        self.gs.piece_add(2, 0, "j")
        D = {(0, 0): "j", (2, 0): "j"}

        assert self.gs.board == S 
        assert self.gs.pieces == D 
        assert self.gs.player_num == 0

        # Moving piece from out-of-board tile
        #
        #  Note: 1, 0 is a free and empty position. Thus the error is ONLY 
        #  the initial location being out-of-board
        with self.subTest("from out-of-board"):
            self.assertRaises(ValueError, self.gs.move_force, -1, 0, 1, 0)

            # Safe recovery
            self.assertEqual(self.gs.board, S)
            self.assertEqual(self.gs.pieces, D)
            self.assertEqual(self.gs.player_num, 0)

        with self.subTest("from empty tile"):
            self.assertRaises(ValueError, self.gs.move_force, 3, 0, 1, 0)

            # Safe recovery
            self.assertEqual(self.gs.board, S)
            self.assertEqual(self.gs.pieces, D)
            self.assertEqual(self.gs.player_num, 0)

        with self.subTest("to out-of-board"):
            self.assertRaises(ValueError, self.gs.move_force, 0, 0, -1, 0)

            # Safe recovery
            self.assertEqual(self.gs.board, S)
            self.assertEqual(self.gs.pieces, D)
            self.assertEqual(self.gs.player_num, 0)

        with self.subTest("to occupied tile"):
            self.assertRaises(ValueError, self.gs.move_force, 0, 0, 2, 0)

            # Safe recovery
            self.assertEqual(self.gs.board, S)
            self.assertEqual(self.gs.pieces, D)
            self.assertEqual(self.gs.player_num, 0)

    def test_move_force(self):
        # SETUP radius 1 circle
        #
        #          0 . 
        # board = j u .
        #          1 . 
        #
        S = {(0, 0)}.union(set(self.NEIGHBOURHOOD))
        self.gs.board_add_iter(S)
        self.gs.player_add(2)
        self.gs.piece_add(1, -1, "j")
        self.gs.piece_add(0, 0, "u")
        self.gs.piece_add(1, 0, "0")
        self.gs.piece_add(0, -1, "1")
        D = {(1, -1): "j", (0, 0):"u", (1, 0):"0", (0, -1):"1"}

        assert self.gs.board == S 
        assert self.gs.pieces == D
        assert self.gs.player_num == 2
        assert self.gs.player == 0

        # MOVE `0`: (1, 0) to (-1, 0)
        #
        #          . .
        # board = j u .
        #          1 0
        #
        # Note: this should be impossibile without forcing since u is unjump
        with self.subTest("over unjump, in turn"):
            self.gs.move_force(1, 0, -1, 0)
            D[(-1, 0)] = D.pop((1, 0))

            self.assertEqual(self.gs.board, S) 
            self.assertEqual(self.gs.pieces, D)
            self.assertEqual(self.gs.player, 0)

        # MOVE `1`: (1, 0) to (-1, 0)
        #
        #          . 1
        # board = j u .
        #          . 0
        #
        # Note: this should be impossibile without forcing since it's P0's turn
        with self.subTest("over unjump, out of turn"):
            self.gs.move_force(0, -1, 0, 1)
            D[(0, 1)] = D.pop((0, -1))

            self.assertEqual(self.gs.board, S)
            self.assertEqual(self.gs.pieces, D)
            self.assertEqual(self.gs.player, 0)

        # MOVE `j`: (1, -1) -> (-1, 1)
        #
        #          . 1
        # board = . u j
        #          . 0
        #
        # Note: this should be impossibile since `j` cannot be moved normaly
        with self.subTest("over unjump, jump"):
            self.gs.move_force(1, -1, -1, 1)
            D[(-1, 1)] = D.pop((1, -1))

            self.assertEqual(self.gs.board, S)
            self.assertEqual(self.gs.pieces, D)
            self.assertEqual(self.gs.player, 0)


    def test_player_add(self):
        # Initially there should be no players
        with self.subTest("initial value is 0"):
            self.assertEqual(self.gs.player_num, 0)
            self.assertEqual(self.gs.player, None)

        # Adding the first player makes player 0 the current player
        with self.subTest("Adding first player"):
            self.gs.player_add(1)
            self.assertEqual(self.gs.player_num, 1)
            self.assertEqual(self.gs.player, 0)

        # Default Value adds one player
        for i in range(2, 5+1):
            with self.subTest("adding players, Default", i=i):
                self.gs.player_add()
                self.assertEqual(self.gs.player_num, i)
                self.assertEqual(self.gs.player, 0)

        # Adding custom number of players
        n = 5
        for num in (3, 5, 7, 11):
            with self.subTest("adding players, Default", num=num):
                self.gs.player_add(num)
                n += num 
                self.assertEqual(self.gs.player_num, n)
                self.assertEqual(self.gs.player, 0)

        # Testing Error: non-int number of new player
        for num in (1.0, '3', (5,)):
            with self.subTest("non-int new players", num=num):
                self.assertRaises(TypeError, self.gs.player_add, num)

                # Safe Recovery
                self.assertEqual(self.gs.player_num, n)
                self.assertEqual(self.gs.player, 0)

        # Testing Error: num < 1
        for num in range(-1, 1):
            with self.subTest("non positive new players", num=num):
                self.assertRaises(ValueError, self.gs.player_add, num)

                # Safe Recovery
                self.assertEqual(self.gs.player_num, n)
                self.assertEqual(self.gs.player, 0)

    def test_player_pop_behaviour(self):
        # Removing from empty state does nothing
        self.gs.player_pop()

        with self.subTest("pop with no player"):
            self.assertEqual(self.gs.player_num, 0)
            self.assertEqual(self.gs.player, None)

        # Removing the last player set current player to None
        self.gs.player_add()

        assert self.gs.player_num == 1
        assert self.gs.player == 0

        self.gs.player_pop()
        with self.subTest("pop last"):
            self.assertEqual(self.gs.player_num, 0)
            self.assertEqual(self.gs.player, None)


        # Removing last player when this is the current player set P0 as
        #  current player
        #
        # Also, the default removes only one player
        self.gs.player_add()
        self.gs.player_add()
        self.gs.player_next()

        assert self.gs.player_num == 2
        assert self.gs.player == 1

        self.gs.player_pop()
        with self.subTest("pop current player"):
            self.assertEqual(self.gs.player_num, 1)
            self.assertEqual(self.gs.player, 0)

        # Removing multiple players form empty state does nothing
        self.gs.player_pop()

        assert self.gs.player_num == 0
        assert self.gs.player == None

        self.gs.player_pop(7)
        with self.subTest("pop many with no player"):
            self.assertEqual(self.gs.player_num, 0)
            self.assertEqual(self.gs.player, None)

        # Removing more than possibile does nothing more than removing all
        self.gs.player_add(3)

        assert self.gs.player_num == 3
        assert self.gs.player == 0

        self.gs.player_pop(7)
        with self.subTest("pop too many"):
            self.assertEqual(self.gs.player_num, 0)
            self.assertEqual(self.gs.player, None)

        # Removing many actually removes that many
        self.gs.player_add(10)

        assert self.gs.player_num == 10
        assert self.gs.player == 0

        self.gs.player_pop(7)
        with self.subTest("pop 7 out of 10"):
            self.assertEqual(self.gs.player_num, 3)
            self.assertEqual(self.gs.player, 0)

    def test_player_pop_error(self):

        # The method only accepts integers values
        for num in (3.0, "3", (3,)):
            with self.subTest("typecheck", t=type(num)):
                self.assertRaises(TypeError, self.gs.player_pop, num)

        # We cannot remove players while they have pieces on board.
        # SETUP
        S = {(0, 0)}
        self.gs.board_add_iter(S)
        self.gs.player_add(2)
        self.gs.piece_add(0, 0, "0")

        assert self.gs.board == {(0, 0)}
        assert self.gs.pieces == {(0, 0): "0"}
        assert self.gs.player_num == 2
        assert self.gs.player == 0

        with self.subTest("Removing with pieces on board"):
            self.assertRaises(ValueError, self.gs.player_pop, 2)




























