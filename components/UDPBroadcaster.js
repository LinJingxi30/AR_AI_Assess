const dgram = require('dgram');
const os = require('os');

class UDPBroadcaster {
    constructor(config) {
        this.config = {
            port: config.port || 9999,
            interval: config.interval || 1000,
            serviceName: config.serviceName || 'service',
            servicePort: config.servicePort || 8000
        };
        
        this.server = dgram.createSocket('udp4');
        this.isRunning = false;
        this.broadcastTimer = null;
        
        // 绑定错误处理
        this.server.on('error', this.handleError.bind(this));
    }
    
    // 计算广播地址
    calculateBroadcast(ip, netmask) {
        const ipParts = ip.split('.').map(Number);
        const maskParts = netmask.split('.').map(Number);
        return ipParts.map((part, i) => (part & maskParts[i]) | (~maskParts[i] & 255)).join('.');
    }
    
    // 获取所有网卡的广播地址
    getBroadcastAddresses() {
        const interfaces = os.networkInterfaces();
        const broadcasts = [];
        
        for (let [name, addrs] of Object.entries(interfaces)) {
            for (let addr of addrs) {
                if (addr.family === 'IPv4' && !addr.internal) {
                    const broadcast = this.calculateBroadcast(addr.address, addr.netmask);
                    broadcasts.push({
                        name,
                        address: addr.address,
                        broadcast: broadcast
                    });
                }
            }
        }
        return broadcasts;
    }
    
    // 开始广播
    start() {
        if (this.isRunning) return;
        
        this.server.bind(this.config.port, () => {
            this.server.setBroadcast(true);
            console.log(`UDP 服务已启动在端口 ${this.config.port}`);
            
            this.broadcastTimer = setInterval(() => {
                const networkInterfaces = this.getBroadcastAddresses();
                
                for (const iface of networkInterfaces) {
                    const broadcastInfo = JSON.stringify({
                        ip: iface.address,
                        port: this.config.servicePort,
                        name: this.config.serviceName,
                        interface: iface.name,
                        timestamp: Date.now()
                    });
                    
                    this.server.send(
                        broadcastInfo,
                        this.config.port,
                        iface.broadcast,
                        this.handleSendCallback.bind(this, iface)
                    );
                }
            }, this.config.interval);
        });
        
        this.isRunning = true;
    }
    
    // 停止广播
    stop() {
        if (this.broadcastTimer) {
            clearInterval(this.broadcastTimer);
            this.broadcastTimer = null;
        }
        
        if (this.isRunning) {
            this.server.close();
            this.isRunning = false;
        }
    }
    
    // 错误处理
    handleError(err) {
        console.error('UDP 广播错误:', err);
    }
    
    // 发送回调处理
    handleSendCallback(iface, err) {
        if (err) {
            console.error(`UDP 广播错误 (${iface.name}):`, err);
        } else {
            // console.log(`UDP 广播已发送到 ${iface.name} (${iface.broadcast})`);
        }
    }
}

module.exports = UDPBroadcaster;