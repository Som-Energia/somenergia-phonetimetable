# Changelog

## Unreleased

- 2021 holidays
- Common error handling to all entry points
- areavoip: api calls have a time out, to avoid thread locks
- Fix: areavoip: send 'ids' not 'numbers' in `add` and `clear`
- `tomatic_rtqueue.py` takes `tomatic.areavoip.queue` as default
- areavoip supports extensions interface, adapting
  semantics to assign and remove names instead of adding
  and removing the extensions, a forbiden operation in the platform.
- Api CLI options `--date` and `--time` make fake pbx (`--fake`)
  to preload the queue at that moment acording to the timetables.
- Persons rule:
	- Fix: Persons information no more queried to the timetable
		but the persons module based on `persons.yaml`
	- Queue `pause`, `add` and derivatives are safely ignored
		when the person has no extension in persons.yaml
	- `persons.update()` to centralize info updating
- Refactorings to unify pbx backends interfaces
	- Operations in PBX backends dealing with timetibles
	  have been extracted out
	- `ScheduleStorage.queueScheduleFor` can provide
	  a queue for a given time
	- Api uses a wrapper which methods have an implicit default queue
- Cleaned some of the test warnings

## 3.7.0  2020-11-30

- PBX backend to use the Areavoip (Nubelphon) API
- PBX backends now use agent ids instead extensions
- scriptlauncher: Fix: failed to load because of colons in titles
- Added a nice favicon
- Few remaining Py3 fixes

## 3.6.5  2020-09-16

- Fix: shiftload stalled when compensation don't get a better credit
- Fix: scriptlauncher entry for `tomatic_says` failed
- Cron warn each operator by hangouts individually on new turn
- Experimental API /api/persons/extension/<extension> to get the email for a given extension
- Documentation:
	- How to upgrade

## 3.6.4  2020-06-04

- Documentation:
    - How to setup drive data sources
    - How to setup Hangouts notifications
- Dependency fixes for old Python2
- `tomatic_says.py`:
    - Migrated to `async/await` syntax (unsupported by python 3.4 and earlier)
    - README indicates how to setup: authentication, token files...
    - new option `-t,--tokenfile` to change the default token file (implies changing sender)
    - new option `-c,--channel` to change the default target of the message (config.yaml/hangoutsChannel)
    - Addressing a conversation by full name or hangouts id (base64 code)
    - Addressing a person by tomatic id, email, full hangouts name, or hangouts `gaia_id` (21 digits)
    - When target is not found a list of available targets is displayed

## 3.6.3  2020-06-03

- Penalties info is included in html timetable uploaded to the tomatic-static website
- Penalties info is included in html timetable shown in the planner execution result
- Busy reasons are displayed in planner when hovering over the blocking time slot

## 3.6.2  2020-06-01

- api: `--ring` option to enable incoming call notifications
- `tomatic_busy.py`
	- explains the reasons why people is busy each time
	- takes persons from ponderatedIdeal
	- scriptlauncher item to call it

## 3.6.1  2020-05-18

- Auto-backup timetables on edit and upload
- Fix: planner upload does it locally instead of calling manual upload api
- Cron setup documented
- `tomatic_says.py` Target channel configured in config.yaml
- Callinfo: Fix: downloading complaint reason freezed flask
  threads while downloading info from drive. Tomatic load should be faster.

## 3.6.0  2020-05-11

- Web frontend to launch and monitor sandboxed schedulers /api/planner

## 3.5.1  2020-04-29

- FIX: Health leaves had no effect in capacity
- Entry point and script launcher to retire old timetables

## 3.5.0  2020-03-20

- New functionality to keep track of shift credit across weeks
- Day-off retrieval from notoi API
	- Relates by emails
	- Removed config params that shoud be constants
	- Extracted Notoi proxy class
- New script: `tomatic_uploadtimetable.py`
- API: download shiftload and overload from last
	`tomatic_shiftload.py` execution for the week
	- /api/shifts/download/shiftload/<week>
	- /api/shifts/download/overload/<week>

## 3.4.0  2020-03-09

- New script: `tomatic_shiftload.py` to automate weekly load generation
- New script: `tomatic_mergedicts.py` to perform person by person manipulations
	in person->value yaml dicts (add, substract, extract 
- script `scheduler.py` renamed as `tomatic_schedule.py`
- Scheduler: `--lines` option to indicate the number of lines
- Scheduler: `--personsfile` option to indicate the persons file
- Scheduler: Holidays are automatically removed from search days
- Scheduler: Fix: people without table (ningu) is in table -1 (None)

## 3.3.1  2020-02-24

- Fixes on persons.yaml split
- Travis compilation

## 3.3.0  2020-02-24

- Py3 compatibility
- Scheduler: algorithm modifications to indiscriminate lines
- Persons information is splitted out of the config.yaml file into persons.yaml
- Scheduler: busy files and person info are downloaded from tomatic api
- Scheduler: B2B tested, required stop conditions and deterministic execution

## 3.1.0  2019-10-18

- Callinfo: ability to fill claims

## 3.0.0  2019-07-24

- Call info
- User identification
- Must identify before edit schedule

## 2.1.0  2018-02-07

- First tagged release 


