import json
import sys
import os
import typer
import requests

app = typer.Typer()
server_app = typer.Typer()
app.add_typer(server_app, name="server")
backup_app = typer.Typer()
app.add_typer(backup_app, name="backup")

configDir = os.path.expanduser('~') + '/.config/wyvern-cli/'
configFilePath = configDir + 'config.json'
try:
    configFile = json.load(open(configFilePath))

    for item in configFile['keys']:
            if item['account_id'] == configFile['default_account']:
                keyData = item
                break

    client_key = keyData['client_key']
    application_key = keyData['application_key']
    base_url = keyData['base_url']
    if keyData['account_type'] == 'admin':
        admin = True
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    payload = 0
except:
    typer.secho("Config File doesn't exist or isn't configured. run 'wyvern config' to create file", bold=True, bg=typer.colors.RED)

def panelGET(type: str, path: str):
    if type == 'client':
        api_key = client_key
        apiPath = 'api/client'
    elif type == 'applic':
        api_key = application_key
        apiPath = 'api/application'
    headers['Authorization'] = f'Bearer {api_key}'
    return requests.get(f'{base_url}{apiPath}{path}', headers=headers)

def panelPOST(type: str, path: str, data):
    if type == 'client':
        api_key = client_key
        apiPath = 'api/client'
    elif type == 'applic':
        api_key = application_key
        apiPath = 'api/application'
    headers['Authorization'] = f'Bearer {api_key}'
    return requests.post(f'{base_url}{apiPath}{path}', headers=headers, data=data)

def panelDELETE(type: str, path: str):
    if type == 'client':
        api_key = client_key
        apiPath = 'api/client'
    elif type == 'applic':
        api_key = application_key
        apiPath = 'api/application'
    headers['Authorization'] = f'Bearer {api_key}'
    return requests.delete(f'{base_url}{apiPath}{path}', headers=headers)

@app.command()
def config():
    defaultConfig = { "default_account": "", "keys": [{"account_id": "1", "account_type": "admin", "base_url": "", "client_key": "", "application_key": ""},{"account_id": "2", "account_type": "user", "base_url": "", "client_key": ""}]}
    if os.path.isfile(configFilePath) == False:
        open(configFilePath, 'w').write(json.dumps(defaultConfig, indent=1))
        typer.echo('Default Config written to ~/.config/wyvern-cli/config.json\n Please Edit and change to your needs.')
    else:
        typer.echo('Config File Exists')

@app.command()
def key_test():
    dataClient = panelGET('client', '')
    typer.secho('Testing Client API Key', bold=True)
    if dataClient.status_code == 200:
        typer.secho('Success', fg=typer.colors.GREEN)
    else:
        typer.secho('Error', bg=typer.colors.RED)
        typer.echo(data)
    if admin:
        dataApplic = panelGET('applic', '/servers')
        typer.secho('Testing Application API Key', bold=True)
        if dataApplic.status_code == 200:
            typer.secho('Success', fg=typer.colors.GREEN)
        else:
            typer.secho('Error', bg=typer.colors.RED)
            typer.echo(data)

@app.command()
def api_test(type: str, path: str = typer.Argument('')):
    data = panelGET(type, path)
    typer.echo(json.dumps(data.json(), indent=1))

@server_app.command()
def list(status: bool = typer.Option(False)):
    if admin:
        data1 = panelGET('applic', '/servers')
    else:
        data1 = panelGET('client', '')
    print("### Server List ###")
    x = 0
    for item in data1.json()['data']:
        ident = item['attributes']['identifier']
        name = item['attributes']['name']
        if status:
            data2 = panelGET('client', f'/servers/{ident}/resources').json()
            ps = data2['attributes']['current_state']
            typer.echo(f"{ident} # {name}:{ps}")
        else:
            typer.echo(f"{ident} # {name}")
        x += 1
    typer.echo(f'Showing {x} servers')

@server_app.command()
def status(name: str):
    identifier = search(name)
    data1 = panelGET('client', f'/servers/{identifier}').json()
    name = data1['attributes']['name']
    node = data1['attributes']['node']
    typer.secho(f'{name}@{node}', bold=True)
    print('')
    typer.echo(f'Server Id: {identifier}')
    response = panelGET('client', f'/servers/{identifier}/resources').json()
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
def search(name: str, print: bool = typer.Option(False, help="Display output. Otherwise is silent.")):
    if admin:
        data = panelGET('applic', '/servers').json()
    else:
        data = panelGET('client', '').json()
    for item in data['data']:
        if item['attributes']['name'] == name:
            if print == True:
                typer.echo(item['attributes']['identifier'])
            return item['attributes']['identifier']

def power_status(identifier: str):
    data = panelGET('client', f'/servers/{identifier}/resources').json()
    return data['attributes']['current_state']

def power_action(identifier: str, action: str):
    if action == 'start':
        actionData = '{"signal": "start"}'
    elif action == 'stop':
        actionData = '{"signal": "stop"}'
    elif action == 'restart':
        actionData = '{"signal": "restart"}'
    elif action == 'kill':
        actionData = '{"signal": "stop"}'
    else:
        return 'error invalid action'
    data = panelPOST('client', f'/servers/{identifier}/power', actionData).status_code
    if data == 204:
        return f'{action}ing server'
    elif data == 404:
        return 'server not found, check your spelling and capitalization'
    else:
        return f'error {data}'

@server_app.command()
def start(name: str):
    identifier = search(name)
    data = power_action(identifier, 'start')
    typer.echo(data)

@server_app.command()
def stop(name: str):
    identifier = search(name)
    data = power_action(identifier, 'stop')
    typer.echo(data)

@server_app.command()
def restart(name: str):
    identifier = search(name)
    data = power_action(identifier, 'restart')
    typer.echo(data)

@server_app.command()
def kill(name: str):
    identifier = search(name)
    data = power_action(identifier, 'kill')
    typer.echo(data)

@server_app.command()
def console():
    identifier = 'fce8d9d1'
    data1 = panelGET('client', f'/servers/{identifier}/websocket').json()
    token = data1['data']['token']
    socket = data1['data']['socket']
    typer.echo(token)
    typer.echo(socket)

@backup_app.command()
def info(name: str, uuid: str = typer.Argument('None', help="if given, will show details for specified backup")):
    identifier = search(name)
    if uuid == 'None':
        response = panelGET('client', f'/servers/{identifier}/backups')
        typer.secho(f'### Listing Backups for {name} ###', bold=True)
        for item in response.json()['data']:
            bName = item['attributes']['name']
            bUuid = item['attributes']['uuid']
            typer.echo(f"{bUuid} # {bName}")
    else:
        response = panelGET('client', f'/servers/{identifier}/backups/{uuid}').json()
        typer.echo(json.dumps(response, indent=1))

@backup_app.command()
def create(name: str):
    identifier = search(name)
    response = panelPOST('client', f'/servers/{identifier}/backups', 0).status_code
    if response == 200:
        typer.echo(f'Success {response}')
    else:
        typer.echo(f'Error {response}')

@backup_app.command()
def delete(name: str, uuid: str):
    identifier = search(name)
    bName = panelGET('client', f'/servers/{identifier}/backups/{uuid}').json()['attributes']['name']
    protect = typer.confirm(f"Are you sure you want to delete {bName}")
    if protect:
        response = panelDELETE('client', f'/servers/{identifier}/backups/{uuid}')
        if response.status_code == 204:
            print('Success')
        else:
            print('Error')
            print(response.status_code)
    else:
        print("Deletion Aborted")