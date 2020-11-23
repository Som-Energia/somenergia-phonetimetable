# -*- coding: utf-8 -*-

from future import standard_library
standard_library.install_aliases()
from flask import (
    Flask, Response, request,
    send_from_directory,
    send_file,
    )
from datetime import datetime, timedelta
from threading import Semaphore
import os.path
import urllib.parse
import decorator
import erppeek
from pathlib2 import Path
from sheetfetcher import SheetFetcher
from yamlns import namespace as ns
from consolemsg import error, step, warn

from .callinfo import CallInfo
from . import schedulestorage
from .pbxmockup import PbxMockup
from .claims import Claims

try:
    import dbconfig
except ImportError:
    dbconfig = None

packagedir = Path(__file__).parent
staticpath = packagedir/'dist'
schedules = schedulestorage.Storage.default()


def fillConfigurationInfo():
    return ns.load('config.yaml')


CONFIG = fillConfigurationInfo()


SHEETS = {
    "infos_log": 0,
    "claims_log": 4,
    "general_reasons": 2,
    "specific_reasons": 3
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
    return format(now().date() - timedelta(days=now().weekday()))

dbconfig=None
try:
    import dbconfig
except ImportError:
    pass

from .planner_api import api as Planner

app = Flask(__name__)
app.drive_semaphore = Semaphore()
app.register_blueprint(Planner, url_prefix='/api/planner')


class ApiError(Exception): pass

def yamlfy(status=200, data=[], **kwd):
    return Response(ns(
        data, **kwd
        ).dump(), status,
        mimetype = 'application/x-yaml',
    )

@decorator.decorator
def yamlerrors(f,*args,**kwd):
    try:
        return f(*args,**kwd)
    except ApiError as e:
        error("ApiError: {}", e)
        return yamlfy(
            error=format(e),
            status=400,
            )
    except Exception as e:
        error("UnexpectedError: {}", e)
        return yamlfy(
            error=format(e),
            status=500,
            )

@app.route('/')
@app.route('/<file>')
def tomatic(file=None):
    return send_from_directory(str(staticpath), file or 'index.html')

@app.route('/api/graella-<week>.yaml')
@app.route('/api/graella/<week>')
@yamlerrors
def graellaYaml(week):
    schedule = schedules.load(week)

    return yamlfy(**schedule)

@app.route('/api/graella/<week>/<day>/<int:houri>/'
        '<int:turni>/<name>', methods=['UPDATE'])
@yamlerrors
def editSlot(week, day, houri, turni, name):
    myname = request.data.decode().split('"')[1]
    graella = schedules.load(week)
    # TODO: Ensure day, houri, turni and name are in graella
    oldName = graella.timetable[day][int(houri)][int(turni)]
    graella.timetable[day][int(houri)][int(turni)] = name
    graella.overload = graella.get('overload', ns())
    graella.overload[oldName] = graella.overload.get(oldName, 0) -1
    graella.overload[name] = graella.overload.get(name, 0) +1
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
    print(logmsg)
    graella.setdefault('log',[]).append(logmsg)
    schedules.save(graella)
    schedulestorage.publishStatic(graella)
    return graellaYaml(week)


@app.route('/api/graella/list')
def listGraelles():
    return yamlfy(weeks=schedules.list())

@app.route('/api/graella', methods=['POST'])
@yamlerrors
def uploadGraella(week=None):
    step("uploading {}".format(request.files))
    if 'yaml' not in request.files:
        error("Cap graella pujada")
        return "KO"
    yaml = request.files['yaml']
    if yaml.content_length > 30:
        warn("Pujat yaml sospitosament llarg: {} bytes"
            .format(yaml.content_length))
        return "KO"
    graella = ns.load(yaml.stream)
    logmsg = (
        "{}: {} ha pujat {} ".format(
        datetime.now(),
        "nobody", # TODO: ERP user
        graella.week,
        ))
    graella.setdefault('log',[]).append(logmsg)
    schedules.save(graella)
    schedulestorage.publishStatic(graella)
    return yamlfy(result='ok')

@app.route('/api/graella/retireold')
@yamlerrors
def retireOldTimeTable():
    today = datetime.today()
    twoMondaysAgo = str((today - timedelta(days=today.weekday()+7*2)).date())
    step("Retiring timetables older than {}", twoMondaysAgo)
    try:
        schedules.load(twoMondaysAgo)
    except:
        raise ApiError("Graella {} no trobada, potser ja ha estat retirada".format(twoMondaysAgo))
    else:
        schedules.retireOld(twoMondaysAgo)
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

def persons():
    # TODO: Just load persons.yaml
    config = ns.load('config.yaml')
    if Path('persons.yaml').exists():
        persons = ns.load('persons.yaml')
        config.update(persons)

    return ns(
        names = config.get('names',ns()),
        extensions = config.get('extensions',ns()),
        tables = config.get('tables',ns()),
        colors = config.get('colors',ns()),
        emails = config.get('emails',ns()),
        groups = config.get('groups',ns()),
    )

@app.route('/api/persons/extension/<extension>')
def personInfoFromExtension(extension):
    allpersons=persons()
    names = [name for name,ext in allpersons.extensions.items() if ext == extension]
    if not names:
        return 'nobody@somenergia.coop'
    name = names[0]
    email = allpersons.emails[name]
    return email

@app.route('/api/persons/')
def personInfo():
    result=persons()
    return yamlfy(persons=result)

@app.route('/api/person/<person>', methods=['POST'])
def setPersonInfo(person):
    result = persons()
    print(request.data)
    data = ns.loads(request.data)
    if 'name' in data:
        result.names[person] = data.name
    if 'extension' in data:
        result.extensions[person] = data.extension
    if 'table' in data:
        result.tables[person] = data.table
    if 'color' in data:
        result.colors[person] = data.color
    if 'email' in data:
        result.emails[person] = data.email
    if 'groups' in data:
        for group, components in result.groups.items():
            if person in components and group not in data.groups:
                components.remove(person)
            if group in data.groups and person not in components:
                components.append(person)

    result.dump('persons.yaml')
    return yamlfy(persons=result)

@app.route('/api/busy/<person>', methods=['GET'])
def busy(person):
    from . import busy
    return yamlfy(**busy.busy(person))

@app.route('/api/busy/<person>', methods=['POST'])
def busy_post(person):
    from . import busy
    data = ns.loads(request.data)
    return yamlfy(**busy.update_busy(person, data))

@app.route('/api/busy/download/weekly')
def downloadWeeklyBusy():
    response = send_file(
        '../indisponibilitats.conf',
        as_attachment=True,
        mimetype='text/plain',
    )
    print("response {}".format(response))
    return response

@app.route('/api/busy/download/oneshot')
def downloadOneShotBusy():
    return send_file(
        '../oneshot.conf',
        as_attachment=True,
        mimetype='text/plain',
    )

@app.route('/api/shifts/download/credit/<week>')
@yamlerrors
def downloadWeekShiftCredit(week):
    try:
        credit = schedules.credit(week)
    except schedulestorage.StorageError as e:
        raise ApiError(e)
    return yamlfy(**credit)

@app.route('/api/shifts/download/shiftload/<week>')
def downloadShiftLoad(week):
    loadfile = Path('carrega-{}.csv'.format(week))

    return send_file(
        str('..'/loadfile),
        as_attachment=True,
        mimetype='text/csv',
    )

@app.route('/api/shifts/download/overload/<week>')
def downloadOverload(week):
    loadfile = Path('overload-{}.yaml'.format(week))

    return send_file(
        str('..'/loadfile),
        as_attachment=True,
        mimetype = 'application/x-yaml',
    )

@app.route('/api/info/phone/<phone>', methods=['GET'])
@yamlerrors
def getInfoPersonByPhone(phone):
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByPhone(phone)
        if (not data.partners):
            message = 'no_info'
        elif data.partners == "Masses resultats":
            message = 'response_too_long'
    except ValueError:
        message = 'error_getByPhone'
        error("Getting information from {}.", phone)
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/name/<name>', methods=['GET'])
def getInfoPersonByName(name):
    decoded_name = urllib.parse.unquote(name)
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByName(decoded_name)
        if (not data.partners):
            message = 'no_info'
        elif (data.partners == "Masses resultats"):
            message = 'response_too_long'
    except ValueError:
        message = 'error_getByName'
        error("Getting information from {}.", name)
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/nif/<nif>', methods=['GET'])
def getInfoPersonByNif(nif):
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByDni(nif)
        if (not data.partners):
            message = 'no_info'
        elif (data.partners == "Masses resultats"):
            message = 'response_too_long'
    except ValueError:
        message = 'error_getByDni'
        error("Getting information from {}.", nif)
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/soci/<iden>', methods=['GET'])
def getInfoPersonBySoci(iden):
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getBySoci(iden)
        if (not data.partners):
            message = 'no_info'
        elif (data.partners == "Masses resultats"):
            message = 'response_too_long'
    except ValueError:
        message = 'error_getBySoci'
        error("Getting information from {}.", iden)
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/email/<email>', methods=['GET'])
def getInfoPersonByEmail(email):
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByEmail(email)
        if (not data.partners):
            message = 'no_info'
        elif (data.partners == "Masses resultats"):
            message = 'response_too_long'
    except ValueError:
        message = 'error_getByEmail'
        error("Getting information from {}.", email)
    result = ns(
        info=data,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/info/all/<field>', methods=['GET'])
def getInfoPersonBy(field):
    decoded_field = urllib.parse.unquote(field)
    message = 'ok'
    o = erppeek.Client(**dbconfig.erppeek)
    info = CallInfo(o)
    data = None
    try:
        data = info.getByData(decoded_field)
        if (not data.partners):
            message = 'no_info'
        elif (data.partners == "Masses resultats"):
            message = 'response_too_long'
    except ValueError:
        message = 'error_getByData'
        error("Getting information from {}.", field)
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
    clients = app.websocket_kalinfo_server.websockets.get(ext, [])
    time = datetime.now().strftime('%m-%d-%Y %H:%M:%S')

    if not os.path.exists('atc_cases'):
        os.makedirs('atc_cases')

    if not os.path.isfile(CONFIG.my_calls_log):
        error("[U] Opening file {} but it doesn't exists", CONFIG.my_calls_log)
        step("Creating file...")

        f = open(CONFIG.my_calls_log, "w+")
        f.close()
        logs = ns()
    else:
        logs = ns.load(CONFIG.my_calls_log)

    if ext not in logs:
        logs[ext] = []
    elif len(logs[ext]) == 20:
        logs[ext].pop(0)
    info = {
        "data": time,
        "telefon": phone,
        "motius": "",
        "partner": "",
        "contracte": "",
    }
    logs[ext].append(info)
    logs.dump(CONFIG.my_calls_log)

    if not clients:
        error("Calling {} but has no client.", ext)
    for client in clients:
        app.websocket_kalinfo_server.wserver.send_message(client, "PHONE:" + phone + ":" + time)
    result = ns(
        notified=len(clients),
        phone=phone,
        ext=ext,
    )
    return yamlfy(info=result)


@app.route('/api/socketInfo', methods=['GET'])
def getConnectionInfo():
    result = ns(
        port_ws=CONFIG.websocket_port,
        message="ok"
    )
    return yamlfy(info=result)


@app.route('/api/callReasons/<info_type>', methods=['GET'])
def getReasonsInfo(info_type):
    message = 'ok'
    try:
        fetcher = SheetFetcher(
            documentName=CONFIG.call_reasons_document,
            credentialFilename=CONFIG.credential_name,
        )
        reasons = fetcher.get_fullsheet(
                SHEETS["general_reasons"] if info_type == 'general' else SHEETS["specific_reasons"]
        )
    except IOError:
        reasons = []
        message = 'error_get_fullsheet'
        error("Trying to open {} drive sheet.", CONFIG.call_reasons_document)
    result = ns(
        info=reasons,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/infoReasons', methods=['POST'])
def savePhoneInfosLog():
    message = 'ok'
    try:
        info = ns.loads(request.data)
        fetcher = SheetFetcher(
            documentName=CONFIG.call_reasons_document,
            credentialFilename=CONFIG.credential_name,
        )
        row = [
            info.date,
            info.person,
            info.phone,
            info.reason,
            info.extra,
        ]
        with app.drive_semaphore:
            fetcher.add_to_last_row(SHEETS["infos_log"], row)
    except IOError:
        error("Saving {} to the drive sheet.", CONFIG.call_reasons_document)
        message = 'error_add_to_las_row'
    result = ns(
        message=message
    )
    return yamlfy(info=result)


@app.route('/api/claimReasons', methods=['POST'])
def savePhoneClaimsLog():
    message = 'ok'
    try:
        info = ns.loads(request.data)
        fetcher = SheetFetcher(
            documentName=CONFIG.call_reasons_document,
            credentialFilename=CONFIG.credential_name,
        )
        row = [
            info.date,
            info.person,
            info.partner,
            info.contract,
            info.cups,
            info.user,
            info.reason,
            info.procedente,
            info.improcedente,
            info.solved,
            info.observations,
        ]
        with app.drive_semaphore:
            fetcher.add_to_last_row(SHEETS["claims_log"], row)
    except IOError:
        error("Saving {} to the drive sheet.", CONFIG.call_reasons_document)
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
            documentName=CONFIG.call_reasons_document,
            credentialFilename=CONFIG.credential_name,
        )
        log = fetcher.get_fullsheet(SHEETS["infos_log"])
    except IOError:
        log = []
        message = 'error_get_fullsheet'
        error("Getting reason calls from {}.", CONFIG.call_reasons_document)
    reasons = [x for x in log if x[LOGS["phone"]] == phone]
    reasons.sort(key=lambda x: datetime.strptime(x[0], '%d-%m-%Y %H:%M:%S'))
    result = ns(
        info=reasons,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/personlog/', methods=['GET'])
@app.route('/api/personlog/<ext>', methods=['GET'])
def getMyLog(ext=-1):
    message = 'ok'
    mylog = ""
    try:
        logs = ns.load(CONFIG.my_calls_log)
        if ext in logs:
            mylog = logs[ext]
        else:
            message = 'not_registers_yet'
            error("{} does not appear in the register.", ext)
    except IOError:
        message = 'not_register_yet'
        error("There are not calls in the register yet.")
    result = ns(
        info=mylog,
        message=message,
    )
    return yamlfy(info=result)


@app.route('/api/updatelog/<ext>', methods=['POST'])
def updateMyLog(ext):
    msg = 'ok'

    try:
        logs = ns.load(CONFIG.my_calls_log)
        info = ns.loads(request.data)
        if ext not in logs:
            logs[ext] = [info]
        for call in logs[ext]:
            if call.data == info.data:
                i = logs[ext].index(call)
                logs[ext].pop(i)
                logs[ext].insert(i, info)
                break
        logs.dump(CONFIG.my_calls_log)
        app.websocket_kalinfo_server.say_logcalls_has_changed(ext)
    except ValueError:
        msg = 'error_update_log'
        error("[U] Opening file {}: unexpected", CONFIG.my_calls_log)
    result = ns(
        message=msg
    )
    return yamlfy(info=result)


@app.route('/api/updateClaims', methods=['GET'])
def updateClaims():
    message = 'ok'

    o = erppeek.Client(**dbconfig.erppeek)
    claims = Claims(o)
    erp_claims = claims.get_claims()

    f = open(CONFIG.claims_file, "w+")
    for claim in erp_claims:
        try:
            f.write(claim.encode('utf-8'))
        except:
            f.write(claim)
        f.write('\n')
    f.close()

    result = ns(
        message=message
    )
    return yamlfy(info=result)


@app.route('/api/getClaims', methods=['GET'])
def getClaims():
    message = 'ok'
    claims = []
    claims_dict = []
    try:
        f = open(CONFIG.claims_file, "r")
        for line in f:
            claims.append(line.strip())
        f.close()
    except IOError:
        message = "error"
        error("File of claims does not exist")

    try:
        claims_dict = ns.load(CONFIG.claims_dict_file)
    except IOError:
        message = "error"
        error("File of claims dict does not exist")

    result = ns(
        message=message,
        claims=claims,
        dict=claims_dict,
    )
    return yamlfy(info=result)


@app.route('/api/atrCase', methods=['POST'])
def postAtrCase():

    atc_info = ns.loads(request.data)

    today = datetime.today()
    file_name = "atc_cases/{}{}{}.yaml".format(
        today.year,
        today.month if today.month//10 != 0 else "0{}".format(today.month),
        today.day if today.day//10 != 0 else "0{}".format(today.day),
    )
    if not os.path.isfile(file_name):
        with open(file_name, "w+"): pass

    atc_cases = ns.load(file_name) or ns()

    if atc_info.person not in atc_cases:
        atc_cases[atc_info.person] = []

    atc_cases[atc_info.person].append(atc_info)

    atc_cases.dump(file_name)

    return yamlfy(info=ns(
        message="ok"
    ))


@app.route('/api/getInfos', methods=['GET'])
def getInfos():
    message = 'ok'
    infos = []
    try:
        with open(CONFIG.info_cases, "r") as f:
            infos = f.read().splitlines()
    except IOError:
        message = "error"
        error("File of infos does not exist")

    result = ns(
        message=message,
        infos=infos,
    )
    return yamlfy(info=result)


@app.route('/api/infoCase', methods=['POST'])
def postInfoCase():

    info = ns.loads(request.data)

    today = datetime.today()
    file_name = "info_cases/{}{}{}.yaml".format(
        today.year,
        today.month if today.month//10 != 0 else "0{}".format(today.month),
        today.day if today.day//10 != 0 else "0{}".format(today.day),
    )
    if not os.path.isfile(file_name):
        with open(file_name, "w+"): pass

    info_cases = ns.load(file_name) or ns()

    if info.person not in info_cases:
        info_cases[info.person] = []

    info_cases[info.person].append(info)

    info_cases.dump(file_name)

    return yamlfy(info=ns(
        message="ok"
    ))


# vim: ts=4 sw=4 et
