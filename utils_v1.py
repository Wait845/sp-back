import numpy as np
from numpy import sqrt, dot, cross
from numpy.linalg import norm
import datetime
from dao import DataAccess
import threading
import random
import json
import info_compute
import time
import requests


room_position = []
room_hight = 0
ap_position = {}
room_area = 0
sensor_filter_list = set()


def poly_area(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))


def update_room_position(position: list):
    global room_position, room_hight, room_area
    room_position = position[:-1]
    room_hight = position[-1]
    print("current room position:", room_position, room_hight)
    # calculate room area
    room_area = poly_area([i[0] for i in room_position], [i[1] for i in room_position])


def update_ap_position(position: dict):
    global ap_position
    ap_position = position



def detected_device(addr: str, distance_info: dict, circles_list: list, device_position: list):
    """record device which is detected
    """
    dao = DataAccess()
    sql_record_device = "\
        INSERT INTO detect_device \
            SET addr = '{}';".format(
                    addr
                )
    print("RECORD A DETECTED DEVICE:", dao.execute(sql_record_device))


def _trilaterate(circle1, circle2, circle3):
    print("trilaterate:", circle1, circle2, circle3)
    P1, r1 = circle1[:3], float(circle1[3:][0])
    P2, r2 = circle2[:3], float(circle2[3:][0])
    P3, r3 = circle3[:3], float(circle3[3:][0])

    temp1 = P2-P1
    e_x = temp1/norm(temp1)
    temp2 = P3-P1
    i = dot(e_x,temp2)
    temp3 = temp2 - i*e_x
    e_y = temp3/norm(temp3)
    e_z = cross(e_x,e_y)
    d = norm(P2-P1)
    j = dot(e_y,temp2)
    x = (r1*r1 - r2*r2 + d*d) / (2*d)
    y = (r1*r1 - r3*r3 -2*i*x + i*i + j*j) / (2*j)
    temp4 = r1*r1 - x*x - y*y
    if temp4<0:
        # raise Exception("The three spheres do not intersect!");
        return None
    z = sqrt(temp4)
    p_12_a = P1 + x*e_x + y*e_y + z*e_z
    p_12_b = P1 + x*e_x + y*e_y - z*e_z
    return p_12_a,p_12_b


def _is_in_poly(p, poly):
    """
    :param p: [x, y]
    :param poly: [[], [], [], [], ...]
    :return:
    """
    px, py = p
    is_in = False
    for i, corner in enumerate(poly):
        next_i = i + 1 if i + 1 < len(poly) else 0
        x1, y1 = corner
        x2, y2 = poly[next_i]
        if (x1 == px and y1 == py) or (x2 == px and y2 == py):  # if point is on vertex
            is_in = True
            break
        if min(y1, y2) < py <= max(y1, y2):  # find horizontal edges of polygon
            x = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if x == px:  # if point is on edge
                is_in = True
                break
            elif x > px:  # if point is on left-side of line
                is_in = not is_in
    return is_in


def is_device_inside(distance_info: dict, addr):
    if len(distance_info) != 3:
        return False
    circles_list = []
    for i in distance_info.keys():
        ap = ap_position.get(i, None)
        if ap == None:
            return False
        # make circle and append into the list
        circle = np.append(ap, distance_info[i])
        circles_list.append(circle)

    device_position = _trilaterate(*circles_list)
    print(f"DEVICE_POSITION {addr}:{device_position}")
    if device_position:
        # print("device position in True")
        for device_p_a in device_position:
            # one of position is in the room is enough
            if _is_in_poly(device_p_a[:2], room_position) and abs(device_p_a[2]) <= room_hight:
                print("DEVICE IS IN THE ROOM!")
                print(f"DISTANCE_INFO:{distance_info}")
                print(f"CIRCLES_LIST:{circles_list}")
                print(f"DEVICE_POSITION:{device_position}")
                circles_list = [list(i) for i in circles_list]
                device_position = [list(i) for i in device_position]
                return {"distance_info": distance_info, "circles_list": circles_list, "device_position": list(device_position)}
        # device position: (array([3.9864    , 3.65851667, 9.25431093]), array([ 3.9864    ,  3.65851667, -9.25431093]))
    return False    


def calculate_stream(start_time: str, duration_time: int):
    threading.Thread(target=_calculate_stream, args=(start_time, duration_time)).start()


def _calculate_stream(start_time: str, duration_time: int):
    if room_position == [] or ap_position == {}:
        print("position is none")
        return "position is none"

    # calculate offset
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    start_time -= datetime.timedelta(seconds=duration_time)
    end_time = start_time + datetime.timedelta(seconds=duration_time*2)

    start_time = datetime.datetime.strftime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.strftime(end_time, "%Y-%m-%d %H:%M:%S")

    # select past 60 seconds data
    sql_get_stream = "\
        SELECT * \
        FROM detect_stream \
        WHERE probe_type = 'Probe Req' \
        AND timestamp BETWEEN '{}' AND '{}' \
        ORDER BY id DESC".format(
            start_time, end_time
    )
    dao = DataAccess()
    result_stream = dao.execute(sql_get_stream)
    # print("CALCULATE STREAM LENGTH:", len(result_stream))
    merge_dict = {}
    if result_stream != None:
        for stream in result_stream:
            s_iface, s_addr, s_distance = stream[1], stream[2], stream[10]
            # initial table - iface
            if merge_dict.get(s_addr, None) == None:
                merge_dict[s_addr] = {}
            # initial table - distance
            iface_distance = merge_dict[s_addr].get(s_iface, [])
            iface_distance.append(s_distance)

            merge_dict[s_addr][s_iface] = iface_distance
            # if iface_distance == 0:
            #     merge_dict[s_addr][s_iface] = s_distance
            # else:
            #     merge_dict[s_addr][s_iface] = round((iface_distance + s_distance) / 2, 2)
        
        # select 6 smallest distance message and get average value 
        for addr, iface_val in merge_dict.items():
            for iface, iface_dis_list in iface_val.items():
                # {"wlan0": [], "wlan1": []}
                # iface_dis_list = sorted(iface_dis_list)[:6]
                iface_dis_list = iface_dis_list[:5]
                iface_dis = round(sum(iface_dis_list) / len(iface_dis_list), 2)
                iface_val[iface] = iface_dis

    print(f"MERGE_DICT:{merge_dict}")


    for addr, aps in merge_dict.items():
        device_inside_result = is_device_inside(aps, addr)
        if device_inside_result != False:
            detected_device(addr, *device_inside_result.values())


def get_ignore_address():
    dao = DataAccess()
    sql_get_ignore_address = "\
        SELECT val \
        FROM config \
        WHERE `key` = 'ignore_address'";
    result_ignore_address = dao.execute(sql_get_ignore_address)
    if result_ignore_address == None or len(result_ignore_address) == 0 or result_ignore_address[0][0] == None:        
        return ""
    return result_ignore_address[0][0]


def get_notify_device():
    dao = DataAccess()
    sql_get_notify_device = "\
        SELECT val \
        FROM config \
        WHERE `key` = 'notify_device'";
    result_notify_device = dao.execute(sql_get_notify_device)
    if result_notify_device == None \
        or len(result_notify_device) == 0 \
        or result_notify_device[0][0] == None:
        return ""

    return result_notify_device[0][0]    


def get_overflow_num():
    dao = DataAccess()
    sql_get_overflow_num = "\
        SELECT val \
        FROM config \
        WHERE `key` = 'overflow_num'";
    result_overflow_num = dao.execute(sql_get_overflow_num)
    if result_overflow_num == None \
        or len(result_overflow_num) == 0 \
        or result_overflow_num[0][0] == None:
        # print("get overflow num error")
        return -1

    return int(result_overflow_num[0][0])


def notify_device(msg: str):
    notify_list = get_notify_device()
    if notify_list == "" or notify_list == "null":
        notify_list = []
    else:
        notify_list = json.loads(notify_list)
    
    url = "https://api2.pushdeer.com/message/push?pushkey={}&text={}"
    # print(f"NOTIFY_LIST:{notify_list}")
    for device in notify_list:
        requests.get(url.format(device, msg))
        

def _listen_overflow_num():
    while True:
        time.sleep(10)
        overflow_num = get_overflow_num()
        device_num = info_compute.occupancy(60, datetime.datetime.fromtimestamp(int(time.time())-1200), datetime.datetime.fromtimestamp(int(time.time())))["current"]
        print("CURRENT DEVICE NUMBER:", device_num)
        if overflow_num != -1 and device_num > overflow_num:
            notify_device(msg="Devices of Number Overflow:".format(device_num))

def listen_overflow_num():
    threading.Thread(target=_listen_overflow_num).start()