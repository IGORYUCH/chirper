import socket
from time import ctime
from threading import Thread

class Connected_User(Thread):
    def __init__(self,data):
        Thread.__init__(self)
        self.conn = data[0]
        self.addr = data[1]
        self.disconnected = False
        self.nickname = ''
        self.room = None
        
    def run(self):
        print('Connection Established with',self.addr,' A ',self.conn)
        try:
            while not self.disconnected:
                data = self.conn.recv(1024)
                data_words = data.decode('utf-8').split(' ')
                if data_words[0] == 'SETNAME':
                    if not (data_words[1] in occupied_nicknames):
                        self.conn.send(('ACCEPT '+data_words[1]).encode('utf-8'))
                        self.nickname = data_words[1]
                        occupied_nicknames.append(self.nickname)
                    else:
                        self.conn.send(('REJECT '+data_words[1]).encode('utf-8'))
                elif data_words[0] == 'MESSAGE':
                    if self.room:
                        self.room.send_msg(' '.join(data_words[1:]).encode('utf-8'))
                    else:
                        self.conn.send('system: you are not in the room'.encode('utf-8'))
                elif data_words[0] == 'CONNECT':
                    for room in rooms:
                        if room.room_name == data_words[1]:
                            room.connect_user(self)
                            break
                        else:
                            self.conn.send(('system: the room "'+data_words[1]+'" are not avaliable').encode('utf-8'))
                elif data_words[0] == 'CREATE':
                    if not( data_words[1] in occupied_room_names):
                        new_room = Room(data_words[1])
                        new_room.connect_user(self)
                        rooms.append(new_room)
                        occupied_room_names.append(new_room.room_name)
                    else:
                        self.conn.send(('system: this room name is occupied').encode('utf-8'))
                elif data_words[0] == 'USERLIST':
                    if self.room:
                        self.conn.send( ('system: ' + ','.join([user.nickname for user in self.room.connected_users])).encode('utf-8')  )
                    else:
                        self.conn.send('system: you are not in the room'.encode('utf-8'))
                elif data_words[0] == 'ROOMLIST':
                    if occupied_room_names:
                        self.conn.send(('system: the list fo abaliable rooms ' + ','.join(occupied_room_names)).encode('utf-8'))
                    else:
                        self.conn.send('system: no rooms have been created yet'.encode('utf-8'))
                elif data_words[0] == 'DISCONNECT':
                    if self.room:
                        self.room.disconnect_user(self)
                    else:
                        self.conn.send('system: you are not in the room!'.encode('utf-8')) 
                else:
                    data = 'Cant recongnize: '.encode('utf-8') + data

                print(data.decode('utf-8'))
            self.conn.close()
        except ConnectionError:
            print('Disconnected '+self.nickname)
            if self.room:
                self.room.disconnect_user(self)
            occupied_nicknames.remove(self.nickname)
            del connections[connections.index(self)]

class Room:
    def __init__(self,room_name):
        self.connected_users = []
        self.room_name = room_name
        self.admins = []
        
    def send_msg(self,msg):
        for connection in self.connected_users:
            connection.conn.send(msg)

    def connect_user(self,user_conn):
        self.connected_users.append(user_conn)
        user_conn.room = self
        self.send_msg(('system: connected ' + user_conn.nickname).encode('utf-8'))

    def disconnect_user(self,user_conn):
        self.send_msg(('system: disconnected '+user_conn.nickname).encode('utf-8'))
        del self.connected_users[self.connected_users.index(user_conn)]
        user_conn.room = None

    def delete_room(self):
        for user in self.connected_users:
            self.disconnect_user(user)
        occupied_room_names.remove(self.room_name)
        rooms.remove(self)
        del self
        
HOST,PORT = '127.0.0.1', 9090
sock = socket.socket()
sock.bind((HOST,PORT))
connections = []
rooms = []
occupied_nicknames = ['system', 'System', 'admin', 'Admin', 'Administrator', 'FOXYMILIAN', 'HuHguZ', 'FOXYMILLIAN']
occupied_room_names = []
print('Running on', HOST + ':' + str(PORT), 'started', ctime(), '\nWaiting for connections...')
while True:
    sock.listen(1)
    connection = Connected_User(sock.accept())
    connection.start()
    connections.append(connection)
