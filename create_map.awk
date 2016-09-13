#!/bin/awk -f

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
    printf("\n\t\t ***** HOLD ON!!!! PRINTING THE CALL GRAPH *****");
}

/^Breakpoint [0-9]+,/ {
    isFunctionCall = 1;
    callee = getCalleeFunctionName($0);
    params = getParameters($0, callee);
}

#check the starting of the line
/^#1[ \t]+/ {
    if (isFunctionCall){
        caller = $4;
        printf("\n%s calling ----> %s with arguments %s", caller, callee, params);
        callee = caller = params = "";
    }
}
END {
}
