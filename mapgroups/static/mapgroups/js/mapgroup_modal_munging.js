$('#bookmark-audit-modal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget); // Button that triggered the modal
  var bookmark_id = button.data('bookmark_id');
  var bookmark_name = button.data('bookmark_name');
  $('#bookmark-modal-title').html(bookmark_name + ' Details');
  $('#bookmark-modal-content').html('Loading...');
  $.ajax({
    url: '/visualize/rest/bookmarks/' + bookmark_id + '/?format=json',
    success: function(response){
      var layer_table = '<table class="modal-layer-table"><tr><th>layer</th><th>Description</th><th>Owner</th></tr>';
      for (var i = 0; i < response.overview.layers.length; i++){
        row = response.overview.layers[i];
        if (row.url) {
          row_name = '<a target="_blank" href="' + row.url + '">' + row.name + '</a>';
        } else {
          row_name = row.name;
        }
        if (row.owner.url) {
          row_owner = '<a target="_blank" href="' + row.owner.url + '">' + row.owner.name + '</a>';
        } else {
          row_owner = row.owner.name;
        }
        layer_table = layer_table + '<tr>' +
          '<td>' + row_name + '</td>' +
          '<td>' + row.description + '</td>' +
          '<td>' + row_owner + '</td>' +
        '</tr>';
      }
      layer_table = layer_table + '</table>';
      var description = '<p><a target="_blank" href=' + response.overview.url + '>View In Maps</a></p>' +
        '<table class="modal-bookmark-table">' +
          '<tr><th>Name: </th><td><a target="_blank" href="' + response.overview.admin + '">' + response.overview.name + '</a></td></tr>' +
          '<tr><th>Description: </th><td>' + response.overview.description + '</td></tr>' +
          '<tr><th>Owner: </th><td><a target="_blank" href="' + response.overview.owner.url + '">' + response.overview.owner.name + '</a></td></tr>' +
          '<tr><th>Layers: </th><td>' + layer_table + '</td></tr>' +
        '</table>';
      $('#bookmark-modal-content').html(description);
    }
  })

});

var draw_map = function(drawing_json) {

  var baselayer = new ol.layer.Tile({
    source: new ol.source.OSM(),
  });

  var features = new ol.format.GeoJSON().readFeatures(drawing_json);
  vectorSource = new ol.source.Vector({
    wrapX: false,
    features: features
  });
  var vectorLayer = new ol.layer.Vector({
    source: vectorSource,
  });
  map = new ol.Map({
    layers: [
      baselayer,
      vectorLayer
    ],
    target: 'map',
    view: new ol.View({
      center: [
        -13580977,
        5471521
      ],
      zoom: 6,
    })
  });
  map.getView().fit(vectorSource.getExtent(), {'duration': 1000});
  window.setTimeout(
    function(){map.updateSize();}, 
    500
  );
}

$('#drawing-audit-modal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget); // Button that triggered the modal
  var user_admin_url = button.data('user_admin_url');

  // DRAWING MODAL
  var drawing_id = button.data('drawing_id');
  var drawing_name = button.data('drawing_name');
  var drawing_description = button.data('drawing_description');
  var drawing_admin_url = button.data('drawing_admin_url');
  var drawing_owner_id = button.data('drawing_owner_id');
  var drawing_owner_name = button.data('drawing_owner_name');
  $('#drawing-modal-title').html(drawing_name + ' Details');
  $('#drawing-modal-admin-link').html(
    '<p style="margin: 2rem 0 0 2rem;"><a target="_blank" href="' + 
    drawing_admin_url + drawing_id +
    '/change/">View in Admin</a></p>'
  );
  $('#drawing-modal-content').html(
    '<div class="row">' + 
      '<div class="col-sm-1"></div>' +
      '<div class="col-sm-10">' +
        '<table>' +
          '<tr><th>Name: </th><td>' + drawing_name + '</td></tr>' +
          '<tr><th>Description:&nbsp;&nbsp;&nbsp; </th><td>' + drawing_description + '</td></tr>' +
          '<tr><th>Owner: </th><td>' + drawing_owner_name + '</td></tr>' +
        '</table>' +
      '</div>' +
      '<div class="col-sm-1"></div>' +
    '</div>' +
    '<div class="row">' + 
      '<div class="col-sm-3"></div>' +
      '<div class="col-lg-6">' +
        '<div id="map" class="map">' +
        '</div>' +
      '</div>' +
      '<div class="col-sm-3"></div>' +
    '</div>'
  );
  draw_map(button.data('drawing_json'));
});

// USER LAYER MODAL
$('#user-layer-audit-modal').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget); // Button that triggered the modal
  var userlayer_id = button.data('userlayer_id');
  var userlayer_name = button.data('userlayer_name');
  var userlayer_description = button.data('userlayer_description');
  var userlayer_admin_url = button.data('userlayer_admin_url');
  var userlayer_owner_id = button.data('userlayer_owner_id');
  var userlayer_owner_name = button.data('userlayer_owner_name');
  var user_admin_url = button.data('user_admin_url');
  $('#user-layer-modal-title').html(userlayer_name + ' Details');
  $('#user-layer-modal-admin-link').html(
    '<p style="margin: 2rem 0 0 2rem;"><a target="_blank" href="' + 
    userlayer_admin_url + userlayer_id +
    '/change/">View in Admin</a></p>'
  );
  $('#user-layer-modal-content').html(
    '<div class="row">' + 
      '<div class="col-sm-1"></div>' +
      '<div class="col-sm-10">' +
        '<table>' +
          '<tr><th>Name: </th><td>' + userlayer_name + '</td></tr>' +
          '<tr><th>Description:&nbsp;&nbsp;&nbsp; </th><td>' + userlayer_description + '</td></tr>' +
          '<tr><th>Owner: </th><td>' + userlayer_owner_name + '</td></tr>' +
        '</table>' +
      '</div>' +
      '<div class="col-sm-1"></div>' +
    '</div>' +
    '<div class="row">' + 
      '<div class="col-sm-3"></div>' +
      '<div class="col-lg-6">' +
        '<div id="map" class="map">' +
        '</div>' +
      '</div>' +
      '<div class="col-sm-3"></div>' +
    '</div>'
  );
});

$('#rus-membership-approval').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget); // Button that triggered the modal
  var member_pk = button.data('member_id');
  var member_name = button.data('member_name');
  var title = button.data('title');
  var action = button.data('act');
  $('#approve-member-button-form').attr('action', '/collaborate/groups/' + member_pk + '/' + action);
  $('#approve-username').html(member_name);
  $('#approve-title').html(title);
  $('#approval-act').html(action);
});

$('#rus-membership-status').on('show.bs.modal', function (event) {
  var button = $(event.relatedTarget); // Button that triggered the modal
  var member_pk = button.data('member_id');
  var member_name = button.data('member_name');
  var title = button.data('title');
  var action = button.data('act');
  $('#status-member-button-form').attr('action', '/collaborate/groups/' + member_pk + '/' + action);
  $('#status-username').html(member_name);
  $('#rus-status-title').html(title);
  $('#status-act').html(action);
});
