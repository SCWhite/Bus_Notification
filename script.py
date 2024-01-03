# TDX api sample code from:
# https://github.com/tdxmotc/SampleCode

import argparse
import configparser
import concurrent.futures
import itertools
import json
import requests
import time
from collections import defaultdict
from datetime import datetime
from threading import Thread



# This API key will only last for three days
app_id = 'XXXXX-XXXXXXXX-XXXX-XXXX'
app_key = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'

# for fetching data from TDX
class Auth():

    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key
        

    def get_auth_header(self):
        content_type = 'application/x-www-form-urlencoded'
        grant_type = 'client_credentials'

        return{
            'content-type' : content_type,
            'grant_type' : grant_type,
            'client_id' : self.app_id,
            'client_secret' : self.app_key
        }

class data():

    def __init__(self, app_id , app_key , auth_response):
        self.app_id = app_id
        self.app_key = app_key
        self.auth_response = auth_response

    def get_data_header(self):
        auth_JSON = json.loads(self.auth_response.text)
        access_token = auth_JSON.get('access_token')

        return{
            'authorization': 'Bearer '+access_token
        }

# Get station_id (both way) in order,
# Format: [route_id] stops, updatetime, versionid
def get_station_seqence(route_no) -> list:

    route_no = route_no[:-2]
    
    auth_url="https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    # Station seqence is almost static, no need for mock api
    url = "https://tdx.transportdata.tw/api/basic/v2/Bus/DisplayStopOfRoute/City/Taipei/"+ str(route_no) +"?%24top=30&%24format=JSON"
    
    try:
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())
    except:
        a = Auth(app_id, app_key)
        auth_response = requests.post(auth_url, a.get_auth_header())
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())

    data_response = data_response.json()

    for i in data_response:
        
        name_of_route = i['RouteName']['En'] + "_" + str(i['Direction'])
        route[name_of_route] = {}
        station_list = []
        for j in i['Stops']:
            station_list.append(j['StopID'])
            
        list_as_string = ','.join(station_list)
        route[name_of_route]['Stops'] = list_as_string
        route[name_of_route]['UpdateTime'] = i['UpdateTime']
        route[name_of_route]['VersionID'] = str(i['VersionID'])

    with open('route_table.ini', 'w') as configfile:
        route.write(configfile)    

# Get current bus
def get_route_update(route_no) -> list:

    auth_url="https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    # Enable mock_api for testing / test api will only last for a week.
    if test_api:
        url = "http://host/api/basic/v2/Bus/RealTimeNearStop/City/Taipei/" + str(route_no)
    else:
        url = "https://tdx.transportdata.tw/api/basic/v2/Bus/RealTimeNearStop/City/Taipei/"+ str(route_no) +"?%24top=30&%24format=JSON"
    
    try:
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())
    except:
        a = Auth(app_id, app_key)
        auth_response = requests.post(auth_url, a.get_auth_header())
        d = data(app_id, app_key, auth_response)
        data_response = requests.get(url, headers=d.get_data_header())    

    data_response = data_response.json()
    busses = []

    for i in data_response:      
        Bus_ID = i['PlateNumb']
        route = i['RouteName']['En'] + "_" + str(i['Direction'])
        current_stop = i['StopID']

        busses.append([route,Bus_ID,current_stop])    
        
    return busses

# Check if current buses is in our condition
def rule_chacker(bus_list) -> list:

    route.read('route_table.ini')
    mission.read('mission.ini')

    notify_list = []
    for bus in bus_list:
        # TODO: consider same route, but have multiple target

        if bus[0] in mission:
            # Notification logic, only send message between 3~5 station away
            try:
                station_list = route[bus[0]]['stops'].split(',')
                notify_range = station_list.index(mission[bus[0]]['target']) - station_list.index(bus[2])
                if notify_range >=3 and notify_range <= 5 :
                    #print("send notification! Plate: ",bus[1])
                    notify_list.append(bus[0])
                else:
                    pass
            except:
                # TODO: Index error, write to log
                pass
    
    return notify_list


# Telegram bot is broken, so....
# this is the fastest fix I can think of. 
def send_notification(user_list) -> list:

    user.read('user.ini')
    mission.read('mission.ini')

    deliver_list = []

    for group in user_list:
        try:
            grup_id = mission[group]['user_group']
            target = mission[group]['target']
            send_list = user[grup_id]['user'].split(',')
            for u in send_list:
                print("Notification to: %s / bus_id: %s / station_id: %s "% (u, group, target))
                time.sleep(0.2)
                
            time_now = datetime.now()
            #current_time = time_now.strftime("%H:%M:%S")
            deliver_list.append([group,time_now])
        except:
                # TODO: Index error, write to log
                pass

    return deliver_list
    

    

if __name__ == '__main__':

    # Get argument from cmd
    parser = argparse.ArgumentParser(description="Demo script for bus notification system.")
    parser.add_argument('--test', type=int, default=0, help='Set to 1 to enable the test API')
    args = parser.parse_args()

    if args.test == 0:
        test_api = 0
    else:
        test_api = 1

    
    route  = configparser.ConfigParser()
    mission = configparser.ConfigParser()
    user = configparser.ConfigParser()   

    duplicate_dict = defaultdict(list)
    
    # Main cycle, repeat in 30sec
    while True:
        route.read('route_table.ini')
        mission.read('mission.ini')
        user.read('user.ini')

        

        mission_list = mission.sections()

        # Check if target route is already in station_list
        # TODO: check timestamp for latest schedule 
        for route_no in mission_list:
            # if doesn't exist, fetch from tdx API
            if route_no not in route.sections():
                get_station_seqence(route_no)
            else:
                # TODO: write to log
                pass
            
        # Reduce API request
        for i in range(len(mission_list)):
            mission_list[i] = mission_list[i][:-2]
        mission_list = set(mission_list)
                
        
        # Do polling on mission route
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            current_bus_list = executor.map(get_route_update, mission_list)

        # Convert to proper format
        current_bus_list = list(current_bus_list)
        

        # Apply to rule
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            notification_list = executor.map(rule_chacker, current_bus_list)
            

        # Convert to proper format
        notification_list = list(notification_list)
        #notification_list = list(itertools.chain.from_iterable(notification_list))

        # Remove duplicate notify after first one / time base rule
        for i in range(len(notification_list)):
            if notification_list[i] != [] and notification_list[i][0] in duplicate_dict:
                time_now = datetime.now()
                time_diff = time_now - duplicate_dict[notification_list[i][0]]
                if time_diff.total_seconds() < 300:
                    notification_list[i] = []
                else:
                    pass

        # Send Notification
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            sent_list = executor.map(send_notification, notification_list)

        # Mantain duplicate dict
        sent_list = list(itertools.chain.from_iterable(sent_list))
        for i in sent_list:
            duplicate_dict[i[0]] = i[1] 

        
        # Formatting for notification 
        time_now = datetime.now()
        current_time = time_now.strftime("%H:%M:%S")
        print("---- %s ----" % current_time)
        
        time.sleep(30)
    
    print("EOF")
    
