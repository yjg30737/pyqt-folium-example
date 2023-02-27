{% macro script(this, kwargs) %}
    async function newMarker(e){
        let new_mark = L.marker().setLatLng(e.latlng).addTo({{this._parent.get_name()}});
        new_mark.dragging.enable();
        new_mark.on('dblclick', function(e){ {{this._parent.get_name()}}.removeLayer(e.target)})
        let lat = e.latlng.lat.toFixed(4),
           lng = e.latlng.lng.toFixed(4);
        new_mark.bindPopup({{ this.popup }});
        };
    {{this._parent.get_name()}}.on('click', newMarker);
{% endmacro %}