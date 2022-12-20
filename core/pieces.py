class game_state:
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
        # sets of object that can be jumped over (but not on)
        self._ch_jump = set()

        # list of object that cannot be jumped over nor on
        self._ch_unjump = set()


        # current player
        # | None: when no player exists
        # | Int : when there is at least a player (from 0 to n-1)
        #
        # Implementation Note: Add getters and setters for _player.
        self._player = None

        # number of players
        self._player_num = 0

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
            raise ValeuError(f"unrecognized kind = \"{kind}\"")

        # Check that if kind is a valid player kind, it refers existing players
        if kind.isdigit() and not (0 <= int(kind) < self._player_num):
            raise ValueError(f"adding piece for uninitialized player "
                f"{int(king)}")

        # Insert the piece
        self._pieces[(x, y)] = kind
        self._cache()

    def piece_remove(self, x, y):
        ''' Remove the object currently stored at position (x, y). No error is
        thrown if no piece is at position (x, y).
        '''

        pass

    def piece_remove_all(self, f=None):
        ''' Remove all objects for which f returns true. If no function is
        specified all objects are removed.

        f(x, y, kind) -> bool   : `x`, `y` are the piece coordinate
        |                         `kind` is the object kind (see `.add`)

        Implementation Note: the default case should be f=lambda x, y, k: True
        '''

        pass

    # board methods
    def board_add(self, x, y):
        ''' Add position x, y on the board. If (x, y) was already on board
        nothing happens.

        Errors      : ValueError if x, y are not integer values
        '''

        if type(x) != int or type(y) != int:
            TypeError(f"Board entries have type int, got ({type(x)}, "
                f"{type(y)}) instead")

        self._board.add((x, y))

    def board_add_iter(self, iterator):
        ''' Add the couples in `iterator` to the board. Those elements that 
        were already on the board are clearly not added again.

        Errors      : ValueError if `iterator` objects are not couples of Int
        '''
        pass

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

    def board_remove_all(self, f):
        ''' Remove all pieces of board for which f returns true. If no function is specified all objects are removed.

        f(x, y) -> bool     : `x`, `y` are the hole coordinates

        Errors:             : ValueError if a removed position contains a piece
        |                       consider removing pieces first with the same
        |                       filter f and method `piece_remove_all`
        '''
        pass

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


    def player_num(self):
        ''' Returns the number of currently playing players

        Implementation Note: alias to len(_player_pieces)
        '''
        pass

    # game mechanics methods
    def paths(self, x, y):
        ''' Return a list of positions that a piece in (x, y) can reach
        
        Errors      : ValueError if (x, y) not on board

        Note: (x, y) does not need to be a currently placed piece (although
        the relevance of using this method for empty positions is unclear)
        '''
        pass

    def move(self, x1, y1, x2, y2):
        ''' Move a piece in position (x1, y1) to position (x2, y2). Returns a shortest path from (x1, y1) to (x2, y2) including both points.
        (x1, y1) has to be a piece of the current player. 
        The next player then becomes the new `current player`.

        Errors      : ValueError if (x1, y1) is not a piece (use add instead!)
        |           : ValueError if (x1, y1) is not a current player piece
        |               (use `move_no_check` instead)
        |           : ValueError if (x2, y2) is a piece or out-of-board.
        |           : ValueError if there is no valid path from the two points.
        |               (if this is intended, use `move_no_checks` instead)
        '''
        pass

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
        pass

    # miscellaneous methods
    def shift(self, dx, dy):
        '''shift each element internal representation.

        Usage Note: This method might create complications just for the sake
        of keeping coordinates small. Its usage is not recommended and might
        be deprecated in future version
        '''
        pass

    # debug methods
    def __str__(self):

        out = (
            f"board = {self._board}\n"
            f"pieces = {self._pieces}\n"
            f"player = ({self._player}: {self._player_num})"
            )

        return out




gs = game_state()

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

        case _ : 
            print("I didn't understand that")

    print(gs)