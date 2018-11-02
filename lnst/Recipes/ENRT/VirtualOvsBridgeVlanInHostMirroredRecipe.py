"""
Implements scenario similar to regression_tests/phase2/
(virtual_ovs_bridge_vlan_in_host_mirrored.xml + virtual_ovs_bridge_vlan_in_host_mirrored.py
)
"""
from lnst.Common.Parameters import Param
from lnst.Common.IpAddress import ipaddress
from lnst.Controller import HostReq, DeviceReq
from lnst.Recipes.ENRT.BaseEnrtRecipe import BaseEnrtRecipe, EnrtConfiguration
from lnst.Devices import VlanDevice
from lnst.Devices import OvsBridgeDevice

class VirtualOvsBridgeVlanInHostMirroredRecipe(BaseEnrtRecipe):
    host1 = HostReq()
    host1.eth1 = DeviceReq(label="to_switch")
    host1.tap0 = DeviceReq(label="to_guest1")

    host2 = HostReq()
    host2.eth1 = DeviceReq(label="to_switch")
    host2.tap0 = DeviceReq(label="to_guest2")

    guest1 = HostReq()
    guest1.tap0 = DeviceReq(label="to_guest1")

    guest2 = HostReq()
    guest2.tap0 = DeviceReq(label="to_guest2")

    offload_combinations = Param(default=(
        dict(gro="on", gso="on", tso="on", tx="on", rx="on"),
        dict(gro="off", gso="on", tso="on", tx="on", rx="on"),
        dict(gro="on", gso="off", tso="off", tx="on", rx="on"),
        dict(gro="on", gso="on", tso="off", tx="off", rx="on"),
        dict(gro="on", gso="on", tso="on", tx="on", rx="off")))

    def test_wide_configuration(self):
        host1, host2, guest1, guest2 = self.matched.host1, self.matched.host2, self.matched.guest1, self.matched.guest2

        host1.eth1.down()
        host1.tap0.down()
        host1.br0 = OvsBridgeDevice()
        host1.br0.port_add(host1.eth1)
        host1.br0.port_add(host1.tap0, tag="10")

        host2.eth1.down()
        host2.tap0.down()
        host2.br0 = OvsBridgeDevice()
        host2.br0.port_add(host2.eth1)
        host2.br0.port_add(host2.tap0, tag="10")

        guest1.tap0.down()

        guest2.tap0.down()

        #Due to limitations in the current EnrtConfiguration
        #class, a single vlan test pair is chosen
        configuration = EnrtConfiguration()
        configuration.endpoint1 = guest1.tap0
        configuration.endpoint2 = guest2.tap0

        if "mtu" in self.params:
            host1.br0.mtu = self.params.mtu
            host2.br0.mtu = self.params.mtu
            guest1.tap0.mtu = self.params.mtu
            guest2.tap0.mtu = self.params.mtu

        net_addr_1 = "192.168.10"
        net_addr6_1 = "fc00:0:0:1"

        guest1.tap0.ip_add(ipaddress(net_addr_1 + ".3/24"))
        guest1.tap0.ip_add(ipaddress(net_addr6_1 + "::3/64"))
        guest2.tap0.ip_add(ipaddress(net_addr_1 + ".4/24"))
        guest2.tap0.ip_add(ipaddress(net_addr6_1 + "::4/64"))

        host1.eth1.up()
        host1.tap0.up()
        host1.br0.up()
        host2.eth1.up()
        host2.tap0.up()
        host2.br0.up()
        guest1.tap0.up()
        guest2.tap0.up()

        #TODO better service handling through HostAPI
        host1.run("service irqbalance stop")
        host2.run("service irqbalance stop")
        guest1.run("service irqbalance stop")
        guest2.run("service irqbalance stop")

        for m in self.matched:
            for dev in m.devices:
                self._pin_dev_interrupts(dev, self.params.dev_intr_cpu)

        return configuration

    def test_wide_deconfiguration(self, config):
        host1, host2, guest1, guest2 = self.matched.host1, self.matched.host2, self.matched.guest1, self.matched.guest2

        #TODO better service handling through HostAPI
        host1.run("service irqbalance start")
        host2.run("service irqbalance start")
        guest1.run("service irqbalance start")
        guest2.run("service irqbalance start")