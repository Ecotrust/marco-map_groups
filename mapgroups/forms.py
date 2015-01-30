from django import forms

# TODO: Move to common forms module
class DivForm(forms.Form):
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


class CreateGroupForm(DivForm):
    name = forms.CharField(max_length=255)
    blurb = forms.CharField(max_length=512)
    is_open = forms.BooleanField()
