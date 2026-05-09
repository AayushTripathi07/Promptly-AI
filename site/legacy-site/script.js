// script.js
document.getElementById('modal-button').addEventListener('click', function() {
    document.getElementById('glass-modal').style.display = 'flex';
});

document.querySelector('.close-button').addEventListener('click', function() {
    document.getElementById('glass-modal').style.display = 'none';
});