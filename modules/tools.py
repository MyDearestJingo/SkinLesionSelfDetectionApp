import json
import socket
import logging

class Status:
    def __init__(self):
        self.STAT_WAIT = -5
        self.STAT_CHECKFAILED = -4
        self.STAT_KEYBORDINTERRUPT = -3
        self.STAT_TIMEOUT = -2
        self.STAT_FAILURE = -1
        self.STAT_NOERROR = 0
stat = Status()

class Logger():
    def __init__(self, filelog_name, log_level, name, fmt):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        fh = logging.FileHandler(fl_name)
        fh.setLevel(log_level)

        ch = logging.StreamHandler()
        ch.setLevel(log_level)

        formatter = logging.Formatter(fmt)
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        pass
    def getLogger(self):
        return self.logger

HEAD_LENGTH = 4 # the length of header

def get_checksum(bstream):
    cs = 0 # checksum
    for byte in bstream:
        cs ^= byte
    return cs


def send_data(send_socket, pack, max_seg_size=0, timeout=10, max_retry=5, check_method=get_checksum, feedback=True):
    stat_flag = stat.STAT_NOERROR
    pre_timeout = send_socket.gettimeout()
    send_socket.settimeout(timeout)
    pack_size = len(pack)
    if check_method is not None:
        cs = check_method(pack).to_bytes(1,"little")
        pack_size += len(cs)
    bstream = pack_size.to_bytes(HEAD_LENGTH,"little") + pack
    if check_method is not None:
        bstream += cs
    size_to_send = len(bstream)
    
    sent_size = 0
    is_successful = False
    max_seg_size = size_to_send if max_seg_size <= 0 else max_seg_size
    n_check = 0
    n_timeout = 0
    while (not is_successful) and stat_flag == stat.STAT_NOERROR:
        sent_size = 0
        while True:
            if stat_flag != stat.STAT_NOERROR:
                print("Send Failed")
                break
            if sent_size >= size_to_send:
                stat_flag = stat.STAT_NOERROR
                break
            next_size = max_seg_size if size_to_send-sent_size>max_seg_size else size_to_send-sent_size 
            try:
                sent_size += send_socket.send(bstream[sent_size:sent_size+next_size])
                n_timeout = 0
                print("Total Size: {}B | Sent: {}B".format(size_to_send, sent_size), end='\r')
            except socket.timeout:
                n_timeout += 1
                if n_timeout >= max_retry:
                    print("\nTimeout Error for {} times".format(n_retry))
                    stat_flag = stat.STAT_TIMEOUT
            except Exception as e:
                print("\nException Catched: ",e)
                stat_flag = stat.STAT_FAILURE
        print('\n',end="")
        if stat_flag == stat.STAT_NOERROR and feedback:
            recv_stat, recv_cs = recv_data(send_socket, feedback=False)
            if recv_stat == stat.STAT_NOERROR:
                if recv_cs == cs:
                    print("Check Complete")
                    is_successful = True
                else:
                    n_check += 1
                    print("Check Failed. Data Error Found. Retry")
                    if n_check >= max_retry:
                        stat_flag = stat.STAT_CHECKFAILED
                        print("Network Error. There is always error in data")
            else:
                stat_flag = recv_stat
        elif stat_flag == stat.STAT_NOERROR:
            is_successful = True

    send_socket.settimeout(pre_timeout)
    return (stat_flag, sent_size)

def recv_data(recv_socket, size_to_recv=None, max_seg_size=0, timeout=10, max_retry=5, check_method=get_checksum, feedback=True):
    stat_flag = stat.STAT_NOERROR
    per_timeout = recv_socket.gettimeout()
    recv_socket.settimeout(timeout)
    if size_to_recv is None:
        size_to_recv = int.from_bytes(recv_socket.recv(HEAD_LENGTH),byteorder="little")

    recv_buff = bytes()
    n_timeout = 0
    n_check = 0
    max_seg_size = size_to_recv if max_seg_size <= 0 else max_seg_size
    is_successful = False
    while (not is_successful) and stat_flag == stat.STAT_NOERROR:
        recved_size = 0
        recv_buff = bytes()
        while True:
            if stat_flag != stat.STAT_NOERROR:
                print("Recv Failed")
                break
            if recved_size >= size_to_recv:
                stat_flag = stat.STAT_NOERROR
                break
            next_size = max_seg_size if size_to_recv-recved_size>max_seg_size else size_to_recv-recved_size
            try:
                recv_buff += recv_socket.recv(next_size)
                recved_size = len(recv_buff)
                print("size: {}B | recv: {}B".format(size_to_recv, recved_size),end='\r')
            except socket.timeout:
                n_timeout += 1
                if n_timeout >= max_retry:
                    print("Timeout Error for {} times".format(n_retry))
                    stat_flag = stat.STAT_TIMEOUT
                    break 
            except Exception as e:
                print("Exception Catched: ",e)
                stat_flag = stat.STAT_FAILURE
                raise e
                break
        if stat_flag == stat.STAT_NOERROR:
            if check_method is not None:
                print('\nChecking...',end='\r')
                cs = get_checksum(recv_buff[:-1])
                recv_cs = recv_buff[-1]
                if feedback:
                    send_stat,_ = send_data(recv_socket,cs.to_bytes(1,"little"),feedback=False)
                if cs == recv_cs:
                    print("Checking Success. Transfer Complete")
                    is_successful = True
                    break
                else:
                    print("Data Error, need to retransfer")
                    n_check += 1
                    if n_check >= max_retry:
                        stat_flag = stat.STAT_CHECKFAILED
            else:
                is_successful = True

    recv_socket.settimeout(per_timeout)
    if check_method is not None:
        return (stat_flag, recv_buff[:-1])
    else:
        return (stat_flag, recv_buff)
                
    
