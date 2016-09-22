# -*- coding: utf-8 -*-
from flask import Flask
from htmlgen import HtmlGenFromYaml
from datetime import datetime
from yamlns import namespace as ns

hs = {}
app = Flask(__name__)
now = None

def loadYaml(yaml):
    global hs
    parsedYaml = ns.loads(yaml)
    week = str(parsedYaml.setmana)
    setmana_underscore = week.replace("-","_")
    hs[setmana_underscore]=HtmlGenFromYaml(parsedYaml)

def setNow(year,month,day,hour,minute):
    global now
    now=datetime(year,month,day,hour,minute)

@app.route('/')
def index():
    global now
    if not now:
        now=datetime.now()
    return get_queue(
        "_".join([
            str(now.year),
            "%02d" % now.month,
            "%02d" % now.day]),
        now.hour,
        now.minute
    )

@app.route('/getqueue/<setmana>/<hour>/<minute>')
def get_queue(setmana,hour,minute):
    year,month,day=(
        int(tok) 
        for tok 
        in setmana.split('_')
    )
    startOfWeek = HtmlGenFromYaml.iniciSetmana(
        datetime(year,month,day)
    )
    h = hs[startOfWeek.strftime("%Y_%m_%d")]
    day,turn = h.getCurrentQueue(
        datetime(year,month,day,int(hour),int(minute))
    )
    response = (h.htmlHeader()+
        h.htmlColors()+
        h.htmlSubHeader()+
        h.htmlSetmana()+
        h.partialCurrentQueue(day,turn)+
        h.htmlExtensions()+
        h.htmlFixExtensions()+
        h.htmlFooter()
    )
    return response
