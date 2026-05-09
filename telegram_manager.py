import subprocess
import sys
import time

def main():
    print("==================================================")
    print("                 BOT STARTED                      ")
    print("==================================================")
    
    # Just run the job_apply.py script
    print(">> Launching Job Application Bot...")
    subprocess.call([sys.executable, "job_apply.py"])
    
    print(">> Bot Execution Finished.")
    time.sleep(5)

if __name__ == "__main__":
    main()