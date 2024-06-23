#!/usr/bin/env python3

import configparser
import os
import sys
import curses
from curses.textpad import Textbox, rectangle
from curses import wrapper

config = configparser.ConfigParser()
configpath = os.path.expanduser('~/.config/jcmd/example.ini')
recentpath = os.path.expanduser('~/.config/jcmd/recent')
toppath = os.path.expanduser('~/.config/jcmd/top')
logpath = f"/tmp/jcmd.{os.getlogin()}.log"

try:
    with open(configpath, "r") as configfile:
        config.read(configpath)
        #print(config["forge.example"]['User'])
except FileNotFoundError:
    print(f"config: {configpath} not found.. creating default")

    #default config
    #config['DEFAULT'] = {'ServerAliveInterval': '45',
    #                     'Compression': 'yes',
    #                     'CompressionLevel': '9'}
    #config['forge.example'] = {}
    #config['forge.example']['User'] = 'hg'
    #config['topsecret.server.example'] = {}
    #topsecret = config['topsecret.server.example']
    #topsecret['Port'] = '50022'     # mutates the parser
    #topsecret['ForwardX11'] = 'no'  # same here
    #config['DEFAULT']['ForwardX11'] = 'yes'
    config["test"] = "hello"

    os.makedirs(os.path.dirname(configpath), exist_ok=True)
    with open(configpath, 'w') as configfile:
      config.write(configfile)

logfile = open(logpath, "w")
def log(msg):
    logfile.write(str(msg)+"\n")
    logfile.flush()

# def set_pairs(fg, bg):
#     curses.init_pair(1, fg, colors['black'])
#     curses.init_pair(2, fg, colors['yellow'])
#     curses.init_pair(3, fg, colors['white'])
#     curses.init_pair(4, fg, colors['red'])
#     curses.init_pair(5, colors['black'], bg)
#     curses.init_pair(6, colors['yellow'], bg)
#     curses.init_pair(7, colors['white'], bg)
#     curses.init_pair(8, colors['red'], bg)

# load recents
try:
    with open(recentpath, 'r') as f:
        recents = []
        for line in f.readlines():
            recents.append(line.strip())
except FileNotFoundError:
    # initialize to random path
    recents = ["/home", "/etc/systemd", "/var/log", "/usr/bin"]

# load top path
try:
    with open(toppath, 'r') as f:
        tops = []
        for line in f.readlines():
            tokens = line.split()
            count = int(tokens[0])
            path = tokens[1]
            tops.append([count, path])
except FileNotFoundError:
    # initialize to random path
    tops=[[100, "/var/lib"], ["99", "/etc/X11"]]

log("tops...")
log(tops)
log(len(tops))

log("recents...")
log(recents)
log(len(recents))
editing = ""

# add the current directory to path if it's not in recent
#if os.getcwd() not in recents:
##    recents.append(

def set_recent(path):
    # move it to the top of recent files
    if path in recents:
        recents.remove(path)
    recents.insert(0, path)

    # also update top count
    found=False
    for top in tops:
        if top[1] == path:
            top[0]+=1
            found=True
            break
    if not found:
        tops.append([1, path])
       
def draw_screen(stdscr, tab, sid, recents, tops):
    stdscr.clear()

    recent_height = 15
    top_height = curses.LINES-4-recent_height

    ##########################################################################

    # draw recent list
    rectangle(stdscr, 0, 0, recent_height, curses.COLS-1)
    stdscr.addstr(0, 1, "recent")

    # scroll..
    if tab == "recent":
        if sid > recent_height-2:
            recents = recents[sid-recent_height+2:]
            sid = recent_height-2
            stdscr.addstr(1, curses.COLS-1, "^")

        # bottom scroll indicator
        if len(recents) > recent_height-1:
            stdscr.addstr(recent_height-1, curses.COLS-1, "v")

    y = 1
    for r in recents:
        color = curses.COLOR_WHITE
        path = r
        if tab == "recent" and y-1 == sid:
            color = curses.A_REVERSE
        stdscr.addstr(y, 1, path, color)
        y+=1

        if y > recent_height-1:
            break

    ##########################################################################

    # draw top list
    rectangle(stdscr, recent_height+1, 0, curses.LINES-2, curses.COLS-1)
    stdscr.addstr(recent_height+1, 1, "top")

    # scroll..
    if tab == "top":
        if sid > top_height-1:
            tops = tops[sid-top_height+1:]
            sid = top_height-1
            stdscr.addstr(recent_height+1, curses.COLS-1, "^")

        # bottom scroll indicator
        if len(tops) > top_height-1:
            stdscr.addstr(curses.LINES-2, curses.COLS-1, "v")

    y = 1
    for t in tops:
        color = curses.COLOR_WHITE
        path = t[1]
        if tab == "top" and y-1 == sid:
            color = curses.A_REVERSE
            #path = editing
        stdscr.addstr(y+recent_height+1, 1, path, color)

        # now I want to draw the count in blue
        color_pair = curses.color_pair(1)
        stdscr.addstr(y+recent_height+1, 1+len(t[1]), f" ({str(t[0])})", color_pair)
        y+=1

        if y > top_height:
            break
        
    stdscr.refresh()

def clear_rectangle(win, ul_y, ul_x, lr_y, lr_x):
    rectangle(win, ul_y, ul_x, lr_y, lr_x)
    for y in range(ul_y+1, lr_y):
        for x in range(ul_x+1, lr_x):
            win.addch(y, x, ' ')

    win.refresh()

def draw_edit_screen(stdscr, sid, path, subdirs):
    height = curses.LINES-10

    clear_rectangle(stdscr, 3, 10, curses.LINES-3, curses.COLS-10)
    stdscr.addstr(3, 12, path)

    # scroll..
    if sid > height+2:
        subdirs = subdirs[sid-height-2:]
        sid = height+2
        stdscr.addstr(4, curses.COLS-10, "^")

    # bottom scroll indicator
    if len(subdirs) > height+3:
        stdscr.addstr(curses.LINES-4, curses.COLS-10, "v")

    for i, subdir in enumerate(subdirs):
        color = curses.COLOR_WHITE
        if not os.access(path+"/"+subdir, os.R_OK):
            color = curses.color_pair(2)

        if  i == sid:
            color = curses.A_REVERSE

        stdscr.addstr(4+i, 11, subdir, color)
        if i > height+1:
            break
    if len(subdirs) == 0:
        stdscr.addstr(4, 11, "(no sub directories)", curses.COLOR_CYAN)

def edit_path(stdscr, path):

    subdirs = []

    def _load_subdirs():
        subdirs = []
        for entry in os.scandir(path):
            if entry.is_dir():
                subdirs.append(entry.name)
        subdirs.sort()
        return subdirs
    
    subdirs = _load_subdirs()

    sid = 0
 
    while True:
        draw_edit_screen(stdscr, sid, path, subdirs)
        ch = stdscr.getch()
        #log(ch)
        if ch == 27:
            break
        if ch == ord("\n"):
            # if subdirs[sid] == ".":
            #     return path
            # else:
            if len(subdirs) == 0:
                return path
            if path != "/":
                return path+"/"+subdirs[sid]
            else:
                return "/"+subdirs[sid]  # root directory
        
        if ch == ord("k"):
            sid-=1
            if sid == -1:
                sid = 0

        if ch == ord("j"):
            if sid < len(subdirs) -1 :
                sid+=1

        if ch == ord("h"):
            if path == "/":
                continue
            base = os.path.basename(path)
            path = os.path.dirname(path)
            subdirs = _load_subdirs()
            sid = subdirs.index(base)

        if ch == ord("l"):
            # if sid == 0: # "."
            #     continue
            if len(subdirs) == 0:
                continue
            if path != "/":
                path = path+"/"+subdirs[sid]
            else:
                path = "/"+subdirs[sid]  # root directory
            subdirs = _load_subdirs()
            sid = 0

    return None

def main(stdscr):

    curses.escape_delay = 100 # reduce escape delay to 25 msec
    curses.curs_set(0)
    curses.start_color()

    # Create a color pair (pair number, foreground color, background color)
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)

    # application states
    tab="recent"
    sid=0
    editing = None # recents[sid]

    #stdscr.addstr(0, 0, "Enter IM message: (hit Ctrl-G to send)")

    # Let the user edit until Ctrl-G is struck.
    #editwin = curses.newwin(5,30, 2,1)
    #rectangle(stdscr, 1,0, 1+5+1, 1+30+1)
    #stdscr.refresh()
    #box = Textbox(editwin)
    #box.edit()
    #message = box.gather() # Get resulting contents
    #print(message)

    #while True:
    #    c = stdscr.getch()
    #    log(f"key: {c}")
    #    if c == ord('p'):
    #        stdscr.addstr(0,0, c)
    #        stdscr.refresh()
    #    elif c == ord('q'):
    #        break  # Exit the while loop
    #    elif c == 27: # Esc or Alt
    #        break
    #    elif c == 

    while True:
        draw_screen(stdscr, tab, sid, recents, tops)
        ch = stdscr.getch()
        #log(ch)
        if ch == ord("q") or ch == 27:
            #set_recent(os.getcwd())
            sys.exit(1) 
            break
        if ch == ord("\t"):
            if tab == "recent":
                tab = "top"
                sid = 0
                # editing = recents[sid]
            elif tab == "top":
                tab = "recent"
                sid = 0
                # editing = tops[sid][1]

        if ch == ord("k"):
            sid-=1
            if sid == -1:
                sid = 0
            # if tab == "recent":
            #     editing = recents[sid]
            # if tab == "top":
            #     editing = tops[sid][1]

        if ch == ord("\n"):
            if tab == "recent":
                nextdir = recents[sid]
            if tab == "top":
                nextdir = tops[sid][1]
            set_recent(nextdir)
            break

        if ch == ord('d'):
            if tab == "recent":
                del recents[sid]
            if tab == "tops":
                del tops[sid]

        if ch == ord("j"):
            sid+=1
            if tab == "recent" and sid == len(recents):
                sid = len(recents)-1
            if tab == "top" and sid == len(tops):
                sid = len(tops)-1

            # if tab == "recent":
            #     editing = recents[sid]
            # if tab == "top":
            #     editing = tops[sid][1]

            #log(editing)

        if ch == ord("h"):
            editing = None
            if tab == "recent":
                editing = os.path.dirname(recents[sid])
            if tab == "top":
                editing = os.path.dirname(tops[sid][1])
            if editing:
                nextdir = edit_path(stdscr, editing)
                if nextdir:
                    set_recent(nextdir)
                    break

        if ch == ord("l"):
            editing = None
            if tab == "recent":
                editing = recents[sid]
            if tab == "top":
                editing = tops[sid][1]
            if editing:
                nextdir = edit_path(stdscr, editing)
                if nextdir:
                    set_recent(nextdir)
                    break

    print("done!")

os.environ.setdefault('ESCDELAY', '25')
wrapper(main)
logfile.close()

with open(recentpath, 'w') as f:
  f.write("\n".join(recents))

with open(toppath, 'w') as f:
  for t in tops:
      f.write(f"{t[0]} {t[1]}\n")



