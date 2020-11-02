window.onload = function () {
  var toggle = document.querySelector(".toggle-wrap");
  var togglein = document.querySelector(".toggle-btn");
  var clockText = document.querySelector(".title-right");
  var warnDiv = document.querySelector(".warning");
  var rowDiv = document.querySelector(".row1");
  var obj = {};
  var sleepDetect = false;
  var sensorValue = [[0, 0, 0, 0, 0, 0, 0],[0, 0, 0, 0, 0, 0, 0]];
  var audio = document.getElementsByTagName('audio')[0];
  var sensorText = document.querySelector('.right-button');

  var ctx = document.getElementById('myChart').getContext('2d');

  var chart = new Chart(ctx, {
    // The type of chart we want to create
    type: 'line',

    // The data for our dataset
    data: {
      labels: ['1', '2', '3', '4', '5', '6', '7'],
      datasets: [
        {
          label: '온도센서 값',
          backgroundColor: 'rgba(0,0,0,0.00)',
          borderColor: 'rgb(255, 99, 132)',
          data: sensorValue[0],
        },
        {
          label: '습도센서 값',
          backgroundColor: 'rgba(0,0,0,0.00)',
          borderColor: 'rgb(75, 192, 192)',
          data: sensorValue[1],
        }        
                ] // datasets
    },

    // Configuration options go here
    options: {

    }
  });

  toggle.addEventListener("click", function (e) {
    togglein.classList.toggle("active");
    rowDiv.classList.toggle("active");
    sleepDetect = !sleepDetect;

    fetch("http://localhost:5000/active").then(function (response) {
      response.text().then(function (text) {
        console.log(text);
      });
    });
  });

  function clock() {
    var date = new Date();

    // 시간을 받아오고
    var hours = date.getHours();
    // 분도 받아옵니다.
    var minutes = date.getMinutes();

    // 초까지 받아온후
    var seconds = date.getSeconds();

    clockText.innerHTML = hours + ":" + minutes + ":" + seconds;
  }


  function warn() {
    if (sleepDetect == true) {
      fetch("http://localhost:5000/sleep").then(function (response) {
        response.json().then(function (json) {
          obj = json;
          console.log(obj);

          //   console.log(obj);
          if (obj.sleep == true) {
            // sleeping
            warnDiv.classList.remove("deactive");
              audio.play(); 
            
          } else {
            // not sleeping
            warnDiv.classList.add("deactive");
            audio.pause();
          }

        });
      });
    } 
    else {
      warnDiv.classList.add("deactive");
    }
  } // warn

  function graph() {
    if (sleepDetect == true) {
      
      fetch("http://192.168.43.141:5000/data").then(function (response) {
        response.json().then(function (json) {
          obj = json;
          console.log(obj);
          sensorValue[0] = obj.sensor1;
          sensorValue[1] = obj.sensor2;
          // console.log(obj);
          sensorText.innerHTML = "온도 센서 값 : " + sensorValue[0] + " , 습도 센서 값 : " + sensorValue[1];

          //라벨 삭제
          chart.data.labels.splice(0,1);

          // 데이터 삭제
          chart.data.datasets.forEach(function(dataset) {
            dataset.data.splice(0,1);
          });

          //라벨추가
          chart.data.labels.push(chart.data.labels.length.toString())

          //데이터셋 수 만큼 반복
          var dataset = chart.data.datasets;
          for (var i = 0; i < dataset.length; i++) {
            //데이터셋의 데이터 추가
            dataset[i].data.push(sensorValue[i]);
          }
          chart.update(); //차트 업데이트
        });
      });
    } 
    else {

    }
  } // graph

  function Init() {
    clock();
    setInterval(function () {
      clock();
      warn();
    }, 500);

    setInterval(function() {
      graph();
    }, 3000);

  } // Init

  Init();
};