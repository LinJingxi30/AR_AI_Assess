const mqtt = require('mqtt');
const { random, time } = require('mathjs');

// MQTT连接配置
const brokerUrl = 'wss://ws.chainpray.top/mqtt';
const client = mqtt.connect(brokerUrl);

// 生成随机心率（60-100 bpm）
function generateHeartRate() {
  return Math.floor(random(60, 100)); // 基础心率
}

// 生成随机血氧（95%-100%）
function generateBloodOxygen() {
  return Number(random(95, 100).toFixed(1)); // 保留1位小数
}

client.on('connect', () => {
  console.log('成功连接到MQTT服务器');
  
  // 每1秒发送一次数据
  setInterval(() => {
    const timestamp = new Date().toISOString();
    const data = {
      heart_rate: generateHeartRate(),
      blood_oxygen: generateBloodOxygen(),
      timestamp: timestamp
    };

    // 发送数据到单一主题
    client.publish('health/data', JSON.stringify(data), {
      qos: 0,
      retain: false
    });

    console.log(`[${timestamp}] 数据已发送:`, data);
  }, 1000);
});

client.on('error', (err) => {
  console.error('MQTT连接错误:', err);
  client.end();
});

// 处理关闭信号
process.on('SIGINT', () => {
  console.log('\n正在关闭模拟器...');
  client.end();
  process.exit();
});