{% macro script(this, kwargs) %}
    async function newMarker(e){
        let lat = e.latlng.lat.toFixed(4),
        lng = e.latlng.lng.toFixed(4);
        let data = {lat: lat, lng: lng};
        let response = await fetch('http://127.0.0.1:5000/add_marker', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        }).then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            let new_mark = L.marker().setLatLng(e.latlng).addTo({{this._parent.get_name()}});
            new_mark.dragging.enable();
            new_mark.on('dblclick', function(e){ {{this._parent.get_name()}}.removeLayer(e.target)})
            new_mark.bindPopup({{ this.popup }});
            console.log('Marker saved successfully!');
        })
        .catch(error => {
            console.error('Error saving marker data:', error);
        });
    };
    {{this._parent.get_name()}}.on('click', newMarker);
{% endmacro %}