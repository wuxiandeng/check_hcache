import re
import requests
import subprocess
import sys

from time import gmtime, strftime

goroutine_url = 'http://localhost:13403/debug/pprof/goroutine?debug=1'
resp_url = 'http://localhost:89/get?uid=23412'
goroutine_max = 100


def log(string):
    dt = strftime("[%d-%m-%Y %H:%M:%S] ", gmtime())
    with open("/var/log/gohcache.log", "a") as myfile:
        myfile.write(dt + string + "\n\r")
    pass


def restart_hcache(reason):
    log(reason + " restarting hcache...")
    proc = subprocess.Popen(["/sbin/restart hcache"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    print(err)
    log(str(out))
    sys.exit(1)
    pass


def check_response():
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

    print(response)
    print(response.status_code)
    print(response.headers['content-type'])
    text = response.text
    print(text)
    dmp = re.search('dmp', text)
    print(dmp)

    return dmp


def check_goroutine():
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

    print(response)
    print(response.status_code)

    print(response.headers['content-type'])
    text = response.text

    lines = text.split("\n")
    line = lines[0]
    print(lines[0])
    goroutine = re.search('\d+', line)
    goroutine_cnt = goroutine.group(0)

    print(goroutine_cnt)

    return goroutine_cnt


log('Starting')
log('Check response & dmp data')

dmp_data = check_response()

if dmp_data:
    log('found dmp data')
else:
    restart_hcache('dmp data not found')

log('Check goroutine')
grt_cnt = check_goroutine()
log('Goroutine count: ' + grt_cnt)

if int(grt_cnt) > goroutine_max:
    restart_hcache('Goroutine too much')

else:
    log('ok')

log('=================== finish ===================')
