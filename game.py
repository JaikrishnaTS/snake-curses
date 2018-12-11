#!/usr/bin/env python3

import curses
import random
import time

from collections import deque

CH_FULL_BLK = '█'
CH_FOOD = '●'
CH_SPACE = ' '

MOVES = {
    -1: None,
    ord('l'): (0, 1),
    curses.KEY_RIGHT: (0, 1),
    ord('h'): (0, -1),
    curses.KEY_LEFT: (0, -1),
    ord('j'): (1, 0),
    curses.KEY_DOWN: (1, 0),
    ord('k'): (-1, 0),
    curses.KEY_UP: (-1, 0)
}
CH_PAUSE = ord(' ')
CH_q = ord('q')  # quit

MINX, MINY = 80, 31

LEV_DELAY = [0.19, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05, 0.03]
LEV_SCORE = [10, 20, 30, 40, 50, 60, 70, 80]
FOOD_N = 5
INIT_SNAKE_LEN = 10

class Snake:
    def __init__(self, parent_window):
        self.score = 0
        self.parent_win = parent_window
        self.setup_curses()
        # pts as deque of (y, x)
        self.pts = deque((MINY // 2, i) for i in range(1, INIT_SNAKE_LEN + 1))
        self.dir = (0, 1)
        self.render()
        # True if food; False if part of snake
        self.food = {p: False for p in self.pts}
        self.add_food(FOOD_N)

    def setup_curses(self):
        curses.curs_set(0)
        sizey, sizex = self.parent_win.getmaxyx()
        if sizey < MINY or sizex < MINX:
            err_msg = 'Terminal size of {}x{} is required. ' \
                      'Have only {}x{}'.format(MINY, MINX, sizey, sizex)
            raise RuntimeError(err_msg)
        self.window = self.parent_win.subwin(MINY - 1, MINX,
                            (sizey - MINY) // 2, (sizex - MINX) // 2)
        self.canvas = MINY - 2, MINX - 1  # 1 char for border
        self.score_line = (sizey - MINY) // 2 + MINY - 1, \
                                (sizex - MINX) // 2 + 1
        self.parent_win.nodelay(True)
        self.parent_win.leaveok(True)
        self.parent_win.clear()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        self.parent_win.attron(curses.color_pair(1))
        self.window.nodelay(True)
        self.window.leaveok(True)
        self.window.clear()
        self.window.border()

    def render(self):
        for y, x in self.pts:
            self.window.addch(y, x, CH_FULL_BLK)
        self.update_score()
        self.window.refresh()

    def add_food(self, n):
        maxy, maxx = self.canvas[0] - 1, self.canvas[1] - 1
        for _ in range(n):
            pt = random.randint(2, maxy), random.randint(2, maxx)
            while pt in self.food:
                pt = random.randint(2, maxy), random.randint(2, maxx)
            self.food[pt] = True
            self.window.addch(pt[0], pt[1], CH_FOOD)

    def move(self, direction=None):
        if direction:
            if direction[0] + self.dir[0] != 0 or \
                    direction[1] + self.dir[1] != 0:
                self.dir = direction
        ## add new point
        last = self.pts[-1]
        new_pt = last[0] + self.dir[0], last[1] + self.dir[1]
        y, x = new_pt
        # check for out of bounds
        if (not 0 < y < self.canvas[0]) or (not 0 < x < self.canvas[1]):
            return self.end_game()
        # check if eating food
        eating_food = self.food.get(new_pt)
        if eating_food is True:
            self.add_food(1)
            self.food.pop(new_pt)
            self.update_score(1)
            ate = True
        elif eating_food is False:
            return self.end_game()
        # finalize
        self.food[new_pt] = False
        self.pts.append(new_pt)
        self.window.addch(new_pt[0], new_pt[1], CH_FULL_BLK)
        ## remove old point
        if not eating_food:
            old_pt = self.pts.popleft()
            self.window.addch(*old_pt, CH_SPACE)
            del self.food[old_pt]
        self.window.refresh()
        return True

    def update_score(self, add=0):
        self.score += add
        self.parent_win.addstr(*self.score_line,
                              'Score: {}'.format(self.score))

    def end_game(self):
        self.window.attron(curses.color_pair(2))
        self.parent_win.nodelay(False)
        self.window.addstr(MINY // 2, MINX // 2 - 4, 'GAME OVER')
        self.window.refresh()
        time.sleep(2)
        self.parent_win.getch()
        return False

    def pause(self):
        self.parent_win.nodelay(False)
        while self.parent_win.getch() != CH_PAUSE:
            pass
        self.parent_win.nodelay(True)

    def play(self):
        playing = True
        level = 0
        delay = LEV_DELAY[level]
        req_score = LEV_SCORE[level + 1]
        while playing:
            if self.score >= req_score:
                level += 1
                if level + 1 == len(LEV_SCORE):
                    self.end_game()
                req_score = LEV_SCORE[level + 1]
                delay = LEV_DELAY[level]
            kp = self.parent_win.getch()  # get key pressed
            if kp in MOVES:
                playing = self.move(MOVES[kp])
            elif kp == CH_PAUSE:
                self.pause()
            elif kp == CH_q:
                playing = self.end_game()
            else:  # unknown character
                continue
            time.sleep(delay)


def main(stdscr):
    snake = Snake(stdscr)
    snake.play()

if __name__ == '__main__':
    # do cbreak(), echo(False), enable-terminal-keypad, colors, on exception,
    # disable
    curses.wrapper(main)
