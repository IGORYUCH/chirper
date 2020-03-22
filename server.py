import socket
from time import ctime
from threading import Thread
from datetime import datetime
import rsa

class Connected_User(Thread):
    def __init__(self,data):
        Thread.__init__(self)
        self.conn = data[0]
        self.addr = data[1]
        self.disconnected = False
        self.xor_key = b''
        self.nickname = ''
        self.room = None
        
    def disconnect_from_server(self):
        if self.room:
            self.room.disconnect_user(self, '(connection refused)')
        if self.nickname:
            occupied_nicknames.remove(self.nickname)
        del connections[connections.index(self)]
        del self
        return True
        
    def send_msg(self, message):
        try:
            self.conn.send(xor_crypt(message.encode('utf-8'), self.xor_key))
            return False
        except ConnectionResetError:
            print(get_date(), 'connection reset by', self.addr)
            self.disconnect_from_server()
            return False

    def get_msg(self):
        try:
            data = self.conn.recv(1024)
            if not data:
                print(get_date(), 'connection reset by', self.addr)
                self.disconnect_from_server()
                return False
            return xor_crypt(data, self.xor_key).decode('utf-8')
        except ConnectionResetError:
            print(get_date(), 'connection reset by', self.addr)
            self.disconnect_from_server()
        return False

    def parse_msg(message):
        pass
            
    def run(self):
        print(get_date(), 'connection established with', self.addr)
        self.conn.send(public.save_pkcs1())
        encrypted_xor_key = self.conn.recv(1024)
        self.xor_key = rsa.decrypt(encrypted_xor_key, private)
        print(get_date(), 'secure connection established with', self.addr)
        while True:
            client_data = self.get_msg()
            if not client_data:
                break
            data_words = client_data.split(' ')
            if data_words[0] == 'SETNAME':
                if not (data_words[1] in occupied_nicknames):
                    self.send_msg('ACCEPT ' + data_words[1])
                    self.nickname = data_words[1]
                    occupied_nicknames.append(self.nickname)
                else:
                    self.send_msg('REJECT '+data_words[1])
            elif data_words[0] == 'MESSAGE':
                if self.room:
                    self.room.send_msg(' '.join(data_words[1:]))
                else:
                    self.send_msg('system: you are not in the room!')
            elif data_words[0] == 'CONNECT':
                for room in rooms:
                    if room.room_name == data_words[1]:
                        room.connect_user(self, data_words[2])
                        break
                else:
                   self.send_msg('system: the room "' + data_words[1] + '" are not avaliable')
            elif data_words[0] == 'CREATE':
                if not( data_words[1] in occupied_room_names):
                    new_room = Room(data_words[1])
                    new_room.connect_user(self)
                    new_room.admins.append(self.nickname)
                    rooms.append(new_room)
                    occupied_room_names.append(new_room.room_name)
                else:
                    self.send_msg('system: this room name is occupied')
            elif data_words[0] == 'USERLIST':
                if self.room:
                    self.send_msg( ('system: ' + ', '.join([user.nickname for user in self.room.connected_users])) )
                else:
                    self.send_msg('system: you are not in the room!')
            elif data_words[0] == 'ROOMLIST':
                if occupied_room_names:
                    self.send_msg('system: the list fo avaliable rooms: ' + ', '.join(occupied_room_names))
                else:
                    self.send_msg('system: no rooms have been created yet')
            elif data_words[0] == 'DISCONNECT':
                if self.room:
                    self.room.disconnect_user(self)
                else:
                    self.send_msg('system: you are not in the room!')
            elif data_words[0] == 'BAN':
                if self.room:
                    self.room.ban_user(self, data_words[1])
                else:
                    self.send_msg('system: you are not in the room!')
            elif data_words[0] == 'KICK':
                if self.room:
                    self.room.kick_user(self, data_words[1])
                else:
                    self.send_msg('system: you are not in the room!')
            elif data_words[0] == 'PASSWORD':
                if self.room:
                    self.room.change_pass(self,data_words[1])
                else:
                    self.send_msg('system: you are not in the room!')
                    
            else:
                client_data = 'Can not recognize: ' + client_data
                break
            print(get_date(), client_data)
        self.conn.close()

class Room:
    def __init__(self, room_name):
        self.connected_users = []
        self.room_name = room_name
        self.admins = []
        self.password = ''
        self.banned_users = []
        
    def send_msg(self ,msg):
        for connection in self.connected_users:
            connection.send_msg(msg)

    def connect_user(self, user_conn, password=''):
        if user_conn.nickname not in self.banned_users:
            if self.password == '':
                self.connected_users.append(user_conn)
                user_conn.room = self
                self.send_msg(('system: connected ' + user_conn.nickname))
            else:
                if self.password == password:
                    user_conn.send_msg('system: password accepted')
                    self.connected_users.append(user_conn)
                    user_conn.room = self
                    self.send_msg(('system: connected ' + user_conn.nickname))
                else:
                    if password == '':
                        user_conn.send_msg('system: this is a password protected room. Please enter a password')
                    else:
                        user_conn.send_msg('system: wrong password. Check your input and try again')
                
        else:
            user_conn.send_msg('system: you are banned from this room')
        
    def delete_user_data(self, user_conn):
        del self.connected_users[self.connected_users.index(user_conn)]
        user_conn.room = None
        
    def disconnect_user(self, user_conn,reason='(left the room)'):
        if reason == '(left the room)':
            self.send_msg('system: disconnected ' + user_conn.nickname)
            self.delete_user_data(user_conn)
        else:
            self.delete_user_data(user_conn)
            self.send_msg('system: disconnected ' + user_conn.nickname)
            
    def delete_room(self, deleting_user_conn):
        if deleting_user_conn.nickname in self.admins:
            for user in self.connected_users:
                self.disconnect_user(user)
            occupied_room_names.remove(self.room_name)
            rooms.remove(self)
            del self
        else:
            deleting_user_conn.send_msg('system: you do not have admin rights')
        
    def add_admin(self):
        pass

    def ban_user(self, banning_user_conn, banned_username):
        if banning_user_conn.nickname in self.admins:
            if banned_username in self.banned_users:
                banning_user_conn.send_msg('system: ' + banned_username + ' already banned')
            else:
                self.banned_users.append(banned_username)
                for user in self.connected_users:
                    if user.nickname == banned_username:
                        self.disconnect_user(user)
                        break
                self.send_msg('system: ' + banned_username + ' banned by ' + banning_user_conn.nickname)  
        else:
            banning_user_conn.send_msg('system: you do not have admin rights')
            
    def unban_user(self, unbanning_user_conn, unbanned_username):
        if unbanning_user_conn.nickname in self.admins:
            if unbanned_username in self.banned_users:
                self.banned_users.remove(unbanned_username)
                self.send_msg('system: ' + unbanned_username + ' unbanned by ' + unbanning_user_conn.nickname)
            else:
                unbanning_user_conn.send_msg('system: ' + unbammed_username + ' is not banned')   
        else:
            banning_user_conn.send_msg('system: you do not have admin rights')
            
    def kick_user(self, kicking_user_conn, kicked_username):
        if kicking_user_conn.nickname in self.admins:
            for user in self.connected_users:
                if user.nickname == kicked_username:
                    self.disconnect_user(user)
                    self.send_msg('system: ' + kicked_username + ' kicked by ' + kicking_user_conn.nickname) 
                    break
            else:
                kicking_user_conn.send_msg('system: there is no ' + kicked_username + ' in room')
        else:
            kicking_user_conn.send_msg('system: you do not have admin rights')

    def change_pass(self,changing_user,password):
        if changing_user.nickname in self.admins:
            if password == 'reset':
                self.password = ''
                self.send_msg('system: password has been reset')
            else:
                self.password = password
                self.send_msg('system: password has been changed')
        else:
            changing_user.send_msg('system: you do not have admin rights')


def xor_crypt(string:bytes, key:bytes) -> bytes:
    assert isinstance(string, bytes)
    assert isinstance(key, bytes)
    key_len = len(key)
    fitted_key = bytes(key[index % key_len] for index in range(len(string)))
    crypto_str = bytes([string[index] ^ fitted_key[index] for index in range(len(string))])
    return crypto_str


def get_date() -> str:
    date = datetime.now()
    date_str = '[{0:0>2}-{1:0>2}-{2:0>4} {3:0>2}:{4:0>2}]'.format(date.day, date.month, date.year, date.hour, date.minute)
    return date_str
    
    
commands_length = {
    'SETNAME':2,
    'MESSAGE':2,
    'CONNECT':2,
    'CREATE':2,
    'USERLIST':1,
    'ROOMLIST':1,
    'DISCONNECT':1,
    'BAN':2,
    'KICK':2
    }

print(get_date(), 'server started')
HOST,PORT = '127.0.0.1', 9090
sock = socket.socket()
sock.bind((HOST,PORT))
print(get_date(), 'running on', HOST + ':' + str(PORT))
connections = []
rooms = []
occupied_nicknames = ['system', 'System', 'admin', 'Admin', 'Administrator', 'FOXYMILIAN', 'HuHguZ', 'Alisa', 'alisa']
occupied_room_names = []
public, private = rsa.newkeys(1024)
print(get_date(), 'RSA keypair generated')
print(get_date(), 'ready for connections')
while True:
    sock.listen(1)
    connection = Connected_User(sock.accept())
    connection.start()
    connections.append(connection)
