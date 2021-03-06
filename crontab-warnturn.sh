#!/bin/bash
# To setup those task you should:
#    sudo chown root:root crontab
#    sudo chmod 755 crontab

turn=$(tomatic_rtqueue.py preview --time $(date -d '10 minutes' +'%H:%M') )

./tomatic_says.sh "Canvi de torn en 5m: $turn"
./tomatic_says.sh "Recordeu anotar les trucades: https://intranet.helpscoutdocs.com/article/749-formulari-telefon-inquietuds-clients"

for person in $turn
do
	./tomatic_says.sh -c ${person/,/} "Hola super, tens torn de telefon en 5 minuts!"
done

