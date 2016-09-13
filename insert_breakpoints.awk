#!/bin/awk -f
#var is the filename passed
function getFunctionName(str)
{
    split(str, part, "(");
    len = split(part[1], part, " ");
    len = split(part[len], part, "*");
    return part[len];
}

function getClassName(str)
{
    split(str, part, "{");
    len = split(part[1], part, " ");
    return part[len];
}

BEGIN {
    total = 0;
    isValidFile = 0;
}

/[a-zA-Z0-9_]+\.c/ {
    if(var == ""){
        isValidFile = 1;
    } else {
        temp = match($0, var)
        if(temp == 0){
            isValidFile = 0;
        } else{
            isValidFile = 1;
        }
    }
}

/symbols:/ {
    isValidFile = 0;
}

/[a-zA-Z_][a-zA-Z0-9_]*\(/ {
    if(isValidFile){
        fn = getFunctionName($0);
        badName = match(fn, /[~>][::]*/)
        if(badName == 0){
            printf("b %s\n", fn);
            ++total;
        }
    }
}
END {
    for (i = 1; i <= total; i++) {
        print "command", i;
            print "bt 2";
            print "c";
        print "end";
    }
    print "continue";
    print "shell ./create_map.awk harish >/dev/tty";
    print "continue";
}
