from dao import DataAccess
import datetime
import utils


def occupancy(gap_sec: int, start_time: datetime, end_time: datetime):
    """Calculate occupancy by particular gap time and duration time
    """
    dao = DataAccess()
    
    # sql_get_occupancy_device = "\
    #     SELECT DISTINCT addr, manuf \
    #     FROM detect_stream \
    #     WHERE timestamp > DATE_SUB(NOW(), INTERVAL 60 SECOND) \
    #     AND addr in ( \
    #         SELECT DISTINCT addr \
    #         FROM detect_device \
    #         WHERE timestamp > DATE_SUB(NOW(), INTERVAL 120 SECOND ) \
    #         )"
    # print("============== OCCUPANCY DEVICE INFO")
    # for i in dao.execute(sql_get_occupancy_device):
    #     print(i)

    sql_get_occupancy = "\
        SELECT * \
        FROM detect_device \
        WHERE timestamp BETWEEN '{}' AND '{}' \
        ORDER BY timestamp".format(
            start_time, end_time
    )
    # print(sql_get_occupancy)
    result_occupancy = dao.execute(sql_get_occupancy)
    if result_occupancy == None:
        return False

    result = {
        "current": 0, 
        "sequence": []
    }

    while start_time < end_time:
        temp_end_time = start_time + datetime.timedelta(seconds=gap_sec)
        mac_in_gap = []
        for i in result_occupancy:
            if i[2] < temp_end_time:
                mac_in_gap.append(i[1])
            else:
                break
        result_occupancy = result_occupancy[len(mac_in_gap):]
        # delete same addr
        mac_in_gap = set(mac_in_gap)
        result["sequence"].append(len(mac_in_gap))
        start_time = temp_end_time

    result["current"] = result["sequence"][-1]
    # sql_get_occupancy = "\
    #     SELECT a.time, COUNT(a.addr) \
    #     FROM ( \
    #         SELECT DISTINCT addr, \
    #             DATE_FORMAT( \
    #                 CONCAT(DATE(timestamp), ' ', HOUR(timestamp), ':', MINUTE(timestamp), ':', \
    #                     FLOOR(SECOND(timestamp) / 10) * 10), \
    #                     '%Y-%m-%d %H:%i:%s' \
    #             ) AS time \
    #         FROM detect_device \
    #         WHERE timestamp BETWEEN '{}' AND '{}' \
    #     ) a \
    #     GROUP BY a.time; \
    #     ORDER BY a.time".format(
    #         start_time, end_time
    #     )
    # result_occupancy = dao.execute(sql_get_occupancy)
    # if result_occupancy == None:
    #     return False
    
    # result = {
    #     "sequence": [r[1] for r in result]
    # }
    # result["current"] = result["sequence"][-1]

    return result


def enter_exits(gap_sec: int, start_time: datetime, end_time: datetime):
    """Calculate enter and exits devices number
    """
    dao = DataAccess()
    
    sql_get_occupancy = "\
        SELECT * \
        FROM detect_device \
        WHERE timestamp BETWEEN '{}' AND '{}' \
        ORDER BY timestamp".format(
            start_time, end_time
    )

    result_occupancy = dao.execute(sql_get_occupancy)
    if result_occupancy == None:
        return False
    
    result = {
        "enter": [],
        "exits": []
    }
    device_dict = {}
    while start_time < end_time:
        enter, exits = 0, 0

        temp_end_time = start_time + datetime.timedelta(seconds=gap_sec)
        mac_in_gap = []
        for i in result_occupancy:
            if i[2] < temp_end_time:
                mac_in_gap.append(i[1])
            else:
                break
        result_occupancy = result_occupancy[len(mac_in_gap):]
        # delete same addr
        mac_in_gap = set(mac_in_gap)

        # disappear time record
        for device in device_dict:
            device_dict[device] += 1
        # set disappear time 0
        for mac in mac_in_gap:
            # new mac enter
            if device_dict.get(mac, None) == None:
                enter += 1
            device_dict[mac] = 0
        for device in list(device_dict.keys()):
            # disappear time equal 5 regard as exits
            if device_dict[device] == 1:
                exits += 1
                device_dict.pop(device)
        
        result["enter"].append(enter)
        result["exits"].append(exits)

        start_time = temp_end_time
    # print(device_dict)
    # combine data by half hours
    temp_enter = []
    temp_exits = []
    while len(result["enter"]) != 0:
        temp_enter.append(sum(result["enter"][:30]))
        temp_exits.append(sum(result["exits"][:30]))
        result["enter"] = result["enter"][30:]
        result["exits"] = result["exits"][30:]
    result["enter"] = temp_enter
    result["exits"] = temp_exits

    return result


def flow_rate(gap_sec: int, start_time: datetime, end_time: datetime):
    room_area = utils.room_area
    room_area = max(1, room_area)
    # delete area of furniture
    room_area = round(room_area * (1 - utils.room_furniture), 2)

    occupancy_val = occupancy(gap_sec, start_time, end_time)["sequence"]
    # round(1/(10/2.0/5)*100,2)
    people_average_area = 1.0
    result = [0 if i == 0 else round(1/(room_area/people_average_area/i)*100,2) for i in occupancy_val]
    return {"data": result}