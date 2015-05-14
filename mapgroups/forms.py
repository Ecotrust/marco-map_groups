from django import forms

# TODO: Move to common forms module
from django.forms import ModelForm
from django.utils.safestring import mark_safe
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


class BSCheckboxInput(forms.CheckboxInput):
    """A checkbox input with a bootstrap classes that renders as
    <label>[x] name</label>
    """

    TEMPLATE = """{default_input}"""

    def __init__(self, attrs=None, **kwargs):
        attrs = attrs or {}
        attrs.update({'class': 'form-control'})
        super(BSCheckboxInput, self).__init__(attrs, **kwargs)

    def render(self, name, value, attrs=None):
        sup = super(BSCheckboxInput, self)
        default_input = sup.render(name, value, attrs)
        return mark_safe(self.TEMPLATE.format(default_input=default_input))

class CreateGroupForm(forms.Form, DivForm):
    # def __init__(self, *args, **kwargs):
    #     print("Args are", args)
    #     print("Kwargs are", kwargs)
    #     return super(CreateGroupForm, self).__init__()
    name = forms.CharField(max_length=255,
                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    blurb = forms.CharField(max_length=512,
                            widget=forms.Textarea(attrs={'class': 'form-control'}))
    is_open = forms.BooleanField(required=False, widget=BSCheckboxInput())
    image = forms.ImageField(required=False,
                             widget=forms.FileInput(attrs={'class': 'form-control'}))

    def clean(self):
        print("CreateGroupForm: clean()")

        cleaned_data = super(CreateGroupForm, self).clean()

        return cleaned_data


class EditMapGroupForm(CreateGroupForm):
    """Form for editing group information.
    Currently identical to the Create form.
    """


class RemoveMapGroupImageForm(forms.Form):
    """Form that adds a "Remove image" function to the MapGroup edit form.
    Implemented separately so I don't have to maintain a "Remove" checkbox.
    """
    pass

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