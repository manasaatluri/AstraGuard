fetch("http://raspberrypi.local:5000/status")
.then(res => res.json())
.then(data => {
    document.getElementById("animalName").innerText = data.animal;
    document.getElementById("confidence").innerText = (data.confidence*100).toFixed(2)+"%";
    document.getElementById("cameraFrame").src = data.frame;
});
