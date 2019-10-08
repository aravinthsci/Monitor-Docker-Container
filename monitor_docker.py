import docker
from datetime import datetime
from elasticsearch import Elasticsearch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# requried dependencies
#pip install elasticsearch
#pip install docker

def send_mail(node_addr, hostname, image_name, image, action):
    print "inside mail"
    print node_addr + "===" + hostname + "===" + image_name + "===" + image + "===" + action
    fromaddr = "admin@localhost.com"
    toAddr = ["aravinth@outlook.in", "aravinth.raja@xyz.com"]
    toadr = ', '.join(str(e) for e in toAddr)
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toadr
    msg['Subject'] = "[AUTOMATED] Docker Monitor "
    html = "<html><body><ps tyle=\"font-size:160%;\">" \
           " <b>Node_Address:<\b>" + node_addr + \
           "<br> <b>Hostname:<\b>" + hostname +\
           "<br><b>Image Name:<\b>" + image_name + \
           "<br><b>Image:<\b>" + image + \
           " <br><b>Status: <\b>" +action+ \
           " </p></body></html>"
    part = MIMEText(html, 'html')
    msg.attach(part)
    server = smtplib.SMTP('smtp.office365.com', 587)
    server.starttls()
    server.login(fromaddr, "password")
    text = msg.as_string()
    server.sendmail(fromaddr, toAddr, text)
    server.quit()



# Push docker status to elastic search
def monitor_logs(client, es):
    node_addr = client.info().get('Swarm').get('NodeAddr')
    hostname = client.info().get('Name')
    for container in client.containers.list(all):
        container_obj = client.containers.get(container.id)
        print (container_obj.name + " ===> " + container_obj.status)
        es.index(index="docker_status_info", doc_type="status",
                 body={"timestamp": datetime.utcnow(),
                       "host_ip": node_addr,
                       "hostname": hostname,
                       "container_name": container_obj.name,
                       "container_status": container_obj.status,
                       "container_logs": container_obj.logs(tail=5)
                       }
                 )

def monitor(cli):
    node_addr = cli.info().get('Swarm').get('NodeAddr')
    hostname = cli.info().get('Name')
    events = cli.events(decode=True)
    for event in events:
        action = event.get('Action')
        image = event.get('Actor').get('Attributes').get('image')
        image_name = event.get('Actor').get('Attributes').get('name')
        print "action===>" + action
        if(action == "kill" or action == "die" or action == "stop"):
            send_mail(node_addr, hostname, image_name, image, action)


if __name__ == '__main__':
    client = docker.from_env()
    #Another Way of creating Docker Client
    #URL to the Docker server. For example, unix:///var/run/docker.sock or tcp://127.0.0.1:1234.
    #client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    es = Elasticsearch(['localhost'], port=9200,)
    es.indices.create(index='docker_status_info', ignore=400)
    monitor(client)
    monitor_logs(client, es)