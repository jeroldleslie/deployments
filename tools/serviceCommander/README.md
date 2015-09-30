#Service Commander#
Use Ansible to manage services in your cluster!

##Usage##
```
Usage: serviceCommander.py [OPTIONS]

  Use Ansible to manage services in your cluster!

Options:
  --debug / --no-debug       Turn debugging on
  --logfile TEXT             Log file to write to
  -e, --services TEXT        Services to impact input as a comma separated
                             list
  -l, --subset TEXT          Further limit selected hosts with an additional
                             pattern
  -i, --inventory-file TEXT  Ansible inventory file to use
  -r, --restart              restart services
  -s, --start                start services
  -t, --stop                 stop services
  -f, --force-stop           kill services
  -f, --clean                clean services
  -n, --install              install services
  -c, --configure            configure services
  --ansible-root-dir TEXT    Root directory for Ansible
  -m, --max-retries INTEGER  Max retries for running the playbook
  --help                     Show this message and exit.
```

##Setup##
```
sudo pip install click
```


##Examples##
Using the below structure as an example...
```
#Install, configure, and start kafka and zookeeper
./serviceCommander.py --services kafka,zookeeper --install --configure --start 

#Start zookeeper
./serviceCommander.py --services zookeeper --start

#Start kafka and point to a non-default ansible-root-dir
./serviceCommander.py --services kafka --start --ansible-root-dir /etc/ansible/
```


##Directory Structure Setup##
- You must have a directory structure to support Service Commander
- Each service must have its own playbook
- Each service you attempt to use must correspond to a role in your [ansible-root-dir]
- Example: 
    ```
    .
    └── tools/
      └── ansible/
      |    ├── kafka.yml
      |    ├── zookeeper.yml
      |    └── roles/
      |      └──  kafka/
      |      └──  zookeeper/
      |      └──  common/
      └── serviceCommander/
          └── serviceCommander.py
    ```


##Playbook Setup##
```
#example ansible/roles/kafka/tasks/main.yml
---
 
# Do stuff to install
- name: Install step 1
  file: path={{ kafka_home_dir }} owner={{ kafka_user }} group={{ kafka_group }} state='directory' recurse='yes'
  sudo: true
  tags:
    - install

- name: Install step 2
  command: ls -la
  tags:
    - install
 
## Adding Zookeeper ID file
- name: Do some configuration
  template: src={{ item }}.j2 dest={{ zookeeper_data_dir }}/{{ item }} group={{ zookeeper_group }} owner={{ zookeeper_user }}
  with_items:
    - myid
  tags:
    - configure
  
 
- name: Stop Kafka Service
  service: name=kafka-zookeeper state=stopped
  sudo: true
  when: ansible_virtualization_type != 'docker'
  tags:
    - stop
 
 
- name: Force Stop Kafka (Docker)
  command: killall kafka
  sudo: yes
  tags:
    - force-stop
  
- name: Clean Kafka
  command: rm -rf {{ kafka_home_dir }}/data && rm -rf {{ kafka_home_dir }}/logs
  when: ansible_virtualization_type == 'docker'
  tags:
    - clean
 
 
- name: Start Kafka Service
  service: name=kafka-zookeeper state=started enabled=yes
  sudo: true
  when: ansible_virtualization_type != 'docker'
  tags:
    - start

```



