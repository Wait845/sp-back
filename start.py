from flask import Flask, request, render_template
from dao import DataAccess
import json
import configuration
from datetime import datetime, timedelta
import utils
import info_compute
from flask_cors import CORS


app = Flask(__name__, template_folder="build", static_folder="build/static")
CORS(app, resources=r"/*")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/report", methods=["GET"])
def report():
    return render_template("index.html")

@app.route("/setting", methods=["GET"])
def setting():
    return render_template("index.html")

@app.route("/api/status/", methods=["GET"])
def status_handle():
    # gap 10s, duration 20 mins
    # http://192.168.31.10:888/api/status/?gap_sec=10&s_time=1646829577&e_time=1646830777
    gap_sec = int(request.args.get("gap_sec"))
    start_time = int(request.args.get("s_time"))
    end_time = int(request.args.get("e_time"))

    start_time = datetime.fromtimestamp(start_time)
    end_time = datetime.fromtimestamp(end_time)

    result = info_compute.occupancy(gap_sec, start_time, end_time)
    if result:
        return json.dumps(result)
    return "error"


@app.route("/api/enter_exits/", methods=["GET"])
def enter_handle():
    # gap 60s
    # http://192.168.31.10:888/api/enter_exits/?gap_sec=60&s_time=1646830881&e_time=1646833881
    gap_sec = int(request.args.get("gap_sec"))
    start_time = int(request.args.get("s_time"))
    end_time = int(request.args.get("e_time"))

    start_time = datetime.fromtimestamp(start_time)
    end_time = datetime.fromtimestamp(end_time)
    # print(start_time, end_time)
    result = info_compute.enter_exits(gap_sec, start_time, end_time)
    if result:
        return json.dumps(result)
    return "error"


@app.route("/api/flow_rate/", methods=["GET"])
def flow_rate():
    gap_sec = int(request.args.get("gap_sec"))
    start_time = int(request.args.get("s_time"))
    end_time = int(request.args.get("e_time"))

    start_time = datetime.fromtimestamp(start_time)
    end_time = datetime.fromtimestamp(end_time)
    result = info_compute.flow_rate(gap_sec, start_time, end_time)
    if result:
        return json.dumps(result)
    return "error"


@app.route("/api/access_log/", methods=["GET"])
def access_log():
    num = int(request.args.get("num"))
    sql_get_log = "\
        SELECT interface, addr, timestamp \
        FROM detect_stream \
        ORDER BY timestamp DESC \
        LIMIT {}".format(num)
    dao = DataAccess()
    result_get_log = dao.execute(sql_get_log)
    if result_get_log == None:
        return ""
    result_get_log = list(result_get_log)
    for i in range(len(result_get_log)):
        result_get_log[i] = list(result_get_log[i])
        result_get_log[i][2] = datetime.strftime(result_get_log[i][2], "%H:%M:%S")
    return json.dumps({"data":result_get_log})


@app.route("/api/detect_log", methods=["GET"])
def detect_log():
    sql_get_detect = "\
        SELECT DISTINCT addr, manuf \
        FROM detect_stream \
        WHERE timestamp > DATE_SUB(NOW(), INTERVAL 60 SECOND) \
        AND addr in ( \
            SELECT DISTINCT addr \
            FROM detect_device \
            WHERE timestamp > DATE_SUB(NOW(), INTERVAL 120 SECOND ) \
            )"
    dao = DataAccess()
    result_get_log = dao.execute(sql_get_detect)
    if result_get_log == None:
        return ""
    return json.dumps({"data": result_get_log})


@app.route("/api/ignore_address/", methods=["GET"])
def add_ignore_address():
    ignore_addr = request.args.get("addr")
    ignore_list = utils.get_ignore_address()
    if ignore_list == "" or ignore_list == "null":
        ignore_list = []
    else:
        ignore_list = json.loads(ignore_list)
    ignore_list.append(ignore_addr)

    dao = DataAccess()
    sql_record_ignore = "\
        REPLACE INTO config \
        SET `key` = 'ignore_address', \
            val = '{}'".format(
            json.dumps(ignore_list)
    )
    dao.execute(sql_record_ignore)
    return json.dumps({"data":ignore_list})


@app.route("/api/del_ignore_address/", methods=["GET"])
def del_ignore_address():
    ignore_addr = request.args.get("addr")
    ignore_list = utils.get_ignore_address()
    if ignore_list == "":
        ignore_list = []
    else:
        ignore_list = json.loads(ignore_list)
    ignore_list.remove(ignore_addr)

    dao = DataAccess()
    sql_record_ignore = "\
        REPLACE INTO config \
        SET `key` = 'ignore_address', \
            val = '{}'".format(
            json.dumps(ignore_list)
    )
    dao.execute(sql_record_ignore)
    return json.dumps({"data":ignore_list})


@app.route("/ignore_address/", methods=["GET"])
def ignore_address():
    ignore_list = utils.get_ignore_address()
    if ignore_list == "":
        return json.dumps({"data":[]})
    ignore_list = json.loads(ignore_list)
    return json.dumps({"data":ignore_list})


@app.route("/api/notify_device/", methods=["GET"])
def add_notify_device():
    notify_id = request.args.get("id")
    notify_list = utils.get_notify_device()
    if notify_list == "" or notify_list == "null":
        notify_list = []
    else:
        notify_list = json.loads(notify_list)
    notify_list.append(notify_id)

    dao = DataAccess()
    sql_record_ignore = "\
        REPLACE INTO config \
        SET `key` = 'notify_device', \
            val = '{}'".format(
            json.dumps(notify_list)
    )
    dao.execute(sql_record_ignore)
    return json.dumps({"data":notify_list})

@app.route("/api/del_notify_device/", methods=["GET"])
def del_notify_device():
    notify_id = request.args.get("id")
    notify_list = utils.get_notify_device()
    if notify_list == "":
        notify_list = []
    else:
        notify_list = json.loads(notify_list)
    notify_list.remove(notify_id)

    dao = DataAccess()
    sql_record_ignore = "\
        REPLACE INTO config \
        SET `key` = 'notify_device', \
            val = '{}'".format(
            json.dumps(notify_list)
    )
    dao.execute(sql_record_ignore)
    return json.dumps({"data":notify_list})


@app.route("/notify_device/", methods=["GET"])
def notify_device():
    notify_list = utils.get_notify_device()
    if notify_list == "":
        return json.dumps({"data":[]})
    print(notify_list)
    notify_list = json.loads(notify_list)
    return json.dumps({"data":notify_list})


@app.route("/sensor_status/", methods=["GET"])
def sensor_status():
    result = {s:1 for s in utils.ap_position.keys()}
    for s in utils.sensor_filter_list:
        if result.get(s, None):
            result[s] = 0
    return json.dumps({"data":result})


@app.route("/api/sensor_status/", methods=["GET"])
def sensor_switch():
    sensor = request.args.get("sensor")
    if sensor in utils.sensor_filter_list:
        utils.sensor_filter_list.remove(sensor)
    else:
        utils.sensor_filter_list.add(sensor)
    return ""


@app.route("/overflow_num/", methods=["GET"])
def overflow_num():
    num = utils.get_overflow_num()
    return json.dumps({"data":num})


@app.route("/api/overflow_num/", methods=["GET"])
def set_overflow_num():
    num = int(request.args.get("num"))
    dao = DataAccess()
    sql_record_num = "\
        REPLACE INTO config \
        SET `key` = 'overflow_num', \
            val = {}".format(
            num
    )
    dao.execute(sql_record_num)
    return ""

@app.route("/update_room_position/", methods=["POST"])
def update_room_position():
    if request.method == "POST":
        form_dict = request.form.to_dict()
        position_list = form_dict.get("position", '[]')
        try:
            position_list = json.loads(position_list)
        except:
            return "invalid data form"
        utils.update_room_position(position_list)
        return "success update room position"
    else:
        return "invalid method"


@app.route("/update_ap_position/", methods=["POST"])
def update_ap_position():
    if request.method == "POST":
        form_dict = request.form.to_dict()
        position_dict = form_dict.get("position", '{}')
        try:
            position_dict = json.loads(position_dict)
        except:
            return "invalid data form"
        utils.update_ap_position(position_dict)
        return "success update ap position"
    else:
        return "invalid method"




@app.route("/detect_info/", methods=["POST"])
def detect_info():
    """receving detected messages and record
    """
    et = datetime.now()
    st = et - timedelta(minutes=30)
    print(info_compute.occupancy(60, st, et))

    if request.method == "POST":
        form_dict = request.form.to_dict()
        data_list = form_dict.get("data", '[]')
        try:
            data_list = json.loads(data_list)
        except:
            return "invalid data form"

        if len(data_list) == 0:
            return "None Data"
        ig_addr = utils.get_ignore_address()
        record_count = 0
        record_data_list = []
        start_time = None
        for data in data_list:
            interface = data.get("interface", None)
            addr = data.get("addr", None)
            target = data.get("target", "")
            manuf = data.get("manuf", "")
            rssi = data.get("rssi", None)
            frequency = data.get("frequency", None)
            channel = data.get("channel", None)
            timestamp = data.get("timestamp", None)
            probe_type = data.get("probe_type", None)
            distance = data.get("distance", None)

            # filter none data
            if None in [interface, addr, rssi, frequency, channel, timestamp, probe_type, distance]:
                continue
            if addr in ig_addr:
                continue
            if interface in utils.sensor_filter_list:
                continue

            # cover timestamp to str
            timestamp = datetime.fromtimestamp(timestamp)
            if start_time == None:
                start_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")

            record_data = (interface, addr, target, manuf, rssi, frequency, channel, timestamp, probe_type, distance)
            record_data_list.append(record_data)
            record_count += 1
        # print(record_data_list)

        sql_record_info = "\
            INSERT INTO detect_stream \
                (interface, addr, target, manuf, rssi, frequency, channel, timestamp, probe_type, distance) \
            VALUES {};".format(
                str(record_data_list)[1:-1]
            )
        
        # print(sql_record_info)

        dao = DataAccess()
        sql_record_result = dao.execute(sql_record_info)
        print("record result:", sql_record_result)
        if sql_record_result != None:
            utils.calculate_stream(start_time, 20)
            return "success recorded {}".format(record_count)
        else:
            return "record failed!"

    else:
        return "invalid method"


if __name__ == "__main__":
    config = configuration.config
    listen_ip = config.get("general", "listen_ip")
    listen_port = config.get("general", "listen_port")
    utils.listen_overflow_num()
    app.run(listen_ip, listen_port, debug=True)