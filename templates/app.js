// const startTime = {{ start_time }}
// function display_c() {
//     var refresh = 1000;
//     mytime = setTimeout('display_ct()', refresh)
// }

// function display_ct() {
//     var x = new Date()
//     document.getElementById('ct').innerHTML = x;
//     document.getElementById('since').innerHTML = Math.floor((new Date().getTime() - (startTime * 1000)) / 1000);
//     display_c();
// }

// const socket = io('ws://localhost:8000');
// socket.on('message', text => {
//     const el = document.createElement('li');
//     el.innerHTML = text;
//     document.querySelector('ul').appendChild(el)
// });

// document.getElementById('sendBtn').onclick = () => {
//     const text = document.getElementById('textInput').value;
//     socket.emit('message', text)
// }

// display_ct();

// console.log('hello world');