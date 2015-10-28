This ansible component is responsible for installation,configuration,starting,force-stopping,stopping,cleaning services. Neverwinterdp-Deployments follows some standards for developments in this component.

###Structure

```
./neverwinterdp-deployments
|-- ansible
|   |-- common.yml
|   |-- zookeeper.yml
|   |-- profile
|   |   |-- default.yml
|   |   |-- performance.yml
|   |   |-- small.yml
|   |   `-- stability.yml
|   |-- programs
|   |   |-- openjdk7_java.yml
|   |   `-- wget.yml
|   |-- roles
|   |   |-- common
|   |   |   `-- tasks
|   |   |       `-- main.yml
|   |   `-- zookeeper
|   |       |-- files
|   |       |   |-- conf
|   |       |   |   `-- log4j.properties
|   |       |   `-- zookeeper-server
|   |       |-- handlers
|   |       |   `-- main.yml
|   |       |-- meta
|   |       |   `-- main.yml
|   |       |-- tasks
|   |       |   `-- main.yml
|   |       `-- templates
|   |           |-- java.env.j2
|   |           |-- myid.j2
|   |           |-- zoo.cfg.j2
|   |           |-- zookeeper-env.sh.j2
|   |           `-- zookeeper.service.j2                              

```

###Development Standards

- For maintainability and ease of use, all the variables should be placed in ```ansible/profile/*.yml```. See the below example how variables are used in task.


```
Example task:
- name: Create zookeeper directory
  file: path={{zookeeper.software.installation.zookeeper_home_dir}} state=directory
  tags:
    - install
```

- All the tasks should have atleast one tag. Allowed tags are "install,configure,start,stop,clean,force-stop". See the below example how tags are used in task.

```
Example task:
- name: Create zookeeper directory
  file: path={{zookeeper.software.installation.zookeeper_home_dir}} state=directory
  tags:
    - install
````


###Example Playbook Setup

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
