import sys
import os
import json
from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy() 
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters


#######
    def find_words(self, matrix, words):
        width = len(matrix[0])
        height = len(matrix)
        output = {"width": width, "height": height, "words": []}

        for word in words:
            word_found = False
            letters = []

            # Search horizontally
            for i in range(height):
                row = matrix[i]
                for j in range(width - len(word) + 1):
                    if row[j:j+len(word)] == list(word):
                        word_found = True
                        for k in range(len(word)):
                            letters.append({"x": j+k, "y": i, "letter": word[k]})

            # Search vertically
            for i in range(width):
                column = [row[i] for row in matrix]
                for j in range(height - len(word) + 1):
                    if column[j:j+len(word)] == list(word):
                        word_found = True
                        for k in range(len(word)):
                            letters.append({"x": i, "y": j+k, "letter": word[k]})

            if word_found:
                output["words"].append({"word": word, "letters": letters})

        return output
    
    def transform_to_json(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        words = assignment.values()

        output = self.find_words(letters,words)

        return output
    
    def save_json(self, output):
        if not os.path.exists('output'):
          os.makedirs('output')

        with open('output/boards.json', 'w') as json_file:
            json.dump(output, json_file, indent=4)
        
    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable in self.domains:
            for word in set(self.domains[variable]):
                if variable.length != len(word):
                    self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False

        # If there is an overlap between x and y
        if self.crossword.overlaps[x, y] is not None:
            # Save the x and y indexes
            x_idx, y_idx = self.crossword.overlaps[x, y]
            # Save the domain values to be removed in a set to not alter the loop range
            remove = set()

            # Compare the values in x.domain with the values in y.domain
            for x_value in self.domains[x]:
                # Create a flag
                removable = True
                # Loop over variable y's domain
                for y_value in self.domains[y]:
                    # If the value can be used
                    if x_value[x_idx] == y_value[y_idx]:
                        # Dont remove
                        removable = False
                        break
                # If it's not arc consistant, add to the remove set
                if removable:
                    remove.add(x_value)   

            # Remove the values tagged to remove from the domain of variable x, and return True, meaning changes were made
            for value in remove:
                self.domains[x].remove(value)
                revised = True
        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # If no arc given
        if arcs is None:
            queue = self.crossword.overlaps.copy()
        # Inference arc
        else:
            queue = arcs

        # Loop while there are items in the queue
        while len(queue) > 0:
            # Save the item keys (variable objects), and remove it
            x, y = list(queue.keys())[0]
            queue.pop((x, y))

            # Check with revise(x, y) if any value has to be removed
            if self.revise(x, y):
                # No solution if the domain of x is empty
                if len(self.domains[x]) == 0:
                    return False
                # Add the arcs of x and its neighbors to the queue
                
                for neighbor in (self.crossword.neighbors(x) - {y}):
                    overlap = self.crossword.overlaps[x, neighbor]
                    queue[x, neighbor] = overlap
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for variable in self.crossword.variables:
            if assignment.get(variable) is None:
                return False
        return True
    
    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        used_words = set()
        for variable in assignment:
            if assignment[variable] not in used_words:
                used_words.add(assignment[variable])
            else:
                return False

            if len(assignment[variable]) != variable.length:
                return False

            # There are no conflicts between neighbors
            for neighbor in self.crossword.neighbors(variable):
                if neighbor in assignment:
                    i, j = self.crossword.overlaps[variable, neighbor]
                    if assignment[variable][i] != assignment[neighbor][j]:
                        return False
            
        return True
    
    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Agarramos var y revisamos cuales son su posibles vecinos
        # De sus posibles vecinos revisamos en assignment aquellos que no hayan sido asignados
        # una vez tenemos los vecinos que no han sido asignados evaluamos cada posible valor de var
        # y ordenamos de mayor a menor aquellos valores que eleminen mas palabras en el vecino``
        words = dict()
        for word in self.domains[var]:
            for neighbor in self.crossword.neighbors(var):
                
                if assignment[neighbor] is None:
                    i,j = self.crossword.overlaps[var,neighbor]
                    for neighbor_word in self.domains[neighbor]:
                        if word[i] != neighbor_word[j]:
                            if words[word] is None:
                                words[word] = 1
                            else:
                                words[word] = words[word] + 1
        
        sorted_words = [n for n,m in sorted(words.items(), key=lambda x: x[1])]

        return sorted_words
                                   
    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # Debemos recorrer domains
        # cada Variable que se encuentre domains debemos ver si se encuentra en assigment
        # si no se encuentra en assigment debemos ver la cantidad de palabras posibles
        # y debemos quedarnos con aquella variable que tenga la menor cantidad de palabras posibles
        i, unnasigned_variable = 0, None
        for variable in self.crossword.variables - set(assignment):
            if unnasigned_variable is None:
                i = len(self.domains[variable])
                unnasigned_variable = variable
                continue

            if len(self.domains[variable]) == i:
                    neighbor_variable = len(self.crossword.neighbors(variable))
                    neighbor_unnasigned = len(self.crossword.neighbors(unnasigned_variable))
                    if neighbor_variable > neighbor_unnasigned:
                        i = len(self.domains[variable])
                        unnasigned_variable = variable
            elif len(self.domains[variable]) < i:
                i = len(self.domains[variable])
                unnasigned_variable = variable
        return unnasigned_variable

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.
        `assignment` is a mapping from variables (keys) to words (values).
        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)

        for value in self.domains[var]:
            assignment[var] = value

            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result is not None:
                    return result

            assignment.pop(var)

        return None

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    boards_path = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    boards_files = os.listdir(boards_path)
    boards = []
    for board_file in boards_files:

      file_path = os.path.join(boards_path, board_file)
      crossword = Crossword(file_path, words)
      creator = CrosswordCreator(crossword)
      assignment = creator.solve()
      
      # Print result
      if assignment is None:
          print("No solution.")
      else:
          ouput = creator.transform_to_json(assignment)
          boards.append(ouput)
          if output:
              creator.save(assignment, output)
    
    creator.save_json(boards)
    
if __name__ == "__main__":
    main()
