import json
import sys
import os
import typer
import requests

app = typer.Typer()
server_app = typer.Typer()
app.add_typer(server_app, name="server")

configDir = os.path.expanduser('~') + '/.config/wyvern-cli/'
configFilePath = configDir + 'config.json'
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
if admin:
    print('admin powers activated')
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
payload = 0

def panelGET(type: str, path: str):
    if type == 'client':
        api_key = client_key
        apiPath = 'api/client'
    elif type == 'applic':
        api_key = application_key
        apiPath = 'api/application'
    headers['Authorization'] = f'Bearer {api_key}'
    return requests.get(f'{base_url}{apiPath}{path}', headers=headers)

@app.command()
def get_default_key():
    print(json.dumps(keyData, indent=1))

@app.command()
def key_test():
    if key_type == 'admin':
        path = 'api/application'
    elif key_type == 'client':
        path = 'api/client'
    data = requests.request('GET', f'{base_url}{path}', headers=headers).status_code
    if data == 200:
        typer.secho('Success', fg=typer.colors.GREEN)
    else:
        typer.secho('Error', bg=typer.colors.RED)
        typer.echo(data)

@server_app.command()
def list():
    if admin:
        data1 = panelGET('applic', '/servers')
    else:
        data1 = panelGET('client', '')
    print("### Server List ###")
    x = 0
    for item in data1.json()['data']:
        ident = item['attributes']['identifier']
        name = item['attributes']['name']
        data2 = panelGET('client', f'/servers/{ident}/resources').json()
        ps = data2['attributes']['current_state']
        print(ident, "#",  name, ':', ps)
        x += 1
    typer.echo(f'Showing {x} servers')

def power_status():
    return response['attributes']['current_state']

@app.command()
def api_test(path: str):
    data = panelGET(path)
    typer.echo(json.dumps(data.json(), indent=1))