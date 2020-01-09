
import os
import time
import socket
from threading import Thread
import curses

SCREEN_Y, SCREEN_X = 24, 80
screen = curses.initscr()
screen.resize(SCREEN_Y, SCREEN_X)
screen.keypad(True)
curses.start_color()
curses.noecho()
SEPARATOR = ': '

curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)

colors = {
    'red':curses.color_pair(1),
    'blue':curses.color_pair(2),
    'yellow':curses.color_pair(3),
    'cyan':curses.color_pair(4),
    'magenta':curses.color_pair(5),
    'green':curses.color_pair(6)
    }

user_colors = {
    'system':colors['red'],
    }

class Msg_accepter(Thread):
    'Thread-child class that accept strings from server'
    
    def __init__(self):
        Thread.__init__(self)
        self.strings = []
        # string[n][0] - nickname
        # string[n][1] - message
        self.max_strings = SCREEN_Y - 3
        self.scrolled_strs = 0

    def run(self) -> None:
        try:
            while True:
                data1 = sock.recv(1024)
                self.add_str(data1.decode('utf-8'))
        except Exception as err:
            screen.addstr(0, 1, 'run ' + str(err))
            
    def print_screen(self) -> None:
        try:
            string_y = 1
            screen.border(0)
            if self.scrolled_strs:
                for string in self.strings[-self.max_strings - self.scrolled_strs : -self.scrolled_strs]:
                    if string[0]:
                        screen.addstr(string_y, 1, string[0], user_colors.get(string[0],colors['green']))
                        screen.addstr(string_,y,1 + len(string[0]),string[1])
                    else:
                        screen.addstr(string_y,1, string[1])
                    string_y += 1
##                    for msg in self.strings[-self.max_strings - self.scrolled_strs:-self.scrolled_strs]:
##                        nick,text = msg.split(':')
##                        screen.addstr(string_y,1, nick, user_colors.get(nick,colors['green']))
##                        screen.addstr(string_y, 1 + len(nick), ':' + text + ' '*(SCREEN_X - 3 - (len(text)+len(nick))))
##                        string_y += 1
            else:
                for string in self.strings[-self.max_strings:]:
                    if string[0]:
                        screen.addstr(string_y, 1, string[0], user_colors.get(string[0],colors['green']))
                        screen.addstr(string_y,1 + len(string[0]), string[1])
                    else:
                        screen.addstr(string_y,1, string[1])
                    string_y += 1
##                    for msg in self.strings[-self.max_strings:]:
##                        nick,text = msg.split(':')
##                        screen.addstr(string_y, 1, nick, user_colors.get(nick,colors['green']))
##                        screen.addstr(string_y, 1 + len(nick), ':' + text + ' '*(SCREEN_X - 3 - (len(text)+len(nick))))
##                        string_y += 1
                screen.refresh()
        except Exception as err:
            screen.addstr(0,1,'print_screen ' + str(err))
            
    def add_str(self,*new_strings) -> None:
        splitted_strings = []
        try:
            for new_string in new_strings:
                chunks = [new_string[i:i + (SCREEN_X - 2)] for i in range(0, len(new_string),(SCREEN_X - 2))]
                # If length of new_string is more of screen x length, divides it by chunks
                chunks[0] = [(chunks[0])[:chunks[0].index(':')], ((chunks[0])[chunks[0].index(':'):])]
                # Do not touch it till this shit string works!
                for i in range(1, len(chunks)):
                    chunks[i] = ['', chunks[i]]
                chunks[-1] = [chunks[-1][0],chunks[-1][1] + ' ' * (SCREEN_X - 2 - len(chunks[-1][1]))]
                # The length of last chunk probably will be less than screen length thus fill the last length by spaces
                splitted_strings.extend(chunks)
            self.strings.extend(splitted_strings)
            self.print_screen()
        except Exception as err:
            screen.addstr(0,1,'add_str ' + str(err))
        
##def add_str(*new_strings):
##	strings = []
##	for new_str in new_strings:
##		chunks = [new_str[i:i+10] for i in range(0, len(new_str),10)]
##		chunks[0] = [   (chunks[0])[:chunks[0].index(':')],    ((chunks[0])[chunks[0].index(':')+1:]).strip()   ]
##		if len(chunks) > 1:
##			for i in range(1,len(chunks)-1):
##				chunks[i] = ['',chunks[i].strip()]
##		strings.extend(chunks)
##	return strings 

class User_input_listener(Thread):
    'A thread-child class that gets messages from local user, parses commands if they are, and sends to server'
    
    def __init__(self):
        Thread.__init__(self)

    def run(self) -> None:
        try:
            while True:
                msg = get_msg()
                if len(msg) > 255:
                    msg_accepter.add_str('system:255 symbols message limit')
                    continue
                if not( msg in ('','\n','\t')):
                    if msg[0]=='!':
                        words = msg.split()
                        if words[0] == '!create':
                            sock.send(('CREATE '+words[1]).encode('utf-8'))
                        elif words[0] == '!connect':
                            sock.send(('CONNECT '+words[1]).encode('utf-8'))
                        elif words[0] == '!rooms':
                            sock.send('ROOMLIST'.encode('utf-8'))
                        elif words[0] == '!users':
                            sock.send('USERLIST'.encode('utf-8'))
                        elif words[0] == '!disconnect':
                            sock.send(('DISCONNECT ').encode('utf-8'))
                        elif words[0] == '!help':
                            msg_accepter.add_str('system:!create <room name> - create a room with a name',
                                                 ':!connect <room name> - connect to a room',
                                                 ':!disconnect - disconnect from the current room',
                                                 ':!roomlist - see the list of public rooms',
                                                 ':!users - see the list of users in current room')
                        elif words[0] == '!test':
                            msg_accepter.add_str('system:text')
                        else:
                            msg_accepter.add_str('system:cant recognize "'+words[0]+'" command',
                                                 ':try !help to see the list of commands')
                    else:
                        sock.send(('MESSAGE '+nickname + ": " + msg).encode('utf-8'))
        except Exception as err:
            screen.addstr(0,1, 'run2' + str(err))
            

def get_msg(welcome_msg = '>>> ') -> str:
    letter_list = [] 
    cursor_x = len(welcome_msg) + 1
    # the position of cursor after of printing the welcome message '+1' is a compensation of border symbol
    enter = False
    str_space = SCREEN_X - 2 - len(welcome_msg)
    # the avaliable space for typed message '-2' is a compensation of both left and right borders
    screen.addstr(22, 1, welcome_msg)
    screen.refresh()
    while not enter:
        letter = screen.getch(22, cursor_x)
        if letter == 10: # Enter
            if letter_list:
                screen.addstr(22, 1, ' '*(SCREEN_X - 2) ) # clear the input area
                enter = True
        elif letter == 8: # Backspace
            if letter_list:
                letter_x = len(welcome_msg)+1
                letter_list.pop()
                screen.addstr(22,letter_x,' ' * str_space)
                for char in letter_list[-str_space:]:
                    screen.addstr(22, letter_x, char)
                    letter_x += 1
                if len(letter_list) < str_space - 1:
                    cursor_x -= 1
                
        elif letter == 259: # Arrow up
            if (msg_accepter.max_strings + msg_accepter.scrolled_strs + 1
                <= len(msg_accepter.strings)):
                msg_accepter.scrolled_strs += 1
                msg_accepter.print_screen()
        elif letter == 258: # Arrow down
            if msg_accepter.scrolled_strs -1 >= 0:
                msg_accepter.scrolled_strs -= 1
                msg_accepter.print_screen()
        elif letter == 260: # Arrow left
            pass
        elif letter == 261: # Arrow right
            pass
        elif letter == 27: # Esc
            exit()
        else: # Another letter
            letter_list.append(chr(letter))
            letter_x = len(welcome_msg)+ 1
            for char in letter_list[-str_space:]:
                screen.addstr(22, letter_x, char)
                letter_x += 1
            if len(letter_list) < str_space:
                cursor_x += 1
    return ''.join(letter_list)


def pick_username() -> str:
    picked = False
    unique = False
    nickname = ''
    letter_pool = 'qwerttyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM123' + \
                  '4567890_'
    while not unique:
        while not picked:
            nickname = get_msg('Enter your name: ')        
            if len(nickname) > 3 and len(nickname) < 16:
                for letter in nickname:
                    if not (letter in letter_pool):
                        msg_accepter.add_str('system:can contain only ASCII' + \
                                             ' letters or numbers')
                        break
                else:
                    picked = True
            else:
                msg_accepter.add_str('system:must be more than 3 and less t' + \
                                     'han 16 letters')
        sock.send(('SETNAME ' + nickname).encode('utf-8'))
        respond = sock.recv(1024)
        if respond.decode('utf-8').split()[0] == 'ACCEPT':
            unique = True
            msg_accepter.add_str('system:nickname accepted')
        else:
            msg_accepter.add_str('system:"' + nickname + '" is occupied!')
            picked = unique = False
    return nickname


def connect_to_server(host: str, port: int) -> None:
    attempts = 1
    while attempts <= 3:
        try:
            msg_accepter.add_str('system:trying to connect(' + \
                                 str(attempts) + ')...')
            sock.connect((host, port))
            #msg_accepter.strings = []
            msg_accepter.add_str('system:connected!')
            break
        except ConnectionError:
            attempts += 1
    else:
        msg_accepter.add_str('system:can not connect to server!')
        desicion = get_msg('retry? (y,n): ')
        if desicion[0] == 'y':
            connect_to_server(HOST, PORT)
        elif desicion[0] == 'n':
            exit()


HOST, PORT = '127.0.0.1', 9090
#'ec2-13-48-115-122.eu-north-1.compute.amazonaws.com',25565
sock = socket.socket()
user_input_listener = User_input_listener()
msg_accepter = Msg_accepter()
connect_to_server(HOST,PORT)
nickname = pick_username()
user_colors[nickname] = colors['blue']
msg_accepter.start()
user_input_listener.start()
