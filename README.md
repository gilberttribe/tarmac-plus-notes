# tarmac-plus-notes
Python application to analyze and annotate tarmac files to improve debug efficiency

This Python application reads in a tarmac trace file and adds notes or annotations to
the tarmac file making analyzing the tarmac file simpler.  This application uses the
list file, source code files, and a list of critical variables and registers to add
notes such as the following:

    o Call tree
    o function prototypes with function entry and exit
    o Global variable and register accesses

A tarmac file is an assembly-level trace file produced during RTL simulation, which
shows a trace of the instructions executed and memory accessed by the processor
during execution of the fimrware in the ARM processor.  The following is an
example of a tarmac file:

      22225 ns IT 10000076 488e        LDR      r0,[pc,#568]  ; [0x100002b0]
      22425 ns MR4_D 100002b0 2001ec00
      22425 ns R r0 2001ec00
      22425 ns IT 10000078 2600        MOVS     r6,#0
      22525 ns MR4_I 1000007c 4a724971
      22525 ns R r6 00000000
      22525 ns IT 1000007a 6006        STR      r6,[r0,#0]
      22625 ns R psr 41000200

The following shows an example of the tarmac file with annotations:

    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    LOG_ILogWaypointValue entry (2000afc0) 
    C:\\prod\\tags\\Project_06.07.09.02\\Source\\Log\\Log_Handlers.c
    void LOG_ILogWaypointValue( uint32 logVal )
        Project_AppMain -> Project_AppExecute -> Project_ILogWriteDebugString -> Project_ILogWriteDebugvalue -> LOG_ILogWaypointValue

    454166925 ns IT 2000afc0 b510        PUSH     {r4,lr}
    454167025 ns MR4_I 2000afc4 49076008
    454167125 ns MW4_D 2001fe48 40240000
    454167225 ns MW4_D 2001fe4c 2000a241
    454167225 ns R r13 2001fe48 (MSP)
    ...
    454167825 ns MW4_D 40240a5c 33000609                        ; REGISTER_Waypoint <= 33000609
    454167825 ns IT 2000afc6 4907        LDR      r1,[pc,#28]  ; [0x2000afe4]
    454168025 ns MR4_D 2000afe4 2001ec00
    454168025 ns R r1 2001ec00
    454168025 ns IT 2000afc8 680a        LDR      r2,[r1,#0]
    454168125 ns MR4_I 2000afcc 50e04c06
    454168225 ns MR4_D 2001ec00 00000072                        ; ADDRESS_Glb_LogCounter => 00000072
    454168225 ns R r2 00000072

Set the variableDictionary and default path strings prior to executing this Python
application.  See the argumentParser for a list of available parameters. 
