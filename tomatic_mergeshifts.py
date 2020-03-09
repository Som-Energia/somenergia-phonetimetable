#!/usr/bin/env python

import sys
from tomatic.shiftload import loadSum, loadMin, loadSubstract
from yamlns import namespace as ns

def main():
    nonzero = 'nonzero' in sys.argv
    if nonzero: sys.argv.remove('nonzero')

    if sys.argv[1] == 'min':
        result = loadMin(*(
            ns.load(filename)
            for filename in sys.argv[2:]
        ))
    elif sys.argv[1] == 'subs':
        result = loadSubstract(*(
            ns.load(filename)
            for filename in sys.argv[2:4]
        ))
    elif sys.argv[1] == "timetable":
        from collections import Counter
        timetable = ns.load(sys.argv[2])
        result = ns(sorted((p,v) for p,v in Counter(
            shift
            for day in timetable.timetable.values()
            for turn in day
            for shift in turn
        ).items()))
    else:
        result = loadSum(*(
            ns.load(filename)
            for filename in sys.argv[1:]
        ))

    result = ns(
        (p,round(v,1) if type(v) is float else v)
        for p,v in sorted(result.items())
        if not nonzero or v
    )
    print(result.dump())

if __name__ == "__main__":
    main()

# vim: et ts=4 sw=4
