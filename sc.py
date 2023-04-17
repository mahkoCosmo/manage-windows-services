import sys
import logging
import subprocess
import re
import keyboard
from enum import Enum
from typing import NamedTuple



services = []

class Menu:
    def __init__(self):
        self.selected = 1
 
    def show_menu(self):
        print("\n" * 30)
        print("Choose an option:")
        print("{0} 1.list services {1}".format(">" if self.selected == 1 else " ", "<" if self.selected == 1 else " "))
        print("{0} 2.find a service by name {1}".format(">" if self.selected == 2 else " ", "<" if self.selected == 2 else " "))
        print("{0} 3.search a service starts with {1}".format(">" if self.selected == 3 else " ", "<" if self.selected == 3 else " "))
        print("{0} 4.search a service ends with {1}".format(">" if self.selected == 4 else " ", "<" if self.selected == 4 else " "))
        print("{0} 5.search a service contains {1}".format(">" if self.selected == 5 else " ", "<" if self.selected == 5 else " "))
        print("{0} 6.stop a service {1}".format(">" if self.selected == 6 else " ", "<" if self.selected == 6 else " "))
        print("{0} 7.delete a service {1}".format(">" if self.selected == 7 else " ", "<" if self.selected == 7 else " "))        


    def up(self):
        if self.selected == 1:
            return
        self.selected -= 1
        self.show_menu()

    def down(self):
        if self.selected == 7:
            return
        self.selected += 1
        self.show_menu() 



menu_options = {
    1: 'list services',
    2: 'find a service by name',
    3: 'search a service starts with',
    4: 'search a service ends with',
    5: 'search a service contains',
    6: 'stop a service',
    7: 'delete a service',
    8: 'exit',
}

def print_menu():
    for key in menu_options.keys():
        print (key, '--', menu_options[key] )


class SearchPattern(Enum):
    START_WITH=0
    END_WITH=1
    CONTAINS=2

class Type(NamedTuple):
    id: str
    name: str

class State(NamedTuple):
    id: int
    name: str


class Service(NamedTuple):
    service_name: str
    display_name: str
    type: Type
    state: State
    pid: int
    flags: str

def run_win_cmd(cmd):
    result = []
    process = subprocess.Popen(cmd,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    for line in process.stdout:
        result.append(line)

    if len(result) == 0:
        logging.warning('An error occured!')
        for line in process.stderr:
            result.append(line)

    return result

    errcode = process.returncode
    for line in result:
        print(line)
    if errcode is not None:
        raise Exception('cmd %s failed, see above for details', cmd)

    
def print_result(res):
    print("\r\n\n")
    for line in res:
        print(line)   


def query_services_information():
    logging.info('Start querying services informations ..')
  
    cmds = ["sc", "queryex", "state=all", "type=service"]
    return run_win_cmd(cmds)

def parse_services_information(services_information):
    logging.info('Start parsing services information...')
     
    services = []
    for line in services_information:
        if line == b'\r\n': continue
        sub_strings = line.decode('ISO-8859-1').split(": ")
        
        sn: str
        dn: str
        type: Type
        state: State
        pid: int
        flags: str
        match sub_strings[0].strip():
            case "SERVICE_NAME": sn = sub_strings[1]
            case "DISPLAY_NAME": dn = sub_strings[1]
            case "TYPE": 
                types = sub_strings[1].split()
                type = Type(types[0], types[1])
            case "STATE": 
                states = sub_strings[1].split()
                state = State(int(states[0]), states[1])   
            case "PID": pid = int(sub_strings[1])
            case "FLAGS": 
                flags = sub_strings[1].strip()      
                services.append(Service(sn,dn,type, state, pid,flags))

    return services

def search_service_with_pattern(searchingStr, searchPattern):
    logging.info('Start searching with pattern...')
    pattern = ""
    match searchPattern:
        case SearchPattern.START_WITH:
            pattern = "^{0}".format(searchingStr)
        case SearchPattern.END_WITH:
            pattern = ".*{0}$".format(searchingStr)
        case SearchPattern.CONTAINS:
            pattern = ".*{0}".format(searchingStr)

    svs = []
    for service in services:
        res = re.match(pattern, service.display_name)
        if res:
            svs.append(service)

    return svs

def find_service(service_name):
    logging.info('Start finding a srvice...')
    for service in services:
        if service.service_name.count(service_name):
            return service

def stop_service(service_name):
    logging.info('Start stopping a service...')
    service = find_service(service_name)
    if service:
        cmds = ["net", "stop"]
        cmds.append("{0}".format(service_name))
        run_win_cmd(cmds)

def delete_service(service_name):
    logging.info('Start deleting a service...')
    service = find_service(service_name)
    if service:
        cmds = ["net", "stop"]
        cmds.append("{0}".format(service_name))
        run_win_cmd(cmds)   
        cmds.clear()
        cmds.append("sc") 
        cmds.append("delete")
        cmds.append("{0}".format(service_name))
        run_win_cmd(cmds)

if __name__ == '__main__':
    # print(f"Arguments count: {len(sys.argv)}")
    cmds = ["sc", "queryex", "state= all", "type= service"]
    # net stop “service-name-here”
#https://www.technewstoday.com/stop-service-command-line/
#my_item = MyStruct('foo', 0, ['baz'], User('peter'))

    services_information = query_services_information()

    # menu = Menu()
    # menu.show_menu()
    # keyboard.add_hotkey('up', menu.up)
    # keyboard.add_hotkey('down', menu.down)
    # keyboard.wait('space')

    services = parse_services_information(services_information)

  

    while(True):
        print_menu()
        option = ''
        try:
            option = int(input('Enter your choice: '))
        except:
            print('Wrong input. Please enter a number ...')

        match option:
            case 1:
                print_result(services)
            case 2:
                sn = input("Input the service name: ")
                print_result(find_service(sn))
            case 3:
                sstring = input("Input the searching string: ")
                print_result(search_service_with_pattern(sstring, SearchPattern.START_WITH))
            case 4:
                sstring = input("Input the searching string: ")
                print_result(search_service_with_pattern(sstring, SearchPattern.END_WITH))
            case 5:
                sstring = input("Input the searching string: ")
                print_result(search_service_with_pattern(sstring, SearchPattern.CONTAINS))
            case 6:
                sn = input("Input the service name: ")
                stop_service(sn)
            case 7:
                sn = input("Input the service name: ")
                delete_service(sn)  
            case 8:
                print('Thanks, see you')
                exit()
