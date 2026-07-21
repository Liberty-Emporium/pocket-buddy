import mimetypes

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CommentForm, UploadForm
from .models import Document, DocumentComment


def _org(request):
    """The caller's organization, or None. Every view scopes to this."""
    return request.user.organization


def _get_owned_document(request, pk):
    """Fetch a document ONLY if it belongs to the caller's org. Else 404."""
    org = _org(request)
    if org is None:
        raise Http404
    return get_object_or_404(Document, pk=pk, organization=org)


@login_required
def secretary_list(request):
    org = _org(request)
    documents = (
        Document.objects.filter(organization=org)
        .select_related("matter", "uploaded_by")
        if org
        else Document.objects.none()
    )
    return render(
        request,
        "secretary_list.html",
        {"documents": documents, "org": org},
    )


@login_required
def upload(request):
    org = _org(request)
    if org is None:
        return HttpResponseForbidden("Your account is not linked to an organization.")
    form = UploadForm(
        request.POST or None,
        request.FILES or None,
        organization=org,
    )
    if request.method == "POST" and form.is_valid():
        doc = form.save(commit=False)
        doc.organization = org
        doc.uploaded_by = request.user
        doc.save()
        return redirect("secretary_list")
    return render(request, "upload.html", {"form": form, "org": org})


@login_required
def boss_feed(request):
    org = _org(request)
    show_handled = request.GET.get("handled") == "1"
    qs = (
        Document.objects.filter(organization=org).select_related("matter")
        if org
        else Document.objects.none()
    )
    if not show_handled:
        qs = qs.filter(handled=False)
    return render(
        request,
        "boss_feed.html",
        {"documents": qs, "org": org, "show_handled": show_handled},
    )


@login_required
def document_detail(request, pk):
    doc = _get_owned_document(request, pk)
    # Mark seen the first time the boss opens it.
    if request.user.is_boss and not doc.seen_by_boss:
        doc.seen_by_boss = True
        doc.save(update_fields=["seen_by_boss"])
    return render(
        request,
        "document_detail.html",
        {"doc": doc, "comment_form": CommentForm()},
    )


@login_required
def document_serve(request, pk):
    """Stream a file only after auth + tenant-ownership check."""
    doc = _get_owned_document(request, pk)
    if not doc.file:
        raise Http404
    content_type, _ = mimetypes.guess_type(doc.original_name or doc.file.name)
    raw_name = doc.original_name or doc.file.name.split("/")[-1]
    # Sanitize: no quotes/newlines can leak into the Content-Disposition header.
    filename = raw_name.replace('"', "").replace("\n", "").replace("\r", "").strip() or "download"
    disposition = "inline" if request.GET.get("view") else "attachment"
    try:
        response = FileResponse(
            doc.file.open("rb"),
            content_type=content_type or "application/octet-stream",
        )
    except FileNotFoundError:
        raise Http404("File is missing from storage.")
    response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    return response


@login_required
@require_POST
def document_comment(request, pk):
    doc = _get_owned_document(request, pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        DocumentComment.objects.create(
            document=doc,
            author=request.user,
            body=form.cleaned_data["body"],
        )
    return redirect("document_detail", pk=doc.pk)


@login_required
@require_POST
def document_handle(request, pk):
    doc = _get_owned_document(request, pk)
    doc.handled = not doc.handled
    doc.save(update_fields=["handled"])
    if request.user.is_boss:
        return redirect("boss_feed")
    return redirect("document_detail", pk=doc.pk)
