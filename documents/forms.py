import os

from django import forms
from django.conf import settings

from .models import Document, Matter

# Whitelist of safe extensions for a law office. Executables blocked.
ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "jpg", "jpeg", "png", "gif", "heic", "tif", "tiff",
    "txt", "rtf", "csv", "eml", "msg", "zip",
}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


class UploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["file", "matter", "title", "note"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "Note for the boss (optional)"}),
            "title": forms.TextInput(attrs={"placeholder": "Leave blank to use the file name"}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        # Only show matters belonging to this organization (tenant isolation).
        if organization is not None:
            self.fields["matter"].queryset = Matter.objects.filter(
                organization=organization
            )
        self.fields["matter"].required = False
        self.fields["title"].required = False

    def clean_file(self):
        f = self.cleaned_data["file"]
        ext = os.path.splitext(f.name)[1].lower().lstrip(".")
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                f"'.{ext}' files are not allowed. Allowed: "
                + ", ".join(sorted(ALLOWED_EXTENSIONS))
            )
        if f.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError("File is too large (50 MB max).")
        return f


class CommentForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Add a note…"}),
        max_length=5000,
    )
