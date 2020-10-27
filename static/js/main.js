window.onload = function () {
  var toggle = document.querySelector(".toggle-wrap");
  var togglein = document.querySelector(".toggle-btn");
  var clockText = document.querySelector(".title-right");
  var warnDiv = document.querySelector(".warning");
  var rowDiv = document.querySelector(".row1");
  var obj = {};
  var sleepDetect = false;

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
      fetch("http://localhost:5000/data")
        .then(function (response) {
          return response.json();
        })
        .then(function (json) {
          obj = json;
          //   console.log(obj);
          if (obj.sleep == true) {
            // sleeping
            warnDiv.classList.remove("deactive");
          } else {
            // not sleeping
            warnDiv.classList.add("deactive");
          }
        });
    } else {
      warnDiv.classList.add("deactive");
    }
  }

  function Init() {
    clock();
    setInterval(function () {
      clock();
      warn();
    }, 1000);
  }

  Init();
};
