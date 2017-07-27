firewall-cmd --list-all-zones

firewall-cmd --zone=home --remove-interface=eno33557248 --permanent
firewall-cmd --zone=home --remove-interface=eno16777984 --permanent

firewall-cmd --zone=external --add-interface=eno33557248 --permanent
firewall-cmd --zone=internal --add-interface=eno16777984 --permanent


firewall-cmd --zone=external --remove-service=ssh --permanent
firewall-cmd --zone=external --add-masquerade --permanent


firewall-cmd --direct --permanent --add-rule ipv4 filter INPUT 0 --in-interface eno16777984 --destination 224.0.0.18 --protocol vrrp -j ACCEPT
firewall-cmd --direct --permanent --add-rule ipv4 filter OUTPUT 0 --out-interface eno16777984 --destination 224.0.0.18 --protocol vrrp -j ACCEPT

firewall-cmd --direct --permanent --add-rule ipv4 filter INPUT 0 --in-interface eno33557248 --destination 224.0.0.18 --protocol vrrp -j ACCEPT
firewall-cmd --direct --permanent --add-rule ipv4 filter OUTPUT 0 --out-interface eno33557248 --destination 224.0.0.18 --protocol vrrp -j ACCEPT

firewall-cmd --set-default-zone=internal
firewall-cmd --complete-reload

--это штоб нат заработал и кипаливд зафайрволен был
--а это для форварда
--add forward port
firewall-cmd --direct --permanent --add-rule ipv4 nat POSTROUTING 0 -j MASQUERADE
firewall-cmd --permanent --zone=external --add-forward-port=port=81:proto=tcp:toport=80:toaddr=192.168.154.110
firewall-cmd --permanent --zone=external --add-forward-port=port=82:proto=tcp:toport=8080:toaddr=192.168.155.33


-- это попытка сделать лог (
firewall-cmd --zone=external --permanent --add-rich-rule='rule family="ipv4" forward-port port="63389" protocol="tcp" to-port="3389" to-addr="192.168.155.143" log prefix="RDP_63389_"'

sudo tail -f /var/log/messages |grep RDP_63389_

--не робит пока
--это логинг всего трафа
firewall-cmd --zone=external --add-rich-rule='rule family="ipv4" source address=0.0.0.0 invert="true" log prefix="FIREWALL_" accept'

man 5 firewalld.richlanguage
