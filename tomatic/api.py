# -*- coding: utf-8 -*-

from flask import (
    Flask, Response, request,
    redirect, url_for,
    send_from_directory,
    )
from datetime import datetime, timedelta
from yamlns import namespace as ns
from callinfo import CallInfo
from websocket_server import WebsocketServer
from . import schedulestorage
from .pbxmockup import PbxMockup
from .htmlgen import HtmlGen
from .remote import remotewrite
import os
import erppeek
from sheetfetcher import SheetFetcher
from threading import Semaphore
try:
    import dbconfig
except ImportError:
    dbconfig = None

packagedir = os.path.join(os.path.dirname(__file__))
schedules_path = os.path.join(packagedir,'..','graelles')
schedules = schedulestorage.Storage(schedules_path)
staticpath = os.path.join(packagedir,'dist')
websockets = {}

CONFIG = ns.load('config_connection.yaml')

SHEETS = {
    "log": 0,
    "reasons": 1,
}

LOGS = {
    "date": 0,
    "person": 1,
    "phone": 2,
    "partner": 3,
    "contract": 4,
    "reason": 5,
    "proc": 6,
    "improc": 7,
    "extras": 8,
}


def pbx(alternative = None):
    if alternative:
        pbx.cache = alternative
    if not hasattr(pbx,'cache'):
        p = PbxMockup(now)
        p.reconfigure(schedules.load(thisweek()))
        pbx.cache = p
    return pbx.cache

def now():
    return datetime.now()

def anow():
    return datetime(2016,12,27,10,23,23)

def thisweek():
    return str(now().date() - timedelta(days=now().weekday()))

dbconfig=None

try:
    import dbconfig
except ImportError:
    pass

app = Flask(__name__)
app.wserver = None
app.drive_semaphore = Semaphore()

def publishStatic(graella):
    if not dbconfig: return
    if not hasattr(dbconfig, 'tomatic'): return
    if not hasattr(dbconfig.tomatic, 'publishStatic'): return
    params = dbconfig.tomatic.publishStatic
    sched=HtmlGen(graella)
    remotewrite(
        params.user,
        params.host,
        os.path.join(params.path,
            'graella-{week}.html'.format(**graella)),
        sched.html(),
        )

class ApiError(Exception): pass

import decorator

@decorator.decorator
def yamlerrors(f,*args,**kwd):
    try:
        return f(*args,**kwd)
    except ApiError as e:
        raise
        return yamlfy(
            error=str(e),
            status=500,
            )

@app.route('/')
@app.route('/<file>')
def tomatic(file=None):
    return send_from_directory(staticpath, file or 'index.html')

@app.route('/api/graella-<week>.yaml')
@app.route('/api/graella/<week>')
def graellaYaml(week):
    # TODO: ensure week is an iso date
    # TODO: ensure week is monday

    schedule = schedules.load(week)

    return Response(
        schedule.dump(),
        mimetype = 'application/x-yaml',
        )

@app.route('/api/graella/<week>/<day>/<int:houri>/'
        '<int:turni>/<name>', methods=['UPDATE'])
@yamlerrors
def editSlot(week, day, houri, turni, name):
    myname = request.data.split('"')[1]
    # TODO: Same ensures than graella
    graella = schedules.load(week)
    # TODO: Ensure day, houri, turni and name are in graella
    oldName = graella.timetable[day][int(houri)][int(turni)]
    graella.timetable[day][int(houri)][int(turni)] = name
    logmsg = (
        "{}: {} ha canviat {} {}-{} {} de {} a {}".format(
        datetime.now(),
        myname, # TODO: ERP user
        day,
        graella.hours[int(houri)], 
        graella.hours[int(houri)+1], 
        graella.turns[int(turni)],
        oldName,
        name
        ))
    graella.setdefault('log',[])
    print logmsg
    graella.log.append(logmsg)
    schedules.save(graella)
    publishStatic(graella)
    return graellaYaml(week)


@app.route('/api/graella/list')
def listGraelles():
    return Response(
        ns(weeks=schedules.list()).dump(),
        mimetype = 'application/x-yaml')

@app.route('/api/graella', methods=['POST'])
@yamlerrors
def uploadGraella(week=None):
    print "uploading", request.files
    if 'yaml' not in request.files:
        print("Cap graella pujada")
        return "KO"
    yaml = request.files['yaml']
    if yaml.content_length > 30:
        print("Pujat yaml sospitosament llarg: {} bytes"
            .format(yaml.content_length))
        return "KO"
    graella = ns.load(yaml.stream)
    logmsg = (
        "{}: {} ha pujat {} ".format(
        datetime.now(),
        "nobody", # TODO: ERP user
        graella.week,
        ))
    graella.setdefault('log',[])
    print logmsg
    schedules.save(graella)
    publishStatic(graella)
    return yamlfy(result='ok')

@app.route('/api/queue')
def get_queue():
    return yamlfy(
        currentQueue = pbx().currentQueue()
    )

@app.route('/api/queue/add/<person>')
def add_line(person):
    p = pbx()
    p.addLine(person)
    return yamlfy(
        currentQueue = p.currentQueue()
    )

@app.route('/api/queue/pause/<person>')
def pause_line(person):
    p = pbx()
    p.pause(person)
    return yamlfy(
        currentQueue = p.currentQueue()
    )

@app.route('/api/queue/resume/<person>')
def resume_line(person):
    p = pbx()
    p.resume(person)
    return yamlfy(
        currentQueue = p.currentQueue()
    )

@app.route('/api/persons/')
def personInfo():
    config = ns.load('config.yaml')
    result = ns(
        names = config.names,
        extensions = config.extensions,
        tables = config.taules,
        colors = config.colors,
    )
    return yamlfy(persons=result)

@app.route('/api/person/<person>', methods=['POST'])
def setPersonInfo(person):
    config = ns.load('config.yaml')
    print(request.data)
    data = ns.loads(request.data)
    if 'name' in data:
        config.names[person] = data.name
    if 'extension' in data:
        config.extensions[person] = data.extension
    if 'table' in data:
        config.taules[person] = data.table
    if 'color' in data:
        config.colors[person] = data.color
    config.dump('config.yaml')
    result = ns(
        names = config.names,
        extensions = config.extensions,
        tables = config.taules,
        colors = config.colors,
    )
    return yamlfy(persons=result)

@app.route('/api/busy/<person>', methods=['GET'])
def busy(person):
    import busy
    return yamlfy(**busy.busy(person))

@app.route('/api/busy/<person>', methods=['POST'])
def busy_post(person):
    import busy
    data = ns.loads(request.data)
    return yamlfy(**busy.update_busy(person, data))


@app.route('/api/info/phone/<phone>', methods=['GET'])
def getInfoPersonByPhone(phone):
    decoded_phone = phone.decode('base64')
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByPhone(decoded_phone)
    except ValueError:
        message = 'error_getByPhone'
        print "Error: Obtenció de la informació a partir del telèfon."
    if (not data.partners):
        message = 'no_info'
    elif data.partners == "Masses resultats":
        message = 'response_too_long'
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/name/<name>', methods=['GET'])
def getInfoPersonByName(name):
    aux = name.decode('base64')
    decoded_name = aux.decode(encoding='latin-1', errors='strict')
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByName(decoded_name)
    except ValueError:
        message = 'error_getByName'
        print "Error: Obtenció de la informació a partir del nom."
    if (not data.partners):
        message = 'no_info'
    elif (data.partners == "Masses resultats"):
        message = 'response_too_long'
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/nif/<nif>', methods=['GET'])
def getInfoPersonByNif(nif):
    decoded_nif = nif.decode('base64')
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByDni(decoded_nif)
    except ValueError:
        message = 'error_getByDni'
        print "Error: Obtenció de la informació a partir del nif."
    if (not data.partners):
        message = 'no_info'
    elif (data.partners == "Masses resultats"):
        message = 'response_too_long'
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/soci/<iden>', methods=['GET'])
def getInfoPersonBySoci(iden):
    decoded_iden = iden.decode('base64')
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getBySoci(decoded_iden)
    except ValueError:
        message = 'error_getBySoci'
        print "Error: Obtenció de la informació a partir del num de soci."
    if (not data.partners):
        message = 'no_info'
    elif (data.partners == "Masses resultats"):
        message = 'response_too_long'
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/email/<email>', methods=['GET'])
def getInfoPersonByEmail(email):
    decoded_email = email.decode('base64')
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByEmail(decoded_email)
    except ValueError:
        message = 'error_getByEmail'
        print "Error: Obtenció de la informació a partir del email."
    if (not data.partners):
        message = 'no_info'
    elif (data.partners == "Masses resultats"):
        message = 'response_too_long'
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/all/<field>', methods=['GET'])
def getInfoPersonBy(field):
    decoded_field = field.decode('base64')
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByData(decoded_field)
    except ValueError:
        message = 'error_getByData'
        print "Error: Obtenció de la informació a partir del camp general."
    if (not data.partners):
        message = 'no_info'
    elif (data.partners == "Masses resultats"):
        message = 'response_too_long'
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/ringring', methods=['POST'])
def callingPhone():
    data = request.form.to_dict()
    phone = data['phone']
    ext = data['ext']
    try:
        clients = websockets[ext]
        for client in clients:
            app.wserver.send_message(client, phone)
    except ValueError:
        print ext + " sense identificar."
    result = ns(
        phone=phone,
        ext=int(ext),
    )
    return yamlfy(info=result)


@app.route('/api/socketInfo', methods=['GET'])
def getConnectionInfo():
    result = ns(
        ip=CONFIG.ip,
        port=CONFIG.port,
        port_ws=CONFIG.port_ws,
        adress=CONFIG.adress,
        message="ok"
    )
    return yamlfy(info=result)


def initialize_client(client, server, extension):
    if extension not in websockets:
        websockets[extension] = []
    websockets[extension].append(client)


def client_left(client, server):
    for ext in websockets:
        if client in websockets[ext]:
            websockets[ext].remove(client)
            break


@app.route('/api/info/openSock', methods=['GET'])
def obreConnexio():
    message = 'error_WebSocketServer'
    if not app.wserver:
        app.wserver = WebsocketServer(CONFIG.port_ws, host=CONFIG.ip)
        app.wserver.set_fn_message_received(initialize_client)
        app.wserver.set_fn_client_left(client_left)
        app.wserver.run_forever()
        message = 'ok'
    else:
        message = 'done'
    result = ns(
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/generalReasons', methods=['GET'])
def reasonsInfo():
    message = 'ok'
    try:
        fetcher = SheetFetcher(
            documentName=CONFIG.document_name,
            credentialFilename=CONFIG.credential_name,
        )
        reasons = fetcher.get_fullsheet(SHEETS["reasons"])
    except IOError:
        reasons = []
        message = 'error_get_fullsheet'
        print "Error: Obtenció dels motius generals."
    result = ns(
        info=reasons,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/reasons', methods=['POST'])
def savePhoneLog():
    message = 'ok'
    try:
        info = ns.loads(request.data)
        fetcher = SheetFetcher(
            documentName=CONFIG.document_name,
            credentialFilename=CONFIG.credential_name,
        )
        row = [
            info["date"],
            info["person"],
            info["phone"],
            info["partner"],
            info["contract"],
            info["reason"],
            info["procedente"],
            info["improcedente"],
            info["extra"],
        ]
        with app.drive_semaphore:
            fetcher.add_to_last_row(SHEETS["log"], row)
    except IOError:
        print 'Error: Desar al full de calcul.'
        message = 'error_add_to_las_row'
    result = ns(
        message=message
    )
    return yamlfy(info=result)


@app.route('/api/log/<phone>', methods=['GET'])
def getPhoneLog(phone):
    message = 'ok'
    try:
        fetcher = SheetFetcher(
            documentName=CONFIG.document_name,
            credentialFilename=CONFIG.credential_name,
        )
        log = fetcher.get_fullsheet(SHEETS["log"])
    except IOError:
        log = []
        message = 'error_get_fullsheet'
        print "Error: Obtenció histric de trucades del número."
    reasons = filter(lambda x: x[LOGS["phone"]] == phone, log)
    reasons.sort(key=lambda x: datetime.strptime(x[0], '%d-%m-%Y %H:%M:%S'))
    result = ns(
        info=reasons,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/personlog/<iden>', methods=['GET'])
def getMyLog(iden):
    message = 'ok'
    mylog = ""
    try:
        logs = ns.load(CONFIG.my_calls_log)
        if iden in logs:
            mylog = logs[iden]
        else:
            message = 'not_registers_yet'
            print iden + " no apareix al registre."
    except IOError:
        f = open("my_calls_log.yaml", "w+")
        f.write("nom:\r\n")
        f.write("- data: DD-MM-YYYY HH:MM:SS\r\n")
        f.write("  telefon: \'Num de Telefon\' \r\n")
        f.write("  partner: NumPartner\r\n")
        f.write("  contracte: \'Num de Contracte\' \r\n")
        f.write("  motius: \'[ETIQUETA] Motiu1, [ETIQUETA] Motiu2\' \r\n")
        f.close()
    result = ns(
        info=mylog,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/mylog/<iden>', methods=['POST'])
def saveMyLog(iden):
    msg = 'ok'
    try:
        logs = ns.load(CONFIG.my_calls_log)
        info = ns.loads(request.data)
        if iden not in logs:
            logs[iden] = []
        elif len(logs[iden]) == 20:
            logs[iden].pop(0)
        logs[iden].append(info)
        logs.dump(CONFIG.my_calls_log)
    except ValueError:
        msg = 'error_save_log'
        print "Error desant informació del log de" + iden + "."
    result = ns(
        message=msg
    )
    return yamlfy(info=result)


@app.route('/api/updatelog/<iden>', methods=['POST'])
def updateMyLog(iden):
    msg = 'ok'
    try:
        logs = ns.load(CONFIG.my_calls_log)
        info = ns.loads(request.data)
        for call in logs[iden]:
            if call["data"] == info["data"]:
                i = logs[iden].index(call)
                logs[iden].pop(i)
                logs[iden].insert(i, info)
                break
        logs.dump(CONFIG.my_calls_log)
    except ValueError:
        msg = 'error_update_log'
        print "Error actualitzant informació del log de" + iden + "."
    result = ns(
        message=msg
    )
    return yamlfy(info=result)


def yamlfy(status=200, data=[], **kwd):
    return Response(ns(
        data, **kwd
        ).dump(), status,
        mimetype = 'application/x-yaml',
    )


# vim: ts=4 sw=4 et
