(function () {
  'use strict';

  function goToNearby(position) {
    var lat = position.coords.latitude;
    var lng = position.coords.longitude;
    window.location.href = '/listings/nearby/?lat=' + lat + '&lng=' + lng;
  }

  function handleError() {
    alert('Location access is required to explore nearby food experiences.');
  }

  document.addEventListener('click', function (e) {
    if (!e.target.closest('.js-nearby-btn')) return;
    if (!navigator.geolocation) {
      alert('Location access is required to explore nearby food experiences.');
      return;
    }
    navigator.geolocation.getCurrentPosition(goToNearby, handleError);
  });
}());
