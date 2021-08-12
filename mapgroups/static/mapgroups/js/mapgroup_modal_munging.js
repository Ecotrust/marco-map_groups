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
