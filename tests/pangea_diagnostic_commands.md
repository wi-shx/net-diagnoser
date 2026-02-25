# Pangea 网络诊断命令手册

本文档记录了针对 Pangea 网络问题的所有诊断命令及其典型输出。

## 场景1: 驱动问题诊断

### 1.1 检查驱动是否加载
```bash
lsmod | grep pangea
```

**预期输出:**
```
pangea_drv            532480  0
pangea_kern           262144  2
```

### 1.2 查看驱动详细信息
```bash
modinfo pangea_drv
```

**预期输出:**
```
filename:       /lib/modules/5.15.0/kernel/drivers/net/pangea/pangea_drv.ko
version:        2.5.1
license:        GPL
description:    Pangea Network Driver
author:         Pangea Networks
srcversion:     ABC123DEF456
alias:          pci:v000010EEd00009023sv*sd*bc*sc*i*
depends:        pangea_kern
retpoline:      Y
name:           pangea_drv
vermagic:       5.15.0 SMP mod_unload modversions
parm:           debug:Debug level (int)
```

### 1.3 检查内核日志中的驱动消息
```bash
dmesg -T | grep -i pangea | tail -20
```

**预期输出:**
```
[  123.456789] pangea_drv: loading driver version 2.5.1
[  123.567890] pangea_drv: PCI device 10ee:9023 detected
[  123.678901] pangea_drv: Firmware version 1.2.3 loaded
[  123.789012] pangea_drv: Device pangea0 initialized
```

---

## 场景2: 内核态问题诊断

### 2.1 检查内核模块状态
```bash
cat /proc/modules | grep pangea
```

**预期输出:**
```
pangea_drv 532480 0 - Live 0xffffffffc0123000
pangea_kern 262144 2 pangea_drv, Live 0xffffffffc0234000
```

### 2.2 检查内核丢包统计
```bash
dmesg -T | grep -i "dropped\|error\|fail" | grep pangea
```

**预期输出:**
```
[  234.567890] pangea_kern: RX queue 0 dropped 15234 packets
[  234.678901] pangea_kern: buffer allocation failed, out of memory
```

### 2.3 检查内核网络参数
```bash
sysctl -a | grep net.core
```

**预期输出:**
```
net.core.somaxconn = 128
net.core.optmem_max = 20480
net.core.rmem_default = 212992
net.core.rmem_max = 212992
net.core.wmem_default = 212992
net.core.wmem_max = 212992
net.core.netdev_max_backlog = 1000
net.core.netdev_budget = 300
```

---

## 场景3: 用户态软件诊断

### 3.1 检查 pangea 服务状态
```bash
systemctl status pangea-agent
```

**预期输出:**
```
● pangea-agent.service - Pangea Network Agent
   Loaded: loaded (/etc/systemd/system/pangea-agent.service; enabled; vendor preset: enabled)
   Active: active (running) since Tue 2026-02-25 10:00:00 UTC; 1h ago
 Main PID: 12345 (pangea_agent)
    Tasks: 5 (limit: 4915)
   Memory: 128.5M
   CGroup: /system.slice/pangea-agent.service
           └─12345 /usr/bin/pangea_agent
```

### 3.2 检查进程状态
```bash
ps aux | grep pangea
```

**预期输出:**
```
root     12345  0.5  1.2 128456 128512 ?        Ssl  10:00   0:30 /usr/bin/pangea_agent
root     12346  0.0  0.1  12345  12345 ?        S    10:00   0:00 /usr/bin/pangea_monitor
```

### 3.3 检查服务日志
```bash
journalctl -u pangea-agent -n 20 --no-pager
```

**预期输出:**
```
Feb 25 10:00:00 server1 pangea_agent[12345]: Starting Pangea Network Agent
Feb 25 10:00:01 server1 pangea_agent[12345]: Connected to kernel module
Feb 25 10:00:02 server1 pangea_agent[12345]: Flow rules updated successfully
```

---

## 场景4: 网卡固件诊断

### 4.1 查看固件版本
```bash
ethtool -i pangea0
```

**预期输出:**
```
driver: pangea_drv
version: 2.5.1
firmware-version: 1.2.3
expansion-rom-version:
bus-info: 0000:17:00.0
supports-statistics: yes
supports-test: yes
supports-eeprom-access: yes
supports-register-dump: yes
supports-priv-flags: yes
```

### 4.2 查看网卡特性
```bash
ethtool -k pangea0
```

**预期输出:**
```
Features for pangea0:
rx-checksumming: on
tx-checksumming: on
scatter-gather: on
tcp-segmentation-offload: on
generic-receive-offload: on
large-receive-offload: off
hw-vlan-strip: on
hw-vlan-filter: on
```

---

## 场景5: 网卡硬件诊断

### 5.1 查看 PCI 设备信息
```bash
lspci -vvv -s 17:00.0 | head -40
```

**预期输出:**
```
17:00.0 Ethernet controller: Pangea Networks Device 9023
        Subsystem: Pangea Networks Device 0001
        Control: I/O+ Mem+ BusMaster+ SpecCycle- MemWINV- VGASnoop- ParErr+
        Status: Cap+ 66MHz- UDF- FastB2B- ParErr- DEVSEL=fast >TAbort-
        Latency: 0, Cache Line Size: 64 bytes
        Interrupt: pin A routed to IRQ 125
        Region 0: Memory at fe800000 (64-bit, prefetchable) [size=2M]
        Region 2: Memory at fe600000 (64-bit, non-prefetchable) [size=256K]
        Capabilities: [40] Power Management version 3
        Capabilities: [50] MSI: Enable+ Count=1/32 Maskable+ 64bit+
        Capabilities: [70] Express (v2) Endpoint, MSI 00
        Capabilities: [100] Advanced Error Reporting
        Capabilities: [150] Device Serial Number 00-1a-2b-3c-4d-5e
```

### 5.2 查看硬件统计
```bash
ethtool -S pangea0 | head -30
```

**预期输出:**
```
NIC statistics:
     rx_packets: 123456789
     tx_packets: 98765432
     rx_bytes: 102345678901
     tx_bytes: 87654321098
     rx_errors: 0
     tx_errors: 0
     rx_dropped: 0
     tx_dropped: 0
     multicast: 12345
     collisions: 0
     rx_length_errors: 0
     rx_over_errors: 0
     rx_crc_errors: 0
     rx_frame_errors: 0
     rx_fifo_errors: 0
     rx_missed_errors: 0
```

---

## 场景6: 光模块诊断

### 6.1 查看光模块信息
```bash
ethtool -m pangea0
```

**预期输出:**
```
        Identifier                                : 0x03 (SFP)
        Extended identifier                       : 0x04 (GBIC/SFP defined)
        Connector                                 : 0x21 (LC)
        Transceiver codes                         : 0x00 0x00 0x00 0x00 0x00
        Transceiver type                          : 10G Ethernet: 10G Base-LR
        Encoding                                  : 0x06 (64B/66B)
        BR, Nominal                               : 10300MBd
        Rate identifier                           : 0x00
        Length (SMF, km)                          : 10km
        Length (SMF)                              : 10000m
        Laser wavelength                          : 1310nm
        Vendor name                               : PANGEA-OPTICS
        Vendor OUI                                : 00:1a:2b
        Vendor PN                                 : SFP-10G-LR-10
        Vendor rev                                : 1.0
        Option values                             : 0x00 0x1a
        Option                                    : RX_LOS implemented
        Option                                    : TX_FAULT implemented
        Option                                    : TX_DISABLE implemented
        BR margin, max                            : 0%
        Transmit avg power (dBm)                  : -1.5
        Receiver signal avg power (dBm)           : -8.3
```

### 6.2 检查光功率
```bash
ethtool -m pangea0 | grep -i power
```

**预期输出:**
```
        Transmit avg power (dBm)                  : -1.5
        Receiver signal avg power (dBm)           : -8.3
```

---

## 场景7: 网络配置诊断

### 7.1 查看接口状态
```bash
ip addr show pangea0
```

**预期输出:**
```
4: pangea0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc mq state UP group default qlen 1000
    link/ether 00:1a:2b:3c:4d:5e brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.100/24 brd 192.168.1.255 scope global pangea0
       valid_lft forever preferred_lft forever
    inet6 fe80::21a:2bff:fe3c:4d5e/64 scope link
       valid_lft forever preferred_lft forever
```

### 7.2 检查 MTU 配置
```bash
ip link show pangea0 | grep mtu
```

**预期输出:**
```
4: pangea0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc mq state UP mode DEFAULT
```

### 7.3 检查 VLAN 配置
```bash
ip -d link show pangea0.100
```

**预期输出:**
```
5: pangea0.100@pangea0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc noqueue state UP mode DEFAULT
    link/ether 00:1a:2b:3c:4d:5e brd ff:ff:ff:ff:ff:ff promiscuity 0
    vlan protocol 802.1Q id 100 <REORDER_HDR> addrgenmode eui64
```

---

## 场景8: IP配置诊断

### 8.1 检查 IP 地址
```bash
ip -4 addr show pangea0
```

**预期输出:**
```
4: pangea0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 9000 qdisc mq state UP group default qlen 1000
    inet 192.168.1.100/24 brd 192.168.1.255 scope global pangea0
       valid_lft forever preferred_lft forever
```

### 8.2 检查 IP 冲突
```bash
arping -c 3 -I pangea0 192.168.1.100
```

**预期输出:**
```
ARPING 192.168.1.100 from 192.168.1.100 pangea0
Unicast reply from 192.168.1.100 [00:1A:2B:3C:4D:5E]  0.500ms
Unicast reply from 192.168.1.100 [00:1A:2B:3C:4D:5E]  0.501ms
Unicast reply from 192.168.1.100 [00:1A:2B:3C:4D:5E]  0.502ms
Sent 3 probes (3 broadcast(s))
Received 3 response(s)
```

---

## 场景9: MAC配置诊断

### 9.1 检查 MAC 地址
```bash
ip link show pangea0 | grep ether
```

**预期输出:**
```
    link/ether 00:1a:2b:3c:4d:5e brd ff:ff:ff:ff:ff:ff
```

### 9.2 检查 ARP 表
```bash
arp -a -n | grep pangea0
```

**预期输出:**
```
? (192.168.1.1) at 00:11:22:33:44:55 [ether] on pangea0
? (192.168.1.2) at 00:11:22:33:44:56 [ether] on pangea0
```

### 9.3 检查组播地址
```bash
ip maddr show pangea0
```

**预期输出:**
```
4:      pangea0
        link  01:00:5e:00:00:01
        link  33:33:00:00:00:01
        link  33:33:ff:3c:4d:5e
        inet  224.0.0.1
        inet6 ff02::1
        inet6 ff02::1:ff3c:4d5e
```

---

## 场景10: 网关配置诊断

### 10.1 检查默认路由
```bash
ip route show default
```

**预期输出:**
```
default via 192.168.1.1 dev pangea0 proto dhcp metric 100
```

### 10.2 检查完整路由表
```bash
ip route show
```

**预期输出:**
```
default via 192.168.1.1 dev pangea0 proto dhcp metric 100
10.0.0.0/8 via 192.168.1.1 dev pangea0 proto static metric 101
172.16.0.0/12 via 192.168.1.1 dev pangea0 proto static metric 102
192.168.1.0/24 dev pangea0 proto kernel scope link src 192.168.1.100 metric 100
```

### 10.3 测试网关连通性
```bash
ping -c 3 192.168.1.1
```

**预期输出:**
```
PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data.
64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=0.234 ms
64 bytes from 192.168.1.1: icmp_seq=2 ttl=64 time=0.256 ms
64 bytes from 192.168.1.1: icmp_seq=3 ttl=64 time=0.245 ms

--- 192.168.1.1 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2002ms
rtt min/avg/max/mdev = 0.234/0.245/0.256/0.009 ms
```

---

## 场景11: 子网配置诊断

### 11.1 检查子网掩码
```bash
ip addr show pangea0 | grep inet
```

**预期输出:**
```
    inet 192.168.1.100/24 brd 192.168.1.255 scope global pangea0
```

### 11.2 检查网络和广播地址
```bash
ipcalc 192.168.1.100/24
```

**预期输出:**
```
Address: 192.168.1.100
Netmask: 255.255.255.0 = 24
Network: 192.168.1.0/24
HostMin: 192.168.1.1
HostMax: 192.168.1.254
Broadcast: 192.168.1.255
Hosts/Net: 254
```

---

## 场景12: DNS配置诊断

### 12.1 检查 DNS 配置
```bash
cat /etc/resolv.conf
```

**预期输出:**
```
nameserver 192.168.1.1
nameserver 8.8.8.8
search pangea.local
```

### 12.2 测试 DNS 解析
```bash
dig @192.168.1.1 internal.pangea.io +short
```

**预期输出:**
```
10.0.0.100
```

---

## 场景13: 综合连通性测试

### 13.1 端到端连通性
```bash
ping -c 3 -I pangea0 10.0.0.100
```

**预期输出:**
```
PING 10.0.0.100 (10.0.0.100) from 192.168.1.100 pangea0: 56(84) bytes of data.
64 bytes from 10.0.0.100: icmp_seq=1 ttl=62 time=1.234 ms
64 bytes from 10.0.0.100: icmp_seq=2 ttl=62 time=1.456 ms
64 bytes from 10.0.0.100: icmp_seq=3 ttl=62 time=1.345 ms

--- 10.0.0.100 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2003ms
rtt min/avg/max/mdev = 1.234/1.345/1.456/0.090 ms
```

### 13.2 路由追踪
```bash
traceroute -n -i pangea0 10.0.0.100
```

**预期输出:**
```
traceroute to 10.0.0.100 (10.0.0.100), 30 hops max, 60 byte packets
 1  192.168.1.1  0.534 ms  0.456 ms  0.423 ms
 2  10.0.0.1     1.234 ms  1.123 ms  1.145 ms
 3  10.0.0.100   1.567 ms  1.456 ms  1.489 ms
```

### 13.3 端口连通性
```bash
nc -zv -w 3 10.0.0.100 443
```

**预期输出:**
```
Connection to 10.0.0.100 443 port [tcp/https] succeeded!
```

---

## 快速诊断命令汇总

```bash
# 一键收集所有网络诊断信息
echo "=== 网络接口状态 ===" && ip addr show
echo "=== 路由表 ===" && ip route show
echo "=== ARP 表 ===" && arp -a -n
echo "=== DNS 配置 ===" && cat /etc/resolv.conf
echo "=== 网卡统计 ===" && ethtool -S pangea0
echo "=== 驱动信息 ===" && ethtool -i pangea0
echo "=== 内核消息 ===" && dmesg -T | grep -i pangea | tail -20
echo "=== 服务状态 ===" && systemctl status pangea-agent
echo "=== 模块列表 ===" && lsmod | grep pangea
echo "=== PCI 设备 ===" && lspci -v | grep -A 10 -i pangea
```
