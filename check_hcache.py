import re
import requests
import subprocess
import commands
import sys

from time import localtime, strftime

#dev
#goroutine_url = 'http://m8.c8.net.ua:13403/debug/pprof/'
#resp_url = 'http://m8.c8.net.ua:89/get?uid=23412'

#prod
goroutine_url = 'http://localhost:13403/debug/pprof/'
resp_url = 'http://localhost:89/get?uid=23412'
goroutine_max = 100


def log(string):
    dt = strftime("[%d-%m-%Y %H:%M:%S] ", localtime())
    with open("/var/log/gohcache.log", "a") as myfile:
        myfile.write(dt + string + "\r\n")
    pass


def restart_hcache(reason):
    #check status
    log('Check status & restart hcache')
    out = commands.getoutput('/bin/ps -A')
    if ('hcache' in out):
        log(reason + ", restarting hcache...")
        proc = subprocess.Popen(['/sbin/restart hcache'], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        print(err)
        log(str(out))
    else:
        log(reason + ", not running, starting hcache...")
        proc = subprocess.Popen(["/sbin/start hcache"], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        print(err)
        log(str(out))

    # check status again
    out = commands.getoutput('/bin/ps -A')
    if ('hcache' in out):
        log('Running')
    else:
        log("Can't start service, panic!")
        # send mail here

    log('=================== Finish ===================')
    sys.exit(1)
    pass


def check_response():
    print("Check response...")
    try:
        response = requests.get(resp_url, timeout=(5, 5))
        response.raise_for_status()

    except requests.exceptions.ReadTimeout:
        print('Oops. Read timeout occured')
        restart_hcache('Read timeout')
    except requests.exceptions.ConnectTimeout:
        print('Oops. Connection timeout occured!')
        restart_hcache('Connection timeout')
    except requests.exceptions.ConnectionError:
        print('Seems like dns lookup failed..')
        restart_hcache('ConnectionError')
    except requests.exceptions.HTTPError as err:
        print('Oops. HTTP Error occured')
        print('Response is: {content}'.format(content=err.response.content))

    print("Response status code: " + str(response.status_code))

    text = response.text
    print("Response text: " + text)
    dmp = re.search('dmp', text)
    print("Match dmp: " + str(dmp))

    return dmp


def check_goroutine():
    print("Check goroutine...")
    try:
        response = requests.get(goroutine_url, timeout=(5, 5))
        response.raise_for_status()

    except requests.exceptions.ReadTimeout:
        print('Oops. Read timeout occured')
        restart_hcache('Read timeout')
    except requests.exceptions.ConnectTimeout:
        print('Oops. Connection timeout occured!')
        restart_hcache('Connection timeout')
    except requests.exceptions.ConnectionError:
        print('Seems like dns lookup failed..')
        restart_hcache('ConnectionError')
    except requests.exceptions.HTTPError as err:
        print('Oops. HTTP Error occured')
        print('Response is: {content}'.format(content=err.response.content))

    print("Response status code: " + str(response.status_code))
    text = response.text
#   print(text)
#   lines = text.split("\n")
#   line = lines[0]
#   print(lines[0])
    goroutine = re.search('(\d+).*(goroutine)', text)
    goroutine_cnt = goroutine.group(1)

    print('-' + goroutine_cnt + '-')

    return goroutine_cnt


log('=================== Starting ===================')
log('Check response & dmp data')

dmp_data = check_response()

if dmp_data:
    log('Found dmp data')
else:
    restart_hcache('dmp data not found')

log('Check goroutine')
grt_cnt = check_goroutine()
log('Goroutine count: ' + grt_cnt)

if int(grt_cnt) > goroutine_max:
    restart_hcache('Goroutine too much')

else:
    log('ok')

log('=================== Finish ===================')


