HOW TO RUN THE ALGORITHM ON YOUR LOCAL MACHINE

Step 1: Dowload the files and ensure that the 4 pyhton files are located in the same directory
Step 2: Create an Oanda account and generate a private API Key and new account (paper account) for trading
Step 3: Edit scheduled_job.py
    3a: /scheduled_job.py line 25: input your account id
    3b: /scheduled_job.py line 26: input your private API key
    3c: /scheduled_job.py: edit line 15-27 with whatever metrics you want
Step 4: Edit run_me.py
    4a: the program automatically runs every 5 minutes, if you want to run it with a different invterval, edit line 12, minute ="*/5"
Step 5: Download and install these python libraries: Pandas, Numpy, Pytz, matplotlib, TA-Lib, stocktrends, oandapyV20, oanda_candles, apscheduler & Enum
    Note: to install TA-Lib you need python version that works with the TA-Lib library. (python 3.10 as of 14 November 2023)
    To change python environment, use conda
    helpful link: https://anaconda.org/conda-forge/ta-lib
    another link: https://openai.com/blog/chatgpt
Step 6: Once all the libraries are installed, you can run the bot.
Step 7: Run run_me.py on your IDE
note: algorithm will terminate once the IDE is closed or if terminal/command prompt is closed.



HOW TO RUN THE ALGORITHM ON A SERVER:
1: works the exact same. Download the packages on the server and run the file in the background
2: establish connection with a server on your local machine terminal/command prompt. (example: aws server)
3: download the python packages
4: transfer the files over to the server (example: filezila ssh file transfer protocol)
5: go to the directory of the 4 python files
6: run "run_me.py" on the server in the background and record the output (example syntax: nohup python3 run_me.py)
7: check if the algorithm is running using "ps x" command
8. kill algorithm using "kill -9 __<PID>___"

