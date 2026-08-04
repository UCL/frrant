import pytest
from django.contrib.auth.models import Permission
from django.test import RequestFactory
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    CitingAuthor,
    CitingWork,
    Fragment,
    Testimonium,
    Work,
)
from rard.research.views import (
    anonymous_fragment_set_publishable,
    antiquarian_set_publishable,
    citing_author_set_publishable,
    citing_work_set_publishable,
    fragment_set_publishable,
    work_set_publishable,
)

# Aliased so pytest does not collect this imported view as a test.
from rard.research.views.testimonium import (
    testimonium_set_publishable as set_testimonium_publishable,
)
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def _create_antiquarian():
    return Antiquarian.objects.create(name="name", re_code="re1")


def _create_work():
    return Work.objects.create(name="work")


def _create_fragment():
    return Fragment.objects.create(name="fragment")


def _create_anonymous_fragment():
    return AnonymousFragment.objects.create(name="anonymous fragment")


def _create_testimonium():
    return Testimonium.objects.create(name="testimonium")


def _create_citing_author():
    return CitingAuthor.objects.create(name="citing author")


def _create_citing_work():
    return CitingWork.objects.create(title="citing work")


PUBLISHABLE_CASES = [
    pytest.param(
        _create_antiquarian,
        antiquarian_set_publishable,
        "antiquarian:set_publishable",
        "antiquarian:detail",
        "publish_antiquarian",
        id="Antiquarian",
    ),
    pytest.param(
        _create_work,
        work_set_publishable,
        "work:set_publishable",
        "work:detail",
        "publish_work",
        id="Work",
    ),
    pytest.param(
        _create_fragment,
        fragment_set_publishable,
        "fragment:set_publishable",
        "fragment:detail",
        "publish_fragment",
        id="Fragment",
    ),
    pytest.param(
        _create_anonymous_fragment,
        anonymous_fragment_set_publishable,
        "anonymous_fragment:set_publishable",
        "anonymous_fragment:detail",
        "publish_anonymous_fragment",
        id="AnonymousFragment",
    ),
    pytest.param(
        _create_testimonium,
        set_testimonium_publishable,
        "testimonium:set_publishable",
        "testimonium:detail",
        "publish_testimonium",
        id="Testimonium",
    ),
    pytest.param(
        _create_citing_author,
        citing_author_set_publishable,
        "citingauthor:set_publishable",
        "citingauthor:detail",
        "publish_citing_author",
        id="CitingAuthor",
    ),
    pytest.param(
        _create_citing_work,
        citing_work_set_publishable,
        "citingauthor:work_set_publishable",
        "citingauthor:work_detail",
        "publish_citing_work",
        id="CitingWork",
    ),
]


@pytest.mark.parametrize(
    "create_obj, view_func, url_name, detail_url_name, permission_codename",
    PUBLISHABLE_CASES,
)
def test_set_publishable_denied_without_permission(
    create_obj, view_func, url_name, detail_url_name, permission_codename
):
    obj = create_obj()
    assert obj.publishable is False

    url = reverse(url_name, kwargs={"pk": obj.pk})
    request = RequestFactory().post(url, data={"publishable": "True"})
    request.user = UserFactory.create(is_superuser=False)

    response = view_func(request, pk=obj.pk)

    obj.refresh_from_db()
    assert obj.publishable is False
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.parametrize(
    "create_obj, view_func, url_name, detail_url_name, permission_codename",
    PUBLISHABLE_CASES,
)
def test_set_publishable_allowed_with_permission(
    create_obj, view_func, url_name, detail_url_name, permission_codename
):
    obj = create_obj()
    assert obj.publishable is False

    user = UserFactory.create(is_superuser=False)
    permission = Permission.objects.get(
        content_type__app_label="research",
        codename=permission_codename,
    )
    user.user_permissions.add(permission)
    # Refresh so the permission cache is cleared after assignment.
    user = type(user).objects.get(pk=user.pk)

    url = reverse(url_name, kwargs={"pk": obj.pk})
    request = RequestFactory().post(url, data={"publishable": "True"})
    request.user = user

    response = view_func(request, pk=obj.pk)

    obj.refresh_from_db()
    assert obj.publishable is True
    assert response.status_code == 302
    assert response.url == reverse(detail_url_name, kwargs={"pk": obj.pk})

    # And back again...
    request = RequestFactory().post(url, data={"publishable": "False"})
    request.user = user

    response = view_func(request, pk=obj.pk)

    obj.refresh_from_db()
    assert obj.publishable is False
    assert response.status_code == 302
    assert response.url == reverse(detail_url_name, kwargs={"pk": obj.pk})
