import json
import subprocess

import docker


client = docker.APIClient(base_url='unix://var/run/docker.sock')


def update_firewall():
    rules = [
        '*filter',
        ':DOCKER-AUTOFIREWALL - [0:0]',
        '-F DOCKER-AUTOFIREWALL',
    ]

    for container in client.containers():
        config = client.inspect_container(container['Id'])

        host_network = 'host' in config['NetworkSettings']['Networks']
        if host_network:
            if 'Config' not in config:
                continue
            if 'ExposedPorts' not in config['Config']:
                continue
            for port in config['Config']['ExposedPorts'].keys():
                port, prot = port.split('/')
                rules.append(f'-A DOCKER-AUTOFIREWALL -m state --state NEW -m {prot} -p {prot} --dport {port} -j ACCEPT')
        else:
            for port, port_config in config['NetworkSettings']['Ports'].items():
                port, prot = port.split('/')
                for share in port_config:
                    host_port = share['HostPort']
                    rules.append(f'-A DOCKER-AUTOFIREWALL -m state --state NEW -m {prot} -p {prot} --dport {host_port} -j ACCEPT')

    rules.append('COMMIT\n')


    iptables_conf = '\n'.join(rules)
    print(iptables_conf)

    p = subprocess.run(['iptables-restore', '-n'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, input=iptables_conf, encoding='ascii')
    print(p.stdout)
    print(p.returncode)


def main():
    print(client.version())

    print("Monitor started; building new firewall rules")
    update_firewall()

    for event in client.events():
        event = json.loads(event.decode('utf-8'))
        if event['Type'] != 'container':
            continue
        if event['Action'] not in ['create', 'start', 'die']:
            continue

        print("Change detected; building new firewall rules")
        update_firewall()


if __name__ == '__main__':
    main()
