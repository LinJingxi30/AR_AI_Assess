// 心率/血氧图表模块

function createHealthChart(ctx) {
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [], // 时间戳
      datasets: [
        {
          label: '心率',
          data: [],
          borderColor: 'red',
          borderWidth: 2,
          fill: false,
          yAxisID: 'y', // 绑定到左侧纵轴
        },
        {
          label: '血氧',
          data: [],
          borderColor: 'blue',
          borderWidth: 2,
          fill: false,
          yAxisID: 'y1', // 绑定到右侧纵轴
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: {
          title: {
            display: true,
            text: '',
            color: 'white',
          },
          ticks: {
            color: 'white',
          },
        },
        y: {
          title: {
            display: true,
            text: '心率',
            color: 'white',
          },
          ticks: {
            color: 'white',
          },
          position: 'left',
        },
        y1: {
          title: {
            display: true,
            text: '血氧',
            color: 'white',
          },
          ticks: {
            color: 'white',
          },
          position: 'right',
          grid: {
            drawOnChartArea: false,
          },
        },
      },
      plugins: {
        legend: {
          labels: {
            color: 'white',
          },
        },
      },
    },
  });
}