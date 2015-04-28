from django import forms

# TODO: Move to common forms module
from django.forms import ModelForm
from mapgroups.models import MapGroup


class DivForm(object):
    """A form that adds an 'as_div()' method which renders each form element
    inside <div></div> tags.
    """

    def as_div(self):
        "Returns this form rendered as HTML <div>s."
        return self._html_output(
            normal_row='<div%(html_class_attr)s>%(errors)s%(label)s %(field)s%(help_text)s</div>',
            error_row='<div>%s</div>',
            row_ender='</div>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=False)


class CreateGroupForm(forms.Form, DivForm):
    
    # def __init__(self, *args, **kwargs):
    #     print("Args are", args)
    #     print("Kwargs are", kwargs)
    #     return super(CreateGroupForm, self).__init__()
    name = forms.CharField(max_length=255)
    blurb = forms.CharField(max_length=512)
    is_open = forms.BooleanField(required=False)
    image = forms.ImageField(required=False)

    def clean(self):
        print("CreateGroupForm: clean()")

        cleaned_data = super(CreateGroupForm, self).clean()

        return cleaned_data


class EditMapGroupForm(CreateGroupForm):
    """Form for editing group information.
    Currently identical to the Create form.
    """


class JoinMapGroupActionForm(forms.Form, DivForm):
    pass


class LeaveMapGroupActionForm(forms.Form, DivForm):
    pass


class DeleteMapGroupActionForm(forms.Form, DivForm):
    pass


class MapGroupPreferencesForm(forms.Form, DivForm):
    show_real_name = forms.BooleanField(required=False)


class RequestJoinMapGroupActionForm(forms.Form, DivForm):
    message = forms.CharField()