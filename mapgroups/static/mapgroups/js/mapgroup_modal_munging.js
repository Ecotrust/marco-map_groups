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
