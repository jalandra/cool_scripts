#!/bin/bash

#usage:
#"./logging_task Executable

#check for the arguments
if [ $# -lt 1 ]
then
    echo "Please provide the executable name"
    exit 1
fi

#get the file name
file_name=$1

#check if file exists
if [ ! -x $file_name ]
then
    echo "File doesn't exists or it is not executable $file_name"
    exit 1
else
    #start gdb & check if it is debug version with the regular expression
    #2>&1 redirects standard error (2) to standard output (1), which then discards it as well since standard output has already been redirected.
    gdb -ex 'quit' $file_name 2>&1 | grep --regexp='(no\ debugging\ symbols\ found)' 2>&1> /dev/null

    #check the exit status of the last command executed.
    if [ $? -eq 0 ]
    then
        echo "binary executable not compiled with debugging mode, use -g during compilation."
        exit 1;
    fi
fi

echo "binary is fine"

# Make the temp files
TRACE="`mktemp -t $file_name.XXXXXXXXXX`" || exit
GETFUNCS="`mktemp -t $file_name.XXXXXXXXXX`" || exit

#The exit command that follows the rm is necessary because without it
#the execution would continue in the program at the point that it left off when the signal was received.
trap 'rm -f -- "$TRACE" "$GETFUNCS"' EXIT
trap 'trap - EXIT; rm -f -- "$TRACE" "$GETFUNCS"; exit 1' HUP INT QUIT TERM

# Take control of GDB and print call graph.
cat > $GETFUNCS <<EOF
set height 0
info function
EOF

gdb -batch -command=$GETFUNCS $file_name 2>/dev/null | awk '
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
    isCppFile = 0;
    isMoonRaceFile = 0;
    print "set width 0";
    print "set height 0";
    print "set verbose off";
}

/[a-zA-Z0-9_]+\.cpp:/ {
    isCppFile = 1;
    
    if(match($0, /AuditMenuBackend.cpp/) != 0){
        isMoonRaceFile = 1;
    }
    else
        isMoonRaceFile = 0;
}

/[a-zA-Z0-9_]+\.c:/ {
    isCppFile = 0;
}

/[a-zA-Z_][a-zA-Z0-9_]*\(/ {
    if(isMoonRaceFile) {
        fn = getFunctionName($0);
        badName = match(fn, /[~>][::]*/)
        if(badName == 0){
            if(isCppFile){
                position = match($0, /::/)
                if(position){
                    printf("b %s\n", fn);
                    ++total;
                }
            }
            else{
                printf("b %s\n", fn);
                ++total;
            }
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

    print "run"
}
' > $TRACE

#for Debugging, print the TRACE contents
cat $TRACE

# output in trace file is as below for main->foo->bar->baz
#set width 0
#set height 0
#set verbose off
#b main
#b bar
#b baz
#b foo
#command 1
#bt 2
#c
#end
#command 2
#bt 2
#c
#end
#command 3
#bt 2
#c
#end
#command 4
#bt 2
#c
#end
#run


gdb -batch -command=$TRACE -tty=/dev/null -args $file_name $@ 2>/dev/null | awk '
function getCalleeFunctionName(string)
{
    split(string, splittedStrings, ","); #result: foo (n=23) at test.c:19
    split(splittedStrings[2], functionName, " "); #result: foo | (n=23) | at | test.c:19
    #print("function name is %s \n", functionName[1]) #prints 0x08048471
    return functionName[1]; #result: foo
}

function getParameters(string, n)
{
    #printf("string is %s \n", string)
    split(string, splittedStrings, n);
    #printf("splittedStrings[2] is %s \n", splittedStrings[2]) #returns in foo (), in main ()
    split(splittedStrings[2], splittedStrings, " at ");
    #printf("string is %s \n", splittedStrings[1])
    sub(/ \(/, "(", splittedStrings[1]);
    #printf("substitute string is: %s \n", splittedStrings[1])
    return splittedStrings[1];
}

BEGIN {
    isFunctionCall = 0;
    callee = "";
    caller = "Start";
    params = "";
}

/^Breakpoint [0-9]+,/ {
    isFunctionCall = 1;
    callee = getCalleeFunctionName($0);
    params = getParameters($0, callee); # gets "in foo()"
}

#check the starting of the line
/^#1[ \t]+/ {
    if (isFunctionCall){
        caller = $4;
        printf("%s calling -> %s with arguments %s\n", caller, callee, params);
        callee = caller = params = "";
    }
}
END {
}
'
echo "The End, Hope you enjoyed it"