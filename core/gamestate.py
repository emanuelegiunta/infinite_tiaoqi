from collections import deque



class GameState:
    ''' Class containing abstract informations on the current game
    
    What is it:
    Implements the basic game mechanics, path-finding, movement, and manages player rounds (leaving however some controll over these things).
        
    What it DOES assume:
    This class assumes basic rules [and some variation] for tiaoqi applies. Although some variations are provided, those are internal to the class
    and no API to dynamically alter those is provided.

    What it DOES NOT assume:
    This class is agnostic to board shape (which can be even dynamically adjusted), number of pieces, number of players, existence of unjumpable pieces
    '''
    
    def __init__(self): 

        # dictionary of pieces. Each piece is an entry of the form
        #  (x, y) -> kind
        self._pieces = {}

        # sets of points on the board. Entries of the form
        #  (x, y)
        self._board = set()

        # Cached objects: To speedup membership checks (frequent operation)
        #  objects are cached to sets to allow for fast membership checks
        #
        # set of object that can be jumped over (but not on)
        self._ch_jump = set()

        # set of all objects that occupies a tile
        self._ch_pieces = set()


        # current player
        # | None: when no player exists
        # | Int : when there is at least a player (from 0 to n-1)
        #
        # Implementation Note: Add getters and setters for _player.
        self._player = None

        # number of players
        self._player_num = 0

        # CONSTANTS
        #  difference between a tile and neighbouring cells.
        #  
        #  Note: This need not to be a constant. If one wish to explore more 
        #        interesting topologies it's enough to lowercase this and
        #        implement getters/setters (and adjust a bit .paths)
        self._NEIGHBOURHOOD = ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), 
            (1, -1))

    # piece methods
    def piece_add(self, x, y, kind):
        ''' Add a new piece on the board at position (x, y).

        kind: specifies the type of object inserted. Accepted values are
        |   "1", "2", ...       :    players p i-th piece.
        |   "j", "jump"         :    jumpable, non-playing object
        |   "u", "unjump"       :    unjumpable, non-playing object

        Errors                  : ValueError if (x, y) is occupied or not on
        |                           board
        |                       : ValueError if `kind` is malformed
        |                       : ValueError if player p[i] does not exists
        |                           (use `player_add`)
        '''
            
        # Check (x, y) on board
        if (x, y) not in self._board:
            raise ValueError(f"Adding piece ({x}, {y}, {kind}) out of board")

        # Check (x, y) not occupied
        if (x, y) in self._pieces.keys():
            raise ValueError(f"Adding piece ({x}, {y}, {kind}) into occupied "
                "space")

        # Check that kind is valid
        if not (kind == "j" or kind == "u" or kind.isdigit()):
            raise ValueError(f"unrecognized kind = \"{kind}\"")

        # Check that if kind is a valid player kind, it refers existing players
        if kind.isdigit() and not (0 <= int(kind) < self._player_num):
            raise ValueError(f"adding piece for uninitialized player "
                f"{int(kind)}")

        # Insert the piece
        self._pieces[(x, y)] = kind
        self._cache()

    def piece_remove(self, x, y):
        ''' Remove the object currently stored at position (x, y). No error is
        thrown if no piece is at position (x, y).

        Implementation Note: No error should be thrown from this function as
        no typecheck is performed on x, y (if they are malformed, (x, y) is
        not going to be mapped to any value in self._pieces). 
        '''

        # Pop with default value raises no error when the key is not present
        self._pieces.pop((x, y), None)
        self._cache()

    def piece_remove_all(self, f=None):
        ''' Remove all objects for which f returns true. If no function is
        specified all objects are removed.

        f(x, y, kind) -> bool   : `x`, `y` are the piece coordinate
        |                         `kind` is the object kind (see `.add`)

        Implementation Note: the default case should be f=lambda x, y, k: True
        '''

        if f is None:
            # Instead of actually removing all items, we simply reset the
            # dictionary
            self._pieces = {}

        else:
            self._pieces = {(x, y): k for (x, y), k in self._pieces.items()
                if not f(x, y, k)}
        
        self._cache()

    # board methods
    def board_add(self, x, y):
        ''' Add position x, y on the board. If (x, y) was already on board
        nothing happens.

        Errors      : TypeError if x, y are not integer values
        '''

        if type(x) != int or type(y) != int:
            raise TypeError(f"Board entries have type int, got ({type(x)}, "
                f"{type(y)}) instead")

        self._board.add((x, y))
        self._cache()

    def board_add_iter(self, iterator):
        ''' Add the couples in `iterator` to the board. Those elements that 
        were already on the board are clearly not added again.

        Errors      : ValueError if `iterator` objects are not couples of Int
        '''
        
        new_tiles = {t for t in iterator}

        # We type-check each entry. This might slow down the insertion but
        #  boards are assumed to be small and here safety beats peformances
        f = lambda c: type(c[0]) != int or type(c[1]) != int
        if any(filter(f, new_tiles)):
            raise TypeError(f"Board entries have type int!")

        self._board = self._board.union(new_tiles)
        self._cache()

    def board_remove(self, x, y):
        ''' Remove the board place at position x, y. No error is raised if
        (x, y) was not on board.

        Errors      : ValueError if (x, y) contains a piece. Consider removing 
        |               it first
        '''

        if (x, y) in self._pieces.keys():
            raise ValueError(f"Removing board hole {(x, y)} while it "
                "cointains a piece")

        self._board.discard((x, y))
        self._cache()

    def board_remove_all(self, f=None):
        ''' Remove all pieces of board for which f returns true. If no function is specified all objects are removed.

        f(x, y) -> bool     : `x`, `y` are the hole coordinates

        Errors:             : ValueError if a removed position contains a piece
        |                       consider removing pieces first with the same
        |                       filter f and method `piece_remove_all`
        '''
        
        if f is None:
            if self._pieces:
                raise ValueError("Removing all tiles while pieces are "
                    "still on the board")

            self._board = set()

        else:
            # Note: This requires in the worst case 2N evaluations of f
            #       it might be worth to optimize this in the future
            #  
            # check no piece makes f evaluates to True
            if any(filter(lambda p: f(*p), self._pieces.keys())):
                raise ValueError("Removing some tiles while pieces are "
                    "still on them")

            self._board = {(x, y) for (x, y) in self._board if not f(x, y)}
            self._cache()


    # player methods
    def player_add(self):
        ''' Add a player with no pieces
        
        Implementation Note: Simply append [] to the list of players and
        set `_player` to 0 if it was `None`.
        '''
        
        self._player_num += 1

        if self._player is None:
            self._player = 0

    def player_pop(self):
        ''' Remove the last player.
        
        If the removed player was also the current player, the current player
        becomes player 0. When player 0 is removed, current player is set to
        None.

        Error       : ValueError if the pop-ed player still has pieces on the
        |               board. To remove all pieces of a player, call
        |               `.piece_remove_all(f)` with f being true for all
        |               pieces of kind p{i}.
        '''

        # Nothing happens if there is no player.
        if self._player_num == 0:
            return None

        # Check if there is any piece left belonging to the last player.
        #  -- Note: this code ASSUMES self._player_num > 0
        for (x, y) in self._pieces.keys():
            if self._pieces[(x, y)] == str(self._player_num - 1):
                raise RuntimeError(f"Removing player {self._player_num - 1}"
                    f"while it still owns pieces on the board.")

        # We adjust `_player` so that it matches the documented behaviour
        if self._player_num == 1:
            self._player = None
        elif self._player_num == self._player:
            self._player = 0

        # Finally we reduce the numer of players by 1
        self._player_num -= 1


    # game mechanics methods
    def paths(self, x, y):
        ''' Return a DICT of positions that a piece in (x, y) can reach
        structured as a tree, i.e. if p2 is the father of p1 then

            tree[p1] = p2

        The root of the tree points to None
        
        Errors      : ValueError if (x, y) not on board

        Note: (x, y) does not need to be a currently placed piece (although
        the relevance of using this method for empty positions is unclear).

        Note: If a set of reacheable position is required one can use the 
                set of keys, i.e. set(tree.keys()), as a surrogate
        '''
        
        # BST Search
        tree = {(x, y): None}
        queue = deque()

        queue.append((x, y))

        # Search for jump chain [Note, this does not capture single jumps]
        while queue:
            (x_tmp, y_tmp) = queue.popleft()

            # Examine the 6 possibile tiles you can reach from it
            for dx, dy in self._NEIGHBOURHOOD:

                # First, check that we are not landing in an element we already
                #  explored
                goal = (x_tmp + 2*dx, y_tmp + 2*dy)
                jump = (x_tmp + dx, y_tmp + dy)

                # If we visited the node, halt
                if goal in tree.keys():
                    continue

                # If the jumping node is not a jumpable piece, halt
                if jump not in self._ch_jump:
                    continue

                # If the goal node is not a tile or it is occupied, halt
                if (goal in self._ch_pieces) or (goal not in self._board):
                    continue

                # If all checks passed we have that
                #  goal is a free tile we did not explore before
                #  jump is a jumpable piece
                queue.append(goal)
                tree[goal] = (x_tmp, y_tmp)

        # Search for single jumps
        for dx, dy in self._NEIGHBOURHOOD:
            goal = (x + dx, y + dy)

            # Check goal is free and on board
            if goal in self._ch_pieces or goal not in self._board:
                continue

            # Note, we don't need to check that this places were reached before
            #  (it can be shown that cells one can chain-jump into have a 
            #  different invariant than the neighbouring cells)
            #
            # Notice2: this holds for all tologies in which the symmetric
            #  closure of the neighbour (N union -N for (0,0)) do not admits
            #  a set of four or more points aligned containing the center.
            # 
            # We can then add this to the tree
            tree[goal] = (x, y)

        return tree

    def move(self, x1, y1, x2, y2):
        ''' Move a piece in position (x1, y1) to position (x2, y2). Returns a shortest path from (x1, y1) to (x2, y2) including both points.
        (x1, y1) has to be a piece of the current player. 
        The next player then becomes the new `current player`.

        Errors      : ValueError if (x1, y1) is not a piece (use add instead!)
        |           : ValueError if (x1, y1) is not a current player piece
        |               (use `move_no_check` instead)
        |           : ValueError if there is no valid path from the two points.
        |               (if this is intended, use `move_no_checks` instead)
        '''
    
        # Check that x1, y1 is a current player piece
        if self._pieces.get((x1, y1), None) != str(self._player):
            # choose the right error message

            msg = ""
            if (x1, y1) not in self._pieces.keys():
                msg = f"Moving a piece from empty location ({x1}, {y1})."

            elif not self._pieces[(x1, y1)].isdigit():
                kind = self._pieces[(x1, y1)]
                msg = (f"Moving non playing piece from location ({x1}, {y2}) "
                    f"and kind {kind}")

            else:
                kind = self._pieces[(x1, y1)]
                msg = (f"Moving a piece of player {kind} from ({x1}, {y1}) "
                    f"during the turn of player {self._player}. If this is "
                    f"intentional, use `.player` to change player round first")

            raise ValueError(msg)

        # Get the path tree
        tree = self.paths(x1, y1)

        # Check that a path exists
        if (x2, y2) not in tree.keys():
            # Choose the right error message
            msg = ""
            if (x2, y2) not in self._board:
                msg = f"Moving a piece to ({x2}, {y2}), which is not on board!"

            else:
                msg = (f"Moving a piece from ({x1}, {y1}) to ({x2}, {y2}) but "
                    "no path is available")

            raise ValueError(msg)

        # We can now move since
        #   1. a path is guaranteed
        #       1.1 hence the location is on board and is free
        #   2. x1, y1 contains a corrent player piece
        #       2.1 Thus x1, y1 is in _piece (we can pop() without default)
        self._pieces[(x2, y2)] = self._pieces[(x1, y1)]
        self._pieces.pop((x1, y1))

        self._cache()

        # We update player's turns
        self._player = (self._player + 1)%self._player_num

        # We build the path from tree
        path = []
        point = (x2, y2)
        while point:    # We use the fact that the root's father is None.
            path.append(point)
            point = tree[point]

        path.reverse()
        return path

    def move_force(self, x1, y1, x2, y2):
        ''' Move a piece from position (x1, y1) to position (x2, y2). Its
        behaviour is similar to `remove(x1, y1)`, `add(x2, y2, <kind>)` with
        the exception that no knowledge of `kind` is required, and that there
        has to be a piece in (x1, y1)

        Errors      : ValueError if (x1, y1) is not a piece
        |           : ValueError if (x2, y2) is a piece or not on board
        '''
        pass

    # Memory Caching Methods
    def _cache(self):
        ''' PRIVATE METHOD

        Cache data after some modifications have been performed. Currently has 
        to be called only after ANY modification of `._pieces`.
        '''
        
        # _ch_jump is the set of `jumpable pieces`
        self._ch_jump = {(x, y) for (x, y), kind in self._pieces.items() 
            if kind != "u"}

        # _ch_pieces is the set of all pieces
        self._ch_pieces = set(self.pieces.keys())


    # miscellaneous methods
    def shift(self, dx, dy):
        '''shift each element internal representation.

        Usage Note: This method might create complications just for the sake
        of keeping coordinates small. Its usage is not recommended and might
        be deprecated in future version
        '''
        pass


    # Getters and Setters
    @property
    def pieces(self):
        ''' Return a dictionary of pieces of the form (x, y) -> kind

        Implementation Note: DO NOT return internals as they are passed by
        reference. Even if the output has the same structure, a deep copy
        should be made first
        '''

        # Note: As Tuples and Strings in python3 are immutable, a shallow
        #       copy is enough                           
        return self._pieces.copy()

    @pieces.setter
    def pieces(self, x):
        raise AttributeError(f"Attempted to set pieces. Use `piece_add` "
            "and `piece_remove` instead")

    @property
    def board(self):
        ''' Returns a set-like object whose entries are board locations (x, y)

        Implementation Note: DO NOT return internals as they are passed by
        reference. Even if the output has the same structure, a deep copy should be made first.
        '''

        # Note: As tuples are immutable, returning a shallow copy is ok
        return self._board.copy()

    @board.setter
    def board(self, x):
        raise AttributeError(f"Attempted to directly set the board. Use "
            "`board_add` and `board_remove` instead.")

    @property
    def player_num(self):
        ''' Return the number of currently initialized players
        '''
        return self._player_num

    @player_num.setter
    def player_num(self, x):
        raise AttributeError(f"Attempted to set players number to {x}. Use "
            "`player_add`/`player_pop` instead.")

    @property
    def player(self):
        ''' Return the current player's index
        '''
        return self._player

    @player.setter
    def player(self, x):
        ''' Set the current player

        Errors  : TypeError if x is not an integer
        |       : ValueError if x is not in 0 < x < player_num - 1
        '''

        if type(x) != int:
            raise TypeError("Setting current player's index to non-integer.")

        if not (0 < x < self._player_num):
            raise ValueError("Setting current player's index to an "
                f"uninitialized player {x}")

        self._player = x

    # debug methods
    def __str__(self):

        out = (
            #f"board = {self._board}\n"
            f"pieces = {self._pieces}\n"
            f"player = ({self._player}: {self._player_num})")

        return out




#==============================================================================
# Quick Interactive Object for Debugging

if __name__ == "__main__":
    gs = GameState()

    # create a "large" square
    L = [(x,y) for x in range(-4, 5) for y in range(-4, 5)]
    gs.board_add_iter(L)

    # create 2 player
    gs.player_add()
    gs.player_add()

    # position 4 pieces
    gs.piece_add(0, 0, "0")
    gs.piece_add(0, 2, "0")
    gs.piece_add(1, 0, "1")
    gs.piece_add(-1, 2, "1")

    while True:
        cmd = input("> ")
        argv = cmd.split(" ")
        match argv[0]:
            case "ab": 
                gs.board_add(int(argv[1]), int(argv[2]))

            case "ap":
                gs.piece_add(int(argv[1]), int(argv[2]), argv[3])

            case "au":
                gs.player_add()

            case "p":
                print(f"paths = {gs.paths(int(argv[1]), int(argv[2]))}\n")

            case "m":
                gs.move(*(int(argv[i]) for i in range(1,5)))

            case _: 
                print("I didn't understand that")

        print(gs)
