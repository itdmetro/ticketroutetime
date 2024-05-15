import pandas as pd
import requests
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

def main(query_params):
    startStation = query_params.get("起站", [None])[0]
    endStation = query_params.get("迄站", [None])[0]

    if startStation is None:
        response_data = {
            "error": "請輸入起站"
        }
        return response_data

    if endStation is None:
        response_data = {
            "error": "請輸入迄站"
        }
        return response_data

    if "站" in startStation:
        APIstartStation = startStation.replace("站","")
    else:
        APIstartStation = startStation
        startStation += "站"
    if "站" in endStation:
        APIendStation = endStation.replace("站","")
    else:
        APIendStation = endStation
        endStation += "站"

    # print("APIstartStation:",APIstartStation)
    # print("APIendStation:",APIendStation)
    # print("startStation:",startStation)
    # print("endStation:",endStation)

    #接票價API進來
    url = "https://data.taipei/api/v1/dataset/893c2f2a-dcfd-407b-b871-394a14105532?scope=resourceAquire&q=起站 {}&limit=1000".format(APIstartStation)
    # url = "https://data.taipei/api/v1/dataset/893c2f2a-dcfd-407b-b871-394a14105532?scope=resourceAquire&q=起站 淡水&limit=1000"
    ticketAPI = requests.get(url)
    # "https://data.taipei/api/v1/dataset/893c2f2a-dcfd-407b-b871-394a14105532?scope=resourceAquire&q=起站 淡水&limit=1000"
    # print(ticketAPI.json()["result"]["results"])
    ticketAPIresult = ticketAPI.json()["result"]["results"]
    if ticketAPIresult == []:
        response_data = {
            "error": "請輸入正確的起站、迄站"
        }
        return response_data
    try:
        ticketAPIinfo = [x for x in ticketAPIresult if(x["起站"] == APIstartStation) & (x["訖站"] == APIendStation)][0] #json當中抓取符合起站、訖站
    except:
        response_data = {
            "error": "請輸入正確的起站、迄站"
        }
        return response_data
    # print(ticketAPIinfo)
    ticket_full = ticketAPIinfo["全票票價"]
    ticket_ntpekid = ticketAPIinfo["敬老卡愛心卡愛心陪伴卡及新北市兒童優惠票價"]
    ticket_tpekid = ticketAPIinfo["臺北市兒童優惠票價"]
    # print(ticket_full)
    # print(ticket_ntpekid)
    # print(ticket_tpekid)

    #讀取轉乘csv：
    TravelTimetable = pd.read_csv("TravelTime2020.csv", header=0, sep = ',', dtype={"EntryStationID": "object", "ExitStationID": "object"})
    # EntryStationID    EntryStationName    ExitStationID   ExitStationName TravelTime  PathC   PathE
    # 007   松山機場站   008 中山國中站   3   搭乘文湖線（往動物園） Take Wenhu Line（to Taipei Zoo）from Songshan Airport Station => Zhongshan Junior High School Station

    # print(TravelTimetable.dtypes)
    # print(TravelTimetable.columns)
    # print(TravelTimetable.head())

    TravelTime = TravelTimetable["TravelTime"][(TravelTimetable["EntryStationName"] == startStation) & (TravelTimetable["ExitStationName"] == endStation)].values[0]
    PathC = TravelTimetable["PathC"][(TravelTimetable["EntryStationName"] == startStation) & (TravelTimetable["ExitStationName"] == endStation)].values[0]
    #台北小巨蛋站
    #港墘站

    output = startStation+" 至 "+endStation+\
    "\n全票票價："+str(ticket_full)+\
    "\n敬老卡愛心卡愛心陪伴卡及新北市兒童優惠票價："+str(ticket_ntpekid)+\
    "\n臺北市兒童優惠票價："+str(ticket_tpekid)+\
    "\n乘車時間："+str(TravelTime)+"分鐘"+\
    "\n轉乘資訊："+startStation+" => "+PathC+" => "+endStation
    # output = startStation+" 至 "+endStation+"\n乘車時間："+str(TravelTime)+"分鐘\n轉乘資訊："+startStation+" => "+PathC+" => "+endStation
    print(output)

    response_data = {
        "起站": startStation,
        "迄站": endStation,
        "全票票價": str(ticket_full),
        "敬老卡愛心卡愛心陪伴卡及新北市兒童優惠票價": str(ticket_ntpekid),
        "臺北市兒童優惠票價": str(ticket_tpekid),
        "乘車時間": str(TravelTime),
        "轉乘資訊": startStation+" => "+PathC+" => "+endStation,
        "output": output
    }

    return response_data

class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # print(self.path)
        # self.send_response(200)
        # self.end_headers()
        # self.wfile.write(b'Hello, world!')
        # # self.wfile.write('Hello, world!'.encode('utf-8'))
        # # return

        # 解析URL參數
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        # 調用資料處理函式
        response_data = main(query_params)

        # 設置響應頭
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        # 發送JSON響應
        # self.wfile.write(json.dumps(response_data).encode('utf-8'))
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    server = HTTPServer(("0.0.0.0", 8080), MyRequestHandler)
    print("http://0.0.0.0:8080/")
    server.serve_forever()
