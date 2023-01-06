import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    BibliographyItem,
    CitingAuthor,
    CitingWork,
    Fragment,
    OriginalText,
    Testimonium,
    TextObjectField,
    Topic,
    Translation,
    Work,
)
from rard.research.models.base import AppositumFragmentLink, FragmentLink
from rard.research.views import SearchView
from rard.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestSearchView(TestCase):
    def test_login_required(self):
        # remove this test when the site goes public
        url = reverse("search:home")
        request = RequestFactory().get(url)

        # specify an unauthenticated user
        request.user = AnonymousUser()

        response = SearchView.as_view()(
            request,
        )

        # should be redirected to the login page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, "{}?next={}".format(reverse(settings.LOGIN_URL), url)
        )
        # but if we have an authenticated user it should work
        request.user = UserFactory()

        response = SearchView.as_view()(
            request,
        )

        self.assertEqual(response.status_code, 200)

    def test_default_queryset(self):
        # if we specify nothing to search, we should get nothing in the
        # search queryset
        view = SearchView()

        # create some data and then show we don't find any of it
        # unless we add search terms to the request
        Antiquarian.objects.create(name="findme", re_code="1")
        Antiquarian.objects.create(name="andme", re_code="2")

        url = reverse("search:home")
        request = RequestFactory().get(url, data={})
        view.request = request
        self.assertEqual(0, len(view.get_queryset()))

    def test_search_queryset(self):
        view = SearchView()

        # create some data to search
        Antiquarian.objects.create(name="findme", re_code="1")
        Antiquarian.objects.create(name="searchme", re_code="2")
        Work.objects.create(name="hellofromme")

        # search for '*me' in the antiquarians
        data = {
            "what": "antiquarians",
            "q": "*me",
        }
        url = reverse("search:home")
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(2, len(view.get_queryset()))

        # also test the 'all' parameter
        data = {
            "what": "all",
            "q": "*me",
        }
        url = reverse("search:home")
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(3, len(view.get_queryset()))

    def test_empty_search_redirects(self):

        # any empty sring should be ignored
        for search_term in ("", " ", "              "):
            data = {
                "what": "antiquarians",
                "q": search_term,
            }
            url = reverse("search:home")
            request = RequestFactory().get(url, data=data)
            request.user = UserFactory()
            view = SearchView()
            view.request = request
            response = SearchView.as_view()(request)

            # check we redirect to the home page without GET params
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, url)

    def test_get_only(self):
        # we only allow GET-based search
        data = {
            "what": "antiquarians",
            "q": "hai",
        }
        url = reverse("search:home")
        # create a POST request instead...
        request = RequestFactory().post(url, data=data)
        request.user = UserFactory()
        view = SearchView()
        view.request = request
        response = SearchView.as_view()(request)

        # verboten
        self.assertEqual(response.status_code, 405)

    def test_search_classes(self):
        # the types of objects we can search
        self.assertEqual(
            [x for x in SearchView().SEARCH_METHODS["all_methods"].keys()],
            [
                "antiquarians",
                "apparatus critici",
                "bibliographies",
                "citing authors",
                "citing works",
                "topics",
                "works",
                "fragments_all content",
                "fragments_original texts",
                "fragments_translations",
                "fragments_commentary",
                "testimonia_all content",
                "testimonia_original texts",
                "testimonia_translations",
                "testimonia_commentary",
                "apposita_all content",
                "apposita_original texts",
                "apposita_translations",
                "apposita_commentary",
                "anonymous fragments_all content",
                "anonymous fragments_original texts",
                "anonymous fragments_translations",
                "anonymous fragments_commentary",
            ],
        )

    def setup_content_field_search_data(self):
        cw = CitingWork.objects.create(title="citing_work")
        # fragments
        comm1 = TextObjectField.objects.create(content="step floor cheese")
        comm2 = TextObjectField.objects.create(content="mash fiorentina claus")
        f1 = Fragment.objects.create()
        f2 = Fragment.objects.create()
        f1.commentary = comm1
        f2.commentary = comm2
        ot1 = OriginalText.objects.create(
            content="step fiorentina cheese",
            citing_work=cw,
            owner=f1,
        )
        ot1.references.create(
            reference_position="alice",
        )
        ot2 = OriginalText.objects.create(
            content="mash floor claus", citing_work=cw, owner=f2
        )
        ot2.references.create(
            reference_position="alice",
        )
        Translation.objects.create(
            original_text=ot1, translated_text="mash fiorentina cheese"
        )
        Translation.objects.create(
            original_text=ot2, translated_text="step floor claus"
        )
        f1.save()
        f2.save()

    def test_original_text_content_field_search(self):
        """Test searching just the original text content
        for a fragment"""
        self.setup_content_field_search_data()

        # search for 'fiorentina' in the fragments' original texts
        view = SearchView()
        # Confirm general search returns both fragments
        data = {
            "q": "fiorentina",
        }
        url = reverse("search:home")
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(len(view.get_queryset()), 2)
        # Now search for original_text content only
        data["what"] = "fragments_original texts"
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(len(view.get_queryset()), 1)

    def test_translation_content_field_search(self):
        self.setup_content_field_search_data()

        # search for 'fiorentina' in the fragments' translations
        view = SearchView()
        data = {
            "q": "fiorentina",
            "what": "fragments_translations",
        }
        url = reverse("search:home")
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(len(view.get_queryset()), 1)

    def test_commentary_content_field_search(self):
        self.setup_content_field_search_data()

        # search for 'fiorentina' in the fragments' commentaries
        view = SearchView()
        data = {
            "q": "fiorentina",
            "what": "fragments_commentary",
        }
        url = reverse("search:home")
        request = RequestFactory().get(url, data=data)
        view.request = request
        self.assertEqual(len(view.get_queryset()), 1)

    def test_search_objects(self):

        # Run a particular search and return a list of results
        def do_search(search_function, keywords):
            return list(search_function(SearchView.Term(keywords)))

        view = SearchView()

        # basic tests for antiquarian
        a1 = Antiquarian.objects.create(name="findme", re_code="1")
        a2 = Antiquarian.objects.create(name="foo", re_code="2")
        self.assertEqual(do_search(view.antiquarian_search, "findme"), [a1])
        self.assertEqual(do_search(view.antiquarian_search, "FinDMe"), [a1])
        self.assertEqual(do_search(view.antiquarian_search, "foo"), [a2])
        self.assertEqual(do_search(view.antiquarian_search, "fOo"), [a2])
        self.assertEqual(do_search(view.antiquarian_search, "F*"), [a1, a2])

        # topics
        t1 = Topic.objects.create(name="topic", order=1)
        t2 = Topic.objects.create(name="pictures", order=2)
        self.assertEqual(do_search(view.topic_search, "topic"), [t1])
        self.assertEqual(do_search(view.topic_search, "TOPIc"), [t1])
        self.assertEqual(do_search(view.topic_search, "picture?"), [t2])
        self.assertEqual(do_search(view.topic_search, "PiCTureS"), [t2])
        self.assertEqual(do_search(view.topic_search, "*PIC*"), [t1, t2])

        # works
        w1 = Work.objects.create(name="work")
        w2 = Work.objects.create(name="nothing")
        self.assertEqual(do_search(view.work_search, "work"), [w1])
        self.assertEqual(do_search(view.work_search, "WORK"), [w1])
        self.assertEqual(do_search(view.work_search, "nothing"), [w2])
        self.assertEqual(do_search(view.work_search, "NothInG"), [w2])
        self.assertEqual(do_search(view.work_search, "*O*"), [w2, w1])

        cw = CitingWork.objects.create(title="citing_work")

        # fragments
        f1 = Fragment.objects.create()
        f1.original_texts.create(
            content="findme with your search powers",
            citing_work=cw,
        ).references.create(
            reference_position="louisa may alcott",
        )

        f2 = Fragment.objects.create()
        f2.original_texts.create(content="not$me", citing_work=cw,).references.create(
            reference_position="daisy ma<>,./?;'#:@~[]{}-=_+!\"£$%^&*()\\|y cooper",
        )

        self.assertEqual(do_search(view.fragment_search, "findme yovr"), [f1])
        self.assertEqual(do_search(view.fragment_search, "findme not"), [])
        self.assertEqual(
            do_search(view.fragment_search, 'findme "with yovr" powers'), [f1]
        )
        self.assertEqual(
            do_search(view.fragment_search, 'findme "with yovr powers"'), []
        )
        self.assertEqual(do_search(view.fragment_search, "FINDME"), [f1])
        self.assertEqual(do_search(view.fragment_search, "notme"), [f2])
        self.assertEqual(do_search(view.fragment_search, "No!TMe"), [f2])
        self.assertEqual(do_search(view.fragment_search, "*Me*"), [f1, f2])
        self.assertEqual(do_search(view.fragment_search, "may"), [f1, f2])
        self.assertEqual(
            do_search(view.fragment_search, "m!£$%^&()_+-=|\\{[}]:;@'~#<,>./ay"),
            [f1, f2],
        )
        self.assertEqual(do_search(view.fragment_search, "mav"), [])
        self.assertEqual(do_search(view.fragment_search, 'alcott "louisa may"'), [f1])
        self.assertEqual(do_search(view.fragment_search, 'may "louisa alcott"'), [])

        f3 = Fragment.objects.create()
        f3.original_texts.create(content="de uita Uaticani", citing_work=cw)

        f4 = Fragment.objects.create()
        f4.original_texts.create(content="vita brevIS", citing_work=cw)

        self.assertEqual(do_search(view.fragment_search, "vita"), [f3, f4])
        self.assertEqual(do_search(view.fragment_search, "bREUIs"), [f4])

        t1 = Testimonium.objects.create()
        t1.original_texts.create(content="findme", citing_work=cw)

        t2 = Testimonium.objects.create()
        t2.original_texts.create(content="notme", citing_work=cw)

        self.assertEqual(do_search(view.testimonium_search, "findme"), [t1])
        self.assertEqual(do_search(view.testimonium_search, "FINDME"), [t1])
        self.assertEqual(do_search(view.testimonium_search, "notme"), [t2])
        self.assertEqual(do_search(view.testimonium_search, "NoTMe"), [t2])
        self.assertEqual(do_search(view.testimonium_search, "*Me*"), [t1, t2])

        # fragments with apparatus criticus
        data = {"content": "content", "citing_work": cw}
        f1 = Fragment.objects.create()
        o1 = f1.original_texts.create(**data)
        o1.apparatus_criticus_items.create(content="stuff")

        t1 = Testimonium.objects.create()
        o2 = t1.original_texts.create(**data)
        o2.apparatus_criticus_items.create(content="nonsense")

        f2 = AnonymousFragment.objects.create()
        o3 = f2.original_texts.create(**data)
        o3.apparatus_criticus_items.create(content="rubbish")

        self.assertEqual(do_search(view.apparatus_criticus_search, "?TuF?"), [f1])
        self.assertEqual(do_search(view.apparatus_criticus_search, "?TVF?"), [f1])
        self.assertEqual(do_search(view.apparatus_criticus_search, "*bBi*"), [f2])
        self.assertEqual(do_search(view.apparatus_criticus_search, "*nseN*"), [t1])
        self.assertEqual(do_search(view.apparatus_criticus_search, "*s*"), [f1, f2, t1])
        self.assertEqual(do_search(view.apparatus_criticus_search, "content"), [])

        # bibliography
        # parent = TextObjectField.objects.create(content="foo")
        data = {"authors": "Aab, W", "title": "The Roman Age"}  # , "parent": parent}
        b1 = BibliographyItem.objects.create(**data)
        data = {"authors": "Beeb, Z", "title": "The Roman Era"}  # , "parent": parent}
        b2 = BibliographyItem.objects.create(**data)

        self.assertEqual(do_search(view.bibliography_search, "*aab*"), [b1])
        self.assertEqual(do_search(view.bibliography_search, "*EE*"), [b2])
        self.assertEqual(do_search(view.bibliography_search, "romAN"), [b1, b2])

        # anonymous fragments vs. apposita
        data = {"content": "raddish", "citing_work": cw}
        f1 = Fragment.objects.create()
        af1 = AnonymousFragment.objects.create()
        o1 = af1.original_texts.create(**data)
        af2 = AnonymousFragment.objects.create()
        o2 = af2.original_texts.create(**data)
        # Create appositum link for one of the anonymous fragments
        AppositumFragmentLink.objects.create(anonymous_fragment=af1, linked_to=f1)

        self.assertEqual(
            do_search(view.anonymous_fragment_search, "raddish"), [af1, af2]
        )
        self.assertEqual(do_search(view.appositum_search, "raddish"), [af1])

        # citing authors
        ca1 = CitingAuthor.objects.create(name="Alice")
        ca2 = CitingAuthor.objects.create(name="Felicity")

        self.assertEqual(do_search(view.citing_author_search, "al*"), [ca1])
        self.assertEqual(do_search(view.citing_author_search, "fe*"), [ca2])
        self.assertEqual(do_search(view.citing_author_search, "*lic*"), [ca1, ca2])

        # citing works
        cw1 = CitingWork.objects.create(title="Opus", edition="Book one", author=ca1)
        cw2 = CitingWork.objects.create(title="Book", edition="Sixth", author=ca2)

        self.assertEqual(do_search(view.citing_work_search, "opu?"), [cw1])
        self.assertEqual(do_search(view.citing_work_search, "*xth"), [cw2])
        self.assertCountEqual(do_search(view.citing_work_search, "?ook"), [cw1, cw2])

    def test_wildcards(self):

        # Run a particular search and return a list of results
        def do_search(search_function, keywords):
            return list(search_function(SearchView.Term(keywords)))

        cw = CitingWork.objects.create(title="citing_work")
        f1 = Fragment.objects.create()
        f1.original_texts.create(
            **{"citing_work": cw, "content": "characteristic rage"}
        )
        f2 = Fragment.objects.create()
        f2.original_texts.create(
            **{"citing_work": cw, "content": "middle aged man in lycra"}
        )
        f3 = Fragment.objects.create()
        f3.original_texts.create(
            **{"citing_work": cw, "content": "what's my age again?"}
        )

        view = SearchView()

        self.assertEqual(do_search(view.fragment_search, "age"), [f3])
        self.assertEqual(do_search(view.fragment_search, "age?"), [f2])
        self.assertEqual(do_search(view.fragment_search, "?age"), [f1])
        self.assertEqual(do_search(view.fragment_search, "?age*"), [f1])
        self.assertEqual(do_search(view.fragment_search, "age*"), [f2, f3])
        self.assertEqual(do_search(view.fragment_search, "*age"), [f1, f3])
        self.assertEqual(do_search(view.fragment_search, "*age?"), [f2])
        self.assertEqual(do_search(view.fragment_search, "*age*"), [f1, f2, f3])
        # Non-wildcard punctuation should be ignored in search term
        self.assertEqual(do_search(view.fragment_search, "what's"), [f3])
        self.assertEqual(do_search(view.fragment_search, "whats"), [f3])
        # Punctuation should be ignored in content
        self.assertEqual(do_search(view.fragment_search, "again"), [f3])
        self.assertEqual(do_search(view.fragment_search, "again?"), [])

    def test_search_snippets(self):

        raw_content = (
            "Lorem ipsum dolor sit amet, <span class='test consectatur'>"
            "consectetur</span> adipiscing <strong>elit</strong>, sed do "
            "eiusmod tempor incididunt ut labore et dolore magna aliqua"
        )
        search_term = "consectetur"
        expected_snippet = (
            'Lorem ipsum dolor sit amet <span class="search-snippet">'
            "consectetur</span> adipiscing elit sed do eiusmod ..."
        )

        view = SearchView()

        cw = CitingWork.objects.create(title="citing_work")

        # fragments
        f1 = Fragment.objects.create()
        f1.original_texts.create(
            content=raw_content,
            citing_work=cw,
        )

        search_results = list(view.fragment_search(SearchView.Term(search_term)))

        # Did the search work as expected?
        self.assertIn(f1, search_results)
        # Is the snippet correct?
        self.assertEqual(search_results[0].snippet, expected_snippet)

    def test_search_filters(self):
        # Antiquarians
        ant1 = Antiquarian.objects.create(name="John", re_code="1")
        ant2 = Antiquarian.objects.create(name="Paul", re_code="2")

        # Authors
        auth1 = CitingAuthor.objects.create(name="George")
        cw1 = CitingWork.objects.create(title="Something", author=auth1)
        auth2 = CitingAuthor.objects.create(name="Ringo")
        cw2 = CitingWork.objects.create(title="Yellow Submarine", author=auth2)

        # Fragments
        f1 = Fragment.objects.create()
        f1.original_texts.create(
            content="A fragment of wonderful text", citing_work=cw1
        )
        f2 = Fragment.objects.create()
        f2.original_texts.create(content="Another wonderful fragment", citing_work=cw2)
        FragmentLink.objects.create(fragment=f1, antiquarian=ant1)
        FragmentLink.objects.create(fragment=f2, antiquarian=ant2)

        # Test search requests
        url = reverse("search:home")

        # make sure we can get both fragments
        data = {
            "q": "wonderful",
        }
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory()
        response = SearchView.as_view()(request)

        self.assertCountEqual(response.context_data["results"], [f1, f2])

        # Filter by antiquarian
        data = {"q": "wonderful", "ant": ant1.id}
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory()
        response = SearchView.as_view()(request)

        self.assertEqual(response.context_data["results"], [f1])

        # Filter by citing author
        data = {"q": "wonderful", "ca": auth2.id}
        request = RequestFactory().get(url, data=data)
        request.user = UserFactory()
        response = SearchView.as_view()(request)

        self.assertEqual(response.context_data["results"], [f2])
