######################################################################################
#                                                                                    #
# To build: docker build -t centos:scribengin directory                              # 
# To run:   docker run -t -i centos:scribengin  /bin/bash                            #
#                                                                                    #
######################################################################################

FROM centos:centos7
MAINTAINER Nventdata 
RUN echo "Expose SSH port"
EXPOSE 22 2181 9092 50070 8088 9000 9300

RUN echo "Install openssh"
RUN yum -y install openssh-server openssh-client; yum clean all

RUN echo "Install openssl"
RUN yum -y install openssl

RUN yum install -y sudo 

#RUN echo "Install redhat-lsb"
#RUN yum -y install redhat-lsb

RUN sshd-keygen
RUN echo "SSH login fix for Docker"
RUN sed -i "s/#UsePrivilegeSeparation.*/UsePrivilegeSeparation no/g" /etc/ssh/sshd_config && sed -i "s/UsePAM.*/UsePAM no/g" /etc/ssh/sshd_config

RUN echo "Configure root Account"
RUN mkdir /var/run/sshd
RUN echo 'root:root' | chpasswd

RUN echo "Setup neverwinterdp user"
RUN useradd -m -d /home/neverwinterdp -s /bin/bash -c "neverwinterdp user" -p $(openssl passwd -1 neverwinterdp)  neverwinterdp
RUN echo "neverwinterdp ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN sed -i '/Defaults \+requiretty/s/^/#/' /etc/sudoers
RUN chown -R neverwinterdp:neverwinterdp /opt


RUN echo "Sets up public keys for ssh.  Assumes your public keys are stored in ./tmp"
RUN mkdir -p /root/.ssh
RUN chmod 700 /root/.ssh
ADD tmp/authorized_keys /root/.ssh/authorized_keys
RUN chmod 644 /root/.ssh/authorized_keys

RUN mkdir -p /home/neverwinterdp/.ssh
RUN chown -R neverwinterdp:neverwinterdp /home/neverwinterdp/.ssh
RUN chmod 700 /home/neverwinterdp/.ssh
ADD tmp/authorized_keys /home/neverwinterdp/.ssh/authorized_keys
RUN chmod 644 /home/neverwinterdp/.ssh/authorized_keys




RUN echo "Start sshd service"
CMD ["/usr/sbin/sshd", "-D"]