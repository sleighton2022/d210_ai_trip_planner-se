### Local Testing

in bash call "./run_backend.sh & ./run_frontend.sh" in order to run backend and frontend files
backend shell file is set to run uvicorn to run the backend w/ debugging information
see shell output for any errors 

run command "pkill -f "uvicorn" to end backend running process. 

Main errors encountered:
* 422 Error, request json not formatted correctly (most likely due to formatting in Model)
* Double check model inputs from json request
    *  above out of date