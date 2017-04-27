# somenergia-phonetimetable

Repartidor d'hores d'atenció telefònica


## Install


```bash
sudo apt-get install gcc libpython2.7-dev libffi-dev libssl-dev nodejs-legacy npm
python setup develop
npm install
npm run build # for development assets
npm run deploy # for production assets
```

See below "deployment notes" on how deploy the required certificate.

## Usage

### Scheduler

To compute the timetable for the next week:

```bash
$ ./schedulehours.py
```

To skip the downloading of the data from google drive:

```bash
$ ./schedulehours.py --keep
```

See bellow how to grant access to the script.

### Web and API

To run the fake version to develop:

```bash
$ ./tomatic_api.py --debug --fake
```

To run the version acting on asterisk:

```bash
$ ./tomatic_api.py
```

Use `--help` to see other options.


### Direct asterisk rtqueue control

To load the current queue acording to the schedule

```bash
$ ./tomatic_rtqueue.py set -d 2018-12-26 -t 10:23
```


## Deployment notes

In order to access the configuration available in the Google Drive SpreadSheet
you must provide a 

- Create a Google Apps credential:
    - Create a project in https://console.developers.google.com/project
    - Go to “Credentials” and hit “Create new Client ID”.
    - Select “Service account”. Hitting “Create Client ID” will generate a new
      Public/Private key pair.
    - Download and save it as 'credential.json' in the same folder the script is
    - Take the `client_email` key in the json file and grant it access to the
      'Vacances' file as it was a google user

If you don't want to download the configuration data from the Google Drive
SpreadSheet, you can provide the `--keep` option.


## Certificates

Unless you specify the `--keep` option, required configuration data is
downloaded from the Google Drive spreadsheet where phone load, holidays and
availability are written down.

In order to access it you will require a oauth2 certificate and to grant it
access to the Document.

Follow instructions in http://gspread.readthedocs.org/en/latest/oauth2.html

You can skip steps 5 (already in installation section in this document) and
step 6 (code related) but **don't skip step 7**.

Create a link named 'certificate.json' pointing to the actual certificate.





























