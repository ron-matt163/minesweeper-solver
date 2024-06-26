""" Use the solver to solve a random problem, it uses the minesweeper implementation and GUI from
    https://github.com/JohnnyDeuss/minesweeper to generate minefields and display the results.

    Interesting seeds:
     1614353606 - Top-left unconstrained may have as many mines as squares.
    -1365615019 - Top-right corner where there are no unconstrained and many constrained, highlightss weight and
                  constraint issues.
     1791206719 - Three disconnected areas with non-merged neighboring components
     -436764911 - Top right corner that's cut off by mines.
     1396764919 - A non-boundary square is known to be a mine due to it being there being exactly one mine and one
                  square outside of the boundary.
"""
from time import sleep
from threading import Thread
import random

from PyQt5.QtCore import pyqtSlot, QObject
import numpy as np
from scipy.signal import convolve2d

from minesweeper.minesweeper.gui import MinesweeperGUI
from minesweeper_solver import Solver
from minesweeper_solver.policies import corner_then_edge2_policy


class Example(QObject):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        self.quitting = False

    @pyqtSlot()
    def quit(self):
        """ Receives exit messages from the GUI. """
        self.quitting = True

    def run(self):
        gui = self.gui
        game = gui.game
        # Uncomment to make the probabilities come out right.
        #game.set_config(first_never_mine=False)    # Disable to make first move probability is the same as the solver's?
        gui.aboutToQuit.connect(self.quit)
        wins = 0
        games = 0
        expected_wins = 0

        # This loop keeps running until we force quit
        while not self.quitting:
            seed = random.randint(-2 ** 31, 2 ** 31 - 1)
            print('Seed: {}'.format(seed))
            random.seed(seed)
            # The initial board configuration depends on a seed
            gui.reset()

            expected_win = 1
            games += 1
            solver = Solver(game.width, game.height, game.num_mines)
            state = game.state
            while not game.done and not self.quitting:
                prob = solver.solve(state)
                # Flag newly found mines.
                # The below loop right clicks (flags) every newly found certain mine that is still unflagged. 
                for y, x in zip(*((prob == 1) & (state != "flag")).nonzero()):
                    gui.right_click_action(x, y)
                best_prob = np.nanmin(prob)
                # Finds the location of the cell with the least probability of being a mine
                ys, xs = (prob == best_prob).nonzero()
                # Non zero-probability for the cell being a mine
                if best_prob != 0:
                    # Verifies whether all the probabilistic conditions are still satisfied
                    # If not, it throws an exception (we could probably get rid of this)
                    verify(game, prob)
                    # The expected win measures how much uncertainty we have operated under so far
                    expected_win *= (1-best_prob)
                    x, y = corner_then_edge2_policy(prob)
                    print('GUESS ({:.4%}) ({}, {})'.format(best_prob, x, y))
                    gui.left_click_action(x, y)
                # Enters this block if there is zero probability for the cell being a mine
                else:
                    # Open all the knowns.
                    for x, y in zip(xs, ys):
                        gui.left_click_action(x, y)
                sleep(1)
            expected_wins += expected_win
            if game.is_won():
                wins += 1
            print('{} | E[GameWin%] = {:.3}, Wins = {}, Games = {}, E[Wins] = {:.3}, Win% = {:.3%}'.format(
                'W' if game.is_won() else 'L', expected_win, wins, games, expected_wins, wins/games))
            sleep(5)


def verify(game, prob):
    """ Verify that the probabilistic solutions hasn't returned errors.

        There are a number of things we know for certain that must hold:
        - All known values must be between 0 and 1.
        - If we're in the probabilistic stage, the best probability can't be 1, nor can it be negative.
        - The summed probability of all squares is the number of mines left.
        - The summed probability of cells around that square is the number of mines left to it.
    """
    if not ((prob[~np.isnan(prob)] > 0).all() and (prob[~np.isnan(prob)] <= 1).all()):
        raise Exception('There is a probability outside of the [0, 1] range.')
    if not (0 < np.nanmin(prob) < 1):
        raise Exception('The best probability is outside of the range ]0, 1[.')
    if not np.isclose(np.nansum(prob), game.mines_left + (prob == 1).sum()):
        raise Exception("The total probability doesn't add up to the number of mines left.")
    ar = prob.copy()
    ar[np.isnan(ar)] = 0
    ar[np.array(game.state) == 'flag'] = 1
    summed_prob = convolve2d(ar, np.ones((3, 3)), mode='same')
    state = np.array([[game.state[y][x] if isinstance(game.state[y][x], int) else np.nan
                       for x in range(len(game.state[0]))] for y in range(len(game.state))])
    if not np.isnan(state).all() and not np.isclose(state[~np.isnan(state)], summed_prob[~np.isnan(state)]).all():
        raise Exception("The probability sum around a number doesn't add up to the number - known mines.")


if __name__ == '__main__':
#    random.seed(9)
    gui = MinesweeperGUI(debug_mode=True, difficulty='expert')
    example = Example(gui)
    example_thread = Thread(target=example.run)
    example_thread.start()
    gui.exec()
