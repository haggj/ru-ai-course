import hashlib
from enum import Enum
from itertools import chain

import numpy as np
import random

EMPTY_SPACE = 0

class Version(Enum):

    NAIVE = "Naive"
    """
    Iterate over all empty fields and check which numbers yield legal state.

    Description:
    The initial version of our algorithm was the \verb|Naive| implementation.
    For a given state this version iterates over all fields of the board.
    For each empty fields this implementation assigns all allowed values to this empty field.
    For each assigned value it then checks if the resulting field is still in a valid state or not.
    Therefore, the function \verb|is_legal_state()| is called for each possible value on each empty field.
    If the field is sill in a valid state, the particular move is considered to be legal.

    Evaluation:
    This version is very inefficient because it loops multiple times over the field to determine a 
    single valid move. This makes the computation of all legal moves for a given state very slow.
    """


    IMPROVED = "Improved"
    """
    Use assigned values to find allowed moves for each field.
    
    Description:
    This improved version avoids any call to \verb|is_legal_state()| to improve the performance of the search.
    This is realized by actively computing the valid moves for a given empty field.
    Based on the values found in the row, column and subgrid the empty field belongs to, one can compute the values which can be assigned to the empty field.
    
    Evaluation:
    This version improves the inefficient \verb|Naive| implementation.
    However, it still suffers from a huge branching factor and is not able to find a solution for
    a given field in a short period of time.
    """

    SORTED = "Sorted"
    """
    Same as improved, but sort moves by the number of possible moves per field.
    
    Description:
    This implementation is almost the same than the \verb|Improved| version.
    The only difference is that the returned legal moves are sorted.
    We want to make sure, that the DFS applies moves to fields first, which have less options available.
    This speeds up the algorithm because usually a Sudoko field is solved most efficiently by assigning values to those fields first, which have only one option left.
    If a field has only one option left, there is no other value we can assign to it.
    Thus, we can be sure that we do not have to backtrack our DFS tree assuming there is a unique solution to the field.
    
    Evaluation:
    By sorting the legal moves by the amount of moves per field we can solve Sudoku fields with a unique solution efficiently.
    Effectively, this bypasses the huge branching factor if a unique solution exists.
    If there might be more than one solution the branching factor still heavily influences the search tree.
    """

    STORE_LEGAL = "Store"
    """
    Compute the allowed values per field and store them. Update values if moves are applied.
    
    Description:
    The  \verb|Improved| and  \verb|Sorted| versions compute the allowed values for an empty field based on the corresponding row, colum and subgrid.
    However, they perform this computation for each field again if \verb|get_legal_moves()| is computed.
    This can be avoided by caching the result of this computation.
    This implementation introduces a cache which stores the values which can be assigned to each field.
    Once a move is applied, all affected fields of the cache are updated.
    
    Evaluation:
    Since this approach introduces additional data structures, the deepcopy operation is more expensive in terms of time and memory.
    As a result, the non-recursive implementation is even slower than if we are using the \verb|Sorted| approach.
    However, if we avoid to deepcopy the state by relying on a recursive implementation of DFS, this version is the most efficient one.
    It even outperforms the CSP solver by ORTools for fields which have a unique solution.
    """

class SudokuBoard:

    def __init__(self, n=3, seed=None):
        self.size = n*n
        self.size_sqrt = n
        self._board = [[EMPTY_SPACE] * self.size for i in range(self.size)]  # create an empty board
        self._board = np.array(self._board)
        self._seed = seed
        random.seed(seed)

    def __hash__(self):
        """
        The numpy array stores the underlying data as bytes.
        This allows us to compute the hash of the state efficiently.
        """
        p = self._board.data.tobytes()
        hash_value = hashlib.md5(p).hexdigest()
        return int(hash_value, 16) % 10 ** 16

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __str__(self):
        """
        Returns a string representation of the board.
        """
        all_rows = []
        small_space = ' '
        big_space = '  '

        for x_i, row in enumerate(self._board):
            output = ''
            for y_i, field in enumerate(row):
                # add number
                output += str("." if field == 0 else field)
                # add space if not last number in row
                space = big_space
                if field > 9:
                    space = small_space
                if y_i < self.size - 1:
                    output += space
                    # add seperator at end of subgrid if not last number
                    if (y_i + 1) % self.size_sqrt == 0:
                        output += '| '
            # finish row
            all_rows.append(output)
            # add seperator at end of subgrid if not last row
            if ((x_i + 1) <= self.size - 1) and ((x_i + 1) % self.size_sqrt == 0):
                seperator = ''
                for char in output:
                    seperator += '-'
                all_rows.append(seperator)
        return '\n'.join(all_rows)

    def get_legal_moves(self, version: Version = Version.NAIVE):
        """
        Returns a list of legal moves for the current state based on the specified implementation.
        """
        if version == Version.NAIVE:
            return self.naive_get_legal_moves()
        elif version == Version.STORE_LEGAL:
            return self.cache_get_legal_moves()
        else:
            return self.improved_get_legal_moves(version)

    def set_board(self, board):
        self._board = board

    def get_row(self, row):
        if not isinstance(row, int) or row < 0 or row >= self.size:
            raise Exception('Invalid row: ' + str(row))

        return [self._board[x][row] for x in range(self.size)]
    
    def is_legal_state(self):
        """
        Check if this state is a legal state, i.e. if there are conflicting fields in the board.
        """
        # Check if the numbers are unique in each row
        for row in self._board:
            if len(np.unique(row[row!=0])) != len(np.nonzero(row)[0]):
                return False
            
        # Check if the numbers are unique in each column
        for col in self._board.T:
            if len(np.unique(col[col!=0])) != len(np.nonzero(col)[0]):
                return False
            
        # Check if the numbers are unique in each subgrid
        for i in range(0, self.size, self.size_sqrt):
            for j in range(0, self.size, self.size_sqrt):
                subgrid = self._board[i:i+self.size_sqrt, j:j+self.size_sqrt]
                if len(np.unique(subgrid[subgrid!=0])) != len(np.nonzero(subgrid)[0]):
                    return False
        
        return True

    def apply_move(self, move):
        """
        Apply the specified move to the board.
        """
        x, y, val = move
        self._board[x][y] = val
        self.last_move = move

        if hasattr(self, "_move_cache"):
            del self._move_cache[(x,y)]
            self.update_move_cache(move)

    def undo_move(self, move):
        """
        Undo the specified move from the board.
        """
        x, y, val = move
        self._board[x][y] = EMPTY_SPACE

        if hasattr(self, "_move_cache"):
            self._move_cache = self.get_move_cache()

    def is_complete(self):
        """
        Checks if each field in the board contains a value and if the board is in a legal state.
        """
        for x in range(self.size):
            for y in range(self.size):
                if self._board[x][y] == EMPTY_SPACE:
                    return False
        if self.is_legal_state():
            return True
        print(self)
        raise Exception("Board complete but no in legal state.")

    def remove_random_number(self):
        """
        Removes a random number from the board.
        """
        x = random.randrange(0, self.size)
        y = random.randrange(0, self.size)
        # if random field is not null remove number
        if self._board[x][y] != 0:
            self._board[x][y] = 0
        # repeat until none empty field found
        else:
            # TODO: !!! Infinite Loop on empty board !!!
            self.remove_random_number()

    ################################################################################################
    #                                          NAIVE                                               #
    ################################################################################################

    def naive_get_legal_moves(self):
        """
        Test for each empty field and each number if the resulting board is in a legal state.
        This function iterates over the whole board to detect empty fields. It then iterates over
        all possible values and applies them to the field. For each combination of empty field and
        possible value, the function self.is_legal_state() is called.
        """
        legal_moves = []
        fields = set()
        empty_fields = 0

        for x in range(self.size):
            for y in range(self.size):
                if self._board[x][y] == EMPTY_SPACE:
                    empty_fields += 1
                    for i in range(1, self.size + 1):
                        self._board[x][y] = i
                        if self.is_legal_state():
                            legal_moves.append((x, y, i))
                            fields.add((x, y))
                    self._board[x][y] = EMPTY_SPACE

        if len(fields) == empty_fields:
            return legal_moves
        # If there is not a valid move for each field no solution exists
        return []

    def get_first_legal_move(self):
        """
        Returns the first legal move for the current state.
        """
        legal_moves = []

        for x in range(self.size):
            for y in range(self.size):
                if self._board[x][y] == EMPTY_SPACE:
                    for i in range(1, self.size + 1):
                        self._board[x][y] = i
                        if self.is_legal_state():
                            return (x, y, i)
                    self._board[x][y] = EMPTY_SPACE

        raise Exception("No legal move found.")

    ################################################################################################
    #                                   IMPROVED / SORTED                                          #
    ################################################################################################

    @property
    def sub_grids(self):
        """
        Compute the square sub grids of the board. Returns a list of subgrids.
        A subgrid is a list of values.
        """
        grid_size = self.size_sqrt
        for i in range(0, self.size, grid_size):
            for j in range(0, self.size, grid_size):
                yield np.unique(self._board[i:i+grid_size, j:j+grid_size])

    def get_subgrid_index(self, x, y):
        """
        Computes the index of the subgrid, to which the field with the given coordinates belongs.
        To get the subgrid of a field:
        self.sub_grids[self.get_subgrid_index(x,y)]
        """
        return int(x // self.size_sqrt) * self.size_sqrt + int(y // self.size_sqrt)


    def improved_get_legal_moves(self, version):
        """
        Idea: Avoid calls to self.is_legal_state() by considering the existing values in the board.
        """
        allowed_values = set([i for i in range(1, self.size+1)])

        rows = [allowed_values.difference(set(row)) for row in self._board]
        cols = [allowed_values.difference(set(col)) for col in self._board.T]
        subgrids = [allowed_values.difference(set(subgrid)) for subgrid in self.sub_grids]

        legal_moves = {}
        for x in range(self.size):
            for y in range(self.size):
                if self._board[x][y] == EMPTY_SPACE:
                    subgrid = subgrids[self.get_subgrid_index(x,y)]
                    possible_values = rows[x].intersection(cols[y]).intersection(subgrid)
                    if not possible_values:
                        # If there is not a valid move for each field no solution can be found
                        return []
                    for i in possible_values:
                        legal_moves.setdefault((x, y), []).append((x, y, i))

        if version == Version.SORTED:
            sorted_list = sorted(legal_moves.values(), reverse=True, key=len)
            res = list(chain.from_iterable(sorted_list))
        else:
            res = list(chain.from_iterable(legal_moves.values()))
        return res

    ################################################################################################
    #                                       STORE LEGAL                                            #
    ################################################################################################

    def get_move_cache(self, field=None):
        """
        Returns all possible moves based on the current board.
        If field is specified, this function returns all possible moves
        for this field. Otherwise, the possible field for the whole field are computed.
        """
        move_cache = {}

        allowed_values = set([i for i in range(1, self.size + 1)])

        rows = [allowed_values.difference(set(row)) for row in self._board]
        cols = [allowed_values.difference(set(col)) for col in self._board.T]
        subgrids = [allowed_values.difference(set(subgrid)) for subgrid in self.sub_grids]

        if field:
            x,y = field
            subgrid = subgrids[self.get_subgrid_index(x, y)]
            return rows[x].intersection(cols[y]).intersection(subgrid)

        for x in range(self.size):
            for y in range(self.size):
                if self._board[x,y] == EMPTY_SPACE:
                    subgrid = subgrids[self.get_subgrid_index(x, y)]
                    possible_values = rows[x].intersection(cols[y]).intersection(subgrid)
                    move_cache[(x,y)] = possible_values

        return move_cache

    def get_affected_coordinates(self, x, y):
        """
        Returns a list of coordinates, which are either in the same row, colum or subgrid as the
        given coordinates.
        """
        row = set()
        col = set()
        subgrid = set()

        # Get fields of same row and column
        for j in range(self.size):
            row.add((x, j))
            col.add((j, y))

        # Get fields of same subgrid
        i_start = x - x % self.size_sqrt
        j_start = y - y % self.size_sqrt
        for i in range(self.size_sqrt):
            for j in range(self.size_sqrt):
                subgrid.add((i_start + i, j_start + j))
        return row, col, subgrid

    def update_move_cache(self, move):
        """
        Update the move_cache based on the given move.
        If reversed is True, the specified move is reversed.
        """
        x, y, val = move
        for group in self.get_affected_coordinates(x,y):
            remaining = set()
            fields = 0
            for field in group:
                if field not in self._move_cache:
                    continue
                # Recompute affected cells
                fields += 1
                if val in self._move_cache[field]:
                    self._move_cache[field].remove(val)

                remaining = remaining.union(self._move_cache[field])
            if len(remaining) < fields:
                self._move_cache[(0,0)] = set()

    def cache_get_legal_moves(self):
        """
        Compute legal moves based on cached moves.
        """
        if not hasattr(self, "_move_cache"):
            self._move_cache = self.get_move_cache()

        legal_moves = []
        for ((x,y), moves) in sorted(self._move_cache.items(), reverse=True, key=lambda item: len(item[1])):
            # print(f"{x}\t{y} -> {moves}")
            if not moves:
                return []

            for move in moves:
                legal_moves.append((x, y, move))
        return legal_moves




if __name__=="__main__":
    sb = SudokuBoard(n=3)
    sb._board[3,0] = 4
    while not sb.is_complete():
        sb.apply_move(sb.get_first_legal_move())
        print()
        print()
        print(sb)
    exit()


    print(sb)
    sb.apply_move(sb.get_first_legal_move())
    print()
    print()
    print(sb)

    sb2 = SudokuBoard(n=3)
    legal_moves_2 = sb2.get_legal_moves()

    diff = []
    for element in legal_moves_2:
        if element not in legal_moves:
            diff.append(element)

    print(diff)