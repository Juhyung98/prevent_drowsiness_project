window.onload = function () {
    var toggle = document.querySelector('.toggle-wrap');
    var togglein = document.querySelector('.toggle-btn');
    var clockText = document.querySelector('.title-right');
    var rowDiv = document.querySelector('.row1');

    toggle.addEventListener('click', function (e) {
        togglein.classList.toggle('active');
        rowDiv.classList.toggle('active');

        fetch("http://localhost:5000/active")
        .then(function(response) {
            response.text().then(function(text){
                console.log(text);
            })
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

    function clockInit() {
        clock();
        setInterval(clock, (1000));
    }

    clockInit();
};