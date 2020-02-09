import time
import socket
from threading import Thread
import curses

def err_handler(function):
    def wrapper(*args,**kwargs):
        try:
            result = function(*args,**kwargs)
            return result
        except Exception as err:
            screen.addstr(0,0,function.__name__+' '+str(err.args))
    return wrapper

            
class Server_listener(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stop = False

    
    @err_handler
    def get_data(self):
        try:
            server_data = sock.recv(1024)
            if not server_data:
                add_str('system: disconnected by server1')
                return False
        except ConnectionResetError:
            add_str('system: disconnected by server2')
            return False
        return server_data.decode('utf-8')

    
    @err_handler
    def send_data(self, message):
        try:
            sock.send(message.encode('utf-8'))
            return True
        except ConnectionResetError:
            add_str('system: disconnected by server')
            return False


    @err_handler
    def run(self):
        global disconnected
        while not self.stop:
            server_data = self.get_data()
            if server_data:
                add_str(server_data)
            else:
                disconnected = True
                break


@err_handler
def print_screen() -> None:
    string_y = 1
    screen.border(0)
    if scrolled_strings:
        for string in strings[-max_strings - scrolled_strings : -scrolled_strings]:
            if string[0]:
                screen.addstr(string_y, 1, string[0], user_colors.get(string[0], colors['green']))
                screen.addstr(string_y, 1 + len(string[0]), string[1])
            else:
                screen.addstr(string_y, 1, string[1])
            string_y += 1
    else:
        for string in strings[-max_strings:]:
            if string[0]:
                screen.addstr(string_y, 1, string[0], user_colors.get(string[0],colors['green']))
                screen.addstr(string_y,1 + len(string[0]), string[1])
            else:
                screen.addstr(string_y,1, string[1])
            string_y += 1
        screen.refresh()


@err_handler
def add_str(*new_strings) -> None:
    splitted_strings = []
    for new_string in new_strings:
        chunks = [new_string[i:i + STR_FREE_SPACE] for i in range(0, len(new_string), STR_FREE_SPACE)]
        # If length of new_string is more of screen x length, divides it by chunks
        chunks[0] = [(chunks[0])[:chunks[0].index(':')], ((chunks[0])[chunks[0].index(':'):])]
        # Some magic happens in upper string!
        for i in range(1, len(chunks)):
            chunks[i] = ['', chunks[i]]
        chunks[-1] = [chunks[-1][0],chunks[-1][1] + ' ' * (STR_FREE_SPACE - (len(chunks[-1][1]) + len(chunks[-1][0])))]
        # The length of last chunk probably will be less than screen length thus fill the last length by spaces
        splitted_strings.extend(chunks)
    strings.extend(splitted_strings)
    print_screen()


@err_handler
def parse_command(command_string: str) -> str:
    words = command_string.split()
    if words[0] == '!create':
        return 'CREATE ' + words[1]
    elif words[0] == '!connect':
        return 'CONNECT ' + words[1]
    elif words[0] == '!rooms':
        return 'ROOMLIST'
    elif words[0] == '!users':
        return 'USERLIST'
    elif words[0] == '!disconnect':
        return 'DISCONNECT '
    elif words[0] == '!help':
        add_str('system: !create <room name> - create a room with a name',
                ': !connect <room name> - connect to a room',
                ': !disconnect - disconnect from the current room',
                ': !roomlist - see the list of public rooms',
                ': !users - see the list of users in current room')
    elif words[0] == '!test':
        add_str('system: text')
    else:
        add_str('system: cant recognize "'+words[0]+'" command',
                ':try !help to see the list of commands')

                             
@err_handler           
def get_msg(welcome_msg = '>>> ') -> str:
    global scrolled_strings
    letter_list = [] 
    cursor_x = len(welcome_msg) + 1
    # the position of cursor after of printing the welcome message '+1' is a compensation of border symbol
    enter = False
    msg_free_space = STR_FREE_SPACE - len(welcome_msg)
    # the avaliable space for typed message '-2' is a compensation of both left and right borders
    screen.addstr(22, 1, welcome_msg)
    screen.refresh()
    while not enter:
        letter = screen.getch(22, cursor_x)
        if letter == 10: # Enter
            if letter_list:
                screen.addstr(22, 1, ' ' * STR_FREE_SPACE) # clear the input area
                enter = True
        elif letter == 8: # Backspace
            if letter_list:
                letter_x = len(welcome_msg) + 1
                letter_list.pop()
                screen.addstr(22,letter_x,' ' * msg_free_space)
                for char in letter_list[-msg_free_space:]:
                    screen.addstr(22, letter_x, char)
                    letter_x += 1
                if len(letter_list) < msg_free_space - 1:
                    cursor_x -= 1
        elif letter == 259: # Arrow up
            if (max_strings + scrolled_strings + 1 <= len(strings)):
                scrolled_strings += 1
                print_screen()
        elif letter == 258: # Arrow down
            if scrolled_strings -1 >= 0:
                scrolled_strings -= 1
                print_screen()
        elif letter == 260: # Arrow left
            pass
        elif letter == 261: # Arrow right
            pass
        elif letter == 27: # Esc
            exit()
        else: # Another letter
            letter_list.append(chr(letter))
            letter_x = len(welcome_msg) + 1
            for char in letter_list[-msg_free_space:]:
                screen.addstr(22, letter_x, char)
                letter_x += 1
            if len(letter_list) < msg_free_space:
                cursor_x += 1
    return ''.join(letter_list)  
    
@err_handler
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
                        add_str('system: can contain only ASCII letters or numbers')
                        break
                else:
                    picked = True
            else:
                add_str('system: must be more than 3 and less than 16 letters')
        sock.send(('SETNAME ' + nickname).encode('utf-8'))
        respond = sock.recv(1024)
        if respond.decode('utf-8').split()[0] == 'ACCEPT':
            unique = True
            add_str('system: nickname accepted')
        else:
            add_str('system:"' + nickname + '" is occupied!')
            picked = unique = False
    return nickname

@err_handler
def connect_to_server(host: str, port: int) -> None:
    attempts = 1
    while attempts <= 3:
        try:
            add_str('system: trying to connect(' + str(attempts) + ')...')
            sock.connect((host, port))
            add_str('system: connected!','system: try !help to seethe list of commands')
            break
        except ConnectionError:
            attempts += 1
    else:
        add_str('system: can not connect to server!')
        desicion = get_msg('retry? (y,n): ')
        if desicion[0] == 'y':
            connect_to_server(HOST, PORT)
        elif desicion[0] == 'n':
            exit()

SCREEN_Y, SCREEN_X = 24, 80
screen = curses.initscr()
screen.resize(SCREEN_Y, SCREEN_X)
screen.keypad(True)
curses.start_color()
curses.noecho()
STR_FREE_SPACE = SCREEN_X - 2

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

max_strings = SCREEN_Y - 3
scrolled_strings = 0
strings = []
disconnected = False
something = True
HOST, PORT = '127.0.0.1', 9090

while something:
    server_listener = Server_listener()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connect_to_server(HOST,PORT)
    disconnected = False
    nickname = pick_username()
    server_listener.start()
    user_colors[nickname] = colors['blue']
    while not disconnected:
        message = get_msg()
        if len(message) > 255:
            add_str('system: 255 symbols message limit')
            continue
        if not (message.strip() in ('','\n','\t','\r')):
            if message[0] == '!':
                command = parse_command(message)
                if command:
                    sent = server_listener.send_data(command)
                    if not sent:
                        disconnected = True
            else:
                sent = server_listener.send_data('MESSAGE '+nickname + ": " + message)
                if not sent:
                    disconnected = True

