












#apikey = configFile['api_key']
#base_url = configFile['base_url']
#config_keytype = configFile['keytype']
#headers = {
#   'Authorization': f'Bearer {apikey}',
#    'Accept': 'application/json',
#    'Content-Type': 'application/json'
#}
#payload = 0

def panelGET(path):
    url = f'{base_url}{path}'
    global response
    response = requests.request('GET', url, headers=headers).json()

def panelDELETE(path):
    url = f'{base_url}{path}'
    global response
    response = requests.request('DELETE', url, headers=headers)

def panelPOST(path, payload):
    url = f'{base_url}{path}'
    global response
    response = requests.request('POST', url, data=payload, headers=headers)

@app.command()
def setup(reset: bool = typer.Option(False, help="overwrites config")):
    if os.path.exists(configDir) == False:
        os.mkdir(configDir, mode = 0o750)
    else:
        typer.echo('Directory Already Exists, Continuing...')
    if os.path.isfile(configFilePath) == False or reset:
        if reset:
            typer.secho('Reset specified, overwriting config file. CTRL+C to cancel', bold=True, bg=typer.colors.RED)
            existingConfig = json.load(open(configFilePath, 'r'))
            typer.secho(f'Existing URL: {existingConfig["base_url"]}', bold=True)
            typer.secho(f'Existing API Key: {existingConfig["api_key"]}', bold=True)
        typer.echo('Input Pterodactyl URL. URL must have a `/` at the end.')
        urlConfig = typer.prompt('URL')
        typer.echo('Input API Key, currently support API functions are api/client')
        apikeyConfig = typer.prompt('API Key')
        typer.echo('Input API Key type: client or application')
        apikeyType = typer.prompt('API Key Type')
        aliveCheck = alive(urlConfig, apikeyConfig, apikeyType, '--output')
        if aliveCheck == 200:
            typer.echo('Alive Check Successful')
            typer.echo('Creating Config File')
            configDataDict = {
                'client_key': {
                    'base_url': f'{urlConfig}',
                    'api_key': f'{apikeyConfig}'
                },
                'application_key': {
                    'base_url': f'{urlConfig}',
                    'api_key': f'{apikeyConfig}'
                }
            }
            configData = json.dumps(configDataDict, indent=1)
            #open(configFilePath, 'x+').write(configData)
            #os.chmod(configFilePath, 0o600)
            typer.echo('Configuration Complete')
        else:
            typer.echo(f'Alive Check Failed.\n Use `wyvern alive {urlConfig} {apikeyConfig} {keytype}` to get more information.')
    else:
        typer.echo('Config File Exists, Aborting Setup')

@app.command()
def alive(address: str, key: str, keytype: str = typer.Argument('client'), output: bool = typer.Option(True)):
    headers = {
    'Authorization': f'Bearer {key}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
    }
    if keytype == 'client':
        response = requests.request('GET', f'{address}api/client', headers=headers).status_code
    elif keytype == 'application':
        response = requests.request('GET', f'{address}api/application/servers', headers=headers).status_code
    if output == True:
        typer.echo(response)
        if response == 200:
            typer.echo("It's Alive")
        elif response == 403:
            typer.echo('Forbiden')
        else:
            typer.echo('Error')
    else:
        return response

@server_app.command()
def power_status(identifier: str, output: bool = typer.Option(True)):
    panelGET(f'api/client/servers/{identifier}/resources')
    if output == True:
        print("Current State:", response['attributes']['current_state'])
    elif output == False:
        return response['attributes']['current_state']

@server_app.command()
def status(identifier: str):
    panelGET(f'api/client/servers/{identifier}')
    print(response['attributes']['name'], ':::' ,response['attributes']['node'])
    print('')
    panelGET(f'api/client/servers/{identifier}/resources')
    print("Current State:", response['attributes']['current_state'])
    print("CPU Usage:", round(response['attributes']['resources']['cpu_absolute'], 2), "%")
    mem_used_bytes = float(response['attributes']['resources']['memory_bytes'])
    print("Memory Usage:", round(mem_used_bytes * 0.000001, 2),"MB")
    disk_used_bytes = float(response['attributes']['resources']['disk_bytes'])
    print("Storage Usage:", round(disk_used_bytes * 0.000001, 2),"MB")
    net_rx_bytes = float(response['attributes']['resources']['network_rx_bytes'])
    net_tx_bytes = float(response['attributes']['resources']['network_tx_bytes'])
    print("Network Upload:", round(net_tx_bytes * 0.008, 2), "kbps")
    print("Network Download:", round(net_rx_bytes * 0.008, 2), "kbps")
    #print(json.dumps(response, indent=1))

@server_app.command()
def list():
    panelGET('api/client')
    print("### Server List ###")
    for item in response['data']:
        ident = item['attributes']['identifier']
        name = item['attributes']['name']
        ps = power_status(ident, False)
        print(ident, "###",  name, ":", ps)

@server_app.command()
def info(identifier: str):
    panelGET(f'api/client/servers/{identifier}/resources')
    print(json.dumps(response, indent=1))
    panelGET(f'api/client/servers/{identifier}')
    print(json.dumps(response, indent=1))

@server_app.command()
def start(identifier: str):
    panelPOST(f'api/client/servers/{identifier}/power', '{"signal": "start"}')
    print(response)
    power_status(f'{identifier}')

@server_app.command()
def stop(identifier: str):
    panelPOST(f'api/client/servers/{identifier}/power', '{"signal": "stop"}')
    print(response)
    power_status(f'{identifier}')

@server_app.command()
def backup(identifier: str, action: str, uuid: str = typer.Argument(None)):
    panelGET(f'api/client/servers/{identifier}/backups')

    if action == 'list':
        print(f'### Listing Backups for {identifier} ###')
        for item in response['data']:
            print(item['attributes']['uuid'], ":::", item['attributes']['name'])

    if action == 'info':
        if uuid == 'None':
            print('Please Enter Backup UUID')
        else:
            panelGET(f'api/client/servers/{identifier}/backups/{uuid}')
            print(json.dumps(response, indent=1))

    if action == 'delete':
        protect = input("Are you sure? ::: Y/n\n")
        if protect == 'Y':
            panelDELETE(f'api/client/servers/{identifier}/backups/{uuid}')
            if response.status_code == 204:
                print('Success')
            else:
                print('Error')
                print(response.status_code)
        else:
            print("Deletion Aborted")

    if action == 'create':
        panelPOST(f'api/client/servers/{identifier}/backups', 0)
        if response.status_code == 429:
            print('Error 429: Too Many Requests, Backup creation rate limited')
        else:
            print(response.json()['attributes']['name'])